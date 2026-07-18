# Final Stabilization and Pilot Release Gate

## Scope

Phase 56.5.8 establishes the evidence-backed release decision boundary for the completed AgencyOS foundation. Its canonical marker is `phase_56_5_8_final_stabilization_pilot_release_gate` and its public readiness key is `final_stabilization_pilot_release_gate`.

This phase consolidates existing build, CI, security, MongoDB recovery, tenant-query, observability, deployment, and pilot-safety evidence. It adds no passenger, request, offer, policy, provider, AI, payment, booking, ticketing, portal, or SaaS functionality. It accesses no production system and performs no migration or deployment.

## Pre-Change Inventory

The repository already provided a canonical phase marker, a 139-script governed smoke inventory, four read-only GitHub Actions workflows, authentication and HTTP hardening, authenticated MongoDB configuration and recovery tooling, bounded tenant-aware persistence, privacy-safe observability, and Hostinger deployment runbooks.

Those foundations answered whether implementation mechanisms existed. They did not produce one environment-aware release decision, distinguish workflow definitions from hosted CI results, preserve operator attestations separately from machine checks, or stop disposable success from being presented as production proof.

## Assessment Model

`FinalStabilizationPilotReleaseGateService` builds a bounded immutable `PilotReleaseAssessment`. Every dimension records a stable key, environment scope, required state, evidence references, diagnostic, and remediation. Statuses are `passed`, `warning`, `blocked`, and `not_verified`. Overall status is `blocked`, `conditional`, or `ready`.

A required `blocked` or `not_verified` dimension always produces an overall blocked result. Warnings cannot hide blockers. A ready recommendation is not approval: `human_sign_off_required` remains true and automatic approval, deployment, and migration remain disabled.

Assessments are not persisted in this phase. Their canonical JSON content receives a deterministic SHA-256 hash and immutable Pydantic projection. The API exposes no update or delete route. If persistence is introduced later, corrections must create a superseding snapshot rather than mutate history.

## Environment Evidence Separation

Evidence is classified independently from dimension status:

- **Repository:** phase marker, source state, static validators, inventory registration, and documentation.
- **CI:** workflow definitions are repository evidence; only a reviewed GitHub-hosted run may attest execution success.
- **Disposable:** local or CI containers may prove build, authenticated MongoDB startup, isolation fixtures, and restore rehearsal without proving production state.
- **Production:** deployed commit and phase, authenticated MongoDB, current backup, off-host copy, public health, diagnostics protection, rollback, and operator access remain `not_verified` until explicitly attested.

Machine-verified evidence and operator-attested evidence use distinct labels. The service never derives production state from Docker, local, or CI evidence and never contacts production.

## Hard Blockers

Hard blockers include incomplete production MongoDB authentication, absent verified backup or off-host copy, missing restore rehearsal, unverified complete regression or GitHub Actions, tenant-isolation failure, unsafe readiness or diagnostics, failed frontend or Docker validation, unsafe production configuration, deployment drift, missing rollback evidence, unsafe pilot data, and missing operator readiness.

False evidence is `blocked`; absent required evidence is `not_verified`. Both block release. The default assessment is intentionally blocked because no production evidence is supplied through public readiness or ordinary repository execution.

## Warnings

Warnings cover dependency triage, the existing frontend chunk-size warning, process-local non-durable telemetry, and undefined formal RPO/RTO expectations. They require review and explicit attestation but do not become hard blockers by themselves. This phase records risk; it does not perform broad dependency upgrades, install telemetry vendors, or claim recovery objectives.

The local dependency snapshot recorded on 2026-07-17 must be refreshed before sign-off. `npm audit` reported three unresolved frontend build-tool findings: one high-severity Vite finding and two moderate findings affecting Vite/esbuild and PostCSS, with no critical finding. `python3 -m pip check` reported no broken Python requirements. The production frontend build passed but retained its chunk-size warning at approximately 2.88 MB minified for the main JavaScript asset. Current container bases are `python:3.12-slim`, `node:20-alpine`, `nginx:1.27-alpine`, and `mongo:7`; these floating patch tags require normal image-refresh review. These facts are repository/disposable evidence, not proof of production image state.

## Operator Evidence

`PilotReleaseProductionEvidence` accepts bounded metadata such as commit, phase, verification booleans, verification time, existing Platform role, and short evidence references. Extra fields are rejected. Passwords, tokens, authorization data, cookies, MongoDB URIs, secrets, archives, passenger records, and operational payloads are not accepted.

Operator evidence is an attestation. It is not independently proven by the service. `platform_owner`, `platform_admin`, and `platform_support` may inspect or calculate the protected assessment; only existing `platform_owner` or `platform_admin` roles are valid in a human sign-off record.

## CLI and Validation Orchestration

`backend/scripts/assess_pilot_release_readiness.py` reads repository metadata and an optional bounded JSON evidence file. It prints a human or JSON summary, may write a sanitized report, exits non-zero when blocked, and never runs deployment, migration, backup, restore, provider, or production-network operations.

`backend/scripts/run_pilot_release_validation.py` composes existing validators and smoke inventory tooling. Quick mode runs static release checks. Full mode builds the frontend and runs the canonical inventory under `none`, `shared_backend`, and `fresh_backend` isolation with disposable in-memory backends. Stage timestamps, durations, exit codes, and outcomes are retained in a sanitized result file; failures are not ignored.

Docker CI remains the owner of authenticated production-style container startup and restore rehearsal. The orchestrator can validate Compose syntax but does not deploy or infer production readiness.

## API and Readiness

Public `/api/readiness` exposes only bounded summary counts and safety flags. It contains no dimension details, evidence records, paths, backup names, hostnames, tenant data, or credentials. Public status remains blocked until an independently reviewed release process supplies and approves production evidence outside the public endpoint.

Protected Platform routes are:

- `GET /api/platform/diagnostics/pilot-release-gate`
- `POST /api/platform/diagnostics/pilot-release-gate/assess`
- `GET /api/platform/diagnostics/pilot-release-gate/sign-off-schema`

The POST operation calculates a non-persisted immutable assessment from validated metadata. It does not mutate release state or create approval. No sign-off mutation route exists.

## Pilot Fixture Policy

Pilot validation records must be synthetic, tenant-scoped, removable, free of real identity, passport, medical, payment, and provider credential data, and disconnected from live providers. Governed references begin with `PILOT_TEST_`, `DEMO_SYNTHETIC_`, or `CI_FIXTURE_`. Production startup never creates pilot fixtures automatically.

## Human Sign-Off

`PilotReleaseSignOff` requires an explicit decision, reason, existing approving Platform role, UTC timestamp, assessment hash, rollback reference, conditions, and `human_approved=true`. The system cannot create approval for itself. This phase does not persist sign-offs; future persistence must be append-only and superseding.

## Production Boundary

Repository implementation readiness, CI readiness, disposable validation, migration readiness, and deployment state are separate facts. A passing local or Docker run cannot verify production. GitHub workflow configuration cannot verify a hosted run. Production is expected to remain pinned until the Phase 56.5.5 MongoDB authentication migration, backup verification, off-host copy, restore rehearsal, sequential deployment validation, and human sign-off are complete.

The manual sequence and destructive-operation markings are defined in `deploy/hostinger/PILOT_RELEASE_RUNBOOK.md`.
