# Subscription Entitlement UI Guardrails

Phase 39.6 adds read-only subscription entitlement visibility hints on top of the Phase 39.5 SaaS subscription and entitlement foundation.

## Scope

The feature derives agency/module visibility from existing metadata-only collections:

- `saas_subscription_plans`
- `saas_plan_entitlements`
- `agency_subscription_assignments`
- `agency_entitlement_readiness`
- `agency_subscription_review_notes`
- `agency_subscription_snapshots`

It does not add billing, payment, invoice, settlement, Stripe, card, bank, tax, accounting, charging, or automatic access enforcement.

## Visibility States

Agency modules can show one of these informational statuses:

- `included`
- `limited`
- `not_included`
- `review_required`
- `unknown`

These states are UI guardrails only. Routes remain clickable unless they were already unavailable for another reason.

## APIs

The platform review endpoint is:

- `GET /api/platform/saas-subscriptions/entitlement-visibility`

The agency read-only endpoint is:

- `GET /api/agencies/{agency_id}/saas-subscriptions/module-visibility`

Both endpoints return metadata summaries with disabled safety flags. They do not mutate subscription records and do not enforce access.

## UI

The Agency Workspace navigation and dashboard cards show entitlement badges using the shared module catalog. The explanatory text is:

`Subscription visibility is informational only and does not automatically enforce access.`

The Platform Console subscription page shows agency entitlement review visibility for owners as metadata only.

## Readiness

`/api/readiness` exposes `subscription_entitlement_ui_guardrails` with flags for entitlement visibility, agency navigation badges, platform review visibility, read-only guardrail UI, disabled automatic enforcement, disabled billing/payment/invoice/settlement, disabled provider/booking/PNR/ticketing/EMD execution, disabled external APIs/AI/scraping, disabled automatic sending, and `readiness_required: false`.

## Route Boundary

Phase 39.6 preserves canonical `/platform/*`, `/agency/*`, `/api/platform/*`, and `/api/agencies/{agency_id}/*` routes. It does not add `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes.
