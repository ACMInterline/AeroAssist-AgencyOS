# Platform / Agency UX Consolidation

Phase 39.4 clarifies the product mental model for non-technical platform owners and agency staff without adding operational execution.

## Platform Console

The platform owner area is labeled “Platform Console” and grouped by plain-language owner responsibilities:

- SaaS & Agencies
- Airline Intelligence Governance
- Agency Website/CMS Governance
- CRM / Client Portal Governance
- Offer & Document Governance
- System Readiness

These groups explain that platform users operate the SaaS, agency setup, airline intelligence governance, CMS/portal foundations, offer/document evidence visibility, and readiness checks.

## Agency Workspace

The agency area is labeled “Agency Workspace” and grouped by daily staff responsibilities:

- Daily Work
- Clients & Passengers
- Requests, Offers & Trips
- Website/CMS
- Airline Intelligence Visibility
- Documents & Delivery
- Settings

Agency labels avoid platform-owner control wording where possible. Read-only platform-governed views are marked with helper badges such as “Agency read-only”, “Metadata only”, “No publishing yet”, “No issuance”, and “No payments”.

## Shared Module Catalog

Frontend route descriptions, audience labels, safety status, helper badges, and visible labels live in `frontend/src/lib/moduleCatalog.js`.

`PlatformLayout` and `AgencyLayout` consume this catalog so sidebar/header navigation and landing-page overview cards share the same wording.

## Route Policy

Phase 39.4 does not add or rename route paths. Canonical roots remain:

- `/platform/*`
- `/agency/*`
- `/api/platform/*`
- `/api/agencies/{agency_id}/*`

The supplementary `/admin`, `/agent`, `/api/admin`, and `/api/agent` route roots remain intentionally rejected.

## Readiness

The readiness section `platform_agency_ux_consolidation` confirms:

- Platform Console labels are enabled.
- Agency Workspace labels are enabled.
- Owner/agency separation is explicit.
- Plain-language navigation is enabled.
- Canonical routes are preserved.
- Admin/agent route roots remain rejected.
- The UI remains metadata-only.

## Safety Boundary

Phase 39.4 does not publish CMS/client portal content, recommend airlines, execute providers, book, create or mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external APIs, call external AI, or send automatically.

## Phase 59.0 Module Catalogue Projection

Phase 59.0 retains the groups above as historical internal catalogue ownership, but no longer renders them as the primary product navigation. The catalogue is projected into eight Platform areas and thirteen workflow-ordered Agency areas using product-facing purpose, audience, priority, label, description, and Advanced-placement fields.

Before Phase 59.0, every non-contextual item could appear with similar visual importance. After Phase 59.0, selected daily and governance routes appear in their task area; every remaining non-contextual technical route is available under a collapsed Advanced area. Contextual tools remain linked from their owning workflow. Route paths are resolved from the catalogue during module initialization, so an unknown product-navigation route fails validation rather than creating a conflicting registry.

See:

- `docs/product/platform-information-architecture.md`
- `docs/product/agency-information-architecture.md`
- `docs/product/navigation-and-layout-standards.md`
