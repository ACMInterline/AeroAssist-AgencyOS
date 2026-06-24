#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
EXPORT_DIR="${EXPORT_DIR:-/var/lib/aeroassist/document_exports}"
export EXPORT_DIR

cd "$APP_DIR"

if ! docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps -q backend >/dev/null 2>&1; then
  echo "FAIL: backend container is not available."
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend sh -s <<'EOF'
set -eu
EXPORT_DIR="${EXPORT_DIR:-/var/lib/aeroassist/document_exports}"

if [ ! -d "$EXPORT_DIR" ]; then
  echo "FAIL: document export storage directory is missing."
  exit 1
fi

if [ ! -w "$EXPORT_DIR" ]; then
  echo "FAIL: document export storage directory is not writable."
  exit 1
fi

file_count="$(find "$EXPORT_DIR" -type f | wc -l | tr -d ' ')"
total_bytes="$(du -sb "$EXPORT_DIR" 2>/dev/null | awk '{print $1}')"

echo "PASS: document export storage directory exists and is writable."
echo "Files: ${file_count}"
echo "Bytes: ${total_bytes:-0}"
EOF
