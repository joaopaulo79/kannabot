from html import escape
class Mensagem_Usuario:
    def Arguments(self,mensagem):self.mensagem=mensagem
    def Message(self):return self.mensagem
    def Username(self):return escape(self.mensagem.from_user.username or str(self.mensagem.from_user.id))
    def Grupo_Id(self):return self.mensagem.chat.id
    def Target(self):
        parts=(self.mensagem.text or '').split()
        return escape(parts[1]) if len(parts)>1 else None
    def TargetUsername(self):
        target=self.Target()
        return target.lstrip('@') if target else None
    def User_Id(self):return self.mensagem.from_user.id
