# Phase 57 Evidence Plan

Phase 57 remains the only production release gate. This plan prepares evidence
requirements for the future Product Recovery application merge commit; it does
not submit evidence or sign-off.

## Evidence Binding

Deployment evidence must bind:

- exact deployed application merge SHA reported by the backend;
- exact deployed phase reported by `/api/health`;
- deployment ID and timestamp;
- public backend health, frontend health, database readiness, and smoke result;
- authenticated operator identity;
- sanitized evidence references only.

The later deployment-tooling/tag commit is useful repository provenance but
must not replace the exact application SHA in deployment evidence.

## Required Reviewed Evidence

Persist real records through the existing Phase 57 APIs for:

- deployment;
- complete smoke run;
- backup verification;
- restore rehearsal;
- production validation;
- tenant-isolation validation.

The production evidence record supports:

`production_git_commit`, `production_phase`,
`mongodb_authentication_verified`, `backup_manifest_verified`,
`off_host_copy_verified`, `restore_rehearsal_verified`,
`public_health_verified`, `public_readiness_verified`,
`internal_diagnostics_verified`, `github_actions_verified`,
`complete_regression_verified`, `tenant_isolation_verified`,
`frontend_build_verified`, `docker_build_verified`,
`production_configuration_verified`, `rollback_procedure_verified`,
`operator_credentials_verified`, `synthetic_pilot_fixture_verified`,
`dependency_risk_triaged`, `frontend_chunk_risk_acknowledged`,
`telemetry_limit_acknowledged`, `rpo_rto_risk_acknowledged`, and bounded
`evidence_references`.

Leave unverified booleans `null`. In particular, never set
`off_host_copy_verified` or `restore_rehearsal_verified` without independent
evidence.

## Guided Existing Workflow

Prepare an operator-owned JSON file from
`deploy/hostinger/phase57-attestation.example.json`, using only IDs returned
when real evidence records are persisted. Then run:

```bash
python3 deploy/hostinger/scripts/phase57_pilot_release_attestation.py \
  --base-url "$APP_BASE_URL" \
  --email "$PLATFORM_OWNER_EMAIL" \
  --evidence-file "$ATTESTATION_INPUT" \
  --output-dir "$ATTESTATION_OUTPUT"
```

The password is prompted without echo. The utility authenticates as Platform
Owner, loads current state, records supplied evidence through canonical APIs,
submits the canonical assessment, prompts only for the human decision, verifies
persistence, and exports JSON and Markdown reports.

## Human Sign-Off

An existing `platform_owner` or `platform_admin` supplies:

- immutable assessment snapshot ID;
- assessment hash;
- release ID;
- rollback commit/reference;
- operator name or ID;
- decision: `approved`, `approved_with_conditions`, or `rejected`;
- decision timestamp;
- optional conditions, rationale, and notes.

A blocked assessment cannot be approved. There is no automatic approval,
deployment, backup, restore, migration, pilot activation, or evidence
fabrication path.

## Expected Gate

`pilot_release_ready` may become true only after all required dimensions are
verified, no blocking dimension remains, deployment/backup/tenant evidence is
verified, a rollback reference exists, and an authorized human approval is
persisted. Until then, blocked or not-verified readiness is correct.
