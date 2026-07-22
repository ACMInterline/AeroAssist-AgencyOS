#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_PATH=""
TARGET_DATABASE=""
MONGO_IMAGE="${MONGO_IMAGE:-mongo:7}"
PRESERVE_DISPOSABLE_RESTORE="${PRESERVE_DISPOSABLE_RESTORE:-false}"
RESTORE_MONGO_NOFILE_SOFT="${RESTORE_MONGO_NOFILE_SOFT:-64000}"
RESTORE_MONGO_NOFILE_HARD="${RESTORE_MONGO_NOFILE_HARD:-64000}"
MINIMUM_RESTORE_MONGO_NOFILE=64000
CONTAINER_NAME="aeroassist-restore-rehearsal-${$}"
VOLUME_NAME="${CONTAINER_NAME}-data"

usage() {
  echo "Usage: test_restore_mongodb_backup.sh --archive PATH --target-database NAME"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) ARCHIVE_PATH="${2:-}"; shift 2 ;;
    --target-database) TARGET_DATABASE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "FAIL: unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

[[ -n "$ARCHIVE_PATH" && -n "$TARGET_DATABASE" ]] || { usage; exit 2; }
[[ "${RESTORE_TARGET_ENV:-}" == "test" ]] || { echo "FAIL: rehearsal requires RESTORE_TARGET_ENV=test." >&2; exit 1; }
[[ "${ALLOW_DESTRUCTIVE_TEST_RESTORE:-false}" == "true" ]] || { echo "FAIL: rehearsal requires ALLOW_DESTRUCTIVE_TEST_RESTORE=true." >&2; exit 1; }
[[ "$RESTORE_MONGO_NOFILE_SOFT" =~ ^[1-9][0-9]*$ ]] || { echo "FAIL: RESTORE_MONGO_NOFILE_SOFT must be a positive integer." >&2; exit 1; }
[[ "$RESTORE_MONGO_NOFILE_HARD" =~ ^[1-9][0-9]*$ ]] || { echo "FAIL: RESTORE_MONGO_NOFILE_HARD must be a positive integer." >&2; exit 1; }
(( RESTORE_MONGO_NOFILE_SOFT >= MINIMUM_RESTORE_MONGO_NOFILE )) || { echo "FAIL: disposable MongoDB soft nofile limit must be at least $MINIMUM_RESTORE_MONGO_NOFILE." >&2; exit 1; }
(( RESTORE_MONGO_NOFILE_HARD >= RESTORE_MONGO_NOFILE_SOFT )) || { echo "FAIL: disposable MongoDB hard nofile limit must be greater than or equal to the soft limit." >&2; exit 1; }

cd "$APP_DIR"
python3 "$SCRIPT_DIR/mongodb_backup_manifest.py" verify --archive "$ARCHIVE_PATH" >/dev/null
SOURCE_DATABASE="$(ARCHIVE_PATH="$ARCHIVE_PATH" python3 - <<'PY'
import json
import os
from pathlib import Path

archive = Path(os.environ["ARCHIVE_PATH"])
manifest = archive.with_name(archive.name.removesuffix(".archive.gz") + ".manifest.json")
payload = json.loads(manifest.read_text(encoding="utf-8"))
print(payload["database_name"])
PY
)"
EXPECTED_COUNTS="$(ARCHIVE_PATH="$ARCHIVE_PATH" python3 - <<'PY'
import json
import os
from pathlib import Path

archive = Path(os.environ["ARCHIVE_PATH"])
manifest = archive.with_name(archive.name.removesuffix(".archive.gz") + ".manifest.json")
payload = json.loads(manifest.read_text(encoding="utf-8"))
print(json.dumps(payload.get("collection_counts") or {}, sort_keys=True))
PY
)"
PRODUCTION_DATABASE="${MONGO_DATABASE:-${MONGODB_DATABASE:-aeroassist_agencyos}}"

[[ "$TARGET_DATABASE" != "$PRODUCTION_DATABASE" ]] || { echo "FAIL: disposable rehearsal refuses the configured production database name." >&2; exit 1; }
[[ "$TARGET_DATABASE" != "$SOURCE_DATABASE" ]] || { echo "FAIL: disposable rehearsal target must differ from the source database." >&2; exit 1; }
[[ "$TARGET_DATABASE" =~ ^[A-Za-z0-9_-]+$ ]] || { echo "FAIL: target database contains unsafe characters." >&2; exit 1; }

cleanup() {
  if [[ "$PRESERVE_DISPOSABLE_RESTORE" == "true" ]]; then
    echo "WARN: disposable restore resources preserved by explicit request: $CONTAINER_NAME"
    return
  fi
  docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

ROOT_USERNAME="restore_rehearsal_admin"
ROOT_PASSWORD="$(openssl rand -hex 24)"
docker volume create "$VOLUME_NAME" >/dev/null
docker run --detach --name "$CONTAINER_NAME" \
  --ulimit "nofile=${RESTORE_MONGO_NOFILE_SOFT}:${RESTORE_MONGO_NOFILE_HARD}" \
  --volume "$VOLUME_NAME:/data/db" \
  --env MONGO_INITDB_ROOT_USERNAME="$ROOT_USERNAME" \
  --env MONGO_INITDB_ROOT_PASSWORD="$ROOT_PASSWORD" \
  "$MONGO_IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER_NAME" sh -eu -c 'mongosh --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand(\"ping\").ok"' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec "$CONTAINER_NAME" sh -eu -c 'mongosh --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand(\"ping\").ok"' >/dev/null

APPLIED_NOFILE_SOFT="$(docker exec "$CONTAINER_NAME" sh -eu -c 'ulimit -Sn')"
APPLIED_NOFILE_HARD="$(docker exec "$CONTAINER_NAME" sh -eu -c 'ulimit -Hn')"
[[ "$APPLIED_NOFILE_SOFT" =~ ^[0-9]+$ && "$APPLIED_NOFILE_HARD" =~ ^[0-9]+$ ]] || { echo "FAIL: disposable MongoDB nofile limits could not be verified." >&2; exit 1; }
(( APPLIED_NOFILE_SOFT >= RESTORE_MONGO_NOFILE_SOFT )) || { echo "FAIL: disposable MongoDB soft nofile limit was not applied." >&2; exit 1; }
(( APPLIED_NOFILE_HARD >= RESTORE_MONGO_NOFILE_HARD )) || { echo "FAIL: disposable MongoDB hard nofile limit was not applied." >&2; exit 1; }
echo "PASS: disposable MongoDB nofile limits verified (${APPLIED_NOFILE_SOFT}:${APPLIED_NOFILE_HARD})."

docker exec -i -e RESTORE_SOURCE_DATABASE="$SOURCE_DATABASE" -e RESTORE_TARGET_DATABASE="$TARGET_DATABASE" \
  "$CONTAINER_NAME" sh -eu -c '
    exec mongorestore --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip --drop --stopOnError --nsFrom "$RESTORE_SOURCE_DATABASE.*" --nsTo "$RESTORE_TARGET_DATABASE.*"
  ' < "$ARCHIVE_PATH"

RESTORED_COUNTS="$(docker exec -e RESTORE_TARGET_DATABASE="$TARGET_DATABASE" "$CONTAINER_NAME" sh -eu -c '
  script="const target=db.getSiblingDB(process.env.RESTORE_TARGET_DATABASE); const names=target.getCollectionNames().sort(); print(JSON.stringify(Object.fromEntries(names.map(name => [name, target.getCollection(name).countDocuments({})]))));"
  exec mongosh --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "$script"
')"
EXPECTED_COUNTS="$EXPECTED_COUNTS" RESTORED_COUNTS="$RESTORED_COUNTS" python3 - <<'PY'
import json
import os

expected = json.loads(os.environ["EXPECTED_COUNTS"])
restored = json.loads(os.environ["RESTORED_COUNTS"])
if expected != restored:
    raise SystemExit(f"FAIL: restored collection counts differ: expected={expected} restored={restored}")
print(f"PASS: restored {len(restored)} collections and {sum(restored.values())} documents into a disposable database.")
PY

python3 "$SCRIPT_DIR/mongodb_backup_manifest.py" mark --archive "$ARCHIVE_PATH" --status restore_rehearsed >/dev/null
echo "PASS: disposable restore rehearsal completed; source data was not modified."
