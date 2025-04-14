import json

class Abrir_Arquivos_Emotes:
  def Case_Open_Labels(self):
    caminho_labels = "./arquivos_json/text_files/labels.json"
    with open(caminho_labels) as arquivo_labels:
      dados_labels = json.load(arquivo_labels)
    return dados_labels

  def Case_Open_Punch(self):
    caminho_gif_punch = "./arquivos_json/action_files/punch.json"
    with open(caminho_gif_punch) as arquivo_gif_punch:
      dados_gif_punch = json.load(arquivo_gif_punch)
    return dados_gif_punch

  def Case_Open_Slap(self):
    caminho_gif_slap = "./arquivos_json/action_files/slap.json"
    with open(caminho_gif_slap) as arquivo_gif_slap:
      dados_gif_slap = json.load(arquivo_gif_slap)
    return dados_gif_slap

  def Case_Open_Kiss(self):
    caminho_gif_kiss = "./arquivos_json/action_files/kiss.json"
    with open(caminho_gif_kiss) as arquivo_gif_kiss:
      dados_gif_kiss = json.load(arquivo_gif_kiss)
    return dados_gif_kiss

  def Case_Open_Shy(self):
    caminho_gif_shy = "./arquivos_json/action_files/shy.json"
    with open(caminho_gif_shy) as arquivo_gif_shy:
      dados_gif_shy = json.load(arquivo_gif_shy)
    return dados_gif_shy

  def Case_Open_Hug(self):
    caminho_gif_hug = "./arquivos_json/action_files/hug.json"
    with open(caminho_gif_hug) as arquivo_gif_hug:
      dados_gif_hug = json.load(arquivo_gif_hug)
    return dados_gif_hug

  def Case_Open_Cuddle(self):
    caminho_gif_cuddle = "./arquivos_json/action_files/cuddle.json"
    with open(caminho_gif_cuddle) as arquivo_gif_cuddle:
      dados_gif_cuddle = json.load(arquivo_gif_cuddle)
    return dados_gif_cuddle

  def Case_Open_Pat(self):
    caminho_gif_pat = "./arquivos_json/action_files/pat.json"
    with open(caminho_gif_pat) as arquivo_gif_pat:
      dados_gif_pat = json.load(arquivo_gif_pat)
    return dados_gif_pat

  def Case_Open_Push(self):
    caminho_gif_push = "./arquivos_json/action_files/push.json"
    with open(caminho_gif_push) as arquivo_gif_push:
      dados_gif_push = json.load(arquivo_gif_push)
    return dados_gif_push

  def Case_Open_Stare(self):
    caminho_gif_stare = "./arquivos_json/action_files/stare.json"
    with open(caminho_gif_stare) as arquivo_gif_stare:
      dados_gif_stare = json.load(arquivo_gif_stare)
    return dados_gif_stare

  def Case_Open_Highfive(self):
    caminho_gif_highfive = "./arquivos_json/action_files/highfive.json"
    with open(caminho_gif_highfive) as arquivo_gif_highfive:
      dados_gif_highfive = json.load(arquivo_gif_highfive)
    return dados_gif_highfive

  def Case_Open_Poke(self):
    caminho_gif_poke = "./arquivos_json/action_files/poke.json"
    with open(caminho_gif_poke) as arquivo_gif_poke:
      dados_gif_poke = json.load(arquivo_gif_poke)
    return dados_gif_poke

  def Case_Open_Bite(self):
    caminho_gif_bite = "./arquivos_json/action_files/bite.json"
    with open(caminho_gif_bite) as arquivo_gif_bite:
      dados_gif_bite = json.load(arquivo_gif_bite)
    return dados_gif_bite

  def Case_Open_Lick(self):
    caminho_gif_lick = "./arquivos_json/action_files/lick.json"
    with open(caminho_gif_lick) as arquivo_gif_lick:
      dados_gif_lick = json.load(arquivo_gif_lick)
    return dados_gif_lick 

  def Case_Open_Bonk(self):
    caminho_gif_bonk = "./arquivos_json/action_files/bonk.json"
    with open(caminho_gif_bonk) as arquivo_gif_bonk:
      dados_gif_bonk = json.load(arquivo_gif_bonk)
    return dados_gif_bonk

  def Case_Open_Tickle(self):
    caminho_gif_tickle = "./arquivos_json/action_files/tickle.json"
    with open(caminho_gif_tickle) as arquivo_gif_tickle:
      dados_gif_tickle = json.load(arquivo_gif_tickle)
    return dados_gif_tickle

  def Case_Open_Wave(self):
    caminho_gif_wave = "./arquivos_json/action_files/wave.json"
    with open(caminho_gif_wave) as arquivo_gif_wave:
      dados_gif_wave = json.load(arquivo_gif_wave)
    return dados_gif_wave