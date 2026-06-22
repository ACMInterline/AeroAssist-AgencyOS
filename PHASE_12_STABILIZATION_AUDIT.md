# Phase 12 Stabilization Audit

## Goal

Audit the Phase 12 refund/exchange tracking implementation for routing, tenant isolation, portal visibility, model consistency, seed idempotency, frontend route consistency, booking/finance interactions, and runtime safety.

No Phase 13 features, PDF export, email delivery, payment gateway refunds, GDS/NDC/airline integrations, automatic refund/reissue execution, or accounting ledger behavior were added.

## Files Inspected

- `README.md`
- `BUILD_PHASES.md`
- `PRODUCT_SPEC.md`
- `CANONICAL_DATA_MODEL.md`
- `PERMISSIONS_AND_TENANCY.md`
- `WORKFLOWS.md`
- `NAVIGATION_MODEL.md`
- `REVIEW_NOTES.md`
- `PHASE_5_BOOKING_FINANCE_IMPLEMENTATION.md`
- `PHASE_8_CLIENT_PORTAL_VISIBILITY_IMPLEMENTATION.md`
- `PHASE_9_PERSISTENCE_TENANT_HARDENING.md`
- `PHASE_10_AUTH_INVITATIONS_IMPLEMENTATION.md`
- `PHASE_11_PORTAL_ACTIONS_IMPLEMENTATION.md`
- `PHASE_12_REFUND_EXCHANGE_IMPLEMENTATION.md`
- `backend/models.py`
- `backend/database.py`
- `backend/server.py`
- `backend/routers/refunds_exchanges.py`
- `backend/routers/bookings.py`
- `backend/routers/finance.py`
- `backend/routers/portal.py`
- `backend/services/seed_service.py`
- `frontend/src/App.jsx`
- `frontend/src/layouts/AgencyLayout.jsx`
- `frontend/src/layouts/ClientPortalLayout.jsx`
- `frontend/src/pages/agency/RefundExchangeCasesPage.jsx`
- `frontend/src/pages/agency/RefundExchangeCaseCreatePage.jsx`
- `frontend/src/pages/agency/RefundExchangeCaseDetailPage.jsx`
- `frontend/src/pages/portal/PortalRefundExchangeCasesPage.jsx`
- `frontend/src/pages/portal/PortalRefundExchangeCaseDetailPage.jsx`
- `frontend/src/components/RefundExchangeStatusBadge.jsx`

## Issues Found

- Staff refund/exchange write endpoints relied on role checks but did not explicitly call the shared agency-access assertion before writes.
- Passenger linked-item validation checked passenger agency ownership, but not whether the passenger belonged to the case booking or selected client context.
- Portal timeline projection included `metadata`, an internal-field key blocked by portal projection safety rules.
- Several staff list endpoints sorted raw `datetime` and string timestamp values directly, which can fail depending on storage mode and serialization path.
- The booking-to-refund/exchange case creation UI submitted booking-passenger row IDs instead of passenger profile IDs.
- The agency case detail UI submitted `booking_segment_id`, but the backend item schema accepts the generic `item_id` field for booking-segment items.
- Portal case list contained an unused map from an earlier implementation pass.

## Fixes Applied

- Added explicit `assert_agency_access(...)` inside refund/exchange write authorization.
- Tightened passenger item validation:
  - booking-linked cases require the passenger to exist on the same booking,
  - manual cases require an active client/passenger relationship for the selected client.
- Removed `metadata` from portal timeline projection.
- Normalized staff and portal timestamp sorting through a shared string sort helper.
- Fixed booking passenger linking in the create page to submit `passenger_id`.
- Fixed booking-segment item creation in the detail page to submit `item_id`.
- Removed the unused portal case map.

## Validation Run

- `git status --short` before changes: clean.
- `python3 -m py_compile backend/*.py backend/routers/*.py backend/services/*.py backend/scripts/*.py`
- Backend import/runtime smoke through `backend/scripts/smoke_backend.py`
- Seed idempotency smoke through `backend/scripts/smoke_backend.py`
- Staff refund/exchange endpoint smoke
- Booking-to-case creation smoke
- Same-agency and same-client linked item validation smoke
- Financial line smoke
- Status transition smoke
- Portal refund/exchange list/detail smoke
- Portal cross-client denial smoke
- Portal internal-field leak scan
- `backend/scripts/check_portal_isolation.py`
- `npm run build` from `frontend/`
- `git diff --check`

## Remaining Limitations

- Refund/exchange records remain manual tracking only.
- No ticket, EMD, payment, invoice, booking, or ledger mutations are performed by refund/exchange financial lines or statuses.
- No portal mutation endpoints exist for refund/exchange cases.
- No email delivery, PDF export, payment gateway refund, GDS/NDC integration, airline portal integration, automatic repricing, or automated reissue/refund execution exists.
- Formal migration scripts and a broader authorization matrix remain future production-hardening work.

## Recommended Next Phase

Phase 13 should add document delivery/export workflow only after confirming scope for PDF generation, email/share delivery, retention, visibility expiry, and audit logging. It should remain separate from refund/payment execution.
