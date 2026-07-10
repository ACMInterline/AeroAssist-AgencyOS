# Operational Scenario Testing Foundation

Phase 52.8 adds metadata-only Operational Scenario Testing records.

This foundation creates passenger service scenario test cases for validating airline knowledge production against realistic examples. It does not run live providers, execute rules, call AI, parse files, book, ticket, issue EMDs, or automate operational decisions.

## Purpose

Operational Scenario Testing records expected outcomes for passenger service examples so Platform/Admin users can review whether produced knowledge would support future evaluation, feasibility, recommendation, and offer-intelligence phases.

Agency users can view read-only scenario metadata for their agency scope.

## Collection

`operational_scenario_tests`

## Models

- `OperationalScenarioTest`
- `OperationalScenarioTestCreate`
- `OperationalScenarioTestUpdate`

## Scenario Fields

Each scenario stores:

- `scenario_reference`
- `scenario_name`
- `scenario_family`
- `passenger_context`
- `itinerary_context`
- `airline_context`
- `service_requirements`
- `pets`
- `special_items`
- `documents`
- `expected_policy_outcome`
- `expected_pricing_behavior`
- `expected_feasibility`
- `expected_recommendation_level`
- `expected_required_actions`
- `evidence_links`
- `test_status`
- `review_notes`

## Scenario Families

Supported scenario families are:

- PETC
- AVIH
- SVAN
- EXST passenger of size
- CBBG
- WCHC
- MEDIF
- POC
- UMNR
- musical instrument
- sports equipment
- restricted equipment

## Routes

Platform routes:

- `/api/platform/operational-scenario-testing`
- `/api/platform/operational-scenario-testing/summary`
- `/api/platform/operational-scenario-testing/{scenario_id}`

Agency read-only routes:

- `/api/agencies/{agency_id}/operational-scenario-testing`
- `/api/agencies/{agency_id}/operational-scenario-testing/summary`
- `/api/agencies/{agency_id}/operational-scenario-testing/{scenario_id}`

Frontend routes:

- `/platform/operational-scenario-testing`
- `/agency/scenario-testing`

## Explicit Exclusions

Phase 52.8 does not implement live provider calls, AI/LLM generation, parser execution, automated scenario execution, live rule evaluation, live pricing calculation, booking, ticketing, EMD issuance, background workers, schedulers, or automated operational authority.

Human authority remains final.
