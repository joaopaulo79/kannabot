import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from telebot.apihelper import ApiTelegramException
from requests.exceptions import Timeout
from kannabot.handlers.emotes import Emotes
from kannabot._config.configuracao import Configuracao
from kannabot.interacoes import Interactions

class CallbackRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.bot = Mock()
        self.bot.get_chat_member.return_value = N(status="member")
        self.bot.send_animation.return_value = N(message_id=10)
        self.service = Emotes(self.bot, Configuracao("123:fake", Path("unused"), (1,), "@TesteBot"))
    def message(self, argument="", reply_id=8, reply_username="Alice"):
        reply = N(from_user=N(id=reply_id, username=reply_username)) if reply_id is not None else None
        return N(chat=N(id=1), message_id=1, text="/hug" + argument, sender_chat=None,
                 from_user=N(id=7, username="author", is_bot=False), reply_to_message=reply)
    def call(self, user_id=8):
        return N(id="callback", data="Aceitar_Abraço", from_user=N(id=user_id, username="Alice"),
                 message=N(chat=N(id=1), message_id=10))
    def test_conflicting_argument_and_reply_rejected(self):
        self.service.command("hug", self.message(" @Alice", reply_id=9, reply_username="Bruno"))
        self.bot.send_animation.assert_not_called()
        self.assertIn("diferentes", self.bot.send_message.call_args.args[1])
    def test_reply_to_author_does_not_select_self_for_other_argument(self):
        self.service.command("hug", self.message(" @Alice", reply_id=7, reply_username="author"))
        self.bot.send_animation.assert_not_called()
    def test_reply_and_argument_same_identity(self):
        self.service.command("hug", self.message(" @Alice"))
        self.assertIn("Alice", self.bot.send_animation.call_args.kwargs["caption"])
        self.service.callback(self.call(9))
        self.assertEqual(self.bot.send_animation.call_count, 1)
        self.service.callback(self.call())
        self.assertEqual(self.bot.send_animation.call_count, 2)
        self.service.callback(self.call())
        self.assertEqual(self.bot.send_animation.call_count, 2)
    def test_unknown_username_requests_reply_without_publishing_buttons(self):
        self.service.command("hug", self.message(" @Alice", reply_id=None))
        self.bot.send_animation.assert_not_called()
        self.assertIn("Responda", self.bot.send_message.call_args.args[1])
        self.assertEqual(len(self.service.interactions.items), 0)
    def test_confirmed_rejection_releases_reservation(self):
        self.service.command("hug", self.message())
        error = ApiTelegramException("sendAnimation", None, {"error_code":400, "description":"rejected"})
        self.bot.send_animation.side_effect = [error, N(message_id=11)]
        self.service.callback(self.call())
        self.assertIn("tentar novamente", self.bot.answer_callback_query.call_args.kwargs["text"])
        self.service.callback(self.call())
        self.assertEqual(self.bot.send_animation.call_count, 3)
        self.service.callback(self.call())
        self.assertEqual(self.bot.send_animation.call_count, 3)
    def test_timeout_keeps_reservation_to_avoid_duplicate_delivery(self):
        self.service.command("hug", self.message())
        self.bot.send_animation.side_effect = Timeout("unknown delivery")
        self.service.callback(self.call())
        self.assertIn("não confirmado", self.bot.answer_callback_query.call_args.kwargs["text"])
        self.service.callback(self.call())
        self.assertEqual(self.bot.send_animation.call_count, 2)
    def test_concurrent_reservation_allows_one_execution(self):
        store = Interactions()
        value = dict(owner=7, target=8, buttons={"yes"}, roles={"yes":"target"})
        store.put((1, 10), value)
        barrier = Barrier(2)
        def claim():
            barrier.wait(timeout=5)
            return store.claim((1, 10), 8, "yes")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        store.finish((1, 10), 8, value, success=False)
        self.assertIs(store.claim((1, 10), 8, "yes"), value)
        store.finish((1, 10), 8, value, success=True)
        self.assertIsNone(store.claim((1, 10), 8, "yes"))
