from modules.__init__ import Msg, bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random, json


#Arquivos Punch 
caminho_gif_punch = "./arquivos_json/action_files/punch.json"
with open(caminho_gif_punch) as arquivo_gif_punch:
  dados_gif_punch = json.load(arquivo_gif_punch)

#Arquivos Slap
caminho_gif_slap = "./arquivos_json/action_files/slap.json"
with open(caminho_gif_slap) as arquivo_gif_slap:
  dados_gif_slap = json.load(arquivo_gif_slap)

#Arquivos Kiss
caminho_gif_kiss = "./arquivos_json/action_files/kiss.json"
with open(caminho_gif_kiss) as arquivo_gif_kiss:
  dados_gif_kiss = json.load(arquivo_gif_kiss)

#Arquivos Shy
caminho_gif_shy = "./arquivos_json/action_files/shy.json"
with open(caminho_gif_shy) as arquivo_gif_shy:
  dados_gif_shy = json.load(arquivo_gif_shy)

#Arquivos Hug
caminho_gif_hug = "./arquivos_json/action_files/hug.json"
with open(caminho_gif_hug) as arquivo_gif_hug:
  dados_gif_hug = json.load(arquivo_gif_hug)

#Arquivos Cuddle
caminho_gif_cuddle = "./arquivos_json/action_files/cuddle.json"
with open(caminho_gif_cuddle) as arquivo_gif_cuddle:
  dados_gif_cuddle = json.load(arquivo_gif_cuddle)

#Arquivos Pat
caminho_gif_pat = "./arquivos_json/action_files/pat.json"
with open(caminho_gif_pat) as arquivo_gif_pat:
  dados_gif_pat = json.load(arquivo_gif_pat)

#Arquivos Push
caminho_gif_push = "./arquivos_json/action_files/push.json"
with open(caminho_gif_push) as arquivo_gif_push:
  dados_gif_push = json.load(arquivo_gif_push)

#Arquivos Stare
caminho_gif_stare = "./arquivos_json/action_files/stare.json"
with open(caminho_gif_stare) as arquivo_gif_stare:
  dados_gif_stare = json.load(arquivo_gif_stare)

#Arquivos Highfive
caminho_gif_highfive = "./arquivos_json/action_files/highfive.json"
with open(caminho_gif_highfive) as arquivo_gif_highfive:
  dados_gif_highfive = json.load(arquivo_gif_highfive)

#Arquivos Poke
caminho_gif_poke = "./arquivos_json/action_files/poke.json"
with open(caminho_gif_poke) as arquivo_gif_poke:
  dados_gif_poke = json.load(arquivo_gif_poke)

#Arquivos Labels
caminho_labels = "./arquivos_json/text_files/labels.json"
with open(caminho_labels) as arquivo_labels:
  dados_labels = json.load(arquivo_labels)

class Construcao_Acoes:
  def Arguments(self, target):
    self.mensagem = Msg.Message()
    self.username = Msg.Username()
    self.markup = InlineKeyboardMarkup()
    self.target = target
    self.labels = dados_labels
    self.punch = dados_gif_punch
    self.slap = dados_gif_slap
    self.kiss = dados_gif_kiss
    self.shy = dados_gif_shy
    self.hug = dados_gif_hug
    self.cuddle = dados_gif_cuddle
    self.pat = dados_gif_pat
    self.push = dados_gif_push
    self.stare = dados_gif_stare
    self.highfive = dados_gif_highfive
    self.poke = dados_gif_poke

  def Case_Auto_Punch(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.punch["auto_punch"]["Gif"],
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{self.punch['auto_punch']['Caption']}{self.labels['f']}"
    )

  def Case_Punch(self):
    callback_button = InlineKeyboardButton(
      self.punch["action_punch"]["Button"],
      callback_data="Devolver_Soco"
    )
    self.markup.add(callback_button)

    bot.send_animation(
        self.mensagem.chat.id,
        random.choice(self.punch["action_punch"]["Gifs"]),
        parse_mode="HTML",
        caption=
        f"{self.labels['h']}@{self.username}{self.punch['action_punch']['Caption1']}{self.target}{self.punch['action_punch']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Punch_Me(self):
    callback_button = InlineKeyboardButton(
      self.punch["punch_me"]["Button"], 
      callback_data="Pedir_Desculpa"
    )
    self.markup.add(callback_button)

    bot.send_animation(
      self.mensagem.chat.id,
      self.punch["punch_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{self.punch['punch_me']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Punch_Me_Desculpa(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.punch["punch_me_back"]["Gif"],
      caption=f"{self.labels['h']}@{self.username}{self.punch['punch_me_back']['Caption']}{self.labels['f']}"
    )

  def Case_Revida_Punch(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.punch["action_punch"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.punch['action_punch']['Caption1']}@{self.username}{self.punch['action_punch']['Caption2']}{self.labels['f']}"
    )

  def Case_Auto_Slap(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.slap["auto_slap"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.slap['auto_slap']['Caption']}{self.labels['f']}"
    )

  def Case_Slap(self):
    callback_button = InlineKeyboardButton(
      self.slap["action_slap"]["Button"],
      callback_data="Devolver_Tapa"
    )
    self.markup.add(callback_button)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.slap["action_slap"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.slap['action_slap']['Caption1']}{self.target}{self.slap['action_slap']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Revida_Slap(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.slap["action_slap"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.slap['action_slap']['Caption1']}@{self.username}{self.slap['action_slap']['Caption2']}{self.labels['f']}"
    )

  def Case_Kiss_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.kiss["kiss_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{self.kiss['kiss_me']['Caption']}{self.labels['f']}"
    )

  def Case_Auto_Kiss(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.kiss["auto_kiss"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.kiss['auto_kiss']['Caption']}{self.labels['f']}"
    )

  def Case_Kiss(self):
    callback_button1 = InlineKeyboardButton(
      self.kiss["action_kiss"]["Button1"],
      callback_data="Aceitar_Beijo"
    )
    callback_button2 = InlineKeyboardButton(
      self.kiss["action_kiss"]["Button2"],
      callback_data="Rejeitar_Beijo"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.kiss["action_kiss"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.kiss['action_kiss']['Caption1']}{self.target}{self.kiss['action_kiss']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Rejeita_Kiss(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.slap["action_slap"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.kiss['action_kiss']['Caption3']}@{self.username}{self.kiss['action_kiss']['Caption4']}{self.labels['f']}"
    )

  def Case_Choque_Kiss(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.shy["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{self.kiss['action_kiss']['Caption5']}{self.target}{self.kiss['action_kiss']['Caption6']}{self.labels['f']}"
    )

  def Case_Auto_Shy(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.shy["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{self.shy['auto_shy']['Caption1']}{self.labels['f']}"
    )

  def Case_Shy_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.shy["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.shy['shy_me']['Caption1']}@{self.username}{self.shy['shy_me']['Caption2']}{self.labels['f']}"
    )

  def Case_Hug(self):
    callback_button1 = InlineKeyboardButton(
      self.hug["action_hug"]["Button1"],
      callback_data="Aceitar_Abraço"
    )
    callback_button2 = InlineKeyboardButton(
      self.hug["action_hug"]["Button2"],
      callback_data="Rejeitar_Abraço"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.hug["action_hug"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.hug['action_hug']['Caption1']}{self.target}{self.hug['action_hug']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Hug_Me(self):
    bot.send_animation(
    self.mensagem.chat.id,
    self.hug["hug_me"]["Gif"],
    caption=
    f"{self.labels['h']}@{self.username}{self.hug['hug_me']['Caption']}{self.labels['f']}"
    )

  def Case_Choque_Hug(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.shy["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{self.hug['action_hug']['Caption5']}{self.target}{self.hug['action_hug']['Caption6']}{self.labels['f']}"
    )

  def Case_Rejeita_Hug(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.push["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.hug['action_hug']['Caption3']}@{self.username}{self.hug['action_hug']['Caption4']}{self.labels['f']}"
    )

  def Case_Cuddle(self):
    callback_button1 = InlineKeyboardButton(
      self.cuddle["action_cuddle"]["Button1"],
      callback_data="Aceitar_Carinho"
    )
    callback_button2 = InlineKeyboardButton(
      self.cuddle["action_cuddle"]["Button2"],
      callback_data="Rejeitar_Carinho"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.cuddle["action_cuddle"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.cuddle['action_cuddle']['Caption1']}{self.target}{self.cuddle['action_cuddle']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Cuddle_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.cuddle["cuddle_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.cuddle['cuddle_me']['Caption']}{self.labels['f']}"
    )

  def Case_Choque_Cuddle(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.shy["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{self.cuddle['action_cuddle']['Caption5']}{self.target}{self.cuddle['action_cuddle']['Caption6']}{self.labels['f']}"
    )

  def Case_Rejeita_Cuddle(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.push["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.cuddle['action_cuddle']['Caption3']}@{self.username}{self.cuddle['action_cuddle']['Caption4']}{self.labels['f']}"
    )

  def Case_Pat(self):
    callback_button1 = InlineKeyboardButton(
      self.pat["action_pat"]["Button1"],
      callback_data="Aceitar_Cafuné"
    )
    callback_button2 = InlineKeyboardButton(
      self.pat["action_pat"]["Button2"],
      callback_data="Rejeitar_Cafuné"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.pat["action_pat"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.pat['action_pat']['Caption1']}{self.target}{self.pat['action_pat']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Pat_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.pat["pat_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{self.pat['pat_me']['Caption']}{self.labels['f']}"
    )

  def Case_Choque_Pat(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.shy["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{self.pat['action_pat']['Caption5']}{self.target}{self.pat['action_pat']['Caption6']}{self.labels['f']}"
    )

  def Case_Rejeita_Pat(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.push["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.pat['action_pat']['Caption3']}@{self.username}{self.pat['action_pat']['Caption4']}{self.labels['f']}"
    )

  def Case_Push(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.push["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.push['action_push']['Caption1']}{self.target}{self.push['action_push']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Push_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.push["push_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{self.push['push_me']['Caption']}{self.labels['f']}"
    )

  def Case_Auto_Stare(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.stare["action_stare"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.stare['auto_stare']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Stare(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.stare["action_stare"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}{self.target}{self.stare['action_stare']['Caption1']}@{self.username}{self.stare['action_stare']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )
  
  def Case_Stare_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.stare["stare_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.stare['stare_me']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Highfive(self):
    callback_button1 = InlineKeyboardButton(
      self.highfive["action_highfive"]["Button1"],
      callback_data="Aceitar_Toca_Aqui"
    )
    callback_button2 = InlineKeyboardButton(
      self.highfive["action_highfive"]["Button2"],
      callback_data="Rejeitar_Toca_Aqui"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      self.highfive["action_highfive"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.highfive['action_highfive']['Caption1']}{self.target}{self.highfive['action_highfive']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Highfive_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.highfive["highfive_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.highfive['highfive_me']['Caption']}{self.labels['f']}"
    )

  def Case_Aceita_Highfive(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.highfive["action_highfive"]["Gifs_Aceito"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.highfive['action_highfive']['Caption3']}@{self.username}{self.highfive['action_highfive']['Caption4']}{self.labels['f']}"
    )

  def Case_Rejeita_Highfive(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.highfive["action_highfive"]["Gifs_Negado"],
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{self.highfive['action_highfive']['Caption5']}@{self.username}{self.highfive['action_highfive']['Caption6']}{self.labels['f']}"
    )

  def Case_Poke(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(self.poke["action_poke"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.poke['action_poke']['Caption1']}{self.target}{self.poke['action_poke']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Poke_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      self.poke["poke_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{self.poke['poke_me']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )