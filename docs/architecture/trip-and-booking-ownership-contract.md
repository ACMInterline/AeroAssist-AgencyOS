# Trip And Booking Ownership Contract

## TripDossier

`TripDossier` owns confirmed operational Trip truth. In normal commercial
flow, it is created or confirmed only from a same-Agency immutable
`TripAcceptedOfferSnapshot`. Passengers and segments derive from that snapshot,
and lineage preserves Request, Offer, Offer version, Option, Option version,
Acceptance, and Snapshot IDs.

One snapshot cannot silently create multiple Trips. Request-to-Trip conversion
before acceptance is planning-only and cannot claim a confirmed Trip.

Governed exceptions are limited to manual confirmed trips, imported existing
booking/PNR trips, historical migration, and disruption/after-sales entry from
an existing external document. Each exception records creation mode, source
reference, reason, actor, audit evidence, and reconciliation state. Existing
premature or TripWorkspace records remain readable and are not rewritten.

Operational schedule changes create governed Trip revisions. They never change
the accepted Offer snapshot.

## OfferBookingHandoff

`OfferBookingHandoff` is mutable operational preparation, not a booking result.
It requires the immutable accepted snapshot and carries selected itinerary,
passenger and service requirements, pets/items, fare/readiness flags,
deadlines, warnings, missing information, documents, assignment, and actor
history. Repeated creation in the same attempt context is idempotent.

## BookingWorkspace Versus BookingRecord

| Record | Owns | Must not imply |
|---|---|---|
| `BookingWorkspace` | preparation, readiness, provider selection, tasks, missing data, commands, errors, retries | confirmed PNR or external booking success |
| `BookingRecord` | evidenced PNR/locator, provider/source, passengers, segments, SSR/OSI status, result status, source/import lineage and external-result version | provider execution by AeroAssist |

A BookingWorkspace can enter booked-like compatibility display state only when
it links to an evidenced confirmed or partially confirmed BookingRecord.
Recording a manual/import result requires the PNR, result source, evidence
reference, operator reason, actor, and optimistic result version. Confirmed
results are immutable except through explicit governed history/version paths.
Duplicate active locators within an Agency conflict safely.

Legacy `/bookings` detail/list routes remain readable. Their create/update,
archive/cancel, passenger/segment, Ticket, and EMD mutations return a canonical
conflict instead of creating parallel truth. Historical Finance summaries on
legacy Booking records remain migration debt and are not redesigned here.

## Ticket And EMD Continuity

Normal Ticket/EMD metadata creation requires a same-Agency confirmed or
partially confirmed BookingRecord and preserves Trip/workspace lineage.
TicketCoupon and EmdCoupon remain children of their document owner.

Standalone historical/manual imports require explicit non-normal source
context, source reference, reason, actor, and audit evidence. Idempotent retries
return the existing same-lineage record; conflicting lineage is rejected.
These routes record document mirrors only and never issue, void, exchange, or
refund through a provider.
