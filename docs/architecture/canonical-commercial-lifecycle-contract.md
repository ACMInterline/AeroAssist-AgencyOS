# Canonical Commercial Lifecycle Contract

## Purpose

This contract reconciles AeroAssist commercial operations to one authoritative
lineage:

`TravelRequest -> OfferWorkspace -> OfferOption -> OfferAcceptance ->
TripAcceptedOfferSnapshot -> TripDossier -> OfferBookingHandoff ->
BookingRecord -> TicketRecord / EMDRecord`

It is a P1 product-kernel repair under the existing
`phase_59_0_product_experience_recovery` marker. It introduces no provider
booking, payment, ticket issuance, EMD issuance, production migration, or
parallel aggregate.

## Ownership

| Stage | Owner | Mutable responsibility |
|---|---|---|
| Request | `TravelRequest` | Planning request and canonical Request V4 aggregate |
| Offer | `OfferWorkspace` | Current commercial proposal and governed revision chain |
| Alternative | `OfferOption` | One ordered itinerary/commercial alternative |
| Decision | `OfferAcceptance` | Pending, accepted, declined, expired, or revoked decision |
| Accepted evidence | `TripAcceptedOfferSnapshot` | Create-only frozen commercial and operational evidence |
| Trip | `TripDossier` | Confirmed operational journey and governed operational revisions |
| Booking handoff | `OfferBookingHandoff` | Mutable booking preparation package from accepted evidence |
| Booking result | `BookingRecord` | Evidenced external/manual/imported PNR result |
| Ticket / EMD | `TicketRecord`, `EMDRecord` | Downstream document mirrors with coupon children |

Workspaces, projections, Journey views, legacy records, and compatibility
responses may support the flow, but they do not replace these owners.

## Status Contract

The centralized transition rules in
`backend/services/canonical_commercial_lifecycle_service.py` normalize stable
legacy values and reject invalid transitions server-side.

- Offer: `draft`, `ready`, `delivered`, `accepted`, `declined`, `expired`,
  `superseded`, `cancelled`.
- Acceptance: `pending`, `accepted`, `declined`, `expired`, `revoked`.
- Trip: `planning`, `confirmed`, `booking_in_progress`, `booked`, `ticketed`,
  `servicing`, `completed`, `cancelled`.
- Booking preparation: `preparation`, `ready`, `submitted_manual`, `confirmed`,
  `cancelled`, mapped to existing BookingWorkspace values.
- Booking result: existing `draft`, `pending`, `partially_confirmed`,
  `confirmed`, `failed`, `cancelled`.

Material transitions require permission, same-Agency ownership, optimistic
version checks where mutable, a reason where applicable, audit evidence, and
operational timeline evidence. Frontend controls are guidance, not authority.

## Concurrency And Evidence

- Acceptance targets exact Offer and Option versions.
- Idempotency keys make repeated acceptance return the same accepted evidence.
- The accepted snapshot is created once and carries an integrity hash.
- A normal accepted snapshot maps to one Trip.
- Handoff creation is idempotent within its Trip/provider-attempt context.
- Confirmed BookingRecord state requires a source reference and governed
  evidence; a BookingWorkspace status alone is insufficient.
- Ticket and EMD normal flow requires a confirmed or partially confirmed
  BookingRecord.
- Standalone historical/import paths require explicit mode, source, reason,
  actor, and reconciliation metadata.

No MongoDB multi-document transaction is assumed. Operations validate first,
use deterministic IDs/keys, preserve evidence after partial failure, and
surface reconciliation states rather than fabricating success.

## Compatibility

Legacy Offer, TripWorkspace, Booking, TicketWorkspace, and EmdWorkspace records
remain readable. Normal Agency UI creation now uses the canonical Offer and
Booking preparation routes. Legacy writers cannot overwrite a linked
OfferWorkspace, legacy Booking mutations are read-only conflicts, and legacy
Booking Ticket/EMD routes cannot write canonical records.

Remaining historical ambiguity is reported by:

```bash
python3 backend/scripts/analyze_commercial_lifecycle_migration.py
```

The command is bounded and read-only. It exposes no write or apply mode.
