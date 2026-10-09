import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import Mock
from kannabot._config.configuracao import Configuracao
from kannabot.handlers.emotes import register
from kannabot.permissions import Permissions, PermissionDenied

COMMANDS = "punch slap kiss shy hug cuddle pat push stare highfive poke bite lick bonk tickle wave cry".split()

class EmoteAccessTests(unittest.TestCase):
    def setup_handlers(self, folder):
        bot = Mock()
        bot.get_chat_member.return_value = N(status="member")
        bot.send_animation.return_value = N(message_id=10)
        handlers = {}
        def decorator(**kwargs):
            def save(handler):
                handlers[kwargs["commands"][0]] = handler
                return handler
            return save
        bot.message_handler.side_effect = decorator
        cfg = Configuracao("123:fake", Path(folder)/"groups.json", (-1001,), "@TesteBot")
        register(bot, cfg, Path(folder)/"var")
        message = N(chat=N(id=-1001), message_id=1, text="/wave @target", sender_chat=None,
                    from_user=N(id=7, username="member", is_bot=False), reply_to_message=N(from_user=N(id=8, username="target", is_bot=False)))
        return bot, handlers, message

    def test_member_executes_all_registered_emotes(self):
        with tempfile.TemporaryDirectory() as folder:
            bot, handlers, message = self.setup_handlers(folder)
            for command in COMMANDS:
                with self.subTest(command=command):
                    bot.send_animation.reset_mock()
                    message.text = f"/{command} @target"
                    handlers[command](message)
                    bot.send_animation.assert_called_once()
            bot.delete_message.assert_not_called()
            with self.assertRaises(PermissionDenied):
                Permissions(bot, [-1001]).actor(message)

    def test_group_not_authorized_denies_emote(self):
        with tempfile.TemporaryDirectory() as folder:
            bot, handlers, message = self.setup_handlers(folder)
            message.chat.id = -1002
            handlers["wave"](message)
            bot.send_animation.assert_not_called()
            bot.get_chat_member.assert_not_called()

    def test_unidentified_author_denies_emote(self):
        with tempfile.TemporaryDirectory() as folder:
            bot, handlers, message = self.setup_handlers(folder)
            message.sender_chat = N(id=-1001)
            handlers["wave"](message)
            bot.send_animation.assert_not_called()
            bot.get_chat_member.assert_not_called()

    def test_membership_lookup_failure_denies_emote(self):
        with tempfile.TemporaryDirectory() as folder:
            bot, handlers, message = self.setup_handlers(folder)
            bot.get_chat_member.side_effect = RuntimeError("private response")
            handlers["wave"](message)
            bot.send_animation.assert_not_called()
