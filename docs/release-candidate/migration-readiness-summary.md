# Product Recovery Migration Readiness

**Status:** analysis ready; migration execution not authorized.

Every Product Recovery analyzer was run against disposable in-memory state and
against its deterministic non-empty regression fixture where available.
Production was not accessed. All analyzers reported zero writes; collection
counts were unchanged. Available write-like flags were rejected.

## Analyzer Inventory

| Analyzer | Domain | Bounded records evaluated | Deterministic candidates | Ambiguous/manual review | Writes | Remaining blocker | Future approval |
|---|---|---:|---:|---:|---:|---|---|
| `analyze_identity_tenancy_migration.py` | identity, staff membership, Portal mapping | 10 collections; fixture regression | fixture-verified | ambiguity preserved | 0 | historical identities and subjects need Agency-scoped review | explicit confirmation, one Agency, audit evidence, rollback manifest |
| `analyze_legacy_request_v4_migration.py` | Request intake and V4 aggregate | bounded Request set; fixture regression | fixture-verified | unresolved passengers remain review items | 0 | no automatic identity or Request reconstruction | reviewed request-level conversion plan |
| `analyze_reference_wiring_migration.py` | PTC and canonical references | 7 collections, limit 250; fixture regression | fixture-verified | ambiguous, inactive, and cross-scope values preserved | 0 | legacy free text needs governed mapping | approved Agency/domain reference batch |
| `analyze_commercial_lifecycle_migration.py` | Offer, acceptance, Trip, Booking, Ticket, EMD | 16 collections; 71-check fixture regression | fixture-verified | ambiguous lineage preserved | 0 | compatibility families still require reconciliation | one Agency/domain, before/after manifest, rollback plan |
| `analyze_commercial_ledger_migration.py` | Invoice, Payment, allocation, cost, credit, refund, exchange | 12 collections; 19-check fixture regression | fixture-verified | manual review always required for financial truth | 0 | historical cost, margin, allocation, and lineage cannot be inferred | finance owner approval plus immutable reconciliation evidence |
| `analyze_operational_collaboration_migration.py` | timeline, messages, attachments, notifications | 19 collections; 5-check fixture regression | fixture-verified | orphan/duplicate/link issues preserved | 0 | historical visibility and participants require review | scoped communication/timeline manifest |
| `analyze_portal_completion_migration.py` | explicit Client/Passenger Portal mappings | 6 collections; 31-check fixture regression | fixture-verified | duplicate or missing mappings preserved | 0 | email cannot authorize or auto-select a subject | identity-owner approval and revocation plan |
| `analyze_governed_automation_migration.py` | work, rules, dependencies, SLA, notifications | 11 collections, limit 100; 61-check fixture regression | fixture-verified | invalid lineage/cycles/manual review preserved | 0 | compatibility tasks and rules require review | scoped rule/work-item plan with safety approval |

The direct empty-database baseline also proved bounded output and zero writes;
it is not used as proof that non-empty reconciliation works. The listed fixture
regressions provide that evidence.

## Write-Mode Controls

- Identity, ledger, collaboration, Portal, and automation analyzers reject
  `--write` or `--apply`.
- Reference wiring rejects `--write` with a runtime safety error.
- Request V4 and commercial lifecycle analyzers expose no write mode.
- No analyzer contacts production or selects a production database by default.

## Required Future Migration Gate

A future migration is a separate reviewed change and requires:

1. explicit human authorization;
2. one Agency and one domain at a time;
3. deterministic candidate list and manual-review disposition;
4. immutable before/after counts and checksums;
5. backup, off-host copy, and rehearsed rollback;
6. tenant and Portal isolation tests;
7. audit evidence and operator identity;
8. no inference of passenger identity, commercial truth, or finance truth.

Product Recovery 12 does not add migration execution.
