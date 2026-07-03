# Airline Intelligence Agency Consumption Bridge

Phase 39.3 adds a metadata-only bridge between platform-governed airline intelligence knowledge versions and agency-facing usage areas.

## Scope

- `AirlineIntelligenceAgencyConsumptionProfile` records agency/version/channel safe-use status, plain-language summaries, allowed/blocked notes, and platform internal owner notes.
- `AirlineIntelligenceAgencyKnowledgeAssignmentView` records agency-readable assignment projections with raw payloads hidden.
- `AirlineIntelligenceAgencyUsageReadiness` records metadata-only readiness for CRM, agency website/CMS, client portal, and offer builder usage.
- `AirlineIntelligenceAgencyConsumptionNote` records platform guidance or internal notes, with explicit agency visibility.
- `AirlineIntelligenceAgencyConsumptionSnapshot` records immutable metadata snapshots.

## Routes

Platform governance:

- `/platform/airline-intelligence-agency-consumption`
- `/api/platform/airline-intelligence-agency-consumption/*`

Agency read-only:

- `/agency/airline-intelligence-consumption`
- `/api/agencies/{agency_id}/airline-intelligence-consumption/*`

The agency projection hides internal platform-only notes and raw snapshot JSON.

## Safety

The bridge is metadata only. It does not publish CMS or client portal content, create public links, recommend airlines, execute providers, book, create or mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external APIs, call external AI, or send messages.

## Readiness

Readiness section: `airline_intelligence_agency_consumption_bridge`

Core flags:

- `consumption_profiles_enabled`
- `agency_assignment_visibility_enabled`
- `crm_readiness_metadata_enabled`
- `cms_readiness_metadata_enabled`
- `client_portal_readiness_metadata_enabled`
- `offer_builder_readiness_metadata_enabled`
- `agency_plain_language_ui_enabled`
- `platform_governance_ui_enabled`
- `metadata_only_consumption_enabled`
- all publishing, recommendation, provider execution, booking, PNR mutation, ticketing, EMD, payment/invoice/settlement, scraping, external API, external AI, and automatic sending paths disabled

Counts:

- `profile_count`
- `assignment_view_count`
- `usage_readiness_count`
- `note_count`
- `snapshot_count`
- `agency_visible_profile_count`
