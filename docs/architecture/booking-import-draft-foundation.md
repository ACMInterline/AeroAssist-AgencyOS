# Booking Import Draft Foundation

Phase 36.4.6 adds `BookingImportDraft` as a staging record for cryptic GDS text, itinerary confirmations, manual text, email imports, PDF imports, or other imported booking evidence.

## Purpose

The import draft preserves raw text exactly for audit and gives staff a conservative parsed preview before any internal mirror records are created.

## Lifecycle

1. Create draft with raw text and source metadata.
2. Parse draft using deterministic, low-confidence extraction.
3. Review parsed preview.
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
- warnings for missing or ambiguous data

The parser does not call GDS, NDC, email, PDF, OCR, AI, or supplier providers.

The agency UI presents parsed imports as agent-friendly passenger, segment, SSR/OSI, ticket number, EMD number, and warning panels. The full parsed JSON is retained in a collapsed advanced section for audit/debug review only.

## API Entry Points

- `GET /api/agencies/{agency_id}/booking-import-drafts`
- `POST /api/agencies/{agency_id}/booking-import-drafts`
- `GET /api/agencies/{agency_id}/booking-import-drafts/{draft_id}`
- `POST /api/agencies/{agency_id}/booking-import-drafts/{draft_id}/parse`
- `POST /api/agencies/{agency_id}/booking-import-drafts/{draft_id}/import-as-booking`

## Deferred

Advanced parser training, AI-assisted normalization, provider reconciliation, raw attachment files, OCR, email ingestion, supplier health checks, and live provider imports remain future phases.
