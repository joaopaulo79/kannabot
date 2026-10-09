from kannabot.permissions import Permissions, PermissionDenied

class Checagens_Autorizacao:
    def __init__(self, bot, configuracao):
        self.permissions = Permissions(bot, configuracao.grupos_id)

    def grupo_autorizado(self, grupo_id):
        return self.permissions.authorized(grupo_id)

    def is_admin(self, mensagem):
        try:
            self.permissions.actor(mensagem)
            return True
        except PermissionDenied:
            return False

    def emote_autorizado(self, mensagem):
        try:
            self.permissions.emote_actor(mensagem)
            return True
        except PermissionDenied:
            return False
