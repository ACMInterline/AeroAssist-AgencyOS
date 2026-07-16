#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
SKIP_BACKUP_DIR_CHECK="${SKIP_BACKUP_DIR_CHECK:-false}"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

pass() {
  echo "PASS: $1"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is not installed or not on PATH."
  pass "$1 is available."
}

cd "$APP_DIR" || fail "APP_DIR does not exist: $APP_DIR"

[[ -f "$ENV_FILE" ]] || fail "$ENV_FILE is missing. Copy .env.production.example and set real production values."
[[ -f "$COMPOSE_FILE" ]] || fail "$COMPOSE_FILE is missing."
[[ -d backend && -d frontend && -d deploy/hostinger ]] || fail "APP_DIR does not look like the AeroAssist repository root."
pass "repository layout looks correct."

require_command git
require_command docker
docker compose version >/dev/null 2>&1 || fail "docker compose plugin is not available."
pass "docker compose is available."

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required_env=(
  APP_ENV
  AEROASSIST_DB_MODE
  MONGO_AUTHENTICATION_ENABLED
  MONGO_INITDB_ROOT_USERNAME
  MONGO_INITDB_ROOT_PASSWORD
  MONGO_APP_USERNAME
  MONGO_APP_PASSWORD
  MONGO_AUTH_SOURCE
  MONGO_DATABASE
  MONGODB_DATABASE
  BACKUP_RETENTION_DAYS
  BACKUP_MINIMUM_COUNT
  BACKUP_ENVIRONMENT_LABEL
  DEMO_AUTH_ENABLED
  SEED_ON_STARTUP
  SEED_ENDPOINT_ENABLED
  AUTH_TOKEN_SECRET
  DOCUMENT_EXPORT_STORAGE_DIR
  CORS_ALLOWED_ORIGINS
  FRONTEND_URL
  PUBLIC_APP_URL
  FRONTEND_HTTP_PORT
)

for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    fail "$name is required in $ENV_FILE."
  fi
done
pass "required production environment variables are present."

[[ "${APP_ENV}" == "production" ]] || fail "APP_ENV must be production."
[[ "${AEROASSIST_DB_MODE}" == "mongo" ]] || fail "AEROASSIST_DB_MODE must be mongo."
[[ "${MONGO_AUTHENTICATION_ENABLED}" == "true" ]] || fail "MONGO_AUTHENTICATION_ENABLED must be true after completing the existing-volume migration runbook."
[[ "${DEMO_AUTH_ENABLED}" == "false" ]] || fail "DEMO_AUTH_ENABLED must be false."
[[ "${SEED_ON_STARTUP}" == "false" ]] || fail "SEED_ON_STARTUP must be false."
[[ "${SEED_ENDPOINT_ENABLED}" == "false" ]] || fail "SEED_ENDPOINT_ENABLED must be false."
[[ "${AUTH_TOKEN_SECRET}" != "replace-with-a-long-random-production-secret" ]] || fail "AUTH_TOKEN_SECRET still uses the example placeholder."
[[ "${AUTH_TOKEN_SECRET}" != "replace-with-a-long-random-secret" ]] || fail "AUTH_TOKEN_SECRET still uses a placeholder."
[[ "${MONGO_INITDB_ROOT_PASSWORD}" != replace-with-* && ${#MONGO_INITDB_ROOT_PASSWORD} -ge 16 ]] || fail "MongoDB root password is a placeholder or too short."
[[ "${MONGO_APP_PASSWORD}" != replace-with-* && ${#MONGO_APP_PASSWORD} -ge 16 ]] || fail "MongoDB application password is a placeholder or too short."
[[ "${BACKUP_RETENTION_DAYS}" =~ ^[0-9]+$ && "${BACKUP_RETENTION_DAYS}" -ge 1 ]] || fail "BACKUP_RETENTION_DAYS must be at least 1."
[[ "${BACKUP_MINIMUM_COUNT}" =~ ^[0-9]+$ && "${BACKUP_MINIMUM_COUNT}" -ge 1 ]] || fail "BACKUP_MINIMUM_COUNT must be at least 1."
[[ "${CORS_ALLOWED_ORIGINS}" != *"*"* ]] || fail "CORS_ALLOWED_ORIGINS must not include wildcard '*'."
[[ "${CORS_ALLOWED_ORIGINS}" != *"localhost"* && "${CORS_ALLOWED_ORIGINS}" != *"127.0.0.1"* ]] || fail "CORS_ALLOWED_ORIGINS must not use local development origins in production."
pass "production safety environment checks passed."

if [[ "$SKIP_BACKUP_DIR_CHECK" != "true" ]]; then
  mkdir -p "$BACKUP_ROOT"
  [[ -w "$BACKUP_ROOT" ]] || fail "BACKUP_ROOT is not writable: $BACKUP_ROOT"
  pass "backup root is writable."
fi

AEROASSIST_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --quiet
pass "docker compose config is valid."

if docker info >/dev/null 2>&1; then
  pass "Docker daemon is reachable."
else
  fail "Docker daemon is not reachable. Start Docker before deploy."
fi

echo "PASS: preflight completed without printing secret values."
