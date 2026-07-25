# Portal Approval Contract

## Canonical Decisions

Portal approval is evidence attached to an existing canonical operation. It is
not a generic Portal approval database.

| Decision | Canonical owner | Portal behavior |
|---|---|---|
| Offer acceptance | `OfferAcceptance` + immutable accepted snapshot | Client-only exact-version decision |
| Quote approval | released Offer decision/timeline evidence | Client-visible when addressed to that Client |
| Service approval | canonical service workflow/timeline evidence | visible to the mapped subject |
| Document acknowledgement | canonical Document/Timeline where available; historical acknowledgement remains compatibility | no document mutation |
| Consent | canonical Client or Passenger profile field plus Audit/Timeline evidence | allowlisted subject update |

## Offer Acceptance Rules

1. The release must be addressed to the active Client mapping.
2. The selected option and fare must belong to the immutable released version.
3. Required warnings and terms must be acknowledged.
4. The decision is idempotent and calls the existing canonical Offer
   Acceptance service.
5. One immutable accepted snapshot preserves accepted commercial truth.
6. Acceptance does not create a Booking Record, execute payment, issue a
   Ticket/EMD, or call a provider.

Passenger Portal users may inspect an exact-recipient released option but may
not submit the Client commercial decision.

## Timeline And Audit

Governed profile, Request, document, communication, and Offer decisions create
Audit and/or append-only Timeline evidence through their canonical services.
Approval projections include only records already inside the authenticated
subject's scope. Internal review notes and restricted attachments are never
returned.
