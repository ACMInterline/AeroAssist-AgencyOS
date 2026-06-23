# Hostinger VPS Deployment

This guide packages AeroAssist AgencyOS with Docker Compose for a single Hostinger managed VPS and links to the Phase 19 operations assets.

It does not add DNS automation, real certificate issuance in the repo, monitoring, CI/CD, object storage, background workers, provider webhooks, public links, payment processing, or airline/GDS/NDC integrations.

## Architecture

`docker-compose.production.yml` runs:

- `frontend`: nginx serving the built Vite app on port `80`.
- `backend`: FastAPI/Uvicorn on internal port `8000`.
- `mongo`: MongoDB 7 with a named data volume.

The frontend container proxies `/api/*` to the backend service, so `VITE_API_BASE_URL` can stay blank when the frontend is the public entry point.

Recommended production mode after Phase 19:

- Host nginx owns public ports `80` and `443`.
- The frontend container binds to `127.0.0.1:8080`.
- Host nginx proxies to the frontend container.
- The frontend container proxies `/api` to the backend container.

Persistent volumes:

- `mongo_data` mounted to `/data/db`.
- `document_exports` mounted to `/var/lib/aeroassist/document_exports` in the backend container.

## VPS Prerequisites

For the first deployment, follow the full checklist:

```text
deploy/hostinger/FIRST_DEPLOYMENT_CHECKLIST.md
```

Install Docker Engine and the Compose plugin if your VPS image does not already include them:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out and back in after adding your user to the Docker group.

## Clone And Configure

```bash
git clone <your-repo-url> AeroAssist-AgencyOS
cd AeroAssist-AgencyOS
cp .env.production.example .env.production
chmod 600 .env.production
```

Edit `.env.production`:

```bash
nano .env.production
```

Required production values:

- `APP_ENV=production`
- `AEROASSIST_DB_MODE=mongo`
- `MONGODB_URL=mongodb://mongo:27017` for the bundled Mongo service, or your external Mongo URI.
- `MONGODB_DATABASE=aeroassist_agencyos`
- `DEMO_AUTH_ENABLED=false`
- `SEED_ON_STARTUP=false`
- `SEED_ENDPOINT_ENABLED=false`
- `AUTH_TOKEN_SECRET` set to a long random value.
- `DOCUMENT_EXPORT_STORAGE_DIR=/var/lib/aeroassist/document_exports`
- `CORS_ALLOWED_ORIGINS` set to your frontend origin, for example `https://agencyos.example.com`.
- `FRONTEND_URL` and `PUBLIC_APP_URL` set to the same public origin.
- `FRONTEND_HTTP_PORT=127.0.0.1:8080` when using host nginx/TLS.

Generate an auth secret:

```bash
openssl rand -hex 32
```

SMTP remains optional. If an agency is configured for SMTP mode, store the password only in an environment variable and reference it from agency settings as `env:AEROASSIST_SMTP_PASSWORD`:

```bash
AEROASSIST_SMTP_PASSWORD=<set-outside-git>
SMTP_SECRET_REFS=env:AEROASSIST_SMTP_PASSWORD
```

Do not commit `.env.production`.

## Build And Start

Use the production env file for Compose interpolation and container env:

```bash
deploy/hostinger/scripts/preflight.sh
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml up -d
```

Or use the Phase 19 helper:

```bash
APP_DIR=/opt/aeroassist/AeroAssist-AgencyOS deploy/hostinger/scripts/deploy.sh
```

Check service status:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml ps
docker compose --env-file .env.production -f docker-compose.production.yml logs -f backend
```

## Readiness Checks

From the VPS:

```bash
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/readiness
```

Run the production readiness script inside the backend container:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec backend python scripts/check_production_readiness.py
```

The script prints masked secret references only.

## Host Nginx And TLS

Use:

```text
deploy/hostinger/nginx/aeroassist.conf.example
```

Basic setup:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo cp deploy/hostinger/nginx/aeroassist.conf.example /etc/nginx/sites-available/aeroassist.conf
sudo nano /etc/nginx/sites-available/aeroassist.conf
sudo ln -s /etc/nginx/sites-available/aeroassist.conf /etc/nginx/sites-enabled/aeroassist.conf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d agencyos.example.com -d www.agencyos.example.com
```

Replace placeholders with the real domain before enabling.

## Smoke Checks

The existing smoke scripts can target the public frontend/proxy origin or backend service URL. For local VPS checks through nginx:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec backend \
  env AEROASSIST_SMOKE_BASE_URL=http://frontend python scripts/smoke_backend.py

docker compose --env-file .env.production -f docker-compose.production.yml exec backend \
  env AEROASSIST_SMOKE_BASE_URL=http://frontend python scripts/check_portal_isolation.py
```

These scripts rely on seeded demo data and the seed endpoint. They are for staging or local production-like validation, not for a live production tenant unless you intentionally enable seed tooling in a controlled maintenance window.

For live production endpoint checks without credentials:

```bash
APP_BASE_URL=https://agencyos.example.com deploy/hostinger/scripts/smoke_production.sh
```

## Verify The App

Open your public domain or VPS IP:

```text
http://your-vps-ip/
```

Verify:

- frontend loads,
- `/api/health` returns `ok: true`,
- `/api/readiness` has no production config failures,
- login works with real configured identities,
- portal isolation remains enforced,
- generated document exports download correctly,
- `document_exports` volume contains export files after generation.

## Stop, Restart, Update

Stop:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml down
```

Restart:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d
```

Helper scripts:

```bash
deploy/hostinger/scripts/restart.sh
deploy/hostinger/scripts/status.sh
SERVICE=backend deploy/hostinger/scripts/logs.sh
```

Update safely:

```bash
git pull
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml up -d
docker compose --env-file .env.production -f docker-compose.production.yml exec backend python scripts/check_production_readiness.py
```

Phase 19 deploy helper:

```bash
APP_BASE_URL=https://agencyos.example.com RUN_SMOKE=true deploy/hostinger/scripts/deploy.sh
```

## Backups And Restore

MongoDB backup:

```bash
deploy/hostinger/scripts/backup_mongo.sh
```

Document export backup:

```bash
deploy/hostinger/scripts/backup_exports.sh
```

Restore is intentionally manual because it can overwrite data:

```text
deploy/hostinger/scripts/restore_mongo.md
```

Run backups before every production update and store off-server copies according to your operational policy.

## Operations Runbook

Use:

```text
deploy/hostinger/OPERATIONS_RUNBOOK.md
deploy/hostinger/POST_DEPLOYMENT_SECURITY_CHECKLIST.md
deploy/hostinger/TROUBLESHOOTING.md
```

These cover host folder layout, TLS setup, deploy/update, restart/status/logs, backups, restore, rollback, smoke tests, post-deployment security verification, and troubleshooting.

## External Mongo Option

To use an external MongoDB service, set `MONGODB_URL` in `.env.production` and either leave the bundled `mongo` service unused or remove it from a local override compose file. Keep `AEROASSIST_DB_MODE=mongo`.

## Known Limitations

- No DNS setup is included.
- No real certificate files or issued certificates are included.
- No automated backup retention or off-server backup storage is included.
- No monitoring stack is included.
- No migration framework is included.
- No object-storage lifecycle is included.
- No background workers, automatic sending, provider webhooks, public links, uploads, payment links, or airline integrations are included.
