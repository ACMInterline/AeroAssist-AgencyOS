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

At Phase 56.5.2, `backend/scripts/smoke_legacy_regression_suite_migration.py` owned the exact-current assertion. Exact-current ownership advances with each release-registration phase; this smoke now uses minimum semantics. The current allowlist entry in `smoke_inventory.json` documents its active owner and reason. Historical capability smokes use minimum semantics.

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

## Production Hotfix Correction

The initial Phase 56.5.2 production deployment failed during `server` import with `ModuleNotFoundError: No module named 'smoke_inventory'`. The runtime loader existed in the local validation worktree as an untracked `backend/smoke_inventory.py` file, but commit `7da2bdb7` did not contain it. Local smokes and `uvicorn` therefore resolved the untracked sibling module, while the production image built from a clean Git checkout had no `/app/smoke_inventory.py` for `server.py` to import.

The Docker build context and ignore rules were not the cause: production builds use `backend/` as the context and the Dockerfile copies that context into `/app`; no ignore rule excludes `smoke_inventory.py`. The corrective hotfix includes `backend/smoke_inventory.py` as the canonical application-runtime loader. It resolves `scripts/smoke_inventory.json` from `Path(__file__).resolve().parent`, caches the parsed manifest, exposes one module-level summary for readiness, and raises explicit errors for a missing, malformed, or structurally invalid manifest. Validator, runner, focused smoke, and runtime readiness continue to share this implementation.

`compileall` was insufficient because bytecode compilation checks syntax without importing `server` or resolving `smoke_inventory`. Hotfix validation therefore includes a direct `server` import from `backend/`, an import inside the production Docker image where the working directory is `/app`, container startup, Docker health status, and live Phase 56.5.2 health/readiness checks. The focused migration smoke also verifies the canonical module path, cached summary equality, and absence of per-request filesystem discovery.

## Phase 56.5.3 CI Follow-On

Phase 56.5.3 makes the production-import correction repeatable in GitHub Actions. The Phase 56.5.2 smoke now uses minimum-phase semantics, while the Phase 56.5.3 registration smoke is the sole exact-current assertion. The canonical inventory also classifies CI tiers and backend-state isolation, and the production Docker workflow proves that the tracked loader and manifest exist under `/app` before importing `server` and starting a healthy container. See [GitHub Actions Continuous Integration Foundation](github-actions-continuous-integration-foundation.md).

## Phase 56.5.4 Security Follow-On

Phase 56.5.4 migrates the Phase 56.5.3 CI smoke to minimum-phase semantics and advances sole exact-current ownership to the authentication, security, and HTTP hardening smoke. Public production readiness now exposes a safe summary while the historical detailed payload remains available through configured internal readiness and the development/test regression contract. See [Authentication, Security, and HTTP Hardening Foundation](authentication-security-http-hardening-foundation.md).

Phase 56.5.5 migrates the Phase 56.5.4 security smoke to minimum-phase semantics and advances sole exact-current ownership to the MongoDB security, backup, and disaster-recovery smoke. The inventory now contains 137 classified scripts, with infrastructure safety and disposable recovery validation remaining explicit and non-production. See [MongoDB Security, Backup, and Disaster Recovery Foundation](mongodb-security-backup-disaster-recovery-foundation.md).
