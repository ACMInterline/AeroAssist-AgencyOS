# Phase Marker and Regression Integrity Foundation

## Purpose

Phase 56.5.1 separates mutable application build metadata from immutable capability provenance. Before this phase, historical Epic 55 and Journey smoke tests asserted exact equality with whichever current phase literal had most recently been copied into their services. Advancing from Phase 56.3 to 56.4 therefore made otherwise valid historical regressions fail.

The active build marker is `phase_56_5_1_regression_integrity_foundation`. It is defined once in `backend/build_phase.py` and is consumed by health, readiness, and runtime service response metadata.

## Phase Semantics

Four concepts must remain distinct:

1. **Current build phase** is the phase implemented by the running application. The backwards-compatible response field `phase` keeps this meaning.
2. **Capability phase** is the phase that introduced a service or readiness capability. Audited Epic 55 and Phase 56 readiness sections expose it as `capability_phase`, backed by each service's `CAPABILITY_PHASE` constant.
3. **Minimum required phase** is the oldest application build a historical smoke can validly exercise. Historical smokes use `MINIMUM_PHASE` and an at-or-after assertion.
4. **Historical provenance phase** belongs to a stored record, immutable snapshot, import foundation, or capability catalogue entry. It is not rewritten when the application advances.

Existing stored data is unchanged. In particular, `introduced_phase`, `foundation_phase`, rollout business phases, Journey source provenance, finalized snapshots, and audit event source values retain their historical meanings.

## Identifier Format

Application phase identifiers use:

```text
phase_<major>_<minor>[_<patch>...]_<descriptive_label>
```

At least major and minor numeric components and a descriptive label are required. Examples include `phase_55_9_airline_intelligence_scale_release_readiness_foundation` and `phase_56_5_1_regression_integrity_foundation`. Malformed values raise `InvalidPhaseIdentifier` with a deterministic message.

## Comparison Rules

`compare_phase_identifiers` compares integer components, not strings. Missing trailing numeric components are treated as zero for ordering, and descriptive suffixes do not affect numeric ordering. Therefore:

- 55.9 is before 56.0;
- 56.3 is before 56.4;
- 56.4 is before 56.5.1;
- 56.10 is after 56.9.

`phase_is_exact` validates both values and then requires the complete identifiers to match. It is reserved for a test whose subject is the current release marker or exact immutable provenance. `phase_is_at_least` is used for historical capability availability.

## Smoke Rules

Historical capability smokes must:

- declare the capability's true `MINIMUM_PHASE`;
- verify exact `CAPABILITY_PHASE` provenance where that contract is exposed;
- assert that service, health, and readiness build phases are at or after the minimum;
- continue checking capability-specific readiness sections and behavior.

They must not be changed to assert the newest exact phase. `backend/scripts/phase_assertions.py` provides the shared readable minimum-phase assertion without creating a larger test framework.

## Backwards Compatibility

No route, request schema, stored record, collection, tenant boundary, immutable snapshot, or frontend contract is removed. Existing `phase` fields continue to report the current application build. The additive readiness field `capability_phase` disambiguates provenance for the audited Epic 55 and Journey foundations without changing boolean-only service safety contracts. Runtime services that previously duplicated the stale Phase 56.3 or 56.4 current-build literal now import the canonical source.

## Readiness

`/api/health` and `/api/readiness` report the canonical current build phase. Readiness includes `phase_marker_regression_integrity_foundation`, which verifies only deterministic code capabilities and adds no filesystem or database probe.

## Files and Validation

The implementation adds the build-phase utility, shared smoke helper, focused Phase 56.5.1 smoke, server registration, explicit provenance on audited services, minimum-phase assertions in Epic 55 and Phase 56.0-56.4 smokes, and this documentation. Validation uses:

```bash
python3 -m compileall -q backend
python3 backend/scripts/smoke_phase_marker_regression_integrity_foundation.py
python3 backend/scripts/smoke_airline_master_profile_intelligence_foundation.py
# Remaining Epic 55 and Phase 56.0-56.4 regression smokes
git --no-pager diff --check
```

Frontend build validation is not required because Phase 56.5.1 changes no frontend file.
