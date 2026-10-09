import json
from pathlib import Path
RESOURCE_ROOT = Path(__file__).resolve().parents[1] / "resources"

class Abrir_Arquivos_Emotes:
  def Case_Open_Labels(self):
    caminho_labels = RESOURCE_ROOT / "text_files/labels.json"
    with open(caminho_labels, encoding="utf-8") as arquivo_labels:
      dados_labels = json.load(arquivo_labels)
    return dados_labels

  def Case_Open_Punch(self):
    caminho_gif_punch = RESOURCE_ROOT / "action_files/punch.json"
    with open(caminho_gif_punch, encoding="utf-8") as arquivo_gif_punch:
      dados_gif_punch = json.load(arquivo_gif_punch)
    return dados_gif_punch

  def Case_Open_Slap(self):
    caminho_gif_slap = RESOURCE_ROOT / "action_files/slap.json"
    with open(caminho_gif_slap, encoding="utf-8") as arquivo_gif_slap:
      dados_gif_slap = json.load(arquivo_gif_slap)
    return dados_gif_slap

  def Case_Open_Kiss(self):
    caminho_gif_kiss = RESOURCE_ROOT / "action_files/kiss.json"
    with open(caminho_gif_kiss, encoding="utf-8") as arquivo_gif_kiss:
      dados_gif_kiss = json.load(arquivo_gif_kiss)
    return dados_gif_kiss

  def Case_Open_Shy(self):
    caminho_gif_shy = RESOURCE_ROOT / "action_files/shy.json"
    with open(caminho_gif_shy, encoding="utf-8") as arquivo_gif_shy:
      dados_gif_shy = json.load(arquivo_gif_shy)
    return dados_gif_shy

  def Case_Open_Hug(self):
    caminho_gif_hug = RESOURCE_ROOT / "action_files/hug.json"
    with open(caminho_gif_hug, encoding="utf-8") as arquivo_gif_hug:
      dados_gif_hug = json.load(arquivo_gif_hug)
    return dados_gif_hug

  def Case_Open_Cuddle(self):
    caminho_gif_cuddle = RESOURCE_ROOT / "action_files/cuddle.json"
    with open(caminho_gif_cuddle, encoding="utf-8") as arquivo_gif_cuddle:
      dados_gif_cuddle = json.load(arquivo_gif_cuddle)
    return dados_gif_cuddle

  def Case_Open_Pat(self):
    caminho_gif_pat = RESOURCE_ROOT / "action_files/pat.json"
    with open(caminho_gif_pat, encoding="utf-8") as arquivo_gif_pat:
      dados_gif_pat = json.load(arquivo_gif_pat)
    return dados_gif_pat

  def Case_Open_Push(self):
    caminho_gif_push = RESOURCE_ROOT / "action_files/push.json"
    with open(caminho_gif_push, encoding="utf-8") as arquivo_gif_push:
      dados_gif_push = json.load(arquivo_gif_push)
    return dados_gif_push

  def Case_Open_Stare(self):
    caminho_gif_stare = RESOURCE_ROOT / "action_files/stare.json"
    with open(caminho_gif_stare, encoding="utf-8") as arquivo_gif_stare:
      dados_gif_stare = json.load(arquivo_gif_stare)
    return dados_gif_stare

  def Case_Open_Highfive(self):
    caminho_gif_highfive = RESOURCE_ROOT / "action_files/highfive.json"
    with open(caminho_gif_highfive, encoding="utf-8") as arquivo_gif_highfive:
      dados_gif_highfive = json.load(arquivo_gif_highfive)
    return dados_gif_highfive

  def Case_Open_Poke(self):
    caminho_gif_poke = RESOURCE_ROOT / "action_files/poke.json"
    with open(caminho_gif_poke, encoding="utf-8") as arquivo_gif_poke:
      dados_gif_poke = json.load(arquivo_gif_poke)
    return dados_gif_poke

  def Case_Open_Bite(self):
    caminho_gif_bite = RESOURCE_ROOT / "action_files/bite.json"
    with open(caminho_gif_bite, encoding="utf-8") as arquivo_gif_bite:
      dados_gif_bite = json.load(arquivo_gif_bite)
    return dados_gif_bite

  def Case_Open_Lick(self):
    caminho_gif_lick = RESOURCE_ROOT / "action_files/lick.json"
    with open(caminho_gif_lick, encoding="utf-8") as arquivo_gif_lick:
      dados_gif_lick = json.load(arquivo_gif_lick)
    return dados_gif_lick

  def Case_Open_Bonk(self):
    caminho_gif_bonk = RESOURCE_ROOT / "action_files/bonk.json"
    with open(caminho_gif_bonk, encoding="utf-8") as arquivo_gif_bonk:
      dados_gif_bonk = json.load(arquivo_gif_bonk)
    return dados_gif_bonk

  def Case_Open_Tickle(self):
    caminho_gif_tickle = RESOURCE_ROOT / "action_files/tickle.json"
    with open(caminho_gif_tickle, encoding="utf-8") as arquivo_gif_tickle:
      dados_gif_tickle = json.load(arquivo_gif_tickle)
    return dados_gif_tickle

  def Case_Open_Wave(self):
    caminho_gif_wave = RESOURCE_ROOT / "action_files/wave.json"
    with open(caminho_gif_wave, encoding="utf-8") as arquivo_gif_wave:
      dados_gif_wave = json.load(arquivo_gif_wave)
    return dados_gif_wave

  def Case_Open_Cry(self):
    caminho_gif_cry = RESOURCE_ROOT / "action_files/cry.json"
    with open(caminho_gif_cry, encoding="utf-8") as arquivo_gif_cry:
      dados_gif_cry = json.load(arquivo_gif_cry)
    return dados_gif_cry
