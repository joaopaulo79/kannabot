class Mensagem_Usuario:
  def Arguments(self, mensagem):
    self.mensagem = mensagem

  def Message(self):
    return self.mensagem

  def Username(self):
    self.username = self.mensagem.from_user.username
    return self.username

  def Grupo_Id(self):
    self.grupo_id = self.mensagem.chat.id
    return self.grupo_id

  def Target(self):
    parts = self.mensagem.text.split()
    if len(parts) > 1:
        self.target = parts[1]
        return self.target
    else:
        return None
      
  def TargetUsername(self):
    self.targetusername = self.mensagem.text.split(" @")[1]
    return self.targetusername