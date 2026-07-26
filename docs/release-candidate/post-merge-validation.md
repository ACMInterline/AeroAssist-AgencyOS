# Post-Merge Validation

Run this gate on the exact unmodified `APPLICATION_MERGE_COMMIT`. A later
deployment-tooling commit does not replace application validation evidence.
For the current candidate:

```bash
APPLICATION_MERGE_COMMIT="de22b70c1ccdabf7bd6d28765addf63f79dd189d"
```

```bash
set -Eeuo pipefail
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = "$APPLICATION_MERGE_COMMIT"

python3 -m compileall -q backend
npm ci --prefix frontend
npm run build --prefix frontend
npm audit --prefix frontend
python3 backend/scripts/validate_smoke_inventory.py
python3 backend/scripts/validate_persistence_query_foundation.py
python3 backend/scripts/validate_canonical_domain_ownership.py
python3 backend/scripts/validate_canonical_identity_tenancy.py
python3 backend/scripts/validate_canonical_lifecycle_integrity.py
python3 backend/scripts/validate_product_experience_recovery.py
python3 backend/scripts/validate_stabilization_accessibility.py
python3 backend/scripts/validate_full_system_stabilization.py
python3 backend/scripts/validate_observability_foundation.py
python3 backend/scripts/validate_final_stabilization_pilot_release_gate.py

AEROASSIST_ENV_FILE=.env.production.example \
  docker compose \
    --env-file .env.production.example \
    -f docker-compose.production.yml \
    config --quiet

python3 backend/scripts/run_pilot_release_validation.py \
  --profile full \
  --include-docker-config \
  --output /tmp/aeroassist-product-recovery-post-merge.json

npm run test:e2e --prefix frontend -- --project=chromium
git diff --check
```

Use the repository's production-readiness validator with strong disposable
secrets and a synthetic production-shaped environment. Never point it to a
production database from a workstation.

## Docker Candidate

```bash
docker info
docker build \
  --label "org.opencontainers.image.revision=${APPLICATION_MERGE_COMMIT}" \
  -f backend/Dockerfile \
  -t "aeroassist-backend:rc-${APPLICATION_MERGE_COMMIT:0:8}" \
  .
docker build \
  --label "org.opencontainers.image.revision=${APPLICATION_MERGE_COMMIT}" \
  -f frontend/Dockerfile \
  -t "aeroassist-frontend:rc-${APPLICATION_MERGE_COMMIT:0:8}" \
  frontend
```

Validate both images on a disposable Docker network with a disposable MongoDB,
non-demo authentication, writable document storage, public health and safe
readiness, anonymous diagnostics rejection, and authorized bounded Platform
diagnostics. Remove the temporary network, containers, volumes, reports,
Python caches, and `frontend/dist` after evidence is recorded.

## Workflow Planning Validation

Run `actionlint` across every workflow before dispatching hosted validation:

```bash
actionlint .github/workflows/*.yml
```

Any error is a blocker. In particular, `${{ runner.temp }}` is invalid in
`jobs.<job_id>.env`: GitHub rejects that workflow while planning it, so the run
contains no jobs or runner logs. Affected jobs must instead create
`$RUNNER_TEMP/document-exports` in an early step and append
`DOCUMENT_EXPORT_STORAGE_DIR` to `$GITHUB_ENV`. This keeps the path outside the
repository and makes it available only after a runner exists.

## Hosted Focused-Smoke Dependency Repair

The first hosted Focused run that reached its runner failed in `Run focused
inventory tier` when
`backend/scripts/smoke_platform_agency_ux_consolidation.py` intentionally ran
`npm run build --prefix frontend`. Vite was unavailable because the Focused
workflow had installed backend dependencies only; it had neither configured
Node nor run the locked frontend installation.

The reviewed repair must retain the UX smoke and its frontend build, configure
Node 20 with npm caching against `frontend/package-lock.json`, and run:

```bash
npm ci --prefix frontend
```

before both inventory tiers. The always-run cleanup must remove
`frontend/dist` and temporary frontend build output without deleting source or
failure evidence.

After the repair is committed to the reviewed workflow branch, rerun in this
order:

1. `actionlint .github/workflows/*.yml`;
2. the Focused workflow;
3. confirm frontend dependency installation succeeded;
4. confirm static and focused tiers completed with zero failures;
5. confirm `smoke_platform_agency_ux_consolidation.py` and its production build
   passed; and
6. only then dispatch the exact-commit gate for the approved application SHA.

Stop if locked installation fails, Vite remains unavailable, any selected
smoke is skipped or ignored, the UX smoke fails, or generated build output
survives cleanup. Do not reclassify or weaken the smoke to obtain a pass.

## Hosted Exact-Commit Gate

After the CI tooling repair is reviewed and present on `main`, dispatch its
workflow definition while passing the application SHA:

```bash
BEFORE_RUN_ID="$(
  gh run list \
    --workflow ci-docker.yml \
    --event workflow_dispatch \
    --limit 20 \
    --json databaseId,displayTitle \
    --jq "map(select(.displayTitle | contains(\"application=$APPLICATION_MERGE_COMMIT\")))[0].databaseId // empty"
)"
gh workflow run ci-docker.yml \
  --ref main \
  -f "application_commit=$APPLICATION_MERGE_COMMIT"
RUN_ID=""
for attempt in {1..30}; do
  RUN_ID="$(
    gh run list \
      --workflow ci-docker.yml \
      --event workflow_dispatch \
      --limit 20 \
      --json databaseId,displayTitle \
      --jq "map(select(.displayTitle | contains(\"application=$APPLICATION_MERGE_COMMIT\")))[0].databaseId"
  )"
  if test -n "$RUN_ID" && test "$RUN_ID" != "$BEFORE_RUN_ID"; then
    break
  fi
  RUN_ID=""
  sleep 2
done
test -n "$RUN_ID"
gh run watch "$RUN_ID" --exit-status
gh run view "$RUN_ID" --json headSha,conclusion,url
mkdir -p "/tmp/aeroassist-hosted-$RUN_ID"
gh run download "$RUN_ID" --dir "/tmp/aeroassist-hosted-$RUN_ID"
```

Stop if the run creates no jobs, provides no runner logs, or reports a workflow
planning error. Repair and re-run `actionlint`; do not reinterpret an
unstarted workflow as application-validation evidence.

The workflow validates its own definition at `github.workflow_sha`, checks out
the requested 40-character application commit independently, and fails if
`git rev-parse HEAD` differs. The safe JSON evidence records the application
commit, workflow-definition commit, run ID, checked-out application tree, and
composite result. Uploaded evidence is limited to bounded JSON summaries; raw
logs, environment files, credentials, and database artifacts are excluded.

## Required Result

- The registered, selected, executed, and passed totals all equal the exact
  application's packaged canonical inventory; this candidate's baseline is
  171 with zero unresolved scripts.
- Chromium: 51 checks passed.
- Exact source/inventory, production Docker, authenticated MongoDB,
  backup/checksum, restore rehearsal, protected diagnostics, and workflow
  definition jobs all succeed.
- No tracked or untracked generated artifact remains.
- No release criterion relies only on source inspection when an executed
  validator exists.
