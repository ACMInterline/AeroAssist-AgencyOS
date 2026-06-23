# Phase 14 Stabilization Audit

## Goal

Audit Phase 14 document delivery hardening for file storage safety, export download correctness, retention metadata, delivery attempt and retry consistency, SMTP settings safety, seed idempotency, portal isolation, frontend clarity, and documentation accuracy.

No production PDF rendering, public share links, automatic sending, client-triggered sending, payment links, document upload, provider webhooks, or background worker infrastructure were added.

## Files Inspected

- `README.md`
- `BUILD_PHASES.md`
- `PHASE_13_PDF_EMAIL_DELIVERY_IMPLEMENTATION.md`
- `PHASE_13_STABILIZATION_AUDIT.md`
- `PHASE_14_DOCUMENT_DELIVERY_HARDENING.md`
- `.gitignore`
- `.env.example`
- `backend/models.py`
- `backend/database.py`
- `backend/server.py`
- `backend/routers/documents.py`
- `backend/services/file_storage_service.py`
- `backend/services/seed_service.py`
- `frontend/src/lib/api.js`
- `frontend/src/pages/agency/DocumentDetailPage.jsx`
- `frontend/src/pages/portal/PortalDocumentDetailPage.jsx`

## Issues Found

- File-backed downloads verified checksums but did not verify stored `file_size_bytes`.
- Export downloads did not explicitly reject records whose `content_type` no longer matched their `export_type`.
- Seed idempotency prevented duplicate export records, but an existing seeded file-backed export with a missing local file was not repaired.
- SMTP validation could raise an internal exception if legacy stored data had a non-numeric port.
- FastAPI metadata still described the API as being implemented through Phase 12.
- Phase 14 documentation did not mention file-size verification or seeded export file repair.

## Fixes Applied

- Added file-size verification to `get_export_bytes(...)`.
- Added download-time export metadata checks:
  - `print_html` exports must use `text/html`,
  - `pdf` exports must use `application/pdf`.
- Updated seed behavior so missing local files for existing seeded file-backed exports are regenerated without duplicating export records.
- Made SMTP validation return a friendly error for invalid stored port values.
- Updated FastAPI app description to Phase 14.
- Updated Phase 14 documentation to mention file-size verification and seed file repair.

## Verified Without Code Changes

- Default export storage path is `.local/document_exports`, and `.local/` is ignored by git.
- Storage keys are generated server-side and resolved under the configured export root.
- Staff export downloads require agency access and validate export/document ownership.
- Portal export list/download only returns generated, client-visible exports linked to visible documents for the current portal client.
- Portal users cannot create exports, deliveries, sends, retries, archives, or access delivery attempts.
- Portal export projection omits storage keys, bucket/path data, checksums, retention metadata, delivery records, and attempt records.
- PDF export continues to fail honestly without creating fake PDF bytes.
- Export archive updates status and archive metadata; it does not hard delete export records or files.
- Disabled email mode records failed attempts and never marks a delivery sent.
- Dev-console mode records a simulated sent attempt without sending real email.
- SMTP incomplete/unresolved-secret mode fails safely without exposing raw credentials.
- Retry remains a staff-controlled endpoint.
- Staff UI shows storage, export status, retention, attempts, retry state, and email validation state without public link/share/payment/client-send controls.
- Portal UI remains read-only.

## Validation Run

- `git status --short` before changes.
- `python3 -m py_compile backend/*.py backend/routers/*.py backend/services/*.py backend/scripts/*.py`
- Backend import smoke.
- Seed idempotency smoke.
- Printable HTML export/download smoke.
- PDF honest-unavailable smoke.
- File path traversal denial smoke.
- Portal allowed download smoke.
- Portal cross-client denial smoke.
- Portal non-visible export denial smoke.
- Disabled, dev-console, and SMTP-incomplete send smoke.
- Delivery attempt/retry smoke.
- Email settings validation smoke.
- Existing `backend/scripts/smoke_backend.py`.
- Existing `backend/scripts/check_portal_isolation.py`.
- `npm run build`.
- `git diff --check`.
- `git status --short` after changes.

## Remaining Limitations

- Real PDF generation remains unavailable until a renderer and visual QA path are selected.
- Local filesystem storage is a foundation only; production object storage, lifecycle policy, and migration tooling remain future work.
- No production SMTP secret resolver exists.
- No background queue, retry worker, provider webhook processing, bounce handling, or delivery monitoring exists.
- No public links, expiring URLs, client-triggered sends, automatic sends, bulk sends, payment links, document upload, signatures, or fiscal invoice compliance output exists.
- Broader automated authorization and migration coverage remain future production-hardening work.

## Recommended Next Phase

Phase 15 should be Production PDF Rendering And Delivery Infrastructure: choose and verify a real PDF renderer with visual QA, add production object storage lifecycle, integrate a secret resolver, and add queue/retry/provider webhook handling before considering public links or automated delivery.
