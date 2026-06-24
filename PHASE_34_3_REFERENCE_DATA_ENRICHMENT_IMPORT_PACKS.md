# Phase 34.3 — Reference Data Enrichment Import Packs

Phase 34.3 adds safe platform-owner enrichment packs and normalization workflows for country, airport, airline, currency, language, and region reference data.

## Implemented

- Starter import pack directory at `data/reference_packs/`.
- Platform enrichment APIs under `/api/platform/reference/enrichment/*`.
- Platform console `Enrichment Packs` tab at `/platform/reference`.
- Non-destructive import reports with inserted, updated, skipped, failed, warnings, missing links, and row details.
- Enriched readiness counts for airports, airlines, currencies, languages, country major-airport coverage, country national-carrier coverage, and missing country links.

## CSV Templates

The starter templates are examples only, not full global datasets:

- `countries_enriched.csv`
- `airports_core.csv`
- `airlines_core.csv`
- `currencies_core.csv`
- `languages_core.csv`
- `continents_regions.csv`

Templates can be fetched by platform users via:

- `GET /api/platform/reference/enrichment/templates`
- `GET /api/platform/reference/enrichment/template/{template_name}`

## Import Modes

- `insert_only`: create missing records and skip existing records.
- `update_missing_only`: fill missing metadata only; verified records are not overwritten.
- `update_all_non_verified`: replace non-verified records while preserving verified records.
- `force_update`: intentionally replace existing metadata and labels.

Default behavior is dry-run plus `update_missing_only`.

## Normalization Rules

- Country ISO2 must be 2 uppercase letters; ISO3 must be 3 uppercase letters.
- Airport IATA must be 3 uppercase letters; ICAO must be 4 uppercase letters when present.
- Airline IATA must be 2 alphanumeric characters when present.
- Currency ISO must be 3 uppercase letters.
- Language ISO639-1 must be 2 lowercase letters when present.
- Population estimates must be integers or blank.
- Latitude/longitude must be numeric or blank.
- Major airports, official languages, and major airlines are limited to 3 entries.

## Cross-Link Behavior

Missing linked airports, airlines, currencies, languages, countries, or regions produce warnings and `missing_links`; they do not fail an otherwise valid import row by default.

Country metadata stores useful cross-link fields such as `major_airport_codes`, `national_carrier_iata`, `major_airline_iata_codes`, `currency_iso_code`, `official_language_codes`, and `official_language_names`.

## Platform vs Agency

- Platform owners/admins can use enrichment templates, dry-run imports, commit imports, review reports, and inspect batches.
- Agencies continue to consume approved global records and submit suggestions only.
- Platform enrichment tooling, exports, approval queues, edit/archive controls, and import tabs are not exposed to agency users.

## Known Limits

- No automated external enrichment.
- No full global dataset is included.
- No airline policy engine, pricing engine, offer builder, GDS/NDC import, invoices, payments, or portal expansion is introduced.
- No destructive seed/reset is introduced.
