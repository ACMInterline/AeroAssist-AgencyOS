# Phase 12 Refund and Exchange Tracking

## Goal

Add operational manual tracking for refund and exchange workflows without adding external-side-effect automation.

No automatic refund execution, ticket/EMD reissue, payment gateway actions, BSP/ARC processing, GDS/NDC/OTA integrations, PDF export, email delivery, or accounting-ledger automation is included.

## Models Added

The following models are implemented in `backend/models.py`:

- `RefundExchangeCase`
  - Tracks overall case context and lifecycle.
  - Supports `case_type`, `status`, `priority`, `reason_category`, optional `request_id`/`offer_id`/`booking_id`/`client_id`, manual estimate/final financial totals, `client_visible` flag, and lifecycle timestamps.
- `RefundExchangeItem`
  - Tracks linked records (ticket, EMD, invoice, payment, booking segment, passenger, other) plus estimated/final amounts and staff/client notes.
- `RefundExchangeMessage`
  - Supports sender/visibility and message text with `internal` and `client_visible` values.
- `RefundExchangeTimelineEvent`
  - Tracks audit-friendly workflow history and optional actor metadata.
- `RefundExchangeFinancialLine`
  - Manual financial line items with direction and pass-through flags for staff-calculated outcomes.

## Backend Endpoints Added

Implemented in `backend/routers/refunds_exchanges.py` and attached in `backend/server.py`:

- `GET /api/agencies/{agency_id}/refund-exchange-cases`
- `POST /api/agencies/{agency_id}/refund-exchange-cases`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}`
- `PUT /api/agencies/{agency_id}/refund-exchange-cases/{case_id}`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/status`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/archive`
- `POST /api/agencies/{agency_id}/bookings/{booking_id}/create-refund-exchange-case`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/items`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/items`
- `PUT /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/items/{item_id}`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/financial-lines`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/financial-lines`
- `PUT /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/financial-lines/{line_id}`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/messages`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/messages`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/timeline`
- `GET /api/portal/refund-exchange-cases`
- `GET /api/portal/refund-exchange-cases/{case_id}`

All staff endpoints enforce agency role access and same-tenant consistency checks.

## Frontend Routes Added

Agency routes in `frontend/src/App.jsx` and navigation in `frontend/src/layouts/AgencyLayout.jsx`:

- `/agency/refunds-exchanges`
- `/agency/refunds-exchanges/new`
- `/agency/refunds-exchanges/:caseId`

Portal routes in `frontend/src/App.jsx` and navigation in `frontend/src/layouts/ClientPortalLayout.jsx`:

- `/portal/refunds-exchanges`
- `/portal/refunds-exchanges/:caseId`

## Frontend Pages and Components

Added agency pages:

- `frontend/src/pages/agency/RefundExchangeCasesPage.jsx`
- `frontend/src/pages/agency/RefundExchangeCaseCreatePage.jsx`
- `frontend/src/pages/agency/RefundExchangeCaseDetailPage.jsx`

Added portal pages:

- `frontend/src/pages/portal/PortalRefundExchangeCasesPage.jsx`
- `frontend/src/pages/portal/PortalRefundExchangeCaseDetailPage.jsx`

Added shared visual component:

- `frontend/src/components/RefundExchangeStatusBadge.jsx`

## Financial Line Behavior

- Financial lines are manual and purely informational.
- They can capture refunds, penalties, agency fees, exchange differences, payment refunds, vouchers, and offsets.
- Endpoints do not mutate invoice totals, booking totals, payment records, or ledger data.
- `safe_client_case_line` on portal hides internal-only fields and returns client-visible lines only when `client_visible` is `true`.

## Portal Visibility

- `/api/portal/refund-exchange-cases` returns only cases where:
  - `client_id` matches the authenticated portal context, and
  - `client_visible` is `true`.
- Detail responses remove internal fields and only return:
  - case fields approved for client view,
  - client-visible items,
  - client-visible financial lines,
  - client-visible messages,
  - client-visible timeline events.
- `assert_portal_projection_safe(...)` is applied to portal payloads to reduce regression risk for accidental internal field exposure.

## Seed Data

Added in `backend/services/seed_service.py`:

- `REC-SEED-0001` (refund case) linked to seeded booking/ticket/invoice/payment
- `REC-SEED-0002` (exchange case) linked to another seeded booking
- Linked items, financial lines, portal-visible messages, and timeline entries for both cases
- Booking timeline link events for case context

## Known Limitations

- No external refund/exchange execution logic.
- No ticketing, BSP/ARC, airline portal, or payment processor calls.
- No automated policy-driven decisioning or fare-repricing engine.
- No automated status transitions beyond staff-driven updates.
- No email, notification, or export actions introduced in this phase.

## Exact Next Recommended Phase

Phase 13 should add PDF and email delivery workflow for stabilized document outputs, with delivery logs and visibility/expiry decisions.
