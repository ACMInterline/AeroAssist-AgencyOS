# Journey Option and Fare Brand Composition Workspace Foundation

## Purpose

Phase 56.2 adds an agency-owned composition workspace for arranging canonical Journey segments into itinerary alternatives, attaching governed or manually entered fare-brand choices, recording explicit commercial amounts, comparing options, and preparing an auditable offer handoff. It is a metadata and decision-support layer. It does not retrieve availability or prices, publish offers, contact providers, or execute bookings, tickets, EMDs, payments, or acceptance.

The active phase is `phase_56_2_journey_option_fare_brand_composition_workspace_foundation`.

## Relationship to Phases 56.0 and 56.1

Phase 56.0 owns the canonical Journey presentation family and source-linked segments. Phase 56.1 prepares segment drafts and applies reviewed data through the Phase 56.0 service. Phase 56.2 references those canonical Journey and segment records; it does not copy them into another operational source of truth. Request, Trip, Offer, Booking, Ticket, EMD, Passenger, accepted-offer, and issued-document records retain their existing ownership.

## 3 x 3 Composition Target

The normal workspace target is three itinerary alternatives with up to three prominent fare-brand choices per alternative. The storage model can retain more choices for operational flexibility, but the default interface keeps the comparison compact. Options and fare choices have stable display order, can be cloned, and are archived or restored non-destructively.

## Composition Model

The foundation uses eleven agency-owned collections:

- `journey_option_compositions` owns the working envelope and canonical Journey linkage.
- `journey_option_alternatives` owns display labels, ordering, summaries, warnings, and preferred-option metadata.
- `journey_option_segment_assignments` references canonical Journey segments and records assignment provenance.
- `journey_fare_brand_choices` records governed imports or explicit manual choices.
- `journey_commercial_price_breakdowns` records currency-consistent agency-entered commercial amounts.
- `journey_option_metric_snapshots` stores deterministic schedule and route projections.
- `journey_option_service_assessments` stores advisory service feasibility, approval, document, and confirmation context.
- `journey_option_comparison_profiles` and `journey_option_comparison_results` retain comparison settings and deterministic output.
- `journey_option_composition_snapshots` stores versioned, hashed composition evidence.
- `journey_option_offer_handoffs` stores explicit metadata-only offer linkage and preview traces.

All records carry `agency_id`. Cross-agency Journey, segment, offer, and composition references are rejected. Removal is archival or assignment deactivation; finalized snapshots are immutable.

## Canonical Segment Ownership

Segment assignments store the source Journey segment id, Journey leg id, role, display order, and provenance. They do not duplicate schedule or carrier truth. The workspace resolves current canonical projections for display and deterministic calculation. An active segment cannot be assigned twice inside the same option unless a later, explicitly governed exception model authorizes it.

## Deterministic Metrics

Metrics are calculated only from stored canonical data. They include segment and connection counts, elapsed duration when UTC chronology is available, connection minutes, departure and arrival context, overnight and date-change indicators, airport or terminal changes, route classification, carrier roles, codeshare/interline indicators, and completeness warnings.

The service does not assert minimum connection time, live schedule validity, availability, or operational feasibility from duration alone. Missing timestamps, negative chronology, airport changes, interline contexts, and unknown data become explicit warnings or manual-review states.

## Fare Brand Intelligence

Governed imports consume the approved, agency-visible Phase 55.7 fare-family, attribute, baggage, evidence, freshness, and version metadata. Restricted evidence and internal notes are filtered before agency or client output. Manual choices remain visibly marked as manual and `requires_review`; they are not promoted into governed airline knowledge.

Fare brand, policy, capability, pricing, evidence, and passenger-service feasibility remain separate concepts. A documented fare brand does not imply live inventory or a bookable fare.

## Commercial Amount Provenance

Commercial values are entered by an authorized agency user and retain source, actor, time, notes, and conversion metadata. The deterministic total is:

`commercial base + tax + ancillary + service fee + ticketing fee + assistance fee + markup - discount`

Amounts must be non-negative except for explicit discount or future governed credit fields. A price breakdown has one currency; changing currency requires explicit conversion metadata. An inconsistent supplied total is rejected. No fare calculation, currency conversion, payment, invoice, settlement, live quote, or provider operation occurs.

## Passenger Service and Policy Projection

Service assessments project existing Journey service presentations and governed advisory references into each option. They retain service code, passenger scope, feasibility, confirmation, approval/document requirements, evidence, warnings, internal instructions, and a separate client-safe explanation. Unknown, conditional, interline, and operating-carrier contexts remain reviewable and never become a service guarantee.

## Comparison and Preferred Option

Comparison results use deterministic dimensions such as duration, stops, price, connection time, baggage, changeability, refundability, included services, and advisory warnings. Unknown values remain unknown and are not assigned artificial scores. Preferred-option selection is an explicit agent action with a reason and audit event; the system does not silently recommend or select an itinerary.

## Snapshot Immutability

A composition snapshot contains ordered options, source-segment references, fare choices, price breakdowns, metrics, service assessments, comparison output, warnings, evidence references, knowledge-version references, and client-safe/internal content boundaries. A deterministic hash detects content changes. Finalized snapshots cannot be updated or physically deleted and preserve the historical state even when working metadata later changes.

## Offer Handoff Boundary

The preview explains the snapshot, option, fare, Journey, Trip, Request, and existing Offer links that would be recorded. Apply requires an explicit agency action and stores a trace against an existing offer workspace when supplied. It does not mutate accepted commercial snapshots, create live prices, publish, send, accept, book, ticket, issue an EMD, charge, or contact a provider.

## Routes and UI

- Agency workspace: `/agency/journey-option-composition`
- Platform diagnostics: `/platform/journey-option-compositions`
- Agency API: `/api/agencies/{agency_id}/journey-option-compositions`
- Platform API: `/api/platform/journey-option-compositions`

Agency APIs support governed metadata operations under existing agency authorization. Platform APIs are read-only diagnostics. The agency workspace provides option cards, canonical segment assignment, fare-brand choices, explicit pricing, comparisons, warnings, snapshots, and offer-handoff preview. Internal notes and client-safe explanations remain separate.

## Provider and Execution Boundary

Phase 56.2 performs no live pricing, availability search, schedule lookup, MCT lookup, GDS/NDC/provider call, external API call, scraping, AI inference, background work, automatic publication, acceptance, booking, ticketing, EMD issuance, payment, invoice, email, or SMS operation. No automatic production seed or destructive migration is introduced.

## Known Limitations

- Schedule and connection metrics are only as complete as the stored canonical timestamps and airport data.
- Minimum connection time is deliberately not asserted.
- Fare amounts are explicit agency metadata, not verified live fares.
- Governed fare-brand imports depend on approved Phase 55.7 coverage and freshness.
- Service assessments are advisory and require human review where evidence, approval, operating-carrier responsibility, or applicability is incomplete.
- Offer handoff records metadata only; downstream offer preparation remains an explicit existing-workspace action.
