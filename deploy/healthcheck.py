"""Validate polling progress and schema without Telegram calls or writes."""
import json
import os
import time
import psycopg
from deploy.runtime_common import read_database_url, progress_path


def check_progress(path, now=None, max_age=120):
    data = json.loads(path.read_text(encoding="utf-8"))
    age = (time.time() if now is None else now) - data["time"]
    if not 0 <= age <= max_age:
        raise ValueError("Polling progress is stale.")
    os.kill(data["pid"], 0)


def check_database(url):
    with psycopg.connect(url, connect_timeout=3, autocommit=True, options="-c default_transaction_read_only=on -c statement_timeout=3000") as db:
        if db.execute("SELECT version FROM kanna_schema").fetchone() != (1,):
            raise ValueError("Unsupported schema.")


def main():
    try:
        check_progress(progress_path())
        check_database(read_database_url())
        return 0
    except Exception:
        print("Kanna indisponível: confira progresso do polling e banco.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
