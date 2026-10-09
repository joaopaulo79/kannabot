import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot._config.configuracao import Configuracao
from kannabot.moderation import Moderation
from kannabot.storage import WarningStore

class ModerationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/"moderation.sqlite3"
        self.bot=Mock();self.audit=Mock();self.audit.clean.side_effect=lambda x:x
        self.bot.get_chat_member.side_effect=lambda chat,user:N(status="administrator" if user in (7,99) else "member",can_delete_messages=True,can_restrict_members=True)
        self.bot.get_me.return_value=N(id=99)
        self.cfg=Configuracao("123:fake",Path("unused"),(1,2),"@TesteBot")
        self.service=Moderation(self.bot,self.cfg,WarningStore(self.path),self.audit)
        self.msg=N(chat=N(id=1,type="supergroup"),message_id=20,text="/warn motivo",sender_chat=None,from_user=N(id=7,is_bot=False),reply_to_message=N(chat=N(id=1),message_id=10,sender_chat=None,from_user=N(id=8,is_bot=False)))
    def test_warn_persists_and_isolates_and_deduplicates(self):
        self.assertEqual(self.service.handle("warn",self.msg).outcome,"done")
        store=WarningStore(self.path)
        self.assertEqual(store.history(1,8)[0],1);self.assertEqual(store.history(2,8)[0],0)
        self.assertEqual(self.service.handle("warn",self.msg).outcome,"refused")
        self.assertEqual(store.history(1,8)[0],1)
        self.audit.record.assert_called()
    def test_member_and_admin_target_denied(self):
        self.msg.from_user.id=8
        self.assertEqual(self.service.handle("warn",self.msg).outcome,"refused")
        self.msg.from_user.id=7;self.msg.reply_to_message.from_user.id=7
        self.assertEqual(self.service.handle("warn",self.msg).outcome,"refused")
        self.assertEqual(self.service.store.history(1,7)[0],0)
    def test_invalid_reply_and_reason_no_partial_record(self):
        self.msg.reply_to_message.chat.id=2
        self.assertEqual(self.service.handle("warn",self.msg).outcome,"refused")
        self.msg.reply_to_message.chat.id=1;self.msg.text="/warn"
        self.assertEqual(self.service.handle("warn",self.msg).outcome,"refused")
        self.assertEqual(self.service.store.history(1,8)[0],0)
    def test_storage_failure_is_not_success(self):
        self.service.store=Mock();self.service.store.add.side_effect=OSError("secret")
        result=self.service.handle("warn",self.msg)
        self.assertEqual(result.outcome,"failed");self.assertNotIn("secret",result.message)
    def test_history_requires_admin_and_escapes_reason(self):
        self.msg.text="/warn <reason>";self.service.handle("warn",self.msg)
        self.msg.text="/warnings"
        result=self.service.handle("warnings",self.msg)
        self.assertIn("&lt;reason&gt;",result.message)
        self.msg.from_user.id=8;self.assertEqual(self.service.handle("warnings",self.msg).outcome,"refused")
