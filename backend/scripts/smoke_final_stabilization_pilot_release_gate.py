#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE, phase_is_exact
from models import PilotReleaseProductionEvidence, PilotReleaseSignOff
from services.final_stabilization_pilot_release_gate_service import (
    PILOT_FIXTURE_PREFIXES,
    RELEASE_DIMENSIONS,
    RELEASE_PHASE,
    FinalStabilizationPilotReleaseGateService,
    release_gate_readiness_metadata,
    validate_pilot_fixture_reference,
)


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
SENSITIVE_KEYS = {
    "password",
    "token",
    "authorization",
    "cookie",
    "secret",
    "mongodb_uri",
    "passport",
    "medical",
    "payment",
}


def request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | str]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE_URL + path,
        method=method,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read().decode("utf-8")
        try:
            payload: dict[str, Any] | str = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        return response.status, payload


def synthetic_evidence(**overrides: Any) -> PilotReleaseProductionEvidence:
    values: dict[str, Any] = {
        "production_git_commit": "abcdef12",
        "production_phase": RELEASE_PHASE,
        "mongodb_authentication_verified": True,
        "backup_manifest_verified": True,
        "off_host_copy_verified": True,
        "restore_rehearsal_verified": True,
        "public_health_verified": True,
        "public_readiness_verified": True,
        "internal_diagnostics_verified": True,
        "github_actions_verified": True,
        "complete_regression_verified": True,
        "tenant_isolation_verified": True,
        "frontend_build_verified": True,
        "docker_build_verified": True,
        "production_configuration_verified": True,
        "rollback_procedure_verified": True,
        "operator_credentials_verified": True,
        "synthetic_pilot_fixture_verified": True,
        "dependency_risk_triaged": True,
        "frontend_chunk_risk_acknowledged": True,
        "telemetry_limit_acknowledged": True,
        "rpo_rto_risk_acknowledged": True,
        "verified_at": "2026-01-01T00:00:00Z",
        "verified_by_role": "platform_owner",
        "evidence_references": ["CI_FIXTURE_RELEASE_EVIDENCE"],
    }
    values.update(overrides)
    return PilotReleaseProductionEvidence.model_validate(values)


def all_machine_evidence(value: bool = True) -> dict[str, bool]:
    return {
        definition.machine_key: value
        for definition in RELEASE_DIMENSIONS
        if definition.machine_key is not None
    }


def contains_sensitive_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            any(fragment in str(key).lower() for fragment in SENSITIVE_KEYS)
            or contains_sensitive_key(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(contains_sensitive_key(item) for item in value)
    return False


def verify_assessment_model() -> None:
    service = FinalStabilizationPilotReleaseGateService()
    fixed_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    default = service.build_assessment(generated_at=fixed_time)
    dimension_keys = {item.key for item in default.dimensions}
    required = {item.key for item in RELEASE_DIMENSIONS if item.required_for_pilot}
    if not required.issubset(dimension_keys) or len(dimension_keys) < 24:
        raise AssertionError("Release dimensions are incomplete.")
    if default.assessment_status != "blocked" or default.pilot_release_ready:
        raise AssertionError("Missing production evidence did not block pilot readiness.")
    for critical in ("mongodb_authentication", "off_host_backup", "regression_integrity"):
        if critical not in default.blocking_items:
            raise AssertionError(f"Critical blocker was lost: {critical}")

    warning_evidence = synthetic_evidence(dependency_risk_triaged=False)
    warning_only = service.build_assessment(
        environment_scope="production",
        machine_evidence=all_machine_evidence(),
        production_evidence=warning_evidence,
        git_commit="abcdef12",
        generated_at=fixed_time,
    )
    if warning_only.assessment_status != "conditional" or warning_only.blocking_items:
        raise AssertionError("A warning-only assessment became blocked.")

    blocked = service.build_assessment(
        environment_scope="production",
        machine_evidence=all_machine_evidence(),
        production_evidence=synthetic_evidence(mongodb_authentication_verified=False),
        git_commit="abcdef12",
        generated_at=fixed_time,
    )
    if blocked.assessment_status != "blocked" or "mongodb_authentication" not in blocked.blocking_items:
        raise AssertionError("Blocked status did not take precedence over otherwise complete evidence.")

    ready = service.build_assessment(
        environment_scope="production",
        machine_evidence=all_machine_evidence(),
        production_evidence=synthetic_evidence(),
        git_commit="abcdef12",
        generated_at=fixed_time,
    )
    repeated = service.build_assessment(
        environment_scope="production",
        machine_evidence=all_machine_evidence(),
        production_evidence=synthetic_evidence(),
        git_commit="abcdef12",
        generated_at=fixed_time,
    )
    if ready.assessment_status != "ready" or not ready.pilot_release_ready:
        raise AssertionError("Complete explicit evidence did not produce a ready recommendation.")
    if ready.assessment_hash != repeated.assessment_hash or not ready.immutable:
        raise AssertionError("Assessment snapshots are not deterministic and immutable.")
    verification_types = {item.verification_type for item in ready.evidence}
    if not {"machine_verified", "operator_attested"}.issubset(verification_types):
        raise AssertionError("Machine-verified and attested evidence were not kept distinct.")
    if not ready.human_sign_off_required or not ready.automatic_approval_disabled:
        raise AssertionError("A ready recommendation bypasses human sign-off.")
    if not ready.automatic_deployment_disabled or not ready.automatic_migration_disabled:
        raise AssertionError("Release assessment enables deployment or migration.")


def verify_evidence_and_sign_off_validation() -> None:
    base = synthetic_evidence().model_dump(mode="json")
    try:
        PilotReleaseProductionEvidence.model_validate({**base, "password": "forbidden"})
        raise AssertionError("Credential fields were accepted in operator evidence.")
    except ValueError:
        pass
    try:
        PilotReleaseProductionEvidence.model_validate(
            {**base, "evidence_references": ["x" * 201]}
        )
        raise AssertionError("Oversized evidence metadata was accepted.")
    except ValueError:
        pass
    if not all(validate_pilot_fixture_reference(prefix + "CASE") for prefix in PILOT_FIXTURE_PREFIXES):
        raise AssertionError("Reserved synthetic pilot fixture prefixes are not accepted.")
    if validate_pilot_fixture_reference("REAL_PASSENGER_CASE"):
        raise AssertionError("An ungoverned pilot fixture reference was accepted.")

    assessment = FinalStabilizationPilotReleaseGateService().build_assessment(
        environment_scope="production",
        machine_evidence=all_machine_evidence(),
        production_evidence=synthetic_evidence(),
        git_commit="abcdef12",
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    try:
        PilotReleaseSignOff(
            release_id="PILOT_TEST_RELEASE",
            target_phase=RELEASE_PHASE,
            decision="approved",
            decision_reason="Synthetic test.",
            approved_by_role="platform_owner",
            approved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            assessment_hash=assessment.assessment_hash,
            human_approved=False,
        )
        raise AssertionError("Automatic sign-off was accepted.")
    except ValueError:
        pass


def verify_cli() -> None:
    with tempfile.TemporaryDirectory(prefix="pilot-release-smoke-") as directory:
        root = Path(directory)
        report = root / "blocked-report.json"
        blocked = subprocess.run(
            [
                sys.executable,
                str(BACKEND / "scripts" / "assess_pilot_release_readiness.py"),
                "--output",
                str(report),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if blocked.returncode != 1 or "AeroAssist Pilot Release Assessment" not in blocked.stdout:
            raise AssertionError("Blocked CLI result did not use a non-zero exit and human summary.")
        payload = json.loads(report.read_text(encoding="utf-8"))
        if payload.get("assessment_status") != "blocked" or contains_sensitive_key(payload):
            raise AssertionError("CLI report is not blocked and sanitized.")

        evidence_path = root / "synthetic-evidence.json"
        evidence_path.write_text(
            json.dumps(synthetic_evidence().model_dump(mode="json")),
            encoding="utf-8",
        )
        supplied_report = root / "supplied-report.json"
        supplied = subprocess.run(
            [
                sys.executable,
                str(BACKEND / "scripts" / "assess_pilot_release_readiness.py"),
                "--production-evidence",
                str(evidence_path),
                "--output",
                str(supplied_report),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if supplied.returncode not in {0, 1}:
            raise AssertionError(f"Valid synthetic evidence was rejected: {supplied.stderr}")
        supplied_payload = json.loads(supplied_report.read_text(encoding="utf-8"))
        if supplied_payload.get("production_evidence_supplied") is not True:
            raise AssertionError("CLI did not distinguish supplied attestation metadata.")

        invalid_path = root / "invalid-evidence.json"
        invalid_path.write_text(json.dumps({"password": "must-not-echo"}), encoding="utf-8")
        invalid = subprocess.run(
            [
                sys.executable,
                str(BACKEND / "scripts" / "assess_pilot_release_readiness.py"),
                "--production-evidence",
                str(invalid_path),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if invalid.returncode != 2 or "must-not-echo" in invalid.stdout + invalid.stderr:
            raise AssertionError("Invalid evidence was not safely rejected.")


def verify_static_registration() -> None:
    if not phase_is_exact(CURRENT_BUILD_PHASE, RELEASE_PHASE):
        raise AssertionError(f"Canonical Phase 56.5.8 marker mismatch: {CURRENT_BUILD_PHASE}")
    readiness = release_gate_readiness_metadata()
    if readiness.get("pilot_release_ready") is not False:
        raise AssertionError("Public readiness marked the pilot ready without production evidence.")
    if readiness.get("production_evidence_supplied") is not False:
        raise AssertionError("Public readiness synthesized operator evidence.")
    if not readiness.get("no_automatic_deployment") or not readiness.get("no_automatic_migration"):
        raise AssertionError("Readiness does not prohibit deployment and migration automation.")

    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    router_text = (
        BACKEND / "routers" / "platform_final_stabilization_pilot_release_gate.py"
    ).read_text(encoding="utf-8")
    inventory_text = (BACKEND / "scripts" / "smoke_inventory.json").read_text(encoding="utf-8")
    if '"final_stabilization_pilot_release_gate"' not in server_text:
        raise AssertionError("Release-gate readiness registration is missing.")
    if "require_platform_role" not in router_text or "@router.put" in router_text or "@router.delete" in router_text:
        raise AssertionError("Protected immutable release diagnostics routing is incomplete.")
    if "smoke_final_stabilization_pilot_release_gate.py" not in inventory_text:
        raise AssertionError("Release-gate smoke is absent from the canonical inventory.")
    for path in (
        ROOT / "docs" / "architecture" / "final-stabilization-pilot-release-gate.md",
        ROOT / "deploy" / "hostinger" / "PILOT_RELEASE_RUNBOOK.md",
    ):
        if not path.is_file():
            raise AssertionError(f"Required release documentation is missing: {path.name}")


def verify_live_contracts() -> None:
    health_status, health = request("GET", "/api/health")
    if health_status != 200 or not isinstance(health, dict) or health.get("phase") != RELEASE_PHASE:
        raise AssertionError(f"Health does not report Phase 56.5.8: {health}")

    readiness_status, readiness = request("GET", "/api/readiness")
    if readiness_status != 200 or not isinstance(readiness, dict):
        raise AssertionError(f"Public readiness failed: {readiness}")
    section = readiness.get("final_stabilization_pilot_release_gate") or {}
    allowed = set(release_gate_readiness_metadata())
    if set(section) != allowed or section.get("pilot_release_ready") is not False:
        raise AssertionError(f"Public release-gate projection is unsafe or incomplete: {section}")
    if any(key in section for key in ("dimensions", "evidence", "filesystem_paths", "backup_filenames")):
        raise AssertionError("Public readiness exposed protected release evidence.")

    denied_status, _ = request(
        "GET",
        "/api/platform/diagnostics/pilot-release-gate",
        headers={"Authorization": "Bearer release-gate-invalid-token"},
    )
    if denied_status != 401:
        raise AssertionError("Protected release diagnostics accepted invalid authorization.")
    authorized_status, authorized = request(
        "GET",
        "/api/platform/diagnostics/pilot-release-gate",
        headers={"X-Demo-User-Email": "owner@aeroassist.dev"},
    )
    if authorized_status != 200 or not isinstance(authorized, dict):
        raise AssertionError(f"Authorized release diagnostics failed: {authorized}")
    assessment = authorized.get("assessment") or {}
    if not assessment.get("dimensions") or assessment.get("production_evidence_supplied") is not False:
        raise AssertionError("Protected release diagnostics do not preserve environment-aware evidence.")

    schema_status, schema = request(
        "GET",
        "/api/platform/diagnostics/pilot-release-gate/sign-off-schema",
        headers={"X-Demo-User-Email": "owner@aeroassist.dev"},
    )
    if schema_status != 200 or not isinstance(schema, dict) or schema.get("automatic_approval_disabled") is not True:
        raise AssertionError("Protected sign-off schema does not preserve human authority.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    verify_static_registration()
    verify_assessment_model()
    verify_evidence_and_sign_off_validation()
    verify_cli()
    if not args.static:
        verify_live_contracts()
    print("Phase 56.5.8 final stabilization and pilot release-gate smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
