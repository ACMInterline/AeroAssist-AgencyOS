# Phase 19 VPS Reverse Proxy, TLS, Backup, And Operations Runbook

## Goal

Prepare server-side deployment assets and operational runbooks for Hostinger managed VPS deployment on top of the Phase 18 Docker Compose packaging.

No product features, public share links, payment gateway integration, airline/GDS/NDC integrations, website/CMS publishing, document upload, background workers, provider webhooks, automatic sending, client-triggered sending, monitoring stack services, or CI/CD automation were added.

## Added Files

- `deploy/hostinger/nginx/aeroassist.conf.example`
- `deploy/hostinger/scripts/deploy.sh`
- `deploy/hostinger/scripts/restart.sh`
- `deploy/hostinger/scripts/status.sh`
- `deploy/hostinger/scripts/logs.sh`
- `deploy/hostinger/scripts/backup_mongo.sh`
- `deploy/hostinger/scripts/backup_exports.sh`
- `deploy/hostinger/scripts/restore_mongo.md`
- `deploy/hostinger/scripts/smoke_production.sh`
- `deploy/hostinger/OPERATIONS_RUNBOOK.md`

## Reverse Proxy Approach

The preferred production mode is:

- host nginx owns ports `80` and `443`,
- Docker frontend binds to `127.0.0.1:8080`,
- host nginx proxies to the frontend container,
- frontend nginx proxies `/api` to the backend container internally.

The nginx template includes:

- HTTP to HTTPS redirect,
- certbot certificate placeholders,
- safe baseline headers,
- 10 MB request size limit,
- frontend proxy,
- commented optional direct backend `/api` proxy.

No real domain or certificate paths are committed.

## Backup Approach

Backups are safe templates and never delete old backups automatically.

- MongoDB backup uses `mongodump --archive --gzip` inside the `mongo` container.
- Document export backup uses `tar` inside the `backend` container from `/var/lib/aeroassist/document_exports`.
- Backups are timestamped under `/var/backups/aeroassist` by default.
- SHA-256 checksum files are written next to each backup artifact.

## Restore Approach

Restore remains a manual documented procedure in `restore_mongo.md` because it can overwrite data.

The guide requires:

- maintenance window,
- checksum verification,
- fresh pre-restore backup,
- explicit `mongorestore --drop`,
- document export tar restore,
- readiness and smoke validation.

## Deployment And Rollback

`deploy.sh` wraps:

- `.env.production` verification,
- optional `git pull --ff-only`,
- Compose config validation,
- image build,
- service startup,
- backend production readiness check,
- optional production smoke test.

Rollback is documented as a manual checkout of a previous known-good commit followed by rebuild/restart. Data restore remains separate.

## Production Smoke Test

`smoke_production.sh` checks:

- frontend root,
- `/api/health`,
- `/api/readiness`,
- no obvious secret-value placeholders in readiness output,
- `/api/auth/login` reachable and rejecting fake credentials.

It does not use real credentials and does not send email.

## Remaining Limitations

- No automated DNS setup.
- No real certificate issuance in the repo.
- No automated backup retention or off-server storage.
- No monitoring stack or alerting service.
- No CI/CD deployment automation.
- No Kubernetes.
- No object storage.
- No migrations framework.
- No background workers, provider webhooks, public links, client-triggered sending, or automatic sending.

## Exact Next Recommended Phase

Phase 20 should be Hostinger VPS First Deployment Preparation: add the final first-run checklist, preflight validation, environment checklist, real-server smoke checklist, rollback checklist, post-deployment security checklist, and troubleshooting guide before the actual first VPS deployment.
