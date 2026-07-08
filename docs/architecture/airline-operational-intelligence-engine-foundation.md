# Airline Operational Intelligence Engine Foundation

Phase 50.0 creates the Airline Operational Intelligence Engine architecture foundation, abbreviated AOIE.

AOIE is architecture and governance metadata only. It defines how future intelligence phases should coordinate existing airline policy, airline data pack, knowledge version, agency consumption, airline knowledge acquisition, service taxonomy, service mechanics, ancillary pricing, policy comparison, offer advisor, passenger workspace, booking workspace, offer workspace, ticket workspace, EMD workspace, and future SSR/OSI workspace foundations.

AOIE does not duplicate those foundations. It is the future decision-support layer that will answer what is possible, allowed, priced, risky, and recommended for a passenger service case.

## Passenger Service Principle

Passenger -> Need -> Service Requirement -> Airline Capability -> Operational Feasibility -> Pricing / Conditions -> Recommendation -> Fulfilment

AgencyOS is a Passenger Service Operations System. Operational workspaces record what is happening. AOIE defines how future intelligence metadata will explain what is possible and what requires human review.

## Backend

- `AirlineOperationalIntelligenceArchitecture`
- `backend/services/airline_operational_intelligence_service.py`
- `backend/routers/platform_airline_operational_intelligence.py`
- `backend/routers/agency_airline_operational_intelligence.py`
- Collection: `airline_operational_intelligence_architecture`

The service seeds one deterministic architecture record for `phase_50_0_airline_operational_intelligence_engine_architecture_foundation`.

Phase 50.1 adds the `airline_knowledge_acquisitions` evidence intake collection. Knowledge Acquisition stores manually entered official-source evidence and the first structured Airline Operational Knowledge Graph pillars: Evidence, Policy, Pricing, Capability, and Operational Constraints & Procedures. It also supports animal transport, extra-seat, and cabin capability metadata. It feeds Phase 50.2 operational constraint metadata and future normalisation, version review, capability, feasibility, recommendation, and cost-comparison metadata. It does not decide operational feasibility.

Phase 50.2 adds the `operational_constraints` collection. Operational Constraints define the formal AOIE constraint language with condition groups, supported operators, outcomes, applicability, priority/precedence, governance, future evaluation notes, and operational links. It does not execute constraints.

Future AOIE does not reason over text alone. It reasons over structured Operational Knowledge Graph records, Operational Constraints, Capabilities, Policies, Pricing, and Evidence.

## Routes

- `GET /api/platform/airline-operational-intelligence`
- `GET /api/platform/airline-operational-intelligence/summary`
- `GET /api/platform/airline-operational-intelligence/architecture`
- `GET /api/agencies/{agency_id}/airline-operational-intelligence`
- `GET /api/agencies/{agency_id}/airline-operational-intelligence/summary`
- `GET /api/agencies/{agency_id}/airline-operational-intelligence/architecture`

All routes are read-only visualization routes.

## Future AOIE Roadmap

- 50.0 Airline Operational Intelligence Engine Architecture Foundation
- 50.1 Airline Knowledge Acquisition Workspace - implemented as manual source evidence intake
- 50.2 Operational Constraint Engine Foundation - implemented as metadata-only constraint language
- 50.3 Airline Service Rule Normalisation Foundation
- 50.4 Airline Knowledge Version Review Foundation
- 50.5 Airline Capability Matrix Foundation
- 50.6 Passenger Service Feasibility Assessment Foundation
- 50.7 Airline-Itinerary Recommendation Foundation
- 50.8 Total Journey Cost Comparison Foundation
- 50.9 Offer Builder AOIE Integration Foundation

## Explicitly Excluded

Phase 50.0 does not implement AI generation, airline scraping, automatic web crawling, live airline APIs, provider integrations, pricing engine execution, itinerary search, booking execution, ticket issuance, EMD issuance, recommendation automation, background workers, external API calls, or automation.

Phase 50.1 does not implement AI parsing, automatic extraction, scraping, crawling, airline website automation, provider integrations, live airline APIs, recommendation engines, feasibility engines, pricing calculation engines, background workers, parser execution, external API calls, or automation.

Phase 50.2 does not implement live rule execution, AI reasoning, recommendation engines, feasibility scoring, pricing calculation, parser execution, scraping, background workers, provider integrations, external API calls, evaluation endpoints, or automation.
