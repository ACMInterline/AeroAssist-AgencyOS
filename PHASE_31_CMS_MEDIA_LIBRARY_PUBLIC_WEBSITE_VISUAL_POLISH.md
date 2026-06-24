# Phase 31 — CMS Media Library, Website Image Assets, and Public Website Visual Polish

Phase 31 adds a safe agency CMS media library for public website images and improves published website rendering so agency sites look like a polished public experience rather than an internal admin preview.

## Implemented

- Added `agency_website_media_assets` as a separate agency-owned collection from logo assets.
- Added website media upload, list, update, and archive endpoints under `/api/agencies/{agency_id}/website/media`.
- Allowed image-like media types only in this phase: PNG, JPEG, and WEBP. SVG is rejected because no sanitizer exists.
- Enforced a 5MB upload limit, extension/MIME/magic-byte checks, decoded image validation, metadata stripping, and server-side PNG derivative generation through Pillow.
- Generated variants:
  - `thumbnail`: max 320px wide.
  - `card`: max 640px wide.
  - `hero`: max 1600px wide.
  - `original_safe`: normalized public-safe copy.
- Added controlled media selection to website sections that support images.
- Public website JSON includes only active, public-safe, public-usage-allowed media assets referenced by published sections.
- Public website renderer now uses safer media variants, improved header/nav, polished hero/content sections, responsive cards, and a clearer public request form.

## Safety Rules

- No arbitrary HTML, CSS, JavaScript, iframes, or raw image URLs.
- No local filesystem paths or private storage URLs are exposed.
- Private/draft/archived media is not included in public website responses.
- Public renderer uses only published site settings, published pages, public-safe branding, and public-safe referenced media.
- Website request forms still create `request_intakes`; they do not create operational requests automatically.

## Known Limits

- No advanced drag-and-drop page builder.
- No custom domain automation.
- No advanced SEO sitemap/robots tooling.
- No background removal.
- No external image editing or CMS service.
- No automatic email notification.
- Media is stored in database-backed records in this phase; a future object-storage move should extend backup/runbook coverage for the binary root.
