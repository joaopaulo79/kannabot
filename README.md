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

Esse comando conecta o bot ao Telegram. Os recursos acompanham o pacote; configure `KANNA_HOME` ao executar fora da raiz. Pare com `Ctrl+C`.

Token vazio ou com formato inválido, username inválido, caminho ausente ou
JSON inválido interrompem a inicialização com mensagem sanitizada. A validação
local não confirma se o token é autêntico nem se o username corresponde a ele.
Falhas de permissão no Telegram exigem conferir os direitos do bot no grupo.

## Fluxo de desenvolvimento

- `main`: versão preservada.
- `develop`: integração do MVP.
- Branch da issue: `<tipo>/<número>`, por exemplo `chore/1`.
- Commits: `#<número> - <descrição-curta>`.
- PRs direcionados a `develop`, com `Refs #1` para esta tarefa.

As etapas posteriores separam autorização administrativa dos emotes e isolam o estado das interações. A validação real no Telegram continua pendente.

## Pacote e dados
Imports não inicializam o bot. Use `python -m kannabot`. `KANNA_HOME` aponta para a pasta local de configuração (.env, data/local, var) ao executar fora da raiz. Os recursos estáticos acompanham o pacote; cliques usam var, nunca arquivos rastreados. O estado antigo dos botões é efêmero e não é migrado; o histórico Git permanece intacto.

## Auditoria administrativa

Configure `LOG_CHAT_ID` no `.env` local com o ID negativo de um grupo privado dedicado aos administradores. Adicione o bot e permita enviar mensagens. Mantenha nesse grupo somente pessoas autorizadas a consultar moderacao; nao configure um grupo publico. Cada registro inclui horario UTC, grupo, autor (ou automacao), alvo, acao, motivo e resultado.

Sem destino configurado, destino publico ou falha de entrega, o registro sanitizado vai para `KANNA_HOME/var/audit.jsonl`. Falhar ao registrar nao repete uma punicao. O arquivo local e ignorado pelo Git; restrinja seu acesso e retenha apenas pelo periodo necessario. Erros registram a classe da excecao, sem payload ou token.

## Advertencias

Admin identificado: responda a mensagem do membro com `/warn motivo`. Consulte com `/warnings` em resposta ao mesmo membro. Historico por grupo/ID fica em `KANNA_HOME/var/moderation.sqlite3`, preservado no reinicio. Consulta mostra total e ultimas 20 entradas. Reentregar o mesmo comando nao duplica advertencia. Administradores sao protegidos; quantidade de advertencias nao aplica outra punicao.

Exclusao: admin responde a mensagem com `/delete motivo`. O bot precisa de permissao de apagar mensagens. Somente a mensagem respondida e apagada; repeticao do mesmo alvo por 10 minutos e recusada. Limites/erros Telegram geram falha, sem sucesso presumido.

Silencio: `/mute 10m motivo` em resposta ao membro. Duracoes aceitam inteiro + `s`, `m`, `h` ou `d`, entre 60 segundos e 365 dias. Somente supergrupo e bot com direito de restringir membros. A data de termino fica no Telegram; nao depende de timer local nem de manter o processo ligado. Intervalo conserva margem dos limites de permanencia da API: https://core.telegram.org/bots/api#restrictchatmember.

Remocao: `/kick motivo` expulsa e libera retorno voluntario; `/ban motivo` impede retorno; `/unban motivo` em resposta a uma mensagem antiga do membro remove banimento sem adiciona-lo. Kick/unban requerem supergrupo; bot precisa de `can_restrict_members`. Se a segunda etapa de kick falhar, o retorno informa que o membro continua banido; nao ha retry automatico. Consulte auditoria e use unban depois de corrigir a permissao.

## Politicas por grupo e boas-vindas

Copie `config/politicas.example.json` para `data/local/politicas.json`, ajuste o ID real e configure `CAMINHO_POLITICAS=data/local/politicas.json`. Cada grupo autorizado pode ter `welcome.text` e `welcome.rules` (texto ou link, ate 250 caracteres cada). `{user}` e substituido por username ou ID. Uma mensagem por membro em entradas multiplas; reentrega do mesmo evento e ignorada por 10 minutos. Sem politica, boas-vindas ficam desligadas. Falha de envio e auditada e nao repete automaticamente. Reinicie para carregar mudancas do arquivo.

## Antispam em observacao

Opcao por grupo: `spam` com `flood_limit`, `flood_window`, `repeat_limit`, `repeat_window`. Limites inteiros 1..100; janelas em segundos 1..3600. Detecao ao exceder limite; janela (agora-janela, agora]. Repeticao compara texto/legenda NFKC, caixa ignorada, espacos colapsados. Ignora bots, autores anonimos, admins, servico e duplicatas. Logs limitados por regra/usuario/grupo a um/60s. Estado limitado e temporario, reinicio zera contadores. Somente observacao, sem punicoes.

Links: opcao `links` por grupo com `allow` e `deny` (listas de hosts) e `include_subdomains` booleano. Deny prevalece; allow nao vazio exige dominio listado. Subdominios so entram quando a opcao e true, por sufixo `.dominio`, nunca substring. Hosts normalizados IDNA/caixa/ponto final. Esquemas HTTP/HTTPS; URL malformada ou esquema de entidade nao suportado e sinalizado. Texto, legenda e entidades url/text_link sao inspecionados, respeitando offsets UTF-16. Sem visitas, redirects ou reputacao externa. Ainda somente observa.

## Revisao humana das deteccoes

Antispam nao aplica sancoes. Deteccoes ficam no SQLite por grupo/mensagem, agregando flood/repeticao/links. `/detections` lista ate20 pendentes; `/dismiss ID motivo` descarta com auditoria; `/review ID warn R10 motivo` escolhe advertencia explicitamente; mute: `/review ID mute 1d R10 motivo`. Resolucao exige catalogo disponivel (ligado pela #15), regra ativa e permissao atual do autor. Com o catálogo importado explicitamente pelo Dono, a decisão usa os cargos internos e as ações previstas na regra. Uma reserva persistida impede decisoes simultaneas/repetidas. Falha/resultado incerto nao retorna automaticamente a fila; conferir logs antes de nova acao manual. Notificacao limitada a uma por usuario/grupo a cada60s.

## Cargos internos e catálogo manual (#15)

O Dono é o proprietário real do grupo (`creator` no Telegram). Somente ele atribui
Admin/Mod internos, por ID e por grupo. Quem não tem atribuição é participante comum,
mesmo quando possui um título cosmético no Telegram. Títulos não concedem privilégios
no bot; aparecem nos registros para auditoria. Os emotes continuam disponíveis aos membros.

| Cargo | Ações internas |
| --- | --- |
| Dono | Todas as ações abaixo e administração de cargos/regras |
| Admin | Warn, consulta/cancelamento de advertências, exclusão, mute, kick, ban, unban e revisão |
| Mod | Warn, consulta, exclusão, mute e revisão; sem kick, ban ou unban |

Nenhuma sanção alcança cargo igual ou superior. O bot verifica também seus próprios
privilégios no Telegram. Um título cosmético não elimina as limitações reais da API:
um administrador nativo do Telegram pode exigir intervenção do Dono antes da sanção.
As consultas de identidade falham sem conceder autorização.

Comandos de administração:

- `/role admin` ou `/role mod`, em resposta ao alvo, e `/role_remove`: somente Dono.
- `/rules_import`: Dono importa explicitamente as 19 entradas resumidas do livro recebido;
  não sobrescreve regras existentes. Enquetes (R04) permanece revogada.
- `/rule_set JSON`: Dono cria uma versão imutável com os campos `code`, `name`,
  `description`, `level`, `weight`, `active` e `actions`. Exemplo:
  `{"code":"R20","name":"Nova regra","description":"Descrição","level":"N2","weight":2,"active":true,"actions":["warn","delete","mute"]}`.
- `/rule_disable R20`: nova versão revogada; ocorrências antigas mantêm seus dados.
- `/catalog` ou `/catalog R10`: consulta da Staff (lista limitada a 20 entradas).
- `/warn R10 motivo`, em resposta: registra uma infração com código, versão e peso.
- `/mute 1d R10 motivo`, em resposta: executa somente o silêncio solicitado, dentro da faixa do nível.
- `/unwarn ID motivo`: Admin/Dono cancela uma infração sem apagar seu histórico, respeitando a hierarquia.

O banco local `var/moderation.sqlite3` guarda cargos, regras, infrações e tentativas/resultados
de sanções. A migração preserva advertências antigas com peso indefinido. Não versionar o banco.
O registro persistente antecede a chamada ao Telegram; duplicatas não repetem efeitos,
mesmo após reinício. Timeout conserva resultado incerto, e uma expulsão incompleta registra
resultado parcial. Esses casos exigem inspeção humana, sem repetição automática.

Quatro pontos apenas indicam revisão humana. Não há ban automático, nem execução de um
pacote de punições ao escolher um nível. N1 não recebe peso inventado; regras especiais
sem condições definidas ficam indisponíveis para as ações indefinidas. Expiração de pontos,
reincidência de N1, duração para nome de usuário especial e escolha entre ban de 30 dias ou
permanente continuam dependendo de uma decisão do Dono. Comandos legados com motivo livre
continuam manuais e não adicionam peso presumido.
