# Phase 34.2 — Platform Reference Data Console and Enriched Countries

Phase 34.2 separates platform-owned reference management from agency reference consumption and adds structured country metadata for operational readiness.

## Implemented

- Platform-only Reference Data Management Console at `/platform/reference`.
- Dedicated platform APIs under `/api/platform/reference/*` for domains, global records, suggestions, import, export, and record cards.
- Agency `/agency/reference` remains a consume-and-suggest surface; agencies cannot edit, import, export, archive, approve, or create global reference records through the platform console.
- Domain metadata management for domain code, label, description, category, active status, sort order, and future schema metadata.
- Global record filters for active/inactive records, quality status, continent, missing ISO3, missing capital IATA, missing currency, missing airports, and missing national carrier.
- Important record cards at `/platform/reference/records/{record_id}`.

## Enriched Countries

Country records continue to use `global_reference_records`, with structured metadata stored in `metadata_json` for legacy compatibility:

- ISO and geography: `iso2_code`, `iso3_code`, `continent`, `capital_city`, `capital_iata_code`.
- Aviation: `major_airports`, `national_carrier`, `major_airlines`.
- Locale/commercial metadata: `official_languages`, `currency_name`, `currency_iso_code`, `population_estimate`, `population_estimate_year`.
- Governance metadata: `travel_notes`, `data_quality_status`, `source_notes`, `updated_by_user_id`, `reviewed_by_user_id`, `reviewed_at`.

Validation enforces uppercase ISO2/ISO3, airport IATA codes, two-character airline IATA codes where supplied, max-3 airport/language/airline arrays, integer population values, and known quality statuses.

## Bulk Import / Export

- Platform CSV import accepts the legacy columns plus enriched country columns.
- Dry-run import is supported and remains non-destructive.
- Committed imports upsert by `domain + code`; no destructive deletes or reset behavior is introduced.
- Platform export supports CSV/JSON for selected domains, enriched countries, service catalogue records, suggestions, and import batches.

## Readiness

`/api/readiness` includes `platform_reference_console` with:

- `platform_reference_console_enabled`
- `enriched_country_schema_enabled`
- `platform_reference_import_enabled`
- `platform_reference_export_enabled`
- `platform_reference_suggestion_review_enabled`
- `country_record_count`
- `enriched_country_record_count`
- `countries_missing_iso3_count`
- `countries_missing_capital_iata_count`
- `reference_record_card_enabled`
- `readiness_required: false`

## Validation

- `backend/scripts/smoke_platform_reference_console.py` verifies platform domain listing, owner-only record management, country validation, agency approval denial, platform suggestion approval, dry-run import, committed upsert import, CSV/JSON export, record cards, and readiness flags.
- Regression smokes remain available for reference core, governance, form profiles, segment-scoped requests, blueprint alignment, agency website/CMS, branding, operational request builder, and request intake conversion.

## Known Limits

- No external country data provider is integrated.
- No automatic enrichment, scraping, airline execution, GDS/NDC integration, pricing, or payment behavior is introduced.
- Agency-local reference overrides remain future work.
