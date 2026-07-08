# Airline Operational Knowledge Governance Foundation

Phase 50.4 creates the Airline Operational Knowledge Governance & Version Control Foundation.

This phase is metadata-only. It treats Airline Operational Knowledge as governed operational assets, not loose documents. Evidence, Policy, Pricing, Capability, Operational Constraints, and Operational Procedures can be versioned independently and grouped into Knowledge Releases.

## Scope

- `AirlineKnowledgeVersion`, `AirlineKnowledgeVersionCreate`, and `AirlineKnowledgeVersionUpdate` models.
- `AirlineKnowledgeRelease`, `AirlineKnowledgeReleaseCreate`, and `AirlineKnowledgeReleaseUpdate` models.
- `airline_knowledge_versions` and `airline_knowledge_releases` Mongo collections and indexes.
- Platform metadata CRUD endpoints at `/api/platform/airline-knowledge-governance`.
- Agency read-only endpoints at `/api/agencies/{agency_id}/airline-knowledge-governance`.
- Platform UI routes `/platform/airline-knowledge-governance` and `/platform/airline-knowledge-releases`.
- Agency UI route `/agency/knowledge-governance`.
- Readiness section `airline_operational_knowledge_governance_foundation`.
- Active phase marker `phase_50_4_airline_operational_knowledge_governance_foundation`.

## Knowledge Lifecycle

Airline Operational Knowledge follows this metadata lifecycle:

Draft -> Under Review -> Approved -> Published -> Effective -> Superseded -> Archived -> Historical Audit

No knowledge object is physically deleted. Archive operations record lifecycle metadata and preserve historical lookup.

## Governed Knowledge Scope

Knowledge Governance controls:

- Evidence
- Policy
- Pricing
- Capability
- Operational Constraints
- Operational Procedures
- Knowledge Releases
- Historical Versions

## Version Metadata

Knowledge versions store lifecycle dates, author/reviewer/approver/publisher metadata, review notes, requested changes, approval notes, publication scope, knowledge-scope reference IDs, previous/superseded/replaced-by relationships, change summaries, comparison metadata, rollback metadata, and historical lookup tags.

Version comparison metadata supports:

- Version A
- Version B
- Added objects
- Modified objects
- Removed objects
- Changed effective dates
- Changed pricing
- Changed capability
- Changed operational constraints
- Changed procedures

## Release Metadata

Knowledge releases group multiple version records with release status, release version, release notes, included version IDs, airline/country/service applicability, audit roles, future AOIE readiness flags, rollback release metadata, superseded release metadata, and historical lookup tags.

Release metadata does not publish operational knowledge automatically. `published` is a lifecycle label only.

## Explicitly Excluded

Phase 50.4 does not implement live rule evaluation, AI reasoning, parser execution, recommendation engines, pricing calculation, provider integrations, background workers, automatic publication, scraping, external API calls, booking, ticketing, EMD issuance, payment, messaging, or automation.

## Phase 50.5 Consumer

Phase 50.5 Airline Operational Capability Matrix consumes governed versions and releases as evidence-backed capability inventory references. Governance records remain lifecycle metadata; the matrix records what airlines can operationally deliver. Neither phase evaluates passenger feasibility, ranks airlines, calculates pricing, calls providers, or automates publication.
