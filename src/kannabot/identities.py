"""Observed group identities; username lookup always revalidates by numeric ID."""
import copy
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from telebot.handler_backends import ContinueHandling

class Identities:
    def __init__(self,bot,groups,path,clock=None,ttl=86400,capacity=10000):
        self.bot,self.groups,self.path=bot,frozenset(groups),Path(path)
        self.clock=clock or time.time
        self.ttl,self.capacity=ttl,capacity
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("CREATE TABLE IF NOT EXISTS identities(chat_id INTEGER NOT NULL,user_id INTEGER NOT NULL,username TEXT,observed_at REAL NOT NULL,PRIMARY KEY(chat_id,user_id))")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS identity_username ON identities(chat_id,username) WHERE username IS NOT NULL")
    def observe_user(self,chat,user):
        user_id=getattr(user,"id",None)
        if chat not in self.groups or type(user_id) is not int or getattr(user,"is_bot",False):return
        username=getattr(user,"username",None)
        username=username.casefold() if isinstance(username,str) and re.fullmatch(r"[A-Za-z0-9_]{1,32}",username) else None
        with closing(sqlite3.connect(self.path)) as db,db:
            if username:db.execute("UPDATE identities SET username=NULL WHERE chat_id=? AND username=? AND user_id!=?",(chat,username,user_id))
            db.execute("INSERT INTO identities VALUES(?,?,?,?) ON CONFLICT(chat_id,user_id) DO UPDATE SET username=excluded.username,observed_at=excluded.observed_at",(chat,user_id,username,self.clock()))
            db.execute("DELETE FROM identities WHERE chat_id=? AND user_id NOT IN (SELECT user_id FROM identities WHERE chat_id=? ORDER BY observed_at DESC,user_id DESC LIMIT ?)",(chat,chat,self.capacity))
    def observe(self,message):
        if getattr(message,"sender_chat",None) is None:self.observe_user(message.chat.id,getattr(message,"from_user",None))
        reply=getattr(message,"reply_to_message",None)
        if reply and getattr(reply,"sender_chat",None) is None and getattr(getattr(reply,"chat",None),"id",message.chat.id)==message.chat.id:
            self.observe_user(message.chat.id,getattr(reply,"from_user",None))
    def resolve(self,chat,username,allow_banned=False):
        requested=username.lstrip("@").casefold()
        if chat not in self.groups or not re.fullmatch(r"[a-z0-9_]{1,32}",requested):raise ValueError("Grupo ou username inválido.")
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT user_id,observed_at FROM identities WHERE chat_id=? AND username=?",(chat,requested)).fetchone()
        if not row or row[1]<self.clock()-self.ttl:raise ValueError("🔎 Não consegui identificar esse username com segurança. Responda à mensagem da pessoa.")
        try:member=self.bot.get_chat_member(chat,row[0])
        except Exception:raise ValueError("🔎 Não foi possível confirmar o alvo. Nenhuma ação foi executada.") from None
        user=getattr(member,"user",None)
        current=getattr(user,"username",None)
        valid_status=member.status in ("member","administrator","creator") or (member.status=="restricted" and getattr(member,"is_member",False) is True) or (allow_banned and member.status=="kicked")
        if getattr(user,"id",None)!=row[0] or not isinstance(current,str) or current.casefold()!=requested or getattr(user,"is_bot",False) or not valid_status:
            # Invalidate a stale association but do not learn an unverified new user.
            with closing(sqlite3.connect(self.path)) as db,db:db.execute("UPDATE identities SET username=NULL WHERE chat_id=? AND user_id=?",(chat,row[0]))
            raise ValueError("🔎 O username ou a participação do alvo mudou. Responda a uma mensagem válida da pessoa.")
        self.observe_user(chat,user)
        return user
    def prepare(self,message,command):
        self.observe(message)
        parts=(getattr(message,"text","") or "").split(maxsplit=1)
        payload=parts[1] if len(parts)>1 else ""
        tokens=payload.split(maxsplit=1)
        if not tokens or not tokens[0].startswith("@"):return message
        if command in ("delete","delwarn"):raise ValueError("🧹 Responda à mensagem que deseja apagar, sem selecionar somente um username.")
        user=self.resolve(message.chat.id,tokens[0],allow_banned=command=="unban")
        reply=getattr(message,"reply_to_message",None)
        if reply and getattr(getattr(reply,"from_user",None),"id",None)!=user.id:
            raise ValueError("O username e a resposta indicam pessoas diferentes.")
        clone=copy.copy(message)
        clone.text=parts[0]+(" "+tokens[1] if len(tokens)>1 else "")
        clone.reply_to_message=reply or SimpleNamespace(chat=message.chat,message_id=None,from_user=user,sender_chat=None)
        return clone
    def username(self,chat,user):
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT username FROM identities WHERE chat_id=? AND user_id=?",(chat,user)).fetchone()
            return row[0] if row else None

def register(bot,identities):
    def observe(message):
        try:identities.observe(message)
        except sqlite3.Error:pass # Resolution remains fail-closed when the index cannot be written.
        return ContinueHandling()
    bot.message_handler(func=lambda message:True,content_types=["text","audio","document","photo","sticker","video","video_note","voice","animation","poll","dice","new_chat_members"])(observe)
