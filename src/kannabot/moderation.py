"""Moderation services: validation precedes effects; failures are audited."""
import re
import json
import sqlite3
from contextlib import closing
from kannabot.presentation import context, user_mention, mention, brief
from telebot.types import ChatPermissions
from telebot.apihelper import ApiTelegramException
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from kannabot.permissions import Permissions, PermissionDenied
from kannabot.interacoes import Seen
from kannabot.governance import Governance
from kannabot.rule_validation import RuleRefusal, validate_rule_action

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

class BanRoleRevocationFailure(PartialFailure):
    pass

class Moderation:
    def __init__(self, bot, config, store, audit, clock=None, roles=None):
        self.bot, self.store, self.audit = bot, store, audit
        self.roles = roles
        self.identities = None
        self.evidence = None
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
        if command=="delwarn":return self.delwarn(message)
        actor, context_data = context(message)
        target = None
        reason = ""
        error = None
        rule = None
        try:
            actor = self.permissions.actor(message, command)
            if self.identities is not None:
                message=self.identities.prepare(message,command)
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
                    validate_rule_action(rule,code,command)
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
                    lines=[f"📋 Histórico de advertências de {user_mention(reply.from_user)}",
                           f"Advertências válidas: {total} · Pontos: {points}."]
                    if points>=4:lines.append("Limite de 4 pontos atingido: revisão humana necessária, sem banimento automático.")
                    for entry in self.governance.detailed_entries(message.chat.id,target):
                        snapshot=json.loads(entry["snapshot"]) if entry["snapshot"] else None
                        lines.extend(["",f"#{entry['id']} — {'Cancelada' if entry['cancel_time'] else 'Válida'}"])
                        if snapshot:
                            lines.extend([escape(f"{snapshot['code']} — {snapshot['name']} · {snapshot['level']} · v{entry['rule_version']}"),"Descrição: "+brief(snapshot)])
                        lines.extend([f"Peso aplicado: {entry['weight'] if entry['weight'] is not None else 'não definido'}",
                                      "Motivo: "+escape(entry["reason"]), "Aplicada por: "+mention(entry["author_id"],entry.get("actor_username")), "Data: "+escape(entry["time"])])
                        if entry["cancel_time"]:lines.extend(["Cancelada por: "+mention(entry["cancel_actor"]),"Motivo do cancelamento: "+escape(entry["cancel_reason"])])
                    if not self.governance.detailed_entries(message.chat.id,target):lines.append("Nenhuma advertência registrada neste grupo.")
                result = Result("done", "\n".join(lines))
            else:
                if not reason:
                    raise ValueError("Informe um motivo explícito.")
                self.permissions.target(message.chat.id, target, actor, action=command)
                if command == "delete" and self.evidence is not None:
                    self.permissions.bot_right(message.chat.id,"can_delete_messages")
                    evidence_id,evidence_state=self.evidence.capture(message.chat.id,reply,f"manual:{message.message_id}",command)
                    context_data.update(evidence_id=evidence_id,evidence_status=evidence_state)
                result = self.execute(command, message.chat.id, actor, target, reply.message_id, reason, f"manual:{message.message_id}", duration=duration, rule=rule)
        except (PermissionDenied, ValueError) as exc:
            result = Result("refused", escape(self.audit.clean(str(exc), limit=3500) if isinstance(exc,RuleRefusal) else str(exc)))
        except BanRoleRevocationFailure as exc:
            error=exc
            result=Result("partial","⚠️ Banimento confirmado, mas a revogação do cargo interno falhou. A administração precisa corrigir o cargo antes de liberar o retorno.")
        except PartialFailure as exc:
            error = exc
            result = Result("failed", "Membro removido, mas a liberação falhou: continua banido. Use /unban após verificar permissões.")
        except Exception as exc:
            error = exc
            result = Result("failed", "Não foi possível concluir a ação.")
        if result.outcome=="done" and command!="warnings":
            result=Result("done",self.feedback(command,message,target,reason,duration,rule,result.message))
        metadata=self.roles.metadata(message.chat.id,actor,target) if self.roles else {}
        context_data.update(metadata)
        if self.identities is not None and target is not None:
            username=self.identities.username(message.chat.id,target)
            if username:context_data["target_username"]=username
        metadata=context_data
        if rule:metadata.update(rule_code=rule["code"],rule_version=rule["version"])
        if command=="warn" and result.outcome=="done" and self.governance:
            entry=next((e for e in self.governance.detailed_entries(message.chat.id,target) if e["event_id"]==f"manual:{message.message_id}"),None)
            if entry:metadata.update(warning_id=entry["id"],weight=entry["weight"],valid_count=self.governance.history(message.chat.id,target)[0],points=self.governance.points(message.chat.id,target))
        status=self.operation_status(message,command,locals().get("reply"))
        if result.outcome=="failed" and status in ("partial","uncertain"):
            result=Result(status,result.message if status=="partial" else "⚠️ Não consegui confirmar o resultado da ação. Confira o registro antes de tentar novamente.")
        metadata["detail"]=result.message[:300]
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
                try:self.governance.finish(claim,status,type(exc).__name__)
                except sqlite3.Error:
                    self.audit.record(chat_id,actor,target,command,reason,status,exc,metadata={"stage":"Persistência do resultado","detail":"Resultado externo requer conferência; ledger indisponível."})
            raise
        if claim:self.governance.finish(claim,result.outcome,result.message)
        return result

    def _execute(self, command, chat_id, actor, target, message_id, reason, event_id, duration=None, rule=None):
        self.permissions.target(chat_id, target, actor, action=command)
        if command in ("mute","kick","ban"):
            if self.permissions.member(chat_id,target).status in ("creator","administrator"):
                raise PermissionDenied("🛡️ O alvo é Administrador ou Dono no Telegram. A ação não foi executada; o cargo nativo precisa ser tratado pela administração.")
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
            previous=self.governance.role(chat_id,target) if command=="ban" and self.governance else "member"
            if self.bot.ban_chat_member(chat_id, target) is not True:
                raise RuntimeError("Ban not confirmed")
            if command == "ban":
                if previous in ("admin","mod"):
                    try:self.governance.set_role(chat_id,target,"member",actor,cause="confirmed_ban")
                    except Exception:raise BanRoleRevocationFailure() from None
                    from kannabot.presentation import ROLE_NAMES
                    return Result("done","Membro banido. Cargo interno de "+ROLE_NAMES[previous]+" revogado.")
                return Result("done", "Membro banido.")
            try:
                self.permissions.target(chat_id, target, actor, action=command)
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


    def feedback(self,command,message,target,reason,duration,rule,original):
        label=user_mention(message.reply_to_message.from_user)
        reason_text=reason
        if rule and reason.startswith(rule["name"]+": "):reason_text=reason[len(rule["name"])+2:]
        suffix="\nMotivo: "+escape(reason_text)
        if command=="warn" and self.governance:
            entry=next((e for e in self.governance.detailed_entries(message.chat.id,target) if e["event_id"]==f"manual:{message.message_id}"),None)
            if not entry:return original
            lines=[f"⚠️ Advertência #{entry['id']} registrada", "Alvo: "+label]
            if rule:lines.extend([escape(f"Regra: {rule['code']} — {rule['name']} · {rule['level']}"),"Descrição: "+brief(rule)])
            lines.extend([f"Peso: +{entry['weight']} pontos" if entry["weight"] is not None else "Peso: não definido","Motivo: "+escape(reason_text),f"Situação atual: {self.governance.history(message.chat.id,target)[0]} advertência(s) válida(s) · {self.governance.points(message.chat.id,target)} pontos."])
            return "\n".join(lines)
        if command=="delete":return f"🧹 Mensagem de {label} apagada!"+suffix+"\nNenhuma advertência foi adicionada."
        if command=="mute":
            unit=next((f"{duration//size} {name}" for size,name in ((86400,"dia(s)"),(3600,"hora(s)"),(60,"minuto(s)")) if duration%size==0),f"{duration} segundos")
            return f"🔇 Hora de uma pausa, {label}.\nSilenciamento aplicado por {unit}."+suffix
        if command=="kick":return f"🚪 {label} foi removido do grupo."+suffix+"\nO retorno está permitido, sujeito ao acesso ao grupo."
        if command=="ban":return f"⛔ {label} foi banido do grupo."+suffix+"\nBanimento sem prazo definido."+("\n🛡️ "+escape(original.split("Membro banido. ",1)[1]) if "Cargo interno" in original else "")
        if command=="unban":return f"✅ Banimento de {label} removido!"+suffix+"\nO usuário pode retornar; este comando não o adiciona novamente."
        return original


    def operation_status(self,message,command,reply):
        if not self.governance or command=="warnings":return None
        event=f"delete:{reply.message_id}" if command=="delete" and reply else f"manual:{message.message_id}"
        try:
            with closing(sqlite3.connect(self.governance.path)) as db:
                row=db.execute("SELECT status FROM sanctions WHERE chat_id=? AND event_id=? AND action=?",(message.chat.id,event,command)).fetchone()
                return row[0] if row else None
        except sqlite3.Error:return None


    def delwarn(self,message):
        actor,metadata=context(message);target=None;error=None;reason="";claim=None;warning=None
        try:
            actor=self.permissions.actor(message,"warn")
            self.permissions.actor(message,"delete")
            if self.identities is not None:message=self.identities.prepare(message,"delwarn")
            reply,target=self.reply_target(message)
            self.permissions.target(message.chat.id,target,actor)
            self.permissions.bot_right(message.chat.id,"can_delete_messages")
            parts=message.text.split(maxsplit=1)
            if len(parts)!=2 or not parts[1].strip():raise ValueError("Use /delwarn motivo ou /delwarn R10 motivo em resposta à mensagem.")
            if not self.governance:raise ValueError("Histórico indisponível; nenhuma ação executada.")
            argument=parts[1].strip();tokens=argument.split(maxsplit=1);rule=None
            if re.fullmatch(r"R[0-9]+",tokens[0]):
                if len(tokens)!=2:raise ValueError("Informe o motivo após o código da regra.")
                rule=self.governance.rule(message.chat.id,tokens[0])
                validate_rule_action(rule,tokens[0],"delwarn")
                argument=tokens[1]
            reason=self.audit.clean(argument)
            if not reason.strip():raise ValueError("Informe um motivo explícito.")
            if self.evidence is not None:
                evidence_id,evidence_state=self.evidence.capture(message.chat.id,reply,f"manual:{message.message_id}","delwarn")
                metadata.update(evidence_id=evidence_id,evidence_status=evidence_state)
            operation=self.governance.start_delwarn(message.chat.id,reply.message_id,actor,target,reason,rule)
            if operation is None:raise ValueError("Esta mensagem já possui um delwarn registrado; ação não repetida.")
            claim,warning=operation
            metadata.update(warning_id=warning)
            if rule:metadata.update(rule_code=rule["code"],rule_version=rule["version"],weight=rule["weight"])
            # Snapshot persistence precedes the irreversible external effect.
            self.permissions.target(message.chat.id,target,actor)
            self.permissions.bot_right(message.chat.id,"can_delete_messages")
            if self.bot.delete_message(message.chat.id,reply.message_id) is not True:
                raise RuntimeError("Deletion not confirmed")
            rule_info=(f"Regra: {escape(rule['code'])} — {escape(rule['name'])} · {rule['level']}\nDescrição: {brief(rule)}\nPeso: +{rule['weight']} pontos" if rule else "Tipo: advertência manual, sem regra vinculada.\nPeso: não definido; não acrescenta pontos.")
            result=Result("done",f"🧹⚠️ Mensagem apagada e advertência #{warning} registrada.\nAlvo: {user_mention(reply.from_user)}\n{rule_info}\nMotivo: {escape(reason)}")
            self.governance.finish(claim,"done","Advertência registrada; exclusão confirmada")
        except (PermissionDenied,ValueError) as exc:
            error=None if isinstance(exc,RuleRefusal) and warning is None else exc
            result=Result("partial" if warning else "refused", ("⚠️ Advertência registrada, mas a exclusão foi recusada.\n" if warning else "")+escape(self.audit.clean(str(exc), limit=3500) if isinstance(exc,RuleRefusal) else self.audit.clean(str(exc))))
        except Exception as exc:
            error=exc
            confirmed=isinstance(exc,ApiTelegramException) and exc.error_code in (400,401,403,429)
            outcome="partial" if warning and confirmed else "uncertain" if warning else "failed"
            result=Result(outcome,f"⚠️ Advertência #{warning} registrada; "+("exclusão recusada." if confirmed else "resultado da exclusão não confirmado. Não repita o comando.") if warning else "⚠️ Não foi possível registrar a advertência. A exclusão não foi solicitada.")
        if claim and result.outcome!="done":
            try:self.governance.finish(claim,result.outcome,type(error).__name__)
            except sqlite3.Error:result=Result("uncertain",result.message+" Não foi possível atualizar o registro da operação.")
        if warning:
            total=self.governance.history(message.chat.id,target)[0];points=self.governance.points(message.chat.id,target)
            result=Result(result.outcome,result.message+f"\nSituação atual: {total} advertência(s) válida(s) · {points} pontos.")
            metadata.update(valid_count=total,points=points)
        if self.roles:metadata.update(self.roles.metadata(message.chat.id,actor,target))
        metadata["detail"]=result.message
        self.audit.record(message.chat.id,actor,target,"delwarn",reason,result.outcome,error,metadata=metadata)
        return result
