# AeroAssist V1 Controlled Pilot Deployment Commands

These commands bind the candidate to commit `5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0`. Production-mutating sections require an approved maintenance window, authorized operator, verified backup, exact rollback commit, and human release sign-off.

## 1. Exact Local Verification

```bash
cd /Users/nik/Documents/GitHub/AeroAssist-AgencyOS
export RELEASE_BRANCH=v1-integration-program
export RELEASE_COMMIT=5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0
export RELEASE_SHORT=5a557b5f

git fetch origin "$RELEASE_BRANCH"
test "$(git branch --show-current)" = "$RELEASE_BRANCH"
test "$(git rev-parse HEAD)" = "$RELEASE_COMMIT"
test "$(git rev-parse origin/$RELEASE_BRANCH)" = "$RELEASE_COMMIT"
test -z "$(git status --porcelain)"

python3 -m compileall -q backend
npm run build --prefix frontend
python3 backend/scripts/validate_smoke_inventory.py
python3 backend/scripts/validate_persistence_query_foundation.py
git diff --check

find deploy/hostinger/scripts deploy/hostinger/mongodb \
  -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n

AEROASSIST_ENV_FILE=.env.production.example \
docker compose --env-file .env.production.example \
  -f docker-compose.production.yml config --quiet

docker build \
  --label "org.opencontainers.image.revision=$RELEASE_COMMIT" \
  --tag "aeroassist-agencyos-backend:$RELEASE_SHORT-preflight" \
  backend

docker build \
  --build-arg VITE_API_BASE_URL= \
  --build-arg VITE_APP_ENV=production \
  --label "org.opencontainers.image.revision=$RELEASE_COMMIT" \
  --tag "aeroassist-agencyos-frontend:$RELEASE_SHORT-preflight" \
  frontend

docker image inspect \
  "aeroassist-agencyos-backend:$RELEASE_SHORT-preflight" \
  "aeroassist-agencyos-frontend:$RELEASE_SHORT-preflight" \
  --format '{{index .Config.Labels "org.opencontainers.image.revision"}}|{{json .Config.Healthcheck}}|{{.Config.User}}'
```

Remove local generated output and preflight image tags after retaining sanitized results:

```bash
find backend -type d -name __pycache__ -prune -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
find frontend/dist -depth -delete 2>/dev/null || true
docker image rm \
  "aeroassist-agencyos-backend:$RELEASE_SHORT-preflight" \
  "aeroassist-agencyos-frontend:$RELEASE_SHORT-preflight"
```

## 2. Exact VPS Backup Commands

Run these before changing the checked-out application commit:

```bash
cd /opt/aeroassist-agencyos
export APP_DIR=/opt/aeroassist-agencyos
export ENV_FILE=.env.production
export COMPOSE_FILE=docker-compose.production.yml
export BACKUP_ROOT=/var/backups/aeroassist
export TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
BACKUP_ROOT="$BACKUP_ROOT" TIMESTAMP="$TIMESTAMP" \
deploy/hostinger/scripts/backup_all.sh

APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
BACKUP_ROOT="$BACKUP_ROOT" \
deploy/hostinger/scripts/verify_backups.sh

test -s "$BACKUP_ROOT/$TIMESTAMP/document_exports.tar.gz"
test -s "$BACKUP_ROOT/$TIMESTAMP/document_exports.tar.gz.sha256"
find "$BACKUP_ROOT/$TIMESTAMP" -maxdepth 1 -type f -name 'mongodb-*.archive.gz' -size +0 -print -quit | grep -q .
find "$BACKUP_ROOT/$TIMESTAMP" -maxdepth 1 -type f -name 'mongodb-*.manifest.json' -size +0 -print -quit | grep -q .
```

Copy the entire timestamped directory to the approved off-host destination and verify it there. Set the destination according to the approved infrastructure policy:

```bash
export OFF_HOST_DEST='<approved-user>@<approved-host>:<approved-backup-root>/'
rsync -a --protect-args "$BACKUP_ROOT/$TIMESTAMP/" "$OFF_HOST_DEST$TIMESTAMP/"
```

Do not proceed until the off-host copy has independent checksum and manifest evidence.

## 3. Exact VPS Deployment Commands

Confirm `.env.production` has real values, `APP_GIT_COMMIT=5a557b5f` or the full commit, and a unique `APP_DEPLOYMENT_ID`. Do not print the environment file.

```bash
cd /opt/aeroassist-agencyos
export APP_DIR=/opt/aeroassist-agencyos
export ENV_FILE=.env.production
export COMPOSE_FILE=docker-compose.production.yml
export RELEASE_BRANCH=v1-integration-program
export RELEASE_COMMIT=5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0
export RELEASE_SHORT=5a557b5f
export APP_BASE_URL=https://avio.my

test -z "$(git status --porcelain)"
git fetch origin "$RELEASE_BRANCH"
test "$(git rev-parse origin/$RELEASE_BRANCH)" = "$RELEASE_COMMIT"
git switch --detach "$RELEASE_COMMIT"
test "$(git rev-parse HEAD)" = "$RELEASE_COMMIT"

grep -Eq '^APP_ENV=production$' "$ENV_FILE"
grep -Eq '^AEROASSIST_DB_MODE=mongo$' "$ENV_FILE"
grep -Eq '^DEMO_AUTH_ENABLED=false$' "$ENV_FILE"
grep -Eq '^SEED_ON_STARTUP=false$' "$ENV_FILE"
grep -Eq '^SEED_ENDPOINT_ENABLED=false$' "$ENV_FILE"
grep -Eq '^APP_GIT_COMMIT=(5a557b5f|5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0)$' "$ENV_FILE"
grep -Eq '^APP_DEPLOYMENT_ID=.+$' "$ENV_FILE"

APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
deploy/hostinger/scripts/preflight.sh

APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
UPDATE_GIT=false RUN_PREFLIGHT=true RUN_SMOKE=false \
deploy/hostinger/scripts/deploy.sh
```

The deployment script validates Compose, builds images, starts services, displays service state, and runs the backend production-readiness check. It does not approve the pilot release.

## 4. Exact Post-Deployment Validation Commands

```bash
cd /opt/aeroassist-agencyos
export APP_DIR=/opt/aeroassist-agencyos
export ENV_FILE=.env.production
export COMPOSE_FILE=docker-compose.production.yml
export RELEASE_COMMIT=5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0
export RELEASE_SHORT=5a557b5f
export APP_BASE_URL=https://avio.my
export CANONICAL_WWW_URL=https://www.avio.my

test "$(git rev-parse HEAD)" = "$RELEASE_COMMIT"
AEROASSIST_ENV_FILE="$ENV_FILE" \
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

test "$(AEROASSIST_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend printenv APP_GIT_COMMIT)" = "$RELEASE_SHORT" \
  || test "$(AEROASSIST_ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend printenv APP_GIT_COMMIT)" = "$RELEASE_COMMIT"

AEROASSIST_ENV_FILE="$ENV_FILE" \
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python scripts/check_production_readiness.py

APP_BASE_URL="$APP_BASE_URL" \
deploy/hostinger/scripts/smoke_production.sh

APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
APP_BASE_URL="$APP_BASE_URL" CANONICAL_WWW_URL="$CANONICAL_WWW_URL" \
deploy/hostinger/scripts/healthcheck.sh

curl --fail --silent --show-error "$APP_BASE_URL/api/health"
curl --fail --silent --show-error "$APP_BASE_URL/api/readiness"
```

Record sanitized evidence for service health, exact commit, phase, backup, smoke, tenant isolation, and human sign-off. Never store secrets, raw logs, passenger records, filesystem paths, or backup contents as release evidence.

## 5. Exact Application Rollback Commands

Before deployment, replace `<approved-40-character-rollback-commit>` with the reviewed previous commit and record it in the release sign-off. These commands roll back application code and containers only. They do not restore or mutate MongoDB data.

```bash
cd /opt/aeroassist-agencyos
export APP_DIR=/opt/aeroassist-agencyos
export ENV_FILE=.env.production
export COMPOSE_FILE=docker-compose.production.yml
export APP_BASE_URL=https://avio.my
export ROLLBACK_COMMIT='<approved-40-character-rollback-commit>'

test "${#ROLLBACK_COMMIT}" -eq 40
git fetch origin --tags
git cat-file -e "$ROLLBACK_COMMIT^{commit}"

APP_DIR="$APP_DIR" ENV_FILE="$ENV_FILE" COMPOSE_FILE="$COMPOSE_FILE" \
BACKUP_ROOT=/var/backups/aeroassist TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)" \
deploy/hostinger/scripts/backup_all.sh

git switch --detach "$ROLLBACK_COMMIT"
test "$(git rev-parse HEAD)" = "$ROLLBACK_COMMIT"
sed -i "s/^APP_GIT_COMMIT=.*/APP_GIT_COMMIT=${ROLLBACK_COMMIT}/" "$ENV_FILE"

AEROASSIST_ENV_FILE="$ENV_FILE" \
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --quiet
AEROASSIST_ENV_FILE="$ENV_FILE" \
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build backend frontend
AEROASSIST_ENV_FILE="$ENV_FILE" \
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --no-deps backend frontend
AEROASSIST_ENV_FILE="$ENV_FILE" \
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

APP_BASE_URL="$APP_BASE_URL" \
deploy/hostinger/scripts/smoke_production.sh
```

If application-only rollback is not data compatible, stop and follow `deploy/hostinger/MONGODB_DISASTER_RECOVERY_RUNBOOK.md` under separate explicit authorization. Never delete volumes, drop indexes, run startup seeding, or execute a production database restore as an automatic rollback shortcut.
