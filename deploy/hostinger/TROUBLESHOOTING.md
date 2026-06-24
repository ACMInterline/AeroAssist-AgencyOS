# Hostinger VPS Troubleshooting

## Docker Daemon Not Running

Symptoms:

- `Cannot connect to the Docker daemon`
- `docker info` fails

Inspect:

```bash
sudo systemctl status docker
docker info
groups
```

Likely fix:

```bash
sudo systemctl start docker
sudo usermod -aG docker "$USER"
```

Log out and back in after changing groups.

## Port 80 Or 443 Conflict

Symptoms:

- nginx fails to start
- Docker cannot bind port
- certbot cannot bind HTTP challenge

Inspect:

```bash
sudo ss -tulpn | grep -E ':80|:443'
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

Likely fix:

- Use `FRONTEND_HTTP_PORT=127.0.0.1:8080` with host nginx.
- Stop any old web server using `80/443`.
- Keep Docker frontend off public `80` when host nginx owns TLS.

## Frontend Cannot Reach Backend

Symptoms:

- frontend loads but API calls fail
- `/api/health` through the domain fails

Inspect:

```bash
curl http://127.0.0.1:8080/api/health
docker compose --env-file .env.production -f docker-compose.production.yml logs frontend
docker compose --env-file .env.production -f docker-compose.production.yml logs backend
```

Likely fix:

- Keep `VITE_API_BASE_URL=` blank for same-origin mode.
- Confirm frontend nginx proxies `/api` to `backend:8000`.
- Confirm backend service is healthy.

## CORS Failure

Symptoms:

- browser console reports CORS errors
- API works with curl but not from browser

Inspect:

```bash
grep CORS_ALLOWED_ORIGINS .env.production
curl -I https://your-domain.example/api/health
```

Likely fix:

- Set `CORS_ALLOWED_ORIGINS=https://your-domain.example`.
- Do not use wildcard or localhost in production.
- Recreate backend after env changes:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d --build backend
```

## Mongo Connection Failure

Symptoms:

- backend fails startup
- readiness database check fails

Inspect:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml ps
docker compose --env-file .env.production -f docker-compose.production.yml logs mongo
docker compose --env-file .env.production -f docker-compose.production.yml logs backend
```

Likely fix:

- Use `MONGODB_URL=mongodb://mongo:27017` for bundled Mongo.
- Confirm Mongo healthcheck passes.
- Confirm the `mongo_data` volume is present.

## Readiness Fails Due To Storage Path

Symptoms:

- `/api/readiness` reports storage not writable
- document export generation fails

Inspect:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend \
  sh -c 'id && ls -ld /var/lib/aeroassist /var/lib/aeroassist/document_exports && touch /var/lib/aeroassist/document_exports/.write-test'
```

Likely fix:

- Ensure `DOCUMENT_EXPORT_STORAGE_DIR=/var/lib/aeroassist/document_exports`.
- Recreate the backend container so the named volume mounts correctly.

## ReportLab Or PDF Capability Issue

Symptoms:

- PDF capability reports unavailable
- PDF export fails

Inspect:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend \
  python - <<'PY'
from services.pdf_rendering_service import pdf_capabilities
print(pdf_capabilities())
PY
```

Likely fix:

- Rebuild backend image.
- Confirm `reportlab>=4.2,<5` installed from `backend/requirements.txt`.

## SMTP Secret Missing

Symptoms:

- delivery diagnostics show secret reference missing
- readiness warns or fails for SMTP refs

Inspect:

```bash
grep SMTP_SECRET_REFS .env.production
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend \
  python scripts/check_production_readiness.py
```

Likely fix:

- Set the SMTP password as an environment variable in `.env.production`.
- Use agency setting `smtp_password_secret_ref=env:VARIABLE_NAME`.
- Never store raw SMTP passwords in agency settings.

## Nginx Config Test Fails

Symptoms:

- `sudo nginx -t` fails

Inspect:

```bash
sudo nginx -t
sudo journalctl -u nginx --no-pager -n 100
```

Likely fix:

- Replace all placeholder domains.
- Ensure certificate paths exist after certbot issuance.
- Remove duplicate `server_name` conflicts.

## Certbot Fails

Symptoms:

- HTTP-01 challenge fails
- domain validation fails

Inspect:

```bash
dig +short your-domain.example
curl -I http://your-domain.example/.well-known/acme-challenge/test
sudo certbot certificates
```

Likely fix:

- Point DNS A record to the VPS IP.
- Wait for DNS propagation.
- Ensure port `80` reaches host nginx.
- Run `sudo nginx -t` before certbot.

## Document Export Download Fails

Symptoms:

- generated export exists in database but download fails
- checksum or file missing errors

Inspect:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec -T backend \
  find /var/lib/aeroassist/document_exports -maxdepth 3 -type f | head
docker compose --env-file .env.production -f docker-compose.production.yml logs backend
```

Likely fix:

- Confirm `document_exports` named volume is mounted.
- Confirm export files were not lost during container rebuild.
- Restore from `backup_exports.sh` output if needed.

## Backup Verification Fails

Symptoms:

- `verify_backups.sh` reports missing MongoDB backup
- checksum verification fails
- latest MongoDB backup is older than the configured threshold

Inspect:

```bash
sudo ls -la /var/backups/aeroassist
sudo find /var/backups/aeroassist -maxdepth 2 -type f | sort | tail -20
deploy/hostinger/scripts/verify_backups.sh
journalctl -u aeroassist-backup.service --no-pager -n 100
```

Likely fix:

- Run `deploy/hostinger/scripts/backup_all.sh` manually.
- Confirm `/var/backups/aeroassist` is writable by root.
- Confirm Docker Compose services are healthy before the backup.
- Do not delete or edit backup artifacts manually unless a restore plan exists.

## Backup Timer Does Not Run

Symptoms:

- no new timestamped backup directory appears
- `systemctl list-timers 'aeroassist-backup*'` does not show the timer

Inspect:

```bash
systemctl status aeroassist-backup.timer
systemctl status aeroassist-backup.service
journalctl -u aeroassist-backup.service --no-pager -n 100
```

Likely fix:

- Reinstall the unit files from `deploy/hostinger/systemd`.
- Run `sudo systemctl daemon-reload`.
- Enable the timer with `sudo systemctl enable --now aeroassist-backup.timer`.
- Keep unit files root-owned and free of secrets.

## Healthcheck Fails

Symptoms:

- `healthcheck.sh` exits nonzero
- public canonical URL or API readiness fails
- frontend is not bound to `127.0.0.1:8080`

Inspect:

```bash
deploy/hostinger/scripts/healthcheck.sh
deploy/hostinger/scripts/status_full.sh
sudo ss -tulpn | grep -E ':80|:443|:8080'
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

Likely fix:

- Confirm nginx owns public ports `80/443`.
- Confirm `FRONTEND_HTTP_PORT=127.0.0.1:8080`.
- Restart Docker Compose services if any are unhealthy.
- Restart nginx only after `sudo nginx -t` passes.
