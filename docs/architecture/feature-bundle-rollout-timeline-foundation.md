# Feature Bundle Rollout Timeline Foundation

Phase 40.6 adds metadata-only rollout timeline history for feature bundle rollout plans.

## Scope

- `FeatureBundleRolloutTimelineEntry` records historical rollout events such as plan created, plan edited, approval requested, approval granted, schedule created, schedule changed, rollout started, rollout completed, and rollback planned.
- `FeatureBundleRolloutActor` records the human/system actor metadata attached to a timeline entry.
- `FeatureBundleRolloutEventType` keeps event naming canonical.
- Platform APIs can create and read timeline entry metadata.
- Agency APIs can only read timeline entry metadata for their own agency.
- Timeline lists are newest first and support filters for plan, agency, bundle, event type, and date range.

## Storage

The `feature_bundle_rollout_timeline_entries` collection is registered with lookup indexes for entry id, rollout plan, agency, bundle, event type, occurred timestamp, and created timestamp. This is additive only and does not migrate or mutate production records.

## Non-Goals

Phase 40.6 does not enable feature bundles, change agency permissions, execute rollout plans, schedule background jobs, publish content, call providers, send emails or notifications, enforce rollout state, modify subscriptions, bill, scrape, use AI, or introduce automation.

## Canonical Routes

- Platform API: `/api/platform/feature-bundle-rollout-timeline`
- Agency API: `/api/agencies/{agency_id}/feature-bundle-rollout-timeline`
- Platform UI: `/platform/feature-bundle-rollout-timeline`
- Agency UI: `/agency/rollout-timeline`

No `/admin`, `/agent`, `/api/admin`, or `/api/agent` route roots are introduced.
