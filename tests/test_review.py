import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot.review import Review
from kannabot.review_store import ReviewStore
from kannabot.antispam import Detection
from kannabot.moderation import Result
from kannabot.permissions import PermissionDenied

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/"database.sqlite3"
        self.store=ReviewStore(self.path);self.service=Mock();self.service.roles=None
        self.service.permissions.actor.return_value=7
        self.service.governance.rule.return_value=dict(active=True)
        self.service.handle.return_value=Result("done","OK")
        self.audit=Mock();self.audit.clean.side_effect=lambda text:text
        self.review=Review(self.service,self.store,self.audit)
    def message(self,text,chat=1):return N(chat=N(id=chat),message_id=100,text=text,from_user=N(id=7,is_bot=False),sender_chat=None)
    def detect(self):self.review.observe([Detection("flood",1,8,10),Detection("repeat",1,8,10)])
    def test_detection_persists_aggregates_and_never_sanctions(self):
        self.detect();self.detect()
        rows=ReviewStore(self.path).pending(1)
        self.assertEqual(len(rows),1);self.assertIn("flood",rows[0][3]);self.assertIn("repeat",rows[0][3])
        self.service.handle.assert_not_called();self.assertEqual(self.audit.record.call_count,1)
    def test_explicit_review_targets_persisted_message_and_is_once(self):
        self.detect();id=self.store.pending(1)[0][0]
        msg=self.message(f"/review {id} warn R10 motivo")
        self.assertEqual(self.review.handle("review",msg).outcome,"done")
        command,synthetic=self.service.handle.call_args.args
        self.assertEqual(command,"warn");self.assertEqual(synthetic.reply_to_message.message_id,10)
        self.assertEqual(synthetic.reply_to_message.from_user.id,8)
        self.assertEqual(self.review.handle("review",msg).outcome,"refused")
        self.service.handle.assert_called_once()
    def test_role_change_or_wrong_group_denies(self):
        self.detect();id=self.store.pending(1)[0][0]
        self.assertEqual(self.review.handle("review",self.message(f"/review {id} warn R10",chat=2)).outcome,"refused")
        self.service.permissions.actor.side_effect=PermissionDenied("revoked")
        self.assertEqual(self.review.handle("review",self.message(f"/review {id} warn R10")).outcome,"refused")
        self.service.handle.assert_not_called()
    def test_dismiss_no_effect_and_unavailable_catalog_refuses(self):
        self.detect();id=self.store.pending(1)[0][0]
        self.service.governance=None
        self.assertEqual(self.review.handle("review",self.message(f"/review {id} warn R10")).outcome,"refused")
        self.assertEqual(self.review.handle("dismiss",self.message(f"/dismiss {id} falso positivo")).outcome,"done")
        self.service.handle.assert_not_called()
    def test_failure_is_recorded_without_automatic_retry(self):
        self.detect();id=self.store.pending(1)[0][0]
        self.service.handle.return_value=Result("failed","API indisponível")
        msg=self.message(f"/review {id} ban R16")
        self.assertEqual(self.review.handle("review",msg).outcome,"failed")
        self.assertEqual(self.store.get(1,id)["status"],"resolved")
        self.assertEqual(self.review.handle("review",msg).outcome,"refused")
        self.service.handle.assert_called_once()
    def test_persistent_claim_is_atomic(self):
        self.detect();id=self.store.pending(1)[0][0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims=list(pool.map(lambda actor:self.store.reserve(1,id,actor),(7,9)))
        self.assertEqual(sum(claims),1)
