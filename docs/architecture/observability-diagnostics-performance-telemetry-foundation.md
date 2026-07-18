# Observability, Diagnostics, and Performance Telemetry Foundation

## Scope

Phase 56.5.7 establishes privacy-safe process observability for the existing FastAPI, MongoDB, and Docker architecture. Its active marker is `phase_56_5_7_observability_diagnostics_performance_telemetry_foundation`.

This is infrastructure only. It adds no Agency product workflow, provider connection, AI, payment, booking execution, ticketing execution, background worker, data migration, production operation, or external telemetry service.

## Pre-Change Inventory

Before this phase:

- Phase 56.5.4 generated one request/correlation identifier and safe JSON error responses.
- Security events used a separate small JSON payload rather than a shared application envelope.
- Phase 56.5.6 captured bounded query diagnostics, but request context and application counters were not shared.
- Root logging used Python's basic human-readable formatter.
- HTTP duration, response status-class counters, readiness timings, startup duration, and shutdown events were absent.
- Public readiness was already lightweight and detailed readiness was bounded, but operators had no cached aggregate telemetry view.
- Uvicorn access logging could duplicate request telemetry and include uncontrolled URL detail.
- Docker Compose did not define bounded local log-file rotation.

The production backend scan found no broad application `print()` calls or request/response body logging. Script output remains an explicit command-line exception and is outside the application logging path.

## Canonical Event Envelope

`backend/observability.py` owns the canonical envelope:

- UTC timestamp;
- level and stable event type;
- service and environment;
- current build phase;
- optional safe deployment identifiers;
- request and correlation IDs;
- tenant scope category;
- optional HMAC-derived agency identifier hash;
- normalized operation;
- duration;
- outcome;
- allowlisted metadata.

Event metadata is structural. It does not include request or response bodies, raw filters, collection documents, free-text client notes, authentication values, passenger identity, or medical, passport, document, payment, email, or phone values.

## Logging Formats

`LOG_FORMAT=json` is required in production. Development may use `LOG_FORMAT=human`. Both formats are generated from the same structured event object and use UTC timestamps. Logs are written to stdout for container collection; the application does not create files or rotate logs.

Unstructured library messages are represented by a generic suppressed-message event. Uvicorn access logging is disabled in the production image because the canonical HTTP middleware owns request completion telemetry.

## Correlation and HTTP Telemetry

`SecurityHttpMiddleware` remains the single request/security middleware. It now maintains separate `X-Request-ID` and `X-Correlation-ID` values while preserving the existing request-ID contract.

Each completed request can emit one event with method, normalized route template, status class/code, safe content length, authentication-state category, duration, outcome, and slow flag. Query strings, headers, bodies, response content, IP addresses, and user-agent strings are not logged. Health and readiness successes use debug level to reduce routine noise; failures and slow probes remain visible.

When FastAPI route templates are unavailable, known resource identifiers and high-entropy path segments are normalized before logging.

## Error and Security Telemetry

Validation, authentication, authorization, not-found, conflict, rate-limit, database, timeout, and unexpected failures use stable event types and safe metadata. Exception class may be recorded, but exception values are not copied blindly.

Existing client responses retain `detail`, the Phase 56.5.4 `error` object, status codes, and request IDs. Observability does not redesign authentication or authorization.

Authentication events reuse the canonical envelope for successful login, failed login, temporary lock, invalid token, permission denial, and rejected CORS origin. Identity IDs, session IDs, submitted credentials, token values, full email addresses, IP addresses, and user-agent values are excluded.

## Query Telemetry Reuse

Phase 56.5.6 `record_query_diagnostic` remains the query telemetry source. It now emits the canonical event and automatically inherits request correlation.

Permitted fields are collection ownership category, operation class, duration, limit, returned count, tenant-scoped flag, governed query class, index classification, and slow state. Filters, records, tenant IDs, and aggregate results remain excluded. Query diagnostics keep their bounded 100-record compatibility buffer.

## Performance Thresholds

Configuration provides warning thresholds for:

- HTTP requests;
- database queries;
- readiness sections;
- startup;
- document rendering when a governed timing integration is added.

Threshold crossings produce warnings and counters. They do not fail requests and are not service-level objective claims.

## Bounded Process Counters

Process-local counters use fixed families and fixed labels for HTTP status classes, authentication failures, authorization failures, unexpected errors, database errors, slow requests, slow queries, and readiness degradation. Readiness, startup, shutdown, and future document-render timing labels are similarly fixed.

Counters contain no user, passenger, request, raw route, or tenant identifiers. They reset on process restart, are not durable monitoring, and do not claim complete historical coverage.

## Readiness and Operator Diagnostics

Public `/api/readiness`, including development detailed mode, adds only non-sensitive capability flags under `observability_diagnostics_performance_telemetry_foundation`. It never includes process counters, timing aggregates, uptime, startup timestamps, or deployment diagnostics.

The bounded aggregate is available only at `/api/platform/diagnostics/observability` to existing `platform_owner`, `platform_admin`, and `platform_support` roles.

No endpoint exposes logs, arbitrary log search, environment variables, stack traces, credentials, raw paths, collection data, or tenant data.

## Redaction Architecture

The central helper combines:

- key-based redaction for password, token, authorization, cookie, secret, MongoDB credential, passport, document number, medical/health, payment/card, email, phone, and date-of-birth fields;
- safe string sanitization for MongoDB URIs, bearer values, secret assignments, email addresses, and phone-like values;
- an allowlist for event metadata.

Regex redaction is defense in depth, not a privacy guarantee. Application events must continue to use allowlisted structural metadata rather than arbitrary values.

## Deployment Correlation

`APP_GIT_COMMIT` and `APP_DEPLOYMENT_ID` are optional, syntax-bounded, non-sensitive identifiers. Hostinger operators may set a short commit and deployment label during a manual release. Neither value is a credential, and neither is required for local development.

## Docker and Nginx

Production Compose applies bounded Docker `json-file` rotation (`10m`, five files) to MongoDB, backend, and frontend containers. This is host disk protection, not application log retention policy.

Host nginx generates and forwards request/correlation IDs. Frontend nginx forwards incoming IDs to the backend. Neither proxy is configured by the application at runtime. Operators should validate host nginx manually and use the existing Docker/journal collection procedures. No log agent is installed.

The host nginx template disables access logging because the default format includes client addresses. Operators may enable a governed host access log only after defining explicit IP treatment, access, and retention policy.

CI no longer uploads raw backend logs as artifacts. Machine-readable smoke result files and a bounded container-state diagnostic remain eligible artifacts.

## Privacy and Retention Limits

This foundation does not assert legal or regulatory compliance. Operators remain responsible for access control, retention periods, host log permissions, incident handling, and deletion policy. Structured allowlists and redaction reduce risk but do not make arbitrary unstructured data safe to log.

## Future Integrations

Future work may add an external metrics, log, or trace backend only through explicit architecture, privacy, retention, tenancy, cost, and credential review. The canonical envelope, bounded labels, and protected diagnostics contract should remain the integration boundary.

## Phase 56.5.8 Release-Gate Integration

The final pilot release gate treats observability implementation, public readiness privacy, and protected diagnostics as separate required dimensions. Repository registration does not prove deployed behavior; production verification remains an operator attestation tied to the candidate assessment. Process-local telemetry durability remains an explicit warning rather than an invented monitoring guarantee.
