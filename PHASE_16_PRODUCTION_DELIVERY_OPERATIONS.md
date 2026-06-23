# Phase 16 Production Delivery Operations And Secret Resolution

## Goal

Make document delivery operations safer for VPS deployment by adding environment-based SMTP secret resolution, staff delivery diagnostics, retry governance, and production configuration checks.

Delivery remains manual and staff-controlled. No public links, client-triggered sending, mass email automation, marketing campaigns, payment links, document upload, electronic signatures, provider webhooks, background workers, airline/GDS/NDC integrations, refund/payment/ticketing execution, or legal/fiscal invoice compliance claims were added.

## Secret Reference Format

SMTP passwords are resolved only from environment-variable references:

- `env:VARIABLE_NAME`

Unsupported schemes fail with a friendly diagnostic. Secret values are never stored in agency email settings, returned by APIs, printed by readiness checks, or seeded.

Example agency email setting:

- `smtp_password_secret_ref=env:AGENCY_SMTP_PASSWORD`

Example environment:

- `AGENCY_SMTP_PASSWORD=replace-with-real-secret-outside-git`

## SMTP Mode Behavior

Email modes remain:

- `disabled`: delivery drafts can exist, but send attempts fail safely.
- `dev_console`: staff-triggered sends are simulated and recorded as sent without real email.
- `smtp`: staff-triggered sends use Python `smtplib` when sender, host, port, username, and `env:` password reference validate.

SMTP sends:

- send exactly one staff-triggered delivery,
- validate the attached generated export before attaching it,
- verify file existence, content type, checksum, file size, document ownership, and agency ownership,
- create a `DocumentDeliveryAttempt`,
- update delivery status, retry status, attempt count, processing state, and lock fields,
- sanitize delivery errors so resolved secrets are not echoed.

## Delivery Diagnostics

Added:

- `GET /api/agencies/{agency_id}/document-deliveries/{delivery_id}/diagnostics`

The endpoint returns staff-safe diagnostics:

- delivery status,
- processing state,
- retry status,
- attempt count and max attempts,
- lock presence,
- attachment validity,
- email mode and validation state,
- masked SMTP secret reference,
- whether the referenced environment secret resolved,
- last safe error,
- next allowed action.

It does not return SMTP passwords, raw secret values, internal snapshots, local paths, storage keys, or provider traces containing secrets.

## Retry Governance

Retry remains staff-controlled.

- `retry` is allowed only when `retry_status=retry_available`.
- `max_retries_reached` returns a specific friendly denial.
- retry creates a new `DocumentDeliveryAttempt`.
- retry/send sets `status=sending`, lock metadata, and `processing_state=processing`.
- sent deliveries clear locks and become terminal sent.
- failed deliveries clear locks and become retryable until max attempts.
- cancelled deliveries clear locks and cannot be sent or retried.

No automatic retry scheduling or worker was added.

## Production Readiness Check

Added:

- `backend/scripts/check_production_readiness.py`

The script checks:

- `AEROASSIST_DB_MODE=mongo`,
- `MONGODB_URL` configured,
- `DEMO_AUTH_ENABLED=false`,
- non-placeholder `AUTH_TOKEN_SECRET`,
- document export storage directory configuration,
- ReportLab capability,
- `CORS_ALLOWED_ORIGINS` for wildcard/local warnings,
- optional `SMTP_SECRET_REFS` environment references.

The script prints warnings/errors and never prints secret values.

## Frontend Changes

Staff document detail now shows:

- delivery diagnostics,
- next allowed action,
- attachment validity,
- masked SMTP secret reference,
- secret configured and resolved booleans,
- explicit copy: `Manual staff-controlled delivery`, `No automatic sending`, and `No public link`.

Send/retry buttons are disabled unless diagnostics say the action is currently allowed.

Portal document detail remains read-only and download-only.

## Seed Data

Seed data remains safe:

- dev-console mode only by default,
- no real SMTP credentials,
- no active SMTP seed,
- idempotent demo exports, deliveries, and attempts.

## Validation

Run for this phase:

- Backend compile.
- Backend import smoke.
- Secret resolver smoke for supported, missing, and unsupported refs.
- SMTP disabled, dev-console, missing-secret, and incomplete-config send smoke.
- Delivery diagnostics smoke.
- Retry governance smoke.
- Attachment validation smoke.
- Production readiness script smoke.
- Seed idempotency smoke.
- Existing backend smoke.
- Existing portal isolation smoke.
- Frontend production build.
- `git diff --check`.

## Remaining Limitations

- No background worker, automatic retry, provider webhook, bounce processing, or delivery monitoring exists.
- SMTP is direct standard-library SMTP, not a provider API integration.
- Local filesystem export storage remains a foundation, not production object-storage lifecycle management.
- No public links, client-triggered sends, payment links, signatures, uploads, airline integrations, or fiscal invoice compliance output exists.
- Formal migrations, broader authorization tests, and deployment hardening remain future work.

## Exact Next Recommended Phase

Phase 17 should be Production Configuration Hardening: centralize production env handling, startup checks, health/readiness reporting, demo/seed gates, CORS, logging, storage path checks, MongoDB config checks, frontend API URL handling, and deployment documentation before adding provider operations or object-storage lifecycle automation.
