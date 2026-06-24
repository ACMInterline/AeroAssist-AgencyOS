#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
APPLY=false
NOW_EPOCH="$(date -u +%s)"

usage() {
  cat <<'EOF'
Usage: prune_backups.sh [--apply]

Dry-run is the default. Pass --apply to delete timestamped backup directories
older than the retention window.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --apply)
      APPLY=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "FAIL: unknown argument: $arg"
      usage
      exit 2
      ;;
  esac
done

timestamp_epoch() {
  local stamp="$1"
  local iso="${stamp:0:4}-${stamp:4:2}-${stamp:6:2} ${stamp:9:2}:${stamp:11:2}:${stamp:13:2} UTC"
  date -u -d "$iso" +%s 2>/dev/null
}

if [[ "$BACKUP_ROOT" != "/var/backups/aeroassist" ]]; then
  echo "FAIL: refusing to prune outside /var/backups/aeroassist."
  exit 1
fi

if [[ ! -d "$BACKUP_ROOT" ]]; then
  echo "PASS: backup root does not exist; nothing to prune."
  exit 0
fi

cutoff_seconds=$(( RETENTION_DAYS * 24 * 3600 ))
found=0

echo "Backup prune mode: $([[ "$APPLY" == "true" ]] && echo apply || echo dry-run)"
echo "Retention: ${RETENTION_DAYS} days"

while IFS= read -r backup_dir; do
  stamp="$(basename "$backup_dir")"
  if [[ ! "$stamp" =~ ^[0-9]{8}T[0-9]{6}Z$ ]]; then
    echo "SKIP: non-timestamped directory: $backup_dir"
    continue
  fi

  epoch="$(timestamp_epoch "$stamp")"
  if [[ -z "$epoch" ]]; then
    echo "SKIP: unparseable timestamp directory: $backup_dir"
    continue
  fi

  age_seconds=$(( NOW_EPOCH - epoch ))
  if (( age_seconds > cutoff_seconds )); then
    found=1
    if [[ "$APPLY" == "true" ]]; then
      rm -rf -- "$backup_dir"
      echo "DELETED: $backup_dir"
    else
      echo "WOULD DELETE: $backup_dir"
    fi
  fi
done < <(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d | sort)

if (( found == 0 )); then
  echo "PASS: no timestamped backup directories are older than ${RETENTION_DAYS} days."
elif [[ "$APPLY" != "true" ]]; then
  echo "PASS: dry-run complete; no files were deleted."
else
  echo "PASS: prune complete."
fi
