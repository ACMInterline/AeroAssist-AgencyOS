#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist/AeroAssist-AgencyOS}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
BRANCH="${BRANCH:-main}"
UPDATE_GIT="${UPDATE_GIT:-true}"
RUN_SMOKE="${RUN_SMOKE:-false}"
APP_BASE_URL="${APP_BASE_URL:-}"
RUN_PREFLIGHT="${RUN_PREFLIGHT:-true}"

cd "$APP_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "FAIL: $ENV_FILE is missing. Copy .env.production.example and set production values." >&2
  exit 1
fi

if [[ "$RUN_PREFLIGHT" == "true" ]]; then
  APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
    deploy/hostinger/scripts/preflight.sh
fi

if [[ "$UPDATE_GIT" == "true" ]]; then
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --quiet
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python scripts/check_production_readiness.py

if [[ "$RUN_SMOKE" == "true" ]]; then
  if [[ -z "$APP_BASE_URL" ]]; then
    echo "FAIL: RUN_SMOKE=true requires APP_BASE_URL=https://your-domain.example" >&2
    exit 1
  fi
  APP_BASE_URL="$APP_BASE_URL" deploy/hostinger/scripts/smoke_production.sh
fi

echo "PASS: deployment completed."
