"""Integration tests use a dedicated, disposable database supplied privately."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest.mock import Mock
import psycopg
import test_governance as fixtures
from kannabot import database
from kannabot.administration import Administration
from kannabot.antispam import Detection
from kannabot.audit import Audit
from kannabot.evidence import Evidence
from kannabot.governance import Governance
from kannabot.identities import Identities
from kannabot.moderation import Moderation
from kannabot.review import Review
from kannabot.review_store import ReviewStore
from kannabot.roles import Roles
from kannabot._config.configuracao import Configuracao, ErroConfiguracao
from kannabot.app import create_app

URL = os.getenv('KANNA_TEST_DATABASE_URL')
TABLES = 'evidence_actions,evidence,infractions,warnings,sanctions,role_changes,roles,rules,identities,detections'


@unittest.skipUnless(URL, 'Dedicated PostgreSQL test database not configured')
class PostgreSQLTests(unittest.TestCase):
    message = fixtures.GovernanceTests.message
    import_rules = fixtures.GovernanceTests.import_rules

    def setUp(self):
        fixtures.GovernanceTests.setUp(self)
        database.initialize(URL)
        with psycopg.connect(URL) as connection:
            connection.execute(f'TRUNCATE {TABLES} RESTART IDENTITY CASCADE')
        self.path = URL
        self.store = Governance(URL)
        self.roles = Roles(self.bot,(1,2),self.store)
        self.roles.assign(1,1,7,'admin')
        self.roles.assign(1,1,8,'mod')
        self.service = Moderation(self.bot,self.config,self.store,self.audit,roles=self.roles)
        self.admin = Administration(self.service,self.store,self.roles,self.audit)

    test_capability_and_hierarchy = fixtures.GovernanceTests.test_capability_and_hierarchy
    test_roles_are_internal_isolated_and_removal_immediate = fixtures.GovernanceTests.test_roles_are_internal_isolated_and_removal_immediate
    test_catalog_seed_revoked_and_undefined = fixtures.GovernanceTests.test_catalog_seed_revoked_and_undefined
    test_rule_versions_points_cancellation_and_no_auto_ban = fixtures.GovernanceTests.test_rule_versions_points_cancellation_and_no_auto_ban
    test_mute_rule_bounds = fixtures.GovernanceTests.test_mute_rule_bounds
    test_rule_edit_disable_and_invalid_input = fixtures.GovernanceTests.test_rule_edit_disable_and_invalid_input
    test_real_review_records_weight_only_after_explicit_decision = fixtures.GovernanceTests.test_real_review_records_weight_only_after_explicit_decision
    test_review_enforces_mod_capability_and_target_hierarchy = fixtures.GovernanceTests.test_review_enforces_mod_capability_and_target_hierarchy
    test_review_revoked_rule_and_revoked_actor_leave_no_effect = fixtures.GovernanceTests.test_review_revoked_rule_and_revoked_actor_leave_no_effect
    make_review = fixtures.GovernanceTests.make_review

    def test_schema_idempotence_and_fresh_database(self):
        for _ in range(2):
            Governance(URL)
            ReviewStore(URL)
            Identities(self.bot,(1,2),URL)
            Evidence(URL,self.audit.clean)
        self.assertEqual(self.store.history(1,9)[0],0)
        self.assertEqual(self.store.catalog(1),[])
        with psycopg.connect(URL) as connection:
            self.assertEqual(connection.execute('SELECT version FROM kanna_schema').fetchall(),[(1,)])

    def test_large_ids_unicode_null_and_zero_remain_distinct(self):
        chat,user,actor = -1001234567890,4503599627370000,4503599627370001
        self.store.add(chat,user,actor,'ação 🍀','now','zero',manual_weight=0)
        self.store.start_delwarn(chat,123,actor,user,'manual')
        entries = self.store.detailed_entries(chat,user)
        self.assertEqual({entry['weight'] for entry in entries},{0,None})
        self.assertEqual(self.store.history(chat,user)[0],2)
        self.assertEqual(self.store.points(chat,user),0)
        self.assertEqual(self.store.history(chat+1,user)[0],0)
        with psycopg.connect(URL) as connection:
            self.assertEqual(connection.execute('SELECT autor_id FROM historico_advertencias ORDER BY registro LIMIT 1').fetchone()[0],actor)

    def test_concurrent_warning_and_delwarn_claims(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.store.add(1,9,7,'motivo','now','event',manual_weight=2),range(4)))
        self.assertEqual(sum(results),1)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.store.start_delwarn(1,10,7,9,'motivo',manual_weight=3),range(4)))
        self.assertEqual(sum(result is not None for result in results),1)
        self.assertEqual(Governance(URL).points(1,9),5)

    def test_concurrent_rule_versions_and_detection_aggregation(self):
        self.import_rules()
        rule = self.store.rule(1,'R10');rule.pop('version')
        with ThreadPoolExecutor(max_workers=4) as pool:
            versions = list(pool.map(lambda _: self.store.put_rule(1,rule,1),range(4)))
        self.assertEqual(set(versions),{2,3,4,5})
        queue = ReviewStore(URL)
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda name:queue.put(Detection(name,1,9,100)),('flood','repeat','links')))
        self.assertEqual(len(queue.pending(1)),1)
        row = queue.get(1,queue.pending(1)[0][0])
        self.assertIn('flood',row['rules']);self.assertIn('links',row['rules']);self.assertIn('repeat',row['rules'])

    def test_evidence_and_identity_snapshots(self):
        from types import SimpleNamespace as N
        identities = Identities(self.bot,(1,2),URL)
        identities.observe_user(1,N(id=7,username='staff',is_bot=False))
        identities.observe_user(1,N(id=9,username='alvo',is_bot=False))
        self.service.evidence = Evidence(URL,self.audit.clean)
        message = self.message('/delwarn p2 texto');message.reply_to_message.text = 'evidência 🍀'
        self.assertEqual(self.service.handle('delwarn',message).outcome,'done')
        entry = self.store.detailed_entries(1,9)[0]
        self.assertEqual(entry['actor_username'],'staff');self.assertEqual(entry['target_username'],'alvo')
        with psycopg.connect(URL) as connection:
            self.assertIn('evidência',connection.execute('SELECT payload FROM evidencias').fetchone()[0])
        identities.observe_user(1,N(id=10,username='alvo',is_bot=False))
        self.assertIsNone(identities.username(1,9))

    def test_transaction_rollback_does_not_leave_warning(self):
        with self.assertRaises(psycopg.Error):
            self.store.add(1,9,7,'texto','now','event',rule={'code':'R10','version':1,'weight':9})
        self.assertEqual(self.store.history(1,9)[0],0)
        self.assertTrue(self.store.add(1,9,7,'texto','now','event',manual_weight=2))

    def test_database_failure_never_executes_external_action(self):
        self.store.begin = Mock(side_effect=psycopg.OperationalError('unavailable'))
        self.assertEqual(self.service.handle('ban',self.message('/ban motivo')).outcome,'failed')
        self.bot.ban_chat_member.assert_not_called()

    def test_manual_weights_cancel_restart_and_timeout(self):
        from requests.exceptions import Timeout
        for weight in range(5):
            self.assertEqual(self.service.handle('warn',self.message(f'/warn p{weight} motivo',event=30+weight)).outcome,'done')
        self.assertEqual(Governance(URL).points(1,9),10)
        entry = self.store.detailed_entries(1,9)[0]
        self.admin.handle('unwarn',self.message(f"/unwarn {entry['id']} revisão"))
        self.assertEqual(self.store.points(1,9),6)
        self.bot.delete_message.side_effect = Timeout('unknown')
        message = self.message('/delwarn p2 motivo',event=50)
        self.assertEqual(self.service.handle('delwarn',message).outcome,'uncertain')
        other = Moderation(self.bot,self.config,Governance(URL),self.audit,roles=self.roles)
        self.assertEqual(other.handle('delwarn',message).outcome,'refused')
        self.bot.delete_message.assert_called_once()

    def test_app_shares_destination_and_hides_credentials(self):
        cfg = Configuracao('123:fake',self.config.caminho_autorizacao,(1,2),'@TesteBot',database_url=URL)
        self.assertNotIn(URL,repr(cfg))
        bot = Mock();bot.message_handler.side_effect=lambda **kwargs:lambda fn:fn
        app = create_app(cfg,bot,self.folder.name)
        self.assertEqual(app.kanna_moderation.store.path,URL)
        self.assertEqual(app.kanna_review.store.path,URL)
        self.assertEqual(app.kanna_evidence.path,URL)
        self.assertNotIn(URL,app.kanna_audit.clean(URL))
        bot.infinity_polling.assert_not_called()
