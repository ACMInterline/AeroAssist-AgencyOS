# Request V4 Compatibility and Migration

## Current State

New canonical requests use `TravelRequest.request_version = 4` and a typed
`canonical_payload`. Existing Request, Request Intake, and Travel Request
Workspace records are not rewritten.

## Compatibility Projection

`request_v4_service.py` validates the complete aggregate before persistence and
then deterministically updates existing operational collections. Parent summary
fields, request passengers, segments, passenger service requests, requested
service mirrors, segment scopes, pets, and special items are generated from the
canonical payload. These rows support existing Request, Offer, and
request-to-trip consumers.

For a V4 record:

- the aggregate endpoint is the only structural writer;
- direct passenger, segment, and requested-service writes return a conflict;
- explicit identity confirmation remains available;
- status, archive, and restore actions synchronize canonical admin metadata;
- normalization rebuilds projections without changing canonical truth.

Projection failures do not disappear. The parent records
`reconciliation_required` and a bounded warning so an operator can retry.

## Legacy Records

Legacy `TravelRequest` records remain readable through the existing detail
route and are labeled `legacy_readable_manual_reconciliation`. They cannot be
edited through the V4 aggregate until reviewed. Old request-builder submissions
are converted through a deterministic adapter. Noncanonical labels, such as a
free-text time window, are not promoted into typed time fields.

`RequestIntake` remains immutable intake provenance. A V4 public intake stores
the validated aggregate on the intake and creates unresolved request travelers
only when staff explicitly converts it.

## Dry-Run Analysis

Run:

```bash
python3 backend/scripts/analyze_legacy_request_v4_migration.py
```

The command reports legacy counts, child coverage, ambiguity, and recommended
manual action. It has no write option and reports `writes_performed: 0`.

## Migration Register

No production migration is authorized by this repair. Future reconciliation
must:

1. preserve intake and builder snapshots;
2. map stable passenger and segment identities within one Agency;
3. retain ambiguous service, pet, and item facts for human review;
4. validate downstream Offer and Trip references before promotion;
5. create a reviewed V4 payload and deterministic projection;
6. never create a `PassengerProfile` from unconfirmed intake identity;
7. keep historical and accepted downstream snapshots unchanged.

`TravelRequestWorkspace` remains independently writable and therefore remains
an open consolidation item in the canonical migration register.

## Known Limits

- PTC codes and labels are reference-compatible, but richer PTC reference IDs
  depend on the next governed reference-data reconciliation.
- Airport, airline, species, breed, country, and currency values accept the
  existing code/label shapes; Request V4 does not duplicate those registries.
- Cross-collection persistence uses validation, projection state, audit, and
  retry rather than MongoDB multi-document transactions.
