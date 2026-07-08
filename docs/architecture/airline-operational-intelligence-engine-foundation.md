# Airline Operational Intelligence Engine Foundation

Phase 50.0 creates the Airline Operational Intelligence Engine architecture foundation, abbreviated AOIE.

AOIE is architecture and governance metadata only. It defines how future intelligence phases should coordinate existing airline policy, airline data pack, knowledge version, agency consumption, airline knowledge acquisition, service taxonomy, service mechanics, ancillary pricing, policy comparison, offer advisor, passenger workspace, booking workspace, offer workspace, ticket workspace, EMD workspace, and future SSR/OSI workspace foundations.

AOIE does not duplicate those foundations. It is the future decision-support layer that will answer what is possible, allowed, priced, risky, and recommended for a passenger service case.

## Foundational Architecture Documents

AOIE and future Chapter 50 work are governed by the permanent foundation documents in `docs/architecture/foundations/`:

- `PASSENGER_SERVICE_OPERATIONS_MANIFESTO.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md`
- `AEROASSIST_ENGINEERING_PRINCIPLES.md`
- `PASSENGER_SERVICE_ONTOLOGY.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_ONTOLOGY.md`
- `GLOSSARY.md`

## Future Codex Guidance

Before implementing future phases, Codex should read and follow:

- `PASSENGER_SERVICE_OPERATIONS_MANIFESTO.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md`
- `AEROASSIST_ENGINEERING_PRINCIPLES.md`
- `PASSENGER_SERVICE_ONTOLOGY.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_ONTOLOGY.md`
- `GLOSSARY.md`

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

Phase 50.1 adds the `airline_knowledge_acquisitions` evidence intake collection. Knowledge Acquisition stores manually entered official-source evidence and the first structured Airline Operational Knowledge Graph pillars: Evidence, Policy, Pricing, Capability, and Operational Constraints & Procedures. It also supports animal transport, extra-seat, and cabin capability metadata. It feeds Phase 50.2 operational constraint metadata, Phase 50.3 normalisation metadata, and future version review, capability, feasibility, recommendation, and cost-comparison metadata. It does not decide operational feasibility.

Phase 50.2 adds the `operational_constraints` collection. Operational Constraints define the formal AOIE constraint language with condition groups, supported operators, outcomes, applicability, priority/precedence, governance, future evaluation notes, and operational links. It does not execute constraints.

Phase 50.3 adds the `airline_knowledge_normalisations` collection. Knowledge Normalisation creates canonical operational vocabulary and taxonomy metadata so future AOIE phases can compare airlines consistently. It does not evaluate rules.

Phase 50.4 adds the `airline_knowledge_versions` and `airline_knowledge_releases` collections. Knowledge Governance versions Evidence, Policy, Pricing, Capability, Operational Constraints, and Operational Procedures independently, groups releases, preserves historical lookup, and records comparison, rollback, superseded, and archived metadata. It does not publish automatically or evaluate rules.

Phase 50.5 adds the `airline_capability_matrix` collection. The Airline Operational Capability Matrix records what airlines can operationally deliver by airline, service, aircraft, cabin, airport, route, country, season, interline/codeshare context, restrictions, confidence, evidence, and governance references. Capability is distinct from Policy and Pricing. It does not evaluate passenger cases, score feasibility, rank airlines, reason with AI, execute parsers, calculate pricing, call providers, run workers, scrape, or publish automatically.

Phase 50.6 adds the `operational_knowledge_evaluations` collection. The Operational Knowledge Evaluation Engine records deterministic, explainable, evidence-backed metadata about what operational knowledge applies to a passenger operational requirement. Evaluation is not recommendation and does not determine passenger feasibility. It only consumes Knowledge Acquisition, Knowledge Normalisation, Operational Constraints, Knowledge Governance, and the Capability Matrix.

Future AOIE does not reason over text alone. It reasons over structured Operational Knowledge Graph records, Operational Constraints, Knowledge Normalisations, Knowledge Governance versions and releases, Capabilities, Policies, Pricing, Evidence, and Operational Evaluation Results.

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
- 50.3 Airline Operational Knowledge Normalisation Foundation - implemented as metadata-only canonical vocabulary
- 50.4 Airline Operational Knowledge Governance & Version Control Foundation - implemented as metadata-only lifecycle governance
- 50.5 Airline Operational Capability Matrix Foundation
- 50.6 Operational Knowledge Evaluation Engine Foundation
- 50.7 Passenger Service Feasibility Engine Foundation
- 50.8 Airline & Itinerary Recommendation Engine Foundation
- 50.9 Offer Builder Intelligence Integration Foundation

## Explicitly Excluded

Phase 50.0 does not implement AI generation, airline scraping, automatic web crawling, live airline APIs, provider integrations, pricing engine execution, itinerary search, booking execution, ticket issuance, EMD issuance, recommendation automation, background workers, external API calls, or automation.

Phase 50.1 does not implement AI parsing, automatic extraction, scraping, crawling, airline website automation, provider integrations, live airline APIs, recommendation engines, feasibility engines, pricing calculation engines, background workers, parser execution, external API calls, or automation.

Phase 50.2 does not implement live rule execution, AI reasoning, recommendation engines, feasibility scoring, pricing calculation, parser execution, scraping, background workers, provider integrations, external API calls, evaluation endpoints, or automation.

Phase 50.3 does not implement live evaluation, AI parsing, recommendation engines, feasibility scoring, pricing calculation, scraping, background workers, provider integrations, external API calls, or automation.

Phase 50.4 does not implement live rule evaluation, AI reasoning, parser execution, recommendation engines, pricing calculation, provider integrations, background workers, automatic publication, external API calls, or automation.
Phase 50.5 does not implement live rule evaluation, passenger feasibility scoring, airline recommendation ranking, AI reasoning, parser execution, pricing calculation, provider integrations, background workers, scraping, automatic publication, external API calls, or automation. Phase 50.6 consumes the matrix for metadata-only operational knowledge evaluation, and future Phase 50.7 consumes evaluation outputs for passenger service feasibility.

Phase 50.6 does not implement AI reasoning, LLM prompts, flight search, itinerary recommendation, passenger feasibility scoring, booking, ticketing, provider integrations, parser execution, pricing optimisation, background workers, external API calls, or automation.
