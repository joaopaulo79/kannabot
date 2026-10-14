#!/bin/sh
set -eu
umask 077
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
mkdir -p "$root/backups"
name="kanna-$(date -u +%Y%m%dT%H%M%SZ)-$$.dump"
temporary="$root/backups/$name.partial"
trap 'rm -f "$temporary"' EXIT
sudo -n docker compose --env-file "$root/compose.env" -f "$root/release/compose.yaml" exec -T db pg_dump -U postgres -d kanna --format=custom > "$temporary"
mv "$temporary" "$root/backups/$name"
printf '%s\n' "Backup criado em $root/backups/$name"
