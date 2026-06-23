# Phase 20 Hostinger VPS First Deployment Preparation

## Goal

Prepare the repository for the actual first Hostinger VPS deployment by adding a linear first-deployment checklist, post-deployment security checklist, troubleshooting guide, and preflight script.

No product features, public share links, payment gateway integration, airline/GDS/NDC integrations, website/CMS publishing, document upload, background workers, provider webhooks, automatic sending, client-triggered sending, CI/CD, monitoring services, DNS automation, or backup scheduling were added.

## Added Files

- `deploy/hostinger/FIRST_DEPLOYMENT_CHECKLIST.md`
- `deploy/hostinger/POST_DEPLOYMENT_SECURITY_CHECKLIST.md`
- `deploy/hostinger/TROUBLESHOOTING.md`
- `deploy/hostinger/scripts/preflight.sh`

## Preflight Script

`deploy/hostinger/scripts/preflight.sh` checks:

- repository layout,
- `.env.production` presence,
- Docker and Docker Compose command availability,
- required production environment variables without printing values,
- production safety values such as `APP_ENV=production`, `DEMO_AUTH_ENABLED=false`, and seed gates disabled,
- backup directory writability,
- Docker Compose config validity,
- Docker daemon reachability.

It does not start, stop, build, or delete services.

`deploy.sh` now runs preflight by default before git update, build, or start. Set `RUN_PREFLIGHT=false` only for an intentional emergency override.

## First Deployment Checklist

The checklist gives the exact first-run sequence:

1. SSH to VPS.
2. Install prerequisites.
3. Clone repository.
4. Create `.env.production`.
5. Run preflight.
6. Build and start containers.
7. Check local readiness.
8. Configure host nginx and TLS.
9. Run production smoke.
10. Verify logins and document exports.
11. Run first backups.
12. Record deployed commit and image IDs.
13. Follow rollback checklist if needed.

## Security Checklist

The post-deployment checklist covers:

- production env values,
- no demo auth or seed gates,
- strict CORS,
- `.env.production` hygiene,
- frontend/backend/Mongo network exposure,
- login and portal isolation verification,
- readiness secret safety,
- mounted storage and backups,
- TLS/certbot checks.

## Troubleshooting

The troubleshooting guide covers:

- Docker daemon issues,
- port conflicts,
- frontend/backend proxy failures,
- CORS failures,
- Mongo connection failures,
- storage path readiness failures,
- ReportLab/PDF issues,
- SMTP secret refs,
- nginx config failures,
- certbot DNS issues,
- document export volume/download failures.

## Remaining Limitations

- No actual server deployment was performed.
- No real domains or secrets were added.
- No live certificate issuance was performed.
- No backup scheduler or retention automation was added.
- No monitoring stack, CI/CD, DNS automation, migrations, object storage, workers, provider webhooks, public links, or automatic sending were added.

## Exact Next Recommended Phase

Phase 21 should be Production Bootstrap And Go-Live Hardening: add an official first-owner bootstrap script, hide production demo UI affordances, record the real temporary deployment state, harden the real deployment path defaults, and document the pending VPS reboot plus nginx/TLS migration plan.
