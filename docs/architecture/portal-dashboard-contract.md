# Portal Dashboard Contract

## One Dashboard, Two Projections

`GET /api/portal/workspace/dashboard` is the canonical dashboard endpoint. It
derives the authenticated subject from `PortalAccessMapping` and returns one
of two task-oriented projections without storing a Portal dashboard record.

## Client Sections

- Upcoming Trips
- Pending Offers
- Action Required
- Outstanding Payments
- Recent Communications
- Recent Documents
- Recent Timeline
- Travel Credits
- Service Requests
- Notifications

## Passenger Sections

- My Trips
- My Tickets
- My Documents
- My Assistance
- My Communications
- My Timeline
- Travel Profile
- Upcoming Actions

Counts are computed from the same bounded, tenant-scoped records shown in each
section. Unknown or stale optional Offer linkage produces a Client-safe review
action instead of a dashboard failure.

## Presentation Rules

The dashboard uses customer language, meaningful empty/loading/error states,
keyboard-operable links and buttons, responsive sections, readable status
labels, and no raw JSON or engineering metadata. Client and Passenger
navigation are separate. Hidden navigation is not authorization; every API
still enforces the server-side mapping and record scope.
