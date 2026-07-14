# Airline Service Coverage And Knowledge Gap Management Foundation

## Purpose

Phase 55.4 creates a deterministic coverage projection over existing airline knowledge. It answers whether a specific airline and service scope has complete published knowledge, partial or stale knowledge, unresolved conflicts, missing policy or pricing, unsupported rules, unnormalized evidence, missing scenarios, failed QA, or approved knowledge that remains unpublished.

The projection does not become a new source of airline policy truth. Policy cards, pricing formulas, operational rules, evidence assertions, capability rows, QA reviews, publications, scenario tests, population toolkits, and pilot-readiness assessments retain their existing ownership.

## Coverage Model

The foundation stores:

- `airline_service_coverage_profiles`: airline-level assessment summaries.
- `airline_service_coverage_cells`: dimensioned airline and service coverage snapshots.
- `airline_knowledge_gaps`: explicit missing, stale, conflicting, failed, or unpublished conditions.
- `airline_coverage_targets`: governed airline, service, dimension, and score targets.
- `airline_coverage_assessments`: deterministic run snapshots and integration counts.
- `airline_coverage_remediation_plans`: human-owned actions linked to detected gaps and existing population toolkits.

Cells can be scoped by service family and code, route and flight type, cabin, fare bundle, operating and marketing carrier, aircraft family, country and airport, distribution channel, effective date, and evidence freshness.

The minimum service catalogue includes WCHR/WCHS/WCHC, mobility devices and batteries, MEDA/MEDIF, OXYG/POC, UMNR, PETC, AVIH, SVAN, ESAN, EXST, CBBG, sports equipment, musical instruments, fragile or valuable items, special baggage, documents/compliance, and EMD/payment handling.

## Deterministic Scoring

Each cell records six integer scores from 0 to 100:

- completeness
- confidence
- freshness
- test coverage
- publication readiness
- operational usability

Completeness is a fixed weighted sum of policy, pricing, rule, evidence, normalization, document, approval, message, effective-date, and distribution signals. Confidence uses governed evidence and capability confidence with a conflict penalty. Freshness uses existing evidence freshness and effective/review dates. Test coverage uses existing scenario review status. Publication readiness combines human QA and controlled publication status. Operational usability is a fixed weighted aggregate.

Critical gaps cap operational usability below readiness and always set `operational_ready` to false. They include missing policy, pricing, rule, or evidence; stale evidence; unresolved conflicts; missing effective dates; required document or approval definitions; missing scenario tests; failed QA; unpublished knowledge; and unknown distribution scope. Score thresholds can be tightened by a coverage target but cannot bypass the critical-gap guard.

## Integrations

Assessment reads existing metadata from Knowledge QA, Publishing, Scenario Testing, Capability Matrix, Evidence Governance, and the normalized knowledge toolchain. It writes deterministic coverage summaries, gaps, and next actions into an already-existing Knowledge Population Toolkit when one is linked. Pilot Readiness includes the new profile, cell, ready-cell, and critical-gap counts.

Agency alternative-airline hints are sourced only from operationally ready published cells and optional ready records from the existing recommendation service. They are advisory links into the existing recommendation workflow, not a replacement ranking engine. Offer Intelligence records are never mutated.

## Visibility And Routes

Platform governance uses:

- `/api/platform/airline-service-coverage`
- `/platform/airline-service-coverage`

Agency read-only consumption uses:

- `/api/agencies/{agency_id}/airline-service-coverage`
- `/agency/airline-service-coverage`

Agency projections include only published cells visible to the agency, sanitized missing-or-unknown warnings, scores, effective dates, and advisory alternative-airline hints. They exclude unpublished source references, draft gap details, remediation internals, restricted evidence, and cross-agency records.

## Safety Boundary

Phase 55.4 does not publish airline knowledge, run scenarios, approve QA, alter recommendations, mutate offers, execute policies, calculate live prices, call providers, use AI, scrape sources, or run background workers. Human reviewers remain authoritative.
