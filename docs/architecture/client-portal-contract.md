# Client Portal Contract

## Purpose

The Client Portal is the authenticated, customer-facing projection of an
Agency's canonical Product Kernel. It does not own Requests, Offers, accepted
commercial evidence, Trips, Bookings, Tickets, EMDs, finance, Documents,
communications, timelines, notifications, or approvals.

Client access requires an active `PortalAccessMapping` whose identity,
`agency_id`, subject type, and canonical `ClientProfile` all agree. Email
matching is never sufficient authorization.

## Canonical Projection

The Portal projects:

- Requests from `TravelRequest`, including Request V4 draft state;
- released travel options backed by governed Offer versions;
- acceptances from `OfferAcceptance` and immutable
  `TripAcceptedOfferSnapshot`;
- travel from `TripDossier` and its governed children;
- fulfilment from `BookingRecord`, `TicketRecord`, and `EMDRecord`;
- documents from `DocumentWorkspace` and immutable storage/export versions;
- balances and history from canonical Invoice, Payment, Credit, Refund, and
  Exchange records;
- messages from `CommunicationThread` and its governed children;
- history from `OperationalTimeline`;
- action notices from notification projections.

The canonical workspace API starts at `/api/portal/workspace/dashboard` with
subject-scoped detail APIs under `/api/portal`. Existing legacy Portal reads
remain compatibility adapters until their records are reconciled.

## Governed Client Actions

A Client may:

- create a Request through the canonical intake/Request path;
- edit the title and Client notes of Request V4 while it is `draft`;
- cancel a `draft` or `new` Request before processing, with a reason;
- compare released travel options;
- accept, decline, request changes to, or save a released Offer for later;
- upload a PDF, JPEG, or PNG only where a visible Document Workspace explicitly
  requests an upload;
- update allowlisted fields of the canonical Client Profile;
- participate in a Client-visible canonical Communication Thread where the
  Client is an explicit participant.

Offer acceptance calls the canonical Offer Acceptance service and records an
immutable accepted snapshot. It does not create a booking, charge a payment,
issue a Ticket or EMD, or invoke a provider.

## Financial Visibility

Client finance is read-only. It includes Client-owned Invoices and lines,
received Payments, Credits, and linked Refunds, with server-derived balances.
Supplier costs, margins, commission, provider details, internal notes, and raw
accounting metadata are excluded recursively. No payment execution control is
available.

## Compatibility

Historical `/api/portal/dashboard`, `/api/portal/offers`,
`/api/portal/bookings`, rendered-document, invoice, and payment reads remain
available for valid old deep links. Normal Portal navigation uses canonical
travel options, Trips, Booking Records, Tickets, EMDs, Document Workspaces,
Collaboration, Timeline, and Ledger projections. Compatibility data is not
promoted to new business truth.

## Safety

All selectors derive from the authenticated mapping's immutable Agency and
subject IDs. Request bodies, query parameters, related record IDs, and token
claims cannot widen the scope. Internal messages and documents are never
projected. Historical ambiguity is reported by the permanently dry-run
`analyze_portal_completion_migration.py` utility.
