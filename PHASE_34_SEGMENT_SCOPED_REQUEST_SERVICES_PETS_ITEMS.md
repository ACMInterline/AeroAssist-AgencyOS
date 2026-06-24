# Phase 34 — Segment-Scoped Request Services, Pets, and Special Items

Phase 34 makes request services, pets, and special items structurally canonical for future trips, offers, policy checks, and airline operations.

## Implemented

- Request normalization service that creates passenger + segment scoped service rows, pet segment transport rows, special item segment rows, and derived case flags.
- Operational request builder support for exact service assignment by passenger and segment.
- Structured pet capture with transport mode, weights, documentation status, and segment transport assignment.
- Structured special item capture with category, quantity, transport location, documentation status, and segment transport assignment.
- Request detail sections for case flags, itinerary segments, request passengers, passenger-segment services, pets, pet segment transport, special items, item segment transport, and source snapshots.
- Public intake conversion compatibility that preserves simplified public forms while generating pending-information placeholders where possible.
- Readiness counters for normalized request segments, passengers, passenger-segment services, pets, and special items.

## Normalization Behavior

- Itinerary remains segment-first through `request_segments`.
- Request passengers are request-context rows and may remain unresolved.
- Services normalize into `request_passenger_segment_services` only when passenger and segment scope are present.
- Pet transport normalizes through `request_pet_segment_transport`.
- Special item transport normalizes through `request_special_item_segments`.
- Case flags summarize normalized records but do not replace exact child rows.
- Repeated normalization uses generated keys to update existing rows rather than duplicating generated records.

## Reference Data Usage

- Service catalogue records supply service code, family, SSR/default metadata, and policy/document/manual-pricing flags where available.
- Pet species and special item categories use Phase 33 reference data when populated.
- Empty reference data falls back to safe local defaults in the UI.

## Known Limits

- No full Trip Dossier UI.
- No airline policy evaluation engine.
- No pricing engine.
- No offer builder expansion.
- No GDS/NDC import or execution.
- No client portal expansion.
