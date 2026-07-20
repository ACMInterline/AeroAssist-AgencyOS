# AeroAssist V1 Environment Variable Checklist

## Release Binding

- [ ] `APP_GIT_COMMIT=5a557b5f` or `APP_GIT_COMMIT=5a557b5fa3d3a057e358bbe45bedd24ab1d38cc0`
- [ ] `APP_DEPLOYMENT_ID` is a unique, non-sensitive pilot deployment identifier.
- [ ] The secure production environment file is outside Git history and has restricted filesystem permissions.
- [ ] No value contains passenger data, payment data, raw logs, or private evidence.

## Application Safety

- [ ] `APP_ENV=production`
- [ ] `AEROASSIST_DB_MODE=mongo`
- [ ] `DEMO_AUTH_ENABLED=false`
- [ ] `SEED_ON_STARTUP=false`
- [ ] `SEED_ENDPOINT_ENABLED=false`
- [ ] `AUTH_TOKEN_SECRET` is random, non-placeholder, securely stored, and rotated through an approved process.

## MongoDB

- [ ] `MONGO_AUTHENTICATION_ENABLED=true` only after the existing-volume migration runbook is complete.
- [ ] `MONGO_INITDB_ROOT_USERNAME` is set to the approved administrative identity.
- [ ] `MONGO_INITDB_ROOT_PASSWORD` is non-placeholder and at least 16 characters.
- [ ] `MONGO_APP_USERNAME` is a distinct least-privilege application identity.
- [ ] `MONGO_APP_PASSWORD` is non-placeholder and at least 16 characters.
- [ ] `MONGO_AUTH_SOURCE=admin` or the reviewed authentication database.
- [ ] `MONGO_DATABASE` and `MONGODB_DATABASE` identify the intended production database consistently.
- [ ] `MONGO_HOST=mongo` and `MONGO_PORT=27017` for the production Compose network.
- [ ] `MONGODB_URL` is blank unless an approved authenticated URI override is required.
- [ ] MongoDB has no host port published.

## Persistent Storage And Backup

- [ ] `DOCUMENT_EXPORT_STORAGE_DIR=/var/lib/aeroassist/document_exports`
- [ ] The `document_exports` named volume is mounted and included in backups.
- [ ] The `mongo_data` named volume is mounted at `/data/db`.
- [ ] `BACKUP_ROOT=/var/backups/aeroassist` is writable only by approved operators.
- [ ] `BACKUP_RETENTION_DAYS` is an integer of at least 1; recommended value is 30.
- [ ] `BACKUP_MINIMUM_COUNT` is an integer of at least 1; recommended value is 7.
- [ ] `BACKUP_ENVIRONMENT_LABEL=production`
- [ ] Off-host destination, access control, encryption, and retention are approved outside this file.

## URLs, CORS, And Frontend

- [ ] `PUBLIC_APP_URL` is the approved HTTPS canonical origin.
- [ ] `FRONTEND_URL` is the approved HTTPS frontend origin.
- [ ] `CORS_ALLOWED_ORIGINS` contains only approved HTTPS origins, with no wildcard or local address.
- [ ] `FRONTEND_HTTP_PORT=127.0.0.1:8080` when host nginx terminates TLS.
- [ ] `VITE_API_BASE_URL` is blank for same-origin nginx proxying or is the reviewed HTTPS backend origin.
- [ ] `VITE_APP_ENV=production`

## Readiness And Query Safety

- [ ] `READINESS_PUBLIC_MODE=summary`
- [ ] `READINESS_AUTHENTICATED_DETAIL_ENABLED=true` only for authorized authenticated detail.
- [ ] `READINESS_INTERNAL_ENABLED=false` unless explicitly approved.
- [ ] `READINESS_INTERNAL_KEY` is blank when internal readiness is disabled; otherwise it is a protected random value of at least 24 characters.
- [ ] `READINESS_DATABASE_TIMEOUT_SECONDS=5` or another reviewed bounded timeout.
- [ ] `QUERY_DEFAULT_LIMIT=50`
- [ ] `QUERY_MAXIMUM_LIMIT=250`
- [ ] `QUERY_SLOW_THRESHOLD_MS=250`
- [ ] `QUERY_DIAGNOSTICS_ENABLED=true`

## Authentication Controls

- [ ] `TOKEN_EXPIRY_MINUTES=720` or the approved policy value.
- [ ] `TOKEN_CLOCK_SKEW_SECONDS=30`
- [ ] `TOKEN_REFRESH_POLICY=disabled` unless a reviewed policy is implemented.
- [ ] `TOKEN_REFRESH_WINDOW_MINUTES=60`
- [ ] `LOGIN_THROTTLE_ENABLED=true`
- [ ] `LOGIN_MAX_ATTEMPTS=5`
- [ ] `LOGIN_LOCK_DURATION_SECONDS=900`
- [ ] `LOGIN_FAILURE_RESET_SECONDS=900`
- [ ] `LOGIN_BACKOFF_BASE_SECONDS=0.1`
- [ ] `LOGIN_BACKOFF_MAX_SECONDS=2.0`
- [ ] `INVITATION_EXPIRY_HOURS=72`
- [ ] `PASSWORD_RESET_EXPIRY_HOURS=2`

## HTTP Security

- [ ] `SECURITY_HEADERS_ENABLED=true`
- [ ] `SECURITY_HSTS_ENABLED=true`
- [ ] `SECURITY_HSTS_MAX_AGE_SECONDS=31536000`
- [ ] `SECURITY_HSTS_INCLUDE_SUBDOMAINS=true` only after all subdomains are HTTPS ready.
- [ ] `SECURITY_HSTS_PRELOAD=false` unless preload is independently approved.
- [ ] `SECURITY_FRAME_OPTIONS=DENY`
- [ ] `SECURITY_REFERRER_POLICY=no-referrer`
- [ ] `SECURITY_PERMISSIONS_POLICY` retains restrictive camera, microphone, geolocation, payment, and USB settings.
- [ ] Cross-origin resource, opener, and embedder policy values match the reviewed deployment architecture.
- [ ] `SECURITY_CONTENT_SECURITY_POLICY` is blank for the generated policy or contains a reviewed policy compatible with required assets.

## Logging And Diagnostics

- [ ] `LOG_LEVEL=INFO`
- [ ] `LOG_FORMAT=json`
- [ ] `LOG_SERVICE_NAME=aeroassist-agencyos-api`
- [ ] `LOG_INCLUDE_REQUEST_PATH=true`
- [ ] `LOG_INCLUDE_QUERY_NAMES=true`
- [ ] Slow-operation thresholds are reviewed for requests, readiness, startup, and document rendering.
- [ ] `LOG_ERROR_STACKTRACES=false`
- [ ] `LOG_HASH_TENANT_IDENTIFIERS=true`
- [ ] `LOG_REQUEST_TELEMETRY_ENABLED=true`
- [ ] `LOG_REDACTION_ENABLED=true`
- [ ] Docker JSON logging remains bounded by size and file count.

## Optional SMTP References

- [ ] `AEROASSIST_SMTP_PASSWORD` is blank unless SMTP is explicitly configured.
- [ ] `SMTP_SECRET_REFS` contains only reviewed `env:` references and never raw passwords.
- [ ] SMTP configuration does not imply automatic message sending or pilot approval.

## Operator Verification

Run from the VPS repository root without printing the environment file:

```bash
APP_DIR=/opt/aeroassist-agencyos \
ENV_FILE=.env.production \
COMPOSE_FILE=docker-compose.production.yml \
deploy/hostinger/scripts/preflight.sh
```

Do not use `.env.production.example` for deployment. It intentionally contains placeholders.
