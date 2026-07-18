# Persistence Scalability and Tenant Query Hardening Foundation

## Scope

Phase 56.5.6 is an infrastructure-only persistence hardening phase. It adds bounded, deterministic, tenant-aware query primitives without changing product routes, authorization roles, operational models, collection ownership, immutable snapshot behavior, or frontend workspaces. It performs no destructive migration and never drops an index.

The canonical build marker is `phase_56_5_6_persistence_scalability_tenant_query_hardening_foundation`.

## Pre-change risk inventory

The repository audit found 1,044 `find_many` call sites before implementation. Many were already tenant-filtered, but the generic adapter had no limit, offset, projection, or deterministic sort contract. The detailed readiness assembly had 101 collection reads and 99 zero-argument reads, so a detailed probe could materialize complete collections. High-risk examples included:

- Passenger, Travel Request, Trip, Offer, Booking, Document, Timeline, and Work Queue list services loading matching collections before Python filtering and sorting.
- Airline service coverage and airline intelligence release-readiness dashboards loading complete governance collections before filtering.
- Work Queue synchronization loading several full tenant source sets during an explicit synchronization action.
- Detailed readiness deriving many historical counts and summaries from unbounded records.

Static source counts are evidence for prioritization, not proof of runtime safety. The checked-in legacy exception inventory sets a non-increasing ceiling and names the remaining reviewed hotspots.

## Canonical query contract

`backend/persistence_query.py` defines the shared contract:

- default page size: `QUERY_DEFAULT_LIMIT`, default 50;
- maximum page size: `QUERY_MAXIMUM_LIMIT`, default 250;
- negative offsets and non-positive limits are rejected;
- excessive limits are capped consistently;
- offset and tenant-bound continuation cursors are supported;
- total count is omitted unless explicitly requested;
- page metadata includes `limit`, `offset`, `returned`, `has_more`, `next_cursor`, and optional `total`.

Existing routes that return lists or established response objects keep those shapes. Migrated services use a maximum bounded compatibility page internally; future endpoint-specific pagination can expose the canonical metadata without forcing an all-at-once route redesign.

## Deterministic sorting

Every governed page uses an allowlisted primary field and an `id` tie-breaker in the same direction. Unsupported sort fields fail with `QueryValidationError`. User input is never passed directly to MongoDB as a sort expression. Existing service-level presentation ordering remains where it carries business semantics, such as Work Queue priority ordering, but the records feeding that ordering are bounded and deterministically read.

## Repository architecture

`backend/persistence_repository.py` provides separate entry points:

- `find_agency_records` requires `agency_id`, injects the tenant predicate, and rejects caller attempts to supply it.
- `count_agency_records` always applies the same tenant predicate.
- `find_platform_records` is the explicit governed cross-agency/platform path and is only appropriate after existing route authorization.
- `find_global_records` accepts only platform/global or reference-data collections.
- `find_mixed_records` merges global and agency records with deterministic precedence: agency override, platform record, and historical fallback only where explicitly requested.

Agency and global helpers reject incompatible collection ownership. Platform authorization remains in the existing dependencies and routers; the repository does not invent permissions.

## Filter and projection safety

Each registry entry allowlists filter and sort fields. Supported structured operators are `$eq`, `$ne`, bounded `$in`, `$gt`, `$gte`, `$lt`, and `$lte`. The foundation rejects:

- tenant-field overrides;
- keys beginning with `$`;
- arbitrary nested paths;
- regular expressions and `$where`;
- multi-operator objects;
- `$in` arrays above the shared bound;
- non-scalar filter values;
- projections outside the governed allowlist.

This is intentionally not a public MongoDB query language.

## Collection ownership registry

The registry makes data-access assumptions testable without redesigning models. Categories are:

- `agency_owned`;
- `platform_global`;
- `mixed_projection`;
- `immutable_snapshot`;
- `audit_security`;
- `operational_ephemeral`;
- `reference_data`.

Entries define the tenant field, default and allowed sorts, allowed filters, pagination support, historical-read behavior, and preservation-oriented deletion policy. The first governed set covers core Request, Trip, Passenger, Offer, Booking, Document, Timeline, Work Queue, Journey, airline coverage, and airline release-readiness paths.

## Index governance

Thirteen high-value additive indexes cover tenant list/queue ordering and selected global knowledge queries. Stable names are declared once in `GOVERNED_INDEX_SPECS` and installed through the existing compatibility-aware index creator. Tenant operational indexes begin with `agency_id`; queue/date fields and `id` complete the deterministic access path. Global coverage and release-readiness indexes begin with their operational lookup fields.

Startup checks an existing same-name or same-key index for compatibility. It raises on incompatible definitions and never calls `drop_index` or `drop_indexes`. Existing indexes and production records are untouched.

## Compatibility adapter and diagnostics

The existing `find_many(filters=None)` signature remains valid. Optional `sort`, `limit`, `offset`, and `projection` keywords were added for governed callers. In-memory and MongoDB adapters now share those semantics. Legacy calls remain observable as `legacy_unbounded`; calls inside a bounded context receive its limit.

Diagnostics contain only collection category, operation, duration, returned count, requested limit, tenant-scoped state, query class, slow-query flag, and optional correlation ID. Filter values, passenger details, credentials, tokens, and payloads are never logged. `QUERY_SLOW_THRESHOLD_MS` and `QUERY_DIAGNOSTICS_ENABLED` control behavior.

## Readiness bounding

Public summary readiness remains lightweight. The historical detailed readiness function is decorated with a 25-record bounded query context, so every legacy `find_many` call inside it is capped without rewriting unrelated readiness calculations. All detailed readiness entry points use `asyncio.wait_for` with `READINESS_DATABASE_TIMEOUT_SECONDS`. A timeout returns the existing public summary contract with `readiness_mode=degraded_summary` and a non-sensitive timeout diagnostic.

The deterministic readiness section is `persistence_scalability_tenant_query_hardening_foundation`. It reports configuration and capability flags only; it does not scan source files or collections per request.

## Migrated services

The first evidence-backed migration includes list/dashboard reads for:

- Passenger Workspaces;
- Travel Request Workspaces;
- Trip Workspaces;
- Offer Workspaces;
- Booking Workspaces;
- Document Workspaces;
- Operational Timelines;
- Agent Work Queue;
- Airline Service Coverage and Gap Management;
- Airline Intelligence Scale and Release Readiness.
- canonical Journey lists and Journey Option Composition lists.

These keep established response structures, filters, projections, and service-level ordering. Agency routes reach tenant-injecting paths; platform/global reads remain explicit.

## Known legacy exceptions

The migration intentionally does not alter hundreds of unrelated service reads blindly. Remaining reviewed areas include:

- explicit Work Queue source synchronization across tenant-scoped source collections;
- source-graph assembly during an explicit airline coverage assessment;
- source-graph assembly during explicit airline scale-readiness assessment;
- historical detailed readiness calculations, now bounded by context and timeout;
- older targeted reads that already include entity or agency predicates but have not adopted page metadata.

`backend/scripts/persistence_query_legacy_exceptions.json` records the non-increasing production call ceilings and reasons. `validate_persistence_query_foundation.py` prevents those ceilings from growing, rejects direct risky Mongo access, validates registry and index invariants, and ensures migrated services use the repository. Static checks complement, but do not replace, runtime isolation tests.

## Validation and future roadmap

The phase smoke uses disposable in-memory records to prove deterministic pages, stable tie-breaking, tenant injection, override prevention, bounded operators, allowlisted sorts, scoped counts, cursor isolation, platform/global separation, mixed precedence, index safety, diagnostic redaction, and readiness metadata. Docker CI additionally starts authenticated disposable MongoDB, creates indexes through normal startup, checks a governed index, and runs the foundation smoke without exporting database content.

Future service migrations should proceed from measured query evidence, register ownership before use, retain route contracts, add endpoint pagination only where callers can consume it, and replace each documented legacy exception as its business semantics are understood.

## Phase 56.5.8 Release-Gate Integration

The final pilot release gate records persistence scalability, query governance, and tenant isolation as distinct dimensions. Static registry validation is repository evidence; disposable tenant fixtures are disposable evidence; neither verifies the deployed production database. Remaining generic compatibility reads stay visible as a warning and are not silently presented as completed migration work.
