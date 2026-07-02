# Offer Policy Advisor Integration Foundation

Phase 37.2 connects the Phase 37.1 airline policy comparison and service advisor layer to offer workspaces as metadata-only advisory context.

## Scope

- `offer_policy_advisor_contexts` stores offer workspace/option context, taxonomy references, service mechanics lookup metadata, linked advisor artifacts, and safety flags.
- `offer_policy_advisor_airline_rows` stores offer-linked airline rows derived from policy comparison/service advisor output.
- `offer_policy_advisor_warnings` stores human-reviewed warning records from context, comparison, advisor, pricing, and mechanics metadata.
- `offer_policy_advisor_decision_notes` stores manual staff notes. Notes are not automatic recommendations.
- `offer_policy_advisor_saved_snapshots` stores immutable advisory snapshots for later review.

## Routes

- Agency operational API: `/api/agencies/{agency_id}/offer-policy-advisor/*`
- Platform read-only diagnostics API: `/api/platform/offer-policy-advisor/*`
- Agency UI: `/agency/offer-policy-advisor`
- Platform UI: `/platform/offer-policy-advisor`

No `/agent` or `/admin` routes are introduced.

## Safety Boundaries

- No automatic airline recommendation.
- No automatic offer price mutation.
- No live booking, ticketing, EMD issuance, payment, invoice, accounting, BSP/ARC settlement, provider execution, scraping, or external AI.
- Complexity scores remain operational indicators only.
- Agency users cannot mutate global platform-owned comparison/advisor records.
- Platform offer advisor endpoints are diagnostics/read-only.

## Integration Links

Offer advisor contexts can reference:

- offer workspace and option ids
- policy comparison snapshots and rows
- service advisor scenarios and results
- ancillary pricing quote results
- service mechanics lookup metadata
- canonical taxonomy domain, family, and variant references

These links support staff review and future governance without creating operational side effects.
