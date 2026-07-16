# First Hostinger VPS Deployment Checklist

Use this as the linear first-deploy path. It assumes a Hostinger managed VPS and the Phase 18-21 Docker Compose deployment.

No real secrets, domain values, or certificate files belong in this repository.

## 1. VPS Access

SSH into the VPS:

```bash
ssh root@your-vps-ip
```

Choose the app directory. The verified Hostinger deployment path is `/opt/aeroassist-agencyos`:

```bash
sudo mkdir -p /opt/aeroassist-agencyos
sudo chown "$USER":"$USER" /opt/aeroassist-agencyos
cd /opt
```

## 2. Install Prerequisites

Install baseline packages:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates gnupg nginx certbot python3-certbot-nginx
```

Install Docker Engine and Compose plugin using Docker's official repository, then verify:

```bash
docker --version
docker compose version
docker info
```

If `docker info` fails for a non-root user, log out and back in after adding the user to the Docker group.

## 3. Clone Repository

```bash
cd /opt
git clone https://github.com/ACMInterline/AeroAssist-AgencyOS.git aeroassist-agencyos
cd /opt/aeroassist-agencyos
git checkout main
git rev-parse HEAD
```

Record the commit hash in your deployment notes.

## 4. Create `.env.production`

```bash
cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production
```

Required checks:

- `APP_ENV=production`
- `AEROASSIST_DB_MODE=mongo`
- `MONGO_AUTHENTICATION_ENABLED=true`
- distinct non-placeholder `MONGO_INITDB_ROOT_PASSWORD` and `MONGO_APP_PASSWORD`
- `MONGO_AUTH_SOURCE=admin`
- `MONGO_DATABASE=aeroassist_agencyos`
- `MONGODB_URL=` remains blank unless an explicit authenticated override is required
- `MONGODB_DATABASE=aeroassist_agencyos`
- `BACKUP_RETENTION_DAYS` and `BACKUP_MINIMUM_COUNT` are positive integers
- `DEMO_AUTH_ENABLED=false`
- `SEED_ON_STARTUP=false`
- `SEED_ENDPOINT_ENABLED=false`
- `AUTH_TOKEN_SECRET` is a real generated secret, not the example placeholder
- `DOCUMENT_EXPORT_STORAGE_DIR=/var/lib/aeroassist/document_exports`
- `CORS_ALLOWED_ORIGINS=https://your-domain.example`
- `FRONTEND_URL=https://your-domain.example`
- `PUBLIC_APP_URL=https://your-domain.example`
- `QUERY_DEFAULT_LIMIT=50` and `QUERY_MAXIMUM_LIMIT=250`
- `QUERY_SLOW_THRESHOLD_MS=250` and `QUERY_DIAGNOSTICS_ENABLED=true`
- `READINESS_DATABASE_TIMEOUT_SECONDS=5`
- `FRONTEND_HTTP_PORT=127.0.0.1:8080`
- `VITE_API_BASE_URL=` remains blank when frontend nginx proxies `/api`

Generate an auth secret:

```bash
openssl rand -hex 32
```

Do not commit `.env.production`.

Phase 56.5.6 query controls are operational bounds, not feature settings. Keep the default limit positive, the maximum at or above the default, the maximum no greater than 1000, and the readiness timeout greater than zero and no more than 60 seconds. Query diagnostics contain structural metadata only and must remain free of filter values and passenger data.

## 5. Preflight

Run preflight before starting services:

```bash
APP_DIR=/opt/aeroassist-agencyos \
deploy/hostinger/scripts/preflight.sh
```

Preflight verifies:

- repository layout,
- `.env.production`,
- Docker and Compose availability,
- required production env vars without printing secrets,
- backup root writability,
- Compose config,
- Docker daemon reachability.

## 6. First Start

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml up -d
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

Check logs:

```bash
SERVICE=backend deploy/hostinger/scripts/logs.sh
```

## 7. Local Readiness Before TLS

```bash
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/readiness
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend python scripts/check_production_readiness.py
```

Do not continue until readiness is healthy.

## 7a. Create First Platform Owner

Only run this when no production owner exists yet:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec backend \
  python scripts/create_first_platform_owner.py
```

The script prompts for owner email, full name, password, and password confirmation. It does not print the password and refuses to run if auth identities already exist.

## 8. Host Nginx And TLS

Copy the nginx template:

```bash
sudo cp deploy/hostinger/nginx/aeroassist.conf.example /etc/nginx/sites-available/aeroassist.conf
sudo nano /etc/nginx/sites-available/aeroassist.conf
```

Replace:

- `agencyos.example.com`
- `www.agencyos.example.com`
- certificate paths if needed

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/aeroassist.conf /etc/nginx/sites-enabled/aeroassist.conf
sudo nginx -t
sudo systemctl reload nginx
```

When DNS points to the VPS:

```bash
sudo certbot --nginx -d your-domain.example -d www.your-domain.example
sudo certbot renew --dry-run
```

## 9. Production Smoke

```bash
APP_BASE_URL=https://your-domain.example deploy/hostinger/scripts/smoke_production.sh
```

Optional staging-only smoke with demo seed tooling:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend \
  env AEROASSIST_SMOKE_BASE_URL=http://frontend python scripts/check_portal_isolation.py
```

Do not enable demo seed tooling on a live production tenant just to run this optional smoke.

## 10. Manual App Verification

Verify:

- platform login,
- agency login,
- portal login,
- portal cross-client denial if test accounts exist,
- document export generation,
- document export download,
- `/api/readiness` does not expose secret values,
- SMTP secret refs are masked if SMTP is configured.

## 11. First Backup

```bash
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TIMESTAMP="$TIMESTAMP" deploy/hostinger/scripts/backup_mongo.sh
TIMESTAMP="$TIMESTAMP" deploy/hostinger/scripts/backup_exports.sh
```

Run `deploy/hostinger/scripts/verify_backups.sh`, rehearse the selected archive according to `MONGODB_DISASTER_RECOVERY_RUNBOOK.md`, and copy complete verified backup sets off the VPS according to your operational policy.

## 12. Record Deployment

Record:

```bash
date -u
git rev-parse HEAD
docker compose --env-file .env.production -f docker-compose.production.yml images
docker compose --env-file .env.production -f docker-compose.production.yml ps
sudo certbot certificates
```

## 13. Rollback Checklist

For code rollback:

```bash
git log --oneline -10
git checkout <previous-good-commit>
UPDATE_GIT=false RUN_PREFLIGHT=true deploy/hostinger/scripts/deploy.sh
```

For data rollback, follow:

```text
deploy/hostinger/MONGODB_DISASTER_RECOVERY_RUNBOOK.md
```

Never restore data without a maintenance window and a fresh backup of the current state.
