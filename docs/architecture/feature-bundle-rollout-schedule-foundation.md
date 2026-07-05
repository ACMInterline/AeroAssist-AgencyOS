# Feature Bundle Rollout Schedule Foundation

Phase 40.5 adds metadata-only rollout scheduling records on top of rollout plan approval metadata.

## Scope

- Platform users can create and update intended rollout schedule metadata.
- Agency users can view rollout schedule metadata for their agency only.
- Schedule status values are `Planned`, `Ready`, `AwaitingApproval`, `Approved`, `Deferred`, `Cancelled`, and `CompletedMetadata`.
- Schedule records may include planned start/finish, maintenance window, estimated duration, dependencies, checklist summary, approval summary, and notes.

## Collection

- `feature_bundle_rollout_schedules`

Indexes are registered for schedule id, rollout plan, agency/status, bundle/status, planned start, and created-at lookups. No migration, destructive data change, or production data mutation is included.

## Routes

- `GET /api/platform/feature-bundle-rollout-schedule`
- `POST /api/platform/feature-bundle-rollout-schedule`
- `GET /api/platform/feature-bundle-rollout-schedule/summary`
- `GET /api/platform/feature-bundle-rollout-schedule/{schedule_id}`
- `PUT /api/platform/feature-bundle-rollout-schedule/{schedule_id}`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-schedule`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-schedule/summary`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-schedule/{schedule_id}`

## Safety

This phase does not execute rollouts, activate features, change entitlement behavior, modify permissions, introduce cron jobs, schedulers, workers, queues, timers, or background execution, call external APIs, introduce AI functionality, add billing logic, or publish anything automatically.
