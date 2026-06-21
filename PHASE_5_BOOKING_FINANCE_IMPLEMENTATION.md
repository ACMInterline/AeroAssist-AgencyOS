# Phase 5 Booking and Finance Tracking Implementation

Phase 5 adds the post-offer operational tracking foundation for AeroAssist AgencyOS. It is intentionally a manual tracking layer for small agencies, not a booking engine, ticketing system, payment gateway, or accounting ledger.

## Scope Implemented

- Agency-owned booking records with `agency_id` tenant isolation.
- Booking creation manually or from an existing offer.
- Offer-to-booking snapshot payloads for selected route, selected fare, passengers, segments, price lines, and service checks.
- Booking passenger and segment records copied from offer content or added manually.
- Ticket records for tickets issued externally.
- EMD records for ancillary/service documents issued externally.
- Invoice records with line-item-derived totals.
- Payment records with received and reconciliation tracking.
- Booking timeline events for operational and finance changes.
- Staff UI routes for bookings, booking creation, booking detail, invoices, invoice detail, and payments.

## Models Added

- `Booking`
- `BookingPassenger`
- `BookingSegment`
- `TicketRecord`
- `EMDRecord`
- `Invoice`
- `InvoiceLineItem`
- `PaymentRecord`
- `BookingTimelineEvent`

Supporting status/channel enums were added for booking lifecycle, booking channel, passenger ticket status, booking segment status, ticket status, EMD type/status, invoice status, invoice line type, payment status, payment method, and reconciliation status.

## Backend Endpoints Added

- `GET /api/agencies/{agency_id}/bookings`
- `POST /api/agencies/{agency_id}/bookings`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/create-booking`
- `GET /api/agencies/{agency_id}/bookings/{booking_id}`
- `PUT /api/agencies/{agency_id}/bookings/{booking_id}`
- `POST /api/agencies/{agency_id}/bookings/{booking_id}/archive`
- `POST /api/agencies/{agency_id}/bookings/{booking_id}/cancel`
- `GET /api/agencies/{agency_id}/bookings/{booking_id}/timeline`
- Booking passenger, booking segment, ticket, and EMD endpoints under `/api/agencies/{agency_id}/bookings/{booking_id}`
- `GET /api/agencies/{agency_id}/invoices`
- `POST /api/agencies/{agency_id}/invoices`
- `GET /api/agencies/{agency_id}/invoices/{invoice_id}`
- `PUT /api/agencies/{agency_id}/invoices/{invoice_id}`
- `POST /api/agencies/{agency_id}/invoices/{invoice_id}/issue`
- `POST /api/agencies/{agency_id}/invoices/{invoice_id}/void`
- Invoice line item endpoints under `/api/agencies/{agency_id}/invoices/{invoice_id}`
- `GET /api/agencies/{agency_id}/payments`
- `POST /api/agencies/{agency_id}/payments`
- `GET /api/agencies/{agency_id}/payments/{payment_id}`
- `PUT /api/agencies/{agency_id}/payments/{payment_id}`
- `POST /api/agencies/{agency_id}/payments/{payment_id}/mark-received`
- `POST /api/agencies/{agency_id}/payments/{payment_id}/mark-reconciled`

## Frontend Routes Added

- `/agency/bookings`
- `/agency/bookings/new`
- `/agency/bookings/:bookingId`
- `/agency/invoices`
- `/agency/invoices/:invoiceId`
- `/agency/payments`

Tickets and EMDs are intentionally embedded inside booking detail and are not exposed as separate top-level modules yet.

## Workflow Notes

- A booking can be created from an offer or manually.
- Creating from an offer copies relevant offer content into booking-owned records and stores a booking snapshot.
- Ticket and EMD records represent external issuance only.
- Invoice totals are recalculated from active line items.
- Payment due is recalculated from received payments.
- Booking totals are recalculated from linked active invoices where invoice activity exists.
- Financial records use void, cancel, archive, and reconciliation statuses instead of destructive deletes.

## Seed Data Added

- One booking created from a seeded offer.
- One manual booking.
- Booking passengers and segments.
- One ticket record.
- One EMD record.
- One paid invoice with line items.
- One received and reconciled payment.
- Booking timeline events.

## Known Limitations

- No GDS, NDC, OTA, airline portal, or supplier integration.
- No automated reservation, ticketing, EMD issuance, refund, or exchange execution.
- No payment gateway or client payment portal.
- No accounting ledger, tax reporting, journal entries, or bank feed import.
- No branded PDF documents or invoice output.
- No client portal booking acceptance/payment workflow.

## Recommended Next Phase

The next build phase should add refund/exchange tracking and branded document output, or airline intelligence workflow support if knowledge assistance is the higher priority. Either path should remain tracking/support oriented until production auth, persistence, and tenant hardening are finalized.
