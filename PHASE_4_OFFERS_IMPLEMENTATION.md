# Phase 4 Offers Implementation

## Goal

Implement manual staff offer creation and management. Offers may be created from requests, from client profiles, or manually. The system organizes manually researched options; it does not search fares or automate ticketing.

## Models Added

- `Offer`
- `OfferPassenger`
- `OfferRouteAlternative`
- `OfferSegment`
- `OfferFareOption`
- `OfferPriceLine`
- `OfferServiceCheck`
- `OfferTimelineEvent`

## Core Rules Implemented

- `request_id` is optional on offers.
- Creating an offer from a request copies the request client and request passengers into offer passenger snapshots.
- Each offer can have at most three active route alternatives.
- Each route alternative can have at most three active fare options.
- Fare totals and offer min/max totals are recalculated from fare options.
- Sending an offer validates that at least one route alternative and one fare option exist.
- Sending an offer sets status to `sent`, records `sent_at`, and stores `sent_snapshot`.
- If an offer is linked to a request, sending updates the request status to `offer_created` and writes a request timeline event.

## Endpoints Added

Offers:

- `GET /api/agencies/{agency_id}/offers`
- `POST /api/agencies/{agency_id}/offers`
- `GET /api/agencies/{agency_id}/offers/{offer_id}`
- `PUT /api/agencies/{agency_id}/offers/{offer_id}`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/archive`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/restore`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/send`
- `POST /api/agencies/{agency_id}/requests/{request_id}/create-offer`

Offer children:

- Offer passengers.
- Route alternatives.
- Segments.
- Fare options.
- Price lines.
- Service checks.
- Offer timeline.

## Frontend Routes Added

- `/agency/offers`
- `/agency/offers/new`
- `/agency/offers/:offerId`

Agency navigation now shows implemented items only:

- Dashboard
- Clients
- Passengers
- Requests
- Offers

## Seed Data Added

- One draft offer from a demo request.
- One manual offer from a demo client.
- Route alternatives.
- Segments.
- Fare options.
- Price lines.
- Service checks.
- Offer timeline events.

No bookings, tickets, EMDs, invoices, payments, refunds, exchanges, airline intelligence, integrations, or PDFs are seeded.

## Limitations

- No client acceptance yet.
- No booking creation.
- No ticketing, EMD, invoice, payment, refund, or exchange workflow.
- No fare search, GDS, NDC, OTA, supplier, or airline integration.
- No airline policy evaluation.
- No branded PDF generation.
- Send marks the offer as sent and snapshots the current content, but does not send email or publish to a client portal.

## Next Recommended Phase

Implement booking, ticket, EMD, invoice, and payment tracking as a post-offer operational lifecycle, while keeping ticketing and payment execution manual.
