# Airline Recommendation Engine Foundation

Phase 50.8 creates the Airline & Itinerary Recommendation Engine foundation.

This phase is metadata-only. It consumes Passenger Service Feasibility records from Phase 50.7 and stores advisory Airline Recommendation records.

## Core Principle

Recommendation is not feasibility.

Feasibility answers:

`Can this airline fulfil the passenger requirements?`

Recommendation answers:

`Among feasible airlines and itinerary options, which option should the travel professional prefer?`

Recommendations are advisory. Human authority remains final.

## Data Foundation

Phase 50.8 adds:

- `AirlineRecommendation`
- `AirlineRecommendationCreate`
- `AirlineRecommendationUpdate`
- `AirlineRecommendationService`
- `airline_recommendations`
- `/api/platform/airline-recommendations`
- `/api/agencies/{agency_id}/airline-recommendations`
- `/platform/airline-recommendations`
- `/agency/recommendations`

Platform routes can create, update, archive, list, and read recommendation metadata.

Agency routes are read-only and only expose recommendation metadata visible to the agency.

## Recommendation Metadata

Recommendation records store:

- Passenger context.
- Trip and itinerary context.
- Airline and carrier context.
- Passenger Service Feasibility references.
- Operational Evaluation, Capability Matrix, Knowledge Version, and Evidence references.
- Recommendation rank, status value, summary, score, and level.
- Operational scores for feasibility, confidence, risk, comfort, and complexity.
- Commercial reference scores and cost references.
- Recommendation strengths, limitations, conditions, and reason.
- Required SSRs, OSIs, EMDs, documents, MEDIF, manual review, station notification, and crew notification metadata.
- Structured comparison metadata across airlines and itineraries.
- Recommendation evidence and trace metadata.
- Lifecycle and archive metadata.

Supported recommendation levels are:

- Highly Recommended
- Recommended
- Acceptable
- Use With Caution
- Not Recommended

## Comparison Metadata

The comparison matrix can store structured rows for:

- Operational Feasibility
- Operational Confidence
- Passenger Comfort
- Operational Risk
- Required Approvals
- Required Documents
- Required SSRs
- Required EMDs
- Operational Complexity
- Ancillary Cost Reference
- Overall Recommendation

Rows are metadata only. They do not call providers, search flights, calculate prices, or mutate offers.

## Relationship To Phase 50.7

Phase 50.7 decides whether a passenger service case appears feasible under evaluated airline, itinerary, and service conditions.

Phase 50.8 compares feasible options and records advisory preference metadata.

Recommendation does not replace feasibility, and feasibility does not automatically become recommendation.

## Relationship To Phase 50.9

Phase 50.9 consumes Airline Recommendation metadata as one approved intelligence input for offer-intelligence packages.

This relationship does not turn Phase 50.8 into an offer builder, booking engine, pricing engine, or client-sending system. Recommendations remain advisory preference metadata and human authority remains final.

## Explicit Exclusions

Phase 50.8 does not implement live GDS search, NDC search, provider search, flight booking, ticket issuance, EMD issuance, provider APIs, parser execution, AI or LLM generation, background workers, price generation, fare calculation, offer mutation, external API calls, scraping, publishing, messaging, or automation.
