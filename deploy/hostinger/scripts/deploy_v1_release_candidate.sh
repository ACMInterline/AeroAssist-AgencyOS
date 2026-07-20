#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
APP_BASE_URL="${APP_BASE_URL:-https://avio.my}"
CANONICAL_WWW_URL="${CANONICAL_WWW_URL:-https://www.avio.my}"
RELEASE_COMMIT="4c2bfccc0fae8af47b0e7196a92d4000bc14791d"
RELEASE_SHORT="4c2bfccc"
TIMESTAMP="${TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
DEPLOYMENT_ID="v1-${RELEASE_SHORT}-${TIMESTAMP}"

ROLLBACK_COMMIT=""
ORIGINAL_APP_GIT_COMMIT=""
ORIGINAL_APP_DEPLOYMENT_ID=""
ORIGINAL_APP_GIT_COMMIT_PRESENT=false
ORIGINAL_APP_DEPLOYMENT_ID_PRESENT=false
ROLLBACK_ARMED=false
ROLLBACK_ACTIVE=false
TEMP_RELEASE_TOOLS_DIR=""

fail() {
  echo "FAIL: $1" >&2
  return 1
}

compose() {
  AEROASSIST_ENV_FILE="$ENV_FILE" \
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

read_env_value() {
  local key="$1"
  local line
  line="$(grep -m1 -E "^${key}=" "$ENV_FILE" 2>/dev/null || true)"
  printf '%s' "${line#*=}"
}

env_key_present() {
  grep -q -E "^$1=" "$ENV_FILE"
}

set_env_value() {
  local key="$1"
  local value="$2"
  if env_key_present "$key"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
  chmod 600 "$ENV_FILE"
}

remove_env_key() {
  local key="$1"
  sed -i "/^${key}=/d" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
}

restore_release_environment() {
  if [[ "$ORIGINAL_APP_GIT_COMMIT_PRESENT" == true ]]; then
    set_env_value APP_GIT_COMMIT "$ORIGINAL_APP_GIT_COMMIT"
  else
    remove_env_key APP_GIT_COMMIT
  fi

  if [[ "$ORIGINAL_APP_DEPLOYMENT_ID_PRESENT" == true ]]; then
    set_env_value APP_DEPLOYMENT_ID "$ORIGINAL_APP_DEPLOYMENT_ID"
  else
    remove_env_key APP_DEPLOYMENT_ID
  fi
}

wait_for_healthy() {
  local service="$1"
  local attempts="${2:-90}"
  local container_id=""
  local state=""
  local health=""

  for ((attempt = 1; attempt <= attempts; attempt += 1)); do
    container_id="$(compose ps -q "$service" 2>/dev/null || true)"
    if [[ -n "$container_id" ]]; then
      state="$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)"
      health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id" 2>/dev/null || true)"
      if [[ "$state" == running && "$health" == healthy ]]; then
        echo "PASS: $service is running and healthy."
        return 0
      fi
    fi
    sleep 2
  done

  fail "$service did not become healthy."
}

validate_application() {
  wait_for_healthy mongo
  wait_for_healthy backend
  wait_for_healthy frontend

  compose exec -T backend python scripts/check_production_readiness.py

  APP_BASE_URL="$APP_BASE_URL" \
    deploy/hostinger/scripts/smoke_production.sh

  APP_DIR="$APP_DIR" \
  ENV_FILE="$ENV_FILE" \
  COMPOSE_FILE="$COMPOSE_FILE" \
  APP_BASE_URL="$APP_BASE_URL" \
  CANONICAL_WWW_URL="$CANONICAL_WWW_URL" \
    deploy/hostinger/scripts/healthcheck.sh
}

rollback_application() {
  local original_status="$1"
  local rollback_status=0

  ROLLBACK_ACTIVE=true
  trap - ERR
  set +e

  echo "FAIL: release deployment failed; starting application-only rollback." >&2
  echo "Rollback commit: $ROLLBACK_COMMIT" >&2

  git switch --detach "$ROLLBACK_COMMIT" || rollback_status=1
  restore_release_environment || rollback_status=1

  if [[ "$rollback_status" -eq 0 ]]; then
    compose config --quiet || rollback_status=1
    compose build backend frontend || rollback_status=1
    compose up -d --no-deps backend frontend || rollback_status=1
  fi

  if [[ "$rollback_status" -eq 0 ]]; then
    wait_for_healthy mongo || rollback_status=1
    wait_for_healthy backend || rollback_status=1
    wait_for_healthy frontend || rollback_status=1
  fi

  if [[ "$rollback_status" -eq 0 ]]; then
    compose exec -T backend python scripts/check_production_readiness.py || rollback_status=1
    APP_BASE_URL="$APP_BASE_URL" deploy/hostinger/scripts/smoke_production.sh || rollback_status=1
  fi

  if [[ "$rollback_status" -eq 0 ]]; then
    echo "ROLLBACK_COMPLETE: application restored to $ROLLBACK_COMMIT" >&2
  else
    echo "ROLLBACK_FAILED: manual operator intervention is required." >&2
  fi

  exit "$original_status"
}

on_error() {
  local status="$?"
  if [[ "$ROLLBACK_ARMED" == true && "$ROLLBACK_ACTIVE" == false ]]; then
    rollback_application "$status"
  fi
  exit "$status"
}
trap on_error ERR

cleanup_temp_release_tools() {
  if [[ -n "$TEMP_RELEASE_TOOLS_DIR" && -d "$TEMP_RELEASE_TOOLS_DIR" ]]; then
    find "$TEMP_RELEASE_TOOLS_DIR" -depth -delete 2>/dev/null || true
  fi
}
trap cleanup_temp_release_tools EXIT

cd "$APP_DIR"
export AEROASSIST_ENV_FILE="$ENV_FILE"

[[ -f "$ENV_FILE" ]] || fail "$ENV_FILE is missing."
[[ -f "$COMPOSE_FILE" ]] || fail "$COMPOSE_FILE is missing."
[[ -z "$(git status --porcelain)" ]] || fail "Production worktree is not clean."
[[ "$TIMESTAMP" =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || fail "TIMESTAMP must use YYYYMMDDTHHMMSSZ format."

ROLLBACK_COMMIT="$(git rev-parse --verify HEAD)"
[[ "$ROLLBACK_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail "Rollback commit is invalid."
[[ "$ROLLBACK_COMMIT" != "$RELEASE_COMMIT" ]] || fail "Release commit is already deployed."

CURRENT_DEPLOYED_COMMIT="$(compose exec -T backend printenv APP_GIT_COMMIT | tr -d '\r\n')"
[[ "$CURRENT_DEPLOYED_COMMIT" =~ ^[0-9a-f]{8,40}$ ]] || fail "Running backend commit is missing or invalid."
[[ "$CURRENT_DEPLOYED_COMMIT" == "$ROLLBACK_COMMIT" \
   || "${ROLLBACK_COMMIT:0:${#CURRENT_DEPLOYED_COMMIT}}" == "$CURRENT_DEPLOYED_COMMIT" ]] \
  || fail "Repository HEAD does not match the running backend commit."

git fetch --no-tags origin main
git cat-file -e "$RELEASE_COMMIT^{commit}"
[[ "$(git rev-parse "$RELEASE_COMMIT^{commit}")" == "$RELEASE_COMMIT" ]] \
  || fail "Approved release commit is unavailable."
[[ "$(git rev-parse HEAD)" == "$ROLLBACK_COMMIT" ]] \
  || fail "Production worktree changed while fetching the release commit."

TEMP_RELEASE_TOOLS_DIR="$(mktemp -d /tmp/aeroassist-release-backup-tools.XXXXXX)"
for release_tool in verify_backups.sh verify_mongodb_backup.sh mongodb_backup_manifest.py; do
  git show "$RELEASE_COMMIT:deploy/hostinger/scripts/$release_tool" \
    > "$TEMP_RELEASE_TOOLS_DIR/$release_tool"
done
chmod 700 \
  "$TEMP_RELEASE_TOOLS_DIR/verify_backups.sh" \
  "$TEMP_RELEASE_TOOLS_DIR/verify_mongodb_backup.sh" \
  "$TEMP_RELEASE_TOOLS_DIR/mongodb_backup_manifest.py"
bash -n "$TEMP_RELEASE_TOOLS_DIR/verify_backups.sh"
bash -n "$TEMP_RELEASE_TOOLS_DIR/verify_mongodb_backup.sh"

if env_key_present APP_GIT_COMMIT; then
  ORIGINAL_APP_GIT_COMMIT_PRESENT=true
  ORIGINAL_APP_GIT_COMMIT="$(read_env_value APP_GIT_COMMIT)"
fi
if env_key_present APP_DEPLOYMENT_ID; then
  ORIGINAL_APP_DEPLOYMENT_ID_PRESENT=true
  ORIGINAL_APP_DEPLOYMENT_ID="$(read_env_value APP_DEPLOYMENT_ID)"
fi

APP_DIR="$APP_DIR" \
ENV_FILE="$ENV_FILE" \
COMPOSE_FILE="$COMPOSE_FILE" \
BACKUP_ROOT="$BACKUP_ROOT" \
  deploy/hostinger/scripts/preflight.sh

echo "Creating verified pre-deployment backup: $TIMESTAMP"
APP_DIR="$APP_DIR" \
ENV_FILE="$ENV_FILE" \
COMPOSE_FILE="$COMPOSE_FILE" \
BACKUP_ROOT="$BACKUP_ROOT" \
TIMESTAMP="$TIMESTAMP" \
  deploy/hostinger/scripts/backup_all.sh

APP_DIR="$APP_DIR" \
ENV_FILE="$ENV_FILE" \
COMPOSE_FILE="$COMPOSE_FILE" \
BACKUP_ROOT="$BACKUP_ROOT" \
  "$TEMP_RELEASE_TOOLS_DIR/verify_backups.sh"

BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
[[ -s "$BACKUP_DIR/mongodb-$TIMESTAMP.archive.gz" ]] || fail "MongoDB backup archive is missing."
[[ -s "$BACKUP_DIR/mongodb-$TIMESTAMP.archive.gz.sha256" ]] || fail "MongoDB backup checksum is missing."
[[ -s "$BACKUP_DIR/mongodb-$TIMESTAMP.manifest.json" ]] || fail "MongoDB backup manifest is missing."
[[ -s "$BACKUP_DIR/document_exports.tar.gz" ]] || fail "Document export backup is missing."
[[ -s "$BACKUP_DIR/document_exports.tar.gz.sha256" ]] || fail "Document export checksum is missing."
printf '%s\n' "$ROLLBACK_COMMIT" > "$BACKUP_DIR/rollback-commit.txt"
chmod 600 "$BACKUP_DIR/rollback-commit.txt"

[[ "$(git rev-parse HEAD)" == "$ROLLBACK_COMMIT" ]] \
  || fail "Production worktree changed before backup validation completed."

ROLLBACK_ARMED=true
git switch --detach "$RELEASE_COMMIT"
[[ "$(git rev-parse HEAD)" == "$RELEASE_COMMIT" ]] || fail "Failed to select the approved release commit."

set_env_value APP_GIT_COMMIT "$RELEASE_SHORT"
set_env_value APP_DEPLOYMENT_ID "$DEPLOYMENT_ID"

compose config --quiet
compose build backend frontend
compose up -d --no-deps backend frontend
compose ps

DEPLOYED_COMMIT="$(compose exec -T backend printenv APP_GIT_COMMIT | tr -d '\r\n')"
[[ "$DEPLOYED_COMMIT" == "$RELEASE_SHORT" || "$DEPLOYED_COMMIT" == "$RELEASE_COMMIT" ]] \
  || fail "Backend container does not report the approved release commit."

validate_application

ROLLBACK_ARMED=false
trap - ERR
echo "DEPLOYMENT_COMPLETE: $RELEASE_COMMIT"
