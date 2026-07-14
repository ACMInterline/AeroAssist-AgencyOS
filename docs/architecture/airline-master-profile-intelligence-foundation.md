# Airline Master Profile Intelligence Foundation

Phase 55.1 adds a governed airline-profile enrichment layer without creating a second airline catalogue. The canonical identity remains the existing `airline_profiles` record and its `id`. Every Phase 55.1 record carries `canonical_airline_id` and must resolve to that identity before it can be created.

## Purpose

The enriched profile gives policy intelligence, capability evaluation, recommendations, offer building, booking readiness, ticketing, EMD handling, and operational workflows a common airline context. It combines existing `airline_profiles`, `airline_intelligence_profiles`, contacts, routes, distribution records, brand assets, capabilities, reference records, and governed Phase 55.1 metadata.

It does not replace those records, execute providers, call external APIs, scrape sources, generate knowledge with AI, or seed production data automatically.

## Model

- `AirlineMasterProfile` governs commercial name, accounting prefix, type, active status, evidence status, confidence, effective dates, review status, version, verification date, and internal notes for an existing canonical airline.
- `AirlineIdentityAlias` maps former names, commercial names, codes, and other identifiers back to one canonical airline.
- `AirlineGroupRelationship` records parent, subsidiary, franchise, affiliate, codeshare, interline, virtual/marketed-carrier, and wet-lease/operator context.
- `AirlineHubAssignment` records primary hubs and focus cities.
- `AirlineOperationalClassification` records business model, route region, haul length, passenger/cargo profile, aircraft-family coverage, and restricted service areas.
- `AirlineDistributionSummary` records known GDS, NDC, direct, call-centre, agency, airport-only, ticket-stock, validating-carrier, and EMD servicing metadata.
- `AirlineServiceDeskSummary` records group, medical, special-service, and other desk availability using existing contact references where available.
- `AirlineProfileEvidenceLink` points to retained source records, preserves unresolved conflicts, and carries field scope, confidence, validity, and verification metadata.
- `AirlineProfileRevision` stores immutable before/after snapshots, changed fields, actor, reason, and profile version.

These are global platform-governed collections. They are deliberately not agency-owned airline copies.

## Composition And Scoring

`AirlineMasterProfileIntelligenceService` resolves canonical identities by id, IATA code, ICAO code, or a governed alias. It composes identity and existing intelligence with approved related metadata, reports explicit unknown fields, and produces deterministic completeness and confidence scores.

Completeness measures presence across identity, governance, relationships, hubs, operations, distribution, service desks, evidence, effective dates, source references, and verification. Confidence combines the governed confidence level, completeness, verified evidence, and unresolved evidence conflicts. A low score or unresolved conflict creates manual-review visibility; it does not crash evaluation or silently manufacture an answer.

## Governance And Visibility

Platform roles use `/api/platform/airline-master-profiles` for governed profile creation and updates, aliases, relationships, hubs, classifications, distribution, service desks, evidence, revisions, coverage, and duplicate-candidate review.

Agency roles use `/api/agencies/{agency_id}/airline-master-profiles` read-only. Only currently effective `approved` or `published` profiles and related records are returned. The agency projection removes internal notes, audit actors, raw source metadata, revision snapshots, and restricted evidence source locations. The optional client-safe projection contains minimal identity and freshness metadata only.

Platform UI is `/platform/airline-master-profiles`. Agency UI is `/agency/airline-profiles`.

## Safety

- Canonical airline identity is reused; no duplicate catalogue is introduced.
- Raw evidence and normalized profile metadata remain separate.
- Conflicting evidence is retained with explicit conflict status.
- Effective dates and revision history are preserved.
- Agency access remains tenant-checked and read-only.
- Internal governance notes never appear in agency or client-safe output.
- No startup seed, destructive reset, external provider call, AI operation, background job, booking, ticketing, EMD action, or runtime enforcement is added.
