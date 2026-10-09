from src import configuracao, bot, botName, Msg
from src._config.erros_utilizacao import Erros_Utilizacao
from src._config.checagem_autorizacao import Checagens_Autorizacao

def get_construcao_acoes():
  from src.emotes.construcao_acoes import Construcao_Acoes
  return Construcao_Acoes

CHAVE_API = configuracao.token
Erro = Erros_Utilizacao()
Checar = Checagens_Autorizacao(bot)
