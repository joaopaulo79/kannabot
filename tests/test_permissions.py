import unittest
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot.permissions import Permissions, PermissionDenied

class PermissionsTests(unittest.TestCase):
    def setUp(self):
        self.bot=Mock(); self.p=Permissions(self.bot,[-100123])
        self.msg=N(chat=N(id=-100123),from_user=N(id=7,is_bot=False),sender_chat=None)
    def test_roles(self):
        for role, allowed in (("administrator",True),("creator",True),("member",False)):
            self.bot.get_chat_member.return_value=N(status=role)
            if allowed: self.assertEqual(self.p.actor(self.msg),7)
            else:
                with self.assertRaises(PermissionDenied): self.p.actor(self.msg)
        self.bot.delete_message.assert_not_called()
    def test_exact_groups(self):
        self.assertTrue(self.p.authorized(-100123))
        self.assertFalse(self.p.authorized(-123))
        with self.assertRaises(PermissionDenied): self.p.member(-123,7)
        self.bot.get_chat_member.assert_not_called()
    def test_anonymous_or_bot_denied(self):
        for field,value in (("sender_chat",N(id=1)),("from_user",None),("from_user",N(id=9,is_bot=True))):
            original=getattr(self.msg,field); setattr(self.msg,field,value)
            with self.assertRaises(PermissionDenied): self.p.actor(self.msg)
            setattr(self.msg,field,original)
    def test_query_failure_is_closed(self):
        self.bot.get_chat_member.side_effect=RuntimeError("secret response")
        with self.assertRaises(PermissionDenied) as error: self.p.actor(self.msg)
        self.assertNotIn("secret",str(error.exception))
    def test_protected_target(self):
        self.bot.get_chat_member.return_value=N(status="creator")
        with self.assertRaises(PermissionDenied): self.p.target(-100123,4)
    def test_bot_rights(self):
        self.bot.get_me.return_value=N(id=99)
        self.bot.get_chat_member.return_value=N(status="administrator",can_delete_messages=False)
        with self.assertRaises(PermissionDenied): self.p.bot_right(-100123,"can_delete_messages")
        self.bot.get_chat_member.return_value.can_delete_messages=True
        self.p.bot_right(-100123,"can_delete_messages")
