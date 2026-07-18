#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from models import PilotReleaseProductionEvidence, PilotReleaseSignOff
from services.final_stabilization_pilot_release_gate_service import (
    RELEASE_DIMENSIONS,
    RELEASE_PHASE,
    FinalStabilizationPilotReleaseGateService,
    release_gate_readiness_metadata,
)


REQUIRED_DIMENSIONS = {
    "source_integrity",
    "build_integrity",
    "regression_integrity",
    "ci_integrity",
    "authentication_security",
    "http_security",
    "mongodb_authentication",
    "backup_verification",
    "off_host_backup",
    "restore_rehearsal",
    "tenant_isolation",
    "persistence_scalability",
    "query_governance",
    "observability",
    "public_readiness_safety",
    "internal_diagnostics_protection",
    "frontend_build",
    "docker_build",
    "production_configuration",
    "production_deployment_alignment",
    "deployment_rollback",
    "documentation_completeness",
    "pilot_data_safety",
    "operator_readiness",
}
PUBLIC_READINESS_FIELDS = {
    "repository_gate_available",
    "assessment_status",
    "required_dimension_count",
    "passed_dimension_count",
    "warning_dimension_count",
    "blocked_dimension_count",
    "not_verified_dimension_count",
    "production_evidence_supplied",
    "production_deployment_verified",
    "pilot_release_ready",
    "release_assessment_available",
    "environment_aware_evidence",
    "hard_blocker_governance",
    "warning_governance",
    "production_attestation_support",
    "machine_attested_evidence_distinction",
    "immutable_assessment_snapshots",
    "human_sign_off_required",
    "full_regression_orchestration",
    "synthetic_pilot_fixture_policy",
    "no_automatic_deployment",
    "no_automatic_migration",
    "no_provider_execution",
    "readiness_required",
}


def forbidden_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden = {"system", "popen", "run", "Popen", "urlopen"}
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            name = function.id if isinstance(function, ast.Name) else function.attr if isinstance(function, ast.Attribute) else ""
            if name in forbidden:
                found.append(f"{name}@{node.lineno}")
    return found


def full_synthetic_evidence() -> PilotReleaseProductionEvidence:
    return PilotReleaseProductionEvidence(
        production_git_commit="abcdef12",
        production_phase=RELEASE_PHASE,
        mongodb_authentication_verified=True,
        backup_manifest_verified=True,
        off_host_copy_verified=True,
        restore_rehearsal_verified=True,
        public_health_verified=True,
        public_readiness_verified=True,
        internal_diagnostics_verified=True,
        github_actions_verified=True,
        complete_regression_verified=True,
        tenant_isolation_verified=True,
        frontend_build_verified=True,
        docker_build_verified=True,
        production_configuration_verified=True,
        rollback_procedure_verified=True,
        operator_credentials_verified=True,
        synthetic_pilot_fixture_verified=True,
        dependency_risk_triaged=True,
        frontend_chunk_risk_acknowledged=True,
        telemetry_limit_acknowledged=True,
        rpo_rto_risk_acknowledged=True,
        verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        verified_by_role="platform_owner",
        evidence_references=("CI_FIXTURE_RELEASE_EVIDENCE",),
    )


def validate_release_gate() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    if CURRENT_BUILD_PHASE != RELEASE_PHASE:
        errors.append(f"Current phase {CURRENT_BUILD_PHASE!r} does not match {RELEASE_PHASE!r}.")

    dimension_keys = {item.key for item in RELEASE_DIMENSIONS}
    missing = sorted(REQUIRED_DIMENSIONS - dimension_keys)
    if missing:
        errors.append("Release dimensions are missing: " + ", ".join(missing))
    if len(dimension_keys) != len(RELEASE_DIMENSIONS):
        errors.append("Release dimension keys must be unique.")

    service = FinalStabilizationPilotReleaseGateService()
    generated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    default_assessment = service.build_assessment(generated_at=generated_at)
    if default_assessment.assessment_status != "blocked" or default_assessment.pilot_release_ready:
        errors.append("Missing production evidence must produce a blocked, not-ready assessment.")
    if not {"mongodb_authentication", "off_host_backup", "regression_integrity"}.issubset(
        default_assessment.blocking_items
    ):
        errors.append("Critical production and regression blockers are not preserved.")

    machine_evidence = {item.machine_key: True for item in RELEASE_DIMENSIONS if item.machine_key}
    ready_assessment = service.build_assessment(
        environment_scope="production",
        machine_evidence=machine_evidence,
        production_evidence=full_synthetic_evidence(),
        git_commit="abcdef12",
        generated_at=generated_at,
    )
    if ready_assessment.assessment_status != "ready" or ready_assessment.blocking_items:
        errors.append("Complete explicit evidence did not produce a blocker-free ready assessment.")
    repeated = service.build_assessment(
        environment_scope="production",
        machine_evidence=machine_evidence,
        production_evidence=full_synthetic_evidence(),
        git_commit="abcdef12",
        generated_at=generated_at,
    )
    if repeated.assessment_hash != ready_assessment.assessment_hash:
        errors.append("Assessment hashing is not deterministic for an identical immutable snapshot.")

    try:
        PilotReleaseProductionEvidence.model_validate(
            {
                **full_synthetic_evidence().model_dump(mode="json"),
                "password": "must-not-be-accepted",
            }
        )
        errors.append("Credential fields are accepted by the production evidence schema.")
    except ValueError:
        pass

    try:
        PilotReleaseSignOff(
            release_id="PILOT_TEST_RELEASE",
            target_phase=RELEASE_PHASE,
            decision="approved",
            decision_reason="Synthetic validation only.",
            approved_by_role="platform_owner",
            approved_at=generated_at,
            assessment_hash=ready_assessment.assessment_hash,
            human_approved=False,
        )
        errors.append("Release sign-off can be created without explicit human approval.")
    except ValueError:
        pass

    service_path = BACKEND / "services" / "final_stabilization_pilot_release_gate_service.py"
    router_path = BACKEND / "routers" / "platform_final_stabilization_pilot_release_gate.py"
    if forbidden_calls(service_path):
        errors.append("Release-gate API service contains shell, network, or provider execution calls.")
    router_text = router_path.read_text(encoding="utf-8")
    if "require_platform_role" not in router_text or "/api/platform/diagnostics/pilot-release-gate" not in router_text:
        errors.append("Protected Platform diagnostics route is missing existing role authorization.")
    if any(token in router_text for token in ("@router.put", "@router.patch", "@router.delete")):
        errors.append("Immutable release snapshots expose a mutation route.")

    public_metadata = release_gate_readiness_metadata()
    if set(public_metadata) != PUBLIC_READINESS_FIELDS:
        errors.append("Public release readiness projection contains missing or unapproved fields.")
    if public_metadata.get("production_evidence_supplied") or public_metadata.get("production_deployment_verified"):
        errors.append("Public readiness synthesized production evidence.")
    if public_metadata.get("pilot_release_ready"):
        errors.append("CI/repository metadata marked the production pilot release ready.")

    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    if '"final_stabilization_pilot_release_gate"' not in server_text:
        errors.append("Server readiness does not register the release gate.")

    workflow_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((ROOT / ".github" / "workflows").glob("ci-*.yml"))
    )
    for token in (
        "validate_final_stabilization_pilot_release_gate.py",
        "smoke_final_stabilization_pilot_release_gate.py",
        "assess_pilot_release_readiness.py",
        "run_pilot_release_validation.py",
    ):
        if token not in workflow_text:
            errors.append(f"CI does not register {token}.")
    if "contents: write" in workflow_text or any(
        token in workflow_text
        for token in ("appleboy/", "docker push", "git push", "deploy/hostinger/scripts/deploy.sh")
    ):
        errors.append("CI release-gate validation contains write permission or deployment behavior.")

    summary = {
        "release_dimensions": len(RELEASE_DIMENSIONS),
        "required_dimensions": sum(1 for item in RELEASE_DIMENSIONS if item.required_for_pilot),
        "public_readiness_fields": len(PUBLIC_READINESS_FIELDS),
    }
    return errors, summary


def main() -> int:
    errors, summary = validate_release_gate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Final stabilization pilot release-gate validation passed: " + json.dumps(summary, sort_keys=True))
    print("Static validation does not verify GitHub-hosted CI, production migration, or deployment state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
