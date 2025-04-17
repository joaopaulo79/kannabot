import json, telebot, threading
from modules.__init__ import Msg, bot

#Arquivos Erros
caminho_erros = "./data/arquivos_json/text_files/mensagens_erro.json"
with open(caminho_erros) as arquivo_erros:
  dados_erros = json.load(arquivo_erros)
  
class Erros_Utilizacao:
  def Arguments(self, mensagem):
    self.mensagem = mensagem
    self.erros = dados_erros

  def Erro_Comando(self):
    temporary_msg = bot.send_message(
      self.mensagem.chat.id, 
      f"@{Msg.Username()}{self.erros['Erro_Comando']}"
    )
    self.Schedule_Delete(temporary_msg)

  def Erro_Grupo(self):
    bot.send_message(
      self.mensagem.chat.id, 
      f"@{Msg.Username()}{self.erros['Erro_Grupo']}"
    )
    bot.leave_chat(Msg.Grupo_Id())

  def Erro_Admin(self):
    temporary_msg = bot.send_message(
      self.mensagem.chat.id, 
      f"@{Msg.Username()}{self.erros['Erro_Admin']}"
    )
    self.Schedule_Delete(temporary_msg)

  def Erro_Button(self, user):
    if user == 0:
      temporary_msg = bot.send_message(
        self.mensagem.chat.id,
        f"@{Msg.Username()}{self.erros['Erro_Button']}"
      )
    else:
      temporary_msg = bot.send_message(
        self.mensagem.chat.id,
        f"{Msg.Target()}{self.erros['Erro_Button']}"
      )
    self.Schedule_Delete(temporary_msg)

  def Erro_Alvo_Indefinido(self):
    temporary_msg = bot.send_message(
      self.mensagem.chat.id, 
      f"@{Msg.Username()}{self.erros['Erro_Alvo_Indefinido']}"
    )
    self.Schedule_Delete(temporary_msg)

  def Schedule_Delete(self, temporary_msg):
    threading.Timer(
      8, self.Delete_Message, 
      args=[temporary_msg.chat.id, 
            temporary_msg.message_id]
    ).start()

  def Delete_Message(self, chat_id, message_id):
    try:
      bot.delete_message(chat_id, message_id)
    except telebot.apihelper.ApiException as e:
      print(f"Erro ao excluir mensagem: {e}")