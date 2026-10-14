"""Container entry point with verified identity and polling progress."""
import json
import logging
import os
import signal
import time
from kannabot.app import create_app
from kannabot._config.configuracao import carregar_configuracao
from deploy.runtime_common import read_database_url, progress_path


def record_progress(path, clock=time.time):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"time": clock(), "pid": os.getpid()}), encoding="utf-8")
    temporary.replace(path)


def observe_polling(bot, path):
    original = bot.get_updates
    def get_updates(*args, **kwargs):
        updates = original(*args, **kwargs)
        record_progress(path)
        return updates
    bot.get_updates = get_updates


def verify_identity(bot, username):
    identity = bot.get_me()
    if "@" + (identity.username or "").lower() != username.lower():
        raise ValueError("Configured bot identity does not match Telegram.")
    if bot.get_webhook_info().url:
        raise ValueError("A webhook is configured; polling cannot start.")


class SecretFormatter(logging.Formatter):
    def __init__(self, secrets):
        super().__init__("%(levelname)s: %(message)s")
        self.secrets = secrets
    def format(self, record):
        text = super().format(record)
        for secret in self.secrets:
            if secret:
                text = text.replace(secret, "[redacted]")
        return text


def main():
    try:
        os.environ["DATABASE_URL"] = read_database_url()
        config = carregar_configuracao()
        handler = logging.StreamHandler()
        handler.setFormatter(SecretFormatter((config.token, config.database_url)))
        logging.basicConfig(level=logging.WARNING, handlers=[handler], force=True)
        telegram_logger = logging.getLogger("TeleBot")
        telegram_logger.handlers.clear()
        telegram_logger.propagate = True
        path = progress_path()
        path.unlink(missing_ok=True)
        bot = create_app(configuracao=config)
        verify_identity(bot, config.bot_username)
        observe_polling(bot, path)
        def stop(_signal, _frame):
            bot.stop_polling()
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        print("Kanna iniciada; identidade confirmada e persistência PostgreSQL configurada.", flush=True)
        bot.infinity_polling(allowed_updates=["message", "callback_query"], skip_pending=os.environ.get("KANNA_SKIP_PENDING", "true").lower() == "true")
        return 0
    except Exception as error:
        print("Inicialização interrompida; confira configuração e acesso. Tipo: " + type(error).__name__, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
