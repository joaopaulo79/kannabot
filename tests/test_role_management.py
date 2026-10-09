import sqlite3
import unittest
from contextlib import closing
from types import SimpleNamespace as N
from requests.exceptions import Timeout
import test_governance as fixtures
from kannabot.governance import Governance

class RoleManagementTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    def native_members(self):
        self.bot.get_chat_member.side_effect=lambda chat,user:N(status="creator" if user==1 else "administrator" if user==99 else "member",can_delete_messages=True,can_restrict_members=True)
    def test_admin_assigns_and_removes_mod_but_cannot_change_admin_or_rules(self):
        self.assertEqual(self.admin.handle("role",self.message("/role mod",target=9)).outcome,"done")
        self.assertEqual(self.admin.handle("role_remove",self.message("/role_remove",target=9)).outcome,"done")
        self.assertEqual(self.admin.handle("role",self.message("/role admin",target=9)).outcome,"refused")
        self.assertEqual(self.admin.handle("role_remove",self.message("/role_remove",target=7)).outcome,"refused")
        self.assertEqual(self.admin.handle("rules_import",self.message("/rules_import")).outcome,"refused")
    def test_admin_bans_mod_owner_bans_admin_and_unban_does_not_restore(self):
        self.native_members()
        result=self.service.handle("ban",self.message("/ban teste",target=8))
        self.assertEqual(result.outcome,"done");self.assertIn("Mod revogado",result.message)
        self.assertEqual(Governance(self.path).role(1,8),"member")
        result=self.service.handle("ban",self.message("/ban teste",actor=1,target=7,event=21))
        self.assertEqual(result.outcome,"done");self.assertEqual(self.store.role(1,7),"member")
        with closing(sqlite3.connect(self.path)) as db:self.assertEqual(db.execute("SELECT COUNT(*) FROM role_changes WHERE cause='confirmed_ban'").fetchone()[0],2)
        self.bot.get_chat_member.side_effect=lambda chat,user:N(status="creator" if user==1 else "administrator" if user==99 else "kicked",can_restrict_members=True)
        self.assertEqual(self.service.handle("unban",self.message("/unban teste",actor=1,target=7,event=22)).outcome,"done")
        self.assertEqual(self.store.role(1,7),"member")
    def test_timeout_does_not_revoke_role(self):
        self.native_members();self.bot.ban_chat_member.side_effect=Timeout("unknown")
        self.assertEqual(self.service.handle("ban",self.message("/ban teste",target=8)).outcome,"uncertain")
        self.assertEqual(self.store.role(1,8),"mod")
    def test_failed_revocation_is_partial_and_ban_not_repeated(self):
        self.native_members()
        self.store.set_role=lambda *args,**kwargs: (_ for _ in ()).throw(sqlite3.OperationalError("locked"))
        result=self.service.handle("ban",self.message("/ban teste",target=8))
        self.assertEqual(result.outcome,"partial");self.assertIn("revogação",result.message)
        self.assertEqual(self.service.handle("ban",self.message("/ban teste",target=8)).outcome,"refused")
        self.bot.ban_chat_member.assert_called_once()
    def test_native_admin_refused_without_api_effect(self):
        self.assertEqual(self.service.handle("mute",self.message("/mute 1m teste",target=10)).outcome,"refused")
        self.bot.restrict_chat_member.assert_not_called()


    def test_owner_refusal_uses_kanna_voice_without_baka(self):
        result=self.service.handle("ban",self.message("/ban teste",target=1))
        self.assertEqual(result.outcome,"refused")
        self.assertIn("Você não pode banir o Dono!",result.message)
        self.assertNotIn("baka",result.message.lower())
        self.bot.ban_chat_member.assert_not_called()
