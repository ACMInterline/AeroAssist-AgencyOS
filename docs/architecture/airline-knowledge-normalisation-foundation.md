# Airline Knowledge Normalisation Foundation

Phase 50.3 creates the metadata-only normalisation layer for the Airline Operational Knowledge Graph.

This layer converts messy operational terms into canonical structured knowledge so future AOIE phases can compare airlines consistently. Examples include mapping `French Bulldog` to dog animal taxonomy, `A321neo` to the A320 family, `Business` to premium cabin, `PETC` to animal transport / pet in cabin, `EXST` to extra seat, and `CBBG` to cabin baggage / bulky cabin baggage.

## Scope

The foundation adds:

- `AirlineKnowledgeNormalisation`, `AirlineKnowledgeNormalisationCreate`, and `AirlineKnowledgeNormalisationUpdate` models.
- `airline_knowledge_normalisations` Mongo collection and indexes.
- Platform metadata CRUD endpoints at `/api/platform/airline-knowledge-normalisation`.
- Agency read-only endpoints at `/api/agencies/{agency_id}/airline-knowledge-normalisation`.
- Platform UI route `/platform/airline-knowledge-normalisation`.
- Agency UI route `/agency/knowledge-normalisation`.
- Readiness section `airline_knowledge_normalisation_foundation`.
- Active phase marker `phase_50_3_airline_knowledge_normalisation_foundation`.

## Metadata Shape

Each normalisation record stores:

- Canonical record metadata: reference, status, type, canonical code, name, and description.
- Taxonomy hierarchy: domain, family, variant, parent canonical id, path, and level.
- Aliases and terms: aliases, abbreviations, airline-specific terms, GDS terms, commercial terms, and operational terms.
- Applicability: airlines, countries, airports, aircraft, cabins, service codes, SSR codes, RFICs, and RFISCs.
- Animal taxonomy: species, breed, breed group, restricted flags, service animal flags, and animal notes.
- Aircraft and cabin taxonomy: aircraft family/subtype, cabin family/name, seat type, armrest and under-seat relevance, and cabin notes.
- Service taxonomy: passenger need category, service domain/family/variant, related SSR, OSI, EMD, and document relevance.
- Units: unit type, canonical unit, unit aliases, and conversion notes.
- Knowledge links: acquisition, constraint, evidence, policy, pricing, and capability references.
- Governance: review and approval metadata.

## Safety Boundary

Normalisation does not evaluate rules.

Normalisation creates canonical operational vocabulary.

Future AOIE uses it to compare airlines consistently.

Phase 50.3 does not implement AI parsing, live evaluation, recommendation engines, feasibility scoring, pricing calculation, scraping, background workers, provider integrations, external API calls, or automation.

Phase 50.4 Airline Operational Knowledge Governance & Version Control versions normalisation-linked Evidence, Policy, Pricing, Capability, Operational Constraints, and Operational Procedures as governed knowledge assets. It also records release grouping, comparison, rollback, superseded, archived, and historical lookup metadata without automatic publication or live evaluation.

Phase 50.5 Airline Operational Capability Matrix consumes canonical normalisation metadata so airline capability records can compare services, aircraft, cabins, stations, routes, countries, seasons, animal transport, EXST, medical/accessibility, and operational requirement dimensions consistently. The matrix does not evaluate passenger cases or recommend airlines.

## Relationship To Phase 50.1 And 50.2

Phase 50.1 captures trusted airline operational knowledge metadata.

Phase 50.2 defines formal operational constraint metadata.

Phase 50.3 normalises the terms used by both layers into canonical vocabulary and taxonomy metadata. It does not replace acquisition evidence or operational constraints, and it does not decide whether a service is allowed, priced, feasible, or recommended.
