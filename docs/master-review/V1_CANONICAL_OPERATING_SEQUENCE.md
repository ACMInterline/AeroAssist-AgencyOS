# AeroAssist V1 Canonical Operating Sequence

## Status And Purpose

This document is the V1 operating contract. It consolidates the implemented record families; it does not create a new phase, database, workflow system, or provider-execution capability.

The canonical commercial and fulfilment sequence is:

```text
Client
-> Passenger
-> Request
-> Trip
-> Offer
-> frozen Accepted Offer
-> Booking Handoff
-> externally obtained Booking result
-> externally obtained Ticket and/or EMD result
-> reconciliation
-> travel completion or After Sales
```

External booking, ticketing, EMD, supplier, airline, and payment actions remain outside AeroAssist unless a separately governed provider capability explicitly says otherwise. V1 records instructions, externally obtained results, evidence, reconciliation, mismatches, and human decisions.

## Three Connected Threads

### Commercial And Booking Thread

1. A Client is the commercial owner; a Passenger is the operational traveler identity.
2. A Request preserves intake truth and passenger need.
3. Request-to-trip conversion creates mappings and a downstream Trip without rewriting the Request.
4. The Trip is the operational journey shell. An Offer is prepared from the Trip and its passenger, segment, service, and knowledge context.
5. Acceptance freezes an immutable Accepted Offer snapshot. Later Offer edits cannot rewrite it.
6. A Booking Handoff assesses the frozen snapshot, readiness package, passenger/segment mappings, instructions, and unresolved blockers.
7. A Booking workspace and record are created through the handoff. They distinguish internal instruction from externally obtained booking result.
8. Ticket and EMD records capture externally obtained results and coupon/service associations. Reconciliation retains unknowns and mismatches.

### Passenger-Service Fulfilment Thread

```text
Passenger need at Request or Trip
-> Passenger Service Case
-> Booking linkage
-> airline/airport confirmation
-> Documents
-> EMD when applicable
-> departure-day fulfilment
-> final outcome
```

Passenger Services do not originate from a Ticket. A Ticket or EMD can be linked as fulfilment evidence to an existing service case, but it cannot retroactively create the passenger need. The same `PassengerServiceRequest` remains the service-case owner from request/trip scope through fulfilment. `SsrOsiWorkspace`, `PassengerServiceWorkflow`, `DocumentWorkspace`, Ticket/EMD coupons, queue items, timelines, and audits are governed supporting records.

Confirmation states are manual or externally evidenced. `unknown` is a valid operational state and must not be normalized to confirmed.

### Financial And After-Sales Thread

```text
Accepted Offer / Booking
-> Invoice and Payment records
-> optional rendered invoice document
-> reconciliation
-> After Sales financial impact when required
```

Financial state does not originate from Documents. Rendering an invoice is a presentation step and does not create, pay, settle, or reconcile financial records.

After Sales may originate from a Trip, Booking, Ticket, EMD, Passenger Service, disruption, claim, or client request. It may reference immutable accepted-offer evidence and affected invoice, payment, ticket, EMD, and line-item snapshots. A manual estimate remains explicitly manual and unreconciled until source records and evidence are reviewed.

## Transition Rules

| Transition | Required source | Required control | Result |
|---|---|---|---|
| Client -> Passenger | Canonical client and passenger identities | Explicit relationship, agency ownership | Client-passenger relationship |
| Passenger/Request -> Trip | Immutable intake and scoped passengers/segments/services | Conversion preview, validation, mapping, idempotency | Trip plus conversion evidence |
| Trip -> Offer | Trip context | Source linkage, actor, timeline/audit | Mutable Offer workspace |
| Offer -> Accepted Offer | Selected option and current commercial snapshot | Explicit acceptance | Frozen acceptance and booking-readiness evidence |
| Accepted Offer -> Booking Handoff | Frozen accepted snapshot | Readiness checks, mappings, instructions, blockers | Assessed handoff |
| Booking Handoff -> Booking | Ready/authorized handoff | Agency-scoped, idempotent creation | Booking workspace/record |
| Booking -> Ticket/EMD | External/manual result evidence | Reconciliation state; no inferred provider execution | Ticket/EMD records and coupons |
| Passenger Service -> Document | Existing service need | Explicit document requirement and explicit output reconciliation | Linked document lifecycle evidence |
| Booking/Ticket/EMD -> Finance | Commercial/fulfilment context | Invoice/payment ownership and reconciliation | Financial records |
| Finance/Operations -> After Sales | Affected operational and financial records | Before/proposed/final snapshots and human approval state | After-sales case and impact records |

## State And Evidence Principles

- Mutable workspaces may advance operational work but must reference immutable request, accepted-offer, imported-source, and reviewed evidence.
- A projection may point downstream from its source. It must never rewrite source truth to make the projection appear consistent.
- Every touched state change records agency, actor, source, target, deterministic correlation, occurrence time, result, warnings, and visibility separation.
- One unresolved obligation should synchronize one source-linked operational work item.
- Rendering, importing, or recording does not imply verification.
- Manual entry does not imply external completion, settlement, issuance, delivery, or approval.
- Cross-agency linkage is invalid even when an object ID exists.

## Forbidden Shortcuts

- Request IDs must not be reused as Trip IDs.
- Mutable Offer records must not be used in place of the frozen Accepted Offer snapshot.
- The primary agency UI must not create a Booking directly from readiness while bypassing `OfferBookingHandoff`.
- Tickets must not create passenger-service needs.
- Rendered documents must not create or settle invoices/payments.
- Document rendering alone must not verify a `DocumentWorkspace` requirement.
- Manual ticket/EMD metadata must not claim provider issuance.
- After-sales estimates must not claim settlement or mutate issued financial evidence.
- Compatibility routes may preserve old callers but must enforce current tenant and immutable-evidence guards and must not be presented as the canonical workflow.

## V1 Completion Boundary

The canonical sequence is operationally complete only when externally obtained results are reconciled, passenger-service and document outcomes are explicit, financial references are reviewed, unresolved mismatches remain visible, and the final Trip outcome or After Sales case has traceable queue, timeline, and audit evidence.
