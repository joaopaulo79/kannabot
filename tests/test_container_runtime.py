import json
import logging
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock, patch
from deploy.runtime import observe_polling, record_progress, verify_identity, SecretFormatter
from deploy.runtime_common import read_database_url
from deploy.healthcheck import check_progress, check_database, main as health_main

class ContainerRuntimeTests(unittest.TestCase):
    def test_polling_health_changes_only_after_success(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"var/health.json";bot=Mock()
            bot.get_updates.side_effect=RuntimeError("network")
            observe_polling(bot,path)
            with self.assertRaises(RuntimeError):bot.get_updates(offset=1)
            self.assertFalse(path.exists())
            # Original method is retained by the wrapper, independently of replacement.
            original=Mock(return_value=["update"]);bot=Mock(get_updates=original)
            observe_polling(bot,path)
            self.assertEqual(bot.get_updates(offset=2),["update"])
            original.assert_called_once_with(offset=2)
            self.assertGreater(json.loads(path.read_text())["time"],0)

    def test_health_rejects_stale_future_and_dead_process(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"health.json";record_progress(path,clock=lambda:100)
            with patch("deploy.healthcheck.os.kill") as alive:
                check_progress(path,now=120)
                alive.assert_called_once_with(os.getpid(),0)
            for now in (99,221):
                with self.assertRaises(ValueError):check_progress(path,now=now)
            with patch("os.kill",side_effect=ProcessLookupError):
                with self.assertRaises(ProcessLookupError):check_progress(path,now=120)

    def test_database_health_is_read_only_and_validates_schema(self):
        connection=Mock();connection.execute.return_value.fetchone.return_value=(1,)
        context=Mock();context.__enter__=Mock(return_value=connection);context.__exit__=Mock(return_value=False)
        with patch("deploy.healthcheck.psycopg.connect",return_value=context) as connect:
            check_database("postgresql://test/db")
            self.assertIn("default_transaction_read_only=on",connect.call_args.kwargs["options"])
            connection.execute.assert_called_once_with("SELECT version FROM kanna_schema")
            connection.execute.return_value.fetchone.return_value=(9,)
            with self.assertRaises(ValueError):check_database("postgresql://test/db")

    def test_secret_file_requires_postgresql(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"url"
            with patch.dict(os.environ,{"DATABASE_URL_FILE":str(path)}):
                path.write_text("sqlite:///test")
                with self.assertRaises(ValueError):read_database_url()
                path.write_text("postgresql://test:private@db/kanna")
                self.assertEqual(read_database_url(),"postgresql://test:private@db/kanna")

    def test_identity_and_webhook_are_checked_without_mutation(self):
        bot=Mock();bot.get_me.return_value=N(username="kannatest_bot")
        bot.get_webhook_info.return_value=N(url="")
        verify_identity(bot,"@KannaTest_bot")
        bot.get_webhook_info.return_value=N(url="https://example.invalid")
        with self.assertRaises(ValueError):verify_identity(bot,"@kannatest_bot")
        with self.assertRaises(ValueError):verify_identity(bot,"@other_bot")
        bot.delete_webhook.assert_not_called();bot.infinity_polling.assert_not_called()

    def test_failed_health_does_not_disclose_exception(self):
        with patch("deploy.healthcheck.check_progress",side_effect=RuntimeError("private-password")),patch("builtins.print") as output:
            self.assertEqual(health_main(),1)
            self.assertNotIn("private-password",str(output.call_args))

    def test_formatter_hides_token_and_connection_string(self):
        formatter=SecretFormatter(("123:fake","postgresql://user:private@db/kanna"))
        record=logging.LogRecord("test",logging.ERROR,"",1,"123:fake postgresql://user:private@db/kanna",(),None)
        text=formatter.format(record)
        self.assertNotIn("123:fake",text);self.assertNotIn("private",text)
