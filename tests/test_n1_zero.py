import unittest
import test_governance as fixtures

class N1ZeroTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules

    def test_n1_without_additional_reason_counts_but_has_no_points(self):
        self.import_rules()
        for event,code in enumerate(("R01","R02","R03"),30):
            result=self.service.handle("warn",self.message(f"/warn {code}",event=event))
            self.assertEqual(result.outcome,"done")
            self.assertIn("Peso: 0 pontos",result.message)
            self.assertEqual(self.store.rule(1,code)["weight"],0)
        self.assertEqual(self.store.history(1,9)[0],3);self.assertEqual(self.store.points(1,9),0)
        self.assertTrue(all(e["weight"]==0 for e in self.store.detailed_entries(1,9)))
        self.bot.ban_chat_member.assert_not_called()

    def test_explicit_upgrade_is_versioned_idempotent_and_preserves_history(self):
        self.import_rules()
        rule=self.store.rule(1,"R02");rule.pop("version")
        rule["weight"]=None;rule["actions"].remove("warn");rule["description"]="Redação personalizada"
        self.store.put_rule(1,rule,1)
        version=self.store.rule(1,"R02")["version"]
        self.store.add(1,9,7,"Anterior","old","legacy",rule=self.store.rule(1,"R02"))
        self.import_rules()
        self.assertIsNone(self.store.rule(1,"R02")["weight"])
        self.assertEqual(self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=7)).outcome,"refused")
        self.assertIsNone(self.store.rule(1,"R02")["weight"])
        self.assertEqual(self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=1)).outcome,"done")
        current=self.store.rule(1,"R02")
        self.assertEqual(current["version"],version+1);self.assertEqual(current["weight"],0)
        self.assertEqual(current["description"],"Redação personalizada")
        self.assertIsNone(self.store.detailed_entries(1,9)[0]["weight"])
        self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=1))
        self.assertEqual(self.store.rule(1,"R02")["version"],version+1)

    def test_custom_weight_is_not_overwritten(self):
        self.import_rules();rule=self.store.rule(1,"R01");rule.pop("version");rule["weight"]=1
        self.store.put_rule(1,rule,1)
        self.admin.handle("rules_import",self.message("/rules_import atualizar",actor=1))
        self.assertEqual(self.store.rule(1,"R01")["weight"],1)

    def test_delwarn_n1_uses_zero_weight(self):
        self.import_rules()
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn r02 teste")).outcome,"done")
        self.assertEqual(self.store.detailed_entries(1,9)[0]["weight"],0)
        self.assertEqual(self.store.history(1,9)[0],1);self.assertEqual(self.store.points(1,9),0)
        self.bot.delete_message.assert_called_once()
