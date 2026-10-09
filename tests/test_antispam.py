import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot.antispam import Antispam
from kannabot.policy import Policy
from kannabot._config.configuracao import Configuracao,ErroConfiguracao

class AntispamTests(unittest.TestCase):
    def setUp(self):
        self.now=[0];self.bot=Mock();self.audit=Mock()
        self.bot.get_chat_member.return_value=N(status="member")
        self.options=dict(flood_limit=2,flood_window=10,repeat_limit=2,repeat_window=10)
        policy=Policy({"groups":{"1":{"spam":self.options},"2":{"spam":dict(self.options)}}})
        self.service=Antispam(self.bot,Configuracao("123:fake",Path("x"),(1,2),"@TesteBot"),policy,self.audit,clock=lambda:self.now[0],capacity=2)
    def message(self,id,user=7,chat=1,text="hello"):
        return N(chat=N(id=chat),message_id=id,from_user=N(id=user,is_bot=False),sender_chat=None,text=text,caption=None)
    def test_boundaries_normalization_duplicate_and_expiry(self):
        self.assertEqual(self.service.handle(self.message(1,text=" Hello  ")),[])
        self.assertEqual(self.service.handle(self.message(2,text="HELLO")),[])
        self.assertEqual({d.rule for d in self.service.handle(self.message(3))},{"flood","repeat"})
        self.assertEqual(self.service.handle(self.message(3)),[])
        self.now[0]=10
        self.assertEqual(self.service.handle(self.message(4)),[])
        self.assertEqual(len(self.service.users[(1,7)][0]),1)
    def test_isolation_and_bounded_state(self):
        self.service.handle(self.message(1));self.service.handle(self.message(2,user=8));self.service.handle(self.message(3,chat=2))
        self.assertEqual(len(self.service.users),2)
        self.assertEqual(self.service.handle(self.message(4,user=8)),[])
    def test_admin_service_and_lookup_failure_ignored(self):
        self.bot.get_chat_member.return_value=N(status="administrator")
        self.assertEqual(self.service.handle(self.message(1)),[])
        self.bot.get_chat_member.return_value=N(status="member")
        msg=self.message(2);msg.new_chat_members=[N(id=9)]
        self.assertEqual(self.service.handle(msg),[])
        self.bot.get_chat_member.side_effect=RuntimeError("unavailable")
        self.assertEqual(self.service.handle(self.message(3)),[])
        self.assertEqual(len(self.service.users),0)
    def test_observation_logs_limited_and_never_punishes(self):
        for id in range(1,8):self.service.handle(self.message(id))
        self.assertEqual(self.audit.record.call_count,2)
        self.bot.delete_message.assert_not_called();self.bot.restrict_chat_member.assert_not_called();self.bot.ban_chat_member.assert_not_called()
    def test_invalid_policy_rejected(self):
        for value in (0,True,101):
            with self.assertRaises(ErroConfiguracao):Policy({"groups":{"1":{"spam":dict(self.options,flood_limit=value)}}})
