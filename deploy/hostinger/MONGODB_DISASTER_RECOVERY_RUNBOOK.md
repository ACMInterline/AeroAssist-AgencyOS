# MongoDB Security and Disaster Recovery Runbook

## Safety Rules

- Never test against the production database or volume.
- Never delete a volume as part of authentication migration.
- Never place `.env.production` in an ordinary backup archive.
- Keep MongoDB without a host port.
- Take a verified pre-change backup and an off-host copy before maintenance.
- Use dry-run restore planning and disposable rehearsal before any cutover.

Examples assume `/opt/aeroassist-agencyos`, `.env.production`, `docker-compose.production.yml`, and `/var/backups/aeroassist`. Substitute intentionally and keep environment files mode `600`.

## New Empty Volume

1. Generate distinct root and application passwords outside shell history.
2. Set `MONGO_AUTHENTICATION_ENABLED=true`, root/app identities, `MONGO_AUTH_SOURCE=admin`, and `MONGO_DATABASE` in `.env.production`.
3. Leave `MONGODB_URL` blank unless an explicit authenticated override is required.
4. Run `deploy/hostinger/scripts/preflight.sh`.
5. Start Compose. The official image creates the root user and the mounted initializer creates the app user once.
6. Verify backend health and create a first backup.

## Existing Unauthenticated Volume Migration

Do not assume initialization variables affect an existing volume.

### Pre-Migration Backup

While the current deployment is healthy, create its final unauthenticated backup using the currently committed tooling, verify it, copy it off-host, and record the Git revision. Also back up document exports.

### Maintenance Window

```bash
cd /opt/aeroassist-agencyos
docker compose --env-file .env.production -f docker-compose.production.yml stop frontend backend
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

Confirm MongoDB has no `ports` mapping and is accessible only through `docker compose exec`.

### Create Users Through Local Container Access

Before enabling `--auth`, create users in the running local MongoDB container. Do not place passwords directly in shell history. Load them from the protected environment or a root-only temporary environment file.

Create an administrative user in `admin` with roles appropriate to recovery administration. Create the application user in `MONGO_AUTH_SOURCE` with only `{role: "readWrite", db: MONGO_DATABASE}`.

Prepare `/root/aeroassist-mongo-auth-migration.env` with mode `600` and the six `MONGO_*` values from the protected production configuration. Load it without echoing values, then pass variable names rather than values on the command line:

```bash
set -a
source /root/aeroassist-mongo-auth-migration.env
set +a

docker compose --env-file .env.production -f docker-compose.production.yml exec -T \
  -e MONGO_INITDB_ROOT_USERNAME -e MONGO_INITDB_ROOT_PASSWORD \
  -e MONGO_APP_USERNAME -e MONGO_APP_PASSWORD \
  -e MONGO_AUTH_SOURCE -e MONGO_DATABASE \
  mongo mongosh --quiet <<'MONGOSH'
const admin = db.getSiblingDB("admin");
if (admin.getUser(process.env.MONGO_INITDB_ROOT_USERNAME) === null) {
  admin.createUser({
    user: process.env.MONGO_INITDB_ROOT_USERNAME,
    pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
    roles: [{role: "root", db: "admin"}],
  });
}
const authDb = db.getSiblingDB(process.env.MONGO_AUTH_SOURCE || "admin");
if (authDb.getUser(process.env.MONGO_APP_USERNAME) === null) {
  authDb.createUser({
    user: process.env.MONGO_APP_USERNAME,
    pwd: process.env.MONGO_APP_PASSWORD,
    roles: [{role: "readWrite", db: process.env.MONGO_DATABASE}],
  });
}
MONGOSH
```

Delete the temporary migration file after the protected production environment is updated and verified. Do not paste credentials into tickets, chat, logs, commands, or this repository.

### Verify Before Switching

Test both identities from inside the container, including an application-user write/read on the application database. Remove the temporary verification record. Record only pass/fail and timestamp.

The backend service explicitly masks `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD`; verify they are empty there. Administrative credentials remain available only to MongoDB and host-side guarded recovery tooling.

### Switch Compose

Set the Phase 56.5.5 variables, run preflight, and recreate MongoDB/backend during the maintenance window:

```bash
deploy/hostinger/scripts/preflight.sh
docker compose --env-file .env.production -f docker-compose.production.yml up -d --force-recreate mongo backend
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

### Validate

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend python scripts/check_production_readiness.py
APP_BASE_URL=https://avio.my deploy/hostinger/scripts/smoke_production.sh
deploy/hostinger/scripts/backup_all.sh
deploy/hostinger/scripts/verify_backups.sh
```

Then start the frontend and validate representative tenant-scoped reads.

### Rollback

If authentication or backend reconnection fails, stop application traffic. Revert only the Compose authentication switch during the same maintenance window; do not remove users or delete the volume. Restore the previous code/config revision if required. Use the pre-migration backup only if data integrity is in question, and rehearse it against a disposable target first.

## Routine Backup and Verification

```bash
deploy/hostinger/scripts/backup_all.sh
deploy/hostinger/scripts/verify_backups.sh
BACKUP_ROOT=/var/backups/aeroassist deploy/hostinger/scripts/prune_backups.sh
```

Apply retention only after reviewing dry-run output:

```bash
BACKUP_RETENTION_DAYS=30 BACKUP_MINIMUM_COUNT=7 deploy/hostinger/scripts/prune_backups.sh --apply
```

Copy complete verified sets off-host. Monitor `journalctl -u aeroassist-backup.service` and `aeroassist-backup-verify.service`.

## Disposable Restore Rehearsal

```bash
archive=/var/backups/aeroassist/YYYYMMDDTHHMMSSZ/mongodb-YYYYMMDDTHHMMSSZ.archive.gz
RESTORE_TARGET_ENV=test \
ALLOW_DESTRUCTIVE_TEST_RESTORE=true \
deploy/hostinger/scripts/test_restore_mongodb_backup.sh \
  --archive "$archive" \
  --target-database aeroassist_restore_rehearsal
```

The script refuses the configured production/source names and deletes its temporary container and volume unless preservation is explicitly requested.

## Restore Planning

Validation-only planning:

```bash
deploy/hostinger/scripts/restore_mongodb_backup.sh \
  --archive "$archive" \
  --target-database aeroassist_recovery_candidate
```

Prefer restoring to a new database, validating it, and planning an explicit cutover. Any execution against the production-configured MongoDB cluster, including a new candidate database name, requires the multi-part production guards documented by `--help`; it must never be placed in cron, systemd, deployment scripts, or CI.

## Recovery Scenarios

### Lost Container

Recreate the container from the pinned Compose revision. The named volume persists. Verify authentication, backend health, and backup capability.

### Failed Deployment

Roll code back to the previous verified Git revision without restoring data. Restore data only when an evidence-backed data integrity problem exists.

### Lost MongoDB Volume

Provision a new empty authenticated volume, verify the chosen archive, rehearse it, restore to a candidate database, validate counts and application behavior, then approve cutover. Recover document exports separately.

### Full VPS Loss

Provision Ubuntu/Docker/nginx/TLS, clone the verified Git revision, restore protected environment values separately, create authenticated MongoDB, restore a verified off-host database backup, restore document exports, validate nginx/domain health, and run production smoke checks before reopening traffic.

## Credential Rotation

Create or update credentials through local authenticated administration, update the protected environment, recreate backend connections, verify health, then retire old credentials. Rotate root and app credentials separately. Do not log values or encode them in documentation.

## Recovery Objectives

Record actual backup completion times, off-host copy times, archive sizes, rehearsal duration, and validation duration. These observations inform RPO/RTO decisions; this runbook does not guarantee either objective.
