import unittest
from unittest.mock import Mock
import test_governance as fixtures
from kannabot.administration import register
from kannabot.help import Help
from kannabot.presentation import ACTION_NAMES

class RulesCommandTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules

    def test_list_and_detail_aliases_and_normalization(self):
        self.import_rules()
        before=self.store.catalog(1)
        old_list=self.admin.handle("catalog",self.message("/catalog"))
        self.assertEqual(self.admin.handle("rules",self.message("/rules")),old_list)
        detail=self.admin.handle("catalog",self.message("/catalog R01"))
        for command,argument in (("rule","R01"),("rule","r1"),("rules","R01"),("catalog","r1")):
            self.assertEqual(self.admin.handle(command,self.message(f"/{command} {argument}")),detail)
        self.assertIn("/rule R10",old_list.message)
        self.assertEqual(self.store.catalog(1),before);self.assertEqual(self.store.history(1,9)[0],0)
        self.bot.delete_message.assert_not_called();self.bot.ban_chat_member.assert_not_called()

    def test_rule_without_code_has_clear_guidance_and_unknown_code_is_refused(self):
        self.import_rules()
        result=self.admin.handle("rule",self.message("/rule"))
        self.assertEqual(result.outcome,"refused")
        self.assertIn("/rule R01",result.message);self.assertIn("/rules",result.message)
        self.assertEqual(self.admin.handle("rule",self.message("/rule R999")).outcome,"refused")

    def test_same_capability_for_new_commands_and_aliases(self):
        self.import_rules()
        for actor in (1,7,8):
            for command in ("rules","rule","catalog"):
                self.assertEqual(self.admin.handle(command,self.message(f"/{command} R01",actor=actor)).outcome,"done")
        for command in ("rules","rule","catalog"):
            self.assertEqual(self.admin.handle(command,self.message(f"/{command} R01",actor=9)).outcome,"refused")
        self.assertEqual(self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=7)).outcome,"refused")

    def test_registered_handlers_respond_and_audit_actual_command(self):
        self.import_rules();handlers={};bot=Mock()
        def decorator(**kwargs):
            def save(handler):
                for command in kwargs["commands"]:handlers[command]=handler
                return handler
            return save
        bot.message_handler.side_effect=decorator
        register(bot,self.admin)
        for command in ("rules","rule","catalog"):
            handlers[command](self.message(f"/{command}@TesteBot r1"))
        self.assertEqual(bot.send_message.call_count,3)
        self.assertEqual(ACTION_NAMES["rules"],"Consulta de regras")
        self.assertEqual(ACTION_NAMES["rule"],"Consulta de regra")
        import json
        actions=[json.loads(line)["action"] for line in self.audit.path.read_text(encoding="utf-8").splitlines()[-3:]]
        self.assertEqual(actions,["rules","rule","catalog"])

    def test_help_promotes_new_commands(self):
        helper=Help(self.service)
        self.assertIn("/rules",helper.render("mod","rules"))
        self.assertIn("/rule R01",helper.render("mod","rule"))
        self.assertIn("/catalog",helper.render("mod","rules"))
