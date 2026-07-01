# GDS Parser Foundation

Phase 36.6 adds a governed parser foundation for cryptic GDS, itinerary, ticket, EMD, and pricing text. It is deterministic and internal-only. It does not connect to GDS/NDC/provider systems, call external AI parsers, or automatically import parser output into booking, ticket, or EMD mirrors.

## Core Records

- `GdsParserProfile` defines parser families by provider family, input format, parser strategy, and confidence thresholds.
- `GdsParserVersion` stores versioned rule metadata, schemas, limitations, notes, and activation status.
- `GdsParserRun` stores one parser execution, detected input type, confidence, counts, warnings/errors, extracted payload, and normalized preview.
- `GdsParsedEntity` stores individual extracted passengers, segments, tickets, EMDs, SSR/OSI, pricing, contacts, remarks, and confidence/status.
- `GdsParseCorrection` stores human accept/correct/reject/ignore/add-missing actions.
- `GdsParseSample` is extended as the governed training sample shape and stored in `gds_parse_training_samples`.
- `GdsParserEvaluationRun` stores deterministic evaluation summaries against approved/promoted samples.

## Parser Behavior

The parser extracts only values present in the text:

- record locator
- passenger names
- itinerary segments
- ticket and EMD numbers
- SSR and OSI lines
- obvious pricing totals
- fare basis, contact, and remark lines

Unknown or ambiguous values are omitted or left null. Low-confidence input produces warnings and `manual_review_required` instead of creating operational mirrors.

## Booking Import Integration

`BookingImportDraft` now stores:

- `latest_parser_run_id`
- `parser_profile_id`
- `parser_version_id`
- `overall_confidence`
- `parsed_entity_counts_json`
- `normalized_preview_json`

Import remains explicit through the existing manual import action. Parsing a draft never creates booking workspaces, booking records, tickets, or EMDs by itself.

## APIs And UI

Agency parser APIs live under `/api/agencies/{agency_id}/gds-parser/*`, with UI at `/agency/gds-parser`.

Platform governance APIs live under `/api/platform/gds-parser/*`, with UI at `/platform/gds-parser`.

## Documents

`DocumentContextService` supports `gds_parser_run` as a source context. Document types `gds_parse_review_summary` and `booking_import_review_summary` render parser confidence, extracted entities, warnings, corrections, and training sample status.

## Phase 36.7 Policy Ingestion Relationship

Airline policy ingestion is separate from the GDS parser. Phase 36.7 stores policy-derived SSR/OSI and GDS examples in policy communication candidate records so later phases can decide whether reviewed policy examples should inform parser samples or SSR/OSI generation. No parser profile, parser version, booking import, or live GDS behavior is changed by policy ingestion.

## Boundaries

- No live GDS/NDC/provider connection.
- No external AI parser.
- No automatic import.
- No full host grammar guarantee.
- No ticketing, EMD issuance, exchange, refund, void, payment, invoice/accounting, BSP/ARC, or settlement execution.
