# Phase 6 Airline Intelligence Implementation

## Goal

Add the Airline Intelligence foundation as platform-owned, searchable, source-backed decision support with agency-specific overrides and annotations.

This phase does not automate policy evaluation, pricing, scraping, GDS/NDC/OTA integrations, refunds/exchanges, branded PDFs, or client portal exposure.

## Models Added

- `AirlineProfile`
- `AirlineKnowledgeItem`
- `AirlineProcedure`
- `AirlineEmdRuleNote`
- `AirlineKnowledgeSource`
- `AgencyAirlineOverride`
- `AirlineKnowledgeUsageEvent`

Supporting enums were added for airline status, knowledge category, review status, confidence, procedure type/channel, source type/reliability, override target/mode/status, and usage context.

## Backend Endpoints Added

Platform maintenance:

- `GET /api/platform/airlines`
- `POST /api/platform/airlines`
- `GET /api/platform/airlines/{airline_id}`
- `PUT /api/platform/airlines/{airline_id}`
- `GET /api/platform/airlines/{airline_id}/knowledge`
- `POST /api/platform/airlines/{airline_id}/knowledge`
- `GET /api/platform/airline-knowledge/{knowledge_id}`
- `PUT /api/platform/airline-knowledge/{knowledge_id}`
- `POST /api/platform/airline-knowledge/{knowledge_id}/publish`
- `POST /api/platform/airline-knowledge/{knowledge_id}/archive`
- `GET /api/platform/airlines/{airline_id}/procedures`
- `POST /api/platform/airlines/{airline_id}/procedures`
- `PUT /api/platform/airline-procedures/{procedure_id}`
- `GET /api/platform/airlines/{airline_id}/emd-notes`
- `POST /api/platform/airlines/{airline_id}/emd-notes`
- `PUT /api/platform/airline-emd-notes/{emd_note_id}`
- `GET /api/platform/airline-sources`
- `POST /api/platform/airline-sources`

Agency read/search and overrides:

- `GET /api/agencies/{agency_id}/airline-intelligence/search`
- `GET /api/agencies/{agency_id}/airlines/{airline_id}/intelligence`
- `GET /api/agencies/{agency_id}/airline-knowledge/{knowledge_id}`
- `GET /api/agencies/{agency_id}/airlines/{airline_id}/overrides`
- `POST /api/agencies/{agency_id}/airlines/{airline_id}/overrides`
- `PUT /api/agencies/{agency_id}/airline-overrides/{override_id}`
- `POST /api/agencies/{agency_id}/airline-overrides/{override_id}/archive`
- `POST /api/agencies/{agency_id}/airline-knowledge/{knowledge_id}/usage`

## Frontend Routes Added

Platform:

- `/platform/airlines`
- `/platform/airlines/:airlineId`
- `/platform/airline-knowledge/:knowledgeId`

Agency:

- `/agency/airline-intelligence`
- `/agency/airline-intelligence/:airlineId`
- `/agency/airline-knowledge/:knowledgeId`

## Components Added

- `AirlineStatusBadge`
- `KnowledgeCategoryBadge`
- `ReviewStatusBadge`
- `ConfidenceBadge`

## Workflow Links Added

- Request detail includes a search panel for airline intelligence service notes.
- Offer detail includes a policy/service note search panel.
- Booking detail includes a servicing/EMD/ticketing note search panel.

These links pass simple query parameters such as airline code and service code. They do not evaluate feasibility, price services, or automate servicing.

## Seed Data Added

- Three fake/demo airlines:
  - `NX` Demo Network Airways
  - `LC` Demo LowCost Air
  - `RG` Demo Regional Connect
- Published knowledge examples for PETC, WCHR/WCHS/WCHC, UMNR, baggage, disruption, and EMD support.
- Procedure examples for special service requests, agency support, EMD handling, and wheelchair assistance.
- EMD/RFIC/RFISC note examples for PETC, WCHR, and UMNR.
- Source examples for official website placeholders, internal agency experience, and ATPCO/IATA-style reference notes.
- One agency PETC annotation override for the demo agency.

## Override Behavior

Global records remain platform-owned and do not carry `agency_id`.

Agency overrides always carry `agency_id`, point to a global target, and can:

- `replace`: prefer agency text in agency view.
- `augment`: append agency text to the global text.
- `annotate`: show an internal agency note alongside global text.

Overrides do not mutate global records and are not visible to other agencies.

## Known Limitations

- No automated rule engine.
- No pricing automation.
- No GDS, NDC, OTA, airline API, or scraping integration.
- No external document ingestion.
- No PDF output.
- No refund/exchange workflow.
- No client portal airline knowledge access.
- No immutable published version table yet; records carry review and publication metadata as the foundation.

## Next Recommended Phase

Implement refund/exchange tracking and/or branded document output, while keeping Airline Intelligence as human decision support until production persistence, authentication, versioning, and tenant hardening are completed.
