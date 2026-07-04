# Feature Bundle Assignment Foundation

Phase 40.0 adds agency Feature Bundle Assignment metadata.

## Scope

This foundation lets Platform Console users record which reusable feature flag bundles are assigned to an agency for review and planning.

Assignments are informational only. They do not activate features, execute feature flags, evaluate entitlements, enforce permissions, hide modules, change subscription state, bill, license, call providers, call external APIs, call external AI, start background workers, run cron jobs, or deploy anything.

## Models

Phase 40.0 introduces:

- `AgencyFeatureBundleAssignment`
- `AgencyFeatureBundleAssignmentCreate`
- `AgencyFeatureBundleAssignmentHistory`

Persistent collections are:

- `agency_feature_bundle_assignments`
- `agency_feature_bundle_assignment_history`

Assignment fields include:

- `assignment_id`
- `agency_id`
- `bundle_id`
- `assigned_by`
- `assigned_at`
- `effective_date`
- `expiration_date`
- `status`
- `notes`
- `review_status`
- `created_at`
- `updated_at`

## Metadata-Only Assignment

An assignment links an agency to a feature flag bundle definition. The link is reviewable and visible, but it does not turn on the bundle or any member feature.

The assignment service resolves bundle metadata for display only. It does not evaluate subscription entitlements, permissions, feature state, or module visibility.

## No Activation Or Entitlement Changes

Phase 40.0 does not:

- activate feature flags
- enforce feature access
- evaluate entitlements
- update subscription plans or assignments
- modify agency permissions
- hide or reveal modules automatically
- create rollout or percentage deployment behavior

DELETE requests mark assignment metadata inactive and append history. They do not remove the assignment history.

## Review Workflow

Platform Console users can review, create, update, and mark assignment metadata inactive under `/platform/feature-bundle-assignments`.

Agency Workspace users can view assignment metadata under `/agency/assigned-bundles`.

Agency routes are read-only and scoped through existing agency tenant checks.

## Future Execution Layer

Any future execution layer requires a separate explicit phase covering authorization, permission semantics, route behavior, rollout controls, migration planning, audit design, tenant isolation, and tests.

Phase 40.0 intentionally stops at metadata and review history.

## Route Boundary

Phase 40.0 preserves canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` routes.

It adds APIs:

- `GET /api/platform/feature-bundle-assignments`
- `GET /api/platform/agencies/{agency_id}/bundle-assignments`
- `POST /api/platform/agencies/{agency_id}/bundle-assignments`
- `PUT /api/platform/bundle-assignments/{assignment_id}`
- `DELETE /api/platform/bundle-assignments/{assignment_id}`
- `GET /api/agencies/{agency_id}/feature-bundle-assignments`
- `GET /api/agencies/{agency_id}/feature-bundle-assignment-history`

It does not add `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes.
