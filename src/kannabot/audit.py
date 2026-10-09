"""Moderation audit with sanitized local fallback and no action retries."""
import json
import logging
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from threading import RLock

class Audit:
    def __init__(self, bot, chat_id=None, path=None, secrets=(), clock=None):
        self.bot, self.chat_id = bot, chat_id
        self.path = Path(path) if path else None
        self.secrets = tuple(value for value in secrets if value)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.lock = RLock()

    def clean(self, text):
        text = str(text)
        for secret in self.secrets:
            text = text.replace(secret, "[redacted]")
        return re.sub(r"[0-9]+:[A-Za-z0-9_-]+", "[redacted]", text)[:300]

    def record(self, chat_id, actor_id, target_id, action, reason, outcome, error=None, metadata=None):
        if outcome not in ("done", "refused", "failed"):
            raise ValueError("Unknown audit outcome")
        if type(chat_id) is not int or any(value is not None and type(value) is not int for value in (actor_id, target_id)):
            raise ValueError("Audit identities must be numeric")
        event = dict(time=self.clock().isoformat(), chat_id=chat_id,
                     actor=actor_id if actor_id is not None else "automation", target=target_id,
                     action=self.clean(action), reason=self.clean(reason), outcome=outcome)
        for key,value in (metadata or {}).items():
            if key in ("actor_role","target_role","actor_title","target_title","rule_code","rule_version","detail"):
                event[key] = self.clean(value)
        if error is not None:
            event["error"] = type(error).__name__
        if self.chat_id is not None:
            try:
                chat = self.bot.get_chat(self.chat_id)
                if chat.type not in ("group", "supergroup") or getattr(chat, "username", None):
                    raise ValueError("Private log group required")
                text = "\n".join(f"{key}: {escape(str(value))}" for key, value in event.items())
                self.bot.send_message(self.chat_id, text, parse_mode="HTML")
                return True
            except Exception:
                pass
        try:
            if self.path is None:
                raise OSError("No fallback path")
            with self.lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as output:
                    output.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            logging.getLogger(__name__).error("Audit destination unavailable; outcome=%s", outcome)
        return False
