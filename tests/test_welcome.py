import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot.welcome import Welcome
from kannabot.policy import Policy
from kannabot._config.configuracao import Configuracao, ErroConfiguracao

class WelcomeTests(unittest.TestCase):
    def setUp(self):
        self.bot=Mock();self.audit=Mock()
        self.policy=Policy({"groups":{"1":{"welcome":{"text":"Oi {user} <x>","rules":"regra & respeito"}}}})
        self.service=Welcome(self.bot,Configuracao("123:fake",Path("x"),(1,),"@TesteBot"),self.policy,self.audit)
        self.msg=N(chat=N(id=1),message_id=10,new_chat_members=[N(id=7,username="<user>"),N(id=8,username=None)])
    def test_multiple_members_html_and_duplicate(self):
        self.service.handle(self.msg);self.service.handle(self.msg)
        self.assertEqual(self.bot.send_message.call_count,2)
        texts=[call.args[1] for call in self.bot.send_message.call_args_list]
        self.assertIn("&lt;user&gt;",texts[0]);self.assertIn("Oi 8",texts[1]);self.assertIn("Regras:",texts[0])
    def test_unauthorized_missing_configuration_and_send_failure(self):
        self.msg.chat.id=2;self.service.handle(self.msg);self.bot.send_message.assert_not_called()
        self.msg.chat.id=1;self.bot.send_message.side_effect=RuntimeError("secret")
        self.service.handle(self.msg)
        self.assertEqual(self.audit.record.call_args.args[5],"failed")
        Welcome(self.bot,Configuracao("123:fake",Path("x"),(1,),"@TesteBot"),Policy(),self.audit).handle(self.msg)
    def test_invalid_configuration_rejected(self):
        for data in ({"groups":{"x":{}}},{"groups":{"1":{"welcome":{"text":"x"}}}},{"groups":[]}):
            with self.assertRaises(ErroConfiguracao):Policy(data)
