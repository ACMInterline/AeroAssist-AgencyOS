# Knowledge Quality Assurance Foundation

Phase 52.6 adds the metadata-only Knowledge Quality Assurance Foundation.

It creates a QA review layer for airline knowledge production. Reviews record findings, severity, requested changes, reviewer metadata, approval recommendations, and governance links. They do not auto-approve, publish, execute rules, use AI, call providers, run background workers, or replace human authority.

## Scope

- Collection: `knowledge_quality_assurance_reviews`
- Service: `backend/services/knowledge_quality_assurance_service.py`
- Platform API: `/api/platform/knowledge-quality-assurance`
- Agency API: `/api/agencies/{agency_id}/knowledge-quality-assurance`
- Platform UI: `/platform/knowledge-quality-assurance`
- Agency UI: `/agency/knowledge-quality-assurance`
- Module catalog entries: Platform `Knowledge QA`, Agency `Knowledge QA`

## Checks

Knowledge QA reviews support these metadata checks:

- `missing_evidence`
- `missing_effective_dates`
- `missing_pricing_applicability`
- `conflicting_support_status`
- `incomplete_service_parameters`
- `missing_documents`
- `unsupported_reference_values`
- `stale_review`
- `low_confidence`
- `operational_validation_pending`
- `duplicate_policy_card`
- `conflicting_rule`
- `incomplete_pricing_formula`

## Review Metadata

Each review stores:

- `review_reference`
- `target_type`
- `target_id`
- `airline_code`
- `service_family`
- `service_code`
- `qa_status`
- `issues`
- `severity`
- `reviewer`
- `requested_changes`
- `approval_recommendation`
- `governance_links`
- `created_at`
- `updated_at`

`approval_recommendation` is advisory metadata only. It is not approval, publication, or operational authority.

## Relationships

Knowledge QA can review metadata produced by Reference Data Engine, Knowledge Import Templates, Visual Policy Editor, Pricing Formula Builder, Operational Rule Composer, Service Parameter Taxonomies, and the Chapter 50 operational intelligence pipeline.

The QA layer does not add new intelligence. It prepares the system for scenario testing, human-reviewed real airline data population, and governance readiness.

## Boundaries

Human authority remains final.

Phase 52.6 must not add:

- automatic approval
- publishing
- rule execution
- live evaluation
- AI/LLM generation
- provider integrations
- background workers
- booking, ticketing, or EMD issuance
- payment integrations
- automatic client sending
- operational automation
