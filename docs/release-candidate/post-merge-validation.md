# Post-Merge Validation

Run this gate on the exact unmodified `APPLICATION_MERGE_COMMIT`. A later
deployment-tooling commit does not replace application validation evidence.

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

## Required Result

- 171 registered, 171 selected, 171 executed, 171 passed.
- Chromium: 51 checks passed.
- No tracked or untracked generated artifact remains.
- No release criterion relies only on source inspection when an executed
  validator exists.
