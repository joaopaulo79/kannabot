import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import psycopg
from kannabot import database
from kannabot._config.configuracao import carregar_configuracao, ErroConfiguracao


class DatabaseConfigurationTests(unittest.TestCase):
    def test_connection_error_never_contains_dsn(self):
        url = 'postgresql://test:private_password@invalid/db'
        with patch('psycopg.connect',side_effect=psycopg.OperationalError(url)):
            with self.assertRaises(psycopg.OperationalError) as raised:
                database.connect(url)
        self.assertNotIn('private_password',str(raised.exception))
        self.assertNotIn(url,str(raised.exception))

    def test_configuration_url_and_repr(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'groups.json').write_text('{"grupos_id": [1]}',encoding='utf-8')
            values = dict(CHAVE_API_BOT='123:fake',BOT_USERNAME='TesteBot',CAMINHO_AUTORZACAO='groups.json')
            url = 'postgresql://test:private_password@db/test'
            with patch.dict(os.environ,dict(values,DATABASE_URL=url),clear=True):
                cfg = carregar_configuracao(root)
                self.assertEqual(cfg.database_url,url)
                self.assertNotIn('private_password',repr(cfg))
            for url in ('mysql://db/test','postgresql://db','postgresql://db:invalid/test'):
                with patch.dict(os.environ,dict(values,DATABASE_URL=url),clear=True):
                    with self.assertRaises(ErroConfiguracao):carregar_configuracao(root)
