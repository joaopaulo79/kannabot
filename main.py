from modules._config.checagem_autorizacao import Checagens_Autorizacao
from modules.emotes.construcao_acoes import Construcao_Acoes
from modules._config.erros_utilizacao import Erros_Utilizacao
from modules.__init__ import bot, botName, Msg
from modules._config.verificar_button import Log

#FERRAMENTAS
#Telebot
Checar = Checagens_Autorizacao(bot)
Acoes = Construcao_Acoes()   
Erro = Erros_Utilizacao()

#Def que analisa todos os cliques em botões de URL
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
  user = 0
  try:      
    if Log.Ja_Clicou(call.from_user.id):
      print(f"O usuário {call.from_user.username} já clicou no botão.")
      return
      
    if call.data == "Pedir_Desculpa_Punch":       
      if Log.Case_Username_Username(call.from_user.username, call.from_user.id):
        Acoes.Case_Punch_Me_Desculpa()
      else:
        pass     
    elif call.data == "Devolver_Soco":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Revida_Punch()
      else:
        pass
    elif call.data == "Devolver_Tapa":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Revida_Slap()
      else:
        pass
    elif call.data == "Pedir_Desculpa_Slap":
      if Log.Case_Username_Username(call.from_user.username, call.from_user.id):
        Acoes.Case_Slap_Me_Desculpa()
      else:
        pass
    elif call.data == "Rejeitar_Beijo":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Rejeita_Kiss()
      else:
        pass
    elif call.data == "Aceitar_Beijo":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Choque_Kiss()
      else:
        pass
    elif call.data == "Aceitar_Abraço":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Choque_Hug()
      else:
        pass
    elif call.data == "Rejeitar_Abraço":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Rejeita_Hug()
      else:
        pass
    elif call.data == "Aceitar_Carinho":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Choque_Cuddle()
      else:
        pass
    elif call.data == "Rejeitar_Carinho":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Rejeita_Cuddle()
      else:
        pass
    elif call.data == "Aceitar_Cafuné":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Choque_Pat()
      else:
        pass
    elif call.data == "Rejeitar_Cafuné":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Rejeita_Pat()
      else:
        pass
    elif call.data == "Aceitar_Toca_Aqui":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Aceita_Highfive()
      else:
        pass
    elif call.data == "Rejeitar_Toca_Aqui":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Rejeita_Highfive()
      else:
        pass
    elif call.data == "Aceitar_Lambida":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Revida_Lick()
      else:
        pass
    elif call.data == "Rejeitar_Lambida":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Rejeita_Lick()
      else: 
        pass
    elif call.data == "Acenar_de_Volta":
      if Log.Case_Username_TargetUsername(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Devolve_Wave()
      else:
        pass
    elif call.data == "Cumprimentar":
      if Log.Case_Username_Not_Username(call.from_user.username, call.from_user.id):
        user += 1
        Acoes.Case_Welcome_Wave(call.from_user.username)
      else:
        pass
  except:
    Erro.Erro_Button(user)

#Def que analisa o comando /punch
@bot.message_handler(commands=["punch"])
def punch(mensagem):  
    try:
        Erro.Arguments(mensagem)
        Msg.Arguments(mensagem)
        Log.Limpar_Log()

        if Checar.grupo_autorizado(Msg.Grupo_Id()):    
            if Checar.is_admin(mensagem):
              
                if Msg.Target() == None:
                  Erro.Erro_Alvo_Indefinido()
                  
                else:
                  Acoes.Arguments(Msg.Target())
  
                  if f"@{Msg.Username()}" == Msg.Target():
                      Acoes.Case_Auto_Punch()
                  else:
                      if Msg.Target() != botName:
                          Acoes.Case_Punch()
                      else:
                          Acoes.Case_Punch_Me()
            else:
                Erro.Erro_Admin()
        else:
            Erro.Erro_Grupo()
    except:
        Erro.Erro_Comando()

#Def que analisa o comando /slap
@bot.message_handler(commands=["slap"])
def slap(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Acoes.Case_Auto_Slap()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Slap()
            else:
              Acoes.Case_Slap_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /kiss
@bot.message_handler(commands=["kiss"])
def kiss(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):

        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Acoes.Case_Auto_Kiss()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Kiss()
            else:
              Acoes.Case_Kiss_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /shy
@bot.message_handler(commands=["shy"])
def shy(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Acoes.Arguments("Vazio")
          Acoes.Case_Auto_Shy()
          
        else:
          Acoes.Arguments(Msg.Target())         
          if f"@{Msg.Username()}" == Msg.Target():
            Acoes.Case_Auto_Shy()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Shy()
            else:
              Acoes.Case_Shy_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /hug
@bot.message_handler(commands=["hug"])
def hug(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Hug()
            else:
              Acoes.Case_Hug_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /cuddle
@bot.message_handler(commands=["cuddle"])
def cuddle(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Cuddle()
            else:
              Acoes.Case_Cuddle_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /pat
@bot.message_handler(commands=["pat"])
def pat(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Pat()
            else:
              Acoes.Case_Pat_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /push
@bot.message_handler(commands=["push"])
def push(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Push()
            else:
              Acoes.Case_Push_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /stare
@bot.message_handler(commands=["stare"])
def stare(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Acoes.Arguments("Vazio")
          Acoes.Case_Auto_Stare()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Stare()
            else:
              Acoes.Case_Stare_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /highfive
@bot.message_handler(commands=["highfive"])
def highfive(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):    
      if Checar.is_admin(mensagem):
        
        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
  
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Highfive()
            else:
              Acoes.Case_Highfive_Me()
      else:
        Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /poke
@bot.message_handler(commands=["poke"])
def poke(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):
      if Checar.is_admin(mensagem):

        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())

          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Poke()
            else:
              Acoes.Case_Poke_Me()
      else:
          Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /bite
@bot.message_handler(commands=["bite"])
def bite(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):
      if Checar.is_admin(mensagem):

        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())

          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Bite()
            else:
              Acoes.Case_Bite_Me()
      else:
          Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /lick
@bot.message_handler(commands=["lick"])
def lick(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):
      if Checar.is_admin(mensagem):

        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Lick()
            else:
              Acoes.Case_Lick_Me()
      else:
          Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /bonk
@bot.message_handler(commands=["bonk"])
def bonk(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):
      if Checar.is_admin(mensagem):

        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Bonk()
            else:
              Acoes.Case_Bonk_Me()
      else:
          Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /tickle
@bot.message_handler(commands=["tickle"])
def tickle(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):
      if Checar.is_admin(mensagem):

        if Msg.Target() == None:
          Erro.Erro_Alvo_Indefinido()

        else:
          Acoes.Arguments(Msg.Target())
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Tickle()
            else:
              Acoes.Case_Tickle_Me()
      else:
          Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()

#Def que analisa o comando /wave
@bot.message_handler(commands=["wave"])
def wave(mensagem):
  try:
    Erro.Arguments(mensagem)
    Msg.Arguments(mensagem)
    Log.Limpar_Log()

    if Checar.grupo_autorizado(Msg.Grupo_Id()):
      if Checar.is_admin(mensagem):

        if Msg.Target() == None:
          Acoes.Arguments("Vazio")
          Acoes.Case_Auto_Wave()

        else:
          Acoes.Arguments(Msg.Target())
          if f"@{Msg.Username()}" == Msg.Target():
            Erro.Erro_Alvo_Indefinido()
          else:
            if Msg.Target() != botName:
              Acoes.Case_Wave()
            else:
              Acoes.Case_Wave_Me()
      else:
          Erro.Erro_Admin()
    else:
      Erro.Erro_Grupo()
  except:
    Erro.Erro_Comando()
  
bot.polling()