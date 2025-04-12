from modules.__init__ import Msg, bot, Abrir
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

class Construcao_Acoes:
  def Arguments(self, target):
    self.target = target
    self.mensagem = Msg.Message()
    self.username = Msg.Username()
    self.markup = InlineKeyboardMarkup()
    self.labels = Abrir.Case_Open_Labels()

  def Case_Auto_Punch(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Punch()["auto_punch"]["Gif"],
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Punch()['auto_punch']['Caption']}{self.labels['f']}"
    )

  def Case_Punch(self):
    callback_button = InlineKeyboardButton(
      Abrir.Case_Open_Punch()["action_punch"]["Button"],
      callback_data="Devolver_Soco"
    )
    self.markup.add(callback_button)

    bot.send_animation(
        self.mensagem.chat.id,
        random.choice(Abrir.Case_Open_Punch()["action_punch"]["Gifs"]),
        parse_mode="HTML",
        caption=
        f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Punch()['action_punch']['Caption1']}{self.target}{Abrir.Case_Open_Punch()['action_punch']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Punch_Me(self):
    callback_button = InlineKeyboardButton(
      Abrir.Case_Open_Punch()["punch_me"]["Button"], 
      callback_data="Pedir_Desculpa_Punch"
    )
    self.markup.add(callback_button)

    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Punch()["punch_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Punch()['punch_me']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Punch_Me_Desculpa(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Punch()["punch_me_back"]["Gif"],
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Punch()['punch_me_back']['Caption']}{self.labels['f']}"
    )

  def Case_Revida_Punch(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Punch()["action_punch"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Punch()['action_punch_back']['Caption1']}@{self.username}{Abrir.Case_Open_Punch()['action_punch_back']['Caption2']}{self.labels['f']}"
    )

  def Case_Auto_Slap(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Slap()["auto_slap"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Slap()['auto_slap']['Caption']}{self.labels['f']}"
    )

  def Case_Slap(self):
    callback_button = InlineKeyboardButton(
      Abrir.Case_Open_Slap()["action_slap"]["Button"],
      callback_data="Devolver_Tapa"
    )
    self.markup.add(callback_button)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Slap()["action_slap"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Slap()['action_slap']['Caption1']}{self.target}{Abrir.Case_Open_Slap()['action_slap']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Revida_Slap(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Slap()["action_slap"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Slap()['action_slap_back']['Caption1']}@{self.username}{Abrir.Case_Open_Slap()['action_slap_back']['Caption2']}{self.labels['f']}"
    )

  def Case_Slap_Me(self):
    callback_button = InlineKeyboardButton(
      Abrir.Case_Open_Slap()["slap_me"]["Button"], 
      callback_data="Pedir_Desculpa_Slap"
    )
    self.markup.add(callback_button)

    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Slap()["slap_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Slap()['slap_me']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Slap_Me_Desculpa(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Slap()["slap_me_back"]["Gif"],
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Slap()['slap_me_back']['Caption']}{self.labels['f']}"
    )
  
  def Case_Kiss_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Kiss()["kiss_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Kiss()['kiss_me']['Caption']}{self.labels['f']}"
    )

  def Case_Auto_Kiss(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Kiss()["auto_kiss"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Kiss()['auto_kiss']['Caption']}{self.labels['f']}"
    )

  def Case_Kiss(self):
    callback_button1 = InlineKeyboardButton(
      Abrir.Case_Open_Kiss()["action_kiss"]["Button1"],
      callback_data="Aceitar_Beijo"
    )
    callback_button2 = InlineKeyboardButton(
      Abrir.Case_Open_Kiss()["action_kiss"]["Button2"],
      callback_data="Rejeitar_Beijo"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Kiss()["action_kiss"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Kiss()['action_kiss']['Caption1']}{self.target}{Abrir.Case_Open_Kiss()['action_kiss']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Rejeita_Kiss(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Slap()["action_slap"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Kiss()['action_rejeita_kiss']['Caption1']}@{self.username}{Abrir.Case_Open_Kiss()['action_rejeita_kiss']['Caption2']}{self.labels['f']}"
    )

  def Case_Choque_Kiss(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Shy()["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Kiss()['action_aceita_kiss']['Caption1']}{self.target}{Abrir.Case_Open_Kiss()['action_aceita_kiss']['Caption2']}{self.labels['f']}"
    )

  def Case_Auto_Shy(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Shy()["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Shy()['auto_shy']['Caption1']}{self.labels['f']}"
    )

  def Case_Shy(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Shy()["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Shy()['action_shy']['Caption1']}@{self.username}{Abrir.Case_Open_Shy()['action_shy']['Caption2']}{self.labels['f']}"
    )

  def Case_Shy_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Shy()["shy_me"]["Gif"],
      parse_mode="HTML",
      caption=f"{self.labels['h']}{Abrir.Case_Open_Shy()['shy_me']['Caption1']}@{self.username}{Abrir.Case_Open_Shy()['shy_me']['Caption2']}{self.labels['f']}"
    )

  def Case_Hug(self):
    callback_button1 = InlineKeyboardButton(
      Abrir.Case_Open_Hug()["action_hug"]["Button1"],
      callback_data="Aceitar_Abraço"
    )
    callback_button2 = InlineKeyboardButton(
      Abrir.Case_Open_Hug()["action_hug"]["Button2"],
      callback_data="Rejeitar_Abraço"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Hug()["action_hug"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Hug()['action_hug']['Caption1']}{self.target}{Abrir.Case_Open_Hug()['action_hug']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Hug_Me(self):
    bot.send_animation(
    self.mensagem.chat.id,
    Abrir.Case_Open_Hug()["hug_me"]["Gif"],
    caption=
    f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Hug()['hug_me']['Caption']}{self.labels['f']}"
    )

  def Case_Choque_Hug(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Shy()["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Hug()['action_aceita_hug']['Caption1']}{self.target}{Abrir.Case_Open_Hug()['action_aceita_hug']['Caption2']}{self.labels['f']}"
    )

  def Case_Rejeita_Hug(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Push()["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Hug()['action_rejeita_hug']['Caption1']}@{self.username}{Abrir.Case_Open_Hug()['action_rejeita_hug']['Caption2']}{self.labels['f']}"
    )

  def Case_Cuddle(self):
    callback_button1 = InlineKeyboardButton(
      Abrir.Case_Open_Cuddle()["action_cuddle"]["Button1"],
      callback_data="Aceitar_Carinho"
    )
    callback_button2 = InlineKeyboardButton(
      Abrir.Case_Open_Cuddle()["action_cuddle"]["Button2"],
      callback_data="Rejeitar_Carinho"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Cuddle()["action_cuddle"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Cuddle()['action_cuddle']['Caption1']}{self.target}{Abrir.Case_Open_Cuddle()['action_cuddle']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Cuddle_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Cuddle()["cuddle_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Cuddle()['cuddle_me']['Caption']}{self.labels['f']}"
    )

  def Case_Choque_Cuddle(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Shy()["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Cuddle()['action_aceita_cuddle']['Caption1']}{self.target}{Abrir.Case_Open_Cuddle()['action_aceita_cuddle']['Caption2']}{self.labels['f']}"
    )

  def Case_Rejeita_Cuddle(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Push()["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Cuddle()['action_rejeita_cuddle']['Caption1']}@{self.username}{Abrir.Case_Open_Cuddle()['action_rejeita_cuddle']['Caption2']}{self.labels['f']}"
    )

  def Case_Pat(self):
    callback_button1 = InlineKeyboardButton(
      Abrir.Case_Open_Pat()["action_pat"]["Button1"],
      callback_data="Aceitar_Cafuné"
    )
    callback_button2 = InlineKeyboardButton(
      Abrir.Case_Open_Pat()["action_pat"]["Button2"],
      callback_data="Rejeitar_Cafuné"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Pat()["action_pat"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Pat()['action_pat']['Caption1']}{self.target}{Abrir.Case_Open_Pat()['action_pat']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Pat_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Pat()["pat_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Pat()['pat_me']['Caption']}{self.labels['f']}"
    )

  def Case_Choque_Pat(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Shy()["emote_shy"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Pat()['action_aceita_pat']['Caption1']}{self.target}{Abrir.Case_Open_Pat()['action_aceita_pat']['Caption2']}{self.labels['f']}"
    )

  def Case_Rejeita_Pat(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Push()["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Pat()['action_rejeita_pat']['Caption1']}@{self.username}{Abrir.Case_Open_Pat()['action_rejeita_pat']['Caption2']}{self.labels['f']}"
    )

  def Case_Push(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Push()["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Push()['action_push']['Caption1']}{self.target}{Abrir.Case_Open_Push()['action_push']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Push_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Push()["push_me"]["Gif"],
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Push()['push_me']['Caption']}{self.labels['f']}"
    )

  def Case_Auto_Stare(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Stare()["action_stare"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Stare()['auto_stare']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Stare(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Stare()["action_stare"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}{self.target}{Abrir.Case_Open_Stare()['action_stare']['Caption1']}@{self.username}{Abrir.Case_Open_Stare()['action_stare']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )
  
  def Case_Stare_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Stare()["stare_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Stare()['stare_me']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Highfive(self):
    callback_button1 = InlineKeyboardButton(
      Abrir.Case_Open_Highfive()["action_highfive"]["Button1"],
      callback_data="Aceitar_Toca_Aqui"
    )
    callback_button2 = InlineKeyboardButton(
      Abrir.Case_Open_Highfive()["action_highfive"]["Button2"],
      callback_data="Rejeitar_Toca_Aqui"
    )
    self.markup.add(callback_button1, callback_button2)

    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Highfive()["action_highfive"]["Gif_Convite"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Highfive()['action_highfive']['Caption1']}{self.target}{Abrir.Case_Open_Highfive()['action_highfive']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Highfive_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Highfive()["highfive_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Highfive()['highfive_me']['Caption']}{self.labels['f']}"
    )

  def Case_Aceita_Highfive(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Highfive()["response_highfive"]["Gifs_Aceito"]),
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Highfive()['response_highfive']['Caption1']}@{self.username}{Abrir.Case_Open_Highfive()['response_highfive']['Caption2']}{self.labels['f']}"
    )

  def Case_Rejeita_Highfive(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Highfive()["reject_highfive"]["Gifs_Negado"],
      parse_mode="HTML",
      caption=f"{self.labels['h']}{self.target}{Abrir.Case_Open_Highfive()['reject_highfive']['Caption1']}@{self.username}{Abrir.Case_Open_Highfive()['reject_highfive']['Caption2']}{self.labels['f']}"
    )

  def Case_Poke(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Poke()["action_poke"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Poke()['action_poke']['Caption1']}{self.target}{Abrir.Case_Open_Poke()['action_poke']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Poke_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Poke()["poke_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Poke()['poke_me']['Caption']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Bite(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Bite()["action_bite"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Bite()['action_bite']['Caption1']}{self.target}{Abrir.Case_Open_Bite()['action_bite']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Bite_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Bite()["bite_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}{Abrir.Case_Open_Bite()['bite_me']['Caption1']}@{self.username}{Abrir.Case_Open_Bite()['bite_me']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Lick(self):
    callback_button1 = InlineKeyboardButton(
      Abrir.Case_Open_Lick()["action_lick"]["Button1"],
      callback_data="Aceitar_Lambida"
    )
    callback_button2 = InlineKeyboardButton(
      Abrir.Case_Open_Lick()["action_lick"]["Button2"],
      callback_data="Rejeitar_Lambida"
    )
    self.markup.add(callback_button1, callback_button2)
    
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Lick()["action_lick"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Lick()['action_lick']['Caption1']}{self.target}{Abrir.Case_Open_Lick()['action_lick']['Caption2']}{self.labels['f']}",
      reply_markup=self.markup
    )

  def Case_Lick_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Lick()["lick_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}{Abrir.Case_Open_Lick()['lick_me']['Caption1']}@{self.username}{Abrir.Case_Open_Lick()['lick_me']['Caption2']}{self.labels['f']}"
    )

  def Case_Revida_Lick(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Lick()["action_revida_lick"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}{self.target}{Abrir.Case_Open_Lick()['action_revida_lick']['Caption1']}@{self.username}{Abrir.Case_Open_Lick()['action_revida_lick']['Caption2']}{self.labels['f']}"
    )

  def Case_Rejeita_Lick(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Push()["action_push"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}{self.target}{Abrir.Case_Open_Lick()['action_rejeita_lick']['Caption1']}@{self.username}{Abrir.Case_Open_Lick()['action_rejeita_lick']['Caption2']}{self.labels['f']}"
    )

  def Case_Bonk(self):
    bot.send_animation(
      self.mensagem.chat.id,
      random.choice(Abrir.Case_Open_Bonk()["action_bonk"]["Gifs"]),
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Bonk()['action_bonk']['Caption1']}{self.target}{Abrir.Case_Open_Bonk()['action_bonk']['Caption2']}{self.labels['f']}"
    )

  def Case_Bonk_Me(self):
    bot.send_animation(
      self.mensagem.chat.id,
      Abrir.Case_Open_Bonk()["bonk_me"]["Gif"],
      parse_mode="HTML",
      caption=
      f"{self.labels['h']}@{self.username}{Abrir.Case_Open_Bonk()['bonk_me']['Caption1']}{self.labels['f']}"
    )