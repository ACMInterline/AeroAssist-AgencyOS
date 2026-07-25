# Product Recovery Merge Checklist

These commands are preparation only. Run them after human review of the
uncommitted release-candidate artifacts.

## 1. Commit And Push The Reviewed Feature Branch

```bash
set -Eeuo pipefail
git switch phase-59-product-experience-recovery
git fetch --prune origin
test "$(git rev-list --left-right --count HEAD...origin/phase-59-product-experience-recovery)" = $'0\t0'
git status --short
python3 backend/scripts/run_pilot_release_validation.py \
  --profile full \
  --include-docker-config \
  --output /tmp/aeroassist-product-recovery-final.json
git --no-pager diff --check
git add \
  README.md \
  BUILD_PHASES.md \
  docs/release-candidate \
  docs/product/aeroassist-product-standards.md \
  docs/architecture/canonical-domain-ownership-map.md \
  docs/architecture/canonical-domain-migration-register.md \
  docs/architecture/current-model-inventory.md \
  docs/architecture/canonical-route-policy.md \
  docs/stabilization/full-system-stabilization-report.md \
  docs/stabilization/frontend-performance-report.md \
  docs/stabilization/release-candidate-gap-register.md \
  docs/pilot/pilot-acceptance-checklist.md
git diff --cached --check
git diff --cached --name-only
git commit -m "Complete Product Recovery release candidate review"
FEATURE_COMMIT="$(git rev-parse HEAD)"
test -z "$(git status --porcelain)"
git push origin phase-59-product-experience-recovery
test "$(git rev-parse origin/phase-59-product-experience-recovery)" = "$FEATURE_COMMIT"
```

Stop if the staged file list contains anything outside the reviewed scope.

## 2. Merge With An Explicit Merge Commit

```bash
set -Eeuo pipefail
git switch main
git fetch --prune origin
git pull --ff-only origin main
test -z "$(git status --porcelain)"
MAIN_BEFORE="$(git rev-parse HEAD)"
git merge --no-ff origin/phase-59-product-experience-recovery \
  -m "Merge Product Recovery release candidate"
APPLICATION_MERGE_COMMIT="$(git rev-parse HEAD)"
test "$(git rev-parse "${APPLICATION_MERGE_COMMIT}^1")" = "$MAIN_BEFORE"
test "$(git rev-parse "${APPLICATION_MERGE_COMMIT}^2")" = "$FEATURE_COMMIT"
```

Do not push `main` until the exact merge commit passes
[Post-Merge Validation](post-merge-validation.md).

## 3. Push The Validated Merge

```bash
git push origin main
git fetch origin main
test "$(git rev-parse origin/main)" = "$APPLICATION_MERGE_COMMIT"
```

## 4. Update The Deployment Pin Separately

After the merge SHA is known and validated, edit only
`RELEASE_COMMIT` and its matching eight-character `RELEASE_SHORT` in
`deploy/hostinger/scripts/deploy_v1_release_candidate.sh`.

```bash
test "${#APPLICATION_MERGE_COMMIT}" -eq 40
bash -n deploy/hostinger/scripts/deploy_v1_release_candidate.sh
rg -n 'RELEASE_(COMMIT|SHORT)=' \
  deploy/hostinger/scripts/deploy_v1_release_candidate.sh
git diff --check
git add deploy/hostinger/scripts/deploy_v1_release_candidate.sh
git diff --cached --check
git commit -m "Pin Product Recovery release candidate"
DEPLOYMENT_TOOLING_COMMIT="$(git rev-parse HEAD)"
git push origin main
```

The full pin must equal `APPLICATION_MERGE_COMMIT`; the short pin must equal
its first eight characters. Do not use a branch, tag, or guessed SHA.

## 5. Release Tag Policy

The current established policy tags the later deployment-tooling commit while
Phase 57 deployment evidence records the exact application merge commit
actually reported by the backend.

```bash
RELEASE_TAG="${RELEASE_TAG:?Set the separately approved release tag}"
test "$(git rev-parse HEAD)" = "$DEPLOYMENT_TOOLING_COMMIT"
git tag -a "$RELEASE_TAG" "$DEPLOYMENT_TOOLING_COMMIT" \
  -m "AeroAssist Product Recovery release"
git push origin "$RELEASE_TAG"
```

Do not create or push a tag without separate human approval.
