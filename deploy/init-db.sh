#!/bin/sh
set -eu
export KANNA_APP_PASSWORD="$(cat /run/secrets/app_password)"
export KANNA_MONITOR_PASSWORD="$(cat /run/secrets/monitor_password)"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
\getenv app_password KANNA_APP_PASSWORD
\getenv monitor_password KANNA_MONITOR_PASSWORD
CREATE ROLE kanna_app LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE kanna_monitor LOGIN PASSWORD :'monitor_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
ALTER ROLE kanna_monitor SET default_transaction_read_only = on;
REVOKE ALL ON DATABASE kanna FROM PUBLIC;
GRANT CONNECT ON DATABASE kanna TO kanna_app, kanna_monitor;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO kanna_app;
GRANT USAGE ON SCHEMA public TO kanna_monitor;
ALTER DEFAULT PRIVILEGES FOR ROLE kanna_app IN SCHEMA public GRANT SELECT ON TABLES TO kanna_monitor;
ALTER DEFAULT PRIVILEGES FOR ROLE kanna_app IN SCHEMA public GRANT SELECT ON SEQUENCES TO kanna_monitor;
SQL
unset KANNA_APP_PASSWORD KANNA_MONITOR_PASSWORD
