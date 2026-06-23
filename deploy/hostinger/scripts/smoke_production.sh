#!/usr/bin/env bash
set -euo pipefail

APP_BASE_URL="${APP_BASE_URL:-https://agencyos.example.com}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-15}"

pass() {
  echo "PASS: $1"
}

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

fetch() {
  local path="$1"
  curl --fail --silent --show-error --max-time "$TIMEOUT_SECONDS" "$APP_BASE_URL$path"
}

root_body="$(fetch /)" || fail "frontend root is unavailable"
if [[ -z "$root_body" ]]; then
  fail "frontend root returned an empty body"
fi
pass "frontend root responded"

health_body="$(fetch /api/health)" || fail "/api/health is unavailable"
echo "$health_body" | grep -q '"ok"[[:space:]]*:[[:space:]]*true' || fail "/api/health did not report ok=true"
pass "/api/health reports ok"

readiness_body="$(fetch /api/readiness)" || fail "/api/readiness is unavailable"
echo "$readiness_body" | grep -q '"ok"[[:space:]]*:[[:space:]]*true' || fail "/api/readiness did not report ok=true"
if echo "$readiness_body" | grep -Eiq 'AUTH_TOKEN_SECRET|AEROASSIST_SMTP_PASSWORD|replace-with|not-a-real|secret-value'; then
  fail "/api/readiness output appears to contain secret-like text"
fi
pass "/api/readiness reports ok without obvious secret output"

login_body="$(curl --silent --show-error --max-time "$TIMEOUT_SECONDS" \
  -o /tmp/aeroassist-login-smoke-body \
  -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{"email":"smoke@example.invalid","password":"not-a-real-password"}' \
  "$APP_BASE_URL/api/auth/login")" || fail "/api/auth/login request failed"

case "$login_body" in
  401|403)
    pass "/api/auth/login is reachable and rejects fake credentials"
    ;;
  *)
    cat /tmp/aeroassist-login-smoke-body >&2 || true
    fail "/api/auth/login returned unexpected HTTP $login_body"
    ;;
esac

rm -f /tmp/aeroassist-login-smoke-body
echo "PASS: production smoke completed."
