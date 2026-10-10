import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot.audit import Audit

class AuditTests(unittest.TestCase):
    def test_remote_fields_html_and_redaction(self):
        bot=Mock();bot.get_chat.return_value=N(type="supergroup", username=None)
        audit=Audit(bot,-1009,secrets=("123:fake",))
        self.assertTrue(audit.record(-1001,7,8,"warn","<x> 123:fake", "failed", RuntimeError("123:fake")))
        args=bot.send_message.call_args
        self.assertEqual(args.args[0],-1009)
        self.assertIn("&lt;x&gt;",args.args[1]);self.assertNotIn("123:fake",args.args[1])
        for item in ("Data/hora:","Usuário 7","Usuário 8","Resultado: Falha confirmada","RuntimeError"):
            self.assertIn(item,args.args[1])
    def test_delivery_failure_has_single_local_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            bot=Mock();bot.get_chat.return_value=N(type="group",username=None)
            bot.send_message.side_effect=RuntimeError("123:fake")
            path=Path(folder)/"audit.jsonl"
            audit=Audit(bot,-9,path,secrets=("123:fake",))
            self.assertFalse(audit.record(-1,None,8,"mute","123:fake", "done"))
            data=json.loads(path.read_text());self.assertEqual(data["actor"],"automation")
            self.assertEqual(data["outcome"],"done");self.assertNotIn("123:fake",path.read_text())
            bot.send_message.assert_called_once();bot.ban_chat_member.assert_not_called()
    def test_public_destination_is_not_used(self):
        with tempfile.TemporaryDirectory() as folder:
            bot=Mock();bot.get_chat.return_value=N(type="supergroup",username="public")
            audit=Audit(bot,-9,Path(folder)/"audit.jsonl")
            audit.record(-1,7,8,"delete","reason","refused")
            bot.send_message.assert_not_called()
    def test_bad_outcome_rejected_and_local_failure_does_not_raise(self):
        audit=Audit(Mock())
        with self.assertRaises(ValueError):audit.record(-1,7,8,"x","r","success")
        with self.assertLogs("kannabot.audit",level="ERROR"):
            self.assertFalse(audit.record(-1,7,8,"x","r","failed"))

    def test_display_time_converts_day_and_preserves_event(self):
        audit=Audit(Mock())
        event=dict(time="2026-10-10T00:22:57.506407+00:00",chat_id=1,actor=7,target=None,action="help",reason="consulta",outcome="done")
        text=audit.render(event)
        self.assertIn("09/10/2026 às 21:22:57 — horário de Brasília (UTC−3)",text)
        self.assertEqual(event['time'],"2026-10-10T00:22:57.506407+00:00")
        self.assertIn("21:22:57",audit.display_time("2026-10-09T21:22:57-03:00"))
        self.assertEqual(audit.display_time("unknown"),"unknown")
