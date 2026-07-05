# Feature Bundle Rollout Risk Register Foundation

Phase 40.8 adds metadata-only risk register records for feature bundle rollouts.

## Scope

- `FeatureBundleRolloutRisk` records rollout risk metadata such as missing approval, dependency not ready, unclear agency impact, schedule conflict, incomplete documentation, or an operational concern.
- `FeatureBundleRolloutRiskImpact`, `FeatureBundleRolloutRiskLikelihood`, and `FeatureBundleRolloutRiskStatus` keep impact, likelihood, and status values canonical.
- Risks can optionally reference an agency, bundle, rollout plan, or dependency.
- Platform APIs can create, update, soft-delete, read, and list risk metadata.
- Agency APIs are read-only and scoped to the agency.

## Persistence

The `feature_bundle_rollout_risks` collection is registered with lookup indexes for risk id, agency/status, bundle/status, rollout plan/status, dependency, impact/likelihood, and created timestamp. This is additive only and does not migrate or destructively modify production records.

## Routes

- Platform API: `/api/platform/feature-bundle-rollout-risks`
- Agency API: `/api/agencies/{agency_id}/feature-bundle-rollout-risks`
- Platform UI: `/platform/feature-bundle-rollout-risks`
- Agency UI: `/agency/rollout-risks`

No `/admin`, `/agent`, `/api/admin`, or `/api/agent` route roots are introduced.

## Safety Boundaries

Rollout risks are informational metadata only. Phase 40.8 does not execute rollouts, enforce risk decisions, block rollouts or routes, send notifications, activate bundles, add automation, start background jobs, publish, or call external providers.
