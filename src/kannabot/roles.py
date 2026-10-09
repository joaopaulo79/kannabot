"""Internal capabilities never derive from usernames or cosmetic titles."""
from kannabot.governance import CAPABILITIES, RANK
from kannabot.permissions import PermissionDenied

class Roles:
    def __init__(self,bot,groups,store):
        self.bot,self.groups,self.store=bot,frozenset(groups),store
    def member(self,chat,user):
        if type(chat) is not int or chat not in self.groups or type(user) is not int:
            raise PermissionDenied("Grupo/identidade não autorizado.")
        try:return self.bot.get_chat_member(chat,user)
        except Exception:raise PermissionDenied("Não foi possível confirmar identidade/cargo.") from None
    def role(self,chat,user):
        member=self.member(chat,user)
        if member.status=="creator":return "owner"
        if member.status not in ("member","administrator","restricted") or (member.status=="restricted" and getattr(member,"is_member",False) is not True):
            return "member"
        return self.store.role(chat,user)
    def authorize(self,chat,user,action):
        role=self.role(chat,user)
        if action not in CAPABILITIES[role]:raise PermissionDenied("Seu cargo interno não permite esta ação.")
        return role
    def target(self,chat,actor,target):
        if RANK[self.role(chat,actor)]<=RANK[self.role(chat,target)]:
            raise PermissionDenied("Não é permitido sancionar cargo igual ou superior.")
    def assign(self,chat,actor,target,role):
        if self.role(chat,actor)!="owner":raise PermissionDenied("Somente o Dono define cargos.")
        member=self.member(chat,target)
        if member.status=="creator" or member.status not in ("member","administrator","restricted") or (member.status=="restricted" and getattr(member,"is_member",False) is not True):
            raise PermissionDenied("Alvo não pode receber esta atribuição.")
        self.store.set_role(chat,target,role,actor)
    def metadata(self,chat,actor,target):
        result={}
        for prefix,user in (("actor",actor),("target",target)):
            if user is None:continue
            try:
                member=self.member(chat,user)
                result[prefix+"_role"]=self.role(chat,user)
                title=getattr(member,"custom_title",None)
                result[prefix+"_title"]=title if isinstance(title,str) else "sem título"
            except Exception:
                result[prefix+"_role"]="não confirmado"
                result[prefix+"_title"]="não confirmado"
        return result
