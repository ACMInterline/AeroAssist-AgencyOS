# Phase 28.1 — AgencyOS App Shell, Sidebar Navigation, and Visual Polish Stabilization

Phase 28.1 upgrades the internal agency workspace from a broad top-nav layout into a polished operational SaaS shell while preserving Phase 28 branding and theme personalization.

## Implemented Scope

- Added a persistent desktop sidebar for agency workspace navigation.
- Added responsive mobile drawer navigation with keyboard-accessible buttons.
- Added active-route highlighting and disabled coming-soon nav affordances; Website/CMS was enabled later in Phase 29.
- Added a compact top bar with workspace context, manual-operations badge, create-request action, and account/logout area.
- Added sidebar collapse behavior on desktop.
- Reused Phase 28 brand name/logo and CSS variable theme settings across the shell.
- Added shared visual polish for app background, cards, forms, buttons, focus outlines, tables, status surfaces, and responsive overflow.
- Improved dashboard layout with real request/intake/staff/workspace summary cards and quick actions.
- Improved request list and intake queue headers, filters, empty states, and card affordances.
- Improved request detail header, panel hierarchy, and list readability.
- Improved request builder hierarchy with a sticky section navigator, stronger section headers, and sticky submit action.

## Enabled Navigation

- Dashboard / Workspace Home
- Requests
- Intakes
- Clients
- Passengers
- Documents
- Settings

## Coming Soon Navigation At Phase 28.1

- Offers / Pricing

Coming-soon entries are rendered disabled and do not navigate.

## Theme Integration

- The shell uses `agencyThemeStyle()` from Phase 28 as the single source for agency theme variables.
- Sidebar, top bar, cards, buttons, inputs, native date fields, badges, and major surfaces consume `--aa-*` variables.
- No arbitrary CSS input or remote font loading was added.

## Validation

- `python3 -m py_compile backend/server.py backend/routers/platform.py backend/scripts/smoke_agency_branding_settings.py backend/scripts/smoke_operational_request_builder.py backend/scripts/smoke_request_intake_conversion.py`
- `npm run build --prefix frontend`
- `git diff --check`
- Backend smoke scripts when the local API is running:
  - `python3 backend/scripts/smoke_agency_branding_settings.py`
  - `python3 backend/scripts/smoke_operational_request_builder.py`
  - `python3 backend/scripts/smoke_request_intake_conversion.py`

## Known Limits

- CMS is not implemented yet.
- Pricing automation is not implemented.
- No external design-system package was added.
- No automated visual regression test harness exists yet.
- Page-level polish is improved for key agency workflows, but a full component-library extraction remains future work.
