# Automation Event Catalog

Canonical `OperationalTimeline` event keys are the only automation trigger
source. Legacy underscore names are accepted only as normalized input aliases.

## Request

`request.created`, `request.submitted`, `request.qualified`,
`request.missing_information`, `request.updated`, `request.cancelled`

## Offer

`offer.created`, `offer.ready`, `offer.delivered`, `offer.revised`,
`offer.accepted`, `offer.declined`, `offer.expired`, `offer.superseded`

## Trip and Booking

`trip.confirmed`, `trip.updated`, `trip.cancelled`, `trip.service_added`,
`trip.document_required`, `booking.preparation_started`, `booking.ready`,
`booking.blocked`, `booking.confirmed`, `booking.failed`,
`booking.cancelled`

## Ticket, EMD, and Finance

`ticket.recorded`, `ticket.deadline_approaching`,
`ticket.refund_requested`, `ticket.exchange_requested`, `emd.required`,
`emd.recorded`, `invoice.draft_created`, `invoice.issued`,
`invoice.due_soon`, `invoice.overdue`, `payment.received`,
`payment.unallocated`, `supplier_cost.missing`,
`supplier_cost.confirmed`, `margin.below_threshold`, `credit_note.issued`,
`refund.requested`, `refund.posted`, `exchange.requested`,
`exchange.confirmed`

## Collaboration and Documents

`communication.received`, `client_reply_received`,
`passenger_reply_received`, `supplier_reply_received`,
`document.requested`, `document.uploaded`, `document.review_required`,
`approval.requested`, `approval.completed`

Each event is Agency-scoped, append-only, schema-bounded, and stably keyed.
Executions reference the exact timeline entry. Recursion and chained actions
are bounded, self-replay is deduplicated, and generated entries record rule and
execution lineage.
