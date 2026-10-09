import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot._config.configuracao import Configuracao
from kannabot.moderation import Moderation, parse_duration
from kannabot.storage import WarningStore

class ModerationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/"moderation.sqlite3"
        self.bot=Mock();self.audit=Mock();self.audit.clean.side_effect=lambda x:x
        self.bot.get_chat_member.side_effect=lambda chat,user:N(status="administrator" if user in (7,99) else "member",can_delete_messages=True,can_restrict_members=True)
        self.bot.get_me.return_value=N(id=99)
        self.bot.get_chat.return_value=N(type="supergroup")
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

    def test_delete_targets_reply_once(self):
        self.bot.delete_message.return_value=True
        result=self.service.handle("delete",self.msg)
        self.assertEqual(result.outcome,"done")
        self.bot.delete_message.assert_called_once_with(1,10)
        self.msg.message_id=21
        self.assertEqual(self.service.handle("delete",self.msg).outcome,"refused")
        self.bot.delete_message.assert_called_once()
    def test_delete_false_or_missing_right_does_not_succeed(self):
        self.bot.delete_message.return_value=False
        self.assertEqual(self.service.handle("delete",self.msg).outcome,"failed")
        self.bot.delete_message.reset_mock()
        self.bot.get_chat_member.side_effect=lambda chat,user:N(status="administrator" if user in (7,99) else "member",can_delete_messages=False)
        self.msg.reply_to_message.message_id=11
        self.assertEqual(self.service.handle("delete",self.msg).outcome,"refused")
        self.bot.delete_message.assert_not_called()
    def test_delete_without_reply_or_non_admin_sends_nothing(self):
        self.msg.from_user.id=8
        self.assertEqual(self.service.handle("delete",self.msg).outcome,"refused")
        self.msg.from_user.id=7;self.msg.reply_to_message=None
        self.assertEqual(self.service.handle("delete",self.msg).outcome,"refused")
        self.bot.delete_message.assert_not_called()

    def test_duration_boundaries_and_invalid_values(self):
        self.assertEqual(parse_duration("60s"),60)
        self.assertEqual(parse_duration("365d"),365*86400)
        for text in ("30s","366d","-1m","0h","10","abc","999999999999d"):
            with self.subTest(text=text), self.assertRaises(ValueError):parse_duration(text)
    def test_mute_until_date_and_permissions(self):
        from datetime import datetime, timezone
        fixed=datetime(2026,10,9,tzinfo=timezone.utc);self.service.clock=lambda:fixed
        self.bot.restrict_chat_member.return_value=True
        self.msg.text="/mute 10m flood"
        self.assertEqual(self.service.handle("mute",self.msg).outcome,"done")
        args=self.bot.restrict_chat_member.call_args
        self.assertEqual(args.args,(1,8));self.assertEqual(args.kwargs["until_date"],int(fixed.timestamp())+600)
        self.assertFalse(args.kwargs["permissions"].can_send_messages)
        self.assertTrue(args.kwargs["use_independent_chat_permissions"])
    def test_mute_invalid_type_duration_or_failure(self):
        self.msg.text="/mute 20s motivo"
        self.assertEqual(self.service.handle("mute",self.msg).outcome,"refused")
        self.bot.restrict_chat_member.assert_not_called()
        self.msg.text="/mute 10m motivo";self.bot.get_chat.return_value=N(type="group")
        self.assertEqual(self.service.handle("mute",self.msg).outcome,"refused")
        self.bot.restrict_chat_member.assert_not_called()
        self.bot.get_chat.return_value=N(type="supergroup");self.bot.restrict_chat_member.return_value=False
        self.assertEqual(self.service.handle("mute",self.msg).outcome,"failed")
