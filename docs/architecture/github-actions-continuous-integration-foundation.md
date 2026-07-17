# GitHub Actions Continuous Integration Foundation

## Purpose

Phase 56.5.3 adds repository validation only. It does not add an application feature, route, collection, migration, frontend surface, provider integration, production credential, deployment operation, or production-data mutation. The active marker is `phase_56_5_3_github_actions_continuous_integration_foundation`, and the diagnostic readiness key is `github_actions_continuous_integration_foundation`.

The foundation responds directly to the Phase 56.5.2 production import incident. The original release passed local validation because an untracked `backend/smoke_inventory.py` was present in the developer worktree, but a clean production checkout did not contain it. CI now checks the tracked runtime loader, imports it from the backend working directory, and reproduces the `/app` production Docker layout before a change can be considered release-ready.

## Workflow Layers

| Workflow | Trigger | Purpose | Database |
| --- | --- | --- | --- |
| `.github/workflows/ci-fast.yml` | Every pull request, push to `main`, manual | Compile backend code, validate phase and inventory semantics, validate CI structure, import runtime modules, run static readiness checks, and build the frontend. | None; imports use memory-mode configuration. |
| `.github/workflows/ci-docker.yml` | Relevant pull requests and `main` pushes, manual | Build the production backend image, verify runtime files and imports under `/app`, start a safe container, and inspect health/readiness. | In-memory disposable backend. |
| `.github/workflows/ci-smoke-focused.yml` | Every pull request, push to `main`, manual | Run the inventory-defined static and focused tiers against a disposable backend. | In-memory disposable backend. |
| `.github/workflows/ci-regression-full.yml` | Manual and Monday/Wednesday/Friday schedule | Run every inventory entry sequentially with explicit backend-state isolation and retain machine-readable results. | Ephemeral MongoDB service is provisioned; the current inventory runs in memory mode because every entry declares `requires_mongodb: false`. |

No workflow publishes an image, logs into a registry, uses SSH, connects to Hostinger, writes repository content, or deploys the application. Production deployment remains an independent manual operation.

## Smoke Inventory Integration

`backend/scripts/smoke_inventory.json` remains the sole smoke classification source. Phase 56.5.3 adds:

- `ci_tier`: `static`, `focused`, `integration`, or `full_only`;
- `execution_isolation`: `none`, `shared_backend`, or `fresh_backend`.

The focused tier covers current phase integrity, legacy inventory integrity, authentication and tenant separation, core Request/Trip/Offer/Booking metadata, Documents, airline operational intelligence, canonical Journey representation, and Offer Delivery. Broad or recursive suites remain outside automatic pull-request smoke execution. `suitable_for_future_ci` retains its meaning: all checked-in smokes may run in the scheduled or manually dispatched complete workflow.

The complete workflow does not claim that the suite is stateless. Most entries run sequentially against a shared disposable backend. `smoke_reference_enrichment_imports.py` is marked `fresh_backend` because a complete shared run demonstrated order-sensitive reference state; it runs after a backend restart with a new in-memory database. Additional isolation classifications require observed evidence and inventory review.

`backend/scripts/run_smoke_inventory.py` supports tier and isolation filters and can write JSON containing discovered, selected, executed, passed, failed, skipped, duration, and exit-code data. A required smoke failure remains a non-zero runner failure.

## Docker Import Protection

The Docker workflow uses `backend/Dockerfile` with `backend/` as the build context, matching production Compose. It verifies:

- `/app/smoke_inventory.py` exists;
- `/app/scripts/smoke_inventory.json` exists;
- the manifest path is derived from the runtime module location;
- `SMOKE_INVENTORY_SUMMARY` loads with zero unresolved entries;
- `import server` succeeds;
- a non-root container starts with the documented writable export path;
- Docker health becomes healthy;
- health and readiness expose Phase 56.5.3 and its CI metadata.

The temporary image and container are removed in an unconditional cleanup step. No image is pushed.

## Safe Test Environment

Automatic focused and complete validation use `AEROASSIST_DB_MODE=memory`, demo authentication, startup seed data, loopback-only backend ports, and `runner.temp` document storage. The complete workflow provisions a GitHub Actions `mongo:7` service so future inventory entries explicitly marked `requires_mongodb` have a governed path, but the current suite does not connect to it. No production environment file, credential, database, document export, or external provider is used.

Safe failure artifacts are limited to runner result JSON and bounded non-sensitive Docker state. Raw backend logs, environment files, container environment inspection, database dumps, document exports, credentials, and tokens are not uploaded. Retention is seven days for focused or Docker failures and fourteen days for complete regression evidence.

## Permissions And Caching

Every workflow declares `contents: read`. Official actions are restricted to checkout, Python setup, Node setup, and artifact upload at pinned major versions. Pip and npm dependency caches use their checked-in lock or requirement files. Runtime data, secrets, tokens, document exports, and database volumes are not cached.

## Local Equivalents

Core validation can be reproduced locally with:

```bash
python3 -m compileall -q backend
python3 backend/scripts/validate_smoke_inventory.py
python3 backend/scripts/validate_ci_foundation.py
python3 backend/scripts/validate_persistence_query_foundation.py
python3 backend/scripts/validate_observability_foundation.py
python3 backend/scripts/smoke_observability_diagnostics_performance_telemetry_foundation.py --static
(cd backend && python3 -c "import smoke_inventory, server; print(server.app)")
npm ci --prefix frontend
npm run build --prefix frontend
python3 backend/scripts/run_smoke_inventory.py --tier static --dry-run
python3 backend/scripts/run_smoke_inventory.py --tier focused --dry-run
docker build --file backend/Dockerfile --tag aeroassist-ci-local backend
```

The underlying smoke commands require a disposable backend and `AEROASSIST_SMOKE_BASE_URL`. GitHub-hosted workflow success cannot be claimed until a commit is pushed and Actions executes it.

## Manual Full Regression

In GitHub, open **Actions**, choose **Full smoke regression**, and select **Run workflow**. The same workflow runs on Monday, Wednesday, and Friday at 02:17 UTC. Results and logs appear on the workflow run; failed jobs can be rerun from GitHub's run summary. This operation never deploys or contacts production.

## Known Limitations

- The complete suite remains sequential and can retain state inside its shared group.
- Fresh-backend isolation is evidence-driven rather than automatically inferred.
- Local structural validation cannot prove that GitHub-hosted runners, service containers, or scheduling are available.
- Workflow duration depends on GitHub runner and package-cache performance; the focused workflow is bounded to 25 minutes and full regression to 60 minutes.
- CI validates the production image layout but does not replace deployment readiness review or production monitoring.

## Phase 56.5.4 Security Follow-On

Phase 56.5.4 keeps all four CI workflows and migrates this phase's smoke to historical minimum semantics. The production Docker workflow now verifies the Phase 56.5.4 marker and 136-script inventory, while the new security smoke owns the sole exact-current assertion. See [Authentication, Security, and HTTP Hardening Foundation](authentication-security-http-hardening-foundation.md).

Phase 56.5.5 preserves least-privilege workflow permissions, advances the inventory to 137 scripts, and moves exact-current ownership to the MongoDB security and disaster-recovery smoke. Fast CI checks shell structure and restore guards; Docker CI uses ephemeral credentials and isolated resources to prove authenticated startup, backup, manifest inspection, count-verified restore rehearsal, and backend health. It uploads no database archive and never deploys or restores production. See [MongoDB Security, Backup, and Disaster Recovery Foundation](mongodb-security-backup-disaster-recovery-foundation.md).

Phase 56.5.6 advances the inventory to 138 scripts and moves exact-current ownership to the persistence scalability smoke. Fast CI runs the persistence static validator and disposable repository smoke. Focused inventory CI covers the same smoke. Docker CI uses authenticated disposable MongoDB startup to exercise normal index registration, verify a stable governed Work Queue index, execute bounded repository tests, and check the new phase marker. Workflow permissions remain `contents: read`; no database content is uploaded and no deployment occurs. See [Persistence Scalability and Tenant Query Hardening Foundation](persistence-scalability-tenant-query-hardening-foundation.md).

Phase 56.5.7 advances the inventory to 139 scripts and moves exact-current ownership to the observability smoke. Fast CI runs the observability validator and static smoke after persistence checks. Focused CI exercises live request correlation, safe errors, public readiness, protected diagnostics, and query telemetry reuse. Docker CI verifies structured application events, authenticated MongoDB startup, credential absence from captured output, current health/readiness, and the existing governed index. Raw backend logs are no longer uploaded as artifacts; bounded smoke result JSON and non-sensitive container state remain eligible. Workflow permissions remain `contents: read`, and no telemetry vendor, production credential, deployment, or production access is introduced. See [Observability, Diagnostics, and Performance Telemetry Foundation](observability-diagnostics-performance-telemetry-foundation.md).
