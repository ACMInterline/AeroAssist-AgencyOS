# AeroAssist V1 Deployment Readiness Report

## Decision

**Repository candidate: READY FOR CONTROLLED REVIEW**

**Pilot deployment authorization: BLOCKED pending external evidence and human sign-off**

This report evaluates branch `v1-integration-program` at baseline `46990a88`. No production access, deployment, backup, restore, provider execution, payment execution, or data migration was performed.

## Pilot Acceptance

- The canonical workflow is executable through persisted application services from Client context through After Sales.
- Canonical UI routes and continuity controls exist for every step.
- The EMD detail continuity gap found during this audit was corrected.
- The persisted pilot acceptance smoke passes all six required scenarios.
- Interactive visual acceptance remains unsigned because an interactive browser runtime was unavailable in the audit environment.

## Packaging Assessment

| Area | Result | Evidence / requirement |
| --- | --- | --- |
| Production Compose | PASS | `docker-compose.production.yml` renders with `.env.production.example` and `AEROASSIST_ENV_FILE=.env.production.example`. |
| Backend package | PASS | Python compilation and smoke inventory validations are required in the final validation record. |
| Frontend package | PASS | Vite production build is required in the final validation record; frontend container has a health check. |
| Environment contract | PASS WITH OPERATOR ACTION | `.env.production.example` enumerates Mongo authentication, auth secret, CORS, public URLs, logging, readiness and storage settings. Placeholders must be replaced outside Git. |
| Database startup | PASS | MongoDB uses a persistent volume. Startup index governance is additive and rejects incompatible destructive changes. |
| Health / readiness | PASS | Backend health reports the current phase; Compose checks backend and frontend health; public readiness remains bounded. |
| Document storage | PASS WITH OPERATOR ACTION | `document_exports` is a named persistent volume at `/var/lib/aeroassist/document_exports`; backup and restore coverage must be verified on the target host. |
| Backups | BLOCKED UNTIL EVIDENCED | MongoDB and document-export scripts, manifests and verification tooling exist. A current authenticated backup, checksum, manifest and off-host copy must be recorded. |
| Restore | BLOCKED UNTIL REHEARSED | Guarded restore tooling and runbooks exist. A disposable restore rehearsal must pass before pilot approval. |
| Rollback | PASS WITH OPERATOR ACTION | Code/config rollback is documented; the exact rollback commit and compatibility decision must be approved before deployment. |
| Tenant isolation | PASS IN AUTOMATION | Persisted acceptance and existing smokes reject cross-agency reads/mutations. Pilot evidence still requires an operator-reviewed synthetic boundary check. |

## Required Environment Controls

Before deployment, an authorized operator must verify:

- `APP_ENV=production` and `AEROASSIST_DB_MODE=mongo`.
- MongoDB root and application credentials are distinct, non-placeholder secrets.
- `AUTH_TOKEN_SECRET` is non-placeholder and stored outside source control.
- `DEMO_AUTH_ENABLED=false`, `SEED_ON_STARTUP=false`, and `SEED_ENDPOINT_ENABLED=false`.
- CORS and public URLs use the approved HTTPS origin and contain no local/wildcard values.
- authenticated MongoDB migration for an existing volume has been completed according to the runbook.
- `DOCUMENT_EXPORT_STORAGE_DIR` is mounted persistently and included in backups.
- `READINESS_PUBLIC_MODE=summary`; internal readiness and protected diagnostics remain authorized.
- backup destination capacity, retention, encryption/access controls, and off-host copy are approved.

## Remaining Deployment Blockers

1. Human browser acceptance in `V1_PILOT_ACCEPTANCE_CHECKLIST.md` is not signed.
2. Exact candidate commit and rollback commit/reference are not approved.
3. CI status for the exact candidate commit has not been recorded as reviewed evidence.
4. Target-host production environment and Docker daemon preflight have not been run.
5. Authenticated production backup, checksum, manifest, off-host copy and restore rehearsal evidence are absent.
6. Production tenant-isolation evidence and synthetic fixture cleanup evidence are absent.
7. The 24-dimension release assessment and authorized human pilot sign-off remain intentionally external to this repository audit.

No deployment should begin while any blocker remains.
