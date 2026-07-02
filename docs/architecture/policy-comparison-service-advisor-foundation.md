# Policy Comparison Service Advisor Foundation

Phase 37.1 adds the first knowledge-consumption layer over airline policy ingestion, canonical service taxonomy, SSR/OSI and EMD mechanics, ancillary pricing, and exception metadata.

## Scope

- Platform owners can build and govern global airline policy comparison profiles.
- Platform and agency users can generate comparison snapshots and normalized comparison rows for airline/service contexts.
- Agencies can create agency-local advisor scenarios, results, and saved comparison views.
- The advisor produces operational guidance metadata only.

## Models

- `AirlinePolicyComparisonProfile`
- `AirlinePolicyComparisonSnapshot`
- `AirlinePolicyComparisonRow`
- `AirlineServiceAdvisorScenario`
- `AirlineServiceAdvisorResult`
- `AirlinePolicyComparisonSavedView`

## APIs

- Platform: `/api/platform/policy-comparison/*`
- Agency: `/api/agencies/{agency_id}/policy-comparison/*`

Agency routes can read global profiles and create agency-local snapshots, scenarios, results, and saved views. Agency routes do not mutate global comparison profiles.

## Operational Complexity Score

The complexity score is deterministic metadata only:

- Manual airline contact required: +25
- Blocker exception: +40
- Warning exception: +20
- Advisory exception: +10
- EMD required: +15
- Airline confirmation required: +10
- Missing pricing: +10
- Unknown mechanics: +10

The score is capped at 100. It is not an automatic airline recommendation.

## Safety Boundaries

- No live booking.
- No live SSR/OSI transmission.
- No provider action.
- No ticketing.
- No EMD issuance.
- No payment processing.
- No invoicing/accounting/BSP/ARC/settlement.
- No scraping or external AI.
- No automatic agency-to-global promotion.

The advisor combines facts and warnings, but recommendations remain disabled.
