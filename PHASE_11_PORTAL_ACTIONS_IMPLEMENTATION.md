# Phase 11 Controlled Client Portal Actions

## Goal

Phase 11 adds controlled client portal actions behind explicit permission checks and staff-review gates.

No payment gateway integration, PDF export, email delivery, refunds/exchanges, document upload, airline automation, or website/CMS publishing was added.

## Models Added

- `PortalActionEvent`: searchable agency-owned record for client-originated portal actions.
- `DocumentAcknowledgement`: compact acknowledgement record for visible rendered documents.

## Backend Endpoints Added

- `POST /api/portal/requests`
- `POST /api/portal/requests/{request_id}/messages`
- `POST /api/portal/offers/{offer_id}/accept`
- `POST /api/portal/offers/{offer_id}/reject`
- `POST /api/portal/documents/{document_id}/acknowledge`
- `GET /api/portal/actions`
- `GET /api/agencies/{agency_id}/portal-actions`
- `POST /api/agencies/{agency_id}/portal-actions/{action_id}/process`

## Behavior

- Portal request submission always uses the authenticated portal client context.
- Portal request passenger IDs must belong to active client/passenger relationships with `can_request_travel=true`, or an active `self` relationship.
- Portal messages are always client-visible and can create staff-review tasks.
- Offer acceptance/rejection updates offer status and timestamps, writes timelines/audit/action records, and creates staff review where a linked request exists.
- Offer decisions do not create bookings, tickets, EMDs, invoices, payments, or supplier actions.
- Document acknowledgement is idempotent for the current client/document pair.
- Staff can list portal actions and mark them processed, cancelled, or archived.

## Frontend Changes

- `/portal/requests/new` portal request submission form.
- Portal request detail message form.
- Portal offer detail accept/reject controls with manual-review warning.
- Portal document detail acknowledgement control.
- `/portal/actions` client action history.
- `/agency/portal-actions` staff review list with mark-processed action.

## Seed Data

Seed now includes:

- One portal-submitted request example.
- One document acknowledgement example.
- Portal action event examples for request submission and document acknowledgement.

## Known Limitations

- Staff review is a lightweight queue, not a full workflow engine.
- No notifications, email delivery, real-time updates, document upload, PDF download, payment action, ticketing, or automatic booking is performed.
- Portal request submission supports a simple route/service text capture, not a full structured trip builder.
- Offer decisions are status changes plus review tasks; staff still manually performs booking work.

## Exact Next Recommended Phase

Phase 12 should add refund and exchange tracking as a separate operational case model, without airline execution automation.
