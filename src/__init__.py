import telebot
from src._config.configuracao import carregar_configuracao, ErroConfiguracao

try:
    configuracao = carregar_configuracao()
except ErroConfiguracao as erro:
    raise SystemExit(f"Erro de configuração: {erro}") from None

from src._config.mensagem_usuario import Mensagem_Usuario
from src.emotes.open_json import Abrir_Arquivos_Emotes

CHAVE_API = configuracao.token
bot = telebot.TeleBot(CHAVE_API)
botName = configuracao.bot_username

Msg = Mensagem_Usuario()
Abrir = Abrir_Arquivos_Emotes()
