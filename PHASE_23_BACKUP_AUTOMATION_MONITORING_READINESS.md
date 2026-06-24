# Phase 23 Backup Automation And Lightweight Monitoring Readiness

Phase 23 adds production-safe host automation for AeroAssist AgencyOS on the live Hostinger VPS without adding external monitoring SaaS, CI/CD, alerting, public links, payment gateway integration, airline integrations, document upload, CMS publishing, automatic email sending, demo auth, or demo seed.

Current production URL:

```text
https://avio.my
```

Current production architecture:

- Host nginx owns public ports `80` and `443`.
- The AgencyOS frontend container is local-only on `127.0.0.1:8080`.
- The backend and MongoDB are internal Docker Compose services.
- Certbot renewal is managed by `certbot.timer`.
- The previous app under `/opt/aeroassist` is stopped and preserved.

## Scripts Added

Host scripts live under `deploy/hostinger/scripts`.

```bash
deploy/hostinger/scripts/backup_all.sh
deploy/hostinger/scripts/verify_backups.sh
deploy/hostinger/scripts/prune_backups.sh
deploy/hostinger/scripts/healthcheck.sh
deploy/hostinger/scripts/status_full.sh
```

`backup_all.sh` runs the existing MongoDB and document export backup scripts with one shared timestamp, writes under `/var/backups/aeroassist`, fails fast on either backup failure, verifies both backup artifacts and `.sha256` files, and prints only safe summaries.

`verify_backups.sh` finds the latest timestamped MongoDB and document export backups, verifies checksums, reports backup age, fails if the latest MongoDB backup is missing or older than `MAX_MONGO_AGE_HOURS` defaulting to `30`, and treats missing or old document export backups as warnings unless an existing export backup is broken.

`prune_backups.sh` is dry-run by default and only deletes with `--apply`. It refuses to prune outside `/var/backups/aeroassist`, skips non-timestamped directories, and conservatively targets timestamped backup directories older than `RETENTION_DAYS`, defaulting to `30`.

`healthcheck.sh` checks Docker, nginx, certbot renewal timer, Compose service health, canonical public URL behavior, `/api/health`, `/api/readiness`, local-only frontend binding, nginx ownership of public ports, and stopped/preserved old app state.

`status_full.sh` prints a safe operational snapshot: git commit, app health and phase, containers, nginx, certbot timer, disk usage, latest backups, redirect summary, and old app status.

## Manual Commands

Run from `/opt/aeroassist-agencyos` on the VPS:

```bash
deploy/hostinger/scripts/backup_all.sh
deploy/hostinger/scripts/verify_backups.sh
deploy/hostinger/scripts/prune_backups.sh
deploy/hostinger/scripts/prune_backups.sh --apply
deploy/hostinger/scripts/healthcheck.sh
deploy/hostinger/scripts/status_full.sh
```

The scripts support these common overrides:

```bash
APP_DIR=/opt/aeroassist-agencyos
BACKUP_ROOT=/var/backups/aeroassist
MAX_MONGO_AGE_HOURS=30
MAX_EXPORT_AGE_HOURS=30
RETENTION_DAYS=30
APP_BASE_URL=https://avio.my
```

## Systemd Timer Templates

Systemd unit templates live under `deploy/hostinger/systemd`.

```text
aeroassist-backup.service
aeroassist-backup.timer
aeroassist-backup-verify.service
aeroassist-backup-verify.timer
```

Install as root on the VPS:

```bash
sudo cp deploy/hostinger/systemd/aeroassist-backup.service /etc/systemd/system/
sudo cp deploy/hostinger/systemd/aeroassist-backup.timer /etc/systemd/system/
sudo cp deploy/hostinger/systemd/aeroassist-backup-verify.service /etc/systemd/system/
sudo cp deploy/hostinger/systemd/aeroassist-backup-verify.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aeroassist-backup.timer
sudo systemctl enable --now aeroassist-backup-verify.timer
```

Check timers:

```bash
systemctl list-timers 'aeroassist-backup*'
systemctl status aeroassist-backup.timer
systemctl status aeroassist-backup-verify.timer
journalctl -u aeroassist-backup.service --no-pager -n 100
journalctl -u aeroassist-backup-verify.service --no-pager -n 100
```

Disable timers:

```bash
sudo systemctl disable --now aeroassist-backup.timer
sudo systemctl disable --now aeroassist-backup-verify.timer
```

## API Readiness

The API phase label now reports:

```text
phase_23_backup_automation_monitoring_readiness
```

Application readiness does not fail because a host backup is missing. Backup freshness remains a host operations check through `verify_backups.sh`.

## Not Included

- No external monitoring SaaS.
- No alerting integration.
- No CI/CD.
- No automated restore.
- No off-server backup target.
- No old app deletion.
- No demo auth or demo seed.
- No public share links, payment gateway, GDS/NDC/airline integrations, CMS publishing, document upload, or automatic email sending.

## Validation

Local validation covers syntax and static checks only. Live VPS validation must be run on the server because Docker, nginx, certbot, public routing, and `/var/backups/aeroassist` are host-owned operational state.
