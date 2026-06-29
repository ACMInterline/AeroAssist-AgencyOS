# Reference Data Consumer Map

Phase 36.2.5 makes reference data governance explicit. The backend source of truth is `backend/services/reference_domain_usage_service.py`; the platform API exposes it through:

- `GET /api/platform/reference/domain-usage`
- `GET /api/platform/reference/domain-usage/{domain_key}`
- `GET /api/platform/reference/health`
- `GET /api/platform/reference/records/action-required`

## Governance Contract

- Platform owners manage global reference domains and records.
- Agencies consume active approved records.
- Agencies submit suggestions for corrections or additions.
- Agencies cannot mutate platform-owned foundation records or service catalogue records.
- Reference data remains separate from airline-specific acceptance policy. It supplies controlled lookup values, metadata, and service catalogue mappings.

## Domain Usage Fields

Each domain usage definition records:

- `domain_key`, `label`, and `description`
- `owner_scope` and `agency_behavior`
- `primary_consumers` and `secondary_consumers`
- `used_in_routes`, `used_in_models`, and `used_in_workflows`
- `required_metadata_fields` and `optional_metadata_fields`
- `bulk_import_supported`, `import_template_type`, and `enrichment_supported`
- `health_checks`, `operational_impact`, and `missing_data_risk_level`

The minimum governed domains are countries, cities, airports, airlines, currencies, languages, service catalogue, service categories, SSR/OSI codes, document types, pet species, pet breeds, special item categories, aircraft types, airline alliances, payment methods, and tax types.

## Health And Action Required

The old unexplained Important Records concept is replaced by Reference Health & Action Required. Records appear only when explicit logic finds:

- missing required metadata
- use by active workflows
- recent import/update activity
- review needs, warnings, or agency suggestions
- platform-pinned records
- high-risk operational domain issues

Each action-required item includes domain, record id, code, label, reason, severity, consumer impact, and recommended action.

## Imports And Enrichment

Domain-aware imports use explicit templates from `backend/services/reference_import_template_service.py`. Supported templates define required columns, optional columns, validation rules, duplicate handling, code normalization, metadata mapping, preview behavior, and apply summaries.

Enrichment packs are controlled metadata update packages. They enrich reference records with operational metadata used by requests, offers, rules, offer acceptance, booking readiness, and documents. Default packs cover airports, airlines, service catalogue SSR/EMD mappings, document compliance, pet species/breeds, and special item handling.

## Readiness

Reference governance is additive and non-blocking. `/api/readiness` exposes flags and counts under `reference_data`, including domain usage count, import template count, enrichment pack count, active service catalogue count, and action-required count.
