# Backup and Recovery Guide

Backup and restore are deployment-operator responsibilities. AeroAssist Agency users cannot execute either action from the Commercial Pilot UI.

## Required Controls

- Use the existing authenticated Hostinger backup scripts and Phase 57 evidence workflow.
- Include MongoDB and persistent document-export storage.
- Verify manifests and checksums without displaying secret values.
- Prepare an off-host copy under the operator’s approved process.
- Record the exact application rollback commit.
- Rehearse restore only in a disposable isolated environment with production-safe resource limits.
- Never restore over production as part of a pilot exercise.

## Recovery Decision

1. Contain the incident and stop unsafe mutation.
2. Confirm current container, repository, database, and storage state.
3. Identify the latest verified canonical backup.
4. Obtain authorized human approval under the deployment runbook.
5. Use the documented rollback or recovery procedure.
6. Validate health, readiness, authentication, tenant isolation, persistence, and the affected workflow.
7. Record sanitized evidence in the existing Phase 57 registry.

Canonical production procedures live in `deploy/hostinger/` and the Phase 57 runbooks. This guide does not supersede them.
