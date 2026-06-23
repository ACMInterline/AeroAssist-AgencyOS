# Phase 17 Production Configuration Hardening

## Goal

Prepare AeroAssist AgencyOS for safer Hostinger/VPS deployment by hardening environment handling, startup checks, demo/seed gates, readiness reporting, CORS, logging, storage checks, MongoDB configuration, frontend API URL handling, and deployment documentation.

No new business workflow modules, public links, uploads, payment gateway integration, airline/GDS/NDC integrations, provider webhooks, background workers, automatic sending, or client-triggered sending were added.

## Config Service

Added `backend/config.py` as the central source for:

- `APP_ENV`
- `AEROASSIST_DB_MODE`
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `DEMO_AUTH_ENABLED`
- `SEED_ON_STARTUP`
- `SEED_ENDPOINT_ENABLED`
- `AUTH_TOKEN_SECRET`
- token/invitation expiry values
- `DOCUMENT_EXPORT_STORAGE_DIR`
- `CORS_ALLOWED_ORIGINS`
- `LOG_LEVEL`
- `FRONTEND_URL`
- `PUBLIC_APP_URL`
- `SMTP_SECRET_REFS`

Production defaults are conservative: demo auth, startup seeding, and the seed endpoint default to disabled when `APP_ENV=production`.

## Startup Safety

Startup now validates configuration before connecting the database. In production, critical failures raise a startup error:

- memory database mode,
- missing MongoDB configuration,
- demo auth enabled,
- startup seed enabled,
- seed endpoint enabled,
- placeholder auth secret,
- wildcard or local CORS origin,
- unwritable document export storage.

Development remains non-blocking except for ordinary runtime failures. Local demo behavior remains available with `APP_ENV=development`.

## Health And Readiness

Added or improved:

- `GET /api/health`
- `GET /api/readiness`
- `GET /api/platform/health`

Health is lightweight and returns app status, environment, and phase metadata.

Readiness returns safe summaries for:

- app env and phase,
- config pass/warn/fail checks,
- database connectivity,
- document export storage writability,
- PDF capability,
- SMTP secret reference diagnostics.

Readiness never returns secret values, raw storage keys, document snapshots, local file paths, or SMTP passwords.

## Demo And Seed Gating

Production should not create demo data implicitly.

- Startup seed runs only when `SEED_ON_STARTUP=true`.
- `SEED_ON_STARTUP` defaults false in production.
- `/api/reference/seed` requires platform owner/admin context and is disabled unless `SEED_ENDPOINT_ENABLED=true`.
- `SEED_ENDPOINT_ENABLED` defaults false in production.
- Demo header auth defaults false in production.
- Development invitation responses still return raw dev invitation tokens only when demo auth is enabled and the app is not production.

First production platform-owner setup should be handled by a controlled maintenance task or one-off administrative process, not by exposing demo seed data.

## Frontend API URL Handling

`frontend/src/lib/api.js` now uses:

- `VITE_API_BASE_URL` when configured,
- `http://localhost:8000` only for development fallback,
- same-origin `/api` calls for production builds without `VITE_API_BASE_URL`.

Documented frontend envs:

- `VITE_API_BASE_URL`
- `VITE_APP_ENV`

## Production Readiness Script

`backend/scripts/check_production_readiness.py` now uses the same config service as runtime startup/readiness checks.

It prints `PASS`, `WARN`, `FAIL`, and `INFO` lines for:

- app env,
- MongoDB mode and URI presence,
- database name,
- demo auth,
- startup seed,
- seed endpoint,
- auth token secret,
- CORS,
- document export storage writability,
- logging level,
- ReportLab/PDF capability,
- SMTP secret refs,
- frontend/public URL notes.

When `APP_ENV=production`, critical failures return a nonzero exit code. Secret values are never printed.

## Environment Examples

Updated `.env.example` for local development and added `.env.production.example` for VPS-style production configuration.

Recommended production posture:

- `APP_ENV=production`
- `AEROASSIST_DB_MODE=mongo`
- `DEMO_AUTH_ENABLED=false`
- `SEED_ON_STARTUP=false`
- `SEED_ENDPOINT_ENABLED=false`
- explicit `DOCUMENT_EXPORT_STORAGE_DIR`
- strict `CORS_ALLOWED_ORIGINS`
- non-placeholder `AUTH_TOKEN_SECRET`
- SMTP passwords supplied only through environment variables and referenced as `env:VARIABLE_NAME`

## Remaining Limitations

- No Docker packaging or deployment script exists yet.
- No nginx, TLS, public domain, backup, or monitoring configuration was added.
- No migration framework was added.
- No background worker, automatic send, provider webhook, bounce processing, public link, payment link, upload, signature, airline integration, or fiscal invoice compliance output exists.
- Local filesystem export storage remains the default storage foundation.

## Exact Next Recommended Phase

Phase 18 should be Docker And Hostinger VPS Packaging: add backend/frontend Dockerfiles, production Docker Compose, mounted document-export storage, health checks, production env alignment, and a Hostinger VPS deployment runbook before adding provider operations or object-storage lifecycle automation.
