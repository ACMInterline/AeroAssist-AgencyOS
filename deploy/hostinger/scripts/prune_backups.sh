#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/aeroassist}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-${RETENTION_DAYS:-30}}"
BACKUP_MINIMUM_COUNT="${BACKUP_MINIMUM_COUNT:-7}"
BACKUP_ALLOW_TEST_ROOT="${BACKUP_ALLOW_TEST_ROOT:-false}"
APPLY=false
NOW_EPOCH="$(date -u +%s)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: prune_backups.sh [--apply]

Dry-run is the default. Only complete, verified MongoDB backup sets older than
the retention window are eligible. The newest verified set and the configured
minimum count are always retained.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "FAIL: unknown argument: $arg" >&2; usage; exit 2 ;;
  esac
done

[[ "$BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ && "$BACKUP_RETENTION_DAYS" -ge 1 ]] || { echo "FAIL: BACKUP_RETENTION_DAYS must be at least 1." >&2; exit 1; }
[[ "$BACKUP_MINIMUM_COUNT" =~ ^[0-9]+$ && "$BACKUP_MINIMUM_COUNT" -ge 1 ]] || { echo "FAIL: BACKUP_MINIMUM_COUNT must be at least 1." >&2; exit 1; }
if [[ "$BACKUP_ROOT" != "/var/backups/aeroassist" && "$BACKUP_ALLOW_TEST_ROOT" != "true" ]]; then
  echo "FAIL: refusing to prune outside /var/backups/aeroassist without BACKUP_ALLOW_TEST_ROOT=true." >&2
  exit 1
fi
if [[ ! -d "$BACKUP_ROOT" ]]; then
  echo "PASS: backup root does not exist; nothing to prune."
  exit 0
fi

verified_manifests=()
while IFS= read -r manifest; do
  archive="$(python3 - "$manifest" <<'PY' 2>/dev/null || true
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
valid_status = payload.get("verification_status") in {"archive_inspected", "restore_rehearsed"}
valid_directory = re.fullmatch(r"\d{8}T\d{6}Z", path.parent.name) is not None
archive = path.parent / str(payload.get("archive_filename") or "")
if valid_status and valid_directory and archive.is_file():
    print(archive)
PY
  )"
  if [[ -n "$archive" ]] && python3 "$SCRIPT_DIR/mongodb_backup_manifest.py" verify --archive "$archive" >/dev/null 2>&1; then
    verified_manifests+=("$manifest")
  else
    echo "SKIP: unverified or incomplete backup set: $(basename "$(dirname "$manifest")")"
  fi
done < <(find "$BACKUP_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'mongodb-*.manifest.json' | sort)

verified_count="${#verified_manifests[@]}"
if (( verified_count == 0 )); then
  echo "PASS: no verified backup sets are eligible for pruning."
  exit 0
fi
newest_manifest="${verified_manifests[$((verified_count - 1))]}"
remaining_count="$verified_count"
eligible_count=0
cutoff_seconds=$(( BACKUP_RETENTION_DAYS * 24 * 3600 ))

echo "Backup prune mode: $([[ "$APPLY" == "true" ]] && echo apply || echo dry-run)"
echo "Retention: ${BACKUP_RETENTION_DAYS} days; minimum verified sets: ${BACKUP_MINIMUM_COUNT}"

for manifest in "${verified_manifests[@]}"; do
  backup_dir="$(dirname "$manifest")"
  stamp="$(basename "$backup_dir")"
  epoch="$(STAMP="$stamp" python3 -c 'import os; from datetime import datetime, timezone; print(int(datetime.strptime(os.environ["STAMP"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp()))' 2>/dev/null || true)"
  [[ -n "$epoch" ]] || { echo "SKIP: unparseable timestamp: $stamp"; continue; }
  age_seconds=$(( NOW_EPOCH - epoch ))
  if [[ "$manifest" == "$newest_manifest" ]]; then
    echo "KEEP: newest verified backup set: $stamp"
    continue
  fi
  if (( remaining_count <= BACKUP_MINIMUM_COUNT )); then
    echo "KEEP: minimum verified count protects: $stamp"
    continue
  fi
  if (( age_seconds <= cutoff_seconds )); then
    continue
  fi
  eligible_count=$((eligible_count + 1))
  archive_name="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["archive_filename"])' "$manifest")"
  if [[ "$APPLY" == "true" ]]; then
    rm -f -- "$backup_dir/$archive_name" "$backup_dir/$archive_name.sha256" "$manifest" \
      "$backup_dir/document_exports.tar.gz" "$backup_dir/document_exports.tar.gz.sha256"
    rmdir "$backup_dir" 2>/dev/null || true
    echo "DELETED VERIFIED SET: $stamp"
    remaining_count=$((remaining_count - 1))
  else
    echo "WOULD DELETE VERIFIED SET: $stamp"
    remaining_count=$((remaining_count - 1))
  fi
done

if (( eligible_count == 0 )); then
  echo "PASS: no verified backup sets are eligible under current retention controls."
elif [[ "$APPLY" == "true" ]]; then
  echo "PASS: verified backup retention applied without deleting the newest or minimum protected sets."
else
  echo "PASS: retention dry-run complete; no files were deleted."
fi
