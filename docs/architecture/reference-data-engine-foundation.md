# Reference Data Engine Foundation

Phase 52.1 adds the metadata-only Reference Data Engine foundation required for airline operational knowledge production.

The foundation creates `reference_data_domains` plus platform and agency metadata CRUD/read routes:

- Platform API: `/api/platform/reference-data-engine`
- Agency API: `/api/agencies/{agency_id}/reference-data-engine`
- Platform UI: `/platform/reference-data-engine`
- Agency UI: `/agency/reference-data-engine`

## Purpose

The Reference Data Engine provides governed domain metadata for values used by airline operational knowledge, service parameter taxonomies, request segment service precision, operational evaluations, feasibility, recommendations, and offer intelligence.

It stores domains such as airlines, airports, countries, cities, currencies, aircraft types/families, cabin classes, seat types, passenger types, service codes/families, SSR codes, OSI templates, RFIC/RFISC, pet species/breeds, breed risk flags, container types, document types, vaccination types, mobility levels, wheelchair device types, battery types, medical equipment types, route types, flight types, fare bundles, pricing units/categories, formula components, temperature zones, seasonal restriction types, and travel purposes.

## Data Shape

Each `reference_data_domains` record stores:

- `id`, `agency_id`, `domain_reference`, `domain_code`, `domain_label`, `domain_description`
- `records`, `aliases`, `normalization_rules`, `validation_rules`
- `import_template_reference`, `governance_status`, `review_status`, `active`
- `created_at`, `updated_at`

The service also returns metadata-only boundary flags showing that provider integrations, AI, live evaluation, pricing calculation, background workers, and old `/admin` routes are disabled.

## Boundaries

Phase 52.1 does not add new intelligence. It supplies governed reference domains that later airline operational knowledge population and scenario testing can reuse.

## Knowledge Import Template Relationship

Phase 52.2 adds `knowledge_import_templates` as reusable metadata schemas for future reference data and airline knowledge population. Reference Data Engine domains may point to import-template references, but templates do not parse files, scrape, use AI, call providers, run workers, automatically import data, or replace human review.

## Visual Policy Editor Relationship

Phase 52.3 adds `visual_policy_editor_cards` as structured airline service policy-card metadata. Visual Policy Editor cards may use Reference Data Engine domains for controlled values in future data population workflows, but Phase 52.3 does not execute policies, evaluate rules, calculate pricing, call providers, use AI/LLM generation, run background workers, create old `/admin` routes, or replace human authority.

## Pricing Formula Builder Relationship

Phase 52.4 adds `pricing_formula_builders` as no-code pricing formula metadata. Pricing Formula Builder records may use Reference Data Engine domains for controlled currencies, fare bundles, pricing units, route types, flight types, pricing categories, and formula component vocabulary, but Phase 52.4 does not calculate live prices, integrate payments, call providers, use AI, run workers, automatically send to clients, or replace human authority.

## Operational Rule Composer Relationship

Phase 52.5 adds `operational_rule_composer_rules` as no-code compound rule metadata. Operational Rule Composer records may use Reference Data Engine domains for controlled airlines, airports, countries, route types, flight types, cabins, service codes, service families, passenger types, pet/container/document/vaccination metadata, mobility levels, wheelchair devices, batteries, medical equipment, temperature zones, and seasonal restrictions. Phase 52.5 does not execute rules, evaluate live cases, calculate prices, call providers, use AI, run workers, make automatic decisions, or replace human authority.

## Knowledge Quality Assurance Relationship

Phase 52.6 adds `knowledge_quality_assurance_reviews` as metadata-only QA reviews. Knowledge QA may flag unsupported reference values, stale review, missing evidence, or operational validation pending for Reference Data Engine domains, but it does not auto-approve, publish, execute rules, call providers, use AI, run workers, or replace human authority.

It does not implement provider integrations, AI/LLM behavior, live rule evaluation, pricing calculation, booking, ticketing, background workers, old `/admin` routes, automatic promotion, or automatic client sending.

Human authority remains final for domain governance, review, imports, operational use, and future production population.
