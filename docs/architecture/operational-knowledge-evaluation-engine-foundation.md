# Operational Knowledge Evaluation Engine Foundation

Phase 50.6 creates the Operational Knowledge Evaluation Engine foundation.

This phase is metadata-only. It stores deterministic, explainable evaluation records for what operational knowledge applies to passenger operational requirements. It does not determine passenger feasibility, recommend airlines or itineraries, use AI or LLM prompts, search flights, book, ticket, call providers, execute parsers, optimise pricing, run background workers, or automate decisions.

## Purpose

Operational Knowledge Evaluation answers:

`What operational knowledge applies to this passenger operational requirement?`

It does not answer:

`Is this passenger service feasible?`

It also does not answer:

`Which airline or itinerary should be recommended?`

Feasibility belongs to Phase 50.7. Recommendation belongs to Phase 50.8.

## Core Principle

Evaluation is deterministic.

Evaluation is explainable.

Evaluation always references evidence.

Evaluation never invents facts.

Evaluation only consumes metadata from:

- Knowledge Acquisition
- Knowledge Normalisation
- Operational Constraints
- Knowledge Governance
- Capability Matrix

## Data Foundation

Phase 50.6 adds:

- `OperationalKnowledgeEvaluation`
- `OperationalKnowledgeEvaluationCreate`
- `OperationalKnowledgeEvaluationUpdate`
- `operational_knowledge_evaluations`
- `OperationalKnowledgeEvaluationService`
- `/api/platform/operational-evaluations`
- `/api/agencies/{agency_id}/operational-evaluations`
- `/platform/operational-evaluations`
- `/agency/operational-evaluations`

Platform APIs may create, update, soft-archive, list, and read evaluation metadata.

Agency APIs are read-only.

## Evaluation Metadata

Evaluation records store:

- Passenger context
- Trip context
- Airline context
- Knowledge source references
- Evaluation scope
- Capability evaluation metadata
- Policy evaluation metadata
- Pricing evaluation metadata
- Constraint evaluation metadata
- Procedure evaluation metadata
- Operational outcome metadata
- Required operational actions
- Evaluation steps
- Evaluated objects
- Evidence trace
- Structured explanation sections
- Risk metadata
- Future feasibility and recommendation readiness metadata
- Lifecycle and archive metadata

## Structured Explanation

Each evaluation supports structured explanation metadata:

- Reason
- Evidence
- Capability
- Policy
- Pricing
- Constraint
- Procedure

No AI-generated prose is required or created by this phase.

## Evaluation Is Not Recommendation

Evaluation determines what operationally applies.

Recommendation comes later.

Phase 50.6 produces an Operational Evaluation Result that future Phase 50.7 can consume for passenger service feasibility. Future Phase 50.8 can consume feasibility for airline and itinerary recommendation. Future Phase 50.9 can consume recommendations for offer-builder intelligence integration.

## Explicit Exclusions

Phase 50.6 does not implement AI reasoning, LLM prompts, flight search, itinerary recommendation, booking, ticketing, provider integrations, parser execution, pricing optimisation, background workers, passenger feasibility scoring, airline ranking, external API calls, scraping, publishing, messaging, or automation.
