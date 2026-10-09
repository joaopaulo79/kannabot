"""Local transactional warning history, isolated by numeric chat/user IDs."""
import sqlite3
from contextlib import closing
from pathlib import Path

class WarningStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY, chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL, author_id INTEGER, reason TEXT NOT NULL, time TEXT NOT NULL, event_id TEXT NOT NULL, UNIQUE(chat_id, event_id))")
            db.execute("CREATE INDEX IF NOT EXISTS warning_member ON warnings(chat_id, user_id)")

    def add(self, chat_id, user_id, author_id, reason, time, event_id):
        with closing(sqlite3.connect(self.path)) as db, db:
            cursor = db.execute("INSERT OR IGNORE INTO warnings(chat_id,user_id,author_id,reason,time,event_id) VALUES(?,?,?,?,?,?)", (chat_id,user_id,author_id,reason,time,str(event_id)))
            return cursor.rowcount == 1

    def history(self, chat_id, user_id):
        with closing(sqlite3.connect(self.path)) as db:
            total = db.execute("SELECT COUNT(*) FROM warnings WHERE chat_id=? AND user_id=?", (chat_id,user_id)).fetchone()[0]
            rows = db.execute("SELECT author_id,reason,time FROM warnings WHERE chat_id=? AND user_id=? ORDER BY id DESC LIMIT 20", (chat_id,user_id)).fetchall()
            return total, rows
