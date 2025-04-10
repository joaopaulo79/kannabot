import telebot, os
from modules._config.mensagem_usuario import Mensagem_Usuario
from modules._config.erros_utilizacao import Erros_Utilizacao
from modules._config.checagem_autorizacao import Checagens_Autorizacao

def get_construcao_acoes():
  from modules.emotes.construcao_acoes import Construcao_Acoes
  return Construcao_Acoes

CHAVE_API = os.getenv("CHAVE_API_BOT")
bot = telebot.TeleBot(str(CHAVE_API))
botName = "@KannaKamui2BOT"

Msg = Mensagem_Usuario()
Erro = Erros_Utilizacao()
Checar = Checagens_Autorizacao(bot)