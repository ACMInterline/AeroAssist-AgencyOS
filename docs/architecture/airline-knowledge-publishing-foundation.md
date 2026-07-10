# Airline Knowledge Publishing Foundation

Phase 52.7 adds the metadata-only Airline Knowledge Publishing Foundation.

It creates a controlled publication workflow record for approved airline operational knowledge. Publications describe what knowledge is included, which QA reviews support it, where it may be visible, and whether consumers are ready. They do not publish automatically, execute recommendations, call providers, use AI, run background workers, or replace human authority.

## Scope

- Collection: `airline_knowledge_publications`
- Service: `backend/services/airline_knowledge_publishing_service.py`
- Platform API: `/api/platform/airline-knowledge-publishing`
- Agency API: `/api/agencies/{agency_id}/published-knowledge`
- Platform UI: `/platform/knowledge-publishing`
- Agency UI: `/agency/published-knowledge`
- Module catalog entries: Platform `Knowledge Publishing`, Agency `Published Knowledge`

## Publication Metadata

Each publication stores:

- `publication_reference`
- `publication_name`
- `airline_codes`
- `service_families`
- `included_knowledge_version_ids`
- `included_policy_cards`
- `included_pricing_formulas`
- `included_rules`
- `qa_review_ids`
- `publication_status`
- `release_channel`
- `effective_from`
- `effective_until`
- `supersedes_publication_ids`
- `rollback_plan`
- `consumer_readiness`
- `AOIE_ready`
- `agency_visibility`
- `created_at`
- `approved_at`
- `published_at`

`published_at` is recorded metadata. It is not an execution trigger.

## Relationships

Airline Knowledge Publishing connects the Chapter 52 production layers:

- Reference Data Engine
- Knowledge Import Templates
- Visual Policy Editor
- Pricing Formula Builder
- Operational Rule Composer
- Knowledge Quality Assurance

It also links to Chapter 50 knowledge versions, operational evaluations, feasibility, recommendations, offer intelligence, and operational intelligence case metadata when needed.

## Boundaries

Human authority remains final.

Phase 52.7 must not add:

- automatic publication
- recommendation execution
- live rule execution
- live evaluation
- AI/LLM generation
- provider integrations
- background workers
- booking, ticketing, or EMD issuance
- payment integrations
- automatic client sending
- operational automation
