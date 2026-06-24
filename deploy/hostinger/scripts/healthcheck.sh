#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
APP_BASE_URL="${APP_BASE_URL:-https://avio.my}"
CANONICAL_WWW_URL="${CANONICAL_WWW_URL:-https://www.avio.my}"
OLD_APP_DIR="${OLD_APP_DIR:-/opt/aeroassist}"
STATUS=0

pass() {
  echo "PASS: $*"
}

warn() {
  echo "WARN: $*"
}

fail() {
  echo "FAIL: $*"
  STATUS=1
}

check_systemd_active() {
  local unit="$1"
  local label="$2"

  if ! command -v systemctl >/dev/null 2>&1; then
    fail "systemctl is unavailable; cannot check $label."
    return
  fi

  if systemctl is-active --quiet "$unit"; then
    pass "$label is active."
  else
    fail "$label is not active."
  fi
}

check_compose_service() {
  local service="$1"
  local container_id
  local state
  local health

  container_id="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null || true)"
  if [[ -z "$container_id" ]]; then
    fail "Compose service $service has no container."
    return
  fi

  state="$(docker inspect -f '{{.State.Status}}' "$container_id" 2>/dev/null || true)"
  health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id" 2>/dev/null || true)"

  if [[ "$state" != "running" ]]; then
    fail "Compose service $service is $state."
  elif [[ "$health" == "healthy" ]]; then
    pass "Compose service $service is running and healthy."
  elif [[ "$health" == "none" ]]; then
    warn "Compose service $service is running without a Docker healthcheck."
  else
    fail "Compose service $service health is $health."
  fi
}

check_url_ok() {
  local url="$1"
  local label="$2"
  local code

  code="$(curl -fsS -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true)"
  if [[ "$code" == "200" ]]; then
    pass "$label responds 200."
  else
    fail "$label returned HTTP ${code:-unreachable}."
  fi
}

check_json_ok() {
  local url="$1"
  local label="$2"
  local body

  body="$(curl -fsS "$url" 2>/dev/null || true)"
  if echo "$body" | grep -q '"ok"[[:space:]]*:[[:space:]]*true'; then
    pass "$label reports ok=true."
  else
    fail "$label did not report ok=true."
  fi
}

check_redirect() {
  local code
  local redirect_url
  local result

  result="$(curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' "$CANONICAL_WWW_URL" 2>/dev/null || true)"
  code="${result%% *}"
  redirect_url="${result#* }"

  if [[ "$code" =~ ^30[1278]$ && "$redirect_url" =~ ^https://avio\.my/?$ ]]; then
    pass "$CANONICAL_WWW_URL redirects to https://avio.my."
  else
    fail "$CANONICAL_WWW_URL redirect mismatch: HTTP ${code:-unreachable} -> ${redirect_url:-none}."
  fi
}

check_frontend_binding() {
  local binding

  binding="$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" port frontend 80 2>/dev/null || true)"
  if [[ "$binding" == "127.0.0.1:8080" ]]; then
    pass "frontend is bound local-only on 127.0.0.1:8080."
  elif [[ -z "$binding" ]]; then
    fail "frontend port binding could not be determined."
  else
    fail "frontend port binding is $binding; expected 127.0.0.1:8080."
  fi
}

check_port_owner() {
  local port="$1"
  local line

  if ! command -v ss >/dev/null 2>&1; then
    fail "ss is unavailable; cannot check port $port owner."
    return
  fi

  line="$(ss -H -ltnp "sport = :$port" 2>/dev/null || true)"
  if [[ "$line" == *nginx* ]]; then
    pass "public port $port is owned by nginx."
  else
    fail "public port $port is not owned by nginx."
  fi
}

check_old_app() {
  local running

  if [[ ! -d "$OLD_APP_DIR" ]]; then
    pass "old app path is absent."
    return
  fi

  running="$(docker ps --filter "label=com.docker.compose.project.working_dir=$OLD_APP_DIR" -q 2>/dev/null || true)"
  if [[ -z "$running" ]]; then
    pass "old app path exists and no old app Compose containers are running."
  else
    fail "old app path exists but old app Compose containers are running."
  fi
}

check_systemd_active docker "Docker service"
check_systemd_active nginx "nginx service"
check_systemd_active certbot.timer "certbot.timer"

cd "$APP_DIR"
check_compose_service mongo
check_compose_service backend
check_compose_service frontend
check_url_ok "$APP_BASE_URL" "$APP_BASE_URL"
check_redirect
check_json_ok "$APP_BASE_URL/api/health" "/api/health"
check_json_ok "$APP_BASE_URL/api/readiness" "/api/readiness"
check_frontend_binding
check_port_owner 80
check_port_owner 443
check_old_app

exit "$STATUS"
