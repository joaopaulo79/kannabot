"""Database connections for PostgreSQL and legacy SQLite data.

Only application-owned SQL uses this interface. Parameters stay separate from SQL.
"""
import hashlib
import re
import sqlite3
from contextlib import closing
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

Error = (sqlite3.Error, psycopg.Error)
Row = sqlite3.Row
ID_TABLES = frozenset(('warnings', 'infractions', 'sanctions', 'detections', 'evidence', 'role_changes'))


def is_postgres(target):
    return isinstance(target, str) and target.startswith(('postgresql://', 'postgres://'))


def location(target):
    if is_postgres(target):
        return target
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect(target):
    if not is_postgres(target):
        return sqlite3.connect(target)
    connection = None
    try:
        connection = psycopg.connect(target, connect_timeout=10)
        connection.execute("SET statement_timeout = '30s'")
        connection.execute("SET lock_timeout = '10s'")
        return PostgresConnection(connection)
    except psycopg.Error:
        if connection is not None:
            connection.close()
        raise psycopg.OperationalError('Não foi possível acessar o banco de dados.') from None


class PostgresCursor:
    def __init__(self, cursor, lastrowid=None):
        self.cursor, self.lastrowid = cursor, lastrowid
        self.rowcount = cursor.rowcount

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def __iter__(self):
        return iter(self.cursor)


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection
        self.row_factory = None

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        if kind is None:
            self.connection.commit()
        else:
            self.connection.rollback()

    def close(self):
        self.connection.close()

    def execute(self, query, params=()):
        # The services use a small fixed set of parameterized SQL statements.
        query = query.replace('?', '%s')
        ignore = query.upper().startswith('INSERT OR IGNORE INTO ')
        if ignore:
            query = re.sub(r'^INSERT OR IGNORE INTO ', 'INSERT INTO ', query, flags=re.IGNORECASE)
            query += ' ON CONFLICT DO NOTHING'
        inserted = re.match(r'INSERT INTO (\w+)', query, re.IGNORECASE)
        returns_id = inserted is not None and inserted[1].lower() in ID_TABLES
        if returns_id:
            query += ' RETURNING id'
        cursor = self.connection.cursor(row_factory=dict_row if self.row_factory is Row else None)
        cursor.execute(query, params or None)
        lastrowid = None
        if returns_id:
            row = cursor.fetchone()
            if row is not None:
                lastrowid = row['id'] if isinstance(row, dict) else row[0]
        return PostgresCursor(cursor, lastrowid)


def lock(db, *key):
    """Serialize read-modify-write within the current transaction."""
    if isinstance(db, PostgresConnection):
        digest = hashlib.sha256(repr(key).encode('utf-8')).digest()[:8]
        db.connection.execute('SELECT pg_advisory_xact_lock(%s)', (int.from_bytes(digest, 'big', signed=True),))
    else:
        db.execute('BEGIN IMMEDIATE')


def initialize(target):
    if not is_postgres(target):
        return False
    with closing(connect(target)) as db, db:
        lock(db, 'schema')
        present = db.connection.execute("SELECT to_regclass('public.kanna_schema')").fetchone()[0]
        if present:
            version = db.connection.execute('SELECT version FROM kanna_schema').fetchone()
            if version != (1,):
                raise ValueError('Versão do banco não suportada.')
            return True
        script = (Path(__file__).parent / 'resources/postgresql.sql').read_text(encoding='utf-8')
        db.connection.execute(script)
    return True


def has_identities(db):
    if isinstance(db, PostgresConnection):
        return db.connection.execute("SELECT to_regclass('public.identities')").fetchone()[0] is not None
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='identities'").fetchone() is not None
