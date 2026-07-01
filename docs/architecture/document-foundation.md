# Document Foundation

Phase 36.5 adds a unified internal document foundation for AgencyOS operational records. It is a preview/package/share-record layer only; it does not send emails, create public links, execute providers, require PDF export, collect signatures, process payments, create invoices/accounting entries, or perform settlement.

## Core Records

- `DocumentTemplate` now supports platform default template metadata through `scope`, `template_key`, `template_type`, `title`, `active`, `locale`, layout/content blocks, and required context metadata while preserving legacy template fields.
- `DocumentRenderJob` stores one generated internal preview with source context, render status, format, normalized render context, rendered HTML/text, warnings, and staff provenance.
- `DocumentPackage` groups render jobs for a shared operational source such as a trip, booking workspace, ticket/EMD set, import review, or internal case.
- `DocumentShareRecord` records a manual/internal share intent for a render job or package. It is an audit foundation, not live delivery.

## Context Sources

`DocumentContextService` normalizes document input from:

- requests
- offer workspaces/options/acceptances
- trip dossiers
- booking workspaces and booking records
- ticket records and EMD records
- booking import drafts
- GDS parser runs
- trip change operations
- ticket exchange operations and EMD exchange operations
- passenger service requests
- mixed manual context

The normalized context includes agency/client/passenger snapshots, trip summary, itinerary segments, booking/PNR summary, pricing, ticket/EMD summaries and coupons, service rows, SSR/OSI rows, pets/special items, change/exchange summaries, warnings, and source links.

## APIs

Platform owners can inspect and seed default templates:

- `GET /api/platform/documents/templates`
- `POST /api/platform/documents/templates/seed-defaults`

Agencies can preview context, render documents, rerender existing jobs, create packages, and record manual/internal shares:

- `GET /api/agencies/{agency_id}/documents/templates`
- `GET /api/agencies/{agency_id}/documents/templates/{template_id}`
- `POST /api/agencies/{agency_id}/documents/context-preview`
- `GET /api/agencies/{agency_id}/documents/render-jobs`
- `POST /api/agencies/{agency_id}/documents/render-jobs`
- `GET /api/agencies/{agency_id}/documents/render-jobs/{render_job_id}`
- `POST /api/agencies/{agency_id}/documents/render-jobs/{render_job_id}/rerender`
- `GET /api/agencies/{agency_id}/documents/packages`
- `POST /api/agencies/{agency_id}/documents/packages`
- `GET /api/agencies/{agency_id}/documents/packages/{package_id}`
- `POST /api/agencies/{agency_id}/documents/share-records`

## UI Entry Points

- `/agency/documents` is the unified agency document foundation console.
- `/platform/document-templates` lists and seeds platform default document templates.
- Trip detail links to trip confirmation, internal case summary, booking documents, ticket/EMD receipts, and change summaries when linked records exist.
- Offer workspace and offer builder link to offer summary/comparison documents.
- Booking workspace detail links to booking confirmation, PNR mirror, and internal case summary documents.
- Tickets & EMDs link to ticket and EMD receipt documents.
- Booking imports link to import review summary documents.
- GDS parser runs link to parse review summary documents.

## Readiness

`/api/readiness` exposes a non-blocking `document_foundation` section with template, render job, package, share record, legacy rendered document, and export counts. The section explicitly keeps `live_delivery_disabled`, `e_signature_disabled`, and `payment_invoice_accounting_disabled` true, with `pdf_export_required` and `readiness_required` false.

## Phase 36.6 Parser Context

Phase 36.6 adds `gds_parser_run` as a document source context and default templates for `gds_parse_review_summary` and `booking_import_review_summary`. Parser documents summarize detected provider/input format, confidence, extracted entities, warnings, corrections, and training sample status without performing delivery or provider actions.

## Phase 36.7 Policy Context

Phase 36.7 adds `airline_policy_source`, `airline_policy_extraction_run`, and `airline_policy_approved_knowledge` as document source contexts. Default templates `airline_policy_extraction_summary` and `airline_policy_review_summary` summarize policy source metadata, detected sections, extraction run counts, candidate rule/pricing/communication/EMD/exception rows, warnings, review corrections, and approved knowledge records. These documents are internal review summaries only; they do not publish policies, call providers, perform AI extraction, or auto-promote policy candidates.
