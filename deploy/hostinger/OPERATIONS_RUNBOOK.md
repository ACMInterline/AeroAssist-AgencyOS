# AeroAssist Hostinger Operations Runbook

This runbook is for operating the Phase 18 Docker Compose deployment and Phase 23 backup/health readiness assets on a Hostinger managed VPS.

It does not add product functionality, monitoring services, CI/CD, background workers, provider webhooks, public links, uploads, payment links, or airline integrations.

For a controlled pilot release after Phase 56.5.8, follow `PILOT_RELEASE_RUNBOOK.md`. Repository validation, CI, disposable testing, MongoDB migration readiness, and deployed production state are separate evidence scopes. The release gate never deploys or performs the migration.

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
6. Configure distinct MongoDB root and application credentials and keep MongoDB without a host port.
7. For an existing populated volume, complete `MONGODB_DISASTER_RECOVERY_RUNBOOK.md` before enabling authentication.
8. Use `FRONTEND_HTTP_PORT=127.0.0.1:8080` when host nginx terminates TLS.
9. Keep `DEMO_AUTH_ENABLED=false`, `SEED_ON_STARTUP=false`, and `SEED_ENDPOINT_ENABLED=false`.
10. Run `deploy/hostinger/scripts/preflight.sh`.
11. Build and start Compose.
12. Configure host nginx and TLS.
13. Run readiness and smoke checks.

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
deploy/hostinger/scripts/status_full.sh
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

Backend application events use JSON in production and include safe request/correlation IDs, normalized operations, duration, outcome, build phase, and optional deployment identifiers. Uvicorn access logs are disabled to avoid duplicate request telemetry. Never paste raw logs into public issues or artifacts; review access and retention according to the agency's operating policy.

For a manual deployment, `APP_GIT_COMMIT` may contain the short checked-out commit and `APP_DEPLOYMENT_ID` may contain a non-sensitive release label. Neither value may contain credentials or client data. The protected `/api/platform/diagnostics/observability` route provides bounded process-local counters to existing Platform operators; it is not durable monitoring.

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

Backups are timestamped under `/var/backups/aeroassist` by default. Phase 56.5.5 extends the Phase 23 foundation with timestamped MongoDB archive names, SHA-256 checksums, credential-free manifests, collection/document counts, and `mongorestore --dryRun` archive inspection.

Combined MongoDB and document exports:

```bash
deploy/hostinger/scripts/backup_all.sh
```

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
deploy/hostinger/scripts/backup_all.sh
```

Verify backups:

```bash
deploy/hostinger/scripts/verify_backups.sh
```

Preview pruning:

```bash
deploy/hostinger/scripts/prune_backups.sh
```

Apply pruning:

```bash
deploy/hostinger/scripts/prune_backups.sh --apply
```

Configure `BACKUP_RETENTION_DAYS` and `BACKUP_MINIMUM_COUNT`. Unverified sets are skipped, the newest verified set is protected, and the minimum count is retained.

Store off-server copies according to your operational policy. This phase does not add automated remote backup storage.

## Backup Timer

The backup timer is installed by an operator, not by application startup.

```bash
sudo cp deploy/hostinger/systemd/aeroassist-backup.service /etc/systemd/system/
sudo cp deploy/hostinger/systemd/aeroassist-backup.timer /etc/systemd/system/
sudo cp deploy/hostinger/systemd/aeroassist-backup-verify.service /etc/systemd/system/
sudo cp deploy/hostinger/systemd/aeroassist-backup-verify.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aeroassist-backup.timer
sudo systemctl enable --now aeroassist-backup-verify.timer
```

Check status:

```bash
systemctl list-timers 'aeroassist-backup*'
systemctl status aeroassist-backup.timer
systemctl status aeroassist-backup-verify.timer
journalctl -u aeroassist-backup.service --no-pager -n 100
journalctl -u aeroassist-backup-verify.service --no-pager -n 100
```

Disable:

```bash
sudo systemctl disable --now aeroassist-backup.timer
sudo systemctl disable --now aeroassist-backup-verify.timer
```

## Restore

Authentication migration, restore rehearsal, disaster recovery, rollback, credential rotation, document-storage recovery, and full-VPS-loss recovery are documented in:

```text
deploy/hostinger/MONGODB_DISASTER_RECOVERY_RUNBOOK.md
```

High-level process:

1. Announce maintenance window.
2. Take a fresh backup of the current state.
3. Verify checksum, manifest, and archive inspection.
4. Rehearse the selected archive in a disposable MongoDB container and compare counts.
5. Use validation-only restore planning against an explicitly named target.
6. Prefer restore to a new database and validate before cutover.
7. Use the multi-part production confirmation only during an approved recovery operation.
8. Restore document exports separately.
9. Run readiness and smoke checks and have application owners validate business-critical records.

No deployment, application startup, CI workflow, or systemd unit invokes production restore.

## Rollback

Code rollback without data restore:

```bash
cd /opt/aeroassist-agencyos
git log --oneline -10
git checkout <previous-good-commit>
UPDATE_GIT=false deploy/hostinger/scripts/deploy.sh
```

Data rollback should use the restore procedure and only after confirming the selected backup point.

Do not automate destructive rollback. Phase 56.5.5 provides explicit guarded tooling and requires human recovery authorization.

## Health And Readiness

```bash
curl https://avio.my/api/health
curl https://avio.my/api/readiness
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend python scripts/check_production_readiness.py
deploy/hostinger/scripts/healthcheck.sh
deploy/hostinger/scripts/status_full.sh
deploy/hostinger/scripts/check_storage.sh
```

Readiness must not expose secret values.

The Phase 23 healthcheck validates Docker, nginx, `certbot.timer`, Compose service health, canonical `https://avio.my` routing, API health/readiness, local-only frontend binding on `127.0.0.1:8080`, nginx ownership of public ports `80/443`, and the stopped/preserved old app state.

## Document Storage Lifecycle

Phase 25 keeps the local filesystem document export volume as the active storage backend. It adds lifecycle metadata, provider readiness summaries, and a storage check script, but it does not add automatic email sending, public links, object storage uploads, or hard deletion.

Check backend export storage from the host:

```bash
deploy/hostinger/scripts/check_storage.sh
```

In the app, use the agency workspace page:

```text
/agency/document-storage
```

The page and APIs must not expose absolute local filesystem paths or secrets.

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
10. Correlate safe events by request ID, correlation ID, deployment ID, and build phase.
11. Check due-slow and degraded counters through protected Platform diagnostics; remember that counters reset on process restart.

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
- Process counters and timings are non-durable and reset on restart.
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
