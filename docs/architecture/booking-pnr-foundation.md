# Booking / PNR Foundation

Phase 36.3 adds a manual booking workspace and PNR mirror foundation after booking readiness. It is a forward-only handoff:

`Request/Trip -> Offer Workspace -> Accepted Offer -> Booking Readiness Package -> Booking Workspace -> Booking Record`

## Implemented Records

- `BookingWorkspace` is created from one `BookingReadinessPackage`.
- `BookingRecord` is a draft/manual PNR mirror linked to a booking workspace.
- `BookingTimelineEvent` now supports booking workspace, booking record, trip, description, and payload fields while retaining the legacy booking timeline shape.

## Snapshot Rules

Booking workspaces and booking records copy readiness package snapshots forward:

- passengers
- segments
- pricing
- service catalogue-backed services
- pets
- special items
- required documents
- warnings
- policy violations
- SSR/OSI previews

Accepted offer snapshots, original requests, and booking readiness packages are not mutated backward by booking workspace actions.

## API Surface

Agency endpoints:

- `GET /api/agencies/{agency_id}/booking-workspaces`
- `POST /api/agencies/{agency_id}/booking-workspaces/from-readiness`
- `GET /api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}`
- `POST /api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}/status`
- `POST /api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}/rebuild-record`
- `POST /api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}/cancel`
- `PUT /api/agencies/{agency_id}/booking-records/{booking_record_id}`

## Boundaries

Phase 36.3 does not perform live GDS, NDC, supplier, ticketing, EMD, invoice, payment, or document designer actions. Provider payload and response fields are placeholders for future import/execution governance and remain manually populated until a later phase explicitly enables integrations.

Readiness exposes the non-blocking `booking_foundation` section. The foundation is optional for deployment readiness, and `provider_execution_disabled` must remain true.
