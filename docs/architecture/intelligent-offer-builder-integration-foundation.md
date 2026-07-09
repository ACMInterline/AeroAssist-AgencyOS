# Intelligent Offer Builder Integration Foundation

Phase 50.9 creates the Intelligent Offer Builder Integration foundation.

This phase is metadata-only. It consumes approved operational intelligence and prepares explainable offer-intelligence packages for later human-reviewed offer presentation.

## Core Principle

Offer Builder should not invent intelligence.

Offer Builder consumes:

- Passenger Service Feasibility from Phase 50.7.
- Airline Recommendations from Phase 50.8.
- Operational Evaluations from Phase 50.6.
- Capability Matrix records from Phase 50.5.
- Knowledge Governance, Knowledge Versions, and Evidence from Phase 50.4 and earlier.

The offer layer is a presentation and decision-support layer. Recommendation and feasibility remain advisory. Human authority remains final.

## Data Foundation

Phase 50.9 adds:

- `IntelligentOfferBuilderPackage`
- `IntelligentOfferBuilderPackageCreate`
- `IntelligentOfferBuilderPackageUpdate`
- `IntelligentOfferBuilderService`
- `intelligent_offer_builder_packages`
- `/api/platform/intelligent-offer-builder`
- `/api/agencies/{agency_id}/offer-intelligence`
- `/platform/intelligent-offer-builder`
- `/agency/offer-intelligence`

Platform routes can create, update, archive, list, and read package metadata across agencies.

Agency routes can create, update, archive, list, and read agency-scoped package metadata.

## Package Metadata

Offer-intelligence packages store package overview, passenger context, trip/request context, offer context, intelligence inputs, recommended options, operational readiness, required actions, pricing/cost references, client explanation, internal explanation, decision pack metadata, lifecycle, and notes.

These records preserve references to recommendations, feasibility records, operational evaluations, capability matrix records, knowledge versions, and evidence references. They do not recompute or generate intelligence.

## Phase 51.0 Consolidation

Phase 51.0 adds `operational_intelligence_cases` as the downstream case view that consolidates the completed Chapter 50 pipeline from passenger requirement to offer-intelligence package.

This does not add new intelligence to Offer Builder. It prepares the system for scenario testing and real airline data population by making the full metadata chain inspectable. Human authority remains final.

## Phase 51.1 Parameter Taxonomies

Phase 51.1 adds `service_parameter_taxonomies` so offer-intelligence packages can reference reusable measurable service parameters through their upstream recommendation, feasibility, evaluation, capability, constraint, and knowledge links. It does not calculate prices, evaluate rules, generate recommendations, or mutate offers.

## Phase 51.2 Request Segment Services

Phase 51.2 adds `request_segment_service_scopes` upstream of offer intelligence. These scopes preserve the original passenger + segment + service intake context, including pets and special items as segment-scoped metadata, so future offer-intelligence packages can trace back to precise request requirements. This does not add policy evaluation, pricing calculation, offer mutation, search, booking, ticketing, EMD issuance, provider execution, AI/LLM generation, workers, automatic sending, or automatic trip conversion.

## Explicit Exclusions

Phase 50.9 does not implement live GDS/NDC search, booking, ticketing, EMD issuance, provider integrations, AI/LLM generation, parser execution, background workers, automatic client sending, fare calculation, price generation, external API calls, scraping, publishing, messaging, or automation.
