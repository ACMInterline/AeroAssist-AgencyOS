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

Decision packs are advisory. They do not execute bookings, issue tickets or EMDs, send communications, charge payment methods, or override human authority.

## North Star

AeroAssist first evaluates which airlines can safely and correctly fulfil the passenger's complete operational service profile, then recommends itinerary options.
