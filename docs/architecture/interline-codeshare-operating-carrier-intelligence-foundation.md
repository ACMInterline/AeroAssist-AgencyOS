# Interline, Codeshare, and Operating Carrier Intelligence Foundation

## Purpose

Phase 55.6 adds a governed intelligence layer for multi-carrier journeys. It records commercial relationships and operational responsibility rules for marketing, operating, validating, ticketing, plating, and handling carriers. The layer is advisory metadata: it does not shop, book, ticket, issue EMDs, message carriers, call providers, or change an operational record.

The foundation preserves existing `airline_interline_agreements` and `airline_emd_interline_rules` records as source truth. The normalized Phase 55.6 records are additive, evidence-linked governance views.

## Canonical Models

- `airline_carrier_relationships` records codeshare, interline, SPA, alliance, wet-lease, franchise, and regional-affiliate relationships.
- `airline_interline_agreement_profiles` describes ticketing, through-check, through-baggage, service-continuity, and interline-EMD support.
- `airline_codeshare_rules` identifies the governed owner for policy, SSR request, service confirmation, ancillary pricing, EMD issuance, airport fulfillment, baggage, and medical or pet rules.
- `airline_operating_carrier_policy_rules` records operating-carrier policy and fulfillment responsibility by service and scope.
- `airline_validating_carrier_rules` records ticket stock, plating, ticket issue, exchange, refund, and disruption responsibility.
- `airline_through_check_rules` records check-in, baggage, seating, and special-service continuity between carriers.
- `airline_baggage_responsibility_rules` records baggage-rule, collection, transfer, and most-significant-carrier context.
- `airline_service_responsibility_rules` records service-specific policy, SSR, confirmation, pricing, EMD, airport, and contact-desk ownership.
- `airline_interline_emd_rules` records EMD-A, EMD-S, RFIC/RFISC, issuing-carrier, and fulfillment responsibility metadata.

Every model supports effective dates, route and market scope, evidence links, confidence, freshness, governance, publication, agency visibility, and explicit unknown states.

## Advisory Evaluation

`InterlineCodeshareIntelligenceService.evaluate_itinerary` accepts a non-persisted itinerary snapshot and produces:

- a segment carrier-role map;
- policy, SSR, confirmation, pricing, ticket, EMD, airport, baggage, medical/pet, exchange, disruption, and contact-desk owners;
- through-check, through-baggage, seat, and special-service continuity;
- rule and evidence trace references;
- warnings, unsupported combinations, and manual-review requirements;
- reference-only context from operational constraints, feasibility, recommendations, and offer intelligence.

Missing evidence never causes a guessed owner. Unknown and conflicting ownership remains a manual-review state. Historical feasibility, recommendation, offer, and operational snapshots are not mutated.

## Visibility and Routes

Platform governance uses `/platform/interline-codeshare-intelligence` and `/api/platform/interline-codeshare-intelligence`.

Agency advisory visibility uses `/agency/interline-codeshare-advisor` and `/api/agencies/{agency_id}/interline-codeshare-advisor`.

Platform knowledge editors may create and update governance metadata. Agency users can view published records and request a transient advisory evaluation; they cannot mutate knowledge records. Restricted notes and unpublished records are removed from agency responses, and tenant access follows existing agency authorization.

## Safety Boundary

Phase 55.6 does not establish live interline, codeshare, GDS, NDC, ticketing, EMD, or baggage capability. It stores and evaluates governed planning assertions only. Human operational authority remains final, and any unsupported, stale, conditional, or unknown combination requires explicit review before action.
