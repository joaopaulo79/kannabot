import json
import unittest
import test_governance as fixtures
from kannabot.presentation import mention
class PresentationTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules
    def test_warn_snapshot_description_and_cancelled_history(self):
        self.import_rules()
        m=self.message("/warn R10 exemplo <tag>")
        m.from_user.username="autor";m.reply_to_message.from_user.username="alvo"
        result=self.service.handle("warn",m)
        self.assertIn("@alvo",result.message);self.assertIn("Descrição:",result.message)
        self.assertIn("&lt;tag&gt;",result.message)
        self.admin.handle("unwarn",self.message("/unwarn 1 revisão"))
        result=self.service.handle("warnings",self.message("/warnings"))
        self.assertIn("Cancelada",result.message);self.assertIn("Pontos: 0",result.message)
    def test_refused_human_keeps_identity(self):
        self.service.handle("ban",self.message("/ban motivo",actor=8))
        event=json.loads(self.audit.path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(event["actor"],8);self.assertEqual(event["origin"],"human")
    def test_mention_escapes_html(self):
        self.assertEqual(mention(1,"<x>"),"@&lt;x&gt;")
    def test_catalog_contains_description(self):
        self.import_rules()
        self.assertIn(self.store.rule(1,"R10")["description"],self.admin.handle("catalog",self.message("/catalog R10")).message)
