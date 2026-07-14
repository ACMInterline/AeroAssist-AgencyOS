# Airline Intelligence Scale and Release Readiness Foundation

## Purpose

Phase 55.9 completes Epic 55 with a measurable, deterministic view of whether governed airline intelligence is ready for population at scale and controlled operational release. It consolidates canonical records created by the airline master, evidence, versioning, service coverage, distribution, interline, fare-brand, contact, knowledge production, QA, publishing, and agency-consumption foundations. It does not create another airline catalogue, policy store, publishing pipeline, or execution engine.

The active phase marker is `phase_55_9_airline_intelligence_scale_release_readiness_foundation`.

## Canonical Records

Phase 55.9 adds governance metadata in:

- `airline_intelligence_readiness_profiles`
- `airline_intelligence_readiness_assessments`
- `airline_intelligence_readiness_checks`
- `airline_intelligence_release_candidates`
- `airline_intelligence_release_gates`
- `airline_intelligence_release_decisions`
- `airline_intelligence_population_waves`
- `airline_intelligence_scale_issues`

These records hold references, deterministic scores, source-count snapshots, gate outcomes, human decisions, assignments, rollback references, warnings, and audit metadata. They do not copy canonical airline knowledge payloads or mutate historical versions, accepted offers, publications, or operational workspaces.

## Readiness Dimensions

Each assessment measures 18 dimensions:

1. Airline master profile completeness
2. Identity and alias integrity
3. Source and evidence coverage
4. Conflict status
5. Evidence freshness
6. Version and change governance
7. Required service-family coverage
8. Pricing coverage
9. Operational-rule coverage
10. Scenario-test coverage
11. Distribution capability coverage
12. Interline and codeshare responsibility coverage
13. Fare-brand and baggage coverage
14. Contact-directory coverage
15. QA state
16. Publishing state
17. Agency assignment readiness
18. Operational consumption readiness

The weighted score is deterministic. `passed`, `warning`, `unknown`, and `blocked` checks have explicit scores, source references, remediation links, and severity. A critical blocked check forces the assessment to `blocked` regardless of the numerical average.

## Release Gates

Every release candidate is evaluated against 11 deterministic gates:

- canonical identity valid
- evidence minimum met
- no unresolved critical conflict
- required service-family coverage met
- QA passed
- scenario tests passed
- version snapshot created
- effective dates valid
- client-facing and internal messages present and separate
- agency consumption payload valid
- rollback reference available

A candidate cannot be `release_ready`, approved, or released while any critical gate is unresolved. Gate evaluation is deterministic; the final release decision is an explicit, audited human action.

Release decisions update Phase 55.9 candidate metadata only. They do not update `airline_knowledge_publications`, publish a release, call a provider, assign an entitlement, activate a feature, or rewrite a historical snapshot.

## Population Waves

Population waves group airline codes, service-family targets, markets, routes, reviewers, due dates, candidate references, assignments, scores, completion, blockers, and warnings. A wave may be `complete` while one or more release candidates remain blocked. Wave completion never triggers automatic publication or production seeding.

The ten isolated templates cover a fully ready PETC/WCHC/UMNR airline, missing evidence, unresolved conflicts, missing pricing, stale contacts, untested interline responsibility, approved but unpublished knowledge, incomplete fare-brand data, a multi-airline population wave, and a rollback-required candidate. Templates are returned as metadata and are never seeded automatically.

## API and UI

Platform governance:

- UI: `/platform/airline-intelligence-readiness`
- API: `/api/platform/airline-intelligence-readiness`

Platform owners, admins, and knowledge editors may create profiles, run deterministic assessments, create candidates, evaluate gates, record decisions, track waves, and resolve issue metadata. Platform support remains read-only.

Agency visibility:

- UI: `/agency/airline-intelligence-readiness`
- API: `/api/agencies/{agency_id}/airline-intelligence-readiness`

Agency routes are read-only. They show only candidates explicitly assigned to the current agency and marked `released`; when a publication reference is present, the linked publication must also be `published`. Draft assessments, gates, decision traces, internal release notes, restricted source references, and other agencies' assignments are excluded.

## Safety Boundary

Phase 55.9 is metadata-only. It does not:

- publish knowledge automatically
- seed production data
- alter canonical policies, evidence, pricing, capabilities, or versions
- mutate historical snapshots
- call providers or external APIs
- run AI, scraping, schedulers, or background workers
- book, ticket, issue EMDs, send messages, or make passenger-specific decisions

Human release authority remains final. Release readiness means that governed metadata has passed the recorded gates; it is not evidence that a provider is live or that a specific passenger journey is feasible.

## Epic 55 Completion

Epic 55 now provides canonical airline identity, evidence governance, structured change detection, service coverage and gap management, distribution capability intelligence, interline responsibility intelligence, fare-brand and baggage intelligence, contact and communication intelligence, and controlled scale/release readiness. These layers support the five-pillar airline knowledge model while preserving Evidence, Policy, Pricing, Capability, and Operational Constraints / Procedures as separate concerns.
