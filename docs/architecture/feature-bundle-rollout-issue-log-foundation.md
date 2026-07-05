# Feature Bundle Rollout Issue Log Foundation

Phase 40.9 adds metadata-only issue log records for feature bundle rollouts.

## Scope

- `FeatureBundleRolloutIssue` records rollout issue metadata for things that already went wrong or need attention, such as failed checklist items, approval follow-up, unresolved dependencies, unclear rollout dates, agency confusion, documentation gaps, or internal review concerns.
- `FeatureBundleRolloutIssueSeverity` and `FeatureBundleRolloutIssueStatus` keep severity and status values canonical.
- Issues can optionally reference an agency, bundle, rollout plan, risk, dependency, or approval.
- Platform APIs can create, update, soft-delete, read, and list issue metadata.
- Agency APIs are read-only and scoped to the agency.

## Persistence

The `feature_bundle_rollout_issues` collection is registered with lookup indexes for issue id, agency/status, bundle/severity, rollout plan/status, risk, dependency, approval, severity/status, and created timestamp. This is additive only and does not migrate or destructively modify production records.

## Routes

- Platform API: `/api/platform/feature-bundle-rollout-issues`
- Agency API: `/api/agencies/{agency_id}/feature-bundle-rollout-issues`
- Platform UI: `/platform/feature-bundle-rollout-issues`
- Agency UI: `/agency/rollout-issues`

No `/admin`, `/agent`, `/api/admin`, or `/api/agent` route roots are introduced.

## Safety Boundaries

Rollout issues are informational metadata only. Phase 40.9 does not execute rollouts, activate bundles, enforce blocking, send notifications, call external providers, or add AI/provider execution.
