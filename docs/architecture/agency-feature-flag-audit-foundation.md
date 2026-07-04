# Agency Feature Flag Readiness & Audit Foundation

Phase 39.8 adds metadata-only readiness and audit history for agency feature flags.

## Scope

The foundation records:

- `AgencyFeatureFlagAudit` for feature visibility state-change history.
- `AgencyFeatureFlagReadiness` for feature readiness checklist metadata.

These records are informational only. They do not enforce features, block routes, change permissions, affect subscription entitlements, bill, execute providers, call external APIs, publish CMS/client portal content, scrape, call external AI, or send automatically.

## Readiness Lifecycle

Readiness rows track review checklist fields for each agency and feature:

- `documentation_complete`
- `backend_complete`
- `api_complete`
- `ui_complete`
- `testing_complete`
- `deployment_ready`
- `rollout_ready`

The checklist is not an execution gate. It is owner-review metadata for future planning and agency read-only visibility.

## Audit Records

Audit rows capture:

- agency
- feature key
- previous state
- proposed state
- reviewer
- change date
- reason
- notes
- metadata

Audit rows are created as metadata history when platform feature visibility changes through the existing feature flag foundation. Phase 39.8 does not add write endpoints for audits or readiness.

## Review Workflow

Platform Console owners can review feature audit history and readiness metadata under `/platform/feature-flag-audit`.

Agency Workspace users can view their own agency readiness metadata under `/agency/feature-readiness`.

Agency routes are read-only and scoped through the existing agency tenant checks.

## Subscription Relationship

Feature flag audit and readiness records are independent of SaaS subscription and entitlement metadata. They do not modify plans, assignments, entitlements, readiness rows, billing records, or subscription visibility hints.

## Future Enforcement Phases

Any future feature enforcement would require a separate explicit phase with permission design, route behavior, rollout controls, migration planning, and tests. Phase 39.8 intentionally stops at audit history and readiness metadata.

## Route Boundary

Phase 39.8 preserves canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` routes.

It adds read-only APIs:

- `GET /api/platform/feature-flags/audits`
- `GET /api/platform/feature-flags/readiness`
- `GET /api/platform/feature-flags/readiness/{feature_key}`
- `GET /api/agencies/{agency_id}/feature-readiness`
- `GET /api/agencies/{agency_id}/feature-readiness/{feature_key}`

It does not add `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes.
