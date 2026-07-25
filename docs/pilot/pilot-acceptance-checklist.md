# Commercial Pilot Acceptance Checklist

## Product Understanding

- [ ] Agency staff understand the Client-to-after-sales operating path.
- [ ] Roles, permissions, tenant boundaries, and manual-review states are understood.
- [ ] Unsupported provider/payment/ticketing/messaging/automation behavior is understood.

## Operating Evidence

- [ ] Onboarding or explicit legacy-agency compatibility is verified.
- [ ] A synthetic demo profile is available for guided exercises where required.
- [ ] Operations, Requests, Offers, Booking, Passengers, Documents, and Tasks provide usable guidance and recovery states.
- [ ] One complete synthetic operating path has been reviewed.
- [ ] One validation failure, one warning/manual-review condition, and one safe retry have been reviewed.
- [ ] Tenant isolation and permission controls have been reviewed.
- [ ] Feedback submission and Platform review have been tested.

## Readiness and Governance

- [ ] Commercial Pilot readiness has no unresolved critical blocker.
- [ ] Warnings have an owner and documented condition.
- [ ] Phase 57 production evidence, backup evidence, rollback reference, tenant-isolation evidence, assessment snapshot, and human sign-off remain valid.
- [ ] Backup/recovery and incident procedures are understood.

## Human Decision

Record the accepting Agency Administrator, Platform authority, date, assessed release, conditions, unresolved warnings, and decision outside this checklist using the existing governed evidence/sign-off workflow. This document does not approve the pilot automatically.

## Product Recovery 11B Stabilization Evidence

- [ ] The 51-check disposable browser acceptance suite passes.
- [ ] The complete registered smoke inventory passes with zero unresolved scripts.
- [ ] Backend compile, frontend production build, dependency audit, persistence governance, canonical ownership, tenant isolation, and migration dry-run checks pass.
- [ ] Generated Python caches, Playwright artifacts, disposable Document storage, and `frontend/dist` are removed.
- [ ] Open accessibility, cross-browser, compatibility, and load-test warnings in the Release-Candidate Gap Register are accepted by the human reviewer.

Product Recovery 11B evidence supplements this checklist. Phase 57 remains the
authoritative production evidence and human sign-off gate.

## Product Recovery 12 Release Evidence

- [ ] The exact application merge SHA passed post-merge validation.
- [ ] The separate deployment-tooling pin names that exact application SHA.
- [ ] Hosted CI passed for the exact reviewed commits.
- [ ] Verified backup, independent off-host copy, and disposable restore
  rehearsal evidence exists.
- [ ] Production health, safe readiness, protected diagnostics, tenant
  isolation, onboarding/Operations routing, and Commercial Pilot readiness
  passed.
- [ ] Phase 57 evidence IDs are persisted and the authorized human decision is
  bound to the immutable assessment hash and rollback reference.

See the [Product Recovery Release Candidate package](../release-candidate/README.md).
These checklist items do not approve or execute deployment.
