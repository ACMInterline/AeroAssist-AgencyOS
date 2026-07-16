#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
TIMESTAMP="${TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

cd "$APP_DIR"
[[ "$TIMESTAMP" =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || { echo "FAIL: TIMESTAMP must use YYYYMMDDTHHMMSSZ format." >&2; exit 1; }
export AEROASSIST_ENV_FILE="$ENV_FILE"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_ROOT" "$BACKUP_DIR"

echo "Creating document export backup in $BACKUP_DIR/document_exports.tar.gz"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  tar -C /var/lib/aeroassist -czf - document_exports > "$BACKUP_DIR/document_exports.tar.gz"

sha256sum "$BACKUP_DIR/document_exports.tar.gz" > "$BACKUP_DIR/document_exports.tar.gz.sha256"
echo "PASS: document export backup complete."
echo "Restore guidance: deploy/hostinger/scripts/restore_mongo.md"
