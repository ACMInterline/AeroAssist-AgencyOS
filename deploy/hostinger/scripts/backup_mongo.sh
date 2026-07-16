#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
TIMESTAMP="${TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
BACKUP_ENVIRONMENT_LABEL="${BACKUP_ENVIRONMENT_LABEL:-production}"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="$BACKUP_DIR/mongodb-$TIMESTAMP.archive.gz"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

cleanup_partial() {
  rm -f -- "$ARCHIVE" "$ARCHIVE.sha256" "${ARCHIVE%.archive.gz}.manifest.json"
}
trap cleanup_partial ERR

cd "$APP_DIR"
[[ -f "$ENV_FILE" ]] || fail "Environment file is missing."
[[ "$TIMESTAMP" =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || fail "TIMESTAMP must use YYYYMMDDTHHMMSSZ format."
export AEROASSIST_ENV_FILE="$ENV_FILE"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

MONGO_DATABASE="${MONGO_DATABASE:-${MONGODB_DATABASE:-aeroassist_agencyos}}"
if [[ "${APP_ENV:-development}" == "production" && "${MONGO_AUTHENTICATION_ENABLED:-false}" != "true" ]]; then
  fail "Production backup refuses unauthenticated MongoDB."
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_ROOT" "$BACKUP_DIR"

echo "Creating timestamped MongoDB backup: $(basename "$ARCHIVE")"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mongo sh -eu -c '
  if [ -n "${MONGO_APP_USERNAME:-}" ] && [ -n "${MONGO_APP_PASSWORD:-}" ]; then
    exec mongodump --quiet --host 127.0.0.1 --username "$MONGO_APP_USERNAME" --password "$MONGO_APP_PASSWORD" --authenticationDatabase "${MONGO_AUTH_SOURCE:-admin}" --db "$MONGO_DATABASE" --archive --gzip
  fi
  exec mongodump --quiet --host 127.0.0.1 --db "$MONGO_DATABASE" --archive --gzip
' > "$ARCHIVE"

[[ -s "$ARCHIVE" ]] || fail "mongodump produced an empty archive."
chmod 600 "$ARCHIVE"

collection_counts="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mongo sh -eu -c '
  script="const target=db.getSiblingDB(process.env.MONGO_DATABASE); const names=target.getCollectionNames().sort(); print(JSON.stringify(Object.fromEntries(names.map(name => [name, target.getCollection(name).countDocuments({})]))));"
  if [ -n "${MONGO_APP_USERNAME:-}" ] && [ -n "${MONGO_APP_PASSWORD:-}" ]; then
    exec mongosh --quiet --host 127.0.0.1 --username "$MONGO_APP_USERNAME" --password "$MONGO_APP_PASSWORD" --authenticationDatabase "${MONGO_AUTH_SOURCE:-admin}" --eval "$script"
  fi
  exec mongosh --quiet --host 127.0.0.1 --eval "$script"
')"
mongo_version="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mongo mongod --version | head -n 1)"
tool_version="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mongo mongodump --version | head -n 1)"
git_commit="$(git rev-parse --verify HEAD 2>/dev/null || echo unknown)"
current_phase="$(PYTHONPATH=backend python3 -c 'from build_phase import CURRENT_BUILD_PHASE; print(CURRENT_BUILD_PHASE)')"

python3 "$SCRIPT_DIR/mongodb_backup_manifest.py" create \
  --archive "$ARCHIVE" \
  --timestamp "$TIMESTAMP" \
  --database "$MONGO_DATABASE" \
  --git-commit "$git_commit" \
  --phase "$current_phase" \
  --mongodb-version "$mongo_version" \
  --tool-version "$tool_version" \
  --environment-label "$BACKUP_ENVIRONMENT_LABEL" \
  --collection-counts "$collection_counts" \
  --document-export-reference "document_exports.tar.gz"

APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
  "$SCRIPT_DIR/verify_mongodb_backup.sh" "$ARCHIVE"

trap - ERR
echo "PASS: MongoDB backup and archive inspection complete."
echo "Restore tooling defaults to validation-only mode."
