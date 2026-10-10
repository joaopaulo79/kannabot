import json
import sqlite3
import unittest
from contextlib import closing
import test_governance as fixtures
from kannabot.governance import Governance
from kannabot.help import PAGES

class ManualWarnTests(unittest.TestCase):
    setUp = fixtures.GovernanceTests.setUp
    message = fixtures.GovernanceTests.message
    import_rules = fixtures.GovernanceTests.import_rules

    def test_no_reason_persists_zero_and_audits_without_external_effect(self):
        result=self.service.handle("warn",self.message("/warn"))
        self.assertEqual(result.outcome,"done")
        self.assertIn("Peso: 0 pontos; não acrescenta pontos.",result.message)
        self.assertIn("Motivo: não informado",result.message)
        self.assertIn("1 advertência(s) válida(s) · 0 pontos",result.message)
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute("SELECT w.reason,i.weight,i.rule_code,i.snapshot FROM warnings w JOIN infractions i ON i.warning_id=w.id").fetchone()
        self.assertEqual(row,("não informado",0,None,None))
        restarted=Governance(self.path)
        self.assertEqual(restarted.history(1,9)[0],1)
        self.assertEqual(restarted.points(1,9),0)
        event=json.loads(self.audit.path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(event["reason"],"não informado");self.assertEqual(event["weight"],"0")
        self.bot.delete_message.assert_not_called();self.bot.ban_chat_member.assert_not_called();self.bot.restrict_chat_member.assert_not_called()
        self.assertEqual(self.service.handle("warn",self.message("/warn")).outcome,"refused")
        self.assertEqual(restarted.history(1,9)[0],1)

    def test_reason_is_optional_but_preserved_when_present_and_can_cancel(self):
        result=self.service.handle("warn",self.message("/warn combinado"))
        self.assertEqual(result.outcome,"done")
        self.assertIn("Motivo: combinado",result.message)
        entry=self.store.detailed_entries(1,9)[0]
        self.assertEqual(entry["weight"],0)
        history=self.service.handle("warnings",self.message("/warnings"))
        self.assertIn("Peso aplicado: 0",history.message)
        self.assertEqual(self.admin.handle("unwarn",self.message(f"/unwarn {entry['id']} revisão")).outcome,"done")
        self.assertEqual(self.store.history(1,9)[0],0);self.assertEqual(self.store.points(1,9),0)

    def test_permissions_and_target_still_required(self):
        self.assertEqual(self.service.handle("warn",self.message("/warn",actor=9)).outcome,"refused")
        self.assertEqual(self.service.handle("warn",self.message("/warn",target=1)).outcome,"refused")
        message=self.message("/warn");message.reply_to_message=None
        self.assertEqual(self.service.handle("warn",message).outcome,"refused")
        self.assertEqual(self.store.history(1,9)[0],0)

    def test_catalog_weights_and_historical_null_are_preserved(self):
        self.import_rules()
        self.assertEqual(self.service.handle("warn",self.message("/warn R10")).outcome,"done")
        self.assertEqual(self.store.points(1,9),3)
        self.assertEqual(self.service.handle("warn",self.message("/warn R09",event=21)).outcome,"refused")
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("UPDATE infractions SET weight=NULL")
        Governance(self.path)
        self.assertIsNone(self.store.detailed_entries(1,9)[0]["weight"])
        self.assertIn("/warn ou /warn motivo",PAGES["warn"][5])
