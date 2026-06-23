# AeroAssist Hostinger Operations Runbook

This runbook is for operating the Phase 18 Docker Compose deployment on a Hostinger managed VPS.

It does not add product functionality, monitoring services, CI/CD, background workers, provider webhooks, public links, uploads, payment links, or airline integrations.

## Folder Layout

Recommended VPS layout:

```text
/opt/aeroassist/AeroAssist-AgencyOS
/var/backups/aeroassist
/etc/nginx/sites-available/aeroassist.conf
/etc/nginx/sites-enabled/aeroassist.conf
```

Repository deployment helpers live under:

```text
deploy/hostinger/
deploy/hostinger/nginx/aeroassist.conf.example
deploy/hostinger/scripts/
```

## First Setup Checklist

1. Install Docker Engine and Docker Compose plugin.
2. Clone the repository into `/opt/aeroassist/AeroAssist-AgencyOS`.
3. Copy `.env.production.example` to `.env.production`.
4. Set a real `AUTH_TOKEN_SECRET`.
5. Set `PUBLIC_APP_URL`, `FRONTEND_URL`, and `CORS_ALLOWED_ORIGINS` to the production domain.
6. Use `FRONTEND_HTTP_PORT=127.0.0.1:8080` when host nginx terminates TLS.
7. Keep `DEMO_AUTH_ENABLED=false`, `SEED_ON_STARTUP=false`, and `SEED_ENDPOINT_ENABLED=false`.
8. Build and start Compose.
9. Configure host nginx and TLS.
10. Run readiness and smoke checks.

## Reverse Proxy And TLS

Recommended production path:

- Host nginx listens on `80` and `443`.
- Docker frontend listens on `127.0.0.1:8080`.
- Host nginx proxies all traffic to `http://127.0.0.1:8080`.
- The frontend container proxies `/api` to the backend container internally.

Install nginx and certbot:

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

Install the template:

```bash
sudo cp deploy/hostinger/nginx/aeroassist.conf.example /etc/nginx/sites-available/aeroassist.conf
sudo nano /etc/nginx/sites-available/aeroassist.conf
sudo ln -s /etc/nginx/sites-available/aeroassist.conf /etc/nginx/sites-enabled/aeroassist.conf
sudo nginx -t
sudo systemctl reload nginx
```

Issue a certificate:

```bash
sudo certbot --nginx -d agencyos.example.com -d www.agencyos.example.com
sudo certbot renew --dry-run
```

Use your real domain, not the placeholder.

## Deploy Or Update

From the repo:

```bash
APP_DIR=/opt/aeroassist/AeroAssist-AgencyOS \
APP_BASE_URL=https://agencyos.example.com \
RUN_SMOKE=true \
deploy/hostinger/scripts/deploy.sh
```

The deploy script:

- verifies `.env.production`,
- optionally pulls latest `main`,
- validates Compose config,
- builds images,
- starts services,
- runs the backend readiness script,
- optionally runs the production smoke test.

Set `UPDATE_GIT=false` to deploy the already-checked-out commit.

## Restart, Status, Logs

Restart:

```bash
deploy/hostinger/scripts/restart.sh
```

Status:

```bash
deploy/hostinger/scripts/status.sh
```

All logs:

```bash
deploy/hostinger/scripts/logs.sh
```

One service:

```bash
SERVICE=backend deploy/hostinger/scripts/logs.sh
SERVICE=frontend deploy/hostinger/scripts/logs.sh
SERVICE=mongo deploy/hostinger/scripts/logs.sh
```

## Production Smoke Test

```bash
APP_BASE_URL=https://agencyos.example.com deploy/hostinger/scripts/smoke_production.sh
```

The smoke test checks:

- frontend root responds,
- `/api/health` reports `ok=true`,
- `/api/readiness` reports `ok=true`,
- readiness does not contain obvious secret-value placeholders,
- `/api/auth/login` is reachable and rejects fake credentials.

It does not use real credentials.

## Backups

Backups are timestamped under `/var/backups/aeroassist` by default. No script deletes old backups automatically.

MongoDB:

```bash
deploy/hostinger/scripts/backup_mongo.sh
```

Document exports:

```bash
deploy/hostinger/scripts/backup_exports.sh
```

Recommended before every production update:

```bash
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TIMESTAMP="$TIMESTAMP" deploy/hostinger/scripts/backup_mongo.sh
TIMESTAMP="$TIMESTAMP" deploy/hostinger/scripts/backup_exports.sh
```

Store off-server copies according to your operational policy. This phase does not add automated remote backup storage.

## Restore

Restore is documented in:

```text
deploy/hostinger/scripts/restore_mongo.md
```

High-level process:

1. Announce maintenance window.
2. Take a fresh backup of the current state.
3. Verify backup checksums.
4. Stop frontend/backend.
5. Restore MongoDB with `mongorestore --drop`.
6. Restore document exports tarball.
7. Restart services.
8. Run readiness and smoke checks.
9. Have application owners validate business-critical records.

## Rollback

Code rollback without data restore:

```bash
cd /opt/aeroassist/AeroAssist-AgencyOS
git log --oneline -10
git checkout <previous-good-commit>
UPDATE_GIT=false deploy/hostinger/scripts/deploy.sh
```

Data rollback should use the restore procedure and only after confirming the selected backup point.

Do not automate destructive rollback until migrations and backup verification policies exist.

## Health And Readiness

```bash
curl https://agencyos.example.com/api/health
curl https://agencyos.example.com/api/readiness
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend python scripts/check_production_readiness.py
```

Readiness must not expose secret values.

## Incident Checklist

1. Check service status.
2. Check backend logs.
3. Check frontend logs.
4. Check Mongo logs.
5. Check `/api/health`.
6. Check `/api/readiness`.
7. Confirm disk space.
8. Confirm certificate validity.
9. Confirm recent backups exist before any risky action.

Useful commands:

```bash
df -h
sudo systemctl status nginx
sudo nginx -t
sudo certbot certificates
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

## Known Limitations

- No automated backups.
- No remote backup storage.
- No monitoring stack.
- No alerting.
- No migrations framework.
- No CI/CD.
- No object storage.
- No background workers, provider webhooks, automatic sending, public links, uploads, payment links, or airline integrations.
