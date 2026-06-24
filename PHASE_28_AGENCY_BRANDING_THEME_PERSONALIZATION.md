# Phase 28 — Agency Branding, Theme, and UI Personalization Settings

Phase 28 adds agency-scoped branding and lightweight UI personalization while keeping the implementation controlled, auditable, and safe by default.

## Implemented Scope

- Added `agency_branding_settings` and `agency_branding_assets` agency-owned collections.
- Added branding settings fields for brand name, optional workspace override, logo reference, font key, radius key, density key, theme mode, palette key, field style, button style, native date input style, card style, actor metadata, and audit metadata.
- Added ten controlled font choices, including Quicksand, as local CSS font stacks without remote font loading.
- Added ten controlled palettes with light and dark values: Aero Blue, Midnight Navy, Graphite, Emerald Aviation, Sky Cyan, Violet Premium, Burgundy Executive, Sandstone, Slate Minimal, and Black Glass.
- Added controlled radius, density, field, button, date input, and card style presets.
- Added agency settings UI at `/agency/settings` with logo upload/removal, save/reset, and live preview.
- Added a shared agency theme layer that maps settings into CSS variables for agency headers, nav, buttons, inputs, cards, badges, request-builder sections, and native date input wrappers.

## API

- `GET /api/agencies/{agency_id}/branding`
- `PUT /api/agencies/{agency_id}/branding`
- `POST /api/agencies/{agency_id}/branding/logo`
- `DELETE /api/agencies/{agency_id}/branding/logo`
- `POST /api/agencies/{agency_id}/branding/reset`

## Security Boundaries

- Branding accepts controlled enum keys only; arbitrary CSS and unknown fields are rejected.
- Logo upload accepts PNG, JPEG, and WEBP only, with a 2MB limit.
- SVG upload is rejected instead of sanitized in this phase.
- Logo responses do not expose filesystem paths or public object-store paths.
- Platform owners/admins and agency owners/admins can manage branding; agency staff/read-only users can read.
- Audit events are emitted for branding updates, logo upload, logo removal, and theme reset.

## Readiness

- `/api/health` reports `phase_28_agency_branding_theme_personalization`.
- `/api/readiness` includes optional agency branding counts.
- Missing branding settings do not fail readiness.

## Verification

- Backend compile:
  - `python3 -m py_compile backend/models.py backend/database.py backend/routers/agencies.py backend/server.py backend/routers/platform.py backend/scripts/smoke_agency_branding_settings.py`
- Frontend build:
  - `npm run build`
- Smoke:
  - `python3 backend/scripts/smoke_agency_branding_settings.py`

## Not Included

- Arbitrary CSS editor.
- Remote font loading.
- SVG logo sanitization/execution.
- Public logo links.
- Agency website/CMS publishing.
- Browser-perfect theme coverage across every future page component.
