"""Moderation services: validation precedes effects; failures are audited."""
import re
from telebot.types import ChatPermissions
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from kannabot.permissions import Permissions, PermissionDenied
from kannabot.interacoes import Seen

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

class Moderation:
    def __init__(self, bot, config, store, audit, clock=None):
        self.bot, self.store, self.audit = bot, store, audit
        self.permissions = Permissions(bot, config.grupos_id)
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
        try:
            actor = self.permissions.actor(message)
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
            if command == "warnings":
                total, rows = self.store.history(message.chat.id, target)
                lines = [f"Advertências: {total} (últimas {len(rows)})."]
                lines += [escape(f"{time} | autor {author}: {text}") for author,text,time in rows]
                result = Result("done", "\n".join(lines))
            else:
                if not reason:
                    raise ValueError("Informe um motivo explícito.")
                self.permissions.target(message.chat.id, target)
                result = self.execute(command, message.chat.id, actor, target, reply.message_id, reason, f"manual:{message.message_id}", duration=duration)
        except (PermissionDenied, ValueError) as exc:
            result = Result("refused", str(exc))
        except Exception as exc:
            error = exc
            result = Result("failed", "Não foi possível concluir a ação.")
        self.audit.record(message.chat.id, actor, target, command, reason, result.outcome, error)
        return result

    def execute(self, command, chat_id, actor, target, message_id, reason, event_id, duration=None):
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
        created = self.store.add(chat_id, target, actor, reason, self.clock().isoformat(), event_id)
        return Result("done", "Advertência registrada.") if created else Result("refused", "Esta advertência já foi registrada.")
