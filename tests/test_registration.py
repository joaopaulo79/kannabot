import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock, patch
from kannabot import database
from kannabot.app import create_app
from kannabot.audit import Audit
from kannabot.group_registry import GroupRegistry, GroupAccess, RegistrationError
from kannabot.permissions import Permissions
from kannabot.registration import Registration, register
from kannabot.roles import Roles
from kannabot.governance import Governance
from kannabot.identities import Identities
from kannabot._config.configuracao import Configuracao, carregar_configuracao, ErroConfiguracao


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/"test.sqlite3"
        self.registry=GroupRegistry(self.path)
        self.now=1000
        self.bot=Mock()
        self.bot.get_me.return_value=N(id=99)
        self.bot.get_chat.side_effect=lambda chat:N(id=chat,type="supergroup",username=None,title="Logs")
        self.status="creator"
        self.bot.get_chat_member.side_effect=self.member
        self.audit=Audit(self.bot,path=Path(self.folder.name)/"audit.jsonl",
                         destination=GroupAccess(self.registry).destination)
        self.service=Registration(self.bot,self.registry,self.audit,(7,),clock=lambda:self.now)

    def member(self, chat, user):
        return N(status="administrator" if user==99 or chat==-20 else self.status,
                 can_delete_messages=True,can_restrict_members=True)

    def message(self, text, chat=-10, user=7, **kw):
        return N(chat=N(id=chat,type="supergroup",title="Grupo"),from_user=N(id=user,username="dono",is_bot=False),
                 sender_chat=None,text=text,message_id=5,**kw)

    def ticket(self):
        result=self.service.handle("cadastrar_logs",self.message("/cadastrar_logs",-20))
        self.assertIn("/cadastrar_grupo ",result)
        return result.split("/cadastrar_grupo ")[1].split()[0]

    def activate(self,token=None,chat=-10,user=7):
        token=token or self.ticket()
        return self.service.handle("cadastrar_grupo",self.message("/cadastrar_grupo "+token,chat,user))

    def test_success_persists_and_routes_only_to_paired_private_group(self):
        token=self.ticket()
        self.assertIsNone(self.registry.get(-10))
        self.assertIn("Grupo cadastrado",self.activate(token))
        self.assertEqual(GroupRegistry(self.path).get(-10),(-20,7))
        self.assertEqual(self.bot.send_message.call_args.args[0],-20)
        self.assertIsNone(self.registry.get(-20))
        contents=(Path(self.folder.name)/"audit.jsonl").read_text(encoding='utf-8')
        self.assertNotIn(token,contents)
        self.assertNotIn(token,str(self.bot.send_message.call_args_list))

    def test_public_replies_never_include_ids_on_success_refusal_or_error(self):
        responses=[self.service.handle("cadastrar_grupo",self.message("/cadastrar_grupo")),self.activate()]
        self.registry.get=Mock(side_effect=RuntimeError("secret -10 -20"))
        responses.append(self.service.handle("cadastrar_grupo",self.message("/cadastrar_grupo")))
        for response in responses:
            for item in ("-10","-20","secret"):self.assertNotIn(item,response)

    def test_admin_and_member_cannot_register_even_if_globally_allowed(self):
        token=self.ticket()
        for status in ("administrator","member","left"):
            self.status=status
            self.assertIn("membro identificado" if status=="left" else "Dono real",self.activate(token))
            self.assertIsNone(self.registry.get(-10))

    def test_global_configuration_empty_or_different_actor_denies(self):
        for allowed in ((),(8,)):
            self.service.registrars=frozenset(allowed)
            self.assertIn("não está autorizada",self.service.handle("cadastrar_logs",self.message("/cadastrar_logs",-20)))
            self.assertIsNone(self.registry.get(-10))

    def test_anonymous_bot_and_private_context_denied(self):
        for mode in ("anonymous","bot","private","missing"):
            m=self.message("/cadastrar_logs",-20)
            if mode=="anonymous":m.sender_chat=N(id=-20)
            if mode=="bot":m.from_user.is_bot=True
            if mode=="private":m.chat.type="private"
            if mode=="missing":m.from_user=None
            self.assertNotIn("/cadastrar_grupo ",self.service.handle("cadastrar_logs",m))

    def test_destination_requires_human_and_bot_admin_and_private_chat(self):
        for bad in ("public","channel","human_member","bot_member","active_username"):
            self.bot.get_chat.side_effect=lambda chat:N(id=chat,type="channel" if bad=="channel" else "supergroup",username="public" if bad=="public" else None,active_usernames=["public"] if bad=="active_username" else [])
            self.bot.get_chat_member.side_effect=lambda chat,user:N(status="member" if (bad=="human_member" and user==7) or (bad=="bot_member" and user==99) else "administrator")
            self.assertNotIn("/cadastrar_grupo ",self.service.handle("cadastrar_logs",self.message("/cadastrar_logs",-20)))

    def test_source_requires_delete_and_restrict_permissions(self):
        token=self.ticket()
        for right in ("can_delete_messages","can_restrict_members"):
            def member(chat,user):
                value=self.member(chat,user)
                if chat==-10 and user==99:setattr(value,right,False)
                return value
            self.bot.get_chat_member.side_effect=member
            self.assertIn("permissões",self.activate(token))
            self.assertIsNone(self.registry.get(-10))

    def test_destination_revalidated_before_activation(self):
        token=self.ticket()
        self.bot.get_chat.side_effect=lambda chat:N(type="supergroup",username="public")
        self.assertIn("privado",self.activate(token))
        self.assertIsNone(self.registry.get(-10))
        self.assertEqual(self.registry.ticket(token,7,self.now),-20)

    def test_expired_ticket_and_actor_mismatch(self):
        token=self.ticket()
        self.service.registrars=frozenset((7,8))
        self.assertIn("outro responsável",self.activate(token,user=8))
        self.now+=600
        self.assertIn("expirado",self.activate(token))
        self.assertIsNone(self.registry.get(-10))

    def test_new_ticket_invalidates_old_and_only_hash_is_stored(self):
        first=self.ticket();second=self.ticket()
        with self.assertRaises(RegistrationError):self.registry.ticket(first,7,self.now)
        with closing(database.connect(self.path)) as db:
            rows=db.execute("SELECT token_hash FROM registration_tickets").fetchall()
        self.assertEqual(len(rows),1)
        self.assertNotEqual(rows[0][0],second)

    def test_idempotent_registration_and_used_ticket_cannot_activate_another_group(self):
        token=self.ticket();self.activate(token)
        self.bot.send_message.reset_mock()
        self.assertIn("já está cadastrado",self.activate(token))
        self.assertIn("inválido",self.activate(token,chat=-11))
        self.assertIsNone(self.registry.get(-11))

    def test_same_group_or_legacy_source_cannot_be_destination(self):
        token=self.ticket()
        self.bot.get_chat_member.side_effect=lambda chat,user:N(status="administrator" if user==99 else "creator",can_delete_messages=True,can_restrict_members=True)
        self.assertIn("distintos",self.activate(token,chat=-20))
        self.service.legacy=frozenset((-20,))
        self.assertNotIn("/cadastrar_grupo ",self.service.handle("cadastrar_logs",self.message("/cadastrar_logs",-20)))

    def test_log_group_cannot_become_source_or_be_shared(self):
        self.activate()
        with self.assertRaises(RegistrationError):self.registry.issue("a"*32,7,-20,self.now)
        self.registry.issue("b"*32,7,-30,self.now)
        with self.assertRaises(RegistrationError):self.registry.activate(-20,-30,7,"b"*32,self.now,"now")
        self.assertIsNone(self.registry.get(-20))

    def test_legacy_log_cannot_become_a_moderated_group(self):
        token=self.ticket()
        self.service.legacy_log=-10
        self.service.legacy=frozenset((-5,))
        self.assertIn("recebe logs",self.activate(token))
        self.assertIsNone(self.registry.get(-10))

    def test_legacy_log_cannot_be_reused_by_another_group(self):
        token=self.ticket()
        self.service.legacy_log=-20
        self.service.legacy=frozenset((-5,))
        self.assertIn("outro grupo legado",self.activate(token))
        self.assertIsNone(self.registry.get(-10))

    def test_telegram_failure_does_not_activate_and_error_is_sanitized(self):
        token=self.ticket();self.bot.get_chat_member.side_effect=RuntimeError("private secret")
        response=self.activate(token)
        self.assertIsNone(self.registry.get(-10))
        self.assertNotIn("secret",response)

    def test_database_failure_never_reports_success(self):
        token=self.ticket()
        self.registry.activate=Mock(side_effect=RuntimeError("private connection"))
        response=self.activate(token)
        self.assertIn("Não consegui confirmar",response)
        self.assertIsNone(self.registry.get(-10))
        self.assertNotIn("private",response)

    def test_database_result_not_confirmed_is_audited_as_uncertain(self):
        token=self.ticket()
        import sqlite3
        self.registry.activate=Mock(side_effect=sqlite3.OperationalError("private connection"))
        self.assertIn("Não consegui confirmar",self.activate(token))
        self.assertIn('"outcome": "uncertain"',(Path(self.folder.name)/"audit.jsonl").read_text(encoding='utf-8'))
        self.assertIsNone(self.registry.get(-10))

    def test_transaction_rolls_back_ticket_consumption_if_insert_fails(self):
        token=self.ticket()
        with closing(database.connect(self.path)) as db,db:
            db.execute("CREATE TRIGGER reject_registration BEFORE INSERT ON group_registrations BEGIN SELECT RAISE(ABORT, 'test'); END")
        with self.assertRaises(database.Error):self.registry.activate(-10,-20,7,token,self.now,"now")
        self.assertIsNone(self.registry.get(-10))
        self.assertEqual(self.registry.ticket(token,7,self.now),-20)

    def test_concurrent_consumption_activates_only_one_group(self):
        token=self.ticket()
        def activate(chat):
            try:return self.registry.activate(chat,-20,7,token,self.now,"now")
            except RegistrationError:return False
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(activate,(-10,-11)))
        self.assertEqual(results.count(True),1)
        self.assertEqual(len(self.registry.chats()),1)

    def test_permissions_roles_and_identities_use_live_membership(self):
        access=GroupAccess(self.registry,(-5,))
        permissions=Permissions(self.bot,access)
        roles=Roles(self.bot,access,Governance(self.path))
        identities=Identities(self.bot,access,self.path)
        self.assertFalse(permissions.authorized(-10))
        self.activate()
        self.assertTrue(permissions.authorized(-10));self.assertTrue(permissions.authorized(-5))
        self.assertEqual(roles.role(-10,7),"owner")
        identities.observe_user(-10,N(id=8,username="membro",is_bot=False))
        self.assertEqual(identities.username(-10,8),"membro")
        self.assertFalse(permissions.authorized(-20))

    def test_audit_never_uses_global_destination_for_unknown_group_or_lookup_failure(self):
        access=GroupAccess(self.registry,(-5,))
        audit=Audit(self.bot,-99,Path(self.folder.name)/"fallback",destination=lambda chat:access.destination(chat,-99))
        audit.record(-10,7,None,"x","r","refused")
        self.bot.send_message.assert_not_called()
        audit.record(-5,7,None,"x","r","done")
        self.assertEqual(self.bot.send_message.call_args.args[0],-99)
        self.bot.send_message.reset_mock()
        self.registry.get=Mock(side_effect=RuntimeError("down"))
        audit.record(-5,7,None,"x","r","done")
        self.bot.send_message.assert_not_called()

    def test_audit_routes_two_groups_separately_and_refuses_public_log(self):
        self.activate()
        self.registry.issue("a"*32,7,-30,self.now)
        self.registry.activate(-11,-30,7,"a"*32,self.now,"now")
        for source,destination in ((-10,-20),(-11,-30)):
            self.audit.record(source,7,None,"x","r","done")
            self.assertEqual(self.bot.send_message.call_args.args[0],destination)
        self.bot.send_message.reset_mock()
        self.bot.get_chat.side_effect=lambda chat:N(type="supergroup",username="public")
        self.audit.record(-10,7,None,"x","r","done")
        self.bot.send_message.assert_not_called()

    def test_handlers_registered_and_response_uses_context_without_id(self):
        handlers={}
        def decorator(**kw):
            def save(handler):handlers[kw['commands'][0]]=handler;return handler
            return save
        self.bot.message_handler.side_effect=decorator
        register(self.bot,self.service)
        handlers['cadastrar_logs'](self.message('/cadastrar_logs@TesteBot',-20))
        token=self.bot.send_message.call_args.args[1].split('/cadastrar_grupo ')[1].split()[0]
        handlers['cadastrar_grupo'](self.message('/cadastrar_grupo@TesteBot '+token))
        response=self.bot.send_message.call_args
        self.assertEqual(response.args[0],-10)
        self.assertIn('Grupo cadastrado',response.args[1])
        self.assertNotIn('-10',response.args[1]);self.assertNotIn('-20',response.args[1])

    def test_create_app_keeps_dynamic_access_for_all_features(self):
        config=Configuracao('123:fake',Path(self.folder.name)/'groups.json',(-5,),'@TesteBot',registrar_ids=(7,))
        bot=create_app(config,self.bot,self.folder.name)
        service=bot.kanna_registration
        self.assertFalse(bot.kanna_moderation.permissions.authorized(-10))
        response=service.handle('cadastrar_logs',self.message('/cadastrar_logs',-20))
        token=response.split('/cadastrar_grupo ')[1].split()[0]
        self.assertIn('Grupo cadastrado',service.handle('cadastrar_grupo',self.message('/cadastrar_grupo '+token)))
        self.assertTrue(bot.kanna_moderation.permissions.authorized(-10))
        self.assertTrue(bot.kanna_antispam.permissions.authorized(-10))
        self.assertEqual(bot.kanna_roles.role(-10,7),'owner')
        bot.kanna_identities.observe_user(-10,N(id=8,username='membro',is_bot=False))
        self.assertEqual(bot.kanna_identities.username(-10,8),'membro')


class RegistrationConfigurationTests(unittest.TestCase):
    def test_registrars_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'groups.json').write_text('{"grupos_id": []}')
            base={'CHAVE_API_BOT':'123:fake','BOT_USERNAME':'TesteBot','CAMINHO_AUTORZACAO':'groups.json'}
            for text,expected in (('',()),('7, 8,7',(7,8))):
                with patch.dict(os.environ,dict(base,KANNA_REGISTRAR_IDS=text),clear=True):
                    self.assertEqual(carregar_configuracao(p).registrar_ids,expected)
            for invalid in ('@dono','-7','0','7,,8','7;8'):
                with patch.dict(os.environ,dict(base,KANNA_REGISTRAR_IDS=invalid),clear=True):
                    with self.assertRaises(ErroConfiguracao):carregar_configuracao(p)


@unittest.skipUnless(os.getenv('KANNA_TEST_DATABASE_URL'),'Dedicated PostgreSQL test database required')
class RegistrationPostgresTests(unittest.TestCase):
    def setUp(self):
        self.path=os.environ['KANNA_TEST_DATABASE_URL']
        self.registry=GroupRegistry(self.path)
        self.clear()
        self.addCleanup(self.clear)

    def clear(self):
        with closing(database.connect(self.path)) as db,db:
            db.execute('DELETE FROM registration_tickets')
            db.execute('DELETE FROM group_registrations')

    def test_postgres_pairing_persists_and_constraints_prevent_cross_group_logs(self):
        self.registry.issue('a'*32,7,-20,1000)
        self.assertTrue(self.registry.activate(-10,-20,7,'a'*32,1000,'now'))
        self.assertEqual(GroupRegistry(self.path).get(-10),(-20,7))
        with self.assertRaises(RegistrationError):self.registry.issue('b'*32,7,-20,1000)
        self.assertFalse(self.registry.activate(-10,-20,7,'a'*32,1000,'now'))

    def test_postgres_concurrent_consumption_is_single_use(self):
        self.registry.issue('a'*32,7,-20,1000)
        def activate(chat):
            try:return self.registry.activate(chat,-20,7,'a'*32,1000,'now')
            except RegistrationError:return False
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(activate,(-10,-11)))
        self.assertEqual(results.count(True),1)

    def test_postgres_failed_insert_rolls_back_ticket(self):
        self.registry.issue('a'*32,7,-20,1000)
        with self.assertRaises(database.Error):self.registry.activate(0,-20,7,'a'*32,1000,'now')
        self.assertEqual(self.registry.ticket('a'*32,7,1000),-20)
        self.assertIsNone(self.registry.get(0))
