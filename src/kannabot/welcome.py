from html import escape
from kannabot.interacoes import Seen
from kannabot.permissions import Permissions

class Welcome:
    def __init__(self, bot, config, policy, audit):
        self.bot, self.policy, self.audit = bot, policy, audit
        self.permissions=Permissions(bot,config.grupos_id)
        self.seen=Seen()
    def handle(self, message):
        chat=message.chat.id
        options=self.policy.get(chat,"welcome")
        if not self.permissions.authorized(chat) or not options:
            return
        for member in getattr(message,"new_chat_members",None) or []:
            if not self.seen.claim((chat,message.message_id,member.id)):
                continue
            user=(getattr(member,"username",None) or str(member.id))[:64]
            text=options["text"].replace("{user}",user)+"\nRegras: "+options["rules"]
            try:
                self.bot.send_message(chat,escape(text),parse_mode="HTML",disable_web_page_preview=True)
                self.audit.record(chat,None,member.id,"welcome","Entrada no grupo","done")
            except Exception as exc:
                self.audit.record(chat,None,member.id,"welcome","Falha de boas-vindas","failed",exc)

def register(bot, service):
    bot.message_handler(content_types=["new_chat_members"])(service.handle)
