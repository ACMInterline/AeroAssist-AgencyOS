# Airline Intelligence Data Pack Review Foundation

Phase 39.1 adds a metadata-only review and promotion-readiness layer on top of Phase 39.0 airline intelligence data packs.

## Purpose

Data packs can contain useful airline profile, fleet, route, fare, service, CMS, and future client portal metadata, but staged data must remain separate from operational airline intelligence collections until a later explicit promotion phase exists. Phase 39.1 records the human review evidence needed before that future work can be considered.

## Core Records

- `AirlineIntelligenceDataPackReview` records the review status, plain-language coverage summary, safe-use flags, and approval/rejection metadata for a staged pack.
- `AirlineIntelligenceDataPackReviewChecklistItem` records pack-level and item-level review checks.
- `AirlineIntelligenceDataPackFieldMapping` records how staged payload fields would map to existing operational airline intelligence collection fields.
- `AirlineIntelligenceDataPackConflict` records duplicate/conflict metadata such as duplicate staged items, missing mappings, missing targets, or unsafe surface flags.
- `AirlineIntelligenceDataPackPromotionReadiness` records whether a human-reviewed pack is ready for future explicit promotion.
- `AirlineIntelligenceDataPackReviewSnapshot` records immutable review snapshots.

## Promotion Readiness

Promotion readiness is not promotion. It is a metadata status that says a reviewed pack has completed checklist coverage, approved field mappings, and no open conflict metadata.

Phase 39.1 does not write to operational airline collections such as `airline_intelligence_profiles`, `airline_routes`, `airline_fare_families`, or `airline_ancillaries`. It only records how staged fields would map if a later explicit promotion phase is designed and authorized.

## Safe-Consumption Flags

Review and readiness records include safe-use flags for:

- Internal CRM context.
- Agency display.
- CMS website display.
- Client portal display later.
- Offer builder context.

These flags remain metadata. They do not publish content, expose client portal data, alter offers, or recommend airlines.

## Agency View

Agencies see plain-language coverage and safe-use status through `/agency/airline-intelligence-review-coverage`. Raw staged payloads, mapping details, and platform maintenance controls remain hidden.

## Safety Boundaries

Phase 39.1 does not:

- Automatically promote data into operational airline tables.
- Scrape airline websites.
- Call external APIs.
- Call external AI.
- Publish CMS content.
- Publish client portal content.
- Recommend airlines.
- Execute providers, GDS, NDC, bookings, PNR mutation, ticketing, EMD issuance, payment, invoice, accounting, or settlement.

## Canonical Routes

Platform governance lives under:

- `/platform/airline-intelligence-data-pack-reviews`
- `/api/platform/airline-intelligence-data-pack-reviews/*`

Agency read-only coverage lives under:

- `/agency/airline-intelligence-review-coverage`
- `/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews/*`

No `/agent`, `/admin`, `/api/agent`, or `/api/admin` routes are added.
