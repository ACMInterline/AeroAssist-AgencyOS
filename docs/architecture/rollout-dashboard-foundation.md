# Rollout Dashboard Foundation

Phase 40.3 adds a read-only rollout dashboard that aggregates existing metadata into one visibility surface for Platform Console and Agency Workspace users.

## Scope

- Platform APIs live under `/api/platform/rollout-dashboard`.
- Agency APIs live under `/api/agencies/{agency_id}/rollout-dashboard`.
- Frontend pages are `/platform/rollout-dashboard` and `/agency/rollout-dashboard`.
- Dashboard sections cover Capability Catalog, Feature Flags, Feature Bundles, Assigned Bundles, Rollout Readiness, and Rollout Plans.
- Metadata collections `rollout_dashboard_views` and `rollout_dashboard_snapshots` are registered with indexes only.

## Metadata Only

The dashboard only aggregates existing records. It does not activate features, enforce entitlements, bill, charge, process payments, execute providers, run AI, publish, automate rollouts, start background workers, schedule jobs, send email/SMS/notifications, block routes, execute webhooks, scrape, call external APIs, or change permissions.

## Response Shape

Responses include:

- `summary` with read-only counts.
- `sections` for each dashboard card.
- `counts` with totals, status counts, warning counts, and blocker counts.
- `filters` for platform dashboard views.
- `snapshots` read from metadata collections only.

Agency responses are scoped to the requested agency and remain read-only.
