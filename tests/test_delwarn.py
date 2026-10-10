import unittest
import sqlite3
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import Timeout
from telebot.apihelper import ApiTelegramException
import test_governance as fixtures
from kannabot.moderation import Moderation
from kannabot.governance import Governance

class DelwarnTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules
    def test_success_and_restart_dedup_per_message(self):
        self.import_rules()
        result=self.service.handle("delwarn",self.message("/delwarn R10 teste"))
        self.assertEqual(result.outcome,"done");self.assertIn("Descrição:",result.message)
        other=Moderation(self.bot,self.config,Governance(self.path),self.audit,roles=self.roles)
        self.assertEqual(other.handle("delwarn",self.message("/delwarn R10 teste",event=21)).outcome,"refused")
        self.assertEqual(self.store.history(1,9)[0],1);self.bot.delete_message.assert_called_once_with(1,10)
    def test_invalid_rule_and_storage_do_not_delete(self):
        self.import_rules()
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn R01 teste")).outcome,"refused")
        self.store.start_delwarn=lambda *args: (_ for _ in ()).throw(sqlite3.OperationalError("locked"))
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn R10 teste")).outcome,"failed")
        self.bot.delete_message.assert_not_called()
    def test_rejected_delete_preserves_warn_and_timeout_does_not_retry(self):
        self.import_rules()
        self.bot.delete_message.side_effect=ApiTelegramException("deleteMessage",None,{"error_code":400,"description":"denied"})
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn R10 teste")).outcome,"partial")
        self.assertEqual(self.store.history(1,9)[0],1)
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn R10 teste",event=21)).outcome,"refused")
        self.bot.delete_message.assert_called_once()
    def test_timeout_is_uncertain(self):
        self.import_rules();self.bot.delete_message.side_effect=Timeout("unknown")
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn R10 teste")).outcome,"uncertain")
        self.assertEqual(self.store.history(1,9)[0],1)
    def test_concurrent_claim_has_one_warning(self):
        self.import_rules();rule=self.store.rule(1,"R10")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:self.store.start_delwarn(1,10,7,9,"teste",rule),range(2)))
        self.assertEqual(sum(value is not None for value in results),1)
        self.assertEqual(self.store.history(1,9)[0],1)


    def test_legacy_warning_id_differs_from_infraction_reference(self):
        self.import_rules()
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("INSERT INTO warnings(id,chat_id,user_id,author_id,reason,time,event_id) VALUES(100,1,9,7,'legacy','old','legacy')")
        Governance(self.path)
        result=self.service.handle("delwarn",self.message("/delwarn R10 teste"))
        self.assertEqual(result.outcome,"done")
        self.assertIn("advertência #2",result.message)
        self.assertEqual(self.admin.handle("unwarn",self.message("/unwarn 2 revisão")).outcome,"done")

    def test_manual_without_rule_records_without_points(self):
        result=self.service.handle("delwarn",self.message("/delwarn Tô só testando"))
        self.assertEqual(result.outcome,"done");self.assertIn("não definido",result.message)
        self.assertEqual(self.store.history(1,9)[0],1);self.assertEqual(self.store.points(1,9),0)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT rule_code,rule_version,weight,snapshot FROM infractions").fetchone(),(None,None,None,None))
        self.bot.delete_message.assert_called_once_with(1,10)
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn outro motivo",event=22)).outcome,"refused")
    def test_missing_reason_and_unknown_rule_have_no_effects(self):
        for text in ("/delwarn", "/delwarn R10", "/delwarn R999 teste"):
            self.assertEqual(self.service.handle("delwarn",self.message(text)).outcome,"refused")
        self.bot.delete_message.assert_not_called();self.assertEqual(self.store.history(1,9)[0],0)
