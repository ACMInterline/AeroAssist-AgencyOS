# Product Recovery Release Candidate

This directory is the controlled handoff package for Product Recovery 12. It
does not approve a release, change the active phase, update the deployment pin,
run a migration, or replace the Phase 57 production release gate.

## Reviewed Baseline

- Branch: `phase-59-product-experience-recovery`
- Implementation baseline reviewed before these documents:
  `a0bdc4a99b3bbb884f2fe190d88eb8e06617294d`
- Merge base: `8fbb5dc7ed3a147f0b1824c014964ca74331c6a3`
- Active marker: `phase_59_0_product_experience_recovery`
- Registered smoke scripts: 171

The final application release commit does not exist until the reviewed branch
is committed, pushed, merged into `main` with `--no-ff`, and validated. Never
substitute the branch name or this implementation baseline for that merge SHA.

## Artifact Map

| Artifact | Purpose |
|---|---|
| [Release Candidate Assessment](release-candidate-assessment.md) | Evidence and decision record |
| [Merge Checklist](merge-checklist.md) | Fail-closed branch and merge procedure |
| [Post-Merge Validation](post-merge-validation.md) | Validation on the exact merge commit |
| [Deployment Plan](deployment-plan.md) | Controlled Hostinger preparation and deployment |
| [Rollback Plan](rollback-plan.md) | Application rollback and separately authorized restore |
| [Migration Readiness](migration-readiness-summary.md) | Dry-run analyzer evidence and future controls |
| [Phase 57 Evidence Plan](phase57-evidence-plan.md) | Existing release-gate evidence and sign-off |
| [Known Limitations](known-limitations.md) | Accepted warnings and remaining gates |

## Authority Boundary

These artifacts prepare an operator decision. The persisted Phase 57
assessment and authorized human sign-off remain authoritative for production.
No item in this directory is itself deployment approval.
