# Feature Bundle Rollout Readiness Foundation

Phase 40.1 adds a metadata-only rollout readiness layer for assigned feature bundles. It helps Platform Console users review whether a bundle assignment appears operationally ready for a future rollout discussion, while Agency Workspace users see read-only readiness summaries.

## Scope

- `FeatureBundleRolloutReadiness` records store `agency_id`, `bundle_id`, `assignment_id`, `readiness_status`, checklist items, notes, reviewer metadata, and timestamps.
- Checklist items store `item_key`, label, status, and notes.
- Status values are intentionally limited to `draft`, `reviewing`, `ready`, and `blocked`; checklist item statuses are `pending`, `passed`, `warning`, and `blocked`.
- Platform APIs live under `/api/platform/feature-bundle-rollout-readiness`.
- Agency read-only APIs live under `/api/agencies/{agency_id}/feature-bundle-rollout-readiness`.
- Frontend pages are `/platform/feature-bundle-rollout-readiness` and `/agency/bundle-rollout-readiness`.

## Metadata Only

Rollout readiness does not activate, deactivate, allow, hide, or block features. It does not enforce entitlements, evaluate subscriptions, change permissions, bill, send email/SMS, call providers, call external APIs, scrape, publish content, start workers, or execute rollout logic.

## Default Views

The service can derive default readiness views from existing Phase 40.0 assignment metadata. These views check whether assignment metadata exists, bundle metadata resolves, assignment review status is recorded, launch window metadata exists, and the rollout safety boundary is explicit. Platform users may persist default readiness records, but doing so stores review metadata only.

## Readiness Response Shape

Each response includes:

- Bundle name/key and agency metadata.
- Assignment summary.
- Readiness status.
- Checklist counts.
- Warning and blocker summaries.
- Safety flags confirming metadata-only behavior.

Agency responses hide payload detail and remain read-only.
