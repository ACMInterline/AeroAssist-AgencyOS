# Phase 21 Production Bootstrap And Go-Live Hardening

## Goal

Harden the already deployed Hostinger VPS production path after the first successful AgencyOS deployment.

No product features, public share links, payment gateway integration, airline/GDS/NDC integrations, website/CMS publishing, document upload, automatic sending, provider webhooks, CI/CD, monitoring stack, real secrets, demo seed requirements, or real users in repository code were added.

## Bootstrap Script

Added:

- `backend/scripts/create_first_platform_owner.py`

The script:

- runs inside the backend container,
- connects through the existing backend database layer,
- refuses to run when auth identities already exist unless `--allow-existing-identities` is supplied,
- still refuses duplicate owner emails,
- prompts for owner email, full name, password, and password confirmation,
- does not echo or print the password,
- requires passwords at least 12 characters long,
- creates one `platform_users` document with `global_role=platform_owner`,
- creates one matching `auth_identities` document with `identity_type=platform_user`,
- does not enable seed,
- does not create demo accounts,
- does not modify agencies or workspaces.

Run from the VPS:

```bash
cd /opt/aeroassist-agencyos
docker compose --env-file .env.production -f docker-compose.production.yml exec backend \
  python scripts/create_first_platform_owner.py
```

## Production Demo UI Hiding

The frontend login UI now hides demo account cards and demo credential defaults in production builds.

Production detection uses:

- `import.meta.env.PROD`
- `VITE_APP_ENV=production`

Development builds can still show demo accounts for local convenience.

## Deployment Path Hardening

Hostinger helper script defaults now use:

```text
/opt/aeroassist-agencyos
```

All scripts still support override through `APP_DIR`.

## Real Deployment Notes

Added:

- `deploy/hostinger/REAL_DEPLOYMENT_NOTES.md`

The notes record the verified temporary `:8080` deployment, deployed commit, old-app coexistence, production owner creation, backups, restart persistence, pending VPS reboot, and nginx/TLS migration status without secrets.

## Reboot Procedure

The operations runbook now includes a safe VPS reboot verification procedure:

- confirm backups,
- confirm pre-reboot health,
- reboot only during an approved window,
- reconnect,
- verify Docker/container auto-start,
- verify old app on port `80`,
- verify AgencyOS on port `8080`,
- verify health/readiness and owner login,
- start containers safely if they did not auto-start.

## Nginx/TLS Migration Plan

The deployment and operations docs now describe how to move from temporary `http://72.62.52.129:8080` exposure to a final HTTPS domain while preserving the older app until routing is decided.

## Remaining Limitations

- VPS reboot has not been executed by this repository change.
- Final domain, nginx routing, and TLS are still pending.
- Port `8080` remains temporary until host nginx/TLS migration.
- No backup scheduler, monitoring stack, CI/CD, object storage, migrations, provider webhooks, public links, automatic sending, or demo production seed path was added.

## Exact Next Recommended Step

Perform the pending VPS reboot verification procedure from `deploy/hostinger/OPERATIONS_RUNBOOK.md`, then choose final domain/routing and execute the nginx/TLS migration plan.
