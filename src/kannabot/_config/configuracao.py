"""Configuração local, sem criar cliente ou chamar a API do Telegram."""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


RAIZ_PROJETO = Path(__file__).resolve().parents[3]


class ErroConfiguracao(ValueError):
    """Erro de configuração que pode ser exibido sem revelar credenciais."""


@dataclass(frozen=True)
class Configuracao:
    token: str = field(repr=False)
    caminho_autorizacao: Path
    grupos_id: tuple[int, ...]
    bot_username: str
    log_chat_id: int | None = None


def carregar_configuracao(raiz: Path | None = None) -> Configuracao:
    """Lê apenas o .env do projeto; variáveis do processo têm precedência."""
    raiz = Path(raiz or os.getenv("KANNA_HOME", RAIZ_PROJETO)).resolve()
    load_dotenv(raiz / ".env", override=False, encoding="utf-8")

    token = os.getenv("CHAVE_API_BOT", "").strip()
    if not token:
        raise ErroConfiguracao(
            "CHAVE_API_BOT ausente ou vazia. Preencha o .env local."
        )
    if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
        raise ErroConfiguracao(
            "CHAVE_API_BOT tem formato inválido. Confira o token no .env local."
        )

    username = os.getenv("BOT_USERNAME", "").strip().removeprefix("@")
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
        raise ErroConfiguracao(
            "BOT_USERNAME ausente ou inválido. Informe o username do bot de testes."
        )

    caminho = os.getenv("CAMINHO_AUTORZACAO", "").strip()
    if not caminho:
        raise ErroConfiguracao(
            "CAMINHO_AUTORZACAO ausente. Informe o caminho do JSON local de grupos."
        )
    arquivo = Path(caminho)
    if not arquivo.is_absolute():
        arquivo = raiz / arquivo
    arquivo = arquivo.resolve()
    try:
        with arquivo.open(encoding="utf-8") as entrada:
            dados = json.load(entrada)
    except (OSError, ValueError):
        raise ErroConfiguracao(
            "CAMINHO_AUTORZACAO não aponta para um JSON legível e válido."
        ) from None

    grupos = dados.get("grupos_id") if isinstance(dados, dict) else None
    if not isinstance(grupos, list) or any(type(item) is not int for item in grupos):
        raise ErroConfiguracao(
            "O JSON de CAMINHO_AUTORZACAO deve conter grupos_id como lista de inteiros."
        )
    log_id = os.getenv("LOG_CHAT_ID", "").strip()
    if log_id and not re.fullmatch(r"-[1-9][0-9]*", log_id):
        raise ErroConfiguracao("LOG_CHAT_ID deve ser o ID negativo de um grupo privado.")
    return Configuracao(token, arquivo, tuple(grupos), f"@{username}", int(log_id) if log_id else None)
