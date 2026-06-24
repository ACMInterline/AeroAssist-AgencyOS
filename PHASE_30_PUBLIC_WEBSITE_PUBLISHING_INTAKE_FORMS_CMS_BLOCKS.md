# Phase 30 — Public Website Publishing, Intake Forms, and CMS Content Blocks

Phase 30 makes the Phase 29 website CMS operationally useful: agencies can manage richer structured content blocks, publish/unpublish sites, render published pages safely, and receive website-origin requests into the existing intake queue.

## Implemented Scope

- Added richer safe CMS section types:
  - `hero`
  - `service_cards`
  - `feature_grid`
  - `process_steps`
  - `faq`
  - `contact_cta`
  - `request_form_cta`
  - `testimonials`
  - `trust_badges`
  - `image_text`
  - `contact_details`
  - `legal_text`
- Preserved Phase 29 legacy section types for compatibility.
- Added section field validation and safe structured JSON block handling.
- Added section create/update/delete/reorder audit events.
- Added explicit publish/unpublish site endpoints.
- Added public page endpoint for published inner pages only.
- Added public website request form endpoint that creates `request_intakes` with agency/site/page source metadata.
- Added frontend `/site/{slug}/request` form and `/site/{slug}/{pageSlug}` rendering.
- Updated intake queue/detail UI to show website CMS source metadata.
- Updated readiness/platform summaries for CMS enablement, renderer enablement, website intake enablement, and website-origin intake counts.

## Public Website Flow

1. Agency owner/admin edits website settings and pages in `/agency/website`.
2. Agency owner/admin saves draft sections.
3. Agency owner/admin publishes at least one home page.
4. Agency owner/admin publishes the site.
5. Public visitors can view `/site/{slug}` and `/site/{slug}/{pageSlug}`.
6. Public visitors can submit `/site/{slug}/request`.
7. The request is stored as a `request_intake`, not an operational request.

## Safety Boundaries

- No raw HTML.
- No arbitrary CSS.
- No custom JavaScript.
- No iframe/embed support.
- Draft pages are not returned by public endpoints.
- Offline sites return not-found responses.
- Website form submissions do not send automatic email and do not create operational requests directly.
- Media asset IDs remain non-public placeholders; no unsafe uploaded files are exposed.

## API

- `POST /api/agencies/{agency_id}/website/publish`
- `POST /api/agencies/{agency_id}/website/unpublish`
- `GET /api/public/websites/{slug}`
- `GET /api/public/websites/{slug}/pages/{page_slug}`
- `POST /api/public/websites/{slug}/request`

## Known Limits

- No custom domain automation.
- No advanced drag-and-drop builder.
- No advanced media library or public media delivery.
- No sitemap/robots automation.
- No automatic email notifications.
- No pricing or offer automation.
- No visual regression test harness.

## Validation

- `python3 -m py_compile backend/models.py backend/services/request_intake_conversion_service.py backend/routers/websites.py backend/server.py backend/routers/platform.py backend/scripts/smoke_agency_website_builder.py`
- `npm run build --prefix frontend`
- `git diff --check`
- `python3 backend/scripts/smoke_agency_website_builder.py`
