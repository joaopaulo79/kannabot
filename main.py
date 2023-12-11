import telebot
import random
import re
import time
import requests
import json
import os


#FERRAMENTAS
#Telebot
CHAVE_API = "6694425215:AAHCFFL7bsCuMciKQCjF_U9_-W7OChxalro"
bot = telebot.TeleBot(CHAVE_API)
botName = "@KannaKamui2BOT"

#ChatGPT
chatgpt_key = os.getenv("OPENAI_API_KEY")
link = "https://api.openai.com/v1/chat/completions"
id_modelo = "gpt-3.5-turbo"


#Gifs
punchGifs = [
    "https://c.tenor.com/VrWzG0RWmRQAAAAC/tenor.gif",
    "https://media.tenor.com/44IcPjhMv5oAAAAd/punch-anime.gif",
    "https://media.tenor.com/GuML2yHT58kAAAAd/punch-anime.gif",
    "https://c.tenor.com/gV0dzQ9WZycAAAAC/tenor.gif",
    "https://64.media.tumblr.com/06ff864c72a9cae3e1d2e2b862fdd486/tumblr_o26zo8cpDN1qj5jqso1_540.gif",
    "https://pa1.aminoapps.com/6602/014fb33cd391ee330f6678f6f856e12b90cb26fd_hq.gif",
    "https://pa1.aminoapps.com/5668/41102d6eba9ba3d2812ee4b25ef51ce911d3a0f3_hq.gif",
    "https://i.pinimg.com/originals/8d/50/60/8d50607e59db86b5afcc21304194ba57.gif",
    "https://media.tenor.com/fG4HO_ccb68AAAAC/anime-my-hero-academia.gif",
    "https://giffiles.alphacoders.com/169/169756.gif",
    "https://i.kym-cdn.com/photos/images/newsfeed/001/856/131/1af.gif",
    "https://media.tenor.com/SUmpLViwKxkAAAAC/anime.gif",
    "https://gifdb.com/images/high/one-punch-man-vs-evil-aquatic-water-ewq3dhaq2mstvirj.gif",
    "https://i.pinimg.com/originals/69/42/5c/69425c3f92baabb3b489eb34d27cc6b9.gif",
    "https://c.tenor.com/p_mMicg1pgUAAAAC/tenor.gif",
    "https://media1.tenor.com/m/FKP8EFeGFzEAAAAC/no-chiochannotsuugakuro.gif",
    "https://media1.tenor.com/m/R0Up44dF6iEAAAAC/anime-barakamon.gif",
    "https://media1.tenor.com/m/lWmjgII6fcgAAAAd/saki-saki-mukai-naoya.gif"
]
slapGifs = [
  "https://media1.tenor.com/m/Ws6Dm1ZW_vMAAAAC/girl-slap.gif",
  "https://media1.tenor.com/m/XLchme2ZVkkAAAAC/slap-slapping.gif",
  "https://media1.tenor.com/m/PeJyQRCSHHkAAAAC/saki-saki-mukai-naoya.gif",
  "https://media1.tenor.com/m/zXqvIewp3ToAAAAC/asobi-asobase.gif",
  "https://media1.tenor.com/m/Sp7yE5UzqFMAAAAC/spank-slap.gif",
  "https://media1.tenor.com/m/5jBuDXkDsjYAAAAC/slap.gif",
  "https://media1.tenor.com/m/-erlAPSYWX0AAAAC/anime-slap.gif",
  "https://media1.tenor.com/m/JlfoyfxPbeEAAAAC/seiya-shinchou-yuusha.gif",
  "https://media1.tenor.com/m/HTHoXnBc400AAAAd/in-your-face-slap.gif",
  "https://media1.tenor.com/m/F-EZIgEUxhkAAAAC/slap.gif",
  "https://media1.tenor.com/m/PhXFEGKoiBYAAAAC/the-god-of-high-school-anime.gif",
  "https://media1.tenor.com/m/-wfr09tbkwcAAAAC/discord-anime.gif",
  "https://media1.tenor.com/m/YJ9sYBxEOEQAAAAd/akebi-chan-anime.gif",
  "https://media1.tenor.com/m/8VAgT4nmZ-UAAAAC/slap-anime.gif",
  "https://media1.tenor.com/m/Q_6Bkwxh6k4AAAAC/sae-kashiwagi-anime.gif",
  "https://media1.tenor.com/m/yFnDgvvpwIgAAAAC/slap-touch.gif",
  "https://media1.tenor.com/m/4QvUx8fB6bYAAAAC/hoshizaki-rika-hoshizaki-risa.gif",
  "https://media1.tenor.com/m/24XQteNk3K0AAAAC/anime-girls.gif" 
]

#Labels
headLabel = "============◇============\n"
footerLabel = "\n============◇============"

#Chats
gruposAutorizados = [
  -1001644217218, 
  -1001835855927,
  -1001448376962
]


#Verifica se Kanna é admin do Chat
def isAdmin(admin, mensagem):
  try:
    ApagarMensagemAcao(mensagem)
  except:
    admin = bool(False)
    pass
  return admin


#Verifica se o Texto da Mensagem está vazio ao usar /kannagpt
def VerificaSeVazioGPT(texto):
  return len(texto) > 15


#Se a Kanna não for admin envia uma mensagem de erro
def KannaIsNotAdmin(mensagem):
  bot.reply_to(
      mensagem,
      "Eu preciso ser administrador do Chat para realizar essa ação!")


#Sempre que um Grupo não for autorizado, o bot irá retornar uma mensagem de erro
def GrupoNaoAutorizado(grupo_id, mensagem, username):
  bot.send_message(
      mensagem.chat.id,
      f"@{username}\nDesculpe, mas eu não tenho autorização para interagir com esse grupo. SAINDO!!!"
  )
  bot.leave_chat(grupo_id)


#Sempre que o usuário usar errado o comando de Ação, o bot irá retornar uma mensagem de erro
def AcaoErrada(mensagem, username, acao):
  formaCorreta = f"Tente usar:\n/{acao} @username"
  bot.send_message(
      mensagem.chat.id,
      f"{headLabel}@{username}\nVocê precisa mencionar alguém\npara usar {acao}! {formaCorreta}{footerLabel}"
  )
  ApagarMensagemAcao(mensagem)


#Sempre que o usuário enviar um input vazio ou muito curto ao GPT, o bot irá retornar uma mensagem de erro
def InputVazio(mensagem):
  bot.reply_to(mensagem, "Por favor, insira um texto maior para usar o GPT!")


#Apagar Mensagem de Ação
def ApagarMensagemAcao(mensagem):
  bot.delete_message(mensagem.chat.id, mensagem.id)


#Tentar expulsar o agressor
def TentarExpulsar(mensagem, grupo_id, user_id, username):
  try:
    bot.kick_chat_member(grupo_id, user_id)
    time.sleep(1)
    bot.send_animation(
      mensagem.chat.id,
      "https://media.tenor.com/v-woNII5o9UAAAAC/kanna-kanna-kamui.gif",
      caption= f"{headLabel}Vish, acho que exagerei um\npouquinho na força...\nAlguém sabe trazer de volta?{footerLabel}")
  except:
    bot.send_animation(
      mensagem.chat.id,
      "https://i.pinimg.com/originals/0f/7c/43/0f7c439601af0a7dd18746aa0c8bfd44.gif",
      caption= f"{headLabel}@{username}\nDroga, você era mais forte do\nque eu imaginava!!{footerLabel}")


#Tentando machucar a Kanna
def TentarMachucarKanna(mensagem, username):
  bot.send_animation(
    mensagem.chat.id, 
    "https://gifdb.com/images/high/anime-kanna-crying-ceuw6xkxbdq4pc2y.gif",
    caption=f"{headLabel}@{username}\nPor que está tentando fazer\nisso Onii-chan? Você quer\nmachucar a Kanna?\n\n/sim_machucar_kanna\n/nao_machucar_kanna{footerLabel}")

  
#ChatGPT da Kanna
@bot.message_handler(commands=["kannagpt"])
def kannagpt(mensagem):

  grupo_id = mensagem.chat.id
  username = mensagem.from_user.username

  if VerificaSeVazioGPT(mensagem.text):
    if grupo_id in gruposAutorizados:
      user_input = mensagem.text
      
      body_mensagem = {
        "model": id_modelo,
        "messages": [{"role": "user", "content": user_input}]
      }
      
      body_mensagem = json.dumps(body_mensagem)
  
      headers = {"Authorization": f"Bearer {chatgpt_key}", "Content-Type": "application/json"}
      requisicao = requests.post(link, headers=headers, data=body_mensagem)
  
      resposta = requisicao.json()
      mensagemGPT = resposta["choices"][0]["message"]["content"]
  
      bot.reply_to(mensagem, mensagemGPT)
    else:
      GrupoNaoAutorizado(grupo_id, mensagem, username)
  else:
    InputVazio(mensagem)
    

#Acao machucar a Kanna
@bot.message_handler(commands=["sim_machucar_kanna"])
def sim_machucar_kanna(mensagem):

  grupo_id = mensagem.chat.id
  user_id = mensagem.from_user.id
  username = mensagem.from_user.username

  if grupo_id in gruposAutorizados:
    lista = mensagem.text.split()
    admin = bool(True)
    admin = isAdmin(admin, mensagem)
    
    if admin == True:
      bot.send_animation(
        mensagem.chat.id,
        "https://media.tenor.com/EZX5igQvsxMAAAAC/kanna-beam.gifif",
        caption= f"{headLabel}@{username}\nVocê fez sua escolha! {footerLabel}")
      
      time.sleep(5)
      
      TentarExpulsar(mensagem, grupo_id, user_id, username)
    else:
      KannaIsNotAdmin(mensagem)
  else:
    GrupoNaoAutorizado(grupo_id, mensagem, username)
      

#Ação não machucar a Kanna
@bot.message_handler(commands=["nao_machucar_kanna"])
def nao_machucar_kanna(mensagem):
  
  grupo_id = mensagem.chat.id
  user_id = mensagem.from_user.id
  username = mensagem.from_user.username

  if grupo_id in gruposAutorizados:
    lista = mensagem.text.split()
    admin = bool(True)
    admin = isAdmin(admin, mensagem)

    if admin == True:
      bot.send_animation(
        mensagem.chat.id,
        "https://gifdb.com/images/high/detective-anime-kanna-91unjpt68egwvkc2.gif",
        caption= f"{headLabel}@{username}\nUhmmm... Kanna ta de olho em\nvocê, Onii-chan!!{footerLabel}")
    else:
      KannaIsNotAdmin(mensagem)
  else:
    GrupoNaoAutorizado(grupo_id, mensagem, username)


#Ação de Socar
@bot.message_handler(commands=["punch"])
def punch(mensagem):

  grupo_id = mensagem.chat.id
  user_id = mensagem.from_user.id
  username = mensagem.from_user.username

  if grupo_id in gruposAutorizados:
    lista = mensagem.text.split()
    admin = bool(True)
    admin = isAdmin(admin, mensagem)

    if admin == True:
      if len(lista) > 1:
        target = mensagem.text.split(" ")[1]
        if f"@{username}" == target:
          bot.send_animation(
              mensagem.chat.id,
              "https://media1.tenor.com/m/yGxUGyhsQ_YAAAAd/buu-hitting-self.gif",
              caption=
              f"{headLabel}@{username} socou a si mesmo!\nEsse cara ta bem?? 🤔🤔{footerLabel}"
          )
        else:
          if target != botName:
            bot.send_animation(
              mensagem.chat.id,
              random.choice(punchGifs),
              caption=
              f"{headLabel}@{username} deu um soco em \n{target}! Essa Doeu!!{footerLabel}")
          if target == botName:
            TentarMachucarKanna(mensagem, username)        
      else:
        acao = "punch"
        AcaoErrada(mensagem, username, acao)
    else:
      KannaIsNotAdmin(mensagem)
  else:
    GrupoNaoAutorizado(grupo_id, mensagem, username)


#Ação de Estapear
@bot.message_handler(commands=["slap"])
def slap(mensagem):

  grupo_id = mensagem.chat.id
  user_id = mensagem.from_user.id
  username = mensagem.from_user.username

  if grupo_id in gruposAutorizados:
    lista = mensagem.text.split()
    admin = bool(True)
    admin = isAdmin(admin, mensagem)
    
    if admin == True:
      if len(lista) > 1:
        target = mensagem.text.split(" ")[1]
        if f"@{username}" == target:
          bot.send_animation(
              mensagem.chat.id,
              "https://i.pinimg.com/originals/18/79/f4/1879f4731a02866437f2a99419bfe56b.gif",
              caption=
              f"{headLabel}@{username} estapeou a si mesmo!\nÉ algum método de concentração?? 🤔🤔{footerLabel}"
          )
        else:
          if target != botName:
            bot.send_animation(
              mensagem.chat.id,
              random.choice(slapGifs),
              caption=
              f"{headLabel}@{username} deu um tapa em \n{target}! Toma jeito!!{footerLabel}")
          if target == botName:
            TentarMachucarKanna(mensagem, username)
      else:
        acao = "slap"
        AcaoErrada(mensagem, username, acao)
    else:
      KannaIsNotAdmin(mensagem)
  else:
    GrupoNaoAutorizado(grupo_id, mensagem, username)


#Ação de rolar Dados
@bot.message_handler(commands=["roll"])
def roll(mensagem):
  grupo_id = mensagem.chat.id
  dado = mensagem.text[-5:]
  matches = re.findall(r'\d+', mensagem.text)
  username = mensagem.from_user.username

  if grupo_id in gruposAutorizados:
    if len(matches) > 0:
      dado = int(matches[-1])
      resultado = random.randint(1, dado)
      bot.reply_to(mensagem, str(resultado))
    else:
      bot.reply_to(mensagem,
                   "Nenhum número válido fornecido para lançar os dados.")
  else:
    GrupoNaoAutorizado(grupo_id, mensagem, username)


#Ação de Pervertido
@bot.message_handler(commands=["kannahentai"])
def kannahentai(mensagem):
  grupo_id = mensagem.chat.id
  username = mensagem.from_user.username

  if grupo_id in gruposAutorizados:
    username = mensagem.from_user.username
    hentai = f"{headLabel}@{username}\nOnii-chan hentai! Para de bater\numa pra 2d! Otaku lolicon de\nmerda! 😡😡{footerLabel}"
    bot.send_animation(
        mensagem.chat.id,
        "https://media.tenor.com/ZHgR2wX5M3AAAAAC/kanna-ill-kill-you.gif",
        caption=hentai)
  else:
    GrupoNaoAutorizado(grupo_id, mensagem, username)


bot.polling()
