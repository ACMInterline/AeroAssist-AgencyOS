# AeroAssist V1 Production Preflight Report

## Release Identity

| Item | Verified value | Result |
| --- | --- | --- |
| Branch | `v1-integration-program` | PASS |
| Candidate commit | `5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0` | PASS |
| Candidate short commit | `5a557b5f` | PASS |
| Commit subject | `Add V1 pilot acceptance and deployment readiness` | PASS |
| Origin synchronization | `HEAD` and `origin/v1-integration-program` identical; ahead `0`, behind `0` after fetch | PASS |
| Initial worktree | Clean before preflight report generation | PASS |

This is a local repository and packaging assessment only. It did not access a VPS, production service, production database, backup archive, secret store, or production user account. It did not deploy or mutate production.

## Package Findings

| Area | Finding | Result |
| --- | --- | --- |
| Production Compose | `docker-compose.production.yml` renders with `.env.production.example` when `AEROASSIST_ENV_FILE` is explicit. | PASS |
| Backend image | Built from `backend/Dockerfile` and labeled with the full release commit. Runs as non-root user `aeroassist`. | PASS |
| Frontend image | Built from `frontend/Dockerfile` and labeled with the full release commit. Uses the production Vite build and nginx runtime. | PASS WITH WARNING |
| Health checks | MongoDB, backend, and frontend have Compose health checks. Both application images also contain image-level health checks. | PASS |
| Public readiness | Example production configuration uses `READINESS_PUBLIC_MODE=summary`; authenticated detail remains explicit and internal readiness defaults off. | PASS |
| Document persistence | Named volume `document_exports` mounts at `/var/lib/aeroassist/document_exports`; backend image creates and owns that path. | PASS |
| MongoDB persistence | Named volume `mongo_data` mounts at `/data/db`; MongoDB has no published host port. | PASS |
| Environment contract | Required names and safety defaults are present in `.env.production.example` and checked by `preflight.sh`. Real values were not inspected. | PASS WITH OPERATOR ACTION |
| Deployment scripts | All checked-in `.sh` files under `deploy/hostinger/scripts` and `deploy/hostinger/mongodb` pass `bash -n`. | PASS |
| Backup scripts | Combined MongoDB and document backup, checksum, manifest, archive inspection, retention, and verification scripts pass syntax validation. | PASS |
| Restore tooling | Restore defaults to validation-only and requires explicit multi-part authorization for execution. | PASS |
| Rollback | No dedicated rollback script exists. Application rollback is a controlled manual sequence and requires an approved prior commit and compatibility review. | PASS WITH OPERATOR ACTION |
| Persistence governance | Static persistence governance passes with 62 registered collections and 13 governed indexes; automatic index dropping remains prohibited. | PASS |
| Smoke inventory | 143 scripts registered, zero unresolved. | PASS |

## Docker Evidence

- Backend tag: `aeroassist-agencyos-backend:5a557b5f-preflight`
- Backend local manifest-list digest: `sha256:6336864fb883e6c741cd3ac7917f1e9dfd5eb681bf3047b8eb221effab47b3b2`
- Frontend tag: `aeroassist-agencyos-frontend:5a557b5f-preflight`
- Frontend local manifest-list digest: `sha256:9a217a21bdcdfc0ab1beb2728226c4d1fb42d9fe8f4b223ebc3fd3bdd43d20cf`
- Both image configurations contain `org.opencontainers.image.revision=5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0`.

These are local preflight image identities, not registry artifacts or deployed production image IDs.

## Warnings

1. The frontend build succeeds but emits the existing warning that the main minified JavaScript chunk is approximately 2.95 MB. This is not a packaging failure, but should be monitored on pilot devices and slower connections.
2. A manual rollback sequence is documented in `V1_DEPLOYMENT_COMMANDS.md`; there is no checked-in one-command rollback script.
3. Compose image builds resolve mutable upstream image tags (`python:3.12-slim`, `node:20-alpine`, `nginx:1.27-alpine`, and `mongo:7`) to current registry digests at build/pull time. The locally built application images are commit labeled, but the package does not publish an immutable application image to a registry.

## Deployment Blockers

The source package is ready for review, but deployment authorization remains blocked until an authorized operator supplies and verifies all of the following:

1. Production `.env.production` values pass `preflight.sh` without exposing secret values.
2. `APP_GIT_COMMIT` is set to `5a557b5f` or the full release commit, and a unique non-sensitive `APP_DEPLOYMENT_ID` is recorded.
3. The exact rollback commit is selected, reviewed for data compatibility, and recorded before deployment.
4. A current authenticated MongoDB and document-export backup passes checksum, manifest, and archive inspection.
5. The complete verified backup set has an independently verified off-host copy.
6. A disposable restore rehearsal and production tenant-isolation evidence are approved.
7. Required CI jobs for the exact commit and the human pilot release sign-off are verified.
8. VPS preflight, capacity, Docker daemon, nginx/TLS, frontend loopback binding, and host health are verified during the approved maintenance window.

No production deployment was attempted by this preflight.
