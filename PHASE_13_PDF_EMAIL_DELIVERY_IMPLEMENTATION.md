# Phase 13 PDF Export And Email Delivery Foundation

## Goal

Add controlled export and delivery records around existing rendered HTML documents. Exports and deliveries operate only on stored `RenderedDocument` snapshots.

This phase does not add business workflow modules, payment links, refund execution, ticketing/EMD execution, GDS/NDC/airline integrations, airline policy automation, accounting ledger behavior, mass marketing email, public share links, or automatic sending.

## Models Added

- `DocumentExport`
  - Tracks generated document outputs.
  - Supports `print_html` and `pdf` as requested export types.
  - This implementation generates `print_html` only because no reliable PDF renderer is installed in the current dependency set.
- `DocumentDelivery`
  - Tracks manual delivery drafts, sends, failures, cancellations, and provider metadata.
  - Supports one document per delivery.
- `AgencyEmailSettings`
  - Stores sender configuration, email mode, SMTP host/port/user placeholders, and a password secret reference.
  - Raw SMTP passwords are not stored.

## Backend Endpoints Added

Staff document exports:

- `POST /api/agencies/{agency_id}/documents/{document_id}/exports`
- `GET /api/agencies/{agency_id}/documents/{document_id}/exports`
- `GET /api/agencies/{agency_id}/document-exports/{export_id}`
- `GET /api/agencies/{agency_id}/document-exports/{export_id}/download`
- `POST /api/agencies/{agency_id}/document-exports/{export_id}/archive`

Staff deliveries:

- `POST /api/agencies/{agency_id}/documents/{document_id}/deliveries`
- `GET /api/agencies/{agency_id}/documents/{document_id}/deliveries`
- `GET /api/agencies/{agency_id}/document-deliveries/{delivery_id}`
- `POST /api/agencies/{agency_id}/document-deliveries/{delivery_id}/send`
- `POST /api/agencies/{agency_id}/document-deliveries/{delivery_id}/cancel`

Agency email settings:

- `GET /api/agencies/{agency_id}/email-settings`
- `PUT /api/agencies/{agency_id}/email-settings`

Portal read-only export access:

- `GET /api/portal/documents/{document_id}/exports`
- `GET /api/portal/document-exports/{export_id}/download`

## Export Behavior

- `print_html` exports are generated from `RenderedDocument.rendered_html`.
- The printable HTML is stored inline as base64 in the export record.
- Downloads return `text/html; charset=utf-8` with an attachment filename.
- `pdf` requests fail with a friendly error and create no downloadable fake PDF.
- Portal users can list/download only exports where:
  - the rendered document belongs to the current portal client,
  - the rendered document is `client_visible`,
  - the export is `client_visible`,
  - the export status is `generated`.

## Email Delivery Behavior

Email settings support three modes:

- `disabled`: delivery drafts can exist, but send attempts fail clearly.
- `dev_console`: send action marks delivery as sent with provider `dev_console`; no real email is sent.
- `smtp`: send action attempts SMTP if host/port are configured. Password secret resolution is not implemented yet, so raw credentials are not stored.

Sending is always staff-controlled. No automatic sends occur when a document is rendered.

## Frontend Changes

Updated `frontend/src/pages/agency/DocumentDetailPage.jsx`:

- Exports panel.
- Printable export generation.
- Export download action.
- Delivery draft form.
- Send/cancel delivery actions.
- Inline email settings panel.
- Clear copy for agency-generated documents and manual delivery.

Updated `frontend/src/pages/portal/PortalDocumentDetailPage.jsx`:

- Lists available client-visible exports.
- Allows download only.
- No send/share controls.

Updated `frontend/src/lib/api.js`:

- Added authenticated download helper for export downloads.

## Seed Data

Seed now creates:

- Demo agency email settings in `dev_console` mode.
- One client-visible `print_html` export for a seeded rendered document.
- One sent `dev_console` delivery record.

No SMTP credentials are seeded.

## Security And Operational Limitations

- No reliable PDF renderer is installed, so real PDF generation remains future work.
- No raw SMTP password storage exists.
- No public links, expiry controls, file storage backend, email queue worker, retry policy, bounce handling, or delivery webhook processing exists.
- No legal/fiscal invoice compliance output is provided.
- Rendered document snapshots remain the source of truth for exports.

## Validation Performed

- Backend compile.
- Backend import smoke.
- Seed idempotency smoke.
- Existing backend smoke.
- Existing portal isolation smoke.
- Targeted document export, delivery draft, dev-console send, portal export list/download, cross-client denial, and PDF-unavailable smoke.
- Frontend production build.
- `git diff --check`.

## Exact Next Recommended Phase

Phase 14 should add a formal document delivery hardening pass: real PDF rendering dependency selection, file storage/retention policy, delivery queue/retry behavior, and production secret handling before any public links or automated delivery are introduced.
