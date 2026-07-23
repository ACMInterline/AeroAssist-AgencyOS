# Navigation And Layout Standards

Phase 59.0 defines the product-level navigation and workspace layout rules that extend the Phase 58.4 AeroAssist Product Standards.

## Before

Platform navigation was a large module grid and both shells constrained work to fixed central widths. Diagnostic pages could appear beside daily work, navigation descriptions clipped, and raw state details were visible without progressive disclosure.

## After

Navigation is organized by user purpose:

- Platform has no more than eight primary areas.
- Agency follows the travel workflow from Operations through Reports and Settings.
- Advanced is always the final area and is collapsed by default.
- Contextual tools remain linked from their owning workspace rather than becoming primary navigation.
- Product labels are projected from the existing module catalogue.
- Backend permissions remain authoritative.

## Workspace Layout Primitives

Use `WorkspacePage` from `frontend/src/components/WorkspacePage.jsx`.

| Variant | Intended use | Width behavior |
|---|---|---|
| `standard` | Normal operational detail and mixed-content pages | Fluid up to 96rem |
| `wide` | Dashboards, queues, tables, grids, and command centers | Full available workspace |
| `focused` | Forms, wizards, and narrow decision flows | Fluid up to 48rem |
| `reading` | Guidance, policies, and long-form documentation | Fluid up to 68rem |

The application shells own viewport padding, not a global content maximum. Pages choose the narrowest primitive that supports their task. Do not set every page to an arbitrary full width.

## Sidebar Rules

- Desktop sidebars have a stable expanded width and an icon-only collapsed width.
- Tablet and mobile use an overlay drawer.
- Opening a mobile drawer restores readable labels.
- Labels may wrap; they must not be horizontally clipped.
- Icon-only controls have accessible names and hover titles.
- Advanced uses a native closed `details` disclosure without an `open` attribute.

## Language Rules

Normal product surfaces should prefer:

- Information instead of metadata
- Related item instead of entity
- Reference instead of identifier
- Current status instead of state map
- System details or Advanced diagnostics instead of architecture terminology
- Planning only or Manual action required where a safety boundary matters

Precise technical language remains valid in developer documentation and inside explicitly Advanced specialist views. Safety wording must explain the real user consequence, such as no automatic payment or ticket issuance.

## Empty And Error States

- Missing optional diagnostic information is an empty state.
- Authorization, tenant, validation, and required-data failures remain errors.
- Do not create placeholder production records to make a page appear populated.
- Raw JSON and state maps must be behind closed progressive disclosure.
- Empty states explain when information will appear and what the user can do next.

## Before And After Mapping

| Previous layout or navigation behavior | Product standard |
|---|---|
| Full catalogue shown as navigation | Validated task-based projection over the catalogue |
| Technical modules equal to daily work | Technical modules in collapsed Advanced |
| Fixed `max-w-7xl` / `max-w-[1440px]` shell | Fluid shell plus explicit page-width primitive |
| Truncated two-line sidebar labels | Wrapping product label with concise purpose |
| Raw workflow maps visible | Closed Advanced system details disclosure |
| Optional diagnostic 404 shown as red page | Useful empty state; real failures preserved |

## Validation

`backend/scripts/validate_product_experience_recovery.py` evaluates area counts and order, catalogue metadata, role projections, deep-link preservation, onboarding and Operations routing, Advanced disclosure, workflow empty states, layout primitives, canonical roots, documentation, phase registration, and unchanged execution boundaries.

