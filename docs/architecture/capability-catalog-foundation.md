# Capability Catalog Foundation

Phase 40.1 adds a metadata-only Capability Catalog for AgencyOS.

The catalog is the canonical inventory of functional capabilities and their review metadata. It records capability codes, names, categories, modules, status, visibility, tags, feature flag references, bundle references, dependency references, UI routes, documentation links, introduced phase, deprecation status, and notes.

## Purpose

The catalog gives Platform Console owners and Agency Workspace users one read-only place to understand what a capability is, which metadata references describe it, and which UI routes/documentation relate to it.

Capabilities do not execute. They do not enable features, evaluate entitlements, change permissions, block routes, bill, publish, call providers, call external APIs, call external AI, start background workers, or send anything.

## Model

`CapabilityCatalogEntry` records:

- `code`
- `name`
- `description`
- `category`
- `module`
- `status`
- `visibility`
- `tags`
- `required_feature_flags`
- `required_bundles`
- `recommended_bundles`
- `dependencies`
- `ui_routes`
- `documentation_links`
- `introduced_phase`
- `deprecated`
- `notes`

The backing collection is `capability_catalog` with indexes for `code`, `category`, `module`, and `status`.

## Relationship Chain

Subscription and capability metadata is intentionally layered:

```text
Subscriptions
  -> Bundles
  -> Feature Flags
  -> Capabilities
  -> Future Enforcement
```

Phase 40.1 does not connect this chain to runtime permission checks. Agency availability labels are informational only and are not used to enforce access.

## Platform Review

Platform Console uses `/platform/capabilities` and read-only APIs under `/api/platform/capabilities`.

The page supports search, category filter, module filter, flag references, bundle references, dependency views, UI route metadata, and documentation links.

## Agency Visibility

Agency Workspace uses `/agency/capabilities` and read-only APIs under `/api/agencies/{agency_id}/capabilities`.

Agency users see capability name, informational status, required bundle metadata, required feature flag metadata, and dependency count. There are no enable buttons, switches, publishing controls, or execution actions.

## Future Enforcement

Any future enforcement phase must be separately authorized and must define migrations, permission behavior, audit guarantees, rollback behavior, route behavior, tests, and operational safety boundaries.

Phase 40.1 intentionally stops at metadata.

## Route Boundary

Phase 40.1 preserves canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` routes.

It adds read-only APIs:

- `GET /api/platform/capabilities`
- `GET /api/platform/capabilities/{code}`
- `GET /api/platform/capabilities/categories`
- `GET /api/platform/capabilities/modules`
- `GET /api/agencies/{agency_id}/capabilities`
- `GET /api/agencies/{agency_id}/capabilities/available`
- `GET /api/agencies/{agency_id}/capabilities/unavailable`

It also exposes the same readiness payload at `GET /api/system/readiness` while preserving `GET /api/readiness`.

It does not add `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes.
