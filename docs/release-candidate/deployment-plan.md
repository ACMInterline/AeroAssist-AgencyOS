# Controlled Product Recovery Deployment Plan

This plan uses the existing Hostinger tooling. It does not authorize execution.

## Preconditions

- `origin/main` contains the validated application merge and separate pin
  commit.
- The pin names the exact 40-character application merge SHA.
- Hosted CI passed for the exact commits.
- The production worktree is clean.
- Current running commit is resolvable and will become `ROLLBACK_COMMIT`.
- Configuration, authenticated MongoDB, document volume, disk, memory, HTTPS,
  health, and safe readiness pass preflight.
- A verified on-host backup, independently verified off-host copy, and
  disposable restore rehearsal exist.
- An authorized maintenance window and operators are present.

## Mac Verification

```bash
set -Eeuo pipefail
git switch main
git fetch --prune origin
git pull --ff-only origin main
test -z "$(git status --porcelain)"
TOOLING_COMMIT="$(git rev-parse HEAD)"
APPLICATION_MERGE_COMMIT="$(
  sed -n 's/^RELEASE_COMMIT="\\([0-9a-f]\\{40\\}\\)"/\\1/p' \
    deploy/hostinger/scripts/deploy_v1_release_candidate.sh
)"
test "${#APPLICATION_MERGE_COMMIT}" -eq 40
git cat-file -e "${APPLICATION_MERGE_COMMIT}^{commit}"
bash -n deploy/hostinger/scripts/deploy_v1_release_candidate.sh
python3 backend/scripts/run_pilot_release_validation.py \
  --profile full \
  --include-docker-config \
  --output /tmp/aeroassist-product-recovery-deployment-candidate.json
git diff --check
```

## VPS Repository Update And Preflight

Run only in the approved maintenance window:

```bash
set -Eeuo pipefail
export APP_DIR="${APP_DIR:?Set the production repository path}"
export ENV_FILE="${ENV_FILE:-.env.production}"
export COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"
export BACKUP_ROOT="${BACKUP_ROOT:?Set the approved backup root}"
export APP_BASE_URL="${APP_BASE_URL:?Set the canonical HTTPS base URL}"
export TOOLING_COMMIT="${TOOLING_COMMIT:?Set the approved deployment-tooling commit}"

cd "$APP_DIR"
test -z "$(git status --porcelain)"
git fetch --prune origin main
git cat-file -e "${TOOLING_COMMIT}^{commit}"
git switch --detach "$TOOLING_COMMIT"
test "$(git rev-parse HEAD)" = "$TOOLING_COMMIT"

APP_DIR="$APP_DIR" \
ENV_FILE="$ENV_FILE" \
COMPOSE_FILE="$COMPOSE_FILE" \
BACKUP_ROOT="$BACKUP_ROOT" \
deploy/hostinger/scripts/preflight.sh
```

## Verified Backup

The deployment script creates and verifies a fresh timestamped MongoDB archive
and document-export backup before switching to the release. An operator should
also make and independently verify the off-host copy before deployment:

```bash
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
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
deploy/hostinger/scripts/verify_backups.sh

BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
sha256sum -c "$BACKUP_DIR/mongodb-$TIMESTAMP.archive.gz.sha256"
sha256sum -c "$BACKUP_DIR/document_exports.tar.gz.sha256"
```

Copy the complete `BACKUP_DIR` to approved off-host storage using the
organization's protected transfer method. Re-run checksum verification at the
destination. Do not put storage credentials or locations in release evidence.

## Disposable Restore Rehearsal

Use a unique non-production database and the guarded test script:

```bash
ARCHIVE="$BACKUP_DIR/mongodb-$TIMESTAMP.archive.gz"
RESTORE_DATABASE="aeroassist_restore_rehearsal_${TIMESTAMP}"
RESTORE_TARGET_ENV=test \
ALLOW_DESTRUCTIVE_TEST_RESTORE=true \
APP_DIR="$APP_DIR" \
ENV_FILE="$ENV_FILE" \
COMPOSE_FILE="$COMPOSE_FILE" \
deploy/hostinger/scripts/test_restore_mongodb_backup.sh \
  --archive "$ARCHIVE" \
  --target-database "$RESTORE_DATABASE"
```

Stop if the rehearsal is not isolated, guarded, checksum-valid, and successful.

## Controlled Deployment

The script records the running backend commit, fetches and verifies the exact
pin, exports the release-version backup verifier, creates another fresh backup,
then switches and builds. Once armed, an application failure triggers automatic
application rollback to the recorded commit.

```bash
sudo env \
  APP_DIR="$APP_DIR" \
  ENV_FILE="$ENV_FILE" \
  COMPOSE_FILE="$COMPOSE_FILE" \
  BACKUP_ROOT="$BACKUP_ROOT" \
  APP_BASE_URL="$APP_BASE_URL" \
  deploy/hostinger/scripts/deploy_v1_release_candidate.sh
```

Success ends with `DEPLOYMENT_COMPLETE: <exact-application-merge-sha>`.

## Post-Deployment Validation

```bash
cd "$APP_DIR"
AEROASSIST_ENV_FILE="$ENV_FILE" \
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
AEROASSIST_ENV_FILE="$ENV_FILE" \
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" \
  exec -T backend python scripts/check_production_readiness.py
APP_BASE_URL="$APP_BASE_URL" deploy/hostinger/scripts/smoke_production.sh
APP_DIR="$APP_DIR" \
ENV_FILE="$ENV_FILE" \
COMPOSE_FILE="$COMPOSE_FILE" \
APP_BASE_URL="$APP_BASE_URL" \
deploy/hostinger/scripts/healthcheck.sh
```

Verify `/api/health`, safe public `/api/readiness`, anonymous protected
diagnostics denial, authenticated bounded Platform diagnostics, tenant
isolation, onboarding-to-Operations routing, Commercial Pilot readiness, and
the exact backend commit. Then follow the Phase 57 evidence plan.

## Stop Conditions

Stop before or during deployment on any dirty worktree, unresolved commit,
pin mismatch, configuration error, backup/checksum/manifest failure, missing
off-host copy, restore-rehearsal failure, database/index incompatibility,
unhealthy container, phase mismatch, unsafe readiness disclosure,
authentication failure, tenant-isolation failure, smoke failure, or blocked
Phase 57 assessment. Never reinterpret a failed check as success.
