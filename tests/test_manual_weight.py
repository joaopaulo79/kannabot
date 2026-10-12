import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from types import SimpleNamespace as N
from unittest.mock import Mock
from requests.exceptions import Timeout
from telebot.apihelper import ApiTelegramException
import test_governance as fixtures
from kannabot.governance import Governance
from kannabot.identities import Identities
from kannabot.evidence import Evidence
from kannabot.moderation import Moderation


class ManualWeightTests(unittest.TestCase):
    setUp = fixtures.GovernanceTests.setUp
    message = fixtures.GovernanceTests.message
    import_rules = fixtures.GovernanceTests.import_rules

    def test_warn_all_weights_persist_reason_audit_and_cancel(self):
        for weight in range(5):
            with self.subTest(weight=weight):
                result = self.service.handle('warn', self.message(f'/warn p{weight} motivo <teste>', event=30+weight))
                self.assertEqual(result.outcome, 'done')
                entry = self.store.detailed_entries(1,9)[0]
                self.assertEqual(entry['weight'], weight)
                self.assertEqual(entry['reason'], 'motivo <teste>')
                self.assertIsNone(entry['rule_code'])
                self.assertIsNone(entry['snapshot'])
                self.assertIn('motivo &lt;teste&gt;', result.message)
                audit = json.loads(self.audit.path.read_text(encoding='utf-8').splitlines()[-1])
                self.assertEqual(audit['weight'], str(weight))
                self.assertEqual(audit['actor'], 7)
                self.assertEqual(audit['target'], 9)
        self.assertEqual(Governance(self.path).points(1,9), 10)
        self.assertIn('revisão humana', self.service.handle('warnings',self.message('/warnings')).message)
        entry = self.store.detailed_entries(1,9)[0]
        self.assertEqual(self.admin.handle('unwarn',self.message(f"/unwarn {entry['id']} erro")).outcome, 'done')
        self.assertEqual(self.store.points(1,9), 6)
        self.bot.delete_message.assert_not_called()
        self.bot.ban_chat_member.assert_not_called()
        self.bot.restrict_chat_member.assert_not_called()

    def test_delwarn_all_weights_and_audit(self):
        for weight in range(5):
            message = self.message(f'/delwarn p{weight} motivo', event=30+weight)
            message.reply_to_message.message_id = 100+weight
            result = self.service.handle('delwarn', message)
            self.assertEqual(result.outcome, 'done')
            self.assertIn(f'Peso: {weight} pontos', result.message)
            entry = self.store.detailed_entries(1,9)[0]
            self.assertEqual(entry['weight'], weight)
            self.assertEqual(entry['reason'], 'motivo')
            self.assertIsNone(entry['rule_code'])
            audit = json.loads(self.audit.path.read_text(encoding='utf-8').splitlines()[-1])
            self.assertEqual(audit['weight'], str(weight))
        self.assertEqual(self.store.points(1,9),10)
        self.assertEqual(self.bot.delete_message.call_count,5)

    def test_invalid_weights_missing_reason_and_rule_combinations_have_no_effects(self):
        self.import_rules()
        self.service.evidence = Mock()
        arguments = ('p5 motivo','p10 motivo','p-1 motivo','p1.5 motivo','p2,5 motivo',
                     'p+2 motivo','p02 motivo','p motivo','p2','p2 R10 motivo',
                     'R10 p2 motivo','p2 p3 motivo')
        for command in ('warn','delwarn'):
            for arguments_text in arguments:
                with self.subTest(command=command,arguments=arguments_text):
                    result = self.service.handle(command,self.message(f'/{command} {arguments_text}'))
                    self.assertEqual(result.outcome,'refused')
        self.assertEqual(self.store.history(1,9)[0],0)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sanctions').fetchone()[0],0)
        self.bot.delete_message.assert_not_called()
        self.service.evidence.capture.assert_not_called()

    def test_weight_only_first_position_and_catalog_unchanged(self):
        result = self.service.handle('warn',self.message('/warn conversar sobre p2'))
        self.assertEqual(result.outcome,'done')
        entry = self.store.detailed_entries(1,9)[0]
        self.assertEqual(entry['weight'],0)
        self.assertEqual(entry['reason'],'conversar sobre p2')
        self.import_rules()
        self.assertEqual(self.service.handle('warn',self.message('/warn R10 motivo',event=21)).outcome,'done')
        self.assertEqual(self.store.detailed_entries(1,9)[0]['weight'],3)

    def test_username_warn_and_delwarn_requires_reply(self):
        identities = Identities(self.bot,(1,2),self.path)
        self.service.identities = identities
        identities.observe_user(1,N(id=9,username='alvo',is_bot=False))
        original = self.bot.get_chat_member.side_effect
        self.bot.get_chat_member.side_effect = lambda chat,user: N(status='member',user=N(id=9,username='alvo',is_bot=False)) if user==9 else original(chat,user)
        message = self.message('/warn @alvo p2 motivo')
        message.reply_to_message = None
        self.assertEqual(self.service.handle('warn',message).outcome,'done')
        self.assertEqual(self.store.points(1,9),2)
        message = self.message('/delwarn p2 motivo',event=21)
        message.reply_to_message = None
        self.assertEqual(self.service.handle('delwarn',message).outcome,'refused')
        self.bot.delete_message.assert_not_called()

    def test_permissions_and_group_isolation(self):
        for command in ('warn','delwarn'):
            for kwargs in ({'actor':9},{'actor':8,'target':7},{'chat':3}):
                self.assertEqual(self.service.handle(command,self.message(f'/{command} p2 motivo',**kwargs)).outcome,'refused')
        self.assertEqual(self.service.handle('warn',self.message('/warn p2 motivo',actor=8)).outcome,'done')
        self.assertEqual(self.store.points(2,9),0)
        self.bot.delete_message.assert_not_called()

    def test_restart_and_duplicate_warn_preserve_single_weight(self):
        message = self.message('/warn p2 motivo')
        self.assertEqual(self.service.handle('warn',message).outcome,'done')
        other = Moderation(self.bot,self.config,Governance(self.path),self.audit,roles=self.roles)
        self.assertEqual(other.handle('warn',message).outcome,'refused')
        self.assertEqual(self.store.history(1,9)[0],1)
        self.assertEqual(self.store.points(1,9),2)

    def test_delwarn_partial_and_timeout_keep_weight_and_do_not_retry(self):
        for error,outcome in ((ApiTelegramException('deleteMessage',None,{'error_code':400,'description':'denied'}),'partial'),(Timeout('unknown'),'uncertain')):
            with self.subTest(outcome=outcome):
                message = self.message('/delwarn p2 motivo',event=30 if outcome=='partial' else 31)
                message.reply_to_message.message_id = message.message_id
                self.bot.delete_message.side_effect = error
                result = self.service.handle('delwarn',message)
                self.assertEqual(result.outcome,outcome)
                self.assertEqual(self.store.detailed_entries(1,9)[0]['weight'],2)
                other = Moderation(self.bot,self.config,Governance(self.path),self.audit,roles=self.roles)
                self.assertEqual(other.handle('delwarn',message).outcome,'refused')
        self.assertEqual(self.store.points(1,9),4)
        self.assertEqual(self.bot.delete_message.call_count,2)

    def test_persistence_rejects_invalid_weight_before_writes(self):
        self.import_rules()
        for method in (lambda weight,rule=None: self.store.add(1,9,7,'motivo','now','test',rule,weight),
                       lambda weight,rule=None: self.store.start_delwarn(1,10,7,9,'motivo',rule,weight)):
            for weight in (-1,5,True,2.5,'2'):
                with self.assertRaises(ValueError):method(weight)
            with self.assertRaises(ValueError):method(2,self.store.rule(1,'R10'))
        self.assertEqual(self.store.history(1,9)[0],0)

    def test_concurrent_delwarn_claim_keeps_one_manual_weight(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.store.start_delwarn(1,10,7,9,'motivo',manual_weight=2),range(2)))
        self.assertEqual(sum(result is not None for result in results),1)
        self.assertEqual(Governance(self.path).points(1,9),2)

    def test_manual_delwarn_evidence_cancel_and_storage_failure(self):
        self.service.evidence = Evidence(self.path,self.audit.clean)
        message = self.message('/delwarn p2 motivo')
        message.reply_to_message.text = 'texto de teste'
        def delete(chat,message_id):
            with closing(sqlite3.connect(self.path)) as db:
                self.assertIn('texto de teste',db.execute('SELECT payload FROM evidence').fetchone()[0])
            return True
        self.bot.delete_message.side_effect = delete
        self.assertEqual(self.service.handle('delwarn',message).outcome,'done')
        entry = self.store.detailed_entries(1,9)[0]
        self.assertEqual(self.admin.handle('unwarn',self.message(f"/unwarn {entry['id']} erro")).outcome,'done')
        self.assertEqual(self.store.points(1,9),0)
        self.assertEqual(self.store.detailed_entries(1,9)[0]['weight'],2)
        self.bot.delete_message.reset_mock()
        self.store.start_delwarn = Mock(side_effect=sqlite3.OperationalError('locked'))
        message = self.message('/delwarn p3 motivo',event=21)
        message.reply_to_message.message_id = 11
        self.assertEqual(self.service.handle('delwarn',message).outcome,'failed')
        self.bot.delete_message.assert_not_called()

    def test_manual_delwarn_capture_failure_prevents_warning(self):
        self.service.evidence = Mock()
        self.service.evidence.capture.side_effect = sqlite3.OperationalError('locked')
        self.assertEqual(self.service.handle('delwarn',self.message('/delwarn p2 motivo')).outcome,'failed')
        self.bot.delete_message.assert_not_called()
        self.assertEqual(self.store.history(1,9)[0],0)
