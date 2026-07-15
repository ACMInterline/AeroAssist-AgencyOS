# Journey Comparison and Client Presentation Foundation

## Purpose

Phase 56.3 turns existing canonical Journey and Phase 56.2 composition metadata into clear, deterministic itinerary and fare-brand comparisons for agent review and client-safe presentation. It is a projection and governance layer, not a shopping, pricing, publication, messaging, booking, ticketing, or provider-execution system.

The active phase marker is `phase_56_3_journey_comparison_client_presentation_foundation`. Its readiness section is `journey_comparison_client_presentation_foundation` and remains diagnostic with `readiness_required: false`.

## Canonical Source Reuse

The source chain is:

`JourneyRepresentation` -> Phase 56.2 `JourneyOptionComposition` -> Phase 56.3 presentation projections -> immutable presentation snapshot -> explicit review -> metadata-only handoff.

Phase 56.3 references canonical Journey segments, composition options, fare choices, commercial price breakdowns, and advisory service assessments. It does not copy or replace Request, Trip, Passenger, Offer, Booking, Ticket, EMD, accepted-offer snapshot, or issued-document truth. Regeneration supersedes projection metadata non-destructively and preserves source hashes and provenance.

## Model Responsibilities

| Record | Responsibility |
| --- | --- |
| `JourneyComparisonPresentation` | Agency-owned presentation envelope, source links, audience, status, explicit preferred option, and review state. |
| `JourneyComparisonOptionProjection` | Client-oriented itinerary summary and deterministic schedule, complexity, warning, unknown, and completeness metrics. |
| `JourneyComparisonSegmentProjection` | Source-linked segment timeline with carrier, airport, terminal, local/UTC time, cabin, and operated-by text. |
| `JourneyComparisonConnectionProjection` | Adjacent-segment connection metadata, including airport/terminal changes, overnight state, explicit MCT uncertainty, and review requirements. |
| `JourneyComparisonFareBrandProjection` | Fare-brand price, baggage, flexibility, inclusion, warning, and unknown metadata. |
| `JourneyComparisonServiceSuitabilityProjection` | Advisory passenger-service support, evidence, confirmation, document, warning, and manual-review summary. |
| `JourneyComparisonDimension` | Governed comparison label, category, order, importance, direction, and client/internal visibility. |
| `JourneyComparisonResult` | Deterministic dimension leaders, ties, unknowns, warnings, and source hash; never an automatic commercial preference. |
| `JourneyPresentationContentBlock` | Separately stored client text and optional internal operational text. |
| `JourneyPresentationConfiguration` | Per-presentation display, visibility, language, currency, and responsive presentation settings. |
| `JourneyPresentationSnapshot` | Versioned client-safe and authorized internal payloads; finalized snapshots are immutable. |
| `JourneyPresentationReview` | Explicit reviewer checklist, decision, unresolved items, and completion metadata. |
| `JourneyPresentationHandoff` | Explicit immutable-source trace to an existing Offer or Document workflow without destination execution. |

## Deterministic Comparison

Calculations use stored, timezone-aware values only. Option projections calculate departure and arrival, elapsed and flight time, connection time, segments, stops, overnight connections, airport and terminal changes, carrier complexity, codeshare/interline indicators, warning counts, unknown counts, review counts, and completeness. Fare projections compare total and per-passenger price, difference from the lowest recorded option, baggage, change, refund, seat, meal, priority, and lounge metadata.

Dimension results retain leaders, ties, not-applicable values, and unknown values. They cover price, schedule convenience, elapsed/flight/connection time, stops, airport changes, overnight travel, baggage, flexibility, inclusions, carrier complexity, service suitability, evidence confidence, unresolved unknowns, operational risk, and manual review. Minimum connection compliance is `not_assessed` or `manual_review_required` unless governed evidence exists. No live fare, schedule, availability, or capability is inferred.

## Preferred Option Governance

System results may identify a lowest recorded price, fastest option, fewest stops, strongest recorded baggage or flexibility, strongest service suitability, or lowest identified risk. These are dimension-specific leaders and preserve ties. The system never turns one into a preferred commercial option automatically.

A preferred option requires an explicit agent action, reason, actor, and timestamp. The client preview shows it only after that decision. A preference does not accept an offer, book, ticket, issue an EMD, or commit money.

## Client and Internal Separation

Client-safe output contains readable schedule, route, connection, fare-brand, baggage, flexibility, inclusion, service-suitability, price, warning, and unknown metadata. Internal fields, evidence IDs, raw policy language, restricted contacts, source URLs, supplier instructions, confidence internals, exception details, pricing construction, supplier cost, margin, and agent notes are excluded.

The internal preview is available only through the existing authenticated agency authorization boundary. Platform diagnostics return counts and summarized governance metadata rather than agency presentation content.

## Snapshots, Reviews, and Handoffs

Snapshots contain both the sanitized client payload and an authorized internal evidence payload with source hashes. A finalized snapshot has no mutation or physical-delete path. Reviews explicitly record content, pricing, schedule, service-assessment, and warning acknowledgement.

Offer and Document handoff previews include presentation and snapshot IDs, client-safe payload, language, currency, source references, destination metadata, and immutable payload hash. Applying a handoff writes only a trace record. It does not mutate or publish an Offer, render or finalize a Document, create a public share token, send a message, change an accepted-offer snapshot, or execute a provider.

## Unknown States and Security

Unknown, not-assessed, conditional, evidence-required, airline-confirmation-required, route-specific, passenger-specific, provider-specific, and interline-uncertain states remain visible. Missing information creates warnings and manual-review states rather than false certainty or crashes.

All records are agency-owned, all agency routes use existing tenant and role checks, platform routes are read-only, and direct frontend database access is absent. No unauthenticated mutation, parallel RBAC, production seed, destructive reset, external API, scraping, AI, worker, or scheduler is introduced.

## Future Phase 56.4

Phase 56.3 provides reviewed, immutable, client-safe comparison evidence for a future Phase 56.4 delivery or interaction layer. That future layer must consume finalized snapshots through explicit canonical workflows; it must not reconstruct mutable comparison truth or weaken the publication, messaging, provider, and client/internal boundaries defined here.
