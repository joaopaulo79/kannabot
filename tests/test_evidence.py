import json
import sqlite3
import unittest
from contextlib import closing
from types import SimpleNamespace as N
from unittest.mock import patch
import test_governance as fixtures
from kannabot.evidence import Evidence

class EvidenceTests(unittest.TestCase):
    setUp=fixtures.GovernanceTests.setUp
    message=fixtures.GovernanceTests.message
    import_rules=fixtures.GovernanceTests.import_rules
    def enable(self):
        self.evidence=Evidence(self.path,self.audit.clean);self.service.evidence=self.evidence
    def remove_in_database(self,chat,reference):
        with closing(sqlite3.connect(self.path)) as db,db:
            return db.execute("UPDATE evidence SET payload=NULL,username=NULL,availability='removed',removed_at='test',removed_by=7,removal_reason='revisão' WHERE chat_id=? AND id=? AND removed_at IS NULL",(chat,reference)).rowcount
    def rows(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.row_factory=sqlite3.Row
            return [dict(row) for row in db.execute('SELECT * FROM evidence')]
    def test_capture_precedes_delete_and_redacts_secret(self):
        self.enable();message=self.message('/delete teste');message.reply_to_message.text='texto 123:fake'
        def delete(chat,target):
            self.assertIn('[redacted]',self.rows()[0]['payload']);return True
        self.bot.delete_message.side_effect=delete
        self.assertEqual(self.service.handle('delete',message).outcome,'done')
        self.assertEqual(self.rows()[0]['availability'],'text_and_metadata')
    def test_capture_failure_prevents_delete_and_warn(self):
        self.enable();self.import_rules()
        with patch.object(self.evidence,'capture',side_effect=sqlite3.OperationalError('locked')):
            self.assertEqual(self.service.handle('delete',self.message('/delete teste')).outcome,'failed')
            self.assertEqual(self.service.handle('delwarn',self.message('/delwarn R10 teste')).outcome,'failed')
        self.bot.delete_message.assert_not_called();self.assertEqual(self.store.history(1,9)[0],0)
    def test_manual_removal_preserves_warn_and_does_not_recapture(self):
        self.enable();self.import_rules();message=self.message('/delwarn R10 teste');message.reply_to_message.text='evidência'
        self.assertEqual(self.service.handle('delwarn',message).outcome,'done')
        self.remove_in_database(1,1)
        self.assertIsNone(self.rows()[0]['payload']);self.assertEqual(self.store.history(1,9)[0],1)
        self.evidence.capture(1,message.reply_to_message,'new','delete')
        self.assertIsNone(self.rows()[0]['payload'])
        Evidence(self.path,self.audit.clean)
        self.assertEqual(self.rows()[0]['availability'],'removed')
    def test_database_removal_is_scoped_and_no_bot_command(self):
        self.enable();self.evidence.capture(1,self.message().reply_to_message,'test','delete')
        self.assertEqual(self.remove_in_database(2,1),0)
        self.assertIsNotNone(self.rows()[0]['payload'])
        self.assertEqual(self.remove_in_database(1,1),1)
        self.assertFalse(hasattr(self.evidence,'handle_remove'))
    def test_media_metadata_no_download_and_no_expiry(self):
        self.enable();message=self.message().reply_to_message;message.photo=[N(file_id='opaque',file_unique_id='unique',width=5)]
        self.evidence.capture(1,message,'test','delete');Evidence(self.path,self.audit.clean)
        row=self.rows()[0];self.assertEqual(row['availability'],'media_metadata_only')
        self.assertEqual(json.loads(row['payload'])['photo']['file_unique_id'],'unique')
        self.bot.get_file.assert_not_called();self.assertNotIn('expires_at',row)
