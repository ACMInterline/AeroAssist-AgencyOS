#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_PATH="${1:-${ARCHIVE_PATH:-}}"

cd "$APP_DIR"
export AEROASSIST_ENV_FILE="$ENV_FILE"
if [[ -z "$ARCHIVE_PATH" ]]; then
  ARCHIVE_PATH="$(find "$BACKUP_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'mongodb-*.archive.gz' 2>/dev/null | sort | tail -n 1)"
fi
[[ -n "$ARCHIVE_PATH" ]] || { echo "FAIL: no MongoDB backup archive was found." >&2; exit 1; }

python3 "$SCRIPT_DIR/mongodb_backup_manifest.py" verify --archive "$ARCHIVE_PATH"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mongo sh -eu -c '
  if [ -n "${MONGO_APP_USERNAME:-}" ] && [ -n "${MONGO_APP_PASSWORD:-}" ]; then
    exec mongorestore --quiet --host 127.0.0.1 --username "$MONGO_APP_USERNAME" --password "$MONGO_APP_PASSWORD" --authenticationDatabase "${MONGO_AUTH_SOURCE:-admin}" --archive --gzip --dryRun
  fi
  exec mongorestore --quiet --host 127.0.0.1 --archive --gzip --dryRun
' < "$ARCHIVE_PATH" >/dev/null

python3 "$SCRIPT_DIR/mongodb_backup_manifest.py" mark --archive "$ARCHIVE_PATH" --status archive_inspected
echo "PASS: checksum, manifest, and MongoDB archive inspection succeeded."
