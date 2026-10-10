import json
import unittest
import test_governance as fixtures

class RuleCaseTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules

    def test_lowercase_warn_uses_catalog_weight_and_keeps_reason(self):
        self.import_rules()
        result=self.service.handle("warn",self.message("/warn r10 Vacilou"))
        self.assertEqual(result.outcome,"done")
        entry=self.store.detailed_entries(1,9)[0]
        self.assertEqual(entry["weight"],3);self.assertEqual(entry["rule_code"],"R10")
        self.assertIn("Motivo: Vacilou",result.message)
        event=json.loads(self.audit.path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(event["rule_code"],"R10")

    def test_delwarn_lowercase_and_unknown_or_revoked_do_not_fall_back(self):
        self.import_rules()
        for command in ("warn","delwarn"):
            for code in ("r999","r04","r02"):
                self.assertEqual(self.service.handle(command,self.message(f"/{command} {code} motivo")).outcome,"refused")
        self.bot.delete_message.assert_not_called();self.assertEqual(self.store.history(1,9)[0],0)
        self.assertEqual(self.service.handle("delwarn",self.message("/delwarn r10 motivo")).outcome,"done")
        self.assertEqual(self.store.detailed_entries(1,9)[0]["weight"],3)
        self.bot.delete_message.assert_called_once()

    def test_catalog_edit_and_disable_normalize_code_only(self):
        self.import_rules()
        result=self.admin.handle("catalog",self.message("/catalog r10"))
        self.assertEqual(result.outcome,"done");self.assertIn("R10",result.message)
        rule=self.store.rule(1,"R10");rule.pop("version")
        rule["code"]="r10";rule["description"]="Conteúdo Original"
        result=self.admin.handle("rule_set",self.message("/rule_set "+json.dumps(rule),actor=1))
        self.assertEqual(result.outcome,"done")
        self.assertEqual(self.store.rule(1,"R10")["description"],"Conteúdo Original")
        self.assertEqual(self.admin.handle("rule_disable",self.message("/rule_disable r10",actor=1)).outcome,"done")
        self.assertFalse(self.store.rule(1,"R10")["active"])

    def test_review_lowercase_resolves_same_rule(self):
        self.import_rules()
        review,queue,id=fixtures.GovernanceTests.make_review(self)
        result=review.handle("review",self.message(f"/review {id} warn r10 Decisão"))
        self.assertEqual(result.outcome,"done")
        self.assertEqual(self.store.points(1,9),3)

    def test_short_code_is_not_interpreted_as_manual_reason(self):
        self.import_rules()
        for command in ("warn","delwarn"):
            for code in ("R1","r1"):
                result=self.service.handle(command,self.message(f"/{command} {code} teste"))
                self.assertEqual(result.outcome,"refused")
                self.assertIn("R01",result.message)
        self.assertEqual(self.store.history(1,9)[0],0)
        self.assertEqual(self.admin.handle("catalog",self.message("/catalog r1")).outcome,"done")
        self.bot.delete_message.assert_not_called()
