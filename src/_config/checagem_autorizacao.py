from src import configuracao
from telebot import TeleBot

class Checagens_Autorizacao: 
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.carregar_grupos_autorizados()

    def carregar_grupos_autorizados(self):
        self.id_autorizacao = list(configuracao.grupos_id)

    def grupo_autorizado(self, grupo_id: int) -> bool:
        grupo_id_formatado = int(str(grupo_id).replace("-100", "-"))

        for id_autorizado in self.id_autorizacao:
            id_formatado = int(str(id_autorizado).replace("-100", "-")) 
            if grupo_id_formatado == id_formatado:
                return True
        return False

    def is_admin(self, mensagem) -> bool:
        try:
            self.bot.delete_message(mensagem.chat.id, mensagem.id)
            return True
        except:
            return False
