# Operational Rule Composer Foundation

Phase 52.5 adds the metadata-only Operational Rule Composer Foundation.

It creates a no-code metadata layer for compound airline passenger service restrictions and outcomes. It does not execute rules, evaluate passenger cases, calculate pricing, use AI, call providers, run background workers, send messages, book, ticket, issue EMDs, process payments, or make automatic decisions.

## Scope

- Collection: `operational_rule_composer_rules`
- Service: `backend/services/operational_rule_composer_service.py`
- Platform API: `/api/platform/operational-rule-composer`
- Agency API: `/api/agencies/{agency_id}/rule-composer`
- Platform UI: `/platform/operational-rule-composer`
- Agency UI: `/agency/rule-composer`
- Module catalog entries: Platform `Operational Rule Composer`, Agency `Rule Composer`

## Rule Metadata

Operational Rule Composer records store:

- `rule_reference`
- `rule_name`
- `rule_family`
- `service_family`
- `service_codes`
- `applies_to`
- `conditions`
- `any_conditions`
- `result`
- `severity`
- `client_message`
- `internal_message`
- `evidence_links`
- `governance_links`
- `parameter_taxonomy_links`
- effective dates
- lifecycle status

The UI exposes no-code sections for overview, applicability, all conditions, any conditions, result, messages, evidence, governance, lifecycle, and safety boundaries.

## Supported Operators

Phase 52.5 registers these operators as metadata values only:

- `=`
- `!=`
- `>`
- `>=`
- `<`
- `<=`
- `in`
- `not_in`
- `contains`
- `exists`
- `not_exists`
- `between`
- `between_month_day`
- `date_before`
- `date_after`
- `route_includes_country`
- `route_crosses_border`
- `outside_range`

The operators are recorded for future scenario testing and human-reviewed airline data population. They are not executable rule-engine behavior in Phase 52.5.

## Relationship To Chapter 52

Reference Data Engine provides controlled values. Knowledge Import Templates describe future data population schemas. Visual Policy Editor stores human-readable service policy-card metadata. Pricing Formula Builder stores pricing formula metadata. Operational Rule Composer stores compound operational rule metadata as a separate layer so restrictions, outcomes, pricing, policy wording, capability, and service parameter definitions remain distinct.

Phase 52.6 adds Knowledge Quality Assurance as a metadata-only review layer over rule-composer records. Knowledge QA can record conflicting rule, missing evidence, unsupported reference values, stale review, operational validation pending, or requested changes, but it does not execute rules, evaluate live cases, auto-approve, publish, call providers, use AI, run workers, or replace human authority.

## Boundaries

Human authority remains final.

Phase 52.5 must not add:

- rule execution
- live rule evaluation
- pricing calculation
- provider integrations
- AI/LLM generation
- background workers
- automatic decisions
- booking, ticketing, or EMD issuance
- payment integrations
- automatic client sending
- old `/admin` routes
