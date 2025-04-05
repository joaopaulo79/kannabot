import telebot, os
from modules.mensagem_usuario import Mensagem_Usuario

CHAVE_API = os.getenv("CHAVE_API_BOT")
bot = telebot.TeleBot(str(CHAVE_API))
botName = "@KannaKamui2BOT"

Msg = Mensagem_Usuario()