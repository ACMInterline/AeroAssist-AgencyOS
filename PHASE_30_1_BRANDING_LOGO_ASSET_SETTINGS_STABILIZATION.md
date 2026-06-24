# Phase 30.1 — Branding, Logo Asset Management, and Agency Settings Stabilization

Phase 30.1 hardens agency branding and logo handling after the public website/CMS foundation. It keeps branding controlled, prepares logo variants server-side, and exposes only public-safe derivatives to published websites.

## Implemented

- Controlled branding settings remain enum/preset driven: no arbitrary CSS, JavaScript, raw HTML, external script URLs, remote image URLs, or filesystem paths are accepted.
- Logo uploads accept PNG, JPEG, and WEBP only, enforce a 2MB limit, validate extension/MIME consistency, verify decoded image bytes, reject SVG, and strip metadata by regenerating PNG derivatives.
- Logo assets are stored as records in `agency_branding_assets` with agency scope, variant key, dimensions, file size, SHA-256 checksum, creator metadata, public-safety flags, and fit mode.
- Generated variants:
  - `original`: private normalized PNG, not public-safe.
  - `square`: 512x512 public-safe PNG.
  - `compact`: 256x256 public-safe PNG.
  - `horizontal`: 512x160 public-safe PNG for headers.
  - `favicon`: 128x128 public-safe PNG.
- Agency settings UI supports logo preview, replace/remove, fit mode (`contain`, `cover`, `center`), preferred usage (`square`, `horizontal`, `compact`), public usage permission, variant regeneration, and shell/public/favicon previews.
- Agency shell uses compact/sidebar logo first, falls back to a safe configured derivative, then text initials.
- Public website rendering uses only public-safe logo variants when `logo_public_usage_allowed=true`; it prefers horizontal/header, then square/compact, then text brand.
- Readiness/platform summaries expose branding/logo capability flags and counts without failing readiness when no logo is configured.

## API Notes

- `GET /api/agencies/{agency_id}/branding` returns safe branding settings, computed theme, design options, and safe logo metadata/previews.
- `PUT /api/agencies/{agency_id}/branding` updates controlled brand/theme/logo usage settings only.
- `POST /api/agencies/{agency_id}/branding/logo` uploads and prepares logo variants.
- `POST /api/agencies/{agency_id}/branding/logo/regenerate` regenerates variants from the private normalized original.
- `DELETE /api/agencies/{agency_id}/branding/logo` removes the configured logo reference and public preview output.
- `GET /api/agencies/{agency_id}/branding/public` returns public-safe branding only when the agency has an active published site.

## Audit Events

- `agency_branding_updated`
- `agency_logo_uploaded`
- `agency_logo_variant_generated`
- `agency_logo_removed`
- `agency_logo_public_usage_changed`
- `agency_theme_reset`

## Storage And Serving

Logo data is kept in controlled database asset records for this phase. API responses never expose raw filesystem paths or private storage URLs. Public website JSON includes only prepared public-safe derivatives.

Existing backups that capture the application database capture logo metadata and encoded derivative records. If a future phase moves logo binaries to object/local file storage, backup scripts must include that storage root explicitly.

## Known Limits

- No advanced drag-and-drop crop editor.
- No automated background removal.
- No SVG sanitization; SVG is rejected.
- No standalone media library or object-storage CDN.
- No custom domain automation.
- No arbitrary CSS/JS customization.
