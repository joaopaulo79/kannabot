import json
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import Mock
import test_governance as fixtures


class RuleRefusalTests(unittest.TestCase):
    setUp = fixtures.GovernanceTests.setUp
    message = fixtures.GovernanceTests.message
    import_rules = fixtures.GovernanceTests.import_rules

    def last_audit(self):
        return json.loads(self.audit.path.read_text(encoding="utf-8").splitlines()[-1])

    def assert_no_effects(self):
        self.assertEqual(self.store.history(1, 9)[0], 0)
        self.bot.delete_message.assert_not_called()
        self.bot.ban_chat_member.assert_not_called()
        self.bot.restrict_chat_member.assert_not_called()
        self.service.evidence.capture.assert_not_called()
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM sanctions").fetchone()[0], 0)

    def test_n1_refusal_explains_pending_definition_and_has_no_effects(self):
        self.import_rules()
        self.service.evidence = Mock()
        for command in ("warn", "delwarn"):
            with self.subTest(command=command):
                result = self.service.handle(command, self.message(f"/{command} R01 teste"))
                self.assertEqual(result.outcome, "refused")
                for text in ("R01", "Assunto do grupo", "reincidência", "critérios", "peso", "/catalog R01", "Nenhuma"):
                    self.assertIn(text, result.message)
                if command == "delwarn":
                    self.assertIn("nenhuma mensagem foi apagada", result.message)
                self.assertNotIn("error", self.last_audit())
                self.assert_no_effects()

    def test_missing_and_revoked_rules_have_distinct_refusals(self):
        self.import_rules()
        self.service.evidence = Mock()
        for command in ("warn", "delwarn"):
            for code, expected in (("R999", "não foi encontrada"), ("R04", "foi revogada")):
                with self.subTest(command=command, code=code):
                    result = self.service.handle(command, self.message(f"/{command} {code} teste"))
                    self.assertIn(expected, result.message)
                    self.assertEqual(result.outcome, "refused")
                    self.assertNotIn("error", self.last_audit())
                    self.assert_no_effects()

    def test_warning_allowed_but_without_weight_explains_configuration(self):
        self.import_rules()
        rule = self.store.rule(1, "R10")
        rule.pop("version"); rule["weight"] = None
        self.store.put_rule(1, rule, 1)
        for command in ("warn", "delwarn"):
            result = self.service.handle(command, self.message(f"/{command} R10 teste"))
            self.assertEqual(result.outcome, "refused")
            self.assertIn("prevê advertência", result.message)
            self.assertIn("peso ainda não foi definido", result.message)
            self.assertNotIn("error", self.last_audit())
        self.assertEqual(self.store.history(1, 9)[0], 0)

    def test_other_unsupported_action_does_not_invent_warning_policy(self):
        self.import_rules()
        result = self.service.handle("ban", self.message("/ban R01 teste"))
        self.assertEqual(result.outcome, "refused")
        self.assertIn("não permite banimento", result.message)
        self.assertNotIn("reincidência", result.message)
        self.bot.ban_chat_member.assert_not_called()

    def test_rule_name_is_escaped_and_long_refusal_keeps_effect_statement(self):
        self.import_rules()
        rule = self.store.rule(1, "R01")
        rule.pop("version"); rule["name"] = "<b>Assunto & grupo</b>"
        self.store.put_rule(1, rule, 1)
        for command in ("warn", "delwarn"):
            result = self.service.handle(command, self.message(f"/{command} R01 teste"))
            self.assertIn("&lt;b&gt;Assunto &amp; grupo&lt;/b&gt;", result.message)
            self.assertNotIn("<b>", result.message)
            self.assertIn("Nenhuma", result.message)

    def test_configured_n1_warning_still_works(self):
        self.import_rules()
        rule = self.store.rule(1, "R01")
        rule.pop("version"); rule["actions"].append("warn"); rule["weight"] = 1
        self.store.put_rule(1, rule, 1)
        result = self.service.handle("warn", self.message("/warn R01 motivo"))
        self.assertEqual(result.outcome, "done")
        self.assertEqual(self.store.points(1, 9), 1)

    def test_reason_policy_is_unchanged(self):
        self.import_rules()
        self.assertEqual(self.service.handle("warn", self.message("/warn")).outcome, "done")
        self.assertEqual(self.service.handle("warn", self.message("/warn R10", event=22)).outcome, "done")
        self.assertEqual(self.service.handle("delwarn", self.message("/delwarn R10", event=21)).outcome, "refused")
        self.bot.delete_message.assert_not_called()

    def test_failure_after_warning_keeps_partial_result_and_technical_error(self):
        self.import_rules()
        from telebot.apihelper import ApiTelegramException
        self.bot.delete_message.side_effect = ApiTelegramException("deleteMessage", None, {"error_code": 400, "description": "denied"})
        result = self.service.handle("delwarn", self.message("/delwarn R10 teste"))
        self.assertEqual(result.outcome, "partial")
        self.assertIn("Advertência #", result.message)
        self.assertNotIn("Nenhuma", result.message)
        self.assertEqual(self.store.history(1, 9)[0], 1)
        self.assertEqual(self.last_audit()["error"], "ApiTelegramException")
