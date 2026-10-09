"""Explicitly moderated message snapshots; retained until administrative removal."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from kannabot.permissions import PermissionDenied
from kannabot.presentation import context, send_reply

class Evidence:
    def __init__(self,path,clean):
        self.path,self.clean=path,clean
        with closing(sqlite3.connect(path)) as db,db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS evidence(
                id INTEGER PRIMARY KEY, chat_id INTEGER NOT NULL, message_id INTEGER NOT NULL,
                user_id INTEGER, username TEXT, captured_at TEXT NOT NULL,
                payload TEXT, availability TEXT NOT NULL, removed_at TEXT,
                removed_by INTEGER, removal_reason TEXT, UNIQUE(chat_id,message_id));
            CREATE TABLE IF NOT EXISTS evidence_actions(
                evidence_id INTEGER NOT NULL, event_id TEXT NOT NULL, action TEXT NOT NULL,
                PRIMARY KEY(evidence_id,event_id,action));
            CREATE VIEW IF NOT EXISTS evidencias AS SELECT * FROM evidence;
            """)

    def snapshot(self,message):
        payload={}
        for key in ('text','caption'):
            value=getattr(message,key,None)
            if isinstance(value,str):payload[key]=self.clean(value,limit=12000)
        date=getattr(message,'date',None)
        if type(date) is int:payload['date']=date
        for field in ('entities','caption_entities'):
            entities=getattr(message,field,None)
            if isinstance(entities,(list,tuple)):
                items=[]
                for entity in entities[:100]:
                    item={}
                    for key in ('type','offset','length','url'):
                        value=getattr(entity,key,None)
                        if type(value) is int or isinstance(value,str):item[key]=self.clean(value,limit=1000) if isinstance(value,str) else value
                    user=getattr(entity,'user',None)
                    if type(getattr(user,'id',None)) is int:item['user_id']=user.id
                    items.append(item)
                payload[field]=items
        for field in ('photo','video','animation','document','audio','voice','sticker','video_note'):
            media=getattr(message,field,None)
            if isinstance(media,(list,tuple)):media=media[-1] if media else None
            if media is None:continue
            item={}
            for key in ('file_id','file_unique_id','mime_type','file_size','duration','width','height'):
                value=getattr(media,key,None)
                if type(value) is int or isinstance(value,str):item[key]=self.clean(value,limit=1000) if isinstance(value,str) else value
            if item:payload[field]=item
        state='text_and_metadata' if 'text' in payload or 'caption' in payload else 'media_metadata_only' if any(key in payload for key in ('photo','video','animation','document','audio','voice','sticker','video_note')) else 'content_unavailable'
        return payload,state

    def capture(self,chat,message,event,action):
        if type(chat) is not int or type(getattr(message,'message_id',None)) is not int:
            raise ValueError('Mensagem original necessária para preservar evidência.')
        payload,state=self.snapshot(message);user=getattr(message,'from_user',None)
        username=getattr(user,'username',None)
        username=self.clean(username,limit=100) if isinstance(username,str) else None
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT OR IGNORE INTO evidence(chat_id,message_id,user_id,username,captured_at,payload,availability) VALUES(?,?,?,?,?,?,?)',
                (chat,message.message_id,getattr(user,'id',None),username,datetime.now(timezone.utc).isoformat(),json.dumps(payload,ensure_ascii=False),state))
            row=db.execute('SELECT id,availability FROM evidence WHERE chat_id=? AND message_id=?',(chat,message.message_id)).fetchone()
            db.execute('INSERT OR IGNORE INTO evidence_actions VALUES(?,?,?)',(row[0],event,action))
            return row

    def remove(self,chat,reference,actor,reason):
        reason=self.clean(reason)
        if not reason.strip():raise ValueError('Informe o motivo da exclusão da evidência.')
        with closing(sqlite3.connect(self.path)) as db,db:
            changed=db.execute("UPDATE evidence SET payload=NULL,username=NULL,availability='removed',removed_at=?,removed_by=?,removal_reason=? WHERE chat_id=? AND id=? AND removed_at IS NULL",
                (datetime.now(timezone.utc).isoformat(),actor,reason,chat,reference)).rowcount
            if not changed:raise ValueError('Evidência inexistente neste grupo ou já removida.')

    def handle_remove(self,service,message):
        actor,metadata=context(message);reason='';error=None
        try:
            service.permissions.actor(message,'delete')
            if service.roles is None or service.roles.role(message.chat.id,actor) not in ('owner','admin'):
                raise PermissionDenied('Somente o Dono ou um Admin pode remover evidências.')
            parts=message.text.split(maxsplit=2)
            if len(parts)!=3 or not parts[1].isdigit():raise ValueError('Use /evidence_remove ID motivo.')
            reason=self.clean(parts[2]);self.remove(message.chat.id,int(parts[1]),actor,reason)
            outcome,text='done','🗂️ Evidência removida. Histórico e advertências preservados.'
            metadata['evidence_id']=int(parts[1])
        except (ValueError,PermissionDenied) as exc:outcome,text='refused',self.clean(str(exc))
        except Exception as exc:error=exc;outcome,text='failed','Não foi possível remover a evidência.'
        metadata['detail']=text
        service.audit.record(message.chat.id,actor,None,'evidence_remove',reason,outcome,error,metadata=metadata)
        return text

def register(bot,evidence,service):
    @bot.message_handler(commands=['evidence_remove'])
    def remove(message):
        send_reply(bot,message.chat.id,evidence.handle_remove(service,message))
