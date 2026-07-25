# Automation Compatibility and Migration

## Runtime Compatibility

- Existing work queue, task, workflow, deadline, timeline, and Operations
  deep links remain valid.
- Request task writes adapt to `OperationalWorkItem`.
- Historical `request_tasks` reads remain available as projections.
- Platform governance routes cannot act as Agency staff.
- Notification records are regenerable from canonical timeline evidence.
- Legacy event aliases normalize to canonical dotted event keys.

Compatibility adapters never dual-write actionable task truth. Unsupported
legacy mutations return `409`.

## Dry-run Analyzer

`backend/scripts/analyze_governed_automation_migration.py` reports, without
writes:

- task duplicates, missing Agency or entity lineage, invalid state/deadline,
  inactive assignee, missing completion evidence, and legacy task types;
- workflow instances without work, orphan deadlines, dependency orphans and
  cycles, duplicate projections, and cross-record inconsistencies;
- conflicting active rule keys, legacy assignment rules, approvals without
  source work, and automation runs without exact timeline lineage.

Output is deterministic by Agency, domain, and category and distinguishes
candidate mappings from ambiguous manual-review cases. Collection counts are
compared before and after analysis. `--write` is explicitly rejected and no
write mode exists.

## Known Migration Gap

Historical duplicate records are not migrated or deleted in Product Recovery
11A. Any future reconciliation requires reviewed dry-run output, explicit
operator authorization, backup evidence, and a separately approved migration.

Persistent scheduler activation also remains a deliberate gap. The current
deployment supports only authenticated, bounded manual processing with
idempotency reservations, recoverable locks, finite retries, and manual-review
outcomes. A scheduler must not be enabled until the deployed topology can
prove duplicate-safe multi-instance processing and protected health
diagnostics without adding unsupported infrastructure.
