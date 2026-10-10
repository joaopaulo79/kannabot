import json
import unittest
import test_governance as fixtures

class RuleDescriptionUpgradeTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules

    def legacy(self,code="R01",**changes):
        rule=self.store.rule(1,code);rule.pop("version");rule.pop("summary",None)
        rule["description"]=f"Referência ao livro de regras fornecido pelo Dono: {rule['name']}. Aplicação depende de avaliação humana; exceções exigem decisão explícita."
        rule.update(changes);self.store.put_rule(1,rule,1)
        return rule

    def update(self,actor=1):
        return self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=actor))

    def test_zero_weight_n1_gets_real_summary_and_preserves_old_warning(self):
        self.import_rules();self.legacy()
        self.service.handle("warn",self.message("/warn R01 antes"))
        old=self.store.detailed_entries(1,9)[0]
        self.assertEqual(self.update().outcome,"done")
        rule=self.store.rule(1,"R01")
        self.assertEqual(rule["version"],3);self.assertEqual(rule["weight"],0)
        self.assertIn("animes e mangás",rule["description"])
        self.assertEqual(old,self.store.detailed_entries(1,9)[0])
        result=self.service.handle("warn",self.message("/warn R01 depois",event=21))
        self.assertIn("Descrição: Respeite o foco em animes e mangás",result.message)
        self.assertNotIn("Referência ao livro",result.message)
        catalog=self.admin.handle("catalog",self.message("/catalog R01"))
        self.assertIn("https://t.me/febreotaku_topicoslivres/3",catalog.message)
        self.update();self.assertEqual(self.store.rule(1,"R01")["version"],3)

    def test_description_upgrade_preserves_custom_policy_and_revocation(self):
        self.import_rules();self.legacy("R10",weight=1,actions=["warn"],active=False)
        self.update();rule=self.store.rule(1,"R10")
        self.assertEqual(rule["weight"],1);self.assertEqual(rule["actions"],["warn"]);self.assertFalse(rule["active"])
        self.assertIn("figurinhas",rule["description"])

    def test_n1_policy_and_description_upgrade_use_one_version(self):
        self.import_rules();self.legacy(weight=None,actions=["delete","mute"])
        self.update();rule=self.store.rule(1,"R01")
        self.assertEqual(rule["version"],3);self.assertEqual(rule["weight"],0)
        self.assertIn("warn",rule["actions"]);self.assertNotIn("Referência ao livro",rule["description"])

    def test_only_explicit_owner_update_replaces_placeholder(self):
        self.import_rules();self.legacy()
        self.import_rules();self.assertEqual(self.store.rule(1,"R01")["version"],2)
        self.assertEqual(self.update(actor=7).outcome,"refused")
        self.assertEqual(self.store.rule(1,"R01")["version"],2)

    def test_custom_wording_and_summary_are_preserved(self):
        self.import_rules();rule=self.store.rule(1,"R01");rule.pop("version")
        rule["description"]="Texto escolhido pelo dono";rule["summary"]="Resumo próprio"
        self.store.put_rule(1,rule,1);self.update()
        current=self.store.rule(1,"R01")
        self.assertEqual(current["description"],rule["description"]);self.assertEqual(current["summary"],rule["summary"])
        self.assertEqual(current["version"],2)
