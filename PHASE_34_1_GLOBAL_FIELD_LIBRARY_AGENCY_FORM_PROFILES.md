# Phase 34.1 — Global Field Library and Agency Form Profiles

Phase 34.1 adds a platform-owned field library plus agency-owned form profiles for safe form configuration.

## Implemented

- `global_field_definitions` stores canonical AeroAssist field definitions, canonical paths, field families/types, reference domains, required level, safety flags, override permissions, validation schema metadata, display order, and active status.
- `agency_form_profiles` stores agency profiles by context: public request, portal request, admin request, offer client view, offer PDF, trip intake, and service-specific forms.
- `agency_form_field_settings` stores agency field visibility, required overrides, label/help/placeholder overrides, ordering, sections, visibility conditions, validation overrides, and agency custom fields.
- `backend/services/form_profile_service.py` resolves effective profiles by combining global fields, agency settings, and safety constraints.
- Public website and admin request forms can fetch effective profiles when available, while falling back to existing UI behavior when no profile exists.
- Agency custom questions are stored under the canonical `agency_custom_fields` namespace.

## Governance Rules

- Platform owners/admins manage global field definitions and run the manual bootstrap.
- Agencies may configure display behavior, labels, helper text, order, optional required overrides, and custom questions.
- Agencies cannot change canonical field meaning, canonical paths, SSR interpretation, policy formulas, pricing formulas, service logic, or system-required compliance fields.
- `system_required` fields cannot be hidden.
- `internal_only` fields cannot be exposed in public contexts.
- Label/help overrides are applied only when the global field permits them.
- Required overrides are applied only when the global field permits them.

## Integration Behavior

- Public forms fetch public-safe `public_request` effective profiles through a public read-only endpoint.
- Admin request builder fetches the default `admin_request` profile when present.
- Hidden optional fields are hidden in the UI only; backend schemas still accept canonical data later.
- Custom agency fields are accepted in intake and builder payloads under `agency_custom_fields`.

## Known Limits

- No full visual/drag-and-drop form builder is added.
- No pricing formula editor is added.
- No airline policy form generator or policy engine is added.
- No portal expansion, offer builder, GDS/NDC import, invoice, or payment module is added.
- Form profiles currently influence selected foundational public/admin request surfaces only.

## Validation

- `backend/scripts/smoke_form_profiles_field_library.py` verifies idempotent bootstrap, global definition permissions, agency profile creation, optional-field hiding, system-required/internal-only enforcement, effective profile resolution, custom agency fields, fallback safety, and readiness counters.
