# AeroAssist AgencyOS Repository Reality Inventory

## Scope

This is Stage A of the Master Architectural Review. It inventories the repository as implemented and does not classify Phases 1-57. No application code, runtime behavior, database state, production system, or deployment was changed or accessed.

The stated production baseline is commit `670af0ead11072d6918ae80882eadf055cc70420` at `phase_57_0_pilot_operations_release_readiness`. The local `HEAD` is the same commit, but the inspected working tree also contains pre-existing uncommitted Phase 57.1 changes and reports `phase_57_1_production_evidence_pilot_sign_off_completion` from `backend/build_phase.py`. This inventory describes that current working tree and does not claim that the uncommitted state is deployed.

## Method

- FastAPI routes were read from the assembled `server.app` without running startup or connecting to MongoDB.
- MongoDB index initialization was replayed through `ensure_mongo_indexes` against an inert index catalog. No database was contacted.
- Python symbols, models, collection constants, service imports, and persistence calls were extracted with AST/token analysis.
- Frontend routes were extracted from the `routes` map and ordered `window.location.pathname` matchers in `frontend/src/App.jsx`.
- Page API lineage includes direct API literals and one-level imported client/component modules.
- Smoke metadata came from `backend/scripts/smoke_inventory.json`; CI and deployment files were inspected directly.
- Documentation comparisons treat wildcard route families as families, not missing literal endpoints.

Static extraction cannot prove runtime branch coverage, data migrations, or semantic equivalence. Confidence boundaries are recorded in `detected-overlaps-and-gaps.md`.

## Repository Size

| Measure | Count |
|---|---:|
| Tracked files at review start | 1,126 |
| Pre-existing untracked files | 2 |
| Backend Python files | 543 |
| Backend Python lines | 224,525 |
| Frontend source lines | 62,344 |
| Markdown lines before these review narratives | 23,176 |
| Architecture documents | 134 |
| Documentation files inventoried | 201 |

Generated Stage A artifacts are intentionally untracked and are not included in the pre-existing untracked-file count.

## Backend Architecture

### Application and routing

The FastAPI application is assembled in `backend/server.py`. It registers every discovered router module through `app.include_router(...)` after defining the top-level health, readiness, and audit endpoints.

| Measure | Count |
|---|---:|
| Router modules under `backend/routers` | 235 |
| Router modules represented in the assembled app | 235 |
| FastAPI method/path operations | 2,163 |
| Unique method/path operations | 2,163 |
| Exact duplicate method/path operations | 0 |
| Platform API operations | 980 |
| Agency API operations | 1,082 |
| Reference API operations | 24 |
| Portal API operations | 40 |
| Other public/shared API operations | 37 |

Canonical route roots found in code are `/api/platform/*`, `/api/agencies/{agency_id}/*`, `/api/reference/*`, and shared/auth/public/portal roots under `/api/*`. Every endpoint row, dependency chain, source symbol, and route prefix is in `backend-route-inventory.csv`.

### Services and models

| Measure | Count |
|---|---:|
| Service modules | 135 |
| Public service classes/functions recorded | 500 |
| Data/schema class definitions | 1,537 |
| Direct `BaseModel` subclasses | 585 |
| Enum definitions | 441 |
| Exact duplicate model names | 0 |
| Exact duplicate service class names | 0 |

Most schemas are centralized in `backend/models.py` (28,386 lines). Services generally receive the shared `Database` abstraction and call `db.collection(...)`; router-to-service imports and collection references are listed in `service-inventory.csv`.

### Persistence and indexes

Persistence is split across:

1. `backend/database.py`: in-memory and Mongo adapters, connection lifecycle, `create_compatible_index`, the legacy `AGENCY_OWNED_COLLECTIONS` startup registry, and `ensure_mongo_indexes`.
2. `backend/persistence_query.py`: bounded/query-safe pagination, collection ownership metadata, tenant predicates, diagnostics, and 13 named governed index specifications.

| Measure | Count |
|---|---:|
| Discovered collection names | 503 |
| Collections receiving startup indexes | 497 |
| Additive startup index specifications | 3,347 |
| Legacy agency-owned startup registry entries | 397 |
| Governed-query ownership entries | 49 |
| Overlap between the two ownership registries | 45 |
| Collection names outside both ownership registries | 102 |
| Named governed-query index specifications | 13 |
| Startup indexes without an inventoried collection | 0 |

The 102 unclassified names are not automatically defects: many are global/reference/security collections indexed directly in `database.py`. They do, however, lack an explicit ownership classification in either current registry and are therefore a factual governance-coverage gap.

### Startup and lifecycle

`backend/server.py` defines `startup` and `shutdown` event handlers. Startup validates configuration, connects through the shared database abstraction, initializes additive indexes, records route count/telemetry, and optionally seeds only when configured. Shutdown disconnects the database and records bounded telemetry. Health and readiness are split among:

- `root_health` at `/api/health`;
- public-safe `public_readiness_payload` at `/api/readiness`;
- bounded detailed readiness for authorized modes;
- key-protected `/api/system/readiness`;
- platform-protected observability diagnostics in `backend/routers/platform_observability.py`.

### Authentication and authorization

Authentication primitives are in `backend/security.py`; identity/session resolution and authorization dependencies are in `backend/auth.py`. Canonical dependencies include `get_current_identity`, `get_current_user`, `require_platform_role`, `require_agency_role`, and `get_current_agency_context`.

Static dependency inspection found 73 endpoints with explicit platform-role closures, 2 with directly named agency-scope dependencies, 2,070 with authenticated dependency chains, 1 internal-header guard, and 17 public/manual routes. Many agency routers use local authenticated helper dependencies and enforce agency scope in service/router code, so dependency-name counts are not a complete authorization audit.

## Frontend Architecture

The frontend is React/Vite but does not use React Router. `frontend/src/App.jsx` evaluates ordered exact/regex matches and then falls back to a static `routes` object. This makes source order part of routing behavior.

| Measure | Count |
|---|---:|
| Page modules under `frontend/src/pages` | 287 |
| Route registrations in `App.jsx` | 302 |
| Unique frontend paths | 288 |
| Redundant path registrations | 14 |
| Module catalog hrefs | 228 |
| Shared API client/component modules with endpoint literals | 7 |
| Page modules without static `App.jsx` registration | 5 |

Primary layouts are `PlatformLayout`, `AgencyLayout`, `ClientPortalLayout`, and `PublicLayout`. Platform navigation is generated from `platformModuleGroups`; agency navigation is generated from `agencyModuleGroups` and annotates entitlement visibility as informational. `ProtectedRoute` renders loading/error boundaries, while authorization is ultimately enforced by backend dependencies and agency checks.

After imported client modules are considered, no routed page with direct API usage lacks a matching backend route family. Seventeen route rows retain a partial static match because one API expression is dynamically composed; those rows require runtime tracing before being called gaps.

## Operations and Infrastructure

| Component | Count | Canonical sources |
|---|---:|---|
| Docker/Compose definitions | 4 | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `docker-compose.production.yml` |
| CI workflows | 4 | `.github/workflows/*.yml` |
| Smoke scripts | 142 | `backend/scripts/smoke_*.py` |
| Smoke inventory entries | 142 | `backend/scripts/smoke_inventory.json` |
| Deployment/support files | 18 | `deploy/hostinger/**` |
| Backup/restore/pruning files | 14 | `deploy/hostinger/scripts/**`, systemd units, runbooks |
| Deploy runbooks | 8 | `deploy/**/*.md` |

The CI surfaces are fast validation, focused smoke, full regression, and production Docker validation. Backup tooling includes authenticated Mongo archive creation, checksum/manifest verification, restore rehearsal, pruning, and systemd scheduling. The inventory records commands and requirements but does not execute them.

Observability is centered in `backend/observability.py`, persistence diagnostics in `backend/persistence_query.py`, configuration/security validation in `backend/config.py`, `backend/security.py`, and `backend/auth.py`, and health/readiness assembly in `backend/server.py`.

## Documentation Architecture

The repository contains root phase/deployment documents, 134 files under `docs/architecture`, six permanent foundation documents under `docs/architecture/foundations`, deployment runbooks, and supplementary blueprint/alignment maps. `documentation-inventory.csv` records titles, phase references, route-reference counts, and existing code-path references for 201 Markdown files.

The documentation corpus references five API strings that do not resolve as implemented route families. Four are intentionally prohibited `/api/admin*` and `/api/agent*` examples. The remaining `/api/health/ready` reference in `docs/architecture/ticket-workspace-foundation.md` is stale relative to `/api/readiness` and `/api/system/readiness`.

## Artifact Guide

- `backend-route-inventory.csv`: router modules, endpoints, prefixes, dependencies, services, and frontend reference status.
- `frontend-route-inventory.csv`: route registrations, pages, layouts, module catalog/navigation, direct/imported API clients, and backend matching.
- `model-and-collection-inventory.csv`: model/schema classes, collections, ownership, and every startup index specification.
- `service-inventory.csv`: service symbols, router consumers, models, collections, persistence helpers, and lexical external-I/O markers.
- `smoke-and-ci-inventory.csv`: smokes, inventory metadata, CI, containers, deployment, backup/restore, readiness, observability, and security surfaces.
- `documentation-inventory.csv`: architecture, blueprint, root, and deploy documentation.
- `detected-overlaps-and-gaps.md`: evidence-based overlap/gap register with confidence limits.

## Limitations

- No production or local database was queried; collection counts describe code-declared names, not deployed collections.
- Index counts describe the final additive startup intent captured in an inert registry, not current production index state.
- Static API matching cannot resolve every computed path or prove a UI action is reachable.
- Static symbol use cannot detect reflection, string-based imports, or external consumers.
- Authorization dependency names do not replace endpoint-by-endpoint security testing.
- Current uncommitted Phase 57.1 files are included because Stage A inventories repository reality, while the declared production baseline remains Phase 57.0.
