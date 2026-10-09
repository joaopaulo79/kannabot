from telebot import apihelper

class PermissionDenied(ValueError):
    pass

class Permissions:
    def __init__(self, bot, groups, roles=None):
        self.bot = bot
        self.roles = roles
        self.groups = frozenset(groups)

    def authorized(self, chat_id):
        return type(chat_id) is int and chat_id in self.groups

    def member(self, chat_id, user_id):
        if not self.authorized(chat_id) or type(user_id) is not int:
            raise PermissionDenied("Grupo ou identidade não autorizado.")
        try:
            return self.bot.get_chat_member(chat_id, user_id)
        except Exception:
            raise PermissionDenied("Não foi possível confirmar permissões.") from None

    def is_admin(self, chat_id, user_id):
        return self.member(chat_id, user_id).status in ("administrator", "creator")

    def emote_actor(self, message):
        """Allow identified group members to use social commands."""
        user = getattr(message, "from_user", None)
        if getattr(message, "sender_chat", None) is not None or user is None or getattr(user, "is_bot", False):
            raise PermissionDenied("Emote requer membro identificado.")
        role = self.member(message.chat.id, user.id)
        allowed = role.status in ("member", "administrator", "creator")
        if role.status == "restricted":
            allowed = getattr(role, "is_member", False) is True
        if not allowed:
            raise PermissionDenied("Emote requer membro do grupo autorizado.")
        return user.id

    def actor(self, message, action="warn"):
        user = getattr(message, "from_user", None)
        if getattr(message, "sender_chat", None) is not None or user is None or getattr(user, "is_bot", False):
            raise PermissionDenied("Comando requer administrador identificado.")
        if self.roles is not None:
            self.roles.authorize(message.chat.id, user.id, action)
            return user.id
        if not self.is_admin(message.chat.id, user.id):
            raise PermissionDenied("Comando exclusivo de administradores.")
        return user.id

    def target(self, chat_id, user_id, actor_id=None, action=None):
        if self.roles is not None:
            if actor_id is None:raise PermissionDenied("Autor necessário para validar hierarquia.")
            self.roles.target(chat_id, actor_id, user_id, action=action)
            return user_id
        if self.is_admin(chat_id, user_id):
            raise PermissionDenied("Administradores estão protegidos.")
        return user_id

    def bot_right(self, chat_id, right):
        try:
            bot_id = self.bot.get_me().id
            role = self.member(chat_id, bot_id)
        except Exception:
            raise PermissionDenied("Não foi possível confirmar direitos do bot.") from None
        if role.status == "creator":
            return
        if role.status != "administrator" or getattr(role, right, False) is not True:
            raise PermissionDenied("O bot não possui a permissão necessária.")
