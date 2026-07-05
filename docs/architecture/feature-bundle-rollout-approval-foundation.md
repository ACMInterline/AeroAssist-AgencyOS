# Feature Bundle Rollout Approval Foundation

Phase 40.4 adds a metadata-only approval layer for feature bundle rollout plans.

## Scope

- Platform users can create and update rollout approval metadata records.
- Platform users can create approval note metadata.
- Platform users and Agency users can view approval status, notes, and timeline metadata.
- Agency endpoints are read-only and agency-scoped.
- Approval status values are `draft`, `submitted`, `under_review`, `approved`, `rejected`, and `archived`.

## Collections

- `feature_bundle_rollout_approvals`
- `feature_bundle_rollout_approval_notes`

Indexes are registered for rollout plan, agency, status, approver, and created-at lookups. No destructive migration or production data mutation is included.

## Routes

- `GET /api/platform/feature-bundle-rollout-approvals`
- `POST /api/platform/feature-bundle-rollout-approvals`
- `GET /api/platform/feature-bundle-rollout-approvals/summary`
- `GET /api/platform/feature-bundle-rollout-approvals/{approval_id}`
- `PUT /api/platform/feature-bundle-rollout-approvals/{approval_id}`
- `GET /api/platform/feature-bundle-rollout-approvals/{approval_id}/notes`
- `POST /api/platform/feature-bundle-rollout-approvals/{approval_id}/notes`
- `GET /api/platform/feature-bundle-rollout-approvals/{approval_id}/timeline`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-approvals`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-approvals/summary`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/notes`
- `GET /api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/timeline`

## Safety

This phase does not enable features, enforce permissions, gate runtime access, bill, use Stripe or payment providers, change authentication, deploy, schedule jobs, run webhooks or background workers, send email/SMS/notifications, use AI/OpenAI, scrape, publish, or execute rollouts.
