import os
from pathlib import Path
from telebot import TeleBot
from kannabot.audit import Audit
from kannabot.storage import WarningStore
from kannabot.moderation import Moderation
from kannabot.handlers.moderation import register as register_moderation
from kannabot._config.configuracao import carregar_configuracao, RAIZ_PROJETO
from kannabot.handlers.emotes import register

def create_app(configuracao=None, client=None, home=None):
    root = Path(home or os.getenv("KANNA_HOME") or RAIZ_PROJETO).resolve()
    settings = configuracao or carregar_configuracao(root)
    bot = client if client is not None else TeleBot(settings.token)
    bot.kanna_audit = Audit(bot, settings.log_chat_id, root / "var/audit.jsonl", secrets=(settings.token,))
    store = WarningStore(root / "var/moderation.sqlite3")
    bot.kanna_moderation = Moderation(bot, settings, store, bot.kanna_audit)
    register_moderation(bot, bot.kanna_moderation)
    register(bot, settings, root / "var")
    return bot
