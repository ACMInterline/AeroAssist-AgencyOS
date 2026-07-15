# Legacy Regression Suite Migration

## Purpose

Phase 56.5.2 completes the migration begun in Phase 56.5.1. Historical smoke tests previously compared the running application's `phase` field with a copied exact current-build literal. Those assertions failed after a valid phase advance even when the capability, tenancy, authorization, persistence, validation, and failure-path behavior remained correct.

The active marker is `phase_56_5_2_legacy_regression_suite_migration`. This phase changes regression metadata and test orchestration only. It adds no product capability, route, schema, collection, migration, frontend surface, provider operation, AI behavior, worker, or production-data mutation.

## Assertion Semantics

Smoke scripts use one of three application-phase modes:

- `minimum`: a historical capability requires the running application to be at or after its evidence-backed `MINIMUM_PHASE`.
- `exact_current`: a narrowly allowlisted smoke explicitly validates current health, readiness, and canonical build registration.
- `none`: the smoke has no application-phase contract.

Minimum-mode scripts use `backend/scripts/phase_assertions.py`, which delegates parsing and numeric comparison to `backend/build_phase.py`. Exact current-build comparisons are prohibited unless the script appears in the inventory allowlist with its purpose and reason.

Legacy whole-number identifiers such as `phase_28_*` are represented as `phase_28_0_*` only for comparator input. Their historical source values and provenance are not rewritten.

## Classification And Evidence

Every phase-related occurrence was classified before migration as a stale current-application assertion, capability minimum, intentional current-build assertion, capability provenance, immutable historical value, fixture value, documentation, or ambiguity. Capability provenance, snapshots, audit values, fixtures, and explanatory text were left unchanged.

Minimum phases were selected from repository evidence in this order:

1. An existing capability constant in the owning service.
2. Readiness registration.
3. The capability architecture document.
4. `BUILD_PHASES.md`.
5. The commit that introduced the script or capability.
6. Closely related models, routes, and services.

The checked-in inventory records the resulting phase and evidence note for every smoke. Introducing commits supplied deterministic evidence for legacy scripts whose capability phase was not exposed elsewhere. No script remained ambiguous.

## Inventory

`backend/scripts/smoke_inventory.json` is the complete machine-readable smoke catalogue. Each `backend/scripts/smoke_*.py` file has exactly one entry containing:

- `script_path` and `capability_name`;
- `minimum_application_phase` or `null`;
- `phase_assertion_mode` (`minimum`, `exact_current`, or `none`);
- `requires_running_backend` and `requires_mongodb`;
- `mutates_disposable_test_data`;
- capability `scope` values;
- `test_class` (`focused`, `integration`, or `broad`);
- `suitable_for_future_ci`;
- evidence and compatibility `notes`.

The manifest is regression metadata, not a source for the current build phase. The canonical current marker remains in `backend/build_phase.py`.

## Validation And Runner

`backend/scripts/validate_smoke_inventory.py` discovers smoke files and verifies complete one-to-one inventory coverage, paths, required types, unique entries, parseable minimum phases, shared minimum semantics, the exact-current allowlist, absence of stale Phase 56.3/56.4 runtime comparisons, phase-neutral scripts, and zero unresolved entries. It is deterministic, reads repository files only, requires neither the application nor MongoDB, and exits non-zero with readable errors.

`backend/scripts/run_smoke_inventory.py` is a narrow subprocess runner. It supports focused, future-CI, scope, backend-requirement, and explicit-script filters. It announces each run or skip, preserves script exit results, reports pass/fail/skip totals, and exits non-zero after any failure. It does not conceal skips or create a parallel test framework.

The inventory is suitable for a future CI workflow, but this phase deliberately adds no GitHub Actions configuration. Runtime integration scripts still require the repository-supported backend environment declared by each entry.

## Exact-Current Allowlist

`backend/scripts/smoke_legacy_regression_suite_migration.py` is the only exact-current smoke. It validates Phase 56.5.2 canonical build, health, readiness, inventory counts, and registration. The allowlist entry in `smoke_inventory.json` documents why exact equality is necessary. Historical capability smokes use minimum semantics.

## Provenance Preservation

Historical values keep their original meaning. This includes `introduced_phase`, `foundation_phase`, capability phase, snapshot phase, release-wave phase, rollout phase, event source, migration provenance, and fixture values. The focused Phase 56.5.2 smoke checks representative model, knowledge-template, and Offer Delivery provenance literals. The validator searches runtime assertion shapes rather than globally rejecting historical phase text.

## Readiness

`/api/health` and `/api/readiness` report the canonical Phase 56.5.2 marker. The diagnostic `legacy_regression_suite_migration` readiness section exposes cached inventory counts for discovered/inventoried, minimum, exact-current, phase-neutral, and unresolved scripts plus validation, provenance, and no-product-change flags. The manifest is loaded once through `backend/smoke_inventory.py`; readiness does not scan the filesystem per request and is not a production dependency gate.

## Backwards Compatibility

Routes, request and response contracts, collections, stored records, immutable snapshots, historical provenance, tenant boundaries, frontend contracts, service behavior, and business assertions remain unchanged. The migration changes only stale application-phase predicates and leaves each smoke's feature-level assertions intact. No database or production-data migration is required.

The complete inventory run also aligned three historical assertions with canonical successor foundations. The Phase 36.3 Booking smoke now validates the preserved readiness-package identifier on the Phase 41.6 workspace projection while accepting its intentionally optional legacy summary. Platform navigation checks the Platform-only slice of the shared module catalogue rendered by the current layout. Rollout and operational timeline readiness use explicitly aliased event-type constants so their independent count namespaces cannot shadow each other. These are regression-contract and diagnostic corrections, not new product behavior.

## Validation Commands

```bash
git --no-pager diff --check
python3 -m compileall -q backend
python3 backend/scripts/validate_smoke_inventory.py
python3 backend/scripts/smoke_phase_marker_regression_integrity_foundation.py
python3 backend/scripts/smoke_legacy_regression_suite_migration.py
python3 backend/scripts/run_smoke_inventory.py
```

The final command executes the complete inventory when a safe local backend is running. Frontend build validation is not required because Phase 56.5.2 changes no frontend file.

## Files And Limitations

The implementation is concentrated in the canonical build marker, shared smoke helper, migrated smoke scripts, inventory loader/manifest/validator/runner, server readiness metadata, focused smoke, and architecture/build documentation. Inventory attributes are reviewed static metadata and must be updated whenever a smoke is added, renamed, or changes runtime requirements. The runner is intentionally sequential and does not provision MongoDB, start the API, isolate test data between scripts, or implement CI policy.
