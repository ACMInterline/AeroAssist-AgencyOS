# Offer Decision Pack Foundation

Phase 37.3 adds a metadata-only offer decision pack layer for AeroAssist AgencyOS.

Decision packs consume saved offer policy advisor contexts and snapshots inside offer workflows. They attach advisor evidence to offer workspaces/options so agency staff can review why an option may be operationally easy, risky, restricted, or manually reviewable.

## Records

- `offer_decision_packs`
- `offer_decision_pack_options`
- `offer_decision_pack_evidence`
- `offer_decision_pack_warnings`
- `offer_decision_pack_review_notes`
- `offer_decision_pack_snapshots`

These records may reference offer workspaces/options, offer policy advisor contexts, saved advisor snapshots, policy comparison snapshots/rows, ancillary pricing quote results, service mechanics metadata, taxonomy domain/family/variant codes, airline codes, and passenger/request/service context.

## Agency Operations

Agency endpoints live under `/api/agencies/{agency_id}/offer-decision-packs/*`.

Agency users can build/rebuild decision packs, attach existing advisor context/snapshot evidence, add or update review notes, list evidence/warnings/snapshots, and save immutable decision pack snapshots.

## Platform Diagnostics

Platform endpoints live under `/api/platform/offer-decision-packs/*`.

Platform users receive read-only diagnostics: summary counts, pack lists/details, evidence, warnings, review notes, and saved snapshots. Platform routes do not create or mutate agency operational records.

## Safety Boundaries

Decision packs are human-reviewed metadata only.

They do not:

- recommend or rank a winning airline automatically
- mutate offer prices
- mutate offer acceptance state
- create bookings or PNRs
- issue tickets or EMDs
- process payments
- generate invoices
- settle BSP/ARC/accounting records
- scrape airline sites
- call external AI
- execute GDS/NDC/provider actions

Operational complexity scores and warning levels are review indicators, not automatic recommendations.
