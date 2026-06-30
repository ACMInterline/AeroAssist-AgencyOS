# Booking Import Draft Foundation

Phase 36.4.6 adds `BookingImportDraft` as a staging record for cryptic GDS text, itinerary confirmations, manual text, email imports, PDF imports, or other imported booking evidence. Phase 36.6 connects drafts to the governed GDS parser foundation.

## Purpose

The import draft preserves raw text exactly for audit and gives staff a conservative parsed preview before any internal mirror records are created.

## Lifecycle

1. Create draft with raw text and source metadata.
2. Parse draft using deterministic governed parser profiles/versions.
3. Review structured preview, confidence, warnings, and extracted entities.
4. Import explicitly as a manual booking workspace/record.
5. Optionally create ticket and EMD mirrors only when explicitly requested.

## Parsed Preview

The parser may extract:

- record locator
- passenger name lines
- flight segment-like lines
- ticket numbers
- EMD numbers
- SSR lines
- OSI lines
- confidence and entity counts
- warnings for missing or ambiguous data

The parser does not call GDS, NDC, email, PDF, OCR, AI, or supplier providers.

The agency UI presents parsed imports as agent-friendly passenger, segment, SSR/OSI, ticket number, EMD number, confidence, entity count, and warning panels. The full parsed JSON is retained in a collapsed advanced section for audit/debug review only.

## API Entry Points

- `GET /api/agencies/{agency_id}/booking-import-drafts`
- `POST /api/agencies/{agency_id}/booking-import-drafts`
- `GET /api/agencies/{agency_id}/booking-import-drafts/{draft_id}`
- `POST /api/agencies/{agency_id}/booking-import-drafts/{draft_id}/parse`
- `POST /api/agencies/{agency_id}/booking-import-drafts/{draft_id}/import-as-booking`
- `POST /api/agencies/{agency_id}/gds-parser/booking-import-drafts/{draft_id}/parse`
- `GET /api/agencies/{agency_id}/gds-parser/runs/{parser_run_id}`
- `GET /api/agencies/{agency_id}/gds-parser/runs/{parser_run_id}/entities`
- `POST /api/agencies/{agency_id}/gds-parser/corrections`

## Deferred

Full host grammar coverage, AI-assisted normalization, provider reconciliation, raw attachment files, OCR, email ingestion, supplier health checks, and live provider imports remain future phases.
