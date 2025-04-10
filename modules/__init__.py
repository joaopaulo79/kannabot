import telebot, os
from modules._config.mensagem_usuario import Mensagem_Usuario
from modules.emotes.open_json import Abrir_Arquivos_Emotes

CHAVE_API = os.getenv("CHAVE_API_BOT")
bot = telebot.TeleBot(str(CHAVE_API))
botName = "@KannaKamui2BOT"

Msg = Mensagem_Usuario()
Abrir = Abrir_Arquivos_Emotes()