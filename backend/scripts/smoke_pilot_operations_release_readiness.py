#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import ast
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE, phase_is_exact
from database import Database
from models import (
    PilotAgencyInvitationCreate,
    PilotHealthTimelineEventCreate,
    PilotOperationalEvidenceCreate,
    PilotReleaseProductionEvidence,
    PilotReleaseSignOff,
    PilotSyntheticDatasetCreate,
)
from services.pilot_operations_release_readiness_service import (
    ASSESSMENT_STATUSES,
    CATEGORY_DIMENSIONS,
    PHASE_LABEL,
    PILOT_OPERATIONS_COLLECTIONS,
    PilotOperationsError,
    PilotOperationsReleaseReadinessService,
    pilot_operations_readiness_metadata,
)


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def request(path: str, *, headers: dict[str, str] | None = None) -> tuple[int, object]:
    value = urllib.request.Request(f"{BASE_URL}{path}", headers=headers or {})
    try:
        with urllib.request.urlopen(value, timeout=10) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        return exc.code, json.loads(body) if body else {}


def full_evidence(role: str = "platform_owner") -> PilotReleaseProductionEvidence:
    return PilotReleaseProductionEvidence(
        production_git_commit="phase570smoke",
        production_phase=PHASE_LABEL,
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
        verified_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        verified_by_role=role,
        evidence_references=("CI_FIXTURE_PHASE_57_RELEASE",),
    )


def verify_static_registration() -> None:
    if not phase_is_exact(CURRENT_BUILD_PHASE, PHASE_LABEL):
        raise AssertionError(f"Phase 57.0 marker mismatch: {CURRENT_BUILD_PHASE}")
    if set(CATEGORY_DIMENSIONS) != {"infrastructure", "security", "database", "frontend", "backend", "observability", "backups", "tenant_isolation"}:
        raise AssertionError("Release assessment groups are incomplete.")
    if ASSESSMENT_STATUSES != {"PASS", "WARNING", "BLOCKED"}:
        raise AssertionError("Canonical Phase 57.0 assessment statuses are incomplete.")
    metadata = pilot_operations_readiness_metadata()
    if not metadata.get("human_pilot_sign_off_required") or not metadata.get("automatic_release_approval_disabled"):
        raise AssertionError("Public readiness does not preserve explicit human approval.")

    required_files = [
        BACKEND / "services" / "pilot_operations_release_readiness_service.py",
        BACKEND / "routers" / "platform_pilot_operations_release_readiness.py",
        ROOT / "frontend" / "src" / "pages" / "platform" / "PilotOperationsReadinessPage.jsx",
        ROOT / "docs" / "architecture" / "pilot-operations-release-readiness.md",
    ]
    for path in required_files:
        if not path.is_file():
            raise AssertionError(f"Phase 57.0 file is missing: {path}")

    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    database_text = (BACKEND / "database.py").read_text(encoding="utf-8")
    router_text = required_files[1].read_text(encoding="utf-8")
    app_text = (ROOT / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
    catalog_text = (ROOT / "frontend" / "src" / "lib" / "moduleCatalog.js").read_text(encoding="utf-8")
    for collection in PILOT_OPERATIONS_COLLECTIONS:
        if collection not in database_text:
            raise AssertionError(f"Mongo collection/index registration is missing: {collection}")
    if '"pilot_operations_release_readiness"' not in server_text or "platform_pilot_operations_release_readiness.router" not in server_text:
        raise AssertionError("Phase 57.0 readiness or router registration is missing.")
    if "OWNER_ONLY = [\"platform_owner\"]" not in router_text or "require_platform_role" not in router_text:
        raise AssertionError("Pilot agency and synthetic data mutations are not Platform Owner governed.")
    if "/platform/pilot-operations" not in app_text or "/platform/pilot-operations" not in catalog_text:
        raise AssertionError("Platform pilot operations route or module registration is missing.")

    tree = ast.parse(required_files[0].read_text(encoding="utf-8"), filename=str(required_files[0]))
    forbidden = {"urlopen", "Popen", "system", "popen", "run"}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name in forbidden:
                found.append(name)
    if found:
        raise AssertionError(f"Pilot operations service contains forbidden execution calls: {found}")


async def verify_service_contracts() -> None:
    db = Database()
    db.mode = "memory"
    service = PilotOperationsReleaseReadinessService(db)
    owner = {"id": "platform-owner-smoke", "global_role": "platform_owner"}
    agency = {
        "id": "agency-phase-57-smoke",
        "name": "Phase 57 Synthetic Agency",
        "slug": "phase-57-synthetic-agency",
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.collection("agencies").insert_one(agency)

    enrollment = await service.invite_agency(PilotAgencyInvitationCreate(agency_id=agency["id"], reason="Controlled smoke enrollment."), owner)
    if enrollment.get("enrollment_status") != "invited":
        raise AssertionError("Pilot agency invitation was not persisted.")
    try:
        await service.create_synthetic_dataset(PilotSyntheticDatasetCreate(agency_id=agency["id"], dataset_reference="PILOT_TEST_PHASE57", record_count=3), owner)
        raise AssertionError("Synthetic data was created before pilot enablement.")
    except PilotOperationsError:
        pass

    enabled = await service.change_enrollment_status(enrollment["id"], "enabled", "Explicit test enablement.", owner)
    if enabled.get("enrollment_status") != "enabled" or not enabled.get("synthetic_data_allowed"):
        raise AssertionError("Pilot enablement state was not tracked.")
    dataset = await service.create_synthetic_dataset(PilotSyntheticDatasetCreate(agency_id=agency["id"], dataset_reference="PILOT_TEST_PHASE57", record_count=3), owner)
    if dataset.get("record_count") != 3 or any(not item.get("synthetic") for item in dataset.get("synthetic_records", [])):
        raise AssertionError("Synthetic dataset is not isolated and explicitly marked.")
    if dataset.get("contains_real_identity_data") or dataset.get("provider_connectivity_enabled"):
        raise AssertionError("Synthetic dataset enables unsafe production semantics.")

    smoke = await service.create_evidence(PilotOperationalEvidenceCreate(
        evidence_type="smoke_run",
        status="PASS",
        title="Phase 57 smoke",
        summary="Disposable smoke metadata passed.",
        reference="CI_FIXTURE_PHASE57_SMOKE",
        evidence_metadata={"ci_status": "PASS", "suite": "focused"},
    ), owner)
    if not smoke.get("immutable"):
        raise AssertionError("Operational evidence is not immutable.")
    try:
        await service.create_evidence(PilotOperationalEvidenceCreate(
            evidence_type="production_validation",
            status="PASS",
            title="Unsafe evidence",
            summary="Must be rejected.",
            reference="CI_FIXTURE_UNSAFE",
            evidence_metadata={"password": "must-not-store"},
        ), owner)
        raise AssertionError("Sensitive evidence metadata was accepted.")
    except PilotOperationsError:
        pass

    earlier = datetime.now(timezone.utc) - timedelta(days=1)
    later = datetime.now(timezone.utc)
    await service.create_health_event(PilotHealthTimelineEventCreate(event_type="incident", status="WARNING", title="Synthetic incident", summary="Controlled incident record.", reference="CI_FIXTURE_INCIDENT_EARLY", occurred_at=earlier), owner)
    await service.create_health_event(PilotHealthTimelineEventCreate(event_type="health", status="PASS", title="Synthetic recovery", summary="Controlled recovery record.", reference="CI_FIXTURE_HEALTH_LATE", occurred_at=later), owner)
    timeline = await service.list_health_timeline()
    if timeline[0].get("reference") != "CI_FIXTURE_HEALTH_LATE":
        raise AssertionError("Health timeline is not newest first.")

    assessment_record = await service.assess_release(full_evidence(), owner)
    assessment = assessment_record.get("evidence_metadata", {}).get("assessment", {})
    if assessment.get("assessment_status") != "ready" or assessment_record.get("status") != "PASS":
        raise AssertionError(f"Complete explicit release evidence was not assessed ready: {assessment.get('blocking_items')}")
    sign_off = PilotReleaseSignOff(
        release_id="PILOT_TEST_PHASE57_RELEASE",
        target_phase=PHASE_LABEL,
        decision="approved",
        decision_reason="Explicit synthetic smoke sign-off.",
        approved_by_role="platform_owner",
        approved_at=datetime.now(timezone.utc),
        assessment_hash=assessment["assessment_hash"],
        human_approved=True,
    )
    signed = await service.record_sign_off(sign_off, owner)
    if signed.get("status") != "PASS":
        raise AssertionError("Explicit pilot sign-off was not persisted.")

    dashboard = await service.dashboard()
    if dashboard.get("overview", {}).get("pilot_approval_state") != "APPROVED":
        raise AssertionError("Dashboard does not show the explicit pilot approval state.")
    if {item.get("category") for item in dashboard.get("assessment_groups", [])} != set(CATEGORY_DIMENSIONS):
        raise AssertionError("Dashboard release assessment groups are incomplete.")
    diagnostics = await service.production_diagnostics()
    if diagnostics.get("raw_logs_exposed") or diagnostics.get("sensitive_values_exposed"):
        raise AssertionError("Protected diagnostics expose raw or sensitive values.")

    removed = await service.remove_synthetic_dataset(dataset["id"], "Smoke cleanup.", owner)
    if removed.get("dataset_status") != "removed" or removed.get("synthetic_records") or removed.get("record_count"):
        raise AssertionError("Synthetic dataset removal did not clear fixture contents safely.")
    audit_count = await db.collection("audit_events").count({"entity_type": "pilot_operations"})
    if audit_count < 6:
        raise AssertionError("Pilot actions were not written to the existing audit stream.")


def verify_live_contracts() -> None:
    health_status, health = request("/api/health")
    if health_status != 200 or not isinstance(health, dict) or health.get("phase") != PHASE_LABEL:
        raise AssertionError(f"Health does not report Phase 57.0: {health}")
    if health.get("pilot_operations_release_readiness") is not True:
        raise AssertionError("Health does not expose the public-safe Phase 57.0 capability flag.")

    readiness_status, readiness = request("/api/readiness")
    section = readiness.get("pilot_operations_release_readiness", {}) if isinstance(readiness, dict) else {}
    if readiness_status != 200 or set(section) != set(pilot_operations_readiness_metadata()):
        raise AssertionError("Public readiness Phase 57.0 projection is missing or unsafe.")
    forbidden = {"operational_diagnostics", "counters", "timings", "startup_timestamp", "uptime_seconds"}
    if forbidden.intersection(section):
        raise AssertionError("Public readiness exposes protected operational diagnostics.")

    denied_status, _ = request("/api/platform/pilot-operations", headers={"Authorization": "Bearer invalid-phase-57-token"})
    if denied_status != 401:
        raise AssertionError("Pilot operations dashboard accepted invalid authorization.")
    authorized_status, dashboard = request("/api/platform/pilot-operations", headers={"X-Demo-User-Email": "owner@aeroassist.dev"})
    if authorized_status != 200 or not isinstance(dashboard, dict) or not dashboard.get("assessment_groups"):
        raise AssertionError(f"Authorized pilot operations dashboard failed: {dashboard}")
    diagnostics_status, diagnostics = request("/api/platform/pilot-operations/production-diagnostics", headers={"X-Demo-User-Email": "owner@aeroassist.dev"})
    if diagnostics_status != 200 or diagnostics.get("raw_logs_exposed") is not False:
        raise AssertionError("Protected bounded production diagnostics failed.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    verify_static_registration()
    asyncio.run(verify_service_contracts())
    if not args.static:
        verify_live_contracts()
    print("Phase 57.0 pilot operations and release readiness smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
