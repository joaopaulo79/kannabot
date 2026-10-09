"""Durable detection review state; one event per chat/message."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

class ReviewStore:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("CREATE TABLE IF NOT EXISTS detections(id INTEGER PRIMARY KEY,chat_id INTEGER NOT NULL,message_id INTEGER NOT NULL,user_id INTEGER NOT NULL,rules TEXT NOT NULL,status TEXT NOT NULL,reviewer INTEGER,reason TEXT,outcome TEXT,time TEXT NOT NULL,UNIQUE(chat_id,message_id))")
    def put(self,detection):
        if detection.rule not in ("flood","repeat","links") or any(type(value) is not int for value in (detection.chat_id,detection.message_id,detection.user_id)):
            raise ValueError("Invalid detection")
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT id,user_id,rules FROM detections WHERE chat_id=? AND message_id=?",(detection.chat_id,detection.message_id)).fetchone()
            if row:
                if row[1]!=detection.user_id:raise ValueError("Detection identity mismatch")
                rules=sorted(set(json.loads(row[2]))|{detection.rule})
                db.execute("UPDATE detections SET rules=? WHERE id=?",(json.dumps(rules),row[0]))
                return row[0],False
            cursor=db.execute("INSERT INTO detections(chat_id,message_id,user_id,rules,status,time) VALUES(?,?,?,?,?,?)",(detection.chat_id,detection.message_id,detection.user_id,json.dumps([detection.rule]),"pending",datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid,True
    def get(self,chat,id):
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT id,chat_id,message_id,user_id,rules,status FROM detections WHERE chat_id=? AND id=?",(chat,id)).fetchone()
            return dict(zip(("id","chat","message","user","rules","status"),row)) if row else None
    def pending(self,chat):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT id,message_id,user_id,rules FROM detections WHERE chat_id=? AND status='pending' ORDER BY id LIMIT 20",(chat,)).fetchall()
    def reserve(self,chat,id,actor):
        with closing(sqlite3.connect(self.path)) as db,db:
            return db.execute("UPDATE detections SET status='reviewing',reviewer=? WHERE chat_id=? AND id=? AND status='pending'",(actor,chat,id)).rowcount==1
    def finish(self,chat,id,actor,outcome,reason,status="resolved"):
        with closing(sqlite3.connect(self.path)) as db,db:
            return db.execute("UPDATE detections SET status=?,outcome=?,reason=? WHERE chat_id=? AND id=? AND status='reviewing' AND reviewer=?",(status,outcome,reason,chat,id,actor)).rowcount==1
