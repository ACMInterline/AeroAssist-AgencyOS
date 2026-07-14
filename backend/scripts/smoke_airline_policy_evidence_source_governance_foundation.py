#!/usr/bin/env python3
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from models import (
    AirlineEvidenceAccessClassification,
    AirlineEvidenceArtifact,
    AirlineEvidenceAssertion,
    AirlineEvidenceConflict,
    AirlineEvidenceFreshnessAssessment,
    AirlineEvidenceLink,
    AirlineEvidenceReview,
    AirlineEvidenceSource,
)
from services.airline_policy_evidence_governance_service import (
    CONFLICT_STATUSES,
    EVIDENCE_COLLECTIONS,
    PHASE_LABEL,
    RAW_SOURCE_COLLECTIONS,
    SOURCE_TYPES,
    TARGET_COLLECTIONS,
    AirlinePolicyEvidenceGovernanceService,
)
from smoke_airline_knowledge_acquisition_workspace_foundation import acquisition_payload
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_6_interline_codeshare_operating_carrier_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
PLATFORM_BASE = "/api/platform/airline-evidence"


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    if text.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_no_restricted_material(value: object) -> None:
    restricted = {
        "internal_notes",
        "review_notes",
        "reviewer_user_id",
        "assessed_by_user_id",
        "storage_reference",
        "raw_source_collection",
        "raw_source_record_id",
        "checksum",
        "source_url",
        "conflicting_values",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency evidence response leaked restricted field {key}")
            assert_no_restricted_material(child)
    elif isinstance(value, list):
        for item in value:
            assert_no_restricted_material(item)


def verify_models_collections_and_indexes() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 55.2 label: {PHASE_LABEL}")
    expected = {
        "airline_evidence_sources",
        "airline_evidence_artifacts",
        "airline_evidence_assertions",
        "airline_evidence_links",
        "airline_evidence_reviews",
        "airline_evidence_conflicts",
        "airline_evidence_freshness_assessments",
        "airline_evidence_access_classifications",
    }
    if set(EVIDENCE_COLLECTIONS) != expected:
        raise AssertionError(f"Evidence collection registration is incomplete: {EVIDENCE_COLLECTIONS}")
    if RAW_SOURCE_COLLECTIONS != {"airline_policy_sources", "airline_knowledge_acquisitions", "airline_knowledge_sources"}:
        raise AssertionError("Phase 55.2 does not retain all canonical raw evidence intake boundaries.")
    if len(SOURCE_TYPES) != 20 or "airline_agent_manual" not in SOURCE_TYPES or "api_response" not in SOURCE_TYPES:
        raise AssertionError("Evidence source taxonomy is incomplete.")
    if set(CONFLICT_STATUSES) != {"detected", "under_review", "accepted_variant", "superseded", "unresolved", "resolved", "archived"}:
        raise AssertionError("Evidence conflict lifecycle is incomplete.")
    for target in ["airline_profile_field", "airline_policy", "pricing_formula", "operational_rule", "capability_matrix", "distribution_fact", "pss_fact", "gds_fact", "interline_codeshare_rule", "contact", "published_knowledge"]:
        if target not in TARGET_COLLECTIONS:
            raise AssertionError(f"Evidence target registration missing {target}")

    source = AirlineEvidenceSource(source_reference="AES-MODEL", source_type="airline_tariff", title="Tariff")
    artifact = AirlineEvidenceArtifact(source_id=source.id, artifact_reference="AEA-MODEL", artifact_type="pdf_manual")
    assertion = AirlineEvidenceAssertion(source_id=source.id, assertion_reference="EAS-MODEL", assertion_type="pricing", assertion_key="petc.limit", structured_value={"value": 8, "unit": "kg"})
    records = [
        AirlineEvidenceLink(source_id=source.id, assertion_id=assertion.id, target_type="airline_policy", target_id="policy"),
        AirlineEvidenceReview(source_id=source.id, review_type="source_review"),
        AirlineEvidenceConflict(conflict_reference="EAC-MODEL", conflict_type="limit_conflict", assertion_key="petc.limit", source_ids=[source.id], assertion_ids=[assertion.id]),
        AirlineEvidenceFreshnessAssessment(source_id=source.id, explanation="Model smoke"),
        AirlineEvidenceAccessClassification(classification_code="agency_approved", name="Agency approved"),
    ]
    if artifact.source_id != source.id or any(not record.id for record in records):
        raise AssertionError("Evidence models did not retain canonical relationships.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_evidence_sources_reference_unique",
        "airline_evidence_artifacts_reference_unique",
        "airline_evidence_assertions_reference_unique",
        "airline_evidence_links_id_unique",
        "airline_evidence_reviews_id_unique",
        "airline_evidence_conflicts_reference_unique",
        "airline_evidence_freshness_id_unique",
        "airline_evidence_access_code_unique",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


def verify_deterministic_governance_and_safety() -> None:
    service = AirlinePolicyEvidenceGovernanceService(None)  # type: ignore[arg-type]
    official = {"source_type": "airline_tariff", "checksum": "abc", "effective_from": "2026-01-01", "review_decision": "approved"}
    observation = {"source_type": "internal_operational_observation"}
    official_score = service.calculate_confidence(official)
    observation_score = service.calculate_confidence(observation)
    if official_score["score"] <= observation_score["score"] or official_score["level"] != "high":
        raise AssertionError("Authority and confidence calculation is not deterministic.")
    superseded = service.calculate_confidence({**official, "superseded": True})
    if superseded["score"] >= official_score["score"]:
        raise AssertionError("Superseded evidence confidence was not reduced.")
    for key, enabled in service.safety_flags().items():
        if enabled is not True:
            raise AssertionError(f"Evidence governance safety flag is disabled: {key}")

    service_path = ROOT / "backend/services/airline_policy_evidence_governance_service.py"
    for forbidden in ["requests.get(", "requests.post(", "httpx.", "openai", "backgroundtasks", "asyncio.create_task", ".delete_one(", ".delete_many(", "seed_core_data"]:
        reject_text(service_path, forbidden)


def verify_routes_ui_and_docs(paths: dict) -> None:
    expected = {
        "/api/platform/airline-evidence": {"get"},
        "/api/platform/airline-evidence/sources": {"post"},
        "/api/platform/airline-evidence/sources/{source_id}": {"get", "put", "delete"},
        "/api/platform/airline-evidence/artifacts": {"post"},
        "/api/platform/airline-evidence/assertions": {"post"},
        "/api/platform/airline-evidence/links": {"post"},
        "/api/platform/airline-evidence/access-classifications": {"post"},
        "/api/platform/airline-evidence/conflicts/{conflict_id}": {"put"},
        "/api/platform/airline-evidence/sources/{source_id}/supersede": {"post"},
        "/api/platform/airline-evidence/freshness-assessments": {"post"},
        "/api/platform/airline-evidence/unsupported-knowledge": {"get"},
        "/api/platform/airline-evidence/trace": {"get"},
        "/api/agencies/{agency_id}/airline-evidence": {"get"},
        "/api/agencies/{agency_id}/airline-evidence/sources/{source_id}": {"get"},
        "/api/agencies/{agency_id}/airline-evidence/trace": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")

    checks = [
        ("frontend/src/App.jsx", "/platform/airline-evidence"),
        ("frontend/src/App.jsx", "/agency/airline-evidence"),
        ("frontend/src/lib/moduleCatalog.js", "Airline Evidence"),
        ("frontend/src/pages/platform/AirlineEvidencePage.jsx", "Conflicts are retained for human review"),
        ("frontend/src/pages/agency/AirlineEvidencePage.jsx", "Restricted attachments, source locations, and internal review notes are not shown"),
        ("docs/architecture/airline-policy-evidence-source-governance-foundation.md", "It never deletes either source or assertion"),
        ("BUILD_PHASES.md", "Implemented Phase 55.2"),
        ("README.md", "Phase 55.2 Airline Policy Evidence And Source Governance"),
        ("docs/architecture/current-model-inventory.md", "airline_evidence_conflicts"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/airline-evidence"),
        ("docs/architecture/foundations/GLOSSARY.md", "Evidence Conflict"),
        ("docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 55.2 Evidence Governance"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.2 Airline Evidence Governance"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.2 Alignment"),
        ("backend/services/blueprint_adoption_service.py", "Airline Policy Evidence Governance"),
    ]
    for relative, text in checks:
        require_text(ROOT / relative, text)
    require_text(ROOT / "backend/routers/agency_airline_policy_evidence_governance.py", "assert_agency_access")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_policy_evidence_source_governance_foundation") or {}
    for key in [
        "airline_policy_evidence_source_governance_enabled",
        "raw_source_truth_preserved",
        "conflicting_sources_preserved",
        "supersede_without_destroying_enabled",
        "unsupported_knowledge_detection_enabled",
        "restricted_evidence_protected",
        "agency_evidence_read_only_enabled",
        "physical_evidence_deletion_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.2 flag {key}: {section}")
    for key in ["source_count", "artifact_count", "assertion_count", "evidence_link_count", "conflict_count", "unsupported_knowledge_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.2 counter {key}")


def ensure_profile_target() -> tuple[str, str]:
    directory = get("/api/platform/airline-master-profiles", OWNER_HEADERS)
    target = next((item for item in directory.get("items") or [] if not item.get("profile")), (directory.get("items") or [None])[0])
    if not target:
        raise AssertionError("No canonical airline exists for evidence linkage.")
    airline_id = target["identity"]["canonical_airline_id"]
    if not target.get("profile"):
        post(
            "/api/platform/airline-master-profiles",
            {
                "canonical_airline_id": airline_id,
                "commercial_name": target["identity"]["commercial_name"],
                "review_status": "approved",
                "confidence": "high",
                "effective_from": "2026-01-01",
                "source_reference_ids": ["phase-55-2-smoke"],
                "internal_notes": "Restricted profile context",
            },
            OWNER_HEADERS,
            201,
        )
    detail = get(f"/api/platform/airline-master-profiles/{airline_id}", OWNER_HEADERS).get("item") or {}
    profile_id = (detail.get("profile") or {}).get("id")
    if not profile_id:
        raise AssertionError(f"Canonical master profile target was not created: {detail}")
    return airline_id, profile_id


def source_payload(*, token: str, agency_id: str, airline_id: str, title: str, source_type: str, classification_id: str, raw_id: str | None = None) -> dict:
    payload = {
        "scope": "agency",
        "agency_id": agency_id,
        "canonical_airline_id": airline_id,
        "source_reference": f"AES-{token}",
        "source_type": source_type,
        "title": title,
        "source_url": f"https://restricted.example.test/{token}",
        "source_owner": "Smoke airline policy desk",
        "captured_at": "2024-01-01T00:00:00Z" if raw_id else "2026-07-14T00:00:00Z",
        "review_due_date": "2025-01-01" if raw_id else "2027-07-14",
        "effective_from": "2026-01-01",
        "language": "en",
        "jurisdiction": "EU",
        "checksum": f"checksum-{token}",
        "evidence_status": "approved",
        "accessibility": "agency_visible",
        "access_classification_id": classification_id,
        "internal_notes": "Restricted source review notes",
    }
    if raw_id:
        payload.update({"raw_source_collection": "airline_knowledge_acquisitions", "raw_source_record_id": raw_id})
    return payload


def verify_live_governance() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.2 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    airline_id, profile_id = ensure_profile_target()
    token = uuid4().hex[:10]

    raw = post(
        "/api/platform/airline-knowledge-acquisition",
        acquisition_payload(agency_id, f"AKA-EVIDENCE-{token}"),
        OWNER_HEADERS,
        201,
    ).get("airline_knowledge_acquisition") or {}
    if not raw.get("id") or not raw.get("raw_source_text"):
        raise AssertionError("Raw acquisition truth was not created before evidence governance metadata.")

    classification = post(
        f"{PLATFORM_BASE}/access-classifications",
        {
            "classification_code": f"agency-approved-{token}",
            "name": "Agency approved evidence",
            "agency_visible": True,
            "client_visible": False,
            "attachment_visible": False,
            "internal_only": False,
        },
        OWNER_HEADERS,
        201,
    )["item"]

    first = post(
        f"{PLATFORM_BASE}/sources",
        source_payload(token=f"{token}-1", agency_id=agency_id, airline_id=airline_id, title="PETC agent manual limit", source_type="airline_agent_manual", classification_id=classification["id"], raw_id=raw["id"]),
        OWNER_HEADERS,
        201,
    )["source"]
    if first.get("raw_source_record_id") != raw["id"] or first.get("authority_assessment", {}).get("level") != "high":
        raise AssertionError(f"Evidence source did not retain raw-source linkage and authority: {first}")
    if (first.get("freshness") or {}).get("freshness_status") not in {"review_overdue", "stale"}:
        raise AssertionError(f"Old evidence was not identified for freshness review: {first}")

    artifact = post(
        f"{PLATFORM_BASE}/artifacts",
        {
            "source_id": first["id"],
            "agency_id": "foreign-agency-must-not-win",
            "artifact_reference": f"AEA-{token}",
            "artifact_type": "pdf_manual",
            "title": "Restricted agent manual excerpt",
            "storage_reference": "restricted://manual.pdf",
            "file_name": "manual.pdf",
            "checksum": f"artifact-{token}",
            "accessibility": "internal_restricted",
            "internal_notes": "Never expose this attachment to agency summaries.",
        },
        OWNER_HEADERS,
        201,
    )["item"]
    if artifact.get("source_id") != first["id"] or artifact.get("agency_id") != agency_id:
        raise AssertionError("Evidence artifact did not inherit canonical source scope.")

    first_assertion_result = post(
        f"{PLATFORM_BASE}/assertions",
        {
            "source_id": first["id"],
            "agency_id": "foreign-agency-must-not-win",
            "canonical_airline_id": "foreign-airline-must-not-win",
            "assertion_reference": f"EAS-{token}-1",
            "assertion_type": "policy_limit",
            "assertion_key": "petc.total_weight_limit",
            "assertion_title": "PETC total weight limit",
            "excerpt": "Manual states a total limit.",
            "structured_value": {"value": 8, "unit": "kg"},
            "unit": "kg",
            "distribution_channel": "agency_gds",
            "route_scope": "EU",
            "service_family": "PETC",
            "effective_from": "2026-01-01",
            "evidence_status": "approved",
            "accessibility": "agency_visible",
            "internal_notes": "Restricted assertion notes",
        },
        OWNER_HEADERS,
        201,
    )["item"]
    first_assertion = first_assertion_result["assertion"]
    if first_assertion.get("agency_id") != agency_id or first_assertion.get("canonical_airline_id") != airline_id:
        raise AssertionError("Evidence assertion did not inherit canonical source scope.")
    if first_assertion_result.get("conflicts"):
        raise AssertionError("The first assertion unexpectedly produced a conflict.")

    first_link = post(
        f"{PLATFORM_BASE}/links",
        {
            "source_id": first["id"],
            "assertion_id": first_assertion["id"],
            "agency_id": "foreign-agency-must-not-win",
            "canonical_airline_id": "foreign-airline-must-not-win",
            "target_type": "airline_profile",
            "target_id": profile_id,
            "target_field_path": "service_capabilities.petc.total_weight_limit",
            "agency_visible": True,
            "client_visible": False,
            "internal_notes": "Restricted link context",
        },
        OWNER_HEADERS,
        201,
    )["item"]
    if first_link.get("target_id") != profile_id or first_link.get("agency_id") != agency_id or first_link.get("canonical_airline_id") != airline_id:
        raise AssertionError("Evidence link did not inherit source scope and retain the canonical knowledge target.")

    second = post(
        f"{PLATFORM_BASE}/sources",
        source_payload(token=f"{token}-2", agency_id=agency_id, airline_id=airline_id, title="PETC public website limit", source_type="airline_public_website", classification_id=classification["id"]),
        OWNER_HEADERS,
        201,
    )["source"]
    second_assertion_result = post(
        f"{PLATFORM_BASE}/assertions",
        {
            "source_id": second["id"],
            "assertion_reference": f"EAS-{token}-2",
            "assertion_type": "policy_limit",
            "assertion_key": "petc.total_weight_limit",
            "structured_value": {"value": 10, "unit": "kg"},
            "unit": "kg",
            "distribution_channel": "public_web",
            "route_scope": "EU",
            "service_family": "PETC",
            "effective_from": "2026-01-01",
            "evidence_status": "approved",
            "accessibility": "agency_visible",
        },
        OWNER_HEADERS,
        201,
    )["item"]
    second_assertion = second_assertion_result["assertion"]
    conflicts = second_assertion_result.get("conflicts") or []
    if len(conflicts) != 1 or conflicts[0].get("source_truth_preserved") is not True:
        raise AssertionError(f"Conflicting assertion was not detected and preserved: {second_assertion_result}")
    conflict = conflicts[0]
    if set(conflict.get("source_ids") or []) != {first["id"], second["id"]}:
        raise AssertionError("Conflict did not retain both source references.")

    post(
        f"{PLATFORM_BASE}/links",
        {
            "source_id": second["id"],
            "assertion_id": second_assertion["id"],
            "target_type": "airline_profile",
            "target_id": profile_id,
            "target_field_path": "service_capabilities.petc.total_weight_limit",
            "agency_visible": True,
        },
        OWNER_HEADERS,
        201,
    )
    resolved = put(
        f"{PLATFORM_BASE}/conflicts/{conflict['id']}",
        {
            "status": "accepted_variant",
            "accepted_assertion_ids": [first_assertion["id"], second_assertion["id"]],
            "resolution_summary": "Both channel-specific values remain valid pending airline clarification.",
        },
        OWNER_HEADERS,
    )
    if resolved.get("source_truth_preserved") is not True or resolved.get("conflict", {}).get("status") != "accepted_variant":
        raise AssertionError(f"Conflict resolution did not preserve source truth: {resolved}")

    trace = get(f"{PLATFORM_BASE}/trace?target_type=airline_profile&target_id={profile_id}", OWNER_HEADERS)
    if not trace.get("trace_complete") or len(trace.get("assertions") or []) < 2 or len(trace.get("sources") or []) < 2:
        raise AssertionError(f"Evidence trace is incomplete: {trace}")
    unsupported = get(f"{PLATFORM_BASE}/unsupported-knowledge", OWNER_HEADERS)
    if any(item.get("target_type") == "airline_profile" and item.get("target_id") == profile_id for item in unsupported.get("items") or []):
        raise AssertionError("Linked airline profile remains incorrectly classified as unsupported knowledge.")
    if not all(item.get("manual_review_required") is True for item in unsupported.get("items") or []):
        raise AssertionError("Unsupported knowledge does not consistently require manual review.")

    agency_summary = get(f"/api/agencies/{agency_id}/airline-evidence", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or agency_summary.get("visible_source_count", 0) < 2:
        raise AssertionError(f"Agency approved evidence summary is incomplete: {agency_summary}")
    assert_no_restricted_material(agency_summary)
    agency_source = get(f"/api/agencies/{agency_id}/airline-evidence/sources/{second['id']}", OWNER_HEADERS)
    assert_no_restricted_material(agency_source)
    agency_trace = get(f"/api/agencies/{agency_id}/airline-evidence/trace?target_type=airline_profile&target_id={profile_id}", OWNER_HEADERS)
    if not agency_trace.get("trace_complete"):
        raise AssertionError(f"Agency evidence trace omitted approved links: {agency_trace}")
    assert_no_restricted_material(agency_trace)
    request("POST", f"/api/agencies/{agency_id}/airline-evidence", {}, OWNER_HEADERS, 405)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    if len(agencies) > 1:
        isolated = get(f"/api/agencies/{agencies[1]['id']}/airline-evidence", OWNER_HEADERS)
        if any(item.get("id") in {first["id"], second["id"]} for item in isolated.get("sources") or []):
            raise AssertionError("Agency-scoped evidence leaked into another agency summary.")

    replacement = post(
        f"{PLATFORM_BASE}/sources",
        source_payload(token=f"{token}-3", agency_id=agency_id, airline_id=airline_id, title="Replacement PETC clarification", source_type="airline_email_confirmation", classification_id=classification["id"]),
        OWNER_HEADERS,
        201,
    )["source"]
    superseded = post(
        f"{PLATFORM_BASE}/sources/{first['id']}/supersede",
        {"replacement_source_id": replacement["id"], "reason": "New airline confirmation"},
        OWNER_HEADERS,
    )
    if superseded.get("source_truth_preserved") is not True or superseded.get("superseded_source", {}).get("superseded") is not True:
        raise AssertionError(f"Source supersession was destructive or incomplete: {superseded}")
    retained = get(f"{PLATFORM_BASE}/sources/{first['id']}", OWNER_HEADERS)["source"]
    if retained.get("superseded_by_source_id") != replacement["id"] or retained.get("raw_source_record_id") != raw["id"]:
        raise AssertionError("Superseded source or its raw provenance was not retained.")


def main() -> int:
    verify_models_collections_and_indexes()
    verify_deterministic_governance_and_safety()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes_ui_and_docs(paths)
    verify_readiness()
    verify_live_governance()
    print("Phase 55.2 airline policy evidence and source governance foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
