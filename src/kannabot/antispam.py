from collections import OrderedDict, deque
from dataclasses import dataclass
from hashlib import sha256
from threading import RLock
from time import monotonic
import unicodedata
from telebot.handler_backends import ContinueHandling
from kannabot.interacoes import Seen
from kannabot.links import violates
from kannabot.permissions import Permissions, PermissionDenied

@dataclass(frozen=True)
class Detection:
    rule: str
    chat_id: int
    user_id: int
    message_id: int

def normalize(text):
    return " ".join(unicodedata.normalize("NFKC",text).casefold().split())

class Antispam:
    def __init__(self,bot,config,policy,audit,clock=monotonic,capacity=1000):
        self.bot,self.policy,self.audit=bot,policy,audit
        self.permissions=Permissions(bot,config.grupos_id)
        self.clock,self.capacity=clock,capacity
        self.users=OrderedDict();self.lock=RLock()
        self.seen=Seen(ttl=3600,clock=clock)
        self.logged=Seen(ttl=60,clock=clock)
    def handle(self,message):
        chat=message.chat.id;options=self.policy.get(chat,"spam")
        links=self.policy.get(chat,"links")
        user=getattr(message,"from_user",None)
        if not self.permissions.authorized(chat) or (not options and not links) or user is None or getattr(user,"is_bot",False) or getattr(message,"sender_chat",None) is not None:
            return []
        if getattr(message,"new_chat_members",None) or getattr(message,"left_chat_member",None):
            return []
        try:
            self.permissions.emote_actor(message)
            if self.permissions.is_admin(chat,user.id):return []
        except PermissionDenied:
            return []
        if not self.seen.claim((chat,message.message_id)):
            return []
        detections=self.inspect(message,options) if options else []
        if links and violates(message,links):
            detections.append(Detection("links",chat,user.id,message.message_id))
            if self.logged.claim((chat,user.id,"links")):
                self.audit.record(chat,None,user.id,"spam_observe","links","done")
        return detections
    def inspect(self,message,options):
        now=self.clock();chat=message.chat.id;user=message.from_user.id
        text=getattr(message,"text",None) or getattr(message,"caption",None) or ""
        normalized=normalize(text)
        digest=sha256(normalized.encode()).digest() if normalized else None
        horizon=max(options["flood_window"],options["repeat_window"])
        with self.lock:
            for key in list(self.users):
                _,last,window=self.users[key]
                if last<=now-window:del self.users[key]
            key=(chat,user)
            events,_,_=self.users.get(key,(deque(maxlen=101),now,horizon))
            while events and events[0][0]<=now-horizon:events.popleft()
            events.append((now,digest));self.users[key]=(events,now,horizon);self.users.move_to_end(key)
            while len(self.users)>self.capacity:self.users.popitem(last=False)
            flood=sum(time>now-options["flood_window"] for time,_ in events)
            repeats=sum(time>now-options["repeat_window"] and value==digest for time,value in events) if digest else 0
        rules=[]
        if flood>options["flood_limit"]:rules.append("flood")
        if repeats>options["repeat_limit"]:rules.append("repeat")
        detections=[Detection(rule,chat,user,message.message_id) for rule in rules]
        for detection in detections:
            if self.logged.claim((chat,user,detection.rule)):
                self.audit.record(chat,None,user,"spam_observe",detection.rule,"done")
        return detections

def register(bot,service):
    def observe(message):
        service.handle(message)
        return ContinueHandling()
    bot.message_handler(func=lambda message:True,content_types=["text","audio","document","photo","sticker","video","video_note","voice","animation","location","contact","poll","dice","venue"])(observe)
