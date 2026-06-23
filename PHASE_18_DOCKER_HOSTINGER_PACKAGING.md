# Phase 18 Docker And Hostinger VPS Packaging

## Goal

Package AeroAssist AgencyOS for a Hostinger managed VPS with Docker Compose while preserving the Phase 17 production configuration hardening.

No business workflows, public links, document upload, payment gateway integration, airline/GDS/NDC integration, website/CMS publishing, background workers, provider webhooks, automatic sending, client-triggered sending, monitoring stack, or backup automation were added.

## Added Packaging

Root:

- `docker-compose.production.yml`
- `.dockerignore`
- `.env.production.example` alignment
- `DEPLOYMENT_HOSTINGER_VPS.md`

Backend:

- `backend/Dockerfile`
- `backend/.dockerignore`

Frontend:

- `frontend/Dockerfile`
- `frontend/.dockerignore`
- `frontend/nginx.conf`

## Docker Architecture

The production compose file defines:

- `frontend`: nginx static frontend on public port `80`.
- `backend`: FastAPI/Uvicorn service on internal port `8000`.
- `mongo`: MongoDB 7 with persistent data volume.

The frontend nginx config proxies `/api/` to `http://backend:8000/api/`, so the default deployment can leave `VITE_API_BASE_URL` blank and use same-origin API calls.

## Volumes

Persistent named volumes:

- `mongo_data` for MongoDB data.
- `document_exports` mounted to `/var/lib/aeroassist/document_exports` in the backend.

`DOCUMENT_EXPORT_STORAGE_DIR` is set to `/var/lib/aeroassist/document_exports` for containers, matching Phase 17 startup/readiness checks.

## Health Checks

Compose health checks cover:

- MongoDB ping.
- Backend `/api/health`.
- Frontend nginx root.

The backend still exposes `/api/readiness` for deeper config, database, storage, PDF, and delivery diagnostics.

## Env Behavior

`.env.production.example` documents production values and Compose defaults:

- `APP_ENV=production`
- `AEROASSIST_DB_MODE=mongo`
- `MONGODB_URL=mongodb://mongo:27017`
- `DEMO_AUTH_ENABLED=false`
- `SEED_ON_STARTUP=false`
- `SEED_ENDPOINT_ENABLED=false`
- explicit mounted export path
- strict CORS/public frontend URL values
- optional SMTP env secret references

No real secrets are committed.

## Validation

Recommended validation:

- backend Python compile,
- backend import smoke,
- production readiness script with production-like fake env,
- frontend production build,
- `docker compose --env-file .env.production.example -f docker-compose.production.yml config`,
- backend Docker build,
- frontend Docker build,
- `git diff --check`.

## Remaining Limitations

- No TLS certificate automation.
- No host-level nginx reverse proxy or domain/DNS setup.
- No backup automation.
- No monitoring stack.
- No CI/CD pipeline.
- No Kubernetes.
- No object storage or lifecycle cleanup automation.
- No migrations framework.

## Exact Next Recommended Phase

Phase 19 should be VPS Reverse Proxy, TLS, Backup, And Operations Runbook: add host-level TLS/domain guidance, backup/restore procedures, operational log review, and update/rollback runbooks before adding provider webhooks, workers, public links, or object-storage lifecycle automation.
