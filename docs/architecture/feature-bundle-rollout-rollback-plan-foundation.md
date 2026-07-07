# Feature Bundle Rollout Rollback Plan Foundation

Phase 40.12 adds metadata-only rollback plan records for feature bundle rollout governance.

Rollback plans describe what humans intend to review if a rollout needs to be reversed later. They do not execute rollbacks, deactivate features, activate features, automate deployments, enforce entitlements, bill, call providers, call external APIs, use AI, run workers or schedulers, send notifications or email, execute webhooks, publish, or switch runtime behavior.

## Data Model

- `FeatureBundleRolloutRollbackPlan`
- `FeatureBundleRolloutRollbackTrigger`
- `FeatureBundleRolloutRollbackScope`
- `FeatureBundleRolloutRollbackStatus`
- `FeatureBundleRolloutRollbackPriority`
- `FeatureBundleRolloutRollbackPlanCreate`
- `FeatureBundleRolloutRollbackPlanUpdate`

The Mongo collection is `feature_bundle_rollout_rollback_plans`. Indexes cover id, rollout plan/status lookup, status/priority lookup, priority, scope, owner, trigger, affected bundle and feature flag references, related change request, decision, issue, risk, dependency references, and created time.

## API Surface

Platform endpoints:

- `GET /api/platform/feature-bundle-rollout-rollback-plans`
- `GET /api/platform/feature-bundle-rollout-rollback-plans/summary`
- `POST /api/platform/feature-bundle-rollout-rollback-plans`
- `GET /api/platform/feature-bundle-rollout-rollback-plans/{rollback_plan_id}`
- `PUT /api/platform/feature-bundle-rollout-rollback-plans/{rollback_plan_id}`
- `DELETE /api/platform/feature-bundle-rollout-rollback-plans/{rollback_plan_id}`

Agency endpoints:

- `GET /api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/summary`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/{rollback_plan_id}`

Agency endpoints are read-only and scoped through rollout plan agency visibility. No `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes are introduced.

## Frontend

- Platform Console: `/platform/feature-bundle-rollout-rollback-plans`
- Agency Workspace: `/agency/rollout-rollback-plans`

Both pages present read-only tables with rollout filters, status, priority, scope, owner, trigger, affected bundles, affected feature flags, related change requests, decisions, risks, issues, dependencies, and rollback steps.

## Readiness

Readiness key:

- `feature_bundle_rollout_rollback_plan_foundation`

Active phase:

- `phase_40_12_feature_bundle_rollout_rollback_plan_foundation`

The readiness section exposes metadata-only flags, disabled rollback execution, disabled activation/deactivation, disabled deployment automation, disabled entitlement enforcement, disabled billing, disabled provider/external API/AI execution, disabled workers/schedulers, disabled notifications/email/webhooks, disabled publishing, disabled runtime switching, and status/priority/scope/trigger counts.
