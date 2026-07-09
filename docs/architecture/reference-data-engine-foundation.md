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

It does not implement provider integrations, AI/LLM behavior, live rule evaluation, pricing calculation, booking, ticketing, background workers, old `/admin` routes, automatic promotion, or automatic client sending.

Human authority remains final for domain governance, review, imports, operational use, and future production population.
