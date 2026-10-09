# Kanna

Bot Telegram em Python com comandos de emotes e botões interativos. O MVP
administrativo está em desenvolvimento: moderação, antispam, boas-vindas e
logs administrativos ainda não estão implementados.

## Preparação no Windows / PowerShell

Use Python 3.10. O projeto aceita `>=3.10,<3.11`. Execute os comandos na raiz
do repositório. O ambiente do bot fica em `.venv`; o Poetry fica separado em
`.tools/poetry`, ambos ignorados pelo Git.

```powershell
py -3.10 --version
py -3.10 -m venv .venv
py -3.10 -m venv .tools/poetry
& .tools/poetry/Scripts/python.exe -m pip install "poetry==1.8.5"
& .tools/poetry/Scripts/poetry.exe env use .venv/Scripts/python.exe
& .tools/poetry/Scripts/poetry.exe install
```

O Poetry usa `poetry.lock` para instalar as versões registradas. Não use uma
instalação avulsa de dependências para contornar o lock. `--no-root` instala
somente as dependências enquanto a estrutura atual não é um pacote distribuível.

No VS Code, selecione o Python da `.venv`: `Ctrl+Shift+P` →
`Python: Select Interpreter` → `.venv\Scripts\python.exe`. O projeto indica
`.venv` como ambiente padrão; uma seleção anterior no editor precisa ser
alterada manualmente. Se `from dotenv import load_dotenv` aparecer como import
não encontrado, confira essa seleção e recarregue a janela. O pacote instalado
se chama `python-dotenv`, e seu módulo Python se chama `dotenv`.

## Configuração local

Crie os arquivos locais apenas se não existirem:

```powershell
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
if (-not (Test-Path data/local/grupos_autorizados.json)) {
    New-Item -ItemType Directory -Path data/local -Force | Out-Null
    Copy-Item config/grupos_autorizados.example.json data/local/grupos_autorizados.json
}
```

Edite `.env` localmente, sem enviar o token ao chat, a comandos ou ao GitHub:

| Variável | Valor necessário |
|---|---|
| `CHAVE_API_BOT` | Token do bot de testes fornecido pelo BotFather. |
| `CAMINHO_AUTORZACAO` | Caminho do JSON de grupos; o exemplo usa `data/local/grupos_autorizados.json`. |
| `BOT_USERNAME` | Username público do bot de testes, com ou sem `@`; não é seu username pessoal. |

O nome legado `CAMINHO_AUTORZACAO` foi preservado. Caminhos relativos são
resolvidos a partir da raiz do projeto. Somente o `.env` dessa raiz é carregado;
variáveis já definidas no processo prevalecem, inclusive valores vazios.
Sem `.env`, todas as variáveis podem ser fornecidas pelo ambiente.

O JSON local deve ter `grupos_id` como lista de IDs numéricos dos grupos de
testes. A lista vazia inicial não autoriza nenhum grupo. Não copie os IDs
legados de outros grupos para fazer testes. A obtenção e validação do ID do
grupo ocorrerá na preparação do teste funcional no Telegram.

O token real fica exclusivamente no `.env` local, que é texto simples e está
ignorado pelo Git. `.env.example` é versionado com campos de credenciais vazios.
Adicionar um arquivo ao `.gitignore` não remove seu versionamento anterior.
O registro legado de cliques já está rastreado e sua migração é uma tarefa futura.

## Verificações sem Telegram

```powershell
& .venv/Scripts/python.exe -m unittest discover -s tests -v
& .venv/Scripts/python.exe -m pip check
git check-ignore .env .venv/probe data/local/grupos_autorizados.json
git ls-files -- .env
```

Os testes usam diretórios temporários e valores fictícios, não leem o `.env`
real e bloqueiam rede na integração simulada. `git ls-files -- .env` deve
retornar vazio. `.env.example` e o exemplo JSON não devem ser ignorados.

## Execução no grupo de testes

Crie uma identidade separada em [BotFather](https://t.me/BotFather), configure
seu username e autorize somente o grupo privado de testes no JSON local.
Use uma única instância em polling por token. Não reutilize a identidade
de produção enquanto testa o desenvolvimento.

Depois de configurar e confirmar o ambiente de testes:

```powershell
& .tools/poetry/Scripts/poetry.exe run python -m kannabot
```

Esse comando conecta o bot ao Telegram. Execute na raiz porque os recursos
de emotes ainda usam caminhos relativos. Pare com `Ctrl+C`.

Token vazio ou com formato inválido, username inválido, caminho ausente ou
JSON inválido interrompem a inicialização com mensagem sanitizada. A validação
local não confirma se o token é autêntico nem se o username corresponde a ele.
Falhas de permissão no Telegram exigem conferir os direitos do bot no grupo.

## Fluxo de desenvolvimento

- `main`: versão preservada.
- `develop`: integração do MVP.
- Branch da issue: `<tipo>/<número>`, por exemplo `chore/1`.
- Commits: `#<número>-<descrição-curta>`.
- PRs direcionados a `develop`, com `Refs #1` para esta tarefa.

Esta preparação não corrige a autorização de administradores nem o estado
compartilhado dos emotes. Esses problemas precisam ser resolvidos antes de
habilitar moderação ou usar esta fase do desenvolvimento em produção.

## Pacote e dados
Imports não inicializam o bot. Use `python -m kannabot`. `KANNA_HOME` aponta para a pasta local de configuração (.env, data/local, var) ao executar fora da raiz. Os recursos estáticos acompanham o pacote; cliques usam var, nunca arquivos rastreados. O estado antigo dos botões é efêmero e não é migrado; o histórico Git permanece intacto.

## Auditoria administrativa

Configure `LOG_CHAT_ID` no `.env` local com o ID negativo de um grupo privado dedicado aos administradores. Adicione o bot e permita enviar mensagens. Mantenha nesse grupo somente pessoas autorizadas a consultar moderacao; nao configure um grupo publico. Cada registro inclui horario UTC, grupo, autor (ou automacao), alvo, acao, motivo e resultado.

Sem destino configurado, destino publico ou falha de entrega, o registro sanitizado vai para `KANNA_HOME/var/audit.jsonl`. Falhar ao registrar nao repete uma punicao. O arquivo local e ignorado pelo Git; restrinja seu acesso e retenha apenas pelo periodo necessario. Erros registram a classe da excecao, sem payload ou token.

## Advertencias

Admin identificado: responda a mensagem do membro com `/warn motivo`. Consulte com `/warnings` em resposta ao mesmo membro. Historico por grupo/ID fica em `KANNA_HOME/var/moderation.sqlite3`, preservado no reinicio. Consulta mostra total e ultimas 20 entradas. Reentregar o mesmo comando nao duplica advertencia. Administradores sao protegidos; quantidade de advertencias nao aplica outra punicao.
