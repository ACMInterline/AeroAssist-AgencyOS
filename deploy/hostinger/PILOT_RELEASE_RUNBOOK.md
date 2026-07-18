# Controlled Pilot Release Runbook

This runbook governs the manual transition from the completed repository foundation to a controlled AeroAssist pilot. It does not authorize automatic deployment, MongoDB migration, restore, data seeding, or provider activity.

Production may remain pinned to Phase 56.5.4 until the existing-volume MongoDB authentication migration is completed. Repository, CI, disposable, migration, and production evidence must be recorded separately.

## Safety Labels

- **READ-ONLY:** may inspect repository or production state without mutation.
- **DISPOSABLE:** may mutate only isolated synthetic test resources.
- **PRODUCTION-MUTATING:** requires an approved maintenance window, current verified backups, explicit operator authorization, and rollback readiness. These steps are never run by CI or application startup.

Never place credentials, connection URIs, backup contents, passenger data, or private host details in release evidence JSON.

## 1. Repository Validation

**READ-ONLY**

1. Confirm the approved commit and a clean worktree.
2. Run the final release validator and quick orchestrator.
3. Run the complete smoke inventory with governed isolation.
4. Build the frontend and production images.
5. Retain sanitized stage summaries and the blocked default assessment.

The default assessment must remain blocked without production evidence.

## 2. GitHub Actions Verification

**READ-ONLY**

Verify Fast Validation, Focused Smoke Validation, Production Docker Validation, and Full Smoke Regression for the exact candidate commit. Workflow files are not evidence that hosted execution passed. Record only workflow names, commit, outcome, and verification time.

## 3. Production Backup

**PRODUCTION-MUTATING**

During an approved maintenance preparation window, create the documented MongoDB and document-export backup. Verify checksum and manifest metadata. Do not continue with an unverified archive.

## 4. Off-Host Backup Copy

**PRODUCTION-MUTATING**

Copy the complete verified backup set to protected storage outside the VPS. Verify the copy independently and record a non-sensitive evidence reference.

## 5. MongoDB Authentication Migration

**PRODUCTION-MUTATING**

Follow `MONGODB_DISASTER_RECOVERY_RUNBOOK.md` exactly. Stop application writes, create distinct administrator and application identities, validate both, enable authenticated startup, and preserve the existing volume. Do not automate this step and do not delete or recreate the volume.

## 6. Phase 56.5.5 Deployment and Validation

**PRODUCTION-MUTATING**

Deploy the approved Phase 56.5.5 checkpoint only after authentication migration readiness. Verify authenticated backend connectivity, public health, safe readiness, and a fresh authenticated backup before advancing.

## 7. Phase 56.5.6 Deployment and Validation

**PRODUCTION-MUTATING**

Deploy the approved persistence checkpoint. Verify additive indexes, bounded tenant queries, readiness timeout behavior, and tenant isolation. Never drop or rebuild production indexes as part of this gate.

## 8. Phase 56.5.7 Deployment and Validation

**PRODUCTION-MUTATING**

Deploy the approved observability checkpoint. Verify JSON events, request correlation, redaction, public readiness privacy, protected diagnostics authorization, and bounded Docker logs. Do not export raw logs into release evidence.

## 9. Phase 56.5.8 Deployment

**PRODUCTION-MUTATING**

Deploy the final gate only after prior checkpoints pass. Record the deployed commit and exact phase. Phase 56.5.8 does not itself execute or approve deployment.

## 9A. Phase 57.0 Pilot Operations Evidence

**PRODUCTION-MUTATING only when an authorized operator explicitly records metadata**

Deploy the approved Phase 57.0 source, then use `/platform/pilot-operations` to record bounded deployment, smoke, backup, restore, and production-validation evidence. Pilot agency enrollment and synthetic fixture actions require Platform Owner authority. Record release assessment and sign-off only after independent evidence review. The console does not deploy, approve, migrate, back up, restore, send invitations, or activate features automatically.

## 10. Tenant-Isolation Verification

**DISPOSABLE** or carefully scoped **READ-ONLY** production verification

Use synthetic tenant records with `PILOT_TEST_`, `DEMO_SYNTHETIC_`, or `CI_FIXTURE_` references. Confirm Platform and Agency boundaries and remove disposable fixtures. Never use real passenger identity, passport, medical, or payment data.

## 11. Public Health and Readiness

**READ-ONLY**

Verify the public frontend, `/api/health`, and `/api/readiness`. Confirm the exact deployed phase and that public readiness contains no protected counters, timings, evidence details, filesystem paths, backup names, or tenant data.

## 12. Protected Diagnostics

**READ-ONLY**

Confirm anonymous and invalid requests are denied. Confirm an existing authorized Platform operator can read bounded observability and pilot-release diagnostics. Do not capture raw credentials or operational records.

## 13. Authenticated Backup

**PRODUCTION-MUTATING**

Create and verify a new backup after authenticated operation is stable. Preserve its sanitized manifest reference and off-host copy evidence.

## 14. Restore Rehearsal

**DISPOSABLE**

Use the guarded test restore script against isolated resources and a non-production target database. Verify collection/document counts. Production restore remains disabled and requires its separate multi-part confirmation process.

## 15. Rollback

**PRODUCTION-MUTATING**

Before release, identify the previous verified commit, database compatibility state, configuration rollback, traffic-control procedure, and responsible operator roles. Roll back application code only when data compatibility is confirmed. Never delete the production volume as a rollback shortcut.

## 16. Pilot User Creation

**PRODUCTION-MUTATING**

Use existing owner bootstrap, agency onboarding, and invitation mechanisms only. Create the minimum authorized pilot users. Do not enable demo authentication, startup seeding, or seed endpoints.

## 17. Synthetic Pilot Case

**PRODUCTION-MUTATING** only after explicit approval

Create one removable, tenant-scoped synthetic case with a reserved prefix. Use invented contact and travel metadata, no real passport or medical values, no provider credentials, and no live booking, ticketing, payment, or airline action.

## 18. Release Decision and Sign-Off

**READ-ONLY decision recording**

Generate the final assessment from reviewed metadata. Confirm every required dimension is passed, review all warnings, and bind the decision to the assessment hash and rollback reference. An existing `platform_owner` or `platform_admin` records `approved`, `approved_with_conditions`, or `rejected`. The system never approves itself.

## Post-Pilot Review

Review incidents, workload, tenant boundaries, readiness warnings, dependency findings, frontend performance, backup verification, restore evidence, and operator feedback. Corrections create a superseding assessment or sign-off record; historical evidence is never edited.
