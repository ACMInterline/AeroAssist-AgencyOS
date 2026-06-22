# Phase 10 Production Authentication And Invitation Flow

## Goal

Phase 10 replaces demo-header-only access with a production-oriented authentication and invitation foundation while keeping local demo mode available.

No new business modules, refunds/exchanges, PDF export, payment gateway integration, offer acceptance, portal request submission, document upload, airline automation, or website/CMS publishing were added.

## Backend Models Added

- `AuthIdentity`: login credential record with normalized email, hashed password, identity type, status, login metadata, and reset-required flag.
- `AuthSession`: opaque bearer-token session record with hashed token, status, issue/expiry metadata, user agent, and IP address.
- `Invitation`: unified invitation record for platform, agency staff, and client portal flows with hashed token, target fields, status, expiry, and acceptance metadata.

## Backend Endpoints Added Or Changed

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/invitations/accept`
- `POST /api/auth/change-password`
- `POST /api/agencies/{agency_id}/staff/invitations`
- `POST /api/agencies/{agency_id}/clients/{client_id}/portal-invitation`

The legacy `POST /api/auth/demo-login` remains only for local/demo use.

## Auth Behavior

- Passwords are stored with PBKDF2-SHA256 hashes and per-password salts.
- Session tokens are opaque random tokens; only HMAC token hashes are stored.
- Invitation tokens are opaque random tokens; only HMAC token hashes are stored.
- Suspended, archived, and still-invited identities cannot log in.
- `GET /api/auth/me` returns a safe identity payload, staff/platform user payload when mapped, active agency memberships, and portal account/client mapping when applicable.
- Existing agency routers continue to use `get_current_user`, `require_platform_role`, `require_agency_role`, `get_current_agency_context`, and tenant helper checks.
- Portal routes now prefer authenticated `client_portal` identities and use demo portal headers only when `DEMO_AUTH_ENABLED=true`.

## Demo Accounts

Seed data creates local demo identities with password `DemoPass123!`:

- `owner@aeroassist.dev`
- `agency.owner@aeroassist.dev`
- `agency.agent@aeroassist.dev`
- `anna.client@example.com`
- `travel@orbitex.example.com`

## Frontend Changes

- `/login` now provides email/password login.
- `/login?invite=...` accepts invitations and sets the password.
- API calls send `Authorization: Bearer ...` when a session exists.
- Demo account helpers remain visible for local development.
- Platform, agency, and portal layouts expose logout actions.

## Environment Variables

- `DEMO_AUTH_ENABLED`
- `AUTH_TOKEN_SECRET`
- `TOKEN_EXPIRY_MINUTES`
- `INVITATION_EXPIRY_HOURS`
- `PASSWORD_RESET_EXPIRY_HOURS`

## Known Security Limitations

This is not final enterprise-grade authentication.

- No email delivery exists; invitation links are returned only for local/demo testing.
- No MFA, SSO, OAuth, magic link delivery, rate limiting, lockout policy, CSRF hardening, or refresh-token rotation exists.
- No formal migration framework exists for auth collections and indexes.
- Demo seed data and automatic seeding must be disabled or separated before production.
- Local storage token handling is sufficient for this foundation, but a production deployment should review cookie/session strategy, CSP, XSS protections, and secret management.

## Exact Next Recommended Phase

Phase 11 should implement controlled client portal actions such as request submission, offer response, document acknowledgement, or client-visible message/task responses, each behind explicit relationship-permission and staff-review gates.
