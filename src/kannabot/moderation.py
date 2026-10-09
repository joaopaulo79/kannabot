"""Moderation services: validation precedes effects; failures are audited."""
import re
from telebot.types import ChatPermissions
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from kannabot.permissions import Permissions, PermissionDenied
from kannabot.interacoes import Seen
from kannabot.governance import Governance

def parse_duration(text):
    match = re.fullmatch(r"([1-9][0-9]{0,8})([smhd])", text)
    if match is None:
        raise ValueError("Use duração como 10m, 2h ou 1d.")
    seconds = int(match[1]) * {"s":1, "m":60, "h":3600, "d":86400}[match[2]]
    if not 60 <= seconds <= 365 * 86400:
        raise ValueError("Duração deve ficar entre 60 segundos e 365 dias.")
    return seconds

@dataclass(frozen=True)
class Result:
    outcome: str
    message: str

class PartialFailure(RuntimeError):
    pass

class Moderation:
    def __init__(self, bot, config, store, audit, clock=None, roles=None):
        self.bot, self.store, self.audit = bot, store, audit
        self.roles = roles
        self.governance = store if isinstance(store, Governance) else None
        self.permissions = Permissions(bot, config.grupos_id, roles)
        self.seen = Seen()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def reply_target(self, message):
        reply = getattr(message, "reply_to_message", None)
        if reply is None or getattr(getattr(reply, "chat", None), "id", None) != message.chat.id:
            raise ValueError("Responda à mensagem do alvo neste grupo.")
        user = getattr(reply, "from_user", None)
        if getattr(reply, "sender_chat", None) is not None or user is None or type(user.id) is not int or getattr(user, "is_bot", False):
            raise ValueError("O alvo deve ser um membro identificado.")
        return reply, user.id

    def handle(self, command, message):
        actor = target = None
        reason = ""
        error = None
        rule = None
        try:
            actor = self.permissions.actor(message, command)
            reply, target = self.reply_target(message)
            parts = message.text.split(maxsplit=1)
            reason = self.audit.clean(parts[1].strip()) if len(parts)>1 else ""
            duration = None
            if command == "mute":
                mute_parts = parts[1].split(maxsplit=1) if len(parts)>1 else []
                if len(mute_parts) != 2:
                    raise ValueError("Use /mute duração motivo em resposta.")
                duration = parse_duration(mute_parts[0])
                reason = self.audit.clean(mute_parts[1].strip())
            if self.governance and command != "warnings":
                reason_parts=reason.split(maxsplit=1)
                code=reason_parts[0] if reason_parts else ""
                if re.fullmatch(r"R[0-9]{2,4}",code):
                    rule=self.governance.rule(message.chat.id,code)
                    if not rule or not rule["active"]:raise ValueError("Regra inexistente ou revogada.")
                    if command not in rule["actions"]:raise ValueError("Ação não prevista nesta regra; condições especiais precisam de definição.")
                    if command=="warn" and rule["weight"] is None:raise ValueError("Peso desta regra ainda não definido.")
                    if command=="mute":
                        minimum,maximum={"N1":(300,3540),"N2":(3600,86400),"N3":(86400,604800)}[rule["level"]]
                        if not minimum<=duration<=maximum:raise ValueError("Duração fora da faixa do nível da regra.")
                    reason=self.audit.clean(rule["name"]+(": "+reason_parts[1] if len(reason_parts)>1 else ""))
            if command == "warnings":
                total, rows = self.store.history(message.chat.id, target)
                lines = [f"Advertências: {total} (últimas {len(rows)})."]
                lines += [escape(f"{time} | autor {author}: {text}") for author,text,time in rows]
                if self.governance:
                    points=self.governance.points(message.chat.id,target)
                    lines=[f"Advertências válidas: {total}; pontos definidos: {points}."]
                    if points>=4:lines.append("Limite de 4 pontos atingido: revisão humana necessária, sem banimento automático.")
                    lines += [escape(f"ID {id} | {code or 'legado'} v{version} | peso {weight} | {'cancelada' if cancelled else 'válida'} | {text[:80]}") for id,code,version,weight,text,cancelled in self.governance.entries(message.chat.id,target)]
                result = Result("done", "\n".join(lines))
            else:
                if not reason:
                    raise ValueError("Informe um motivo explícito.")
                self.permissions.target(message.chat.id, target, actor)
                result = self.execute(command, message.chat.id, actor, target, reply.message_id, reason, f"manual:{message.message_id}", duration=duration, rule=rule)
        except (PermissionDenied, ValueError) as exc:
            result = Result("refused", str(exc))
        except PartialFailure as exc:
            error = exc
            result = Result("failed", "Membro removido, mas a liberação falhou: continua banido. Use /unban após verificar permissões.")
        except Exception as exc:
            error = exc
            result = Result("failed", "Não foi possível concluir a ação.")
        metadata=self.roles.metadata(message.chat.id,actor,target) if self.roles else {}
        if rule:metadata.update(rule_code=rule["code"],rule_version=rule["version"])
        metadata["detail"]=result.message[:180]
        self.audit.record(message.chat.id, actor, target, command, reason, result.outcome, error, metadata=metadata)
        return result

    def execute(self, command, chat_id, actor, target, message_id, reason, event_id, duration=None, rule=None):
        if self.roles:self.roles.authorize(chat_id,actor,command)
        self.permissions.target(chat_id,target,actor)
        if rule:
            latest=self.governance.rule(chat_id,rule["code"])
            if not latest or not latest["active"] or latest["version"]!=rule["version"]:
                raise ValueError("Regra mudou; revise a ação antes de executar.")
        claim=None
        if self.governance:
            key=f"delete:{message_id}" if command=="delete" else event_id
            claim=self.governance.begin(chat_id,key,command,actor,target,reason,rule)
            if claim is None:return Result("refused", "Ação já registrada; não será repetida.")
        try:
            result=self._execute(command,chat_id,actor,target,message_id,reason,event_id,duration,rule)
        except Exception as exc:
            if claim:
                status="partial" if isinstance(exc,PartialFailure) else "refused" if isinstance(exc,(PermissionDenied,ValueError)) else "uncertain"
                self.governance.finish(claim,status,type(exc).__name__)
            raise
        if claim:self.governance.finish(claim,result.outcome,result.message)
        return result

    def _execute(self, command, chat_id, actor, target, message_id, reason, event_id, duration=None, rule=None):
        self.permissions.target(chat_id, target, actor)
        if command in ("kick", "ban", "unban"):
            self.permissions.bot_right(chat_id, "can_restrict_members")
            if command in ("kick", "unban") and self.bot.get_chat(chat_id).type != "supergroup":
                raise ValueError("Expulsão com retorno e remoção de banimento requerem supergrupo.")
            if command == "unban" and self.permissions.member(chat_id, target).status != "kicked":
                return Result("refused", "Este membro não está banido.")
            if not self.seen.claim((chat_id, event_id, command)):
                return Result("refused", "Esta ação já foi processada.")
            if command == "unban":
                if self.bot.unban_chat_member(chat_id, target, only_if_banned=True) is not True:
                    raise RuntimeError("Unban not confirmed")
                return Result("done", "Banimento removido; o membro pode retornar voluntariamente.")
            if self.bot.ban_chat_member(chat_id, target) is not True:
                raise RuntimeError("Ban not confirmed")
            if command == "ban":
                return Result("done", "Membro banido.")
            try:
                self.permissions.target(chat_id, target, actor)
                self.permissions.bot_right(chat_id, "can_restrict_members")
                if self.bot.unban_chat_member(chat_id, target, only_if_banned=True) is not True:
                    raise RuntimeError("Unban not confirmed")
            except Exception:
                raise PartialFailure() from None
            return Result("done", "Membro expulso; retorno voluntário permitido.")
        if command == "mute":
            if type(duration) is not int or not 60 <= duration <= 365 * 86400:
                raise ValueError("Duração temporária inválida.")
            if self.bot.get_chat(chat_id).type != "supergroup":
                raise ValueError("Silêncio temporário requer supergrupo.")
            self.permissions.bot_right(chat_id, "can_restrict_members")
            if not self.seen.claim((chat_id, event_id, command)):
                return Result("refused", "Este silêncio já foi processado.")
            permissions = ChatPermissions(can_send_messages=False, can_send_audios=False,
                can_send_documents=False, can_send_photos=False, can_send_videos=False,
                can_send_video_notes=False, can_send_voice_notes=False, can_send_polls=False,
                can_send_other_messages=False, can_add_web_page_previews=False)
            until = int(self.clock().timestamp()) + duration
            if self.bot.restrict_chat_member(chat_id, target, permissions=permissions,
                    until_date=until, use_independent_chat_permissions=True) is not True:
                raise RuntimeError("Restriction not confirmed")
            return Result("done", f"Membro silenciado por {duration} segundos.")
        if command == "delete":
            self.permissions.bot_right(chat_id, "can_delete_messages")
            if not self.seen.claim((chat_id, message_id, command)):
                return Result("refused", "Esta mensagem já foi processada; exclusão não repetida.")
            if self.bot.delete_message(chat_id, message_id) is not True:
                raise RuntimeError("Deletion not confirmed")
            return Result("done", "Mensagem apagada.")
        if command != "warn":
            raise ValueError("Comando não suportado.")
        if self.governance:
            created=self.governance.add(chat_id,target,actor,reason,self.clock().isoformat(),event_id,rule=rule)
        else:
            created = self.store.add(chat_id, target, actor, reason, self.clock().isoformat(), event_id)
        return Result("done", "Advertência registrada.") if created else Result("refused", "Esta advertência já foi registrada.")
