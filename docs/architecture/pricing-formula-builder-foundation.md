# Pricing Formula Builder Foundation

Phase 52.4 adds the metadata-only Pricing Formula Builder Foundation.

It creates `pricing_formula_builders` as reusable no-code metadata records for airline ancillary and service pricing formulas. Records describe pricing unit, way, route type, flight type, fare bundle, pricing category, amount type, currency, base amount, formula components, multipliers, applicability, manual confirmation, client visibility, and refund/exchange condition references.

## Scope

- Platform API: `/api/platform/pricing-formula-builder`
- Agency API: `/api/agencies/{agency_id}/pricing-formula-builder`
- Platform UI: `/platform/pricing-formula-builder`
- Agency UI: `/agency/pricing-formula-builder`
- Collection: `pricing_formula_builders`
- Module catalog entries: Platform `Pricing Formula Builder`, Agency `Pricing Formula Builder`

## Metadata Stored

Each pricing formula builder record stores:

- airline and service family/code metadata
- pricing unit, way, route type, flight type, and fare bundle metadata
- pricing category and amount type metadata
- currency, base amount, and optional range metadata
- formula components and multipliers as structured metadata
- applicability metadata for route, cabin, passenger, item, service, or agency constraints
- manual confirmation and client visibility metadata
- refund and exchange condition references
- evidence, governance, service parameter taxonomy, and visual policy editor links

## Supported Amount Types

Phase 52.4 supports `fixed`, `range`, `percentage`, `manual_quote`, `formula`, `included`, and `not_applicable`.

## Supported Pricing Categories

Phase 52.4 supports `transport_core`, `ancillary_airline`, `ancillary_non_airline`, `documentation`, `service_coordination`, `compliance_review`, `manual_handling`, `premium_support`, `after_sales_change`, `refund_processing`, and `claim_processing`.

## Boundaries

Phase 52.4 does not calculate live prices, optimize pricing, integrate payment gateways, collect payments, call provider systems, issue bookings, issue tickets, issue EMDs, generate AI/LLM output, run background workers, send client messages automatically, or replace human authority.

Pricing Formula Builder records are advisory metadata. Agents and platform reviewers remain responsible for confirming prices, applicability, visibility, refund/exchange treatment, and client-facing language before use.

## Relationship To Chapter 52

Reference Data Engine supplies controlled values. Knowledge Import Templates describe future population schemas. Visual Policy Editor stores policy-card metadata. Pricing Formula Builder stores pricing formula metadata as a separate layer so pricing remains distinct from policy, capability, operational constraints, and service feasibility.

Phase 52.5 adds Operational Rule Composer as a separate no-code compound rule metadata layer. Pricing Formula Builder may reference rule-condition metadata later for human review, but Phase 52.5 does not execute rules and Phase 52.4 does not calculate prices. Pricing formulas, policy cards, service parameters, reference data, and compound rules remain separate metadata surfaces under human authority.

Phase 52.6 adds Knowledge Quality Assurance as a metadata-only QA review layer over pricing formula metadata. Knowledge QA can record missing pricing applicability, incomplete pricing formula, missing evidence, or requested changes, but it does not calculate prices, auto-approve formulas, publish, call providers, use AI, run workers, or replace human authority.
