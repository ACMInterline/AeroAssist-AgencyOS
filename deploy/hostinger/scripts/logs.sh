#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
SERVICE="${SERVICE:-}"
LINES="${LINES:-200}"

cd "$APP_DIR"
if [[ -n "$SERVICE" ]]; then
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" logs --tail "$LINES" -f "$SERVICE"
else
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" logs --tail "$LINES" -f
fi
