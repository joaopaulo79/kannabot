import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import patch
import test_governance
import test_registration
from kannabot._config.configuracao import carregar_configuracao, ErroConfiguracao
from kannabot.group_registry import GroupRegistry
from kannabot.registration import Registration
from kannabot.roles import Roles
from kannabot.permissions import PermissionDenied
from kannabot.help import Help
from kannabot.governance import CAPABILITIES
from kannabot.app import create_app
from dataclasses import replace


class OperatorRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.f=test_registration.RegistrationTests()
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        f=self.f
        f.service=Registration(f.bot,f.registry,f.audit,operators=(7,),clock=lambda:f.now)
        f.status="member"

    def test_operator_registers_without_real_owner_or_registrar_grant(self):
        self.assertIn("Grupo cadastrado",self.f.activate())
        self.assertEqual(self.f.registry.get(-10),(-20,7))

    def test_operator_still_requires_membership_and_bot_rights(self):
        token=self.f.ticket()
        self.f.status="left"
        self.assertIn("membro identificado",self.f.activate(token))
        self.assertIsNone(self.f.registry.get(-10))
        self.f.status="restricted"
        self.assertIn("membro identificado",self.f.activate(token))
        self.f.bot.get_chat_member.side_effect=lambda chat,user:N(status="administrator" if user==99 else "member",can_delete_messages=False,can_restrict_members=True)
        self.assertIn("permissões",self.f.activate(token))
        self.assertIsNone(self.f.registry.get(-10))

    def test_operator_cannot_bind_logs_where_they_are_not_admin(self):
        self.f.bot.get_chat_member.side_effect=lambda chat,user:N(status="administrator" if user==99 else "member",can_delete_messages=True,can_restrict_members=True)
        self.assertIn("administrador do grupo",self.f.service.handle("cadastrar_logs",self.f.message("/cadastrar_logs",-20)))

    def test_old_registration_column_is_upgraded_without_losing_link(self):
        path=Path(self.f.folder.name)/"old.sqlite3"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE group_registrations(chat_id BIGINT PRIMARY KEY,log_chat_id BIGINT UNIQUE,owner_id BIGINT,registered_at TEXT)")
            db.execute("INSERT INTO group_registrations VALUES(-10,-20,7,'now')")
        self.assertEqual(GroupRegistry(path).get(-10),(-20,7))
        self.assertEqual(GroupRegistry(path).get(-10),(-20,7))


class OperatorCapabilitiesTests(unittest.TestCase):
    def setUp(self):
        self.f=test_governance.GovernanceTests()
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        f=self.f
        f.roles=Roles(f.bot,(1,2),f.store,operators=(7,))
        f.service.roles=f.roles;f.service.permissions.roles=f.roles
        f.admin.roles=f.roles

    def test_operator_has_own_role_and_can_import_rules_and_assign_admin(self):
        f=self.f
        self.assertEqual(f.roles.role(1,7),'operator')
        self.assertEqual(f.admin.handle('rules_import',f.message('/rules_import')).outcome,'done')
        self.assertEqual(f.admin.handle('role',f.message('/role admin',target=9,event=21)).outcome,'done')
        self.assertEqual(f.store.role(1,9),'admin')
        event=json.loads((Path(f.folder.name)/'audit.jsonl').read_text(encoding='utf-8').splitlines()[-1])
        self.assertEqual(event['actor_role'],'operator')

    def test_operator_cannot_punish_real_owner_and_native_admin_limit_remains(self):
        f=self.f
        self.assertEqual(f.roles.role(1,1),'owner')
        with self.assertRaises(PermissionDenied):f.roles.target(1,7,1,'ban')
        self.assertEqual(f.service.handle('ban',f.message('/ban teste',target=10)).outcome,'refused')
        f.bot.ban_chat_member.assert_not_called()

    def test_configuration_removal_revokes_privilege_and_does_not_change_stored_role(self):
        f=self.f
        other=Roles(f.bot,(1,2),f.store)
        self.assertEqual(other.role(1,7),'admin')
        with self.assertRaises(PermissionDenied):other.authorize(1,7,'rules')
        self.assertEqual(f.store.role(1,7),'admin')

    def test_operator_is_not_assignable_or_removable_by_role_command(self):
        f=self.f
        with self.assertRaises(ValueError):f.store.set_role(1,9,'operator',7)
        with self.assertRaises(PermissionDenied):f.roles.assign(1,1,7,'member')
        self.assertEqual(f.roles.role(1,7),'operator')

    def test_operator_cannot_bypass_unknown_group_or_membership_failure(self):
        f=self.f
        with self.assertRaises(PermissionDenied):f.roles.authorize(999,7,'rules')
        f.bot.get_chat_member.side_effect=RuntimeError('private')
        with self.assertRaises(PermissionDenied):f.roles.authorize(1,7,'rules')

    def test_help_identifies_operator_and_includes_owner_capabilities(self):
        helper=Help(self.f.service)
        self.assertEqual(helper.role(self.f.message('/help')),'operator')
        self.assertIn('Operador',helper.render('operator'))
        self.assertIn('rules_import',helper.allowed('operator'))
        self.assertEqual(CAPABILITIES['operator'],CAPABILITIES['owner'])
        for page in helper.allowed('operator'):self.assertLess(len(helper.render('operator',page)),4096)

    def test_application_passes_operator_config_to_roles_and_registration(self):
        f=self.f
        cfg=replace(f.config,operator_ids=(7,))
        bot=create_app(cfg,f.bot,f.folder.name)
        self.assertEqual(bot.kanna_roles.role(1,7),'operator')
        self.assertIn(7,bot.kanna_registration.operators)
        self.assertIn(7,bot.kanna_registration.registrars)


class OperatorConfigurationTests(unittest.TestCase):
    def test_operator_ids_are_numeric_optional_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'groups.json').write_text('{"grupos_id": []}')
            base={'CHAVE_API_BOT':'123:fake','BOT_USERNAME':'TesteBot','CAMINHO_AUTORZACAO':'groups.json'}
            for text,expected in (('',()),('7, 8,7',(7,8))):
                with patch.dict(os.environ,dict(base,KANNA_OPERATOR_IDS=text),clear=True):self.assertEqual(carregar_configuracao(p).operator_ids,expected)
            for text in ('@usuario','-1','0','7,,8','7;8'):
                with patch.dict(os.environ,dict(base,KANNA_OPERATOR_IDS=text),clear=True):
                    with self.assertRaises(ErroConfiguracao):carregar_configuracao(p)
