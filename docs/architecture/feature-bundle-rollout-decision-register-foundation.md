# Feature Bundle Rollout Decision Register Foundation

Phase 40.10 adds a metadata-only decision register for feature bundle rollouts. It records why a rollout-related decision was made, which rollout plan it belongs to, and which bundle, dependency, risk, issue, or timeline metadata it references.

This foundation does not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, send notifications or email, execute webhooks, publish anything, or switch runtime behavior.

## Metadata Model

`feature_bundle_rollout_decisions` stores:

- `id`
- `rollout_plan_id`
- `rollout_phase`
- `decision_title`
- `decision_summary`
- `decision_reason`
- `decision_category`
- `decision_status`
- `decision_owner`
- `decision_date`
- `related_bundle_ids`
- `related_dependency_ids`
- `related_risk_ids`
- `related_issue_ids`
- `timeline_reference_ids`
- `notes`
- `created_at`
- `updated_at`

The service projects related plan, agency, bundle, dependency, risk, issue, and timeline context for display only.

## API Surface

Platform metadata endpoints:

- `GET /api/platform/feature-bundle-rollout-decisions`
- `GET /api/platform/feature-bundle-rollout-decisions/summary`
- `POST /api/platform/feature-bundle-rollout-decisions`
- `GET /api/platform/feature-bundle-rollout-decisions/{decision_id}`
- `PUT /api/platform/feature-bundle-rollout-decisions/{decision_id}`
- `DELETE /api/platform/feature-bundle-rollout-decisions/{decision_id}`

Agency read-only endpoints:

- `GET /api/agencies/{agency_id}/feature-bundle-rollout-decisions`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-decisions/summary`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-decisions/{decision_id}`

Agency visibility is derived from the decision's rollout plan metadata. Agency endpoints do not expose create, update, or delete methods.

## UI

Platform Console adds `Feature Bundle Rollout Decisions`.

Agency Workspace adds `Rollout Decisions`.

Both pages are read-only visualizations with filters for rollout, category, owner, and status. They show title, reason, related bundles, related dependencies, related risks, related issues, timeline references, and metadata-only safety copy.

## Readiness

The readiness section is `feature_bundle_rollout_decision_register_foundation`.

The active phase is `phase_40_10_feature_bundle_rollout_decision_register_foundation`.
