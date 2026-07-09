# Request Segment Service Precision Foundation

Phase 51.2 creates the metadata-only `request_segment_service_scopes` collection and the `RequestSegmentServiceScope` model family.

The purpose is segment-first request intake precision. Each scope records the passenger, request segment, and requested service together so later operational work can inspect exactly who needs which service on which leg.

## Scope

Phase 51.2 stores:

- request context, including travel request reference, source path, channel, client, and contact summary
- passenger context, including request passenger reference, passenger workspace/profile links, link mode, snapshot, and beneficiary type
- segment context, including request segment reference, segment order, origin, destination, dates, preferred airline, cabin, and segment scope type
- service context, including service family, service code, SSR code, catalogue reference, selected service key, details, and requested status
- pet context, including pet reference, transport mode, species, breed, snub-nosed flag, weight, container dimensions, and document status
- special item context, including item reference, category, transport location, weight, dimensions, battery type, and documentation status
- operational flags, knowledge links, readiness metadata, trip conversion metadata, request snapshots, decision trace, and operational notes

## Boundary

Phase 51.2 does not add policy or pricing evaluation. It does not search flights, book, ticket, issue EMDs, call providers, generate AI/LLM output, run background workers, convert trips automatically, or send anything to clients automatically.

Requests remain intake records. Trips remain operational dossiers. A `linked_trip_id` is conversion metadata only and must not reuse the `travel_request_id`.

## Relationship To Existing Models

The existing Phase 34 request children remain canonical intake structures:

- `request_passenger_segment_services`
- `request_pets`
- `request_pet_segment_transport`
- `request_special_items`
- `request_special_item_segments`

Phase 51.2 does not replace them. It adds a richer metadata-managed operational view that consolidates passenger + segment + service precision for review, readiness, traceability, scenario testing, and future real airline data population.

Pets and special items are segment-scoped. Their metadata belongs with the segment/service scope that may later be reviewed against airline knowledge, capability, feasibility, and recommendation records.

## Routes And UI

- Platform API: `/api/platform/request-segment-services`
- Agency API: `/api/agencies/{agency_id}/request-segment-services`
- Platform UI: `/platform/request-segment-services`
- Agency UI: `/agency/request-segment-services`

The platform and agency pages display Scope Overview, Request Context, Passenger Context, Segment Context, Service Context, Pet Context, Special Item Context, Operational Flags, Knowledge Links, Readiness, Conversion Metadata, and Trace / Notes.

## Human Authority

Request Segment Service Scopes are advisory metadata. They prepare intake records for scenario testing, future operational intelligence population, and human review. Human authority remains final for operational decisions, trip conversion, airline approval, offer presentation, booking readiness, ticketing, EMD handling, and client communication.
