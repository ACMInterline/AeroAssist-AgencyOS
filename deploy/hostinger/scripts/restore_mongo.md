# Restore MongoDB And Document Exports

This is intentionally a manual runbook, not an automatic destructive script.

## Inputs

Set:

```bash
APP_DIR=/opt/aeroassist-agencyos
ENV_FILE=.env.production
COMPOSE_FILE=docker-compose.production.yml
BACKUP_DIR=/var/backups/aeroassist/YYYYMMDDTHHMMSSZ
```

Verify backup files:

```bash
cd "$BACKUP_DIR"
sha256sum -c mongo.archive.gz.sha256
sha256sum -c document_exports.tar.gz.sha256
```

## Restore MongoDB

This drops existing MongoDB data in the target database before restore. Confirm the target environment and maintenance window first.

```bash
cd "$APP_DIR"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" stop backend frontend
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T mongo \
  mongorestore --archive --gzip --drop < "$BACKUP_DIR/mongo.archive.gz"
```

## Restore Document Exports

The export restore replaces files inside the backend export directory. Keep a fresh backup of current exports before this step.

```bash
cd "$APP_DIR"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" start backend
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  sh -c 'mkdir -p /var/lib/aeroassist/document_exports && tar -C /var/lib/aeroassist -xzf -' \
  < "$BACKUP_DIR/document_exports.tar.gz"
```

## Restart And Verify

```bash
cd "$APP_DIR"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend python scripts/check_production_readiness.py
APP_BASE_URL=https://agencyos.example.com deploy/hostinger/scripts/smoke_production.sh
```

Do not delete backup files until application owners confirm the restored environment.
