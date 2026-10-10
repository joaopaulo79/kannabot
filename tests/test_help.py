import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as N
from unittest.mock import Mock
import test_governance as fixtures
from kannabot.help import Help, register, CATEGORIES

class HelpTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    def get(self,actor):return Help(self.service).handle(self.message('/help@TesteBot',actor=actor))
    def test_mod_has_only_its_commands(self):
        helper=Help(self.service);self.assertEqual(self.get(8).outcome,'done')
        allowed=helper.allowed('mod')
        for command in ('warn','warnings','delete','delwarn','mute','catalog','detections','dismiss','review'):self.assertIn(command,allowed)
        for command in ('ban','kick','unban','unwarn','role','rules_import','rule_set'):self.assertNotIn(command,allowed)
        self.assertNotIn('p2',''.join(helper.render('mod',page) for page in allowed))
    def test_admin_and_owner_commands_follow_capabilities(self):
        helper=Help(self.service);admin=helper.allowed('admin');owner=helper.allowed('owner')
        for command in ('ban','kick','unban','unwarn','role','role_remove'):self.assertIn(command,admin)
        self.assertNotIn('rules_import',admin)
        for command in ('rules_import','rule_set','rule_disable'):self.assertIn(command,owner)
        self.assertEqual(self.get(1).outcome,'done')
    def test_unauthorized_identity_group_and_lookup_failure(self):
        helper=Help(self.service)
        self.assertEqual(self.get(9).outcome,'refused');self.assertEqual(self.get(10).outcome,'refused')
        self.assertEqual(helper.handle(self.message('/help',chat=3)).outcome,'refused')
        message=self.message('/help');message.sender_chat=N(id=1);self.assertEqual(helper.handle(message).outcome,'refused')
        self.bot.get_chat_member.side_effect=RuntimeError('unavailable');self.assertEqual(helper.handle(self.message('/help')).outcome,'refused')
    def test_no_sanctions_and_role_change_is_immediate(self):
        self.assertEqual(self.get(8).outcome,'done');self.store.set_role(1,8,'member',1);self.assertEqual(self.get(8).outcome,'refused')
        self.assertEqual(self.store.history(1,9)[0],0)
        self.bot.delete_message.assert_not_called();self.bot.ban_chat_member.assert_not_called();self.bot.restrict_chat_member.assert_not_called()
    def open_help(self,actor=7,**kwargs):
        self.bot.send_message.return_value=N(message_id=500)
        helper=Help(self.service,**kwargs);helper.open(self.message('/help',actor=actor))
        token=next(iter(helper.sessions));return helper,token
    def call(self,token,page,actor=7,chat=1,message=500):
        return N(id='callback',data=f'h:{token}:{page}',from_user=N(id=actor,is_bot=False),message=N(chat=N(id=chat),message_id=message))
    def test_navigation_edits_same_message_and_home(self):
        helper,token=self.open_help()
        for page in ('cat_warnings','warn','warnings','cat_warnings','home'):helper.callback(self.call(token,page))
        self.assertEqual(self.bot.edit_message_text.call_count,5)
        for call in self.bot.edit_message_text.call_args_list:
            self.assertEqual(call.kwargs['chat_id'],1);self.assertEqual(call.kwargs['message_id'],500)
        self.bot.send_message.assert_called_once()
        self.assertEqual(helper.sessions[token].page,'home')
    def test_foreign_user_group_message_and_unknown_token(self):
        helper,token=self.open_help()
        for call in (self.call(token,'warn',actor=8),self.call(token,'warn',chat=2),self.call(token,'warn',message=501),self.call('unknown','warn')):
            helper.callback(call)
        self.bot.edit_message_text.assert_not_called();self.assertEqual(self.bot.answer_callback_query.call_count,4)
    def test_expiration_and_capacity(self):
        now=[0];helper,token=self.open_help(clock=lambda:now[0],ttl=10,capacity=1)
        now[0]=10;helper.callback(self.call(token,'warn'));self.bot.edit_message_text.assert_not_called()
        self.assertIn('expirou',self.bot.answer_callback_query.call_args.kwargs['text'])
        helper.open(self.message('/help'));first=next(iter(helper.sessions));helper.open(self.message('/help'))
        self.assertEqual(len(helper.sessions),1);self.assertNotIn(first,helper.sessions)
    def test_callback_rechecks_role_and_lookup_failure(self):
        helper,token=self.open_help();self.store.set_role(1,7,'mod',1)
        helper.callback(self.call(token,'ban'));self.bot.edit_message_text.assert_not_called()
        helper.callback(self.call(token,'home'));self.assertIn('Mod',self.bot.edit_message_text.call_args.args[0])
        self.bot.edit_message_text.reset_mock();self.bot.get_chat_member.side_effect=RuntimeError('unavailable')
        helper.callback(self.call(token,'warn'));self.bot.edit_message_text.assert_not_called()
    def test_failed_edit_can_retry_and_repeated_click_does_not_edit(self):
        helper,token=self.open_help();self.bot.edit_message_text.side_effect=RuntimeError('failed')
        helper.callback(self.call(token,'warn'));self.assertEqual(helper.sessions[token].page,'home')
        self.bot.edit_message_text.side_effect=None;helper.callback(self.call(token,'warn'));helper.callback(self.call(token,'warn'))
        self.assertEqual(self.bot.edit_message_text.call_count,2);self.assertEqual(helper.sessions[token].page,'warn')
    def test_concurrent_same_page_is_edited_once(self):
        helper,token=self.open_help()
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:helper.callback(self.call(token,'warn')),range(2)))
        self.bot.edit_message_text.assert_called_once()
    def test_pages_fit_and_callback_payloads_are_bounded(self):
        helper=Help(self.service)
        for role in ('owner','admin','mod'):
            pages=['home']+list(helper.allowed(role))+['cat_'+category for category in CATEGORIES if any(p[1]==category for p in helper.allowed(role).values())]
            for page in pages:
                self.assertLess(len(helper.render(role,page)),3500)
                for row in helper.keyboard(role,page,'abcdefghijkl').keyboard:
                    for button in row:self.assertLessEqual(len(button.callback_data.encode()),64)
    def test_registration_separates_help_callbacks(self):
        messages={};callbacks=[]
        def decorator(**kwargs):
            def save(handler):messages[kwargs['commands'][0]]=handler;return handler
            return save
        def callback_decorator(**kwargs):
            def save(handler):callbacks.append((kwargs['func'],handler));return handler
            return save
        self.bot.message_handler.side_effect=decorator;self.bot.callback_query_handler.side_effect=callback_decorator
        self.bot.send_message.return_value=N(message_id=500)
        helper=Help(self.service);register(self.bot,helper);messages['help'](self.message('/help',actor=8))
        self.assertTrue(callbacks[0][0](N(data='h:token:home')));self.assertFalse(callbacks[0][0](N(data='emote')))
        self.bot.send_message.side_effect=RuntimeError('failed');messages['help'](self.message('/help',actor=8))
