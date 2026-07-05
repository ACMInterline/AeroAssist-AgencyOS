# Feature Bundle Rollout Plan Foundation

Phase 40.2 adds metadata-only rollout plan records for feature bundles after readiness review. Platform Console users can create and update planning metadata; Agency Workspace users can only read plan summaries for their agency.

## Scope

- `FeatureBundleRolloutPlan` records store `rollout_plan_id`, `agency_id`, `bundle_id`, `plan_name`, rollout stage, target start/end dates, rollout owner, checklist summary metadata, optional readiness snapshot reference, optional assigned bundle reference, notes, and timestamps.
- Rollout stages are `draft`, `readiness_review`, `scheduled`, `paused`, and `archived`.
- Platform APIs live under `/api/platform/feature-bundle-rollout-plans`.
- Agency read-only APIs live under `/api/agencies/{agency_id}/feature-bundle-rollout-plans`.
- Frontend pages are `/platform/feature-bundle-rollout-plans` and `/agency/rollout-plans`.

## Metadata Only

Rollout plans do not activate features, enforce access, block routes, publish content, send email/SMS/notifications, bill, charge, call providers, call external APIs, use AI, scrape, start workers, run cron jobs, or execute rollout logic.

## Response Shape

Plan responses include:

- Bundle name/key and agency metadata.
- Assignment and readiness snapshot references when present.
- Rollout stage and target window metadata.
- Checklist summary counts.
- Warning and blocker counts.
- Safety flags confirming metadata-only behavior.

Agency responses are read-only and scoped to the requested agency.
