# Airline Operational Knowledge Blueprint

Chapter 50 defines the Airline Operational Intelligence Engine, abbreviated AOIE. AOIE is the advisory intelligence architecture that connects passenger service requirements to structured airline operational knowledge.

AOIE does not book, ticket, issue EMDs, send messages, enforce permissions, charge money, call providers, scrape airline sites, run background workers, or make final operational decisions. It prepares evidence-backed decision support for human review.

## Chapter 50 Purpose

Chapter 50 exists to answer a precise question:

Which airlines and itinerary options can safely, correctly, and practically fulfil the passenger's complete operational service profile?

The chapter turns reviewed airline evidence into normalized, governed, comparable operational knowledge. It keeps policy, pricing, capability, constraints, and procedures separate so future recommendations can explain why an option is suitable, uncertain, risky, or unsuitable.

Phase 50.4 implements the metadata-only governance and version-control layer for this blueprint. It governs Evidence, Policy, Pricing, Capability, Operational Constraints, Operational Procedures, Knowledge Releases, and Historical Versions without executing rule evaluation, recommendations, pricing, provider integrations, or automatic publication.

Phase 50.5 implements the metadata-only Airline Operational Capability Matrix. It records what airlines can operationally deliver by airline, service, aircraft, cabin, airport, route, country, season, interline/codeshare context, restrictions, risk, confidence, evidence, and governance references. It does not evaluate passenger cases, score feasibility, rank airlines, calculate pricing, call providers, or automate decisions.

Phase 50.6 implements the metadata-only Operational Knowledge Evaluation Engine. It records deterministic, explainable Operational Evaluation Results for what operationally applies to a passenger operational requirement. Evaluation is not recommendation. Evaluation does not determine passenger feasibility. It only consumes Knowledge Acquisition, Knowledge Normalisation, Operational Constraints, Knowledge Governance, and Capability Matrix metadata.

Phase 50.7 implements the metadata-only Passenger Service Feasibility Engine. It consumes Operational Evaluation Results and records advisory, explainable, evidence-linked, non-Boolean feasibility outcomes for passenger service requirements under evaluated airline, itinerary, and service conditions. Feasibility is not recommendation, does not rank airlines or itineraries, and human authority remains final.

Phase 50.8 implements the metadata-only Airline & Itinerary Recommendation Engine. It consumes Passenger Service Feasibility and records advisory recommendation metadata across feasible airline and itinerary options. Recommendation is not feasibility, not booking, not search, not price generation, and human authority remains final.

Phase 50.9 implements metadata-only Intelligent Offer Builder Integration. It consumes approved recommendations, feasibility records, operational evaluations, capability matrix records, knowledge versions, and evidence references to prepare offer-intelligence packages. Offer Builder should not invent intelligence and must not book, ticket, issue EMDs, search providers, generate AI/LLM content, execute parsers, run workers, send offers automatically, or replace human authority.

Phase 51.0 implements metadata-only Operational Intelligence Pipeline Consolidation. It adds Operational Intelligence Cases that connect the completed Chapter 50 pipeline from passenger requirement to offer-intelligence package. It adds no new intelligence, prepares scenario testing and real airline data population, and keeps human authority final.

Phase 51.2 implements metadata-only Request Intake Segment-Service Precision. It adds Request Segment Service Scopes that preserve segment-first passenger + segment + service metadata before operational intelligence uses it. Pets and special items remain segment-scoped, requests remain intake, trips remain operational dossiers, and no policy evaluation, pricing calculation, provider execution, AI generation, worker, automatic sending, or automatic trip conversion is added.

Phase 51.3 implements metadata-only Client & Passenger Master Workspace Consolidation. It makes Client the commercial owner and Passenger the reusable operational identity, supports many-to-many metadata, and makes passenger service history reusable across requests, trips, booking mirrors, ticket mirrors, EMD mirrors, documents, operational evaluations, feasibility, and recommendations. It adds no new AOIE intelligence and does not implement CRM sales pipelines, marketing automation, provider integrations, AI/LLM generation, booking, ticketing, payment gateways, workers, or automatic sending.

Phase 52.1 implements metadata-only Reference Data Engine Foundation. It adds governed reference domains for airline operational knowledge production, scenario testing, and future real airline data population. It does not add new intelligence, provider integrations, AI/LLM generation, live evaluation, pricing calculation, background workers, old `/admin` routes, or operational automation. Human authority remains final.

Phase 52.3 implements metadata-only Visual Policy Editor Foundation. It adds structured airline service policy cards with no-code sections for overview, support status, limits, route/aircraft/cabin/date/weather restrictions, documents, approvals, warnings, evidence, governance, and service parameter taxonomy links. It does not execute policies, evaluate rules, calculate pricing, call providers, use AI/LLM generation, run background workers, create old `/admin` routes, or replace human authority.

## Chapter 50 Phase Map

- 50.0 AOIE Architecture Foundation
- 50.1 Airline Operational Knowledge Acquisition
- 50.2 Operational Constraint Engine
- 50.3 Knowledge Normalisation
- 50.4 Knowledge Governance & Version Control
- 50.5 Airline Operational Capability Matrix
- 50.6 Operational Knowledge Evaluation Engine
- 50.7 Passenger Service Feasibility Engine
- 50.8 Airline & Itinerary Recommendation Engine
- 50.9 Offer Builder Intelligence Integration
- 51.0 Operational Intelligence Pipeline Consolidation
- 51.1 Service Parameter Taxonomy Integration
- 51.2 Request Intake Segment-Service Precision
- 51.3 Client & Passenger Master Workspace Consolidation
- 52.1 Reference Data Engine Foundation
- 52.3 Visual Policy Editor Foundation

## Five Pillars

AOIE knowledge is organized around five pillars:

- Evidence
- Policy
- Pricing
- Capability
- Operational Constraints / Procedures

Evidence proves where knowledge came from. Policy states what the airline says. Pricing records commercial and charge conditions. Capability records whether the airline, aircraft, airport, or service pathway can support a requirement. Operational Constraints / Procedures describe conditional handling, required steps, exceptions, approval paths, and fulfilment procedures.

## Passenger Service Ontology

The passenger side of AOIE starts with need:

Passenger -> Need -> Service Requirement -> Operational Service -> SSR / OSI -> Approval -> Document -> EMD -> Ticket / Booking -> Travel Readiness

This ontology keeps the passenger requirement ahead of ticketing artifacts. A booking or ticket may be necessary for fulfilment, but it is not the root of the service case.

## Airline Knowledge Ontology

The airline side of AOIE starts with structured operational knowledge:

Airline -> Evidence -> Policy -> Pricing -> Capability -> Constraint -> Procedure -> Outcome

This ontology prevents policy text, price notes, capability claims, and procedures from being merged into one ambiguous record.

## Service Parameter Taxonomies

Phase 51.1 adds Service Parameter Taxonomies as reusable measurable field definitions for the existing ontology. PETC can use species, breed, weight, container dimensions, temperature, route, aircraft, and documents. EXST can use reason, adjacent seat, cabin restrictions, fixed armrests, refund conditions, and pricing basis. WCHC can use mobility level, wheelchair type, battery type, device dimensions, onboard aisle chair, and airport assistance.

Parameter taxonomies do not create new intelligence, evaluate rules, calculate prices, or merge Policy, Pricing, Capability, Constraints, and Procedures. They make future structured knowledge entry and human-reviewed evaluation inputs more consistent.

## Reference Data Engine

Phase 52.1 adds governed reference domains for airlines, airports, countries, cities, currencies, aircraft, cabins, seats, passenger types, service codes, SSR/OSI, RFIC/RFISC, pets, documents, vaccinations, mobility, medical equipment, routes, flights, fare bundles, pricing metadata, temperature zones, seasonal restrictions, and travel purposes.

## Visual Policy Editor

Phase 52.3 adds `visual_policy_editor_cards` for metadata-only airline service policy-card production. Cards store airline, policy family, service family, service codes, status, effective dates, support status, limits, restrictions, required documents, approvals, warnings, client messages, internal notes, evidence links, knowledge governance links, and service parameter taxonomy links.

Cards are a human-reviewed editing and traceability surface. They are not policy execution, rule evaluation, pricing calculation, provider integration, AI generation, worker automation, or final operational authority.

Reference Data Domains provide records, aliases, normalization rules, validation rules, import-template references, governance status, and review status. They prepare scenario testing and real airline data population, but they do not evaluate policies, calculate prices, call providers, generate AI output, or automate operational decisions.

## Decision Pack Concept

A decision pack is the future evidence-backed explanation of why a passenger service option is recommended, rejected, held for review, or considered uncertain.

A decision pack should include:

- Passenger service requirement summary.
- Relevant airline evidence.
- Normalized policy, pricing, capability, constraint, and procedure records.
- Applicability assumptions.
- Missing evidence or unresolved constraints.
- Human review notes.
- Recommendation rationale from Phase 50.8 Airline Recommendation metadata when available.
- Offer-intelligence package traces from Phase 50.9 Intelligent Offer Builder Integration when available.
- Operational Intelligence Case trace metadata from Phase 51.0 when available.
- Service Parameter Taxonomy metadata from Phase 51.1 when available.
- Request Segment Service Scope metadata from Phase 51.2 when available.
- Passenger Master reusable service history and known operational profile metadata from Phase 51.3 when available.
- Reference Data Domain records and normalization metadata from Phase 52.1 when available.
- Visual Policy Editor card metadata from Phase 52.3 when available.

Decision packs are advisory. They do not execute bookings, issue tickets or EMDs, send communications, charge payment methods, or override human authority.

## North Star

AeroAssist first evaluates which airlines can safely and correctly fulfil the passenger's complete operational service profile, then recommends itinerary options.
