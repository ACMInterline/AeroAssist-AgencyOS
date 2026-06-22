# Phase 13 Stabilization Audit

## Goal

Audit the Phase 13 printable document export and email delivery foundation for route safety, portal visibility, download correctness, email-settings safety, seed idempotency, frontend consistency, and documentation accuracy.

No new product features, real PDF rendering, email automation, public share links, payment links, client-triggered sending, fiscal invoice compliance, or document upload were added.

## Files Inspected

- `README.md`
- `BUILD_PHASES.md`
- `PHASE_7_DOCUMENTS_IMPLEMENTATION.md`
- `PHASE_8_CLIENT_PORTAL_VISIBILITY_IMPLEMENTATION.md`
- `PHASE_10_AUTH_INVITATIONS_IMPLEMENTATION.md`
- `PHASE_11_PORTAL_ACTIONS_IMPLEMENTATION.md`
- `PHASE_12_STABILIZATION_AUDIT.md`
- `PHASE_13_PDF_EMAIL_DELIVERY_IMPLEMENTATION.md`
- `backend/models.py`
- `backend/database.py`
- `backend/server.py`
- `backend/routers/documents.py`
- `backend/services/document_rendering_service.py`
- `backend/services/seed_service.py`
- `frontend/src/lib/api.js`
- `frontend/src/pages/agency/DocumentDetailPage.jsx`
- `frontend/src/pages/portal/PortalDocumentDetailPage.jsx`

## Issues Found

- Export downloads trusted the stored filename directly in `Content-Disposition`; generated filenames were safe, but legacy or seeded records could still carry unsafe names.
- Export downloads did not convert corrupt inline base64 data into a controlled client error.
- Staff export list/detail projections omitted `error_message`, making failed PDF export records less clear after the original request toast was gone.
- Delivery send revalidated the delivery and document, but did not re-check that a referenced export still belonged to the same rendered document or was generated at send time.
- The seed export filename used a simpler title replacement than runtime export generation.
- The agency document UI presented PDF generation as an active button even though this installation intentionally has no renderer.
- The agency document UI allowed disabled-mode email sends to look actionable, relying only on the backend failure.
- A README footer still described PDF/export-era capabilities as outside the current implementation without mentioning the Phase 13 printable export and delivery foundation.

## Fixes Applied

- Hardened export filename sanitization and reused it when returning download responses.
- Added strict base64 validation for inline export downloads and a clear `400` response when stored data is invalid.
- Included `error_message` in the safe export projection so failed exports remain explainable without exposing inline file data.
- Added delivery-send attachment validation:
  - referenced exports must belong to the delivery's rendered document,
  - referenced exports must be generated before they can be attached.
- Added rendered-document existence validation for staff delivery detail lookup.
- Updated seed export filename generation to use the same safe filename behavior.
- Changed the agency UI PDF control to a disabled, explicit `PDF unavailable` button.
- Added disabled-mode email delivery explanation and disabled send buttons when agency email mode is `disabled`.
- Updated the stale README footer to reflect Phase 13 printable export and manual delivery foundation while still calling out real PDF rendering as out of scope.

## Verified Without Code Changes

- Phase 13 staff endpoints are registered under `/api/agencies/{agency_id}` and portal export endpoints under `/api/portal`.
- Staff export, delivery, and email-settings mutations require agency access and write/admin-level checks.
- Portal users cannot create exports, create deliveries, send deliveries, cancel deliveries, archive exports, or update email settings.
- Portal export listing and download are constrained by current portal client context, rendered document visibility, export visibility, and generated export status.
- Export archive is a status update, not a hard delete.
- Send/cancel delivery actions do not mutate the source rendered document.
- Printable HTML exports are generated from stored `RenderedDocument.rendered_html`, not live external data.
- PDF requests fail honestly and do not create a downloadable fake PDF.
- Email settings store a password secret reference only; no plaintext SMTP password field exists.
- `disabled`, `dev_console`, and incomplete `smtp` send paths fail or simulate as documented.
- Portal document detail remains read-only and exposes no send/share/email/PDF generation action.
- Portal export projections do not expose raw `source_snapshot`, `brand_snapshot`, delivery records, internal notes, or inline export data.
- Seeded email settings, export, and delivery records are idempotent.

## Validation Run

- `git status --short` before changes.
- `python3 -m py_compile backend/*.py backend/routers/*.py backend/services/*.py backend/scripts/*.py`
- Backend import smoke.
- Seed idempotency smoke.
- Document export smoke.
- PDF request honest-failure smoke.
- Delivery draft smoke.
- Disabled send smoke.
- Dev-console send smoke.
- Portal export list/download allowed smoke.
- Portal cross-client download denial smoke.
- Portal non-visible export denial smoke.
- Existing `backend/scripts/smoke_backend.py`.
- Existing `backend/scripts/check_portal_isolation.py`.
- `npm run build` from `frontend/`.
- `git diff --check`.
- `git status --short` after changes.

## Remaining Limitations

- Real PDF generation remains intentionally unavailable until a renderer, storage, retention, and visual QA path are selected.
- SMTP mode is a foundation only; production secret resolution, queueing, retries, bounce handling, webhook processing, and monitoring are not implemented.
- Export storage is inline base64 only in this phase; file storage and retention policy are future work.
- No public share links, expiring URLs, client-triggered sending, automatic delivery, payment links, or fiscal invoice compliance output exists.
- Formal migrations and broader authorization matrix tests remain future production-hardening work.

## Recommended Next Phase

Phase 14 should be Document Delivery Hardening: choose and verify a real PDF rendering dependency, add file storage and retention rules, add production secret resolution for SMTP, and introduce queued delivery/retry behavior before any public links or automated delivery are considered.
