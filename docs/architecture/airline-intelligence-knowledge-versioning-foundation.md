# Airline Intelligence Knowledge Versioning Foundation

Phase 39.2 adds a metadata-only knowledge versioning and publication-control layer on top of Phase 39.0 airline intelligence data packs and Phase 39.1 review readiness.

## Purpose

Reviewed staged airline intelligence can now be grouped into governed knowledge versions before any future operational promotion work is considered. The versioning layer records what would be included, which release channel metadata references it, how versions compare, and how a rollback would be reviewed. It does not write staged data into operational airline collections.

## Records

- `AirlineIntelligenceKnowledgeVersion` records version code, title, status, source pack/review/readiness references, safe-use flags, agency visibility mode, and metadata-only publication timestamps.
- `AirlineIntelligenceKnowledgeVersionItem` records included staged items, target domain/key/airline metadata, field mapping references, conflict references, readiness references, normalized preview metadata, and agency summaries.
- `AirlineIntelligenceKnowledgeReleaseChannel` records platform-owned release-channel metadata.
- `AirlineIntelligenceKnowledgeReleaseAssignment` records metadata-only channel/version/agency assignment status.
- `AirlineIntelligenceKnowledgeVersionComparison` records added, changed, and removed item summaries between two metadata versions.
- `AirlineIntelligenceKnowledgeRollbackPlan` records human rollback readiness metadata.
- `AirlineIntelligenceKnowledgeVersionSnapshot` records immutable version snapshots.

## Status Flow

Version status is a governance marker:

- `draft`
- `frozen`
- `approved`
- `published`
- `superseded`
- `rolled_back`
- `archived`

The `published` status means published metadata only. It does not publish CMS content, publish client portal content, send messages, or promote staged payloads into operational airline tables.

## Agency Visibility

Agencies can read current and preview knowledge versions through `/agency/airline-intelligence-knowledge-versions`. The agency response hides raw staged payloads and exposes plain-language version/item summaries only.

## Canonical Routes

Platform:

- `/platform/airline-intelligence-knowledge-versions`
- `/api/platform/airline-intelligence-knowledge-versions/*`

Agency:

- `/agency/airline-intelligence-knowledge-versions`
- `/api/agencies/{agency_id}/airline-intelligence-knowledge-versions/*`

Supplementary `/admin/*`, `/agent/*`, `/api/admin/*`, and `/api/agent/*` routes remain rejected.

## Safety Boundaries

Phase 39.2 does not:

- promote staged records into operational airline tables
- scrape
- call external APIs
- call external AI
- publish CMS content
- publish client portal content
- recommend airlines
- execute providers or GDS/NDC/OTA actions
- book or create reservations
- mutate PNRs
- ticket or issue EMDs
- charge, invoice, account, or settle
- send email, SMS, notifications, or public links

All records are governance metadata for human review.
