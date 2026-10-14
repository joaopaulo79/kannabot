# Operação com Docker e PostgreSQL

A configuração define dois serviços: `kanna` e `db`. Use uma única instância por token. O runtime verifica a identidade e recusa polling se houver webhook; não remove webhook automaticamente.

## Configuração privada

Mantenha um diretório privado fora do checkout/contexto de build, indicado por `KANNA_PRIVATE_DIR`. Ele deve conter:

- `bot.env`: CHAVE_API_BOT, BOT_USERNAME e LOG_CHAT_ID opcional.
- `config/groups.json`: JSON com grupos_id numéricos autorizados.
- `config/policies.json`: políticas por grupo, ou `{}`.
- `postgres_password`, `app_password`, `monitor_password`: senhas distintas.
- `database_url`: URL PostgreSQL da conta kanna_app, host db e banco kanna.

O diretório privado deve ter acesso restrito no host. Os arquivos montados como secrets precisam ser legíveis pelos usuários dos containers; não basta mudar uid/mode no Compose para arquivos bind-mounted. O Compose não criptografa os arquivos de origem. Nunca coloque esses arquivos no Git ou no diretório enviado ao build.

Um arquivo externo de opções, sem credenciais, pode definir KANNA_PRIVATE_DIR, KANNA_IMAGE_TAG e KANNA_SOURCE_REVISION. Execute `docker compose --env-file /caminho/compose.env -f /caminho/release/compose.yaml config --quiet` antes de subir.

## Build e inicialização

`docker compose --env-file /caminho/compose.env -f /caminho/release/compose.yaml build kanna`

`docker compose --env-file /caminho/compose.env -f /caminho/release/compose.yaml up -d --wait`

As imagens base são fixadas por digest e as dependências da aplicação vêm do poetry.lock. O build possui estágio separado; a aplicação executa como UID 10001, com filesystem raiz somente leitura, /tmp temporário e volume próprio de estado.

O banco inicia uma base nova. init-db.sh cria kanna_app sem superuser/createdb/createrole e kanna_monitor com consulta, sem escrita. O schema é inicializado pela aplicação; as concessões padrão permitem consultar tabelas futuras.

O banco publica apenas `127.0.0.1:15432` na VM. Não abra 5432/15432 na Internet, nem exponha o socket/API Docker por TCP.

## Saúde, memória e reinício

- PostgreSQL: pg_isready, limite de 256 MiB, buffers de 64 MiB e até 25 conexões.
- Kanna: limite de 384 MiB; saúde exige polling concluído nos últimos 120s e leitura da versão do schema. O healthcheck não envia comandos ao Telegram.
- Ambos: restart unless-stopped, rotação json-file de 3 arquivos de até 10 MiB.
- Um container unhealthy não é reiniciado automaticamente só por estar unhealthy. infinity_polling trata falhas transitórias; saída de processo é coberta pela política de restart. Monitore a saúde.
- KANNA_SKIP_PENDING=true descarta backlog inicial para evitar executar comandos antigos. Ajustar isso é uma decisão operacional; o padrão do container é seguro para a identidade de testes.
- SIGTERM solicita parada do polling; grace period de 45s. Volumes persistem no restart e na recriação, desde que não sejam removidos.
- VM de 1 GiB exige observar memória/OOM; não há promessa de capacidade para cinco grupos nem de disponibilidade garantida da hospedagem gratuita.

## Acesso a partir do PC

Use um alias SSH privado `kanna` para a VM e um alias `kanna-db` que encaminhe `127.0.0.1:15432` local para a mesma porta no loopback da VM. A chave privada fica somente na configuração privada local.

- Banco: `ssh -N kanna-db`. Cliente gráfico conecta em 127.0.0.1, porta 15432, database kanna, usuário kanna_monitor. Senha permanece em arquivo privado, nunca em argumento de processo.
- Estado: `ssh kanna 'sudo -n docker ps --filter label=com.docker.compose.project=kanna'`.
- Uso: `ssh kanna 'sudo -n docker stats --no-stream kanna-bot kanna-db'`.
- Logs: `ssh kanna 'sudo -n docker logs --tail 50 kanna-bot'`.

Essas consultas usam o acesso SSH administrativo existente; não exigem adicionar o usuário ao grupo docker nem ativar uma API Docker pública. O painel do Docker Desktop local não é a interface da VM. Há um script privado de atalhos no PC; seu conteúdo não carrega credenciais.

## Testes PostgreSQL isolados

Crie uma base descartável cujo nome comece com `kanna_test_`, com schema sob controle da conta de testes. Monte a conexão em arquivo privado e indique KANNA_TEST_DATABASE_URL_FILE ao executar `python -m deploy.validate`, com o checkout montado em /work e cwd /work.

O runner recusa um nome de banco fora desse prefixo, bloqueia rede HTTP/Telegram, usa KANNA_HOME temporário e executa a suíte incluindo integração PostgreSQL. Os testes fazem TRUNCATE: nunca aponte para kanna ou dados reais. O container de validação é temporário e deve ser removido ao final; os serviços finais continuam sendo apenas kanna e db.

## Backup e recuperação

No layout `raiz/release` + `raiz/compose.env`, execute `sh release/deploy/backup.sh`. O dump custom fica em raiz/backups com acesso restrito. Ele pode conter dados pessoais; copie para armazenamento protegido fora da VM. O backup de PostgreSQL não inclui o diretório privado nem o arquivo de auditoria do volume da aplicação.

Prove a restauração primeiro em outra base temporária, valide schema/contagens e só então defina um procedimento para recuperação real. Nunca execute compose down -v como rotina de atualização: isso remove dados persistentes. Não restaure sobre um banco real sem uma decisão explícita e backup válido.

## Após começar com base vazia

O Dono do grupo precisa executar /rules_import e atribuir os cargos internos desejados. Os registros antigos não são migrados. A allowlist ainda é a configuração por JSON e os logs ainda usam LOG_CHAT_ID global; esta entrega não implementa o controle global multi-grupo da auditoria. Use somente o grupo de testes aprovado até concluir esse escopo.
