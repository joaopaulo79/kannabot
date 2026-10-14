"""Run integration tests only against an explicitly named disposable database."""
import os
from pathlib import Path
import socket
import tempfile
import unittest
from urllib.parse import urlsplit
from unittest.mock import patch

url = Path(os.environ["KANNA_TEST_DATABASE_URL_FILE"]).read_text(encoding="utf-8").strip()
if not urlsplit(url).path.strip("/").startswith("kanna_test_"):
    raise SystemExit("Refusing tests: database name must start with kanna_test_.")
os.environ["KANNA_TEST_DATABASE_URL"] = url
for key in ("DATABASE_URL", "CHAVE_API_BOT", "BOT_USERNAME", "CAMINHO_AUTORZACAO", "CAMINHO_POLITICAS", "LOG_CHAT_ID", "KANNA_HOME"):
    os.environ.pop(key, None)
home = tempfile.TemporaryDirectory(prefix="kanna-validation-")
os.environ["KANNA_HOME"] = home.name
suite = unittest.defaultTestLoader.discover("tests")
# libpq connects directly to the dedicated database; HTTP/Telegram sockets are blocked.
with patch.object(socket.socket, "connect", side_effect=AssertionError("HTTP network disabled in validation")):
    result = unittest.TextTestRunner(verbosity=2).run(suite)
print("VALIDATION_TOTAL", result.testsRun, "FAILURES", len(result.failures), "ERRORS", len(result.errors), "SKIPS", len(result.skipped))
raise SystemExit(not result.wasSuccessful())
