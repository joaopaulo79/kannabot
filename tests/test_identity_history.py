import sqlite3
import unittest
from types import SimpleNamespace as N
import test_governance as fixtures
from kannabot.identities import Identities
from kannabot.governance import Governance

class IdentityHistoryTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules
    def test_occurrence_preserves_username_after_change_and_restart(self):
        self.import_rules()
        index=Identities(self.bot,(1,),self.path)
        index.observe_user(1,N(id=7,username="Autor",is_bot=False))
        index.observe_user(1,N(id=9,username="Alvo",is_bot=False))
        self.service.handle("warn",self.message("/warn R10 teste"))
        index.observe_user(1,N(id=9,username="Novo",is_bot=False))
        Governance(self.path)
        with sqlite3.connect(self.path) as db:
            row=db.execute("SELECT autor_username,alvo_username,descricao_aplicada FROM historico_advertencias").fetchone()
            self.assertEqual(row[:2],("autor","alvo"));self.assertIn("Flood",row[2])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogo_regras").fetchone()[0],19)
    def test_legacy_is_not_retrofilled(self):
        self.store.add(1,9,7,"old","old","old")
        index=Identities(self.bot,(1,),self.path)
        index.observe_user(1,N(id=9,username="Hoje",is_bot=False))
        Governance(self.path)
        with sqlite3.connect(self.path) as db:
            self.assertIsNone(db.execute("SELECT alvo_username FROM historico_advertencias").fetchone()[0])
    def test_delwarn_has_identity_on_both_records(self):
        self.import_rules();index=Identities(self.bot,(1,),self.path)
        index.observe_user(1,N(id=9,username="Alvo",is_bot=False))
        self.service.handle("delwarn",self.message("/delwarn R10 teste"))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT target_username FROM warnings").fetchone()[0],"alvo")
            self.assertEqual(db.execute("SELECT alvo_username FROM acoes_moderacao").fetchone()[0],"alvo")
