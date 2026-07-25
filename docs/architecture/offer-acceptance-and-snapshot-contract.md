# Offer Acceptance And Snapshot Contract

## Offer And Option Versions

`OfferWorkspace` is the mutable Offer aggregate and must reference one
same-Agency `TravelRequest`. `OfferOption` is a same-Agency child with a stable,
unique `option_order`. Currency resolves through governed reference data where
available, and authoritative totals are derived by the backend from governed
pricing lines.

Commercial edits are allowed while an Offer is mutable. Delivery freezes that
version. A material edit to delivered or accepted evidence creates a new
version in the same revision chain, marks the old version `superseded`, and
keeps both readable. Only one current version may remain active.

## Acceptance Decision

`OfferAcceptance` owns decision state, not the commercial payload. Acceptance
requires:

- exact OfferWorkspace ID and version;
- exact OfferOption ID and version;
- delivered, unexpired, non-superseded Offer state;
- active Agency membership and `edit_offers`;
- actor/channel/terms/consent evidence;
- a deterministic or caller-supplied bounded idempotency key.

Duplicate retries return the existing result. Duplicate active decisions with
conflicting evidence return a conflict. Decline and expiry create no Trip.
Revocation preserves all downstream records and records the lifecycle event.
No anonymous acceptance is supported.

Portal decisions use authenticated identity and active
`PortalAccessMapping` subject scope. A Client mapping may act only on its
released Client Offer. A Passenger mapping does not gain Client-wide acceptance
authority unless the release explicitly grants that subject access.

## Immutable Accepted Evidence

Successful acceptance creates exactly one `TripAcceptedOfferSnapshot`. It
freezes:

- Request, Offer, Option, and Acceptance identifiers and versions;
- Agency, Client, passenger, segment, airline, cabin, and fare evidence;
- baggage, passenger services, pets, and special items;
- airline charges, agency fees, taxes, total, and currency;
- terms, expiry, policy, and readiness evidence available at acceptance;
- creation actor/time, integrity hash, and source hash metadata.

The collection is create-only under persistence governance. There is no normal
update/delete route. Downstream rendering reads the snapshot, not current
Offer or reference labels. Client-safe projections exclude supplier cost,
margin, secrets, and internal-only notes.

## Persistence Classification

`offer_acceptances` is mutable lifecycle state and is no longer classified as
an immutable collection. `trip_accepted_offer_snapshots` remains immutable.
This distinction permits explicit decline, expiry, acceptance, and revocation
events without weakening accepted commercial evidence.
