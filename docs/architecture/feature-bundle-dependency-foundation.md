# Feature Bundle Dependency Foundation

Phase 40.7 adds metadata-only dependency records for feature bundle rollout planning.

## Scope

- `FeatureBundleDependency` records an informational dependency for an agency bundle, optionally connected to a rollout plan.
- `FeatureBundleDependencyReference` records the dependency target, such as another bundle, a capability, an approval, a rollout plan, a schedule, or a readiness checklist.
- `FeatureBundleDependencyType` keeps dependency target categories canonical.
- Platform APIs can create, update, read, list, and metadata-delete dependency records.
- Agency APIs can only read dependency metadata for their own agency.
- Lists support filters by bundle, rollout plan, agency, and dependency type.

## Storage

The `feature_bundle_dependencies` collection is registered with indexes for dependency id, agency/bundle lookup, rollout plan/type lookup, bundle/type lookup, agency/type lookup, dependency reference lookup, and created timestamp. This is additive only and does not migrate or destructively modify existing production data.

## Non-Goals

Phase 40.7 does not execute rollout plans, schedule background jobs, enforce dependencies, block rollouts, activate feature bundles, modify permissions, send notifications, publish anything, call providers, or introduce automation.

## Canonical Routes

- Platform API: `/api/platform/feature-bundle-dependencies`
- Agency API: `/api/agencies/{agency_id}/feature-bundle-dependencies`
- Platform UI: `/platform/feature-bundle-dependencies`
- Agency UI: `/agency/bundle-dependencies`

No `/admin`, `/agent`, `/api/admin`, or `/api/agent` route roots are introduced.
