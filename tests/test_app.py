import os
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
            self.assertTrue(set("punch slap kiss shy hug cuddle pat push stare highfive poke bite lick bonk tickle wave cry".split()).issubset(set(commands)))
            client.infinity_polling.assert_not_called()
            self.assertTrue((Path(folder)/"var/moderation.sqlite3").exists())

    def test_resources_without_cwd(self):
        self.assertIn("h", Abrir_Arquivos_Emotes().Case_Open_Labels())

    def test_kanna_home_loads_configuration_and_state_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / "groups.json").write_text('{"grupos_id": [-1001]}', encoding="utf-8")
            (root / ".env").write_text(
                "CHAVE_API_BOT=123:fake\nBOT_USERNAME=TesteBot\nCAMINHO_AUTORZACAO=groups.json\n",
                encoding="utf-8",
            )
            client = MagicMock()
            with patch.dict(os.environ, {"KANNA_HOME": folder}, clear=True), patch("kannabot.app.register") as register:
                self.assertIs(create_app(client=client), client)
                settings = register.call_args.args[1]
                self.assertEqual(settings.caminho_autorizacao, root / "groups.json")
                self.assertEqual(settings.grupos_id, (-1001,))
                self.assertEqual(register.call_args.args[2], root / "var")
            client.infinity_polling.assert_not_called()

    def test_kanna_home_with_injected_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            cfg = Configuracao("123:fake", root / "groups.json", (-1001,), "@TesteBot")
            client = MagicMock()
            with patch.dict(os.environ, {"KANNA_HOME": folder}, clear=True), patch("kannabot.app.register") as register, patch("kannabot.app.carregar_configuracao") as load:
                create_app(configuracao=cfg, client=client)
                load.assert_not_called()
                register.assert_called_once_with(client, cfg, root / "var")

    def test_explicit_home_overrides_kanna_home(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as other:
            root = Path(folder).resolve()
            cfg = Configuracao("123:fake", root / "groups.json", (-1001,), "@TesteBot")
            client = MagicMock()
            with patch.dict(os.environ, {"KANNA_HOME": other}, clear=True), patch("kannabot.app.register") as register:
                create_app(configuracao=cfg, client=client, home=folder)
                register.assert_called_once_with(client, cfg, root / "var")
