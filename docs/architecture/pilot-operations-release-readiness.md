# Pilot Operations and Release Readiness

Phase 57.0 turns the Phase 56.5.8 release gate into a governed Platform operations surface. It persists operator evidence, pilot agency enrollment, synthetic pilot dataset metadata, health history, and explicit sign-offs while retaining the deterministic release assessment and protected observability boundaries.

Active phase: `phase_57_0_pilot_operations_release_readiness`.

## Canonical Ownership

The Phase 56.5.8 `FinalStabilizationPilotReleaseGateService` remains the canonical release assessment. Phase 57.0 persists its immutable assessment snapshots and groups dimensions for presentation under infrastructure, security, database, frontend, backend, observability, backups, and tenant isolation. It does not create a parallel release engine.

The existing `audit_events` stream records pilot evidence, agency status, synthetic dataset, timeline, assessment, and sign-off actions. Existing Platform roles and authentication are reused. No role, unauthenticated mutation path, `/admin/*` route, or direct database access path is introduced.

## Collections

- `pilot_operational_evidence` stores immutable deployment, smoke, backup, restore, production validation, release assessment, and human sign-off evidence.
- `pilot_agency_enrollments` stores invitation, enablement, activation, and disablement state for existing agencies.
- `pilot_synthetic_datasets` stores isolated synthetic fixture metadata and bounded generated references.
- `pilot_health_timeline_events` stores append-only deployment, health, readiness, smoke, incident, backup, restore, and pilot history.

Indexes are additive. Evidence type/reference, agency enrollment, dataset reference, status, event type, and timestamp access paths are indexed. No migration, reset, collection drop, or production seed occurs.

## Authorization

All routes use the canonical `/api/platform/pilot-operations` root and require existing Platform authorization. Platform Owner, Admin, and Support may read the dashboard, evidence, timeline, and bounded diagnostics. Evidence and timeline registration retain actor identity. Pilot agency invitation, enablement, activation, disablement, and synthetic dataset creation/removal are restricted to `platform_owner`. Sign-off uses the existing `PilotReleaseSignOff` role and explicit-human-approval rules.

Inviting a pilot agency records enrollment metadata for an existing AgencyOS agency. It does not create an agency, send email, change entitlements, or activate product features.

## Synthetic Data Safety

Synthetic datasets must use `PILOT_TEST_`, `DEMO_SYNTHETIC_`, or `CI_FIXTURE_` references and require an enabled or activated pilot agency. Records are bounded to 50, explicitly synthetic, contain no real identity data, and are stored only inside the pilot dataset registry. They do not create Passenger, Request, Trip, Offer, Booking, Ticket, EMD, payment, or provider records.

Removal is a soft, audited operation. It clears the synthetic record payload and record count while preserving the dataset envelope and action history. Production startup never creates pilot data automatically.

## Evidence and Approval

Release assessments require explicit production attestations and store the resulting immutable assessment hash. `PASS`, `WARNING`, and `BLOCKED` are recommendations, not release actions. An approval or approval-with-conditions sign-off can reference only a persisted `ready` assessment and must be submitted by the authenticated approving role with `human_approved=true`. Rejected sign-offs remain valid governance evidence. The service cannot sign off or deploy itself.

Conflicting or updated operational evidence is retained under a new reference. Historical evidence and sign-offs are not silently overwritten.

## Health and Diagnostics

`/api/health` exposes only the current phase and a static Phase 57.0 capability flag. Public `/api/readiness` exposes only static Phase 57.0 capability and safety fields. It contains no pilot agencies, evidence, sign-offs, operational counters, timings, startup timestamps, uptime, slow queries, audit records, or production details.

Protected `/api/platform/pilot-operations/production-diagnostics` reuses existing observability and query diagnostics. It returns bounded audit metadata, process telemetry summary, slow-query metadata, and request statistics. It exposes no raw log messages, request or response bodies, credentials, environment secrets, database values, or cross-tenant business records.

## UI

The canonical Platform page is `/platform/pilot-operations`. It shows deployment phase, health, readiness, database, backup, smoke, CI, production validation, and pilot approval state; grouped release dimensions; evidence; pilot agencies; synthetic datasets; health history; and protected diagnostics. There is no Agency or public pilot operations page.

## Explicit Non-Capabilities

Phase 57.0 does not provide provider connectivity, GDS execution, payment execution, booking or ticketing, release deployment, automatic approval, production migration, backup execution, restore execution, feature activation, entitlement enforcement, external notification, AI, scraping, or production access.
