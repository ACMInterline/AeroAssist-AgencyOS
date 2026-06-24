# Post-Deployment Security Checklist

Run this after the first deployment and after major operational changes.

## Environment

- `APP_ENV=production`
- `AEROASSIST_DB_MODE=mongo`
- `DEMO_AUTH_ENABLED=false`
- `SEED_ON_STARTUP=false`
- `SEED_ENDPOINT_ENABLED=false`
- `AUTH_TOKEN_SECRET` is not an example placeholder
- `CORS_ALLOWED_ORIGINS` has no wildcard and no localhost values
- `PUBLIC_APP_URL` and `FRONTEND_URL` use the public HTTPS domain
- `FRONTEND_HTTP_PORT=127.0.0.1:8080` when host nginx terminates TLS
- `.env.production` is mode `600` or otherwise not world-readable
- `.env.production` is not committed to git

## Network Exposure

- Host nginx owns public `80/443`
- frontend container is bound to `127.0.0.1:8080`
- backend port `8000` is not publicly exposed
- MongoDB port `27017` is not publicly exposed
- host firewall allows only required SSH/HTTP/HTTPS access

## App Checks

- `/api/health` returns `ok=true`
- `/api/readiness` returns `ok=true`
- readiness output does not include secret values
- API phase reports `phase_27_1_mobility_assistance_logic_request_builder_ux_correction`
- platform login verified
- agency login verified
- portal login verified
- portal cross-client denial verified where test data exists
- document export generation verified
- document export download verified
- SMTP secret references are masked and never display raw secret values

## Staff Invitations

- staff invitation creation returns a one-time acceptance link only to the creator
- staff invitation list does not include raw token or `token_hash`
- invalid invitation token validation fails safely
- pending invitation revoke works
- revoked invitation cannot be accepted
- accepted invitation creates exactly one active staff membership
- audit events do not include raw invitation token or `token_hash`

## Document Storage And Delivery Readiness

- `/api/documents/storage/health` requires auth and returns no absolute local paths
- `/api/documents/storage` returns safe metadata only
- storage archive and mark-missing actions are role-gated
- manual delivery provider is enabled
- automatic email/API/object-storage/webhook providers are disabled or not configured
- no public document links are enabled
- `deploy/hostinger/scripts/check_storage.sh` passes on the VPS

## Data And Storage

- `mongo_data` volume exists
- `document_exports` volume exists
- document exports survive container restart
- MongoDB data survives container restart
- first Mongo backup completed
- first document export backup completed
- backup checksums generated
- `deploy/hostinger/scripts/verify_backups.sh` passes for the latest MongoDB backup
- `deploy/hostinger/scripts/prune_backups.sh` dry-run reviewed before any `--apply`
- off-server copy policy decided

## TLS And Nginx

- nginx config passes `sudo nginx -t`
- TLS certificate issued for the real domain
- `sudo certbot renew --dry-run` passes
- HTTP redirects to HTTPS
- public app loads over HTTPS
- `certbot.timer` is active

## Phase 23 Operations

- `deploy/hostinger/scripts/healthcheck.sh` exits `0`
- `deploy/hostinger/scripts/status_full.sh` prints no secrets
- `aeroassist-backup.timer` installed only after operator approval
- `aeroassist-backup-verify.timer` installed only after operator approval
- `systemctl list-timers 'aeroassist-backup*'` shows expected daily schedule if timers are enabled
- old `/opt/aeroassist` path is preserved and old app containers are stopped

## Repository Hygiene

- `.env.production` is untracked
- `.local/` is untracked
- no real SMTP password appears in repo search
- no production auth secret appears in repo search

Useful checks:

```bash
git status --short
git ls-files .env.production .local
sudo nginx -t
sudo certbot certificates
docker compose --env-file .env.production -f docker-compose.production.yml ps
APP_BASE_URL=https://avio.my deploy/hostinger/scripts/smoke_production.sh
deploy/hostinger/scripts/healthcheck.sh
deploy/hostinger/scripts/verify_backups.sh
deploy/hostinger/scripts/check_storage.sh
```
