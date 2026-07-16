#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN="${DRY_RUN:-true}"
ARCHIVE_PATH=""
TARGET_DATABASE=""
CONFIRM_TARGET=""

usage() {
  cat <<'EOF'
Usage: restore_mongodb_backup.sh --archive PATH --target-database NAME [--execute] [--confirm-target NAME]

Validation-only dry-run is the default. Execution requires explicit target-environment guards.
Production-cluster execution additionally requires ALLOW_PRODUCTION_RESTORE=true,
PRODUCTION_RESTORE_CONFIRMATION=I_UNDERSTAND_THIS_WILL_REPLACE_PRODUCTION_DATA,
and a matching --confirm-target value.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) ARCHIVE_PATH="${2:-}"; shift 2 ;;
    --target-database) TARGET_DATABASE="${2:-}"; shift 2 ;;
    --confirm-target) CONFIRM_TARGET="${2:-}"; shift 2 ;;
    --execute) DRY_RUN=false; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "FAIL: unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

[[ -n "$ARCHIVE_PATH" && -n "$TARGET_DATABASE" ]] || { usage; exit 2; }
cd "$APP_DIR"
[[ -f "$ENV_FILE" ]] || { echo "FAIL: environment file is missing." >&2; exit 1; }
export AEROASSIST_ENV_FILE="$ENV_FILE"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

PRODUCTION_DATABASE="${MONGO_DATABASE:-${MONGODB_DATABASE:-aeroassist_agencyos}}"
RESTORE_TARGET_ENV="${RESTORE_TARGET_ENV:-validation}"
python3 "$SCRIPT_DIR/mongodb_backup_manifest.py" verify --archive "$ARCHIVE_PATH" >/dev/null
SOURCE_DATABASE="$(ARCHIVE_PATH="$ARCHIVE_PATH" python3 - <<'PY'
import json
import os
from pathlib import Path

archive = Path(os.environ["ARCHIVE_PATH"])
manifest = archive.with_name(archive.name.removesuffix(".archive.gz") + ".manifest.json")
print(json.loads(manifest.read_text(encoding="utf-8"))["database_name"])
PY
)"

echo "MongoDB restore plan"
echo "  archive: $(basename "$ARCHIVE_PATH")"
echo "  source database: $SOURCE_DATABASE"
echo "  target database: $TARGET_DATABASE"
echo "  target environment: $RESTORE_TARGET_ENV"
echo "  mode: $([[ "$DRY_RUN" == "true" ]] && echo validation-only || echo execute)"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "PASS: restore plan validated; no database connection or write occurred."
  exit 0
fi

if [[ "${APP_ENV:-production}" == "production" ]]; then
  [[ "$RESTORE_TARGET_ENV" == "production" ]] || { echo "FAIL: any restore into the production-configured MongoDB cluster requires RESTORE_TARGET_ENV=production." >&2; exit 1; }
  [[ "${ALLOW_PRODUCTION_RESTORE:-false}" == "true" ]] || { echo "FAIL: production restore is disabled." >&2; exit 1; }
  [[ "${PRODUCTION_RESTORE_CONFIRMATION:-}" == "I_UNDERSTAND_THIS_WILL_REPLACE_PRODUCTION_DATA" ]] || { echo "FAIL: production restore confirmation phrase is missing." >&2; exit 1; }
  [[ "$CONFIRM_TARGET" == "$TARGET_DATABASE" ]] || { echo "FAIL: --confirm-target must exactly match the requested production-cluster target." >&2; exit 1; }
else
  [[ "$RESTORE_TARGET_ENV" == "test" ]] || { echo "FAIL: non-production execution requires RESTORE_TARGET_ENV=test." >&2; exit 1; }
  [[ "${ALLOW_DESTRUCTIVE_TEST_RESTORE:-false}" == "true" ]] || { echo "FAIL: test restore requires ALLOW_DESTRUCTIVE_TEST_RESTORE=true." >&2; exit 1; }
  [[ "$TARGET_DATABASE" != "$PRODUCTION_DATABASE" ]] || { echo "FAIL: non-production execution refuses the configured source/production database name." >&2; exit 1; }
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T \
  -e RESTORE_SOURCE_DATABASE="$SOURCE_DATABASE" \
  -e RESTORE_TARGET_DATABASE="$TARGET_DATABASE" \
  mongo sh -eu -c '
    if [ -z "${MONGO_INITDB_ROOT_USERNAME:-}" ] || [ -z "${MONGO_INITDB_ROOT_PASSWORD:-}" ]; then
      echo "FAIL: restore execution requires administrative MongoDB credentials." >&2
      exit 1
    fi
    exec mongorestore --host 127.0.0.1 --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip --drop --stopOnError --nsFrom "$RESTORE_SOURCE_DATABASE.*" --nsTo "$RESTORE_TARGET_DATABASE.*"
  ' < "$ARCHIVE_PATH"

AUDIT_LOG="${RESTORE_AUDIT_LOG:-$BACKUP_ROOT/mongodb-restore-audit.log}"
mkdir -p "$(dirname "$AUDIT_LOG")"
touch "$AUDIT_LOG"
chmod 600 "$AUDIT_LOG"
printf '%s archive=%s source=%s target=%s environment=%s result=completed\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(basename "$ARCHIVE_PATH")" "$SOURCE_DATABASE" "$TARGET_DATABASE" "$RESTORE_TARGET_ENV" >> "$AUDIT_LOG"
echo "PASS: explicitly authorized restore completed; validate the target before any cutover."
