# Operational Intelligence Pipeline Consolidation Foundation

Phase 51.0 creates the Operational Intelligence Pipeline Consolidation foundation.

This phase is metadata-only. It adds no new intelligence. It consolidates the completed Chapter 50 pipeline into a single Operational Intelligence Case view from passenger requirement to offer-intelligence package.

## Purpose

Operational Intelligence Cases connect:

- Phase 50.1 Knowledge Acquisition.
- Phase 50.2 Operational Constraints.
- Phase 50.3 Knowledge Normalisation.
- Phase 50.4 Knowledge Governance.
- Phase 50.5 Capability Matrix.
- Phase 50.6 Operational Evaluation.
- Phase 50.7 Passenger Service Feasibility.
- Phase 50.8 Airline Recommendations.
- Phase 50.9 Intelligent Offer Builder.

The case object prepares AgencyOS for scenario testing and real airline data population by making the full evidence and decision chain inspectable. It does not compute, generate, or automate intelligence.

## Data Foundation

Phase 51.0 adds:

- `OperationalIntelligenceCase`
- `OperationalIntelligenceCaseCreate`
- `OperationalIntelligenceCaseUpdate`
- `OperationalIntelligenceCaseService`
- `operational_intelligence_cases`
- `/api/platform/operational-intelligence-cases`
- `/api/agencies/{agency_id}/intelligence-cases`
- `/platform/operational-intelligence-cases`
- `/agency/intelligence-cases`

Operational Intelligence Cases store overview metadata, passenger/request context, Chapter 50 pipeline links, pipeline readiness flags, decision summaries, required actions, evidence/decision/knowledge/operational traces, readiness, and notes.

## Case View

The platform page is **Operational Intelligence Cases**.

The agency page is **Intelligence Cases**.

Both views display:

- Case Overview
- Passenger / Request
- Pipeline Status
- Pipeline Links
- Decision Summary
- Required Actions
- Evidence Trace
- Risk / Confidence
- Readiness
- Notes

## Human Authority

Operational Intelligence Cases are advisory metadata. Human authority remains final for operational decisions, client presentation, airline approval, booking readiness, ticketing, EMD handling, and client communication.

## Phase 51.1 Relationship

Phase 51.1 adds `service_parameter_taxonomies` as a reusable parameter vocabulary that Operational Intelligence Cases may reference through upstream knowledge, constraints, capability, evaluation, feasibility, recommendation, and offer-intelligence metadata. Phase 51.1 does not add new case intelligence, run evaluations, calculate prices, or automate operational decisions.

## Phase 51.2 Relationship

Phase 51.2 adds `request_segment_service_scopes` upstream of case consolidation. These scopes preserve segment-first passenger + segment + service intake metadata so future scenario testing can start from precise request requirements. They do not add new intelligence, evaluate policy, calculate pricing, search, book, ticket, issue EMDs, call providers, generate AI/LLM output, run workers, send automatically, or convert trips automatically. Human authority remains final.

## Explicit Exclusions

Phase 51.0 does not implement live flight search, booking, ticketing, EMD issuance, provider integrations, AI/LLM generation, parser execution, background workers, automatic client sending, pricing generation, scraping, external API calls, route aliases, or automation.
