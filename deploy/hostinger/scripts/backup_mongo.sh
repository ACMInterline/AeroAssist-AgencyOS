#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
TIMESTAMP="${TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

cd "$APP_DIR"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_ROOT" "$BACKUP_DIR"

echo "Creating MongoDB backup in $BACKUP_DIR/mongo.archive.gz"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mongo \
  mongodump --archive --gzip > "$BACKUP_DIR/mongo.archive.gz"

sha256sum "$BACKUP_DIR/mongo.archive.gz" > "$BACKUP_DIR/mongo.archive.gz.sha256"
echo "PASS: MongoDB backup complete."
echo "Restore guidance: deploy/hostinger/scripts/restore_mongo.md"
