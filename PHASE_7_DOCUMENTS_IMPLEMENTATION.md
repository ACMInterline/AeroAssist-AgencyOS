# Phase 7 Branded Document Output Implementation

## Goal

Add snapshot-based branded HTML document rendering for agency staff. Documents are generated from stored AgencyOS records, agency branding, and captured source snapshots.

This phase does not add PDF export, email sending, public share links, client portal publishing, e-signature, payment links, fiscal/legal invoice compliance, refund/exchange workflow, or integrations.

## Models Added

- `DocumentTemplate`
- `RenderedDocument`
- `DocumentTimelineEvent`

Supporting enums were added for template scope, document type, template status, rendered document source type, and rendered document status.

## Backend Services Added

- `backend/services/document_rendering_service.py`

The renderer:

- Reads agency workspace branding.
- Stores `brand_snapshot`.
- Stores `source_snapshot`.
- Escapes record data before rendering HTML.
- Produces printable-looking HTML strings.
- Labels documents as agency-generated summaries.
- Includes preview/snapshot/disclaimer text.

## Backend Endpoints Added

Templates:

- `GET /api/agencies/{agency_id}/document-templates`
- `POST /api/agencies/{agency_id}/document-templates`
- `GET /api/agencies/{agency_id}/document-templates/{template_id}`
- `PUT /api/agencies/{agency_id}/document-templates/{template_id}`
- `POST /api/agencies/{agency_id}/document-templates/{template_id}/archive`

Rendered documents:

- `GET /api/agencies/{agency_id}/documents`
- `GET /api/agencies/{agency_id}/documents/{document_id}`
- `POST /api/agencies/{agency_id}/documents/{document_id}/archive`
- `GET /api/agencies/{agency_id}/documents/{document_id}/timeline`

Render actions:

- `POST /api/agencies/{agency_id}/offers/{offer_id}/render-document`
- `POST /api/agencies/{agency_id}/bookings/{booking_id}/render-document`
- `POST /api/agencies/{agency_id}/tickets/{ticket_id}/render-document`
- `POST /api/agencies/{agency_id}/emds/{emd_id}/render-document`
- `POST /api/agencies/{agency_id}/invoices/{invoice_id}/render-document`

## Supported Document Types

- `offer_summary`
- `booking_confirmation`
- `itinerary_summary`
- `ticket_receipt_summary`
- `emd_receipt_summary`
- `invoice_summary`
- `service_summary` template support only in this phase

## Frontend Routes Added

- `/agency/documents`
- `/agency/documents/:documentId`
- `/agency/document-templates`

## Frontend Components Added

- `DocumentTypeBadge`
- `DocumentStatusBadge`
- `DocumentPreviewFrame`

## Workflow Actions Added

- Offer detail can render an offer summary.
- Booking detail can render booking confirmation and itinerary summary.
- Booking ticket rows can render ticket receipt summaries.
- Booking EMD rows can render EMD receipt summaries.
- Invoice detail can render invoice summaries.

## Seed Data Added

- Platform default templates for offer, booking, itinerary, ticket, EMD, and invoice summaries.
- One rendered offer summary.
- One rendered booking confirmation.
- One rendered itinerary summary.
- One rendered invoice summary.

No PDFs are seeded.

## Known Limitations

- No PDF generation.
- No email sending.
- No public share links.
- No client portal document publishing.
- No legal/fiscal invoice compliance output.
- No advanced template editor.
- No request/service summary render action yet.
- Rendered HTML is stored in memory/Mongo according to the existing database mode; no external file storage exists yet.

## Next Recommended Phase

Implement refund/exchange tracking or client portal document publishing, depending on whether operational servicing or client-facing delivery is the next priority. PDF export should wait until a stable HTML/document template contract is validated.
