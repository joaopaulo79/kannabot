"""Configuration shared by container startup and read-only health checks."""
import os
from pathlib import Path
from urllib.parse import urlsplit


def read_database_url():
    value = Path(os.environ.get("DATABASE_URL_FILE", "/run/secrets/database_url")).read_text(encoding="utf-8").strip()
    parsed = urlsplit(value)
    if parsed.scheme not in ("postgres", "postgresql") or not parsed.hostname or not parsed.path.strip("/"):
        raise ValueError("Container requires a PostgreSQL connection secret.")
    return value


def progress_path():
    return Path(os.environ.get("KANNA_HOME", "/state")) / "var/poll-health.json"
