#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
TIMESTAMP="${TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[[ "$TIMESTAMP" =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || { echo "FAIL: TIMESTAMP must use YYYYMMDDTHHMMSSZ format." >&2; exit 1; }

verify_artifact() {
  local artifact="$1"
  local checksum="$artifact.sha256"

  if [[ ! -s "$artifact" ]]; then
    echo "FAIL: missing or empty backup artifact: $artifact"
    return 1
  fi

  if [[ ! -s "$checksum" ]]; then
    echo "FAIL: missing checksum file: $checksum"
    return 1
  fi

  (cd "$(dirname "$artifact")" && sha256sum -c "$(basename "$checksum")" >/dev/null)
}

mkdir -p "$BACKUP_ROOT"
chmod 700 "$BACKUP_ROOT"

echo "Starting combined backup."
echo "Backup directory: $BACKUP_DIR"

APP_DIR="$APP_DIR" BACKUP_ROOT="$BACKUP_ROOT" TIMESTAMP="$TIMESTAMP" "$SCRIPT_DIR/backup_mongo.sh"
APP_DIR="$APP_DIR" BACKUP_ROOT="$BACKUP_ROOT" TIMESTAMP="$TIMESTAMP" "$SCRIPT_DIR/backup_exports.sh"

mongo_archive="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'mongodb-*.archive.gz' | sort | tail -n 1)"
[[ -n "$mongo_archive" ]] || { echo "FAIL: timestamped MongoDB archive is missing." >&2; exit 1; }
verify_artifact "$mongo_archive"
verify_artifact "$BACKUP_DIR/document_exports.tar.gz"
APP_DIR="$APP_DIR" ENV_FILE="${ENV_FILE:-.env.production}" COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}" \
  "$SCRIPT_DIR/verify_mongodb_backup.sh" "$mongo_archive"

if [[ "${BACKUP_PRUNE_AFTER_SUCCESS:-false}" == "true" ]]; then
  BACKUP_ROOT="$BACKUP_ROOT" BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}" \
    BACKUP_MINIMUM_COUNT="${BACKUP_MINIMUM_COUNT:-7}" "$SCRIPT_DIR/prune_backups.sh" --apply
fi

echo "PASS: combined backup complete."
echo "MongoDB backup: present and checksum verified."
echo "Document export backup: present and checksum verified."
