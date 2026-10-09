import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot.links import url_host, extract_urls, violates
from kannabot.policy import Policy
from kannabot.antispam import Antispam
from kannabot._config.configuracao import Configuracao

class LinkTests(unittest.TestCase):
    def options(self,subdomains=False):return dict(allow=["example.com"],deny=["bad.example.com"],include_subdomains=subdomains)
    def message(self,text="",caption=None,entities=None,caption_entities=None):
        return N(chat=N(id=1),message_id=10,from_user=N(id=7,is_bot=False),sender_chat=None,text=text,caption=caption,entities=entities,caption_entities=caption_entities)
    def test_exact_hosts_lookalikes_and_credentials(self):
        for url in ("https://example.com.evil.org","https://example.com@evil.org","https://bad.example.com"):
            self.assertTrue(violates(self.message(url),self.options(True)))
        self.assertFalse(violates(self.message("https://EXAMPLE.COM./p"),self.options()))
        self.assertFalse(violates(self.message("nenhum link"),self.options()))
    def test_subdomains_idna_and_malformed(self):
        self.assertTrue(violates(self.message("https://ok.example.com"),self.options()))
        self.assertFalse(violates(self.message("https://ok.example.com"),self.options(True)))
        self.assertEqual(url_host("https://bücher.de"),"xn--bcher-kva.de")
        for url in ("https://[invalid", "https://example.com:99999", "https://bad%20host"):
            self.assertTrue(violates(self.message(url),self.options()))
    def test_hidden_links_and_utf16_caption_entities(self):
        msg=self.message("clique",entities=[N(type="text_link",url="https://evil.org")])
        self.assertTrue(violates(msg,self.options()))
        msg=self.message(caption="😀 example.com",caption_entities=[N(type="url",offset=3,length=11)])
        self.assertEqual(extract_urls(msg),["example.com"])
        self.assertFalse(violates(msg,self.options()))
        msg.caption_entities=[N(type="url",offset=1,length=2)]
        self.assertEqual(extract_urls(msg),[])
    def test_multiple_links_and_link_only_policy_protects_admin(self):
        options=self.options(True)
        self.assertTrue(violates(self.message("https://example.com https://evil.org"),options))
        bot=Mock();bot.get_chat_member.return_value=N(status="member");audit=Mock()
        policy=Policy({"groups":{"1":{"links":options}}})
        service=Antispam(bot,Configuracao("123:fake",Path("x"),(1,),"@TesteBot"),policy,audit)
        self.assertEqual([d.rule for d in service.handle(self.message("https://evil.org"))],["links"])
        bot.delete_message.assert_not_called();bot.ban_chat_member.assert_not_called()
        bot.get_chat_member.return_value=N(status="administrator")
        msg=self.message("https://evil.org");msg.message_id=11
        self.assertEqual(service.handle(msg),[])
