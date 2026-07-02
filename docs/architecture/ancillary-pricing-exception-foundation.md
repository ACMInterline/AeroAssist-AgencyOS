# Ancillary Pricing And Exception Foundation

Phase 37.0 adds the policy-based ancillary pricing and exception metadata layer for AeroAssist AgencyOS.

## Separation

- Taxonomy identifies what the service is.
- Mechanics identifies how the service is requested, confirmed, or paid as SSR/OSI/EMD metadata.
- Pricing estimates how a fee may apply.
- Exceptions explain when service or pricing is restricted, blocked, risky, or manually reviewed.

Pricing records may reference mechanics records such as payment rules or EMD issuance metadata, but those references never issue EMDs, tickets, SSRs, OSIs, invoices, payments, or settlement events.

## Models

- `AirlineAncillaryPricingRule`
- `AirlineAncillaryPriceComponent`
- `AirlineAncillaryPricingApplicability`
- `AirlineAncillaryPricingMatrix`
- `AirlineAncillaryPricingMatrixRow`
- `AirlineServiceExceptionRule`
- `AirlineServicePriceQuoteScenario`
- `AirlineServicePriceQuoteResult`
- `PolicyCandidatePricingLink`

## APIs

- Platform governance APIs live under `/api/platform/ancillary-pricing/*`.
- Agency lookup, quote scenario, quote result, and candidate-link APIs live under `/api/agencies/{agency_id}/ancillary-pricing/*`.
- UI routes are `/platform/ancillary-pricing` and `/agency/ancillary-pricing`.

## Quote Evaluation

The deterministic evaluator matches active pricing rules by airline and canonical domain/family/variant, applies conservative applicability filters, evaluates applicable exception rules, and sums fixed components using segment and direction counts where available.

Unknown, range, or percentage pricing is flagged for manual review. Missing pricing returns `no_price_found`. Blocker exceptions return `blocked`.

Stored quote results are audit/testing artifacts only. They are not invoices, payment requests, accounting postings, BSP/ARC settlement records, EMDs, tickets, or provider instructions.

## Safety

- No live booking.
- No live ticketing.
- No EMD issuance.
- No payment processing.
- No invoice, accounting, BSP/ARC, settlement, or ledger logic.
- No live GDS/NDC/provider execution.
- No external AI.
- No scraping.
- No automatic agency-to-global promotion.
- No `/agent` or `/admin` routes.
