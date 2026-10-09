"""Moderation services: validation precedes effects; failures are audited."""
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from kannabot.permissions import Permissions, PermissionDenied
from kannabot.interacoes import Seen

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
            if command == "warnings":
                total, rows = self.store.history(message.chat.id, target)
                lines = [f"Advertências: {total} (últimas {len(rows)})."]
                lines += [escape(f"{time} | autor {author}: {text}") for author,text,time in rows]
                result = Result("done", "\n".join(lines))
            else:
                if not reason:
                    raise ValueError("Informe um motivo explícito.")
                self.permissions.target(message.chat.id, target)
                result = self.execute(command, message.chat.id, actor, target, reply.message_id, reason, f"manual:{message.message_id}")
        except (PermissionDenied, ValueError) as exc:
            result = Result("refused", str(exc))
        except Exception as exc:
            error = exc
            result = Result("failed", "Não foi possível concluir a ação.")
        self.audit.record(message.chat.id, actor, target, command, reason, result.outcome, error)
        return result

    def execute(self, command, chat_id, actor, target, message_id, reason, event_id):
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
