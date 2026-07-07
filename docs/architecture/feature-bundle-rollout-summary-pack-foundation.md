# Feature Bundle Rollout Summary Pack Foundation

Phase 40.13 adds a metadata-only summary evidence-pack layer for feature bundle rollouts. It stores references to the rollout metadata that has already been collected across plans, readiness, approvals, schedules, timelines, dependencies, risks, issues, decisions, change requests, and rollback plans.

This foundation does not generate PDFs, export files, publish packs, send notifications, send email, call providers or external APIs, use AI, activate or deactivate features, enforce entitlements, switch runtime behavior, schedule background work, or execute rollouts.

## Metadata Model

The canonical record is `FeatureBundleRolloutSummaryPack` with:

- `id`
- `rollout_plan_id`
- `pack_title`
- `pack_summary`
- `pack_status`
- `generated_for_audience`
- `covered_bundle_ids`
- `readiness_reference_ids`
- `approval_reference_ids`
- `schedule_reference_ids`
- `timeline_reference_ids`
- `dependency_reference_ids`
- `risk_reference_ids`
- `issue_reference_ids`
- `decision_reference_ids`
- `change_request_reference_ids`
- `rollback_plan_reference_ids`
- `evidence_notes`
- `compliance_notes`
- `created_at`
- `updated_at`

The Mongo collection is `feature_bundle_rollout_summary_packs`. Indexes cover id, rollout/status lookup, status/audience lookup, audience, covered bundle references, every reference-id array, and created time. Index registration is additive only and does not migrate or destructively modify existing data.

## API Surface

Platform endpoints:

- `GET /api/platform/feature-bundle-rollout-summary-packs`
- `GET /api/platform/feature-bundle-rollout-summary-packs/summary`
- `POST /api/platform/feature-bundle-rollout-summary-packs`
- `GET /api/platform/feature-bundle-rollout-summary-packs/{pack_id}`
- `PUT /api/platform/feature-bundle-rollout-summary-packs/{pack_id}`
- `DELETE /api/platform/feature-bundle-rollout-summary-packs/{pack_id}`

Agency endpoints are read-only and scoped through the rollout plan agency:

- `GET /api/agencies/{agency_id}/feature-bundle-rollout-summary-packs`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/summary`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/{pack_id}`

Filters are metadata-only and include rollout, status, audience, and bundle.

## UI Surface

- Platform Console: `/platform/feature-bundle-rollout-summary-packs`
- Agency Workspace: `/agency/rollout-summary-packs`

Both pages are read-only visualizations. They show pack title, rollout, audience, status, covered bundles, readiness, approval, schedule, timeline, dependency, risk, issue, decision, change request, rollback plan references, evidence notes, compliance notes, and summary counts.

## Readiness

The readiness section is:

- `feature_bundle_rollout_summary_pack_foundation`

The active phase is:

- `phase_40_13_feature_bundle_rollout_summary_pack_foundation`

Readiness flags explicitly keep PDF generation, file export, rollout execution, feature activation/deactivation, entitlement enforcement, billing, provider calls, external APIs, AI, workers, schedulers, notifications, email, webhooks, publishing, runtime switching, and automation disabled.
