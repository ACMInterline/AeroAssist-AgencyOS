#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[2]
UTILITY = ROOT / "deploy" / "hostinger" / "scripts" / "phase57_pilot_release_attestation.py"
EXAMPLE = ROOT / "deploy" / "hostinger" / "phase57-attestation.example.json"
PHASE = "phase_57_0_pilot_operations_release_readiness"
ASSESSMENT_HASH = "a" * 64
RELEASE_ID = "PILOT_RELEASE_VALIDATOR"
EVIDENCE_REFERENCE = "PILOT_RELEASE_VALIDATION_EVIDENCE"


def load_utility():
    spec = importlib.util.spec_from_file_location("phase57_attestation", UTILITY)
    if spec is None or spec.loader is None:
        raise AssertionError("Phase 57 attestation utility could not be imported.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def production_evidence() -> dict[str, Any]:
    fields = {
        "mongodb_authentication_verified",
        "backup_manifest_verified",
        "off_host_copy_verified",
        "restore_rehearsal_verified",
        "public_health_verified",
        "public_readiness_verified",
        "internal_diagnostics_verified",
        "github_actions_verified",
        "complete_regression_verified",
        "tenant_isolation_verified",
        "frontend_build_verified",
        "docker_build_verified",
        "production_configuration_verified",
        "rollback_procedure_verified",
        "operator_credentials_verified",
        "synthetic_pilot_fixture_verified",
        "dependency_risk_triaged",
        "frontend_chunk_risk_acknowledged",
        "telemetry_limit_acknowledged",
        "rpo_rto_risk_acknowledged",
    }
    return {
        "production_git_commit": "0123456789abcdef0123456789abcdef01234567",
        "production_phase": PHASE,
        **{field: True for field in fields},
        "evidence_references": [EVIDENCE_REFERENCE],
    }


def evidence_bundle() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "operational_evidence": [
            {
                "evidence_type": "production_validation",
                "status": "PASS",
                "title": "Controlled production validation",
                "summary": "Reviewed validation metadata for the isolated attestation utility test.",
                "reference": EVIDENCE_REFERENCE,
                "evidence_metadata": {"validation_scope": "isolated_fixture", "result": "PASS"},
            }
        ],
        "production_evidence": production_evidence(),
        "sign_off_context": {
            "release_id": RELEASE_ID,
            "rollback_reference": "fedcba9876543210fedcba9876543210fedcba98",
        },
    }


class GovernanceState:
    def __init__(self) -> None:
        self.evidence: list[dict[str, Any]] = []
        self.requests: list[tuple[str, str]] = []

    def assessment(self) -> dict[str, Any]:
        return {
            "assessment_id": "assessment-validator",
            "build_phase": PHASE,
            "git_commit": production_evidence()["production_git_commit"],
            "assessment_status": "ready",
            "generated_at": "2026-07-22T12:00:00Z",
            "environment_scope": "production",
            "dimensions": [
                {"key": "production_deployment", "status": "passed"},
                {"key": "backup_recovery", "status": "passed"},
            ],
            "blocking_items": [],
            "warnings": [],
            "recommended_next_action": "Authorized human release decision is required.",
            "assessment_hash": ASSESSMENT_HASH,
            "immutable": True,
            "production_evidence_supplied": True,
            "production_deployment_verified": True,
            "pilot_release_ready": True,
            "human_sign_off_required": True,
            "automatic_approval_disabled": True,
            "automatic_deployment_disabled": True,
            "automatic_migration_disabled": True,
        }

    def record(self, payload: dict[str, Any], *, evidence_type: str | None = None) -> dict[str, Any]:
        record = {
            "id": f"evidence-{len(self.evidence) + 1}",
            **payload,
            "evidence_type": evidence_type or payload["evidence_type"],
            "build_phase": PHASE,
            "recorded_by_user_id": "platform-owner-validator",
            "recorded_by_role": "platform_owner",
            "immutable": True,
            "metadata_only": True,
        }
        self.evidence.insert(0, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        sign_off = next((item for item in self.evidence if item["evidence_type"] == "pilot_sign_off"), None)
        assessment = next((item for item in self.evidence if item["evidence_type"] == "release_assessment"), None)
        return {
            "phase": PHASE,
            "overview": {
                "pilot_approval_state": (
                    sign_off["evidence_metadata"]["sign_off"]["decision"].upper()
                    if sign_off else "NOT_SIGNED_OFF"
                )
            },
            "release_assessment": (
                assessment["evidence_metadata"]["assessment"] if assessment else {
                    "assessment_status": "blocked", "blocking_items": ["production_evidence"], "warnings": []
                }
            ),
        }


def handler_for(state: GovernanceState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def body(self) -> dict[str, Any]:
            size = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(size).decode("utf-8")) if size else {}

        def respond(self, status_code: int, payload: dict[str, Any]) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def authorized(self) -> bool:
            if self.headers.get("Authorization") != "Bearer owner-token":
                self.respond(403, {"detail": "Platform authorization required."})
                return False
            return True

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            state.requests.append(("GET", parsed.path))
            if parsed.path == "/api/health":
                self.respond(200, {"ok": True, "phase": PHASE})
                return
            if not self.authorized():
                return
            if parsed.path == "/api/platform/pilot-operations":
                self.respond(200, state.dashboard())
                return
            if parsed.path == "/api/platform/pilot-operations/evidence":
                requested_type = (parse_qs(parsed.query).get("evidence_type") or [None])[0]
                items = [item for item in state.evidence if requested_type is None or item["evidence_type"] == requested_type]
                self.respond(200, {"phase": PHASE, "items": items, "count": len(items)})
                return
            self.respond(404, {"detail": "Not found."})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            state.requests.append(("POST", parsed.path))
            payload = self.body()
            if parsed.path == "/api/auth/login":
                owner = payload.get("email") == "owner@example.test"
                role = "platform_owner" if owner else "platform_admin"
                token = "owner-token" if owner else "admin-token"
                self.respond(200, {
                    "auth": {"user": {"id": f"{role}-validator", "global_role": role}},
                    "session": {"access_token": token},
                })
                return
            if not self.authorized():
                return
            if parsed.path == "/api/platform/pilot-operations/evidence":
                record = state.record(payload)
                self.respond(201, {"phase": PHASE, "evidence": record})
                return
            if parsed.path == "/api/platform/pilot-operations/release-assessments":
                assessment = state.assessment()
                record = state.record({
                    "status": "PASS",
                    "title": "Pilot release assessment",
                    "summary": assessment["recommended_next_action"],
                    "environment_scope": "production",
                    "reference": ASSESSMENT_HASH,
                    "evidence_metadata": {"assessment": assessment},
                }, evidence_type="release_assessment")
                self.respond(201, {"phase": PHASE, "assessment_evidence": record, "automatic_approval_disabled": True})
                return
            if parsed.path == "/api/platform/pilot-operations/pilot-sign-offs":
                record = state.record({
                    "status": "PASS" if payload["decision"] != "rejected" else "BLOCKED",
                    "title": "Pilot release sign-off",
                    "summary": payload["decision_reason"],
                    "environment_scope": "production",
                    "reference": payload["release_id"],
                    "evidence_metadata": {"sign_off": payload},
                }, evidence_type="pilot_sign_off")
                self.respond(201, {"phase": PHASE, "sign_off": record, "automatic_approval_disabled": True})
                return
            self.respond(404, {"detail": "Not found."})

    return Handler


def run_cli(base_url: str, bundle_path: Path, output_dir: Path, *, email: str, answers: str = "") -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "AEROASSIST_PLATFORM_PASSWORD": "Test-only-password",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return subprocess.run(
        [
            sys.executable,
            str(UTILITY),
            "--base-url", base_url,
            "--evidence-file", str(bundle_path),
            "--output-dir", str(output_dir),
            "--email", email,
            "--timeout", "5",
        ],
        input=answers,
        text=True,
        capture_output=True,
        env=env,
        cwd=ROOT,
        timeout=20,
        check=False,
    )


def verify_owner_attestation(base_url: str, state: GovernanceState, temporary: Path) -> None:
    bundle_path = temporary / "evidence.json"
    output_dir = temporary / "reports"
    bundle_path.write_text(json.dumps(evidence_bundle()), encoding="utf-8")
    result = run_cli(
        base_url,
        bundle_path,
        output_dir,
        email="owner@example.test",
        answers="approved\nReviewed all persisted evidence.\nNo additional notes.\nAPPROVE\n",
    )
    if result.returncode != 0:
        raise AssertionError(f"Guided owner attestation failed:\n{result.stdout}\n{result.stderr}")
    if "PASS: Phase 57 attestation persisted and verified." not in result.stdout:
        raise AssertionError("Attestation CLI did not report verified persistence.")
    required_posts = {
        "/api/platform/pilot-operations/evidence",
        "/api/platform/pilot-operations/release-assessments",
        "/api/platform/pilot-operations/pilot-sign-offs",
    }
    observed_posts = {path for method, path in state.requests if method == "POST"}
    if not required_posts.issubset(observed_posts):
        raise AssertionError("Attestation CLI did not use every required Phase 57 governance API.")

    json_report = output_dir / f"{RELEASE_ID}-attestation.json"
    markdown_report = output_dir / f"{RELEASE_ID}-attestation.md"
    for report_path in (json_report, markdown_report):
        if not report_path.is_file() or stat.S_IMODE(report_path.stat().st_mode) != 0o600:
            raise AssertionError(f"Attestation report is missing or not owner-readable only: {report_path}")
        content = report_path.read_text(encoding="utf-8").lower()
        if "test-only-password" in content or "owner-token" in content:
            raise AssertionError("Attestation report leaked authentication material.")
    report = json.loads(json_report.read_text(encoding="utf-8"))
    if report["sign_off"]["decision"] != "approved":
        raise AssertionError("Attestation report does not contain the explicit human decision.")
    if report["persistence_verification"]["pilot_approval_state"] != "APPROVED":
        raise AssertionError("Attestation report does not prove persisted dashboard state.")
    if stat.S_IMODE(output_dir.stat().st_mode) != 0o700:
        raise AssertionError("Attestation report directory is not private to its owner.")


def verify_platform_owner_required(base_url: str, temporary: Path) -> None:
    bundle_path = temporary / "admin-evidence.json"
    bundle_path.write_text(json.dumps(evidence_bundle()), encoding="utf-8")
    result = run_cli(base_url, bundle_path, temporary / "admin-reports", email="admin@example.test")
    if result.returncode == 0 or "requires an authenticated Platform Owner" not in result.stderr:
        raise AssertionError("Attestation utility accepted a non-owner Platform identity.")


def verify_human_decision_guards(module: Any) -> None:
    answers = iter(["approved", "rejected", "Release remains blocked.", "Reviewed.", "REJECT"])
    decision = module.prompt_human_sign_off(
        {"assessment_status": "blocked"}, input_fn=lambda _prompt: next(answers)
    )
    if decision["decision"] != "rejected":
        raise AssertionError("Blocked assessments can reach an approval decision in the guided prompt.")


def verify_bundle_safety(module: Any, temporary: Path) -> None:
    try:
        module.load_evidence_bundle(EXAMPLE)
    except module.AttestationError:
        pass
    else:
        raise AssertionError("Unreplaced example placeholders were accepted for attestation.")

    unsafe = evidence_bundle()
    unsafe["operational_evidence"][0]["evidence_metadata"] = {"raw_log": "unsafe"}
    unsafe_path = temporary / "unsafe.json"
    unsafe_path.write_text(json.dumps(unsafe), encoding="utf-8")
    try:
        module.load_evidence_bundle(unsafe_path)
    except module.AttestationError:
        return
    raise AssertionError("Sensitive evidence metadata was accepted by the attestation utility.")


def main() -> int:
    if not UTILITY.is_file() or not EXAMPLE.is_file():
        raise AssertionError("Phase 57 attestation utility or example evidence bundle is missing.")
    module = load_utility()
    with tempfile.TemporaryDirectory(prefix="phase57-attestation-validator-") as raw_temporary:
        temporary = Path(raw_temporary)
        verify_human_decision_guards(module)
        verify_bundle_safety(module, temporary)
        state = GovernanceState()
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            verify_platform_owner_required(base_url, temporary)
            verify_owner_attestation(base_url, state, temporary)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
    print("Phase 57 pilot release attestation utility validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
