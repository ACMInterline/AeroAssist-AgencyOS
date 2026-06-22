# Phase 9 Production Persistence And Tenant Hardening

## Goal

Phase 9 moves the Phase 1-8 demo-oriented foundation toward durable, tenant-safe operation without adding product workflows.

No refunds/exchanges, PDF export, email delivery, payment gateway integration, client edit/upload/acceptance actions, airline automation, or website/CMS publishing were added.

## Files Inspected

- `README.md`
- `BUILD_PHASES.md`
- `PRODUCT_SPEC.md`
- `CANONICAL_DATA_MODEL.md`
- `PERMISSIONS_AND_TENANCY.md`
- `WORKFLOWS.md`
- `NAVIGATION_MODEL.md`
- `REVIEW_NOTES.md`
- `PHASE_1_IMPLEMENTATION.md`
- `PHASE_2_CRM_IMPLEMENTATION.md`
- `PHASE_3_REQUESTS_IMPLEMENTATION.md`
- `PHASE_4_OFFERS_IMPLEMENTATION.md`
- `PHASE_5_BOOKING_FINANCE_IMPLEMENTATION.md`
- `PHASE_6_AIRLINE_INTELLIGENCE_IMPLEMENTATION.md`
- `PHASE_7_DOCUMENTS_IMPLEMENTATION.md`
- `PHASE_8_CLIENT_PORTAL_VISIBILITY_IMPLEMENTATION.md`
- `PHASE_8_STABILIZATION_AUDIT.md`
- Backend app, database, auth, model, service, and router files under `backend/`
- Frontend package/build configuration under `frontend/`

## Storage Modes

`AEROASSIST_DB_MODE=memory` remains available for local demo and fast development. It is not durable and should not be used for production.

`AEROASSIST_DB_MODE=mongo` is the documented durable storage path. It uses:

- `MONGODB_URL`
- `MONGODB_DATABASE`

MongoDB mode now creates indexes at startup before seed data runs.

## Persistence Changes

- `backend/database.py` now strips immutable fields from updates: `id`, `_id`, `agency_id`, and `created_at`.
- MongoDB updates now use `ReturnDocument.AFTER` explicitly.
- MongoDB startup runs `ensure_mongo_indexes`.
- Every agency-owned collection receives indexes on `id` and `agency_id`.
- Global collections receive uniqueness indexes for stable IDs and natural keys where used by seed or create flows.

## Tenant Isolation Rules

Reusable helpers were added in `backend/services/tenant_service.py`:

- `require_agency_context`
- `assert_agency_record`
- `filter_by_agency`
- `deny_cross_agency_access`
- `portal_client_context`
- `assert_portal_can_view_passenger`
- `assert_portal_owns_client_record`
- `safe_public_projection`
- `assert_portal_projection_safe`

Agency-owned routers already used `agency_id` filters for list/detail/child collections. Phase 9 keeps those API contracts and adds shared helpers for future routers and smoke validation.

## Portal Isolation Rules

The portal router now resolves context through `portal_client_context` and uses explicit portal helpers for:

- Portal client mapping resolution.
- Cross-client request/offer/booking/invoice denial.
- Passenger visibility through active `can_view` relationships.
- Safe portal account projection.
- Response payload validation against internal field keys.

Portal endpoints still remain read-only. No client edit, upload, payment, request submission, or offer acceptance actions were added.

## Seed Idempotency Behavior

Seed data remains idempotent by natural lookup keys such as owner email, agency slug, reference domain/key, client email, passenger display name, request reference, offer reference, booking reference, airline code, document template name/type, and portal mapping email.

The new backend smoke script calls the seed endpoint twice and verifies platform summary counts do not change.

## Recommended MongoDB Indexes

Implemented at startup where simple and safe:

- `agency_id` on all agency-owned collections.
- Unique `id` on agency-owned collections.
- Unique `platform_users.email`.
- Unique `agencies.slug`.
- Unique `global_reference_records.domain + key`.
- Unique `airline_profiles.airline_code`.
- Unique `portal_access_mappings.agency_id + user_email`.
- Client, passenger, relationship, request, offer, booking, invoice, payment, document, airline intelligence, and audit lookup indexes.

Future migration tooling should convert these startup indexes into formal migrations.

## Smoke Scripts Added

- `backend/scripts/smoke_backend.py`
- `backend/scripts/check_portal_isolation.py`

They assume a backend is running at `AEROASSIST_SMOKE_BASE_URL` or `http://localhost:8000`.

## Production Readiness Warnings

Phase 9 is not a production launch.

Remaining production risks:

- Demo header auth is still development-only.
- There is no production staff/client authentication, invitation, session, password, SSO, or MFA flow.
- No formal migration framework exists yet.
- No backup/restore, monitoring, rate limiting, or deployment hardening exists yet.
- Authorization remains foundation-level rather than a complete policy matrix.
- Seed endpoint and automatic seed behavior must be controlled before production.
- HTML documents remain previews; there is no PDF export, email delivery, public link, or file storage.

## Validation To Run

- `git status --short`
- `python3 -m py_compile backend/*.py backend/routers/*.py backend/services/*.py backend/scripts/*.py`
- Backend import/OpenAPI smoke
- Seed idempotency smoke
- Backend HTTP smoke across active module groups
- Portal isolation smoke
- `npm run build`
- `git diff --check`
- `git status --short`

## Exact Next Recommended Phase

Phase 10 should implement production authentication and invitation/session hardening. It should replace demo headers and portal demo mappings with real identity, invitation, session, account-status, and audit behavior before adding client portal actions.
