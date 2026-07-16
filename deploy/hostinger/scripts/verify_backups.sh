#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
MAX_MONGO_AGE_HOURS="${MAX_MONGO_AGE_HOURS:-30}"
MAX_EXPORT_AGE_HOURS="${MAX_EXPORT_AGE_HOURS:-30}"
NOW_EPOCH="$(date -u +%s)"
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

timestamp_epoch() {
  local stamp="$1"
  local iso="${stamp:0:4}-${stamp:4:2}-${stamp:6:2} ${stamp:9:2}:${stamp:11:2}:${stamp:13:2} UTC"
  date -u -d "$iso" +%s 2>/dev/null
}

latest_for() {
  local artifact="$1"
  find "$BACKUP_ROOT" -mindepth 2 -maxdepth 2 -type f -name "$artifact" \
    -path "$BACKUP_ROOT/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]T[0-9][0-9][0-9][0-9][0-9][0-9]Z/$artifact" \
    2>/dev/null | sort | tail -n 1
}

verify_checksum() {
  local artifact="$1"
  local checksum="$artifact.sha256"

  if [[ ! -s "$artifact" ]]; then
    return 1
  fi

  if [[ ! -s "$checksum" ]]; then
    return 1
  fi

  (cd "$(dirname "$artifact")" && sha256sum -c "$(basename "$checksum")" >/dev/null)
}

age_hours() {
  local artifact="$1"
  local stamp
  local epoch
  stamp="$(basename "$(dirname "$artifact")")"
  epoch="$(timestamp_epoch "$stamp")"
  if [[ -z "$epoch" ]]; then
    echo "unknown"
    return 1
  fi
  echo $(( (NOW_EPOCH - epoch) / 3600 ))
}

if [[ ! -d "$BACKUP_ROOT" ]]; then
  fail "backup root is missing: $BACKUP_ROOT"
  exit "$STATUS"
fi

mongo_backup="$(find "$BACKUP_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'mongodb-*.archive.gz' 2>/dev/null | sort | tail -n 1)"
if [[ -z "$mongo_backup" ]]; then
  fail "latest MongoDB backup is missing."
else
  mongo_age="$(age_hours "$mongo_backup" || true)"
  echo "Latest MongoDB backup: $mongo_backup"
  echo "MongoDB backup age: ${mongo_age}h"
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if APP_DIR="${APP_DIR:-/opt/aeroassist-agencyos}" ENV_FILE="${ENV_FILE:-.env.production}" \
    COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}" "$script_dir/verify_mongodb_backup.sh" "$mongo_backup"; then
    pass "latest MongoDB backup checksum, manifest, and archive inspection verified."
  else
    fail "latest MongoDB backup verification failed."
  fi
  if [[ "$mongo_age" == "unknown" || "$mongo_age" -gt "$MAX_MONGO_AGE_HOURS" ]]; then
    fail "latest MongoDB backup is older than ${MAX_MONGO_AGE_HOURS}h."
  fi
fi

export_backup="$(latest_for "document_exports.tar.gz")"
if [[ -z "$export_backup" ]]; then
  warn "document export backup is missing."
else
  export_age="$(age_hours "$export_backup" || true)"
  echo "Latest document export backup: $export_backup"
  echo "Document export backup age: ${export_age}h"
  if verify_checksum "$export_backup"; then
    pass "latest document export backup checksum verified."
  else
    fail "document export backup exists but checksum verification failed."
  fi
  if [[ "$export_age" == "unknown" || "$export_age" -gt "$MAX_EXPORT_AGE_HOURS" ]]; then
    warn "latest document export backup is older than ${MAX_EXPORT_AGE_HOURS}h."
  fi
fi

exit "$STATUS"
