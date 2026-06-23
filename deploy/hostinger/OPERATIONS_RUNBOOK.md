# AeroAssist Hostinger Operations Runbook

This runbook is for operating the Phase 18 Docker Compose deployment on a Hostinger managed VPS.

It does not add product functionality, monitoring services, CI/CD, background workers, provider webhooks, public links, uploads, payment links, or airline integrations.

## Folder Layout

Recommended VPS layout:

```text
/opt/aeroassist-agencyos
/opt/aeroassist
/var/backups/aeroassist
/etc/nginx/sites-available/aeroassist.conf
/etc/nginx/sites-enabled/aeroassist.conf
```

`/opt/aeroassist` is the older app path and must not be modified by AgencyOS operations.

Repository deployment helpers live under:

```text
deploy/hostinger/
deploy/hostinger/nginx/aeroassist.conf.example
deploy/hostinger/scripts/
```

## First Setup Checklist

For the detailed first-run command sequence, use:

```text
deploy/hostinger/FIRST_DEPLOYMENT_CHECKLIST.md
```

1. Install Docker Engine and Docker Compose plugin.
2. Clone the repository into `/opt/aeroassist-agencyos`.
3. Copy `.env.production.example` to `.env.production`.
4. Set a real `AUTH_TOKEN_SECRET`.
5. Set `PUBLIC_APP_URL`, `FRONTEND_URL`, and `CORS_ALLOWED_ORIGINS` to the production domain.
6. Use `FRONTEND_HTTP_PORT=127.0.0.1:8080` when host nginx terminates TLS.
7. Keep `DEMO_AUTH_ENABLED=false`, `SEED_ON_STARTUP=false`, and `SEED_ENDPOINT_ENABLED=false`.
8. Run `deploy/hostinger/scripts/preflight.sh`.
9. Build and start Compose.
10. Configure host nginx and TLS.
11. Run readiness and smoke checks.

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
APP_DIR=/opt/aeroassist-agencyos \
APP_BASE_URL=https://agencyos.example.com \
RUN_SMOKE=true \
deploy/hostinger/scripts/deploy.sh
```

The deploy script:

- verifies `.env.production`,
- runs preflight by default,
- optionally pulls latest `main`,
- validates Compose config,
- builds images,
- starts services,
- runs the backend readiness script,
- optionally runs the production smoke test.

Set `UPDATE_GIT=false` to deploy the already-checked-out commit.
Set `RUN_PREFLIGHT=false` only for an intentional emergency override.

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
cd /opt/aeroassist-agencyos
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

## First Platform Owner Bootstrap

Run only when no production owner exists:

```bash
cd /opt/aeroassist-agencyos
docker compose --env-file .env.production -f docker-compose.production.yml exec backend \
  python scripts/create_first_platform_owner.py
```

The script refuses to run if auth identities already exist unless a controlled recovery action uses `--allow-existing-identities`. It does not print passwords, enable seed, create demo accounts, or create agencies/workspaces.

## Pending VPS Reboot Verification

Ubuntu reported `*** System restart required ***` after the first deployment. Use this procedure during an approved maintenance window.

Before reboot:

```bash
cd /opt/aeroassist-agencyos
deploy/hostinger/scripts/status.sh
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TIMESTAMP="$TIMESTAMP" deploy/hostinger/scripts/backup_mongo.sh
TIMESTAMP="$TIMESTAMP" deploy/hostinger/scripts/backup_exports.sh
curl http://72.62.52.129:8080/api/health
curl http://72.62.52.129:8080/api/readiness
curl -I http://72.62.52.129/
```

Reboot only after backups and health checks pass:

```bash
sudo reboot
```

After reconnecting:

```bash
cd /opt/aeroassist-agencyos
docker compose --env-file .env.production -f docker-compose.production.yml ps
curl http://72.62.52.129:8080/api/health
curl http://72.62.52.129:8080/api/readiness
curl -I http://72.62.52.129/
APP_BASE_URL=http://72.62.52.129:8080 deploy/hostinger/scripts/smoke_production.sh
```

Verify owner login manually in the browser. If AgencyOS containers did not auto-start:

```bash
cd /opt/aeroassist-agencyos
docker compose --env-file .env.production -f docker-compose.production.yml up -d
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

Do not stop or modify the older `/opt/aeroassist` app unless explicitly planned.

## Nginx/TLS Migration From Temporary 8080

Current temporary AgencyOS URL:

```text
http://72.62.52.129:8080
```

Future HTTPS migration plan:

1. Choose final domain or subdomain.
2. Point DNS A record to `72.62.52.129`.
3. Decide how the older app on port `80` should be handled:
   - keep it on a separate domain/subdomain,
   - move it,
   - or replace it.
4. Set AgencyOS `FRONTEND_HTTP_PORT=127.0.0.1:8080`.
5. Update `.env.production`:
   - `CORS_ALLOWED_ORIGINS=https://your-domain.example`
   - `FRONTEND_URL=https://your-domain.example`
   - `PUBLIC_APP_URL=https://your-domain.example`
6. Apply `deploy/hostinger/nginx/aeroassist.conf.example` after editing placeholders.
7. Run `sudo nginx -t`.
8. Reload nginx.
9. Obtain TLS with certbot only after DNS points correctly.
10. Recreate frontend/backend if env values changed.
11. Run production smoke tests.

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

## First Deployment And Troubleshooting

Use:

```text
deploy/hostinger/FIRST_DEPLOYMENT_CHECKLIST.md
deploy/hostinger/POST_DEPLOYMENT_SECURITY_CHECKLIST.md
deploy/hostinger/TROUBLESHOOTING.md
```
