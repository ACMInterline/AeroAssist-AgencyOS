# Airline Distribution PSS GDS NDC Capability Intelligence Foundation

## Purpose

Phase 55.5 creates governed planning intelligence for how an airline can be shopped, booked, fulfilled, and serviced across distribution channels. It records documented channel behavior, host context, provider readiness, restrictions, evidence, freshness, and fallback methods. It does not connect to a provider or prove that a provider is currently reachable.

Active phase: `phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation`.

## Canonical Ownership

The normalized Phase 55.5 records are additive children around the existing broad `airline_distribution_profiles`, `airline_pss_parameters`, and `airline_gds_parameters` records. Those older records remain retained as source context. Phase 55.5 does not migrate, delete, or silently rewrite them.

The foundation adds:

- `airline_distribution_channels`
- `airline_distribution_capabilities`
- `airline_pss_profiles`
- `airline_gds_participations`
- `airline_ndc_capabilities`
- `airline_fulfillment_capabilities`
- `airline_servicing_capabilities`
- `airline_distribution_restrictions`
- `airline_distribution_evidence_links`

Every record is metadata-only and uses canonical airline identity where available. Evidence links point into the Phase 55.2 governance layer. Phase 55.3 can version the normalized records. Phase 55.4 treats published channel and capability records as distribution-scope evidence.

## Channel And Capability Taxonomy

Canonical channels cover direct website, call center, airport desk, Amadeus, Sabre, Travelport, NDC aggregator, airline-direct NDC, consolidator, tour operator, and manual offline process.

Capability areas remain distinct:

- Shopping: schedule, availability, fares, branded fares, ancillaries, seat maps, and special-service visibility.
- Booking: PNR creation, multi-passenger, SSR, OSI, APIS/documents, special seats, pets, medical requests, groups, and interline/codeshare.
- Fulfillment: ticket issuance, EMD-A, EMD-S, RFIC/RFISC availability, exchanges, refunds, voids, revalidation, and residual value.
- Servicing: voluntary and involuntary change, schedule change, split PNR, name correction, ancillary modification, and disruption handling.

Capability status uses `supported`, `unsupported`, `conditional`, `manual_only`, `unknown`, `provider_specific`, `route_specific`, or `market_specific`.

## Provider Readiness Boundary

Capability status is separate from provider readiness. Provider readiness uses:

1. `documented_capability`
2. `configured_provider`
3. `tested_sandbox`
4. `production_enabled_provider`

Even `production_enabled_provider` is a reviewed planning assertion. All API projections retain `live_connectivity_confirmed: false`. No credential, token, password, secret, API key, or private-key field is accepted. No provider call, search, booking, ticketing, EMD issuance, refund, exchange, or servicing action is implemented.

## Agency Safety

Platform governance uses `/api/platform/airline-distribution-capabilities` and `/platform/airline-distribution-capabilities`. Platform owners, administrators, and knowledge editors can maintain metadata; platform support is read-only.

Agency visibility uses `/api/agencies/{agency_id}/distribution-capabilities` and `/agency/distribution-capabilities`. Agency routes are read-only and expose only published records whose visibility includes the agency. Internal notes, restricted evidence references, unpublished provider details, and credential-like material are not returned.

Agency output distinguishes published planning availability, manual handling, fallback methods, restrictions, freshness, and warnings. Unknown or incomplete data remains visible as a warning rather than becoming a false positive or a runtime error.

## Booking Handoff Integration

Phase 54.6 booking handoff reads a published agency-safe distribution planning snapshot for airline and channel context. The snapshot can explain warnings and fallback methods. It cannot activate a provider, configure connectivity, create a PNR, issue a ticket or EMD, or mutate accepted offer snapshots. Manual booking mode remains valid and human-controlled.

## Safety Invariants

- No credentials are stored.
- A planning record never implies live capability.
- Capability, policy, pricing, evidence, and provider configuration remain separate concepts.
- Historical accepted-offer and booking-readiness snapshots remain unchanged.
- Unknown, stale, conditional, route-specific, market-specific, and manual-only states are explicit.
- Provider and channel records are agency isolated and visibility governed.
- There are no external APIs, GDS/NDC calls, background workers, AI actions, or automatic production seeding.
