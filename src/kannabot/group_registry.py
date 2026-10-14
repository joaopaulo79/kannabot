"""Persistent group/log links and single-use, actor-bound registration tickets."""
from contextlib import closing
from hashlib import sha256
from kannabot import database


class RegistrationError(ValueError):
    pass


class GroupRegistry:
    def __init__(self, path):
        self.path = database.location(path)
        with closing(database.connect(self.path)) as db, db:
            database.lock(db, "registration_schema")
            db.execute("CREATE TABLE IF NOT EXISTS group_registrations(chat_id BIGINT PRIMARY KEY CHECK(chat_id<0),log_chat_id BIGINT NOT NULL UNIQUE CHECK(log_chat_id<0),owner_id BIGINT NOT NULL CHECK(owner_id>0),registered_at TEXT NOT NULL,CHECK(chat_id!=log_chat_id))")
            db.execute("CREATE TABLE IF NOT EXISTS registration_tickets(token_hash TEXT PRIMARY KEY,actor_id BIGINT NOT NULL UNIQUE,log_chat_id BIGINT NOT NULL,expires_at DOUBLE PRECISION NOT NULL)")

    def get(self, chat):
        with closing(database.connect(self.path)) as db:
            return db.execute("SELECT log_chat_id,owner_id FROM group_registrations WHERE chat_id=?", (chat,)).fetchone()

    def chats(self):
        with closing(database.connect(self.path)) as db:
            return [row[0] for row in db.execute("SELECT chat_id FROM group_registrations")]

    @staticmethod
    def digest(token):
        return sha256(token.encode("ascii")).hexdigest()

    def issue(self, token, actor, destination, now, ttl=600):
        with closing(database.connect(self.path)) as db, db:
            database.lock(db, "registration")
            if db.execute("SELECT 1 FROM group_registrations WHERE chat_id=? OR log_chat_id=?", (destination,destination)).fetchone():
                raise RegistrationError("Este chat já está vinculado. Use um grupo privado de logs exclusivo.")
            db.execute("DELETE FROM registration_tickets WHERE expires_at<=? OR actor_id=?", (now,actor))
            db.execute("INSERT INTO registration_tickets VALUES(?,?,?,?)", (self.digest(token),actor,destination,now+ttl))

    def ticket(self, token, actor, now):
        with closing(database.connect(self.path)) as db:
            row=db.execute("SELECT log_chat_id FROM registration_tickets WHERE token_hash=? AND actor_id=? AND expires_at>?", (self.digest(token),actor,now)).fetchone()
            if not row:
                raise RegistrationError("Código inválido, expirado ou de outro responsável. Solicite /cadastrar_logs novamente no grupo privado de logs.")
            return row[0]

    def activate(self, chat, destination, actor, token, now, timestamp):
        with closing(database.connect(self.path)) as db, db:
            database.lock(db, "registration")
            if db.execute("SELECT 1 FROM group_registrations WHERE chat_id=?", (chat,)).fetchone():
                return False
            if chat==destination or db.execute("SELECT 1 FROM group_registrations WHERE chat_id=? OR log_chat_id=? OR log_chat_id=?", (destination,destination,chat)).fetchone():
                raise RegistrationError("Os chats precisam ser distintos e o grupo de logs deve ser exclusivo.")
            consumed=db.execute("DELETE FROM registration_tickets WHERE token_hash=? AND actor_id=? AND log_chat_id=? AND expires_at>?", (self.digest(token),actor,destination,now))
            if consumed.rowcount!=1:
                raise RegistrationError("Código inválido ou expirado. Solicite um novo código no grupo privado de logs.")
            db.execute("INSERT INTO group_registrations VALUES(?,?,?,?)", (chat,destination,actor,timestamp))
            return True


class GroupAccess:
    """Live membership; legacy groups stay explicit, never snapshot this collection."""
    def __init__(self, registry, legacy=()):
        self.registry=registry
        self.legacy=frozenset(legacy)

    def __contains__(self, chat):
        if type(chat) is not int:return False
        if chat in self.legacy:return True
        try:return self.registry.get(chat) is not None
        except database.Error:return False

    def __iter__(self):
        return iter(sorted(self.legacy | set(self.registry.chats())))

    def __len__(self):
        return len(set(iter(self)))

    def __eq__(self, other):
        try:return set(self)==set(other)
        except TypeError:return False

    def destination(self, chat, legacy_destination=None):
        row=self.registry.get(chat)
        if row:return row[0]
        return legacy_destination if chat in self.legacy and chat!=legacy_destination else None


def preserve_access(groups):
    return groups if isinstance(groups, GroupAccess) else frozenset(groups)
