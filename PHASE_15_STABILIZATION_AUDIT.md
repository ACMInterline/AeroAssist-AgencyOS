# Phase 15 Stabilization Audit

## Goal

Audit the Phase 15 ReportLab PDF export and document delivery lifecycle infrastructure for dependency behavior, renderer honesty, export storage safety, portal isolation, delivery state consistency, frontend clarity, seed idempotency, and documentation accuracy.

No new product features, public share links, client-triggered sending, mass email automation, payment links, document upload, electronic signatures, provider webhooks, background workers, SMTP secret resolver, browser renderer, pixel-perfect rendering claims, or legal/fiscal invoice compliance claims were added.

## Files Inspected

- `README.md`
- `BUILD_PHASES.md`
- `PHASE_13_PDF_EMAIL_DELIVERY_IMPLEMENTATION.md`
- `PHASE_13_STABILIZATION_AUDIT.md`
- `PHASE_14_DOCUMENT_DELIVERY_HARDENING.md`
- `PHASE_14_STABILIZATION_AUDIT.md`
- `PHASE_15_PRODUCTION_PDF_DELIVERY_INFRASTRUCTURE.md`
- `backend/requirements.txt`
- `backend/models.py`
- `backend/database.py`
- `backend/server.py`
- `backend/routers/documents.py`
- `backend/services/pdf_rendering_service.py`
- `backend/services/file_storage_service.py`
- `backend/services/seed_service.py`
- `frontend/src/lib/api.js`
- `frontend/src/pages/agency/DocumentDetailPage.jsx`
- `frontend/src/pages/portal/PortalDocumentDetailPage.jsx`

## Issues Found

- Failed PDF export records were created with `generated_at` set, which could make a failed export look partially generated in staff metadata.
- The retry endpoint allowed calls for deliveries whose `retry_status` was not `retry_available`, relying on the broader send path to reject some invalid states.
- The staff UI showed the generic `Send` action for failed deliveries; failed deliveries should expose the explicit retry path only when retry is available.
- The README production-readiness warning still referred to Phase 12 rather than Phase 15.

## Fixes Applied

- Removed `generated_at` from failed PDF export records. Failed records now remain `status=failed`, `storage_mode=not_generated`, `retention_policy=none`, and carry only the friendly `error_message`.
- Hardened `POST /api/agencies/{agency_id}/document-deliveries/{delivery_id}/retry` so only `retry_available` deliveries can be retried; `max_retries_reached` still returns its specific friendly error.
- Updated staff delivery controls so `Send` is shown only for draft/queued deliveries, while failed retryable deliveries use the `Retry` button.
- Updated the README production-readiness warning to describe Phase 15 accurately.

## Verified Without Code Changes

- ReportLab is declared in `backend/requirements.txt` as `reportlab>=4.2,<5`.
- `backend/services/pdf_rendering_service.py` imports ReportLab lazily, so backend import/startup does not depend on an eager ReportLab import.
- The PDF renderer parses stored `RenderedDocument.rendered_html`, strips active/remote tags, extracts text blocks, and does not fetch remote URLs or read local files.
- PDF output is documented and surfaced as a simplified snapshot PDF, not pixel-perfect browser rendering and not legal/fiscal invoice compliance.
- PDF and printable HTML downloads use the file storage abstraction and validate generated status, content type, checksum, and file size.
- Storage keys are server-generated and path traversal is rejected by resolved-path containment checks.
- Legacy `inline_base64` downloads use strict base64 decoding.
- Portal export list/download routes require the current portal client's visible document, generated status, and `client_visible=true`.
- Portal export projections omit storage keys, local paths, checksums, retention metadata, source snapshots, brand snapshots, delivery attempts, and internal notes.
- Portal UI remains read-only and download-only.
- `disabled` email mode records failed attempts and does not mark deliveries sent.
- `dev_console` mode records a simulated sent attempt without sending real email.
- SMTP remains guarded because no production secret resolver exists.
- No automatic sending, background worker, provider webhook, public link, payment link, upload, signature, or client-triggered delivery route exists.

## Validation Run

- `git status --short` before changes.
- `python3 -m py_compile backend/*.py backend/routers/*.py backend/services/*.py backend/scripts/*.py`
- Backend import smoke.
- Seed idempotency smoke.
- Export capability smoke.
- Printable HTML export/download smoke.
- PDF export/download smoke with ReportLab installed.
- Missing ReportLab diagnostic smoke using an import hook.
- File checksum/size tamper smoke.
- Portal PDF/HTML allowed download smoke.
- Portal cross-client denial smoke.
- Portal generation/send denial smoke.
- Delivery attachment validation smoke.
- Disabled, dev-console, and SMTP-incomplete send smoke.
- Delivery retry/cancel state smoke.
- Existing `backend/scripts/smoke_backend.py`.
- Existing `backend/scripts/check_portal_isolation.py`.
- `npm run build`.
- `git diff --check`.
- `git status --short` after changes.

## PDF Renderer Behavior And Limitations

Phase 15 uses ReportLab. PDF generation uses already-stored rendered HTML snapshots and writes a simplified readable PDF. It does not attempt browser layout parity, execute scripts, fetch images, load CSS, follow remote URLs, or read local files from HTML. If ReportLab is unavailable, the capability path reports PDF unavailable with a friendly diagnostic.

## Delivery Lifecycle Behavior

Delivery remains staff-controlled. Staff-created drafts can be sent manually; failed sends become retryable until `max_attempts` is reached. Each send/retry creates a `DocumentDeliveryAttempt`. During a send, the delivery moves to `sending` with `processing_state=processing` and lock metadata; terminal sent/failed/cancelled paths clear lock fields and set the appropriate retry and processing state. No worker consumes queue-state fields in Phase 15.

## Remaining Limitations

- PDF output is simplified ReportLab rendering, not full HTML/browser layout parity.
- No visual PDF QA pipeline is built into the app.
- Local filesystem export storage is still a foundation, not full object-storage lifecycle management.
- No production SMTP secret resolver exists.
- No queue worker, provider webhook, bounce handling, delivery monitoring, public links, client-triggered sends, automatic sends, uploads, signatures, payment links, airline integrations, or fiscal invoice compliance output exists.
- Formal migrations and broader automated authorization coverage remain future production-hardening work.

## Recommended Next Phase

Phase 16 should remain Production Delivery Operations And Secret Resolution: add a production secret resolver, email provider integration strategy, operational queue/worker design, provider webhook/bounce handling, and object-storage lifecycle policies before considering public links or automated delivery.
