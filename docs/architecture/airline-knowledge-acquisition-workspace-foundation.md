# Airline Knowledge Acquisition Workspace Foundation

Phase 50.1 creates the Airline Knowledge Acquisition Workspace foundation and refines it into the metadata foundation for the Airline Operational Knowledge Graph.

This is metadata-only operational knowledge intake. Human users manually paste or record trusted airline policy/source material, and AeroAssist stores it as governed source evidence plus structured policy, pricing, capability, and operational constraint metadata for future parsing, review, normalization, versioning, and AOIE use.

AeroAssist does NOT store airline rules as a flat rule table. It stores Airline Operational Knowledge. A service knowledge record keeps five independent pillars:

- Evidence: official source, publication, effective date, original text/PDF/email/bulletin references, confidence, reviewer, and version.
- Policy: whether a service is allowed, approval requirements, document requirements, SSR/OSI/EMD/MEDIF requirements, and advance notice.
- Pricing: how the service may be charged, including flat fee, route fee, cabin fee, passenger type fee, weight/dimension/fare/percentage basis, manual quotation, currency, taxes, refundability, exchangeability, and extra-seat pricing schemas.
- Capability: whether the airline can operationally deliver the service based on aircraft, cabin, seat map, adjacent seats, armrests, accessible lavatory, onboard wheelchair, cargo, airport, handling, crew, connection, interline, or codeshare capability.
- Operational Constraints & Procedures: generic condition/operator/value/outcome/reason metadata and procedure notes that can evaluate combinations of conditions in future phases.

Capability is not policy. Capability is not pricing. Operational constraints are intentionally generic so a future AOIE can reason over combinations such as aircraft + cabin, species + destination + season, or route + carrier + purchased extra seat.

## Flow

Official airline source -> Human copy/paste or manual entry -> Acquisition record -> Source evidence -> Policy/Pricing/Capability/Constraint metadata -> Review status -> Future parser -> Future normalized knowledge -> Future AOIE decision support

No scraping, crawling, airline website automation, AI parsing, automatic extraction, provider integration, live airline API, recommendation engine, feasibility engine, pricing calculation engine, background worker, or operational decision runs in Phase 50.1.

## Data

Collection: `airline_knowledge_acquisitions`

Models:

- `AirlineKnowledgeAcquisition`
- `AirlineKnowledgeAcquisitionCreate`
- `AirlineKnowledgeAcquisitionUpdate`

Each record stores acquisition reference/status/type/version, airline metadata, source metadata, raw source text, source excerpt, source notes, classification metadata, review status, approval status, versioning links, future AOIE references, operational workspace links, and internal notes.

Each record also supports structured Airline Operational Knowledge Graph metadata:

- `knowledge_graph_pillars`
- `evidence`
- `policy`
- `pricing`
- `capabilities`
- `operational_constraints`
- `animal_transport`
- `extra_seat`
- `cabin_capabilities`
- `operational_procedures`

Animal transport metadata can describe species, breed, brachycephalic and dangerous-breed flags, service animal and emotional support context, import/export/destination restrictions, seasonal and temperature embargoes, airport/aircraft/cabin restrictions, maximum quantity, carrier dimensions/weight, adjacent seat policy, purchased EXST policy, and handling notes.

Extra Seat metadata separates passenger of size, personal comfort, CBBG, musical instrument, and medical use cases. Each use case can carry separate policy, pricing, capability, operational constraints, refund conditions, cabin restrictions, route restrictions, and aircraft exceptions.

Cabin capability metadata describes cabin-specific seat configuration, seat map, armrests, adjacent seats, bassinet, wheelchair, lavatory, PETC, CBBG, EXST, medical equipment, crew handling, notes, and constraints.

## Routes

Platform metadata views and create/update/archive:

- `GET /api/platform/airline-knowledge-acquisition`
- `GET /api/platform/airline-knowledge-acquisition/summary`
- `POST /api/platform/airline-knowledge-acquisition`
- `GET /api/platform/airline-knowledge-acquisition/{acquisition_id}`
- `PUT /api/platform/airline-knowledge-acquisition/{acquisition_id}`
- `DELETE /api/platform/airline-knowledge-acquisition/{acquisition_id}`

Agency read-only visibility:

- `GET /api/agencies/{agency_id}/airline-knowledge-acquisition`
- `GET /api/agencies/{agency_id}/airline-knowledge-acquisition/summary`
- `GET /api/agencies/{agency_id}/airline-knowledge-acquisition/{acquisition_id}`

## UI

- Platform Console: `/platform/airline-knowledge-acquisition`
- Agency Workspace: `/agency/knowledge-acquisition`

The UI shows acquisition records in collapsible metadata sections: Evidence, Policy, Pricing, Capability, Operational Constraints, Animal Transport, Extra Seat, Cabin, Governance, Versioning, and Operational Links. It remains manual and metadata-only.

## AOIE Linkage

Phase 50.1 feeds Phase 50.2, Phase 50.3, and future metadata foundations:

- 50.2 Operational Constraint Engine
- 50.3 Airline Operational Knowledge Normalisation
- 50.4 Airline Operational Knowledge Governance & Version Control
- 50.5 Airline Operational Capability Matrix
- 50.6 Operational Rule Evaluation Engine
- 50.7 Passenger Service Feasibility Engine
- 50.8 Airline & Itinerary Recommendation Engine
- 50.9 Offer Builder Intelligence Integration

Knowledge Acquisition stores Airline Operational Knowledge. Phase 50.2 stores the formal metadata-only Operational Constraint Engine language derived from that knowledge. Phase 50.3 stores canonical operational vocabulary and taxonomy metadata so future AOIE can compare airlines consistently. Phase 50.4 versions acquisition evidence and derived policy, pricing, capability, constraint, and procedure metadata independently without live evaluation, AI reasoning, parser execution, recommendations, pricing calculation, provider calls, workers, or automatic publication. Future AOIE phases should reason over the Operational Knowledge Graph, operational constraints, knowledge normalisations, governed versions/releases, capabilities, policies, pricing, and evidence. Future AOIE should not reason over raw text alone.

Knowledge Acquisition does not decide operational feasibility.

## Explicitly Excluded

Phase 50.1 does not implement AI parsing, automatic extraction, web scraping, web crawling, airline website automation, provider integrations, live airline APIs, recommendation engines, feasibility engines, pricing calculation engines, background workers, parser execution, external API calls, or automation.
