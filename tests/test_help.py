import unittest
from types import SimpleNamespace as N
from unittest.mock import Mock
import test_governance as fixtures
from kannabot.help import Help, register

class HelpTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    def get(self,actor):return Help(self.service).handle(self.message('/help@TesteBot',actor=actor))
    def test_mod_has_only_its_commands(self):
        result=self.get(8);self.assertEqual(result.outcome,'done')
        for command in ('warn','warnings','delete','delwarn','mute','catalog','detections','dismiss','review'):
            self.assertIn('<code>/'+command,result.message)
        for command in ('ban','kick','unban','unwarn','role','rules_import','rule_set'):
            self.assertNotIn('<code>/'+command,result.message)
        self.assertNotIn('p2',result.message)
    def test_admin_and_owner_commands_follow_capabilities(self):
        admin=self.get(7);owner=self.get(1)
        for command in ('ban','kick','unban','unwarn','role','role_remove'):self.assertIn('<code>/'+command,admin.message)
        self.assertNotIn('<code>/rules_import',admin.message);self.assertNotIn('<code>/role admin',admin.message)
        for command in ('rules_import','rule_set','rule_disable'):self.assertIn('<code>/'+command,owner.message)
        self.assertIn('<code>/role admin',owner.message)
    def test_unauthorized_identity_group_and_lookup_failure(self):
        helper=Help(self.service)
        self.assertEqual(self.get(9).outcome,'refused')
        self.assertEqual(self.get(10).outcome,'refused') # Native admin with cosmetic title, internal Member.
        message=self.message('/help',chat=3);self.assertEqual(helper.handle(message).outcome,'refused')
        message=self.message('/help');message.sender_chat=N(id=1);self.assertEqual(helper.handle(message).outcome,'refused')
        self.bot.get_chat_member.side_effect=RuntimeError('unavailable');self.assertEqual(helper.handle(self.message('/help')).outcome,'refused')
    def test_no_sanctions_and_role_change_is_immediate(self):
        self.assertEqual(self.get(8).outcome,'done');self.store.set_role(1,8,'member',1)
        self.assertEqual(self.get(8).outcome,'refused')
        self.assertEqual(self.store.history(1,9)[0],0)
        self.bot.delete_message.assert_not_called();self.bot.ban_chat_member.assert_not_called();self.bot.restrict_chat_member.assert_not_called()
    def test_registration_and_send_failure(self):
        helper=Help(self.service);handlers={}
        def decorator(**kwargs):
            def save(handler):handlers[kwargs['commands'][0]]=handler;return handler
            return save
        self.bot.message_handler.side_effect=decorator;register(self.bot,helper)
        handlers['help'](self.message('/help',actor=8));self.bot.send_message.assert_called()
        self.bot.send_message.side_effect=RuntimeError('failed')
        handlers['help'](self.message('/help',actor=8))
