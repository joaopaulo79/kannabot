import os
from pathlib import Path
from kannabot.app import create_app
from kannabot._config.configuracao import ErroConfiguracao, RAIZ_PROJETO

def main():
    try:
        bot = create_app(home=Path(os.getenv("KANNA_HOME", RAIZ_PROJETO)))
    except ErroConfiguracao as erro:
        raise SystemExit(f"Erro de configuração: {erro}") from None
    bot.infinity_polling(allowed_updates=["message", "callback_query"], skip_pending=False)

if __name__ == "__main__":
    main()
