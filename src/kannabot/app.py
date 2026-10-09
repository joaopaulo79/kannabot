from pathlib import Path
from telebot import TeleBot
from kannabot._config.configuracao import carregar_configuracao, RAIZ_PROJETO
from kannabot.handlers.emotes import register

def create_app(configuracao=None, client=None, home=None):
    root = Path(home or RAIZ_PROJETO)
    settings = configuracao or carregar_configuracao(root)
    bot = client if client is not None else TeleBot(settings.token)
    register(bot, settings, root / "var")
    return bot
