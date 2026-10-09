"""SQLite governance, immutable rule versions, and persistent action claims."""
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from kannabot.storage import WarningStore

CAPABILITIES = {
    "owner": frozenset(("warn","warnings","delete","mute","kick","ban","unban","unwarn","roles","catalog","review")),
    "admin": frozenset(("warn","warnings","delete","mute","kick","ban","unban","unwarn","catalog","review")),
    "mod": frozenset(("warn","warnings","delete","mute","catalog","review")),
    "member": frozenset(),
}
RANK = {"member":0,"mod":1,"admin":2,"owner":3}

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def validate_rule(rule):
    keys={"code","name","description","level","weight","active","actions"}
    if not isinstance(rule,dict) or set(rule)!=keys:
        raise ValueError("Regra requer code, name, description, level, weight, active e actions.")
    if not isinstance(rule["code"],str) or not re.fullmatch(r"R[0-9]{2,4}",rule["code"]):
        raise ValueError("Código deve seguir R01 até R9999.")
    for key in ("name","description"):
        if not isinstance(rule[key],str) or not rule[key].strip() or len(rule[key])>1000:
            raise ValueError("Nome/descrição inválidos ou longos demais.")
    if rule["level"] not in ("N1","N2","N3","N4") or type(rule["active"]) is not bool:
        raise ValueError("Nível/estado inválidos.")
    weight=rule["weight"]
    if weight is not None and (type(weight) is not int or not 0<=weight<=4):
        raise ValueError("Peso deve ser inteiro 0..4 ou null quando indefinido.")
    actions=rule["actions"]
    if not isinstance(actions,list) or any(not isinstance(action,str) for action in actions) or len(actions)!=len(set(actions)) or any(action not in ("warn","delete","mute","ban") for action in actions):
        raise ValueError("Ações de regra inválidas.")
    if rule["level"] == "N4" and "mute" in actions:
        raise ValueError("N4 não define duração de mute; use uma ação prevista no nível.")
    return dict(rule)

class Governance(WarningStore):
    def __init__(self,path):
        super().__init__(path)
        with closing(sqlite3.connect(self.path)) as db, db:
            for statement in (
                "CREATE TABLE IF NOT EXISTS roles(chat_id INTEGER NOT NULL,user_id INTEGER NOT NULL,role TEXT NOT NULL,actor_id INTEGER NOT NULL,time TEXT NOT NULL,PRIMARY KEY(chat_id,user_id))",
                "CREATE TABLE IF NOT EXISTS rules(chat_id INTEGER NOT NULL,code TEXT NOT NULL,version INTEGER NOT NULL,snapshot TEXT NOT NULL,actor_id INTEGER NOT NULL,time TEXT NOT NULL,PRIMARY KEY(chat_id,code,version))",
                "CREATE TABLE IF NOT EXISTS infractions(id INTEGER PRIMARY KEY,warning_id INTEGER NOT NULL UNIQUE,rule_code TEXT,rule_version INTEGER,weight INTEGER,snapshot TEXT,cancel_time TEXT,cancel_actor INTEGER,cancel_reason TEXT)",
                "CREATE TABLE IF NOT EXISTS sanctions(id INTEGER PRIMARY KEY,chat_id INTEGER NOT NULL,event_id TEXT NOT NULL,action TEXT NOT NULL,actor_id INTEGER NOT NULL,target_id INTEGER NOT NULL,rule_code TEXT,rule_version INTEGER,reason TEXT NOT NULL,status TEXT NOT NULL,detail TEXT NOT NULL,time TEXT NOT NULL,UNIQUE(chat_id,event_id,action))",
            ):db.execute(statement)
            db.execute("INSERT OR IGNORE INTO infractions(warning_id) SELECT id FROM warnings")
            db.execute("PRAGMA user_version=1")

    def role(self,chat,user):
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT role FROM roles WHERE chat_id=? AND user_id=?",(chat,user)).fetchone()
            return row[0] if row else "member"

    def set_role(self,chat,user,role,actor):
        if role not in ("admin","mod","member"):raise ValueError("Cargo inválido.")
        with closing(sqlite3.connect(self.path)) as db, db:
            if role=="member":db.execute("DELETE FROM roles WHERE chat_id=? AND user_id=?",(chat,user))
            else:db.execute("INSERT INTO roles VALUES(?,?,?,?,?) ON CONFLICT(chat_id,user_id) DO UPDATE SET role=excluded.role,actor_id=excluded.actor_id,time=excluded.time",(chat,user,role,actor,utcnow()))

    def put_rule(self,chat,rule,actor):
        rule=validate_rule(rule)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            version=db.execute("SELECT COALESCE(MAX(version),0)+1 FROM rules WHERE chat_id=? AND code=?",(chat,rule["code"])).fetchone()[0]
            db.execute("INSERT INTO rules VALUES(?,?,?,?,?,?)",(chat,rule["code"],version,json.dumps(rule,ensure_ascii=False),actor,utcnow()))
            return version

    def rule(self,chat,code):
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT version,snapshot FROM rules WHERE chat_id=? AND code=? ORDER BY version DESC LIMIT 1",(chat,code)).fetchone()
            if not row:return None
            return dict(json.loads(row[1]),version=row[0])

    def catalog(self,chat):
        with closing(sqlite3.connect(self.path)) as db:
            codes=[row[0] for row in db.execute("SELECT DISTINCT code FROM rules WHERE chat_id=? ORDER BY code LIMIT 100",(chat,))]
        return [self.rule(chat,code) for code in codes]

    def add(self,chat,user,actor,reason,time,event_id,rule=None):
        with closing(sqlite3.connect(self.path)) as db, db:
            cursor=db.execute("INSERT OR IGNORE INTO warnings(chat_id,user_id,author_id,reason,time,event_id) VALUES(?,?,?,?,?,?)",(chat,user,actor,reason,time,str(event_id)))
            if cursor.rowcount!=1:return False
            db.execute("INSERT INTO infractions(warning_id,rule_code,rule_version,weight,snapshot) VALUES(?,?,?,?,?)",(cursor.lastrowid,rule["code"] if rule else None,rule["version"] if rule else None,rule["weight"] if rule else None,json.dumps(rule,ensure_ascii=False) if rule else None))
            return True

    def history(self,chat,user):
        with closing(sqlite3.connect(self.path)) as db:
            where="FROM warnings w JOIN infractions i ON w.id=i.warning_id WHERE w.chat_id=? AND w.user_id=? AND i.cancel_time IS NULL"
            total=db.execute("SELECT COUNT(*) "+where,(chat,user)).fetchone()[0]
            rows=db.execute("SELECT w.author_id,w.reason,w.time "+where+" ORDER BY w.id DESC LIMIT 20",(chat,user)).fetchall()
            return total,rows

    def points(self,chat,user):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT COALESCE(SUM(i.weight),0) FROM warnings w JOIN infractions i ON w.id=i.warning_id WHERE w.chat_id=? AND w.user_id=? AND i.cancel_time IS NULL",(chat,user)).fetchone()[0]

    def infraction(self,chat,id):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT w.user_id,i.cancel_time FROM warnings w JOIN infractions i ON w.id=i.warning_id WHERE w.chat_id=? AND i.id=?",(chat,id)).fetchone()

    def cancel(self,chat,id,actor,reason):
        with closing(sqlite3.connect(self.path)) as db, db:
            cursor=db.execute("UPDATE infractions SET cancel_time=?,cancel_actor=?,cancel_reason=? WHERE id=? AND cancel_time IS NULL AND warning_id IN (SELECT id FROM warnings WHERE chat_id=?)",(utcnow(),actor,reason,id,chat))
            return cursor.rowcount==1

    def begin(self,chat,event,action,actor,target,reason,rule=None):
        with closing(sqlite3.connect(self.path)) as db, db:
            cursor=db.execute("INSERT OR IGNORE INTO sanctions(chat_id,event_id,action,actor_id,target_id,rule_code,rule_version,reason,status,detail,time) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(chat,str(event),action,actor,target,rule["code"] if rule else None,rule["version"] if rule else None,reason,"pending","Resultado ainda não confirmado",utcnow()))
            return cursor.lastrowid if cursor.rowcount==1 else None

    def finish(self,id,status,detail):
        if status not in ("done","refused","failed","partial","uncertain"):raise ValueError("Resultado inválido.")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE sanctions SET status=?,detail=? WHERE id=? AND status='pending'",(status,detail,id))

    def entries(self,chat,user):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT i.id,i.rule_code,i.rule_version,i.weight,w.reason,i.cancel_time FROM warnings w JOIN infractions i ON w.id=i.warning_id WHERE w.chat_id=? AND w.user_id=? ORDER BY i.id DESC LIMIT 20",(chat,user)).fetchall()
