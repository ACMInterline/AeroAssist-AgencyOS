# Feature Bundle Rollout Change Request Foundation

Phase 40.11 adds metadata-only change request records for feature bundle rollouts. A change request records proposed scope, schedule, readiness, approval, dependency, risk, issue, decision, documentation, or operational changes around an existing rollout plan.

This phase does not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, run background workers or schedulers, send notifications or email, execute webhooks, publish, or switch runtime behavior.

## Metadata Model

`FeatureBundleRolloutChangeRequest` records:

- `id`
- `rollout_plan_id`
- `rollout_phase`
- `change_title`
- `change_summary`
- `change_reason`
- `requested_by`
- `requested_date`
- `change_type`
- `priority`
- `impact_level`
- `change_status`
- `affected_bundle_ids`
- `affected_feature_flag_ids`
- `related_decision_ids`
- `related_issue_ids`
- `related_risk_ids`
- `related_dependency_ids`
- `review_notes`
- `created_at`
- `updated_at`

The Mongo collection is `feature_bundle_rollout_change_requests`. Indexes cover id, rollout/status, status/priority, priority, impact level, change type, affected bundles, affected feature flags, related decisions, related issues, related risks, related dependencies, requested date, and created date.

## APIs

Platform routes live under `/api/platform/feature-bundle-rollout-change-requests`:

- `GET /api/platform/feature-bundle-rollout-change-requests`
- `GET /api/platform/feature-bundle-rollout-change-requests/summary`
- `POST /api/platform/feature-bundle-rollout-change-requests`
- `GET /api/platform/feature-bundle-rollout-change-requests/{change_request_id}`
- `PUT /api/platform/feature-bundle-rollout-change-requests/{change_request_id}`
- `DELETE /api/platform/feature-bundle-rollout-change-requests/{change_request_id}`

Agency routes live under `/api/agencies/{agency_id}/feature-bundle-rollout-change-requests` and are read-only:

- `GET /api/agencies/{agency_id}/feature-bundle-rollout-change-requests`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-change-requests/summary`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-change-requests/{change_request_id}`

Filters cover rollout, status, priority, impact level, and change type.

## UI

Platform Console adds `/platform/feature-bundle-rollout-change-requests` as **Feature Bundle Rollout Change Requests**.

Agency Workspace adds `/agency/rollout-change-requests` as **Rollout Change Requests**.

Both pages display read-only tables and filters for rollout, status, priority, impact level, and change type. They show affected bundles, affected feature flags, related decisions, related risks, related issues, and related dependencies. The UI explicitly states the metadata-only boundary and includes no activation or execution actions.

## Readiness

The readiness section is `feature_bundle_rollout_change_request_foundation`.

The active phase is `phase_40_11_feature_bundle_rollout_change_request_foundation`.
