import importlib
import pkgutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from kannabot._config.configuracao import Configuracao
from kannabot.app import create_app
from kannabot.emotes.open_json import Abrir_Arquivos_Emotes

class AppTests(unittest.TestCase):
    def test_imports_inert(self):
        import kannabot
        with patch("telebot.TeleBot", side_effect=AssertionError("cliente em import")):
            for info in pkgutil.walk_packages(kannabot.__path__, "kannabot."):
                importlib.import_module(info.name)

    def test_registration_preserves_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = Configuracao("123:fake", Path(folder)/"g.json", (-1001,), "@TesteBot")
            client = MagicMock()
            create_app(cfg, client, folder)
            commands = [call.kwargs["commands"][0] for call in client.message_handler.call_args_list]
            self.assertEqual(set(commands), set("punch slap kiss shy hug cuddle pat push stare highfive poke bite lick bonk tickle wave cry".split()))
            client.infinity_polling.assert_not_called()
            self.assertFalse((Path(folder)/"var").exists())

    def test_resources_without_cwd(self):
        self.assertIn("h", Abrir_Arquivos_Emotes().Case_Open_Labels())
