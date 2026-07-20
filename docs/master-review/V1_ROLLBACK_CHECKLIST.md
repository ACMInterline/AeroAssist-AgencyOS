# AeroAssist V1 Rollback Checklist

## Before Deployment

- [ ] Record the exact candidate commit, phase, image identifiers and deployment ID.
- [ ] Record the last verified application commit and its compatible configuration.
- [ ] Confirm the candidate uses additive persistence/index startup behavior.
- [ ] Confirm no rollback step drops, renames, rebuilds or mutates MongoDB indexes automatically.
- [ ] Create and verify an authenticated MongoDB backup and manifest.
- [ ] Create and verify the document-export backup.
- [ ] Verify checksums and an independently readable off-host copy.
- [ ] Complete a restore rehearsal against disposable, non-production resources.
- [ ] Record database compatibility for both forward and rollback application versions.
- [ ] Record the authorized operator, maintenance window and communication path.

## Rollback Triggers

- [ ] Backend or frontend health remains failed after the approved stabilization window.
- [ ] Public readiness leaks protected diagnostics or required readiness fails unexpectedly.
- [ ] Authentication or tenant isolation fails.
- [ ] MongoDB startup reports an incompatible index or persistence contract.
- [ ] Golden Path create/open/continue behavior is unavailable for the pilot tenant.
- [ ] Document storage is unavailable or non-persistent.
- [ ] Error rate, latency or resource use exceeds the approved pilot threshold.
- [ ] Release evidence does not match the running commit and phase.

## Controlled Rollback

1. Stop new pilot work and record the incident timestamp and correlation references.
2. Preserve bounded diagnostics; do not copy secrets, passenger data or raw production logs into release evidence.
3. Stop application writes using the approved traffic-control procedure.
4. Confirm whether application-only rollback is data compatible.
5. Deploy the previously verified application commit and matching configuration.
6. Do not delete or recreate MongoDB or document-storage volumes.
7. Do not restore a database merely to reverse application code.
8. If data restore is independently authorized, follow the disaster-recovery runbook with its confirmation guards.
9. Start services in dependency order and wait for MongoDB, backend and frontend health checks.
10. Verify `/api/health`, public-safe `/api/readiness`, protected diagnostics authorization and the exact running commit/phase.
11. Run the production-safe smoke set and one synthetic tenant-isolation check.
12. Verify document storage and the pilot Golden Path can open existing records without mutation.

## After Rollback

- [ ] Record outcome, operator, timestamps, previous/candidate/restored commits and sanitized evidence references.
- [ ] Confirm no synthetic fixture or temporary access remains.
- [ ] Confirm backup retention and off-host copies remain intact.
- [ ] Reconcile operational work created during the maintenance window.
- [ ] Preserve failed-release and rollback evidence; do not rewrite historical sign-offs.
- [ ] Require a new assessment and explicit human approval before another deployment.

Never use volume deletion, destructive index changes, automatic migrations, startup seeding or unreviewed restore as a rollback shortcut.
