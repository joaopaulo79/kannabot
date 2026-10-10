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


    def test_catalog_explains_duration_range_and_undefined_conditions(self):
        self.import_rules()
        result=self.admin.handle("catalog",self.message("/catalog R10"))
        self.assertIn("1 dia a 1 semana",result.message)
        result=self.admin.handle("catalog",self.message("/catalog R01"))
        self.assertIn("reincidência",result.message)
        self.assertIn("não definido",result.message)

    def test_catalog_index_groups_active_and_revoked_without_internal_values(self):
        self.import_rules();result=self.admin.handle("catalog",self.message("/catalog"))
        self.assertEqual(result.outcome,"done")
        self.assertIn("18 ativas · 1 revogada",result.message)
        self.assertNotIn("None",result.message);self.assertNotIn(" v1",result.message)
        active,revoked=result.message.split("Regras revogadas")
        self.assertNotIn("R04",active);self.assertIn("R04",revoked)
        for level in (1,2,3,4):self.assertIn(f"Nível {level}",active)
        self.assertEqual(self.store.history(1,9)[0],0);self.bot.delete_message.assert_not_called()
    def test_catalog_index_handles_more_than_twenty_and_escapes_names(self):
        self.import_rules();base=self.store.rule(1,"R10");base.pop("version")
        for number in range(20,45):
            rule=dict(base,code=f"R{number}",name=f"Regra <teste> {number}")
            self.store.put_rule(1,rule,1)
        result=self.admin.handle("catalog",self.message("/catalog"))
        self.assertIn("R44 — Regra &lt;teste&gt; 44",result.message)
        self.assertNotIn("<teste>",result.message)
        self.assertIn("43 ativas · 1 revogada",result.message)

    def test_rule_detail_explains_actions_without_internal_field_line(self):
        self.import_rules();result=self.admin.handle("catalog",self.message("/catalog R10"))
        self.assertIn("<b>Descrição</b>",result.message);self.assertIn("<b>Aplicação prevista</b>",result.message)
        self.assertIn("Advertência: +3 pontos",result.message);self.assertIn("1 dia a 1 semana",result.message)
        self.assertNotIn("· Peso:",result.message);self.assertNotIn("Ações cadastradas",result.message)
        self.assertIn("não aplica nenhuma punição",result.message)
        result=self.admin.handle("catalog",self.message("/catalog R16"))
        self.assertIn("• Banimento.",result.message);self.assertNotIn("peso não definido",result.message)
        result=self.admin.handle("catalog",self.message("/catalog R04"))
        self.assertIn("Regra revogada",result.message);self.assertIn("Não se aplica a novas ocorrências",result.message)

    def test_custom_n1_defined_weight_is_not_reported_as_undefined(self):
        self.import_rules();rule=self.store.rule(1,"R01");rule.pop("version")
        rule['weight']=1;rule['actions'].append('warn');self.store.put_rule(1,rule,1)
        result=self.admin.handle("catalog",self.message("/catalog R01"))
        self.assertIn("Advertência: +1 ponto",result.message)
        self.assertNotIn("peso não definido",result.message)
