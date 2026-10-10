import json
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from requests.exceptions import Timeout
from kannabot._config.configuracao import Configuracao
from kannabot.audit import Audit
from kannabot.storage import WarningStore
from kannabot.governance import Governance
from kannabot.roles import Roles
from kannabot.moderation import Moderation
from kannabot.review import Review
from kannabot.review_store import ReviewStore
from kannabot.antispam import Detection
from kannabot.app import create_app
from kannabot.administration import Administration

class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/"moderation.sqlite3"
        self.store=Governance(self.path);self.bot=Mock()
        def member(chat,user):
            return N(status="creator" if user==1 else "administrator" if user in (7,10,99) else "member",custom_title="VIP <tag>" if user==10 else None,can_delete_messages=True,can_restrict_members=True)
        self.bot.get_chat_member.side_effect=member
        self.bot.get_chat.return_value=N(type="supergroup",username=None)
        self.bot.get_me.return_value=N(id=99)
        self.bot.ban_chat_member.return_value=True;self.bot.unban_chat_member.return_value=True
        self.bot.delete_message.return_value=True;self.bot.restrict_chat_member.return_value=True
        self.config=Configuracao("123:fake",Path("x"),(1,2),"@TesteBot")
        self.roles=Roles(self.bot,(1,2),self.store)
        self.roles.assign(1,1,7,"admin");self.roles.assign(1,1,8,"mod")
        self.audit=Audit(self.bot,path=Path(self.folder.name)/"audit.jsonl",secrets=("123:fake",))
        self.service=Moderation(self.bot,self.config,self.store,self.audit,roles=self.roles)
        self.admin=Administration(self.service,self.store,self.roles,self.audit)
    def message(self,text="/warn motivo",actor=7,target=9,event=20,chat=1):
        return N(chat=N(id=chat,type="supergroup"),message_id=event,text=text,sender_chat=None,from_user=N(id=actor,is_bot=False),reply_to_message=N(chat=N(id=chat),message_id=10,sender_chat=None,from_user=N(id=target,is_bot=False)))
    def import_rules(self):
        self.assertEqual(self.admin.handle("rules_import",self.message("/rules_import",actor=1)).outcome,"done")
    def test_migration_preserves_legacy_without_invented_weight(self):
        path=Path(self.folder.name)/"legacy.sqlite3";old=WarningStore(path)
        old.add(1,9,7,"legacy","old","event")
        for _ in range(2):
            new=Governance(path)
            self.assertEqual(new.history(1,9)[0],1);self.assertEqual(new.points(1,9),0)
        with closing(sqlite3.connect(path)) as db:self.assertEqual(db.execute("SELECT COUNT(*) FROM infractions").fetchone()[0],1)
    def test_roles_are_internal_isolated_and_removal_immediate(self):
        self.assertEqual(self.roles.role(1,10),"member")
        self.assertEqual(self.service.handle("warn",self.message(actor=10)).outcome,"refused")
        self.assertEqual(self.service.handle("warn",self.message(actor=8,chat=2)).outcome,"refused")
        self.roles.assign(1,1,8,"member")
        self.assertEqual(self.service.handle("warn",self.message(actor=8)).outcome,"refused")
        self.bot.ban_chat_member.assert_not_called()
    def test_capability_and_hierarchy(self):
        self.assertEqual(self.service.handle("ban",self.message("/ban motivo",actor=8)).outcome,"refused")
        self.assertEqual(self.service.handle("warn",self.message(actor=8,target=7)).outcome,"refused")
        self.assertEqual(self.service.handle("warn",self.message(actor=7,target=7)).outcome,"refused")
        self.assertEqual(self.service.handle("warn",self.message(actor=1,target=7)).outcome,"done")
        self.bot.ban_chat_member.assert_not_called()
    def test_only_owner_assigns_and_title_does_not_grant_power(self):
        result=self.admin.handle("role",self.message("/role admin",actor=7,target=9))
        self.assertEqual(result.outcome,"refused")
        self.assertEqual(self.roles.role(1,9),"member")
        result=self.admin.handle("role",self.message("/role mod",actor=1,target=9))
        self.assertEqual(result.outcome,"done");self.assertEqual(self.roles.role(1,9),"mod")
    def test_catalog_seed_revoked_and_undefined(self):
        self.import_rules();self.import_rules()
        self.assertEqual(len(self.store.catalog(1)),19)
        self.assertFalse(self.store.rule(1,"R04")["active"])
        self.assertEqual(self.store.rule(1,"R10")["version"],1)
        self.assertEqual(self.service.handle("warn",self.message("/warn R04")).outcome,"refused")
        self.assertEqual(self.service.handle("warn",self.message("/warn R01")).outcome,"refused")
        self.assertEqual(self.service.handle("mute",self.message("/mute 1h R09")).outcome,"refused")
    def test_rule_versions_points_cancellation_and_no_auto_ban(self):
        self.import_rules()
        self.assertEqual(self.service.handle("warn",self.message("/warn R10",actor=8)).outcome,"done")
        rule=self.store.rule(1,"R10");del rule["version"];rule["name"]="Nova redação"
        self.store.put_rule(1,rule,1)
        self.assertEqual(self.service.handle("warn",self.message("/warn R10",actor=8,event=21)).outcome,"done")
        self.assertEqual(self.store.points(1,9),6)
        entries=self.store.entries(1,9);self.assertEqual({entry[2] for entry in entries},{1,2})
        self.bot.ban_chat_member.assert_not_called()
        self.assertIn("revisão humana",self.service.handle("warnings",self.message("/warnings")).message)
        id=entries[0][0]
        self.assertEqual(self.admin.handle("unwarn",self.message(f"/unwarn {id} cancelamento")).outcome,"done")
        self.assertEqual(self.store.points(1,9),3)
        self.assertEqual(len(self.store.entries(1,9)),2)
        self.assertEqual(Governance(self.path).points(1,9),3)
    def test_mute_rule_bounds(self):
        self.import_rules()
        self.assertEqual(self.service.handle("mute",self.message("/mute 10m R10",actor=8)).outcome,"refused")
        self.bot.restrict_chat_member.assert_not_called()
        self.assertEqual(self.service.handle("mute",self.message("/mute 1d R10",actor=8)).outcome,"done")
    def test_restart_cannot_repeat_sanction_and_timeout_is_uncertain(self):
        self.assertEqual(self.service.handle("ban",self.message("/ban motivo")).outcome,"done")
        other=Moderation(self.bot,self.config,Governance(self.path),self.audit,roles=self.roles)
        self.assertEqual(other.handle("ban",self.message("/ban motivo")).outcome,"refused")
        self.bot.ban_chat_member.assert_called_once()
        self.bot.ban_chat_member.side_effect=Timeout("123:fake")
        self.assertEqual(self.service.handle("ban",self.message("/ban motivo",event=21)).outcome,"failed")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT status FROM sanctions WHERE event_id='manual:21'").fetchone()[0],"uncertain")
    def test_audit_includes_cosmetic_title_without_identity_confusion(self):
        self.assertEqual(self.service.handle("warn",self.message(target=10)).outcome,"done")
        event=json.loads((Path(self.folder.name)/"audit.jsonl").read_text().splitlines()[-1])
        self.assertEqual(event["target_role"],"member");self.assertEqual(event["target_title"],"VIP <tag>")
        self.assertEqual(event["actor_role"],"admin")
    def test_rule_edit_disable_and_invalid_input(self):
        data=dict(code="R20",name="Nova regra",description="Descrição",level="N2",weight=2,active=True,actions=["warn","delete","mute"])
        self.assertEqual(self.admin.handle("rule_set",self.message("/rule_set "+json.dumps(data),actor=1)).outcome,"done")
        self.assertEqual(self.admin.handle("rule_disable",self.message("/rule_disable R20",actor=1)).outcome,"done")
        self.assertEqual(self.store.rule(1,"R20")["version"],2)
        self.assertEqual(self.service.handle("warn",self.message("/warn R20")).outcome,"refused")
        data["weight"]=True
        self.assertEqual(self.admin.handle("rule_set",self.message("/rule_set "+json.dumps(data),actor=1)).outcome,"refused")

    def test_failed_identity_and_failed_storage_never_execute_sanction(self):
        self.bot.get_chat_member.side_effect=RuntimeError("private data")
        self.assertEqual(self.service.handle("ban",self.message("/ban motivo")).outcome,"refused")
        self.bot.ban_chat_member.assert_not_called()
        self.bot.get_chat_member.side_effect=lambda chat,user: N(status="creator" if user==1 else "member",custom_title=None)
        self.store.begin=Mock(side_effect=sqlite3.OperationalError("database locked"))
        self.assertEqual(self.service.handle("ban",self.message("/ban motivo",actor=1)).outcome,"failed")
        self.bot.ban_chat_member.assert_not_called()
    def test_nonparticipant_cannot_receive_staff_role(self):
        self.bot.get_chat_member.side_effect=lambda chat,user: N(status="creator" if user==1 else "restricted",is_member=False)
        self.assertEqual(self.admin.handle("role",self.message("/role mod",actor=1)).outcome,"refused")
        self.assertEqual(self.store.role(1,9),"member")
    def test_catalog_rejects_invalid_action_and_undefined_mute_level(self):
        data=dict(code="R20",name="Teste",description="Teste",level="N4",weight=None,active=True,actions=["mute"])
        self.assertEqual(self.admin.handle("rule_set",self.message("/rule_set "+json.dumps(data),actor=1)).outcome,"refused")
        data["actions"]=[{}]
        self.assertEqual(self.admin.handle("rule_set",self.message("/rule_set "+json.dumps(data),actor=1)).outcome,"refused")
        self.assertIsNone(self.store.rule(1,"R20"))

    def make_review(self):
        queue=ReviewStore(self.path)
        review=Review(self.service,queue,self.audit)
        review.observe([Detection("flood",1,9,10)])
        return review,queue,queue.pending(1)[0][0]
    def test_real_review_records_weight_only_after_explicit_decision(self):
        self.import_rules()
        review,queue,id=self.make_review()
        self.assertEqual(self.store.points(1,9),0)
        self.bot.ban_chat_member.assert_not_called()
        result=review.handle("review",self.message(f"/review {id} warn R10 evidência",actor=8))
        self.assertEqual(result.outcome,"done")
        self.assertEqual(self.store.points(1,9),3)
        self.assertEqual(queue.get(1,id)["status"],"resolved")
        self.assertEqual(review.handle("review",self.message(f"/review {id} warn R10",actor=8)).outcome,"refused")
        self.assertEqual(self.store.history(1,9)[0],1)
        self.bot.ban_chat_member.assert_not_called()
    def test_review_enforces_mod_capability_and_target_hierarchy(self):
        self.import_rules()
        review,queue,id=self.make_review()
        self.assertEqual(review.handle("review",self.message(f"/review {id} ban R16",actor=8)).outcome,"refused")
        self.bot.ban_chat_member.assert_not_called()
        review.observe([Detection("flood",1,7,11)])
        id=queue.pending(1)[0][0]
        self.assertEqual(review.handle("review",self.message(f"/review {id} warn R10",actor=8,event=21)).outcome,"refused")
        self.assertEqual(self.store.points(1,7),0)
    def test_review_revoked_rule_and_revoked_actor_leave_no_effect(self):
        self.import_rules()
        review,queue,id=self.make_review()
        self.admin.handle("rule_disable",self.message("/rule_disable R10",actor=1))
        self.assertEqual(review.handle("review",self.message(f"/review {id} warn R10",actor=8)).outcome,"refused")
        self.assertEqual(queue.get(1,id)["status"],"pending")
        self.roles.assign(1,1,8,"member")
        self.assertEqual(review.handle("dismiss",self.message(f"/dismiss {id} falso positivo",actor=8)).outcome,"refused")
        self.assertEqual(self.store.history(1,9)[0],0)
    def test_application_registers_review_and_administration_without_network(self):
        cfg=Configuracao("123:fake",Path("x"),(1,2),"@TesteBot")
        bot=Mock();bot.message_handler.side_effect=lambda **kwargs:lambda fn:fn
        app=create_app(configuracao=cfg,client=bot,home=Path(self.folder.name)/"application")
        commands={command for call in bot.message_handler.call_args_list for command in call.kwargs.get("commands",[])}
        self.assertTrue({"review","detections","dismiss","role","rule_set","rules_import","unwarn","hug","ban"}<=commands)
        self.assertIsInstance(app.kanna_moderation.governance,Governance)
        self.assertIs(app.kanna_review.moderation,app.kanna_moderation)
        bot.get_chat_member.assert_not_called();bot.infinity_polling.assert_not_called()

    def test_partial_kick_persists_failure_without_retry(self):
        self.bot.unban_chat_member.side_effect=RuntimeError("private response")
        message=self.message("/kick motivo")
        result=self.service.handle("kick",message)
        self.assertEqual(result.outcome,"failed")
        self.assertIn("continua banido",result.message)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT status FROM sanctions WHERE action='kick'").fetchone()[0],"partial")
        other=Moderation(self.bot,self.config,Governance(self.path),self.audit,roles=self.roles)
        self.assertEqual(other.handle("kick",message).outcome,"refused")
        self.bot.ban_chat_member.assert_called_once()
        self.bot.unban_chat_member.assert_called_once()

    def test_refused_role_and_catalog_errors_have_correct_accents(self):
        result=self.service.handle("warn",self.message(actor=9))
        self.assertEqual(result.message,"Seu cargo interno n\u00e3o permite esta a\u00e7\u00e3o.")
        data=dict(code="invalid",name="Regra",description="Regra",level="N2",weight=2,active=True,actions=["warn"])
        result=self.admin.handle("rule_set",self.message("/rule_set "+json.dumps(data),actor=1))
        self.assertEqual(result.message,"C\u00f3digo deve seguir R01 at\u00e9 R9999.")
