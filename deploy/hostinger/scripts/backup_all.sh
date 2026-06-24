#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
TIMESTAMP="${TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

verify_artifact "$BACKUP_DIR/mongo.archive.gz"
verify_artifact "$BACKUP_DIR/document_exports.tar.gz"

echo "PASS: combined backup complete."
echo "MongoDB backup: present and checksum verified."
echo "Document export backup: present and checksum verified."
