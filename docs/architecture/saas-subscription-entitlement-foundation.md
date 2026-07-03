# SaaS Subscription & Entitlement Foundation

Phase 39.5 adds metadata-only subscription and entitlement records for the Platform Console and read-only agency visibility.

## Platform Scope

Platform users can define:

- SaaS subscription plans
- Plan entitlements
- Agency subscription assignments
- Agency entitlement readiness
- Manual review notes
- Immutable subscription snapshots

These records describe which modules, airline intelligence domains, and data-pack channels are assigned to an agency. They do not bill, charge, invoice, settle, or enforce access automatically.

## Agency Visibility

Agency users see “My Subscription” in the Agency Workspace. This view is read-only and shows:

- Assigned subscription metadata
- Included module/data/airline-intelligence scopes
- Entitlement readiness
- Agency-visible review notes
- Immutable snapshot history

Internal platform review data stays hidden from agency projections where appropriate.

## API Routes

Platform routes live under:

- `/api/platform/saas-subscriptions/*`

Agency read-only routes live under:

- `/api/agencies/{agency_id}/saas-subscriptions/*`

No `/admin`, `/agent`, `/api/admin`, or `/api/agent` routes are added.

## Readiness

The readiness section `saas_subscription_entitlement_foundation` confirms plans, entitlements, assignments, readiness rows, review notes, immutable snapshots, platform UI, agency visibility UI, counts, and disabled safety flags.

## Safety Boundary

Phase 39.5 is metadata only. It does not add billing, payment, invoicing, settlement, automatic charging, Stripe, bank, card, tax, accounting, automatic access enforcement, CMS/client portal publishing, airline recommendations, provider execution, booking, PNR mutation, ticketing, EMD issuance, scraping, external APIs, external AI, or automatic sending.
