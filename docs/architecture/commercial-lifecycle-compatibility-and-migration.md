# Commercial Lifecycle Compatibility And Migration

## Current Compatibility Families

| Domain | Canonical target | Preserved compatibility data |
|---|---|---|
| Offer | `OfferWorkspace` / `OfferOption` | `offers`, legacy Offer children, `offer_workspaces_v2` |
| Acceptance | `OfferAcceptance` plus immutable snapshot | historical acceptances lacking exact versions/snapshot |
| Trip | `TripDossier` | `trip_workspaces`, premature legacy dossiers |
| Booking | `BookingRecord` with BookingWorkspace context | `bookings`, ambiguous historical workspaces |
| Ticket | `TicketRecord` / `TicketCoupon` | `ticket_workspaces`, standalone legacy lineage |
| EMD | `EMDRecord` / `EmdCoupon` | `emd_workspaces`, standalone legacy lineage |

Compatibility reads remain available. They are not silently rewritten,
deleted, merged, or promoted. Normal UI writes canonical Offer and Booking
workflow records. Linked legacy Offers cannot overwrite canonical Offer truth;
legacy Booking and legacy Booking Ticket/EMD mutation routes are read-only.

## Dry-Run Analysis

`backend/scripts/analyze_commercial_lifecycle_migration.py` scans bounded
records and reports:

- legacy Offers without canonical workspaces and duplicate Offer families;
- orphan OfferOptions;
- accepted decisions without immutable snapshots and multiple active
  acceptances;
- snapshots without Trips, premature Trips, and missing lineage;
- BookingWorkspaces claiming confirmation without evidenced BookingRecords;
- BookingRecords without Trip/handoff lineage and duplicate record locators;
- Ticket/EMD normal-flow records without BookingRecord lineage;
- counts by Agency/domain, deterministic candidates, ambiguous cases, and
  manual-review counts.

It records collection counts before and after the scan and reports
`writes_performed: 0`. No write mode exists.

## Future Migration Gate

Any future migration requires all of:

1. Explicit operator confirmation.
2. One Agency and one domain per run.
3. Before/after manifest and stable record mapping.
4. Audit evidence and operator identity.
5. Backup and rollback plan.
6. Dry-run review of every ambiguous or cross-Agency case.
7. No mutation of accepted, imported raw-source, Ticket, EMD, or Finance
   historical evidence.

Deterministic candidates may be proposed, never auto-applied. Ambiguous
reconciliation remains manual. Startup never migrates these collections.

## Removal Criteria

- Legacy Offer and OfferWorkspaceV2 APIs are projection-only.
- Every acceptance has exact Offer/Option versions and one immutable snapshot.
- Every normal confirmed Trip has accepted-snapshot lineage.
- Every normal booking result is an evidenced BookingRecord.
- Every normal Ticket/EMD has BookingRecord lineage.
- All historical identifiers remain traceable after compatibility UI removal.
