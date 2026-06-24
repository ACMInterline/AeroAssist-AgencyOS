# Phase 29 — Agency Website Builder / CMS Foundation

Phase 29 adds a controlled agency website builder and CMS foundation for public agency-facing content. It is intentionally modest: staff can manage site settings, safe pages, and safe sections, while domain routing, custom code, pricing automation, and external integrations remain out of scope.

## Implemented Scope

- Added agency-owned `agency_website_settings` and `agency_website_pages` collections.
- Added controlled website settings for site name, slug, tagline, status, SEO text, contact details, and request CTA visibility.
- Added controlled website pages with page type, slug, title, draft/published/archived status, SEO text, and section blocks.
- Added controlled section types: hero, text, services, CTA, contact, and intake link.
- Added staff CMS APIs for settings, page CRUD, publish, and archive.
- Added safe public website JSON at `/api/public/websites/{slug}` for active websites only.
- Added agency UI at `/agency/website` for settings, page creation, section editing, publish/archive, and live preview.
- Added frontend public renderer at `/site/{slug}`.
- Enabled the Website / CMS sidebar item from the Phase 28.1 app shell.
- Added readiness/platform counts for configured websites, active websites, and website pages.

## Safety Boundaries

- No arbitrary CSS, JavaScript, HTML embeds, iframes, or remote script support.
- Dangerous content such as `script`, `style`, `iframe`, `javascript:`, and HTML data URLs is rejected.
- Public renderer uses structured fields, not raw HTML injection.
- Only platform owners/admins and agency owners/admins can manage website content.
- Staff/read-only roles can read website content internally.
- Activating a website requires at least one published page.

## API

- `GET /api/agencies/{agency_id}/website`
- `PUT /api/agencies/{agency_id}/website`
- `GET /api/agencies/{agency_id}/website/pages`
- `POST /api/agencies/{agency_id}/website/pages`
- `PUT /api/agencies/{agency_id}/website/pages/{page_id}`
- `POST /api/agencies/{agency_id}/website/pages/{page_id}/publish`
- `POST /api/agencies/{agency_id}/website/pages/{page_id}/archive`
- `GET /api/public/websites/{slug}`

## Not Included

- Custom CSS/JS.
- Domain management or production routing changes.
- Website templates marketplace.
- Pricing engine or offer automation.
- Airline/GDS/NDC integrations.
- Automatic email or delivery provider actions.
- Full visual regression testing.

## Validation

- `python3 -m py_compile backend/models.py backend/database.py backend/routers/websites.py backend/server.py backend/routers/platform.py backend/scripts/smoke_agency_website_builder.py`
- `npm run build --prefix frontend`
- `git diff --check`
- `python3 backend/scripts/smoke_agency_website_builder.py`
