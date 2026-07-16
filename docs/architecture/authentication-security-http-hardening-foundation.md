# Authentication, Security, and HTTP Hardening Foundation

## Purpose

Phase 56.5.4 hardens the existing FastAPI authentication and HTTP boundary before further product development. It preserves current opaque bearer tokens, identity and session collections, role checks, tenant isolation, frontend routes, deployment topology, and product workflows. It adds no OAuth, SSO, external identity provider, provider connectivity, AI, booking execution, or commercial behavior.

The active marker is `phase_56_5_4_authentication_security_http_hardening_foundation`. The readiness key is `authentication_security_http_hardening_foundation`.

## Security Philosophy

- Security behavior is deterministic, environment-configured, and additive.
- Authentication failures reveal no password, token, email, passenger, passport, payment, or medical data.
- An account can be locked only temporarily. Expired lock metadata never permanently changes identity status.
- Existing server-side opaque session tokens remain valid until their existing expiry or revocation state says otherwise.
- Public operational health remains small. Detailed implementation diagnostics are restricted to an explicitly enabled internal readiness path.
- Security controls do not create a second permission, tenant, workflow, or identity architecture.

## Authentication Protections

`authentication_security_service.py` evaluates the existing `auth_identities` record and stores additive failure metadata: `first_failed_login_at`, `last_failed_login_at`, and `locked_until`. Failure counts reset after the configured interval or a successful login. Exponential backoff is bounded by configured base and maximum delays. Reaching the configured attempt limit creates a temporary lock with a `Retry-After` response; identity status is never converted into a permanent lock state.

Password verification for an unknown identity uses a timing-pad password hash so the invalid-login path still performs PBKDF2 work. Responses remain generic. Structured events record reason codes and internal identifiers only.

## Token Security

Opaque tokens continue to be hashed with the existing application secret and looked up in `auth_sessions`. `validate_auth_token` provides one explicit validation path for malformed, unknown, inactive, expired, future-issued, and inactive-identity states. Expiration uses a bounded clock-skew tolerance. Active sessions retain their current token format and response contract.

Refresh is policy metadata only. `disabled` is the default; `manual_metadata` can report eligibility inside the configured window but cannot mint, rotate, or refresh a token. Future OAuth or SSO work can reuse the validator boundary without changing current sessions, but this phase implements neither protocol.

## HTTP Boundary

Every response receives a validated or generated `X-Request-ID`. Errors preserve the legacy `detail` field and add a consistent `error` object with `code`, `message`, and `request_id`. Production validation and unexpected-error messages are safe and do not expose stack traces. Development retains validation detail and exception type, but not a traceback in the response.

The configurable middleware emits:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Referrer-Policy`
- `Permissions-Policy`
- `Cross-Origin-Resource-Policy`
- `Cross-Origin-Opener-Policy`
- `Cross-Origin-Embedder-Policy`

Development emits `Strict-Transport-Security: max-age=0`, avoiding sticky HSTS for local HTTP. Production requires HSTS. COEP defaults to `unsafe-none` because FastAPI Swagger currently loads assets from `cdn.jsdelivr.net`; deployments that self-host those assets may configure `require-corp`. The generated CSP allows the same CDN for Swagger scripts/styles and allows configured HTTP/WebSocket development origins for Vite. React application assets remain served by the existing frontend container.

## CORS

Development defaults remain exact `http://localhost:5173` and `http://127.0.0.1:5173` origins. Production requires explicit absolute HTTP(S) origins, rejects wildcard and local origins during startup validation, and exposes only `X-Request-ID`. No origin is inferred from a request.

## Readiness Modes

`GET /api/readiness` uses `READINESS_PUBLIC_MODE`:

- `detailed` preserves the historical development/test payload used by regression smokes.
- `summary` exposes only service/phase state, safe configuration/database status words, inventory totals, and security readiness metadata. Production requires this mode and performs no storage probe or filesystem scan on the public path.

When `READINESS_AUTHENTICATED_DETAIL_ENABLED=true`, an active existing Platform user may receive the detailed payload from `/api/readiness` using the normal bearer token. Agency staff and portal identities continue to receive the public projection. This preserves authenticated Platform Console diagnostics without exposing them publicly.

`GET /api/system/readiness` returns detailed internal diagnostics only when `READINESS_INTERNAL_ENABLED=true`. Non-production may use it without a key. Production additionally requires a timing-safe `X-Internal-Readiness-Key` matching a configured value of at least 24 characters; otherwise the route behaves as not found.

## Configuration

Authentication and token settings:

- `LOGIN_THROTTLE_ENABLED`, `LOGIN_MAX_ATTEMPTS`
- `LOGIN_LOCK_DURATION_SECONDS`, `LOGIN_FAILURE_RESET_SECONDS`
- `LOGIN_BACKOFF_BASE_SECONDS`, `LOGIN_BACKOFF_MAX_SECONDS`
- `TOKEN_EXPIRY_MINUTES`, `TOKEN_CLOCK_SKEW_SECONDS`
- `TOKEN_REFRESH_POLICY`, `TOKEN_REFRESH_WINDOW_MINUTES`

HTTP settings:

- `CORS_ALLOWED_ORIGINS`
- `SECURITY_HEADERS_ENABLED`, `SECURITY_CONTENT_SECURITY_POLICY`
- `SECURITY_HSTS_ENABLED`, `SECURITY_HSTS_MAX_AGE_SECONDS`
- `SECURITY_HSTS_INCLUDE_SUBDOMAINS`, `SECURITY_HSTS_PRELOAD`
- `SECURITY_FRAME_OPTIONS`, `SECURITY_REFERRER_POLICY`, `SECURITY_PERMISSIONS_POLICY`
- `SECURITY_CROSS_ORIGIN_RESOURCE_POLICY`
- `SECURITY_CROSS_ORIGIN_OPENER_POLICY`
- `SECURITY_CROSS_ORIGIN_EMBEDDER_POLICY`

Readiness settings:

- `READINESS_PUBLIC_MODE`
- `READINESS_AUTHENTICATED_DETAIL_ENABLED`
- `READINESS_INTERNAL_ENABLED`
- `READINESS_INTERNAL_KEY`

All settings are validated at production startup. Development, test, and production behavior changes through environment variables only.

## Security Logging

Security events are JSON-compatible logger records for failed login, temporary lock, invalid token, permission denial, forbidden access, and unexpected authentication failure. The logger accepts a narrow field allowlist and never accepts passwords, raw tokens, email addresses, PII, passport data, payment data, or medical data. Existing audit records and authorization checks remain unchanged.

## Known Limitations

- Lockout state is identity-based, not a distributed IP or device reputation system.
- Refresh behavior is descriptive metadata only.
- CSP retains `unsafe-inline` and a Swagger CDN exception until documentation assets are self-hosted or nonce support is added.
- `Cross-Origin-Embedder-Policy: require-corp` is opt-in because it is incompatible with the current CDN-backed Swagger page.
- OAuth, OpenID Connect, SAML, MFA, recovery codes, centralized SIEM transport, and external rate-limit infrastructure remain future work.
