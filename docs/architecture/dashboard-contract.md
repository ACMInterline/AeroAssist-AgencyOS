# Dashboard Contract

## Purpose

Dashboards answer what needs attention now. They aggregate existing authorized
records and never become a second source of operational truth.

## Agency Dashboard

`/agency` remains the Operations Command Centre. It consumes the existing
Agency-scoped operations command-center response and presents:

- Today's work
- Action required
- Deadlines
- Bookings needing action
- Pending offers
- Pending approvals
- Recent communications
- Financial summary
- Notifications

Every summary links to the owning workflow or record list. Counts are derived
from work queues, deadlines, offer and booking state, passenger-service
requirements, collaboration activity, and posted commercial records. No
dashboard interaction may fabricate a workflow transition or widen
`agency_id`.

## Platform Dashboard

`/platform` presents:

- Agency health
- Reference updates
- Knowledge updates
- Operational alerts
- Commercial Pilot status
- System health
- Attention required
- Recent activity
- Quick actions

It consumes the protected Platform summary plus authorized knowledge, pilot,
feedback, and public-safe readiness responses. Monitoring details remain on
protected Platform routes. The dashboard does not expose internal diagnostics
through public readiness.

## Portal Dashboards

Client and Passenger dashboards are separate projections over records
authorized by their active Portal mapping. Client summaries may include trips,
offers, requests, messages, payments, and actions. Passenger summaries remain
limited to that passenger's trips, tickets, assistance, documents, messages,
timeline, and actions.

## Experience Rules

- Show a loading state while required data is unresolved.
- Show actionable error recovery without treating authorization failures as
  empty data.
- Use zero-value summaries honestly.
- Link each alert or count to its canonical owner.
- Never store dashboard-only business truth.
- Never treat dashboard visibility as authorization.
