# Product Recovery Rollback Plan

Rollback is an operator-controlled safety procedure. Application rollback and
data restore are separate decisions.

## Automatic Application Rollback

`deploy_v1_release_candidate.sh` resolves the currently running backend commit
to a full repository SHA before deployment and stores it as
`ROLLBACK_COMMIT`. After backup validation, failures in checkout, Compose,
build, startup, readiness, smoke, or health validation trigger:

1. detached checkout of `ROLLBACK_COMMIT`;
2. restoration of prior release environment metadata;
3. backend/frontend rebuild and restart;
4. container health, production readiness, and production smoke checks.

Success prints `ROLLBACK_COMPLETE`. Failure prints `ROLLBACK_FAILED` and
requires operator intervention.

## Manual Application Rollback

Use only the exact commit recorded in the verified backup directory:

```bash
set -Eeuo pipefail
export APP_DIR="${APP_DIR:?Set the production repository path}"
export ENV_FILE="${ENV_FILE:-.env.production}"
export COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
export BACKUP_DIR="${BACKUP_DIR:?Set the verified deployment backup directory}"

cd "$APP_DIR"
ROLLBACK_COMMIT="$(tr -d '\\r\\n' < "$BACKUP_DIR/rollback-commit.txt")"
test "$ROLLBACK_COMMIT" = "$(git rev-parse "${ROLLBACK_COMMIT}^{commit}")"
git switch --detach "$ROLLBACK_COMMIT"

AEROASSIST_ENV_FILE="$ENV_FILE" \
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --quiet
AEROASSIST_ENV_FILE="$ENV_FILE" \
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  build backend frontend
AEROASSIST_ENV_FILE="$ENV_FILE" \
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  up -d --no-deps backend frontend
```

Restore the previous `APP_GIT_COMMIT` and `APP_DEPLOYMENT_ID` values using the
operator's protected release record before validation.

## Validation After Rollback

```bash
AEROASSIST_ENV_FILE="$ENV_FILE" \
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
AEROASSIST_ENV_FILE="$ENV_FILE" \
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  exec -T backend python scripts/check_production_readiness.py
APP_BASE_URL="$APP_BASE_URL" deploy/hostinger/scripts/smoke_production.sh
```

The running backend must report the recorded rollback commit and remain healthy
and ready.

## Data Restore Boundary

Do not restore MongoDB or document exports as an automatic application rollback
step. Product Recovery adds no automatic migration, so application rollback is
expected to preserve data. If evidence shows data incompatibility or corruption:

- stop writes;
- preserve the failed state and logs;
- obtain separate restore authorization;
- verify archive checksum, manifest, and off-host copy;
- rehearse the exact restore in a disposable target;
- follow the disaster-recovery runbook;
- record operator, timestamps, counts, and decisions.

Never delete or recreate the production MongoDB volume as a shortcut.
