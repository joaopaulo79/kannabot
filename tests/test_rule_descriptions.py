import unittest
from unittest.mock import Mock
import test_governance as fixtures
from kannabot.governance import validate_rule
from kannabot.presentation import send_reply

class RuleDescriptionTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules
    def test_full_source_and_summary(self):
        self.import_rules();rule=self.store.rule(1,"R10")
        self.assertIn("figurinhas",rule["description"]);self.assertNotIn("Referência ao livro",rule["description"])
        self.assertIn("figurinhas",rule["summary"])
        self.assertIn("tag de Spoiler",self.store.rule(1,"R03")["description"])
        self.assertFalse(self.store.rule(1,"R04")["active"])
    def test_explicit_generic_update_is_idempotent_and_preserves_history(self):
        self.import_rules()
        rule=self.store.rule(1,"R10");rule.pop("version");rule.pop("summary")
        rule["description"]=f"Referência ao livro de regras fornecido pelo Dono: {rule['name']}. Aplicação depende de avaliação humana; exceções exigem decisão explícita."
        self.store.put_rule(1,rule,1)
        self.service.handle("warn",self.message("/warn R10 teste"))
        self.admin.handle("rules_import",self.message("/rules_import",actor=1))
        self.assertEqual(self.store.rule(1,"R10")["version"],2)
        self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=1))
        self.assertEqual(self.store.rule(1,"R10")["version"],3)
        self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=1))
        self.assertEqual(self.store.rule(1,"R10")["version"],3)
        self.assertIn("Referência ao livro",self.store.detailed_entries(1,9)[0]["snapshot"])
    def test_custom_description_never_overwritten(self):
        self.import_rules();rule=self.store.rule(1,"R10");rule.pop("version");rule["description"]="Texto personalizado"
        self.store.put_rule(1,rule,1)
        self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=1))
        self.assertEqual(self.store.rule(1,"R10")["description"],"Texto personalizado")
    def test_long_description_and_paging(self):
        self.import_rules();rule=self.store.rule(1,"R10");rule.pop("version");rule["description"]="x"*2000
        validate_rule(rule)
        bot=Mock();send_reply(bot,1,"a"*2000+"\n"+"b"*2000)
        self.assertEqual(bot.send_message.call_count,2)
        self.assertTrue(all(len(c.args[1])<=3500 for c in bot.send_message.call_args_list))
