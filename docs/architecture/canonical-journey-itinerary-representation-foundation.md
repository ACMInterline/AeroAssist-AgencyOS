# Canonical Journey And Itinerary Representation Foundation

## Status

Phase 56.0 is active as `phase_56_0_canonical_journey_itinerary_representation_foundation`.

This phase is metadata-only presentation infrastructure. It does not search availability, calculate live fares, create bookings, issue tickets or EMDs, call providers, scrape, run AI, publish automatically, or schedule background work.

## Purpose

The Journey Engine gives AeroAssist one stable way to present a passenger journey across operational contexts. It can project a journey from existing Request, Trip, Offer, Offer option, Booking, Ticket, EMD, Flight, Passenger, Service Requirement, and operational-intelligence records.

The Journey representation is not another operational dossier. It is a versionable presentation view over canonical records.

## Source-Truth Boundary

The following records remain authoritative:

- Request remains intake and requirement origin.
- Trip remains the operational journey dossier.
- `trip_segments` and existing Flight Workspace records remain canonical segment sources.
- Offer and accepted-offer snapshots remain commercial proposal truth.
- Booking and booking-readiness snapshots remain booking handoff truth.
- Ticket and ticket coupons remain issued-document truth.
- EMD and EMD coupons remain ancillary-document truth.
- Passenger records remain identity and operational profile truth.

Journey segment records retain `source_entity_type`, `source_entity_id`, and `source_segment_id`. They are projections and never become a second flight-segment source of truth.

Generating a Journey does not mutate the source record. Projection retries reuse an existing Journey for the same agency, source type, and source id.

## Journey Structure

`JourneyRepresentation` stores agency scope, source context, passengers, route summary, lifecycle context, presentation status, version number, completeness, warnings, and non-destructive archive state.

`JourneyItineraryOption` groups one presented routing and records supplied carrier sets, chronology, elapsed/flying/connection totals, recommendation and feasibility references, confidence, warnings, and provenance.

`JourneyLegRepresentation` groups projected segments into a presentation leg. A leg references segment and connection ids; it does not own operational segment truth.

`JourneySegmentRepresentation` presents one canonical or manually supplied segment. It keeps local and UTC schedule fields distinct, carrier roles, terminals, cabin, booking class, aircraft, completeness, warnings, and provenance.

`JourneyConnectionRepresentation` connects adjacent projected segments. It records supplied or deterministically calculated connection time, airport/terminal changes, overnight and calendar-day changes, optional manually supplied MCT, and manual-review warnings. Phase 56.0 does not invent minimum connection time data.

Surface sectors use `segment_type=surface`. They remain explicit and contribute to surface-sector counts.

## Fare And Service Presentations

`JourneyFareBrandPresentation` references existing fare-family and fare-brand intelligence. It can show supplied inclusions, exclusions, variable attributes, baggage, change/refund/seat summaries, and an existing price reference. It is not a fare-pricing engine.

`JourneyServicePresentation` links passenger and segment scope to canonical service references, SSR/OSI references, request/feasibility/confirmation states, approval/document/EMD requirements, warnings, evidence trace, and separate client-safe and internal summaries.

## Provenance And Unknown Data

Supported provenance includes manual entry, GDS cryptic parser, itinerary text parser, booking import, existing Trip, existing Offer, existing Booking, ticket record, airline confirmation, structured import, and a future provider-adapter reference.

Provenance state remains separate from verification. Parsing does not make data verified. The representation preserves imported, normalized, agent-reviewed, confirmed, issued, and historical states.

Missing airports, airline, aircraft, schedule, duration, terminal, cabin, booking class, connection time, or price stays unknown. Missing required presentation values generate incompleteness and manual-review warnings instead of fabricated values.

## Deterministic Calculations

Phase 56.0 may calculate only from supplied fields:

- segment, leg, connection, and surface-sector counts
- itinerary carrier sets
- earliest departure and latest arrival
- itinerary origin and final destination
- segment flying time when valid UTC timestamps exist
- adjacent connection time when valid UTC timestamps exist
- total elapsed time when valid UTC timestamps exist
- overnight and airport-change indicators
- completeness scores
- deterministic SHA-256 snapshot hashes

Broader timezone, airport, schedule, and MCT intelligence belongs to later Phase 56 work.

## Presentation Configuration

`JourneyPresentationConfiguration` controls agent presentation detail and client-safe mode. Client-safe projection removes internal summaries, operational notes, private source locations, provider payloads, raw source payloads, credentials, secrets, and storage references. Client-safe mode always disables internal-information display.

This is sanitization for presentation, not public publication. No client-facing content is published automatically.

## Immutable Snapshots

`JourneySnapshot` stores a normalized Journey payload, deterministic content hash, version, lifecycle and source context, author, finalization state, and supersession reference.

Supported snapshot contexts include offer draft/published/accepted, booking confirmation, ticket issued, journey update, after-sales revision, and client document.

Draft snapshot metadata may be amended before finalization. Once `finalized_at` or `immutable` is set, all mutation is rejected. Finalized snapshots have no destructive delete route. Journey archival updates representation metadata and does not remove snapshots or source records.

## API And UI

Platform governance uses `/api/platform/journey-engine` and `/platform/journey-engine`. It provides diagnostics, summaries, filters, journey detail, and snapshot visibility under existing Platform authorization.

Agency operations use `/api/agencies/{agency_id}/journeys` and `/agency/journeys`. Existing agency access checks and roles protect reads and metadata writes. Every child lookup includes both `agency_id` and `journey_id`.

The Agency Journey Workspace provides source context, passenger and route summary, itinerary option presentations, chronological segments, connection details, fare/service summaries, provenance, completeness warnings, snapshots, and presentation settings.

Trip, Offer, Booking, Ticket, and EMD workspace pages link into the Journey Workspace. Opening a link does not automatically create a representation; an authorized agent must choose the projection action.

## Explicit Non-Goals

Phase 56.0 does not provide:

- live availability or schedule synchronization
- live pricing or fare calculation
- provider, GDS, NDC, airline, supplier, or payment connectivity
- booking, ticket, EMD, refund, or exchange execution
- source-record mutation
- scraping, external API calls, or AI-generated operational truth
- automatic publication, notifications, or background workers
- invented airport, airline, aircraft, timezone, MCT, or schedule data

## Future Phase 56 Roadmap

Later Phase 56 work may add richer journey construction, airport/timezone intelligence, controlled client interaction, document rendering, mobile views, disruption presentation, and after-sales revisions. Those phases must continue to reference canonical operational entities, preserve immutable historical snapshots, and keep imported evidence distinct from verified operational truth.
