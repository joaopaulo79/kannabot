"""Testes sem rede ou acesso ao .env real da Kanna."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "configuracao_isolada", RAIZ / "src/kannabot/_config/configuracao.py"
)
config = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = config
spec.loader.exec_module(config)
TOKEN_FICTICIO = "123456:credencial_ficticia"


class TestConfiguracao(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.raiz = Path(self.temporario.name)
        self.grupos = self.raiz / "grupos.json"
        self.grupos.write_text('{"grupos_id": []}', encoding="utf-8")
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def ambiente_valido(self):
        os.environ.update(
            CHAVE_API_BOT=TOKEN_FICTICIO,
            BOT_USERNAME="KannaTesteBot",
            CAMINHO_AUTORZACAO="grupos.json",
        )

    def carregar(self):
        return config.carregar_configuracao(self.raiz)

    def test_token_ausente_vazio_espacos_e_invalido(self):
        self.ambiente_valido()
        for valor in (None, "", "  ", "segredo_invalido"):
            with self.subTest(valor=valor):
                if valor is None:
                    os.environ.pop("CHAVE_API_BOT", None)
                else:
                    os.environ["CHAVE_API_BOT"] = valor
                with self.assertRaises(config.ErroConfiguracao) as erro:
                    self.carregar()
                self.assertIn("CHAVE_API_BOT", str(erro.exception))
                if valor and valor.strip():
                    self.assertNotIn(valor, str(erro.exception))

    def test_carrega_env_sem_revelar_token_no_repr(self):
        (self.raiz / ".env").write_text(
            f"CHAVE_API_BOT={TOKEN_FICTICIO}\n"
            "BOT_USERNAME=@KannaTesteBot\nCAMINHO_AUTORZACAO=grupos.json\n",
            encoding="utf-8",
        )
        resultado = self.carregar()
        self.assertEqual(resultado.token, TOKEN_FICTICIO)
        self.assertNotIn(TOKEN_FICTICIO, repr(resultado))

    def test_ambiente_prevalece_inclusive_vazio(self):
        self.ambiente_valido()
        (self.raiz / ".env").write_text(
            "CHAVE_API_BOT=999999:outro_ficticio\n", encoding="utf-8"
        )
        self.assertEqual(self.carregar().token, TOKEN_FICTICIO)
        os.environ["CHAVE_API_BOT"] = ""
        with self.assertRaises(config.ErroConfiguracao):
            self.carregar()

    def test_sem_env_com_ambiente_completo(self):
        self.ambiente_valido()
        resultado = self.carregar()
        self.assertEqual(resultado.grupos_id, ())
        self.assertEqual(resultado.caminho_autorizacao, self.grupos.resolve())

    def test_nao_busca_env_em_diretorio_pai_ou_atual(self):
        self.ambiente_valido()
        pai = self.raiz / "pai"
        projeto = pai / "projeto"
        projeto.mkdir(parents=True)
        (pai / ".env").write_text(
            "CHAVE_API_BOT=999999:nao_carregar\n", encoding="utf-8"
        )
        os.environ.pop("CHAVE_API_BOT")
        with self.assertRaises(config.ErroConfiguracao):
            config.carregar_configuracao(projeto)
        self.ambiente_valido()
        anterior = Path.cwd()
        try:
            os.chdir(projeto)
            self.assertEqual(self.carregar().caminho_autorizacao, self.grupos.resolve())
        finally:
            os.chdir(anterior)

    def test_caminho_absoluto_e_grupos_inteiros(self):
        self.ambiente_valido()
        self.grupos.write_text('{"grupos_id": [-100123456, 456]}', encoding="utf-8")
        os.environ["CAMINHO_AUTORZACAO"] = str(self.grupos)
        self.assertEqual(self.carregar().grupos_id, (-100123456, 456))

    def test_caminho_ausente_e_arquivo_inexistente(self):
        self.ambiente_valido()
        for valor in ("", "nao-existe.json"):
            os.environ["CAMINHO_AUTORZACAO"] = valor
            with self.assertRaises(config.ErroConfiguracao) as erro:
                self.carregar()
            self.assertIn("CAMINHO_AUTORZACAO", str(erro.exception))

    def test_json_invalido_e_estrutura_incorreta(self):
        self.ambiente_valido()
        casos = ("conteudo_privado_invalido", "[]", "{}", '{"grupos_id": null}',
                 '{"grupos_id": "123"}', '{"grupos_id": [true]}',
                 '{"grupos_id": [1.5]}', '{"grupos_id": ["123"]}')
        for texto in casos:
            with self.subTest(texto=texto):
                self.grupos.write_text(texto, encoding="utf-8")
                with self.assertRaises(config.ErroConfiguracao) as erro:
                    self.carregar()
                self.assertNotIn(texto, str(erro.exception))

    def test_username_normalizado_e_invalido(self):
        self.ambiente_valido()
        for valor in ("KannaTesteBot", "@KannaTesteBot"):
            os.environ["BOT_USERNAME"] = valor
            self.assertEqual(self.carregar().bot_username, "@KannaTesteBot")
        for valor in ("", "@@KannaTesteBot", "nome com espacos", "abc"):
            os.environ["BOT_USERNAME"] = valor
            with self.assertRaises(config.ErroConfiguracao):
                self.carregar()

    def test_importacao_nao_tem_dependencia_de_telebot(self):
        self.assertNotIn("telebot", config.__dict__)

    def executar_integracao(self, token):
        # Subprocesso com ambiente fictício; load_dotenv é substituído antes
        # de importar src, e socket bloqueia qualquer tentativa de rede.
        codigo = '''
import runpy
from unittest.mock import patch
import dotenv
import telebot
with patch.object(dotenv, "load_dotenv", return_value=False), \
     patch("socket.socket", side_effect=AssertionError("Rede proibida")), \
     patch.object(telebot, "TeleBot") as cliente:
    try:
        runpy.run_path("main.py", run_name="__main__")
    except SystemExit as erro:
        assert "CHAVE_API_BOT" in str(erro)
        cliente.assert_not_called()
        print("configuracao bloqueada antes do cliente")
    else:
        cliente.assert_called_once()
        cliente.return_value.infinity_polling.assert_called_once()
        print("inicializacao e polling simulados")
'''
        ambiente = dict(os.environ)
        ambiente.update(
            CHAVE_API_BOT=token,
            BOT_USERNAME="KannaTesteBot",
            CAMINHO_AUTORZACAO=str(self.grupos),
            PYTHONPATH=str(RAIZ / "src"),
            SYSTEMROOT=os.getenv("SYSTEMROOT", "C:\\Windows"),
        )
        return subprocess.run(
            [sys.executable, "-c", codigo], cwd=RAIZ, env=ambiente,
            text=True, capture_output=True, timeout=20,
        )

    def test_integracao_invalida_nao_cria_cliente(self):
        resultado = self.executar_integracao("")
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("bloqueada", resultado.stdout)

    def test_integracao_valida_sem_rede(self):
        resultado = self.executar_integracao(TOKEN_FICTICIO)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("simulados", resultado.stdout)
        self.assertNotIn(TOKEN_FICTICIO, resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()
