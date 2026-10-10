import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot.identities import Identities
import test_governance as fixtures

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.bot=Mock();self.user=N(id=9,username="Alice",is_bot=False)
        self.bot.get_chat_member.return_value=N(status="member",user=self.user)
        self.path=Path(self.temp.name)/"db.sqlite3"
        self.store=Identities(self.bot,(1,2),self.path)
    def test_restart_case_insensitive_and_isolation(self):
        self.store.observe_user(1,self.user)
        self.assertEqual(Identities(self.bot,(1,2),self.path).resolve(1,"@ALICE").id,9)
        with self.assertRaises(ValueError):self.store.resolve(2,"@Alice")
    def test_changed_username_or_removed_member_never_resolves(self):
        self.store.observe_user(1,self.user);self.user.username="changed"
        with self.assertRaises(ValueError):self.store.resolve(1,"@Alice")
        self.assertIsNone(self.store.username(1,9))
    def test_expiry_and_capacity(self):
        store=Identities(self.bot,(1,),self.path,clock=lambda:10,ttl=5,capacity=1)
        store.observe_user(1,self.user)
        store.clock=lambda:16
        with self.assertRaises(ValueError):store.resolve(1,"Alice")
        store.observe_user(1,N(id=10,username="Bob",is_bot=False))
        self.assertIsNone(store.username(1,9))
    def test_prepare_rejects_conflicting_reply_and_delete_username(self):
        self.store.observe_user(1,self.user)
        message=N(chat=N(id=1),text="/warn @Alice R10 motivo",from_user=N(id=7,is_bot=False),sender_chat=None,reply_to_message=N(chat=N(id=1),from_user=N(id=8,is_bot=False),sender_chat=None))
        with self.assertRaises(ValueError):self.store.prepare(message,"warn")
        with self.assertRaises(ValueError):self.store.prepare(message,"delete")

class UsernameModerationTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules
    def test_warn_by_username_and_unwarn_cannot_redirect(self):
        self.import_rules()
        old=self.bot.get_chat_member.side_effect
        self.bot.get_chat_member.side_effect=lambda chat,user:N(**vars(old(chat,user)),user=N(id=user,username="Alice" if user==9 else "Bob",is_bot=False))
        self.service.identities=Identities(self.bot,(1,2),self.path)
        self.service.identities.observe_user(1,N(id=9,username="Alice",is_bot=False))
        self.service.identities.observe_user(1,N(id=10,username="Bob",is_bot=False))
        msg=self.message("/warn @Alice R10 motivo");msg.reply_to_message=None
        result=self.service.handle("warn",msg)
        self.assertEqual(result.outcome,"done");self.assertEqual(self.store.history(1,9)[0],1)
        msg=self.message("/unwarn @Bob 1 errado");msg.reply_to_message=None
        self.assertEqual(self.admin.handle("unwarn",msg).outcome,"refused")
        self.assertEqual(self.store.history(1,9)[0],1)
