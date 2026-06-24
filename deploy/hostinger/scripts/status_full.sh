#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
APP_BASE_URL="${APP_BASE_URL:-https://avio.my}"
CANONICAL_WWW_URL="${CANONICAL_WWW_URL:-https://www.avio.my}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
OLD_APP_DIR="${OLD_APP_DIR:-/opt/aeroassist}"

section() {
  echo
  echo "== $* =="
}

latest_backup() {
  local artifact="$1"
  find "$BACKUP_ROOT" -mindepth 2 -maxdepth 2 -type f -name "$artifact" \
    -path "$BACKUP_ROOT/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T[0-9][0-9][0-9][0-9][0-9][0-9]Z/$artifact" \
    2>/dev/null | sort | tail -n 1
}

cd "$APP_DIR"

section "Git"
git rev-parse --short HEAD 2>/dev/null || echo "unknown"

section "App Health"
health_body="$(curl -fsS "$APP_BASE_URL/api/health" 2>/dev/null || true)"
if [[ -n "$health_body" ]]; then
  echo "$health_body"
else
  echo "Health unavailable from $APP_BASE_URL/api/health"
fi

section "Containers"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

section "nginx"
if command -v systemctl >/dev/null 2>&1; then
  systemctl is-active nginx || true
else
  echo "systemctl unavailable"
fi

section "certbot.timer"
if command -v systemctl >/dev/null 2>&1; then
  systemctl is-active certbot.timer || true
  systemctl list-timers certbot.timer --no-pager 2>/dev/null || true
else
  echo "systemctl unavailable"
fi

section "Disk"
df -h / "$BACKUP_ROOT" 2>/dev/null || df -h /

section "Latest Backups"
mongo_backup="$(latest_backup "mongo.archive.gz")"
export_backup="$(latest_backup "document_exports.tar.gz")"
echo "MongoDB: ${mongo_backup:-missing}"
echo "Document exports: ${export_backup:-missing}"

section "Domain Redirects"
curl -sS -o /dev/null -w "$APP_BASE_URL -> HTTP %{http_code}\n" "$APP_BASE_URL" 2>/dev/null || echo "$APP_BASE_URL -> unavailable"
curl -sS -o /dev/null -w "$CANONICAL_WWW_URL -> HTTP %{http_code} %{redirect_url}\n" "$CANONICAL_WWW_URL" 2>/dev/null || echo "$CANONICAL_WWW_URL -> unavailable"

section "Old App"
if [[ -d "$OLD_APP_DIR" ]]; then
  running="$(docker ps --filter "label=com.docker.compose.project.working_dir=$OLD_APP_DIR" -q 2>/dev/null || true)"
  if [[ -n "$running" ]]; then
    echo "old app path exists; old Compose containers are running"
  else
    echo "old app path exists; old Compose containers are stopped"
  fi
else
  echo "old app path absent"
fi
