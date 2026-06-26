# Phase 35: Trip Dossier Foundation

Phase 35 introduces the Trip Dossier as the agency operational shell while preserving the blueprint rule that a request is not a trip.

## Implemented

- Additive trip dossier model fields for `trip_reference`, title, status/type, summaries, notes, source, primary request/client, linked requests, counters, and archive metadata.
- Trip child collections for copied passengers, segments, and service items with source request IDs for traceability.
- Trip timeline events and audit events for creation, request conversion, linking, unlinking, child copying, summary rebuild, update, and archive actions.
- `backend/services/trip_dossier_service.py` for manual creation, request-to-trip conversion, request linking/unlinking, idempotent child copying, and summary rebuilding.
- Agency trip APIs under `/api/agencies/{agency_id}/trips`.
- Agency UI routes `/agency/trips`, `/agency/trips/new`, and `/agency/trips/{trip_id}`.
- Request detail Trip Dossier panel and request list linked-trip badge.
- Readiness flags and counters under `/api/readiness`.
- Smoke coverage in `backend/scripts/smoke_trip_dossier_foundation.py`.

## Request Vs Trip Separation

- Requests remain independent intake/case records.
- A request may exist without a trip.
- A trip dossier has its own generated ID and `TRP-YYYYMMDD-XXXX` reference.
- `request_id` is never reused as `trip_id`.
- `TravelRequest.trip_id` is only an additive primary trip back-reference.
- `TripDossier.linked_request_ids` records the requests currently linked to the dossier.

## Request-To-Trip Conversion

Creating a trip from a request:

- Creates a trip shell with request route/date/service summaries where available.
- Sets `source=request_conversion`, `primary_request_id`, and `linked_request_ids`.
- Copies normalized request passengers into `trip_passengers`.
- Copies normalized request segments into `trip_segments`.
- Copies normalized passenger-segment services into `trip_service_items`; if scoped rows are absent, copies request-level services.
- Preserves `source_request_passenger_id`, `source_request_segment_id`, `source_request_service_id`, and `source_passenger_segment_service_id`.
- Does not delete, replace, or destructively mutate original request records.
- Is idempotent for the same request/trip source rows.

Pets and special items are summarized in trip notes for now. Trip-level pet/item models are intentionally not added in this phase.

## APIs

- `GET /api/agencies/{agency_id}/trips`
- `POST /api/agencies/{agency_id}/trips`
- `GET /api/agencies/{agency_id}/trips/{trip_id}`
- `PUT /api/agencies/{agency_id}/trips/{trip_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/archive`
- `POST /api/agencies/{agency_id}/trips/from-request/{request_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/link-request/{request_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/unlink-request/{request_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/rebuild-summary`

Agency owner/admin/agent users can manage trips. Agency readonly users can view. Client portal users cannot access agency trip management endpoints.

## UI

- `/agency/trips`: list, status/type/search filters, counts, linked request count, create button.
- `/agency/trips/new`: manual trip dossier creation.
- `/agency/trips/{trip_id}`: header, edit form, linked requests, passengers, segments, services, timeline, archive/rebuild actions, and future-phase placeholders.
- `/agency/requests/{request_id}`: Trip Dossier panel with create/open/unlink controls.

## Readiness

`/api/readiness` includes:

- `trip_dossier_foundation_enabled`
- `request_to_trip_conversion_enabled`
- `trip_linking_enabled`
- `trip_passenger_copy_enabled`
- `trip_segment_copy_enabled`
- `trip_service_scope_copy_enabled`
- `trip_dossier_count`
- `linked_trip_request_count`
- `trip_passenger_count`
- `trip_segment_count`
- `trip_service_item_count`
- `readiness_required=false`

## Known Limits

- No offer builder expansion.
- No booking, ticket, or EMD import.
- No GDS/NDC import.
- No pricing engine.
- No airline policy automation.
- No invoices/payments expansion.
- No client portal trip view.
- No trip-level pet/special-item model yet.
