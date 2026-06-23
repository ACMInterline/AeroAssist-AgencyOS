# Phase 15 Production PDF Rendering And Delivery Infrastructure

## Goal

Add an honest production PDF export path and strengthen delivery validation while preserving the product principle: documents are agency-generated, snapshot-based, and staff-controlled.

No public share links, payment links, client-triggered sending, mass email automation, marketing campaigns, uploads, signatures, provider webhooks, refund/payment/ticketing execution, airline integrations, or legal/fiscal invoice compliance claims were added.

## PDF Renderer Decision

Phase 15 uses ReportLab as the PDF renderer.

Why:

- It is a Python dependency that runs inside the current FastAPI backend.
- It does not require browser automation or Chromium system dependencies.
- It is suitable for deterministic, server-side PDF generation on a small VPS.

Important limitation:

- The generated PDF is a simplified snapshot PDF derived from stored `RenderedDocument.rendered_html`.
- It is not a pixel-perfect browser rendering of the HTML document.
- It does not claim legal or fiscal invoice compliance.

## Dependency Changes

Updated `backend/requirements.txt`:

- `reportlab>=4.2,<5`

Hostinger/VPS requirement:

- Install backend requirements with `pip install -r backend/requirements.txt`.
- No Chromium/Playwright runtime is required for the Phase 15 ReportLab path.
- Optional visual QA tooling such as Poppler (`pdftoppm`) can be installed separately when browser-grade PDF inspection is needed.

## Backend Services Added

- `backend/services/pdf_rendering_service.py`

The service:

- accepts stored rendered HTML, document title, agency ID, and document ID,
- strips active/remote HTML elements such as scripts, styles, iframes, embeds, links, meta tags, and images,
- extracts readable text blocks from the stored HTML snapshot,
- renders a simplified PDF with ReportLab,
- returns renderer capability diagnostics,
- fails with a friendly diagnostic if ReportLab is missing or rendering fails.

## Backend Endpoints Added Or Hardened

Added:

- `GET /api/agencies/{agency_id}/document-export-capabilities`

It returns:

- printable HTML availability,
- PDF availability,
- renderer name,
- renderer version,
- renderer diagnostic.

Hardened:

- `POST /api/agencies/{agency_id}/documents/{document_id}/exports`
  - `print_html` remains file-backed.
  - `pdf` now generates real ReportLab PDF bytes when available.
  - PDF exports are marked generated only after valid PDF bytes are saved.
- Staff and portal export downloads continue through the same ownership, visibility, checksum, file-size, and content-type checks.
- Delivery send/retry now validates any attached export before processing, including file existence, checksum, file size, content type, generated status, and document ownership.
- Delivery cancellation is limited to draft, queued, failed, or retry-available states.

## Export Storage Behavior

PDF and printable HTML exports use the Phase 14 file storage abstraction.

Generated PDF records store:

- `export_type=pdf`
- `content_type=application/pdf`
- `storage_mode=file_path`
- `storage_bucket=local`
- `storage_key`
- `file_size_bytes`
- `checksum_sha256`
- `retention_policy`
- `retention_expires_at`

No public URLs are created.

## Portal Behavior

Portal users can list and download only generated, client-visible exports for visible documents belonging to their current portal client.

Portal users cannot:

- generate exports,
- send deliveries,
- retry deliveries,
- archive exports,
- access delivery attempts,
- see storage keys, storage buckets, checksums, retention metadata, source snapshots, or internal notes.

## Delivery Behavior

Delivery remains manual and staff-controlled.

- `dev_console` remains a safe simulated send path.
- `smtp` remains guarded because no production secret resolver exists yet.
- No automatic send or background worker was added.
- No provider webhook handling was added.
- Delivery records include local queue-state metadata (`queued_at`, `locked_at`, `locked_by`, `scheduled_for`, and `processing_state`) for manual operational tracking only. No worker consumes those fields in Phase 15.

## Seed Data

Seed data:

- keeps dev-console email settings only,
- keeps a printable HTML demo export,
- creates a PDF demo export only when ReportLab is available,
- repairs missing seeded export files without duplicating export records,
- does not seed real SMTP credentials.

## Frontend Changes

Staff document detail now shows:

- export capability status,
- PDF renderer diagnostic,
- enabled PDF generation when available,
- export type, status, content type, file size, checksum, generated date, storage mode, and retention state,
- delivery attempts/retry state.

Portal document detail remains read-only and labels downloads as `PDF`, `Printable HTML`, or `Document`.

## Validation

Run for this phase:

- Backend compile.
- Backend import smoke.
- Seed idempotency smoke.
- Export capability smoke.
- Printable HTML export/download smoke.
- PDF export/download smoke.
- File checksum/size validation smoke.
- Portal PDF/HTML allowed download smoke.
- Portal cross-client denial smoke.
- Delivery attachment validation smoke.
- Disabled, dev-console, and SMTP-incomplete send smoke.
- Delivery retry/cancel state smoke.
- Existing backend smoke.
- Existing portal isolation smoke.
- Frontend production build.
- `git diff --check`.

## Remaining Production Risks

- PDF output is simplified ReportLab rendering, not full browser layout parity.
- No production object-storage lifecycle exists beyond the local storage abstraction.
- No production SMTP secret resolver exists.
- No background queue, worker, provider webhook, bounce handling, or delivery monitoring exists.
- No public links, client-triggered sends, automatic sends, payment links, signatures, uploads, marketing campaigns, airline integrations, or fiscal invoice compliance output exists.
- Broader automated authorization and migration coverage remain future hardening work.

## Exact Next Recommended Phase

Phase 16 should be Production Delivery Operations And Secret Resolution: add a production secret resolver, email provider integration strategy, queue/worker design, operational retry controls, provider webhook/bounce handling, and object-storage lifecycle policies before public links or automated delivery are considered.
