#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import VisualPolicyEditorCard, VisualPolicyEditorCardCreate
from services.visual_policy_editor_service import (
    PHASE_LABEL,
    POLICY_CARD_STATUSES,
    POLICY_FAMILIES,
    SUPPORT_STATUSES,
    VISUAL_POLICY_EDITOR_CARDS_COLLECTION,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_2_agent_work_queue_assignment_foundation"
ROOT = Path(__file__).resolve().parents[2]

REQUIRED_POLICY_FAMILIES = {
    "PETC",
    "AVIH",
    "SVAN",
    "ESAN",
    "WCHR",
    "WCHS",
    "WCHC",
    "WCOB",
    "MAAS",
    "MEDIF",
    "MEDA",
    "STCR",
    "OXYG",
    "POC",
    "UMNR",
    "YP",
    "EXST",
    "CBBG",
    "sports_equipment",
    "musical_instruments",
    "fragile_valuable",
    "restricted_equipment",
    "documents_compliance",
}


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "visual_policy_editor_foundation",
        "policy_execution_disabled",
        "rule_evaluation_disabled",
        "pricing_calculation_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "old_admin_routes_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def card_payload(agency_id: str, reference: str, policy_family: str = "PETC") -> dict:
    return {
        "agency_id": agency_id,
        "card_reference": reference,
        "airline": "LH",
        "policy_family": policy_family,
        "service_family": "pets_animals" if policy_family in {"PETC", "AVIH"} else "passenger_assistance_medical",
        "service_codes": [policy_family],
        "status": "approved",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "support_status": "conditional",
        "limits": {"max_weight_kg": 8, "container_count": 1},
        "restrictions": {
            "route": [{"type": "country_pair", "value": "BG-DE"}],
            "aircraft": [{"type": "aircraft_family", "value": "A320"}],
            "cabin": [{"type": "cabin_class", "value": "economy"}],
            "date": [{"type": "seasonal_window", "value": "summer"}],
            "weather": [{"type": "temperature_zone", "value": "heat_restriction"}],
        },
        "required_documents": [{"document_type": "pet_passport", "required": True}],
        "approval_requirements": [{"approval_type": "airline_manual_confirmation", "required": True}],
        "warnings": [{"audience": "agent", "message": "Confirm aircraft restriction before offer."}],
        "client_messages": [{"audience": "client", "message": "Airline confirmation is required before travel."}],
        "internal_notes": "Phase 52.3 smoke metadata card.",
        "evidence_links": [{"reference": "EVIDENCE-SMOKE-523", "source": "manual_review"}],
        "knowledge_governance_links": ["KGV-SMOKE-523"],
        "service_parameter_taxonomy_links": ["SPT-SMOKE-523"],
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if VISUAL_POLICY_EDITOR_CARDS_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("visual_policy_editor_cards is not registered as agency-owned metadata.")
    missing_families = REQUIRED_POLICY_FAMILIES - set(POLICY_FAMILIES)
    if missing_families:
        raise AssertionError(f"Supported policy families missing: {sorted(missing_families)}")
    if "approved" not in POLICY_CARD_STATUSES or "conditional" not in SUPPORT_STATUSES:
        raise AssertionError("Policy card statuses are incomplete.")

    create = VisualPolicyEditorCardCreate(**card_payload("agency-smoke", "VPE-SMOKE-MODEL"))
    record = VisualPolicyEditorCard(**create.model_dump(mode="json", exclude_none=True))
    if record.card_reference != "VPE-SMOKE-MODEL" or not record.service_codes or not record.required_documents:
        raise AssertionError("VisualPolicyEditorCard model did not preserve service/document metadata.")
    if record.visual_policy_editor_foundation is not True or record.rule_evaluation_disabled is not True:
        raise AssertionError("VisualPolicyEditorCard model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        VISUAL_POLICY_EDITOR_CARDS_COLLECTION,
        "visual_policy_editor_cards_reference_unique",
        "visual_policy_editor_cards_agency_airline_lookup",
        "visual_policy_editor_cards_policy_family_lookup",
        "visual_policy_editor_cards_service_codes_lookup",
        "visual_policy_editor_cards_status_lookup",
        "visual_policy_editor_cards_support_status_lookup",
        "visual_policy_editor_cards_evidence_lookup",
        "visual_policy_editor_cards_governance_lookup",
        "visual_policy_editor_cards_taxonomy_lookup",
        "visual_policy_editor_cards_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/visual-policy-editor", "get"),
        ("/api/platform/visual-policy-editor", "post"),
        ("/api/platform/visual-policy-editor/summary", "get"),
        ("/api/platform/visual-policy-editor/{card_id}", "get"),
        ("/api/platform/visual-policy-editor/{card_id}", "put"),
        ("/api/platform/visual-policy-editor/{card_id}", "delete"),
        ("/api/agencies/{agency_id}/policy-editor", "get"),
        ("/api/agencies/{agency_id}/policy-editor", "post"),
        ("/api/agencies/{agency_id}/policy-editor/summary", "get"),
        ("/api/agencies/{agency_id}/policy-editor/{card_id}", "get"),
        ("/api/agencies/{agency_id}/policy-editor/{card_id}", "put"),
        ("/api/agencies/{agency_id}/policy-editor/{card_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith("/api/admin") or path.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/visual-policy-editor"),
        (ROOT / "frontend/src/App.jsx", "/agency/policy-editor"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Visual Policy Editor"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "visual_policy_editor"),
        (ROOT / "frontend/src/pages/platform/VisualPolicyEditorPage.jsx", "Route / Aircraft / Cabin / Date / Weather Restrictions"),
        (ROOT / "frontend/src/pages/agency/PolicyEditorPage.jsx", "Support Status"),
        (ROOT / "backend/services/saas_subscription_service.py", "visual_policy_editor"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Visual Policy Editor"),
        (ROOT / "docs/architecture/visual-policy-editor-foundation.md", "Phase 52.3"),
        (ROOT / "docs/architecture/current-model-inventory.md", "visual_policy_editor_cards"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/visual-policy-editor"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Visual Policy Editor"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "visual_policy_editor_cards"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Visual Policy Editor Alignment"),
        (ROOT / "docs/architecture/reference-data-engine-foundation.md", "Visual Policy Editor Relationship"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.3"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Visual Policy Editor"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.3"),
        (ROOT / "README.md", "visual policy editor cards"),
    ]:
        require_text(path, text)


def verify_crud_and_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]

    platform_reference = run_ref("VPE-SMOKE-PLATFORM")
    created = post(
        "/api/platform/visual-policy-editor",
        card_payload(agency_id, platform_reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    platform_card = created["visual_policy_editor_card"]
    assert_safety_flags(platform_card)
    if platform_card.get("policy_family") != "PETC" or not platform_card.get("required_documents"):
        raise AssertionError("Platform policy card did not preserve family and documents metadata.")

    listed = get("/api/platform/visual-policy-editor?airline=LH&policy_family=PETC&service_code=PETC&search=aircraft", OWNER_HEADERS)
    if not any(item.get("card_reference") == platform_reference for item in listed.get("items", [])):
        raise AssertionError("Platform filtered list did not include created policy card.")
    summary = get("/api/platform/visual-policy-editor/summary", OWNER_HEADERS)
    if summary.get("summary", {}).get("evidence_link_count", 0) < 1:
        raise AssertionError("Platform summary did not count evidence links.")

    updated = put(
        f"/api/platform/visual-policy-editor/{platform_card['id']}",
        {
            "status": "in_review",
            "support_status": "request_required",
            "warnings": platform_card["warnings"] + [{"audience": "agent", "message": "Manual airline response pending."}],
        },
        OWNER_HEADERS,
    )["visual_policy_editor_card"]
    if updated.get("status") != "in_review" or updated.get("support_status") != "request_required":
        raise AssertionError("Platform update did not persist status metadata.")

    agency_reference = run_ref("VPE-SMOKE-AGENCY")
    agency_created = post(
        f"/api/agencies/{agency_id}/policy-editor",
        card_payload(agency_id, agency_reference, policy_family="WCHR"),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(agency_created)
    agency_card = agency_created["visual_policy_editor_card"]
    if agency_card.get("agency_id") != agency_id or agency_card.get("policy_family") != "WCHR":
        raise AssertionError("Agency policy card did not preserve agency scope.")

    agency_list = get(f"/api/agencies/{agency_id}/policy-editor?airline=LH&policy_family=WCHR&support_status=conditional", OWNER_HEADERS)
    if not any(item.get("card_reference") == agency_reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency filtered list did not include created policy card.")

    agency_updated = put(
        f"/api/agencies/{agency_id}/policy-editor/{agency_card['id']}",
        {"status": "approved", "limits": {"connection_time_minutes": 90}},
        OWNER_HEADERS,
    )["visual_policy_editor_card"]
    if agency_updated.get("limits", {}).get("connection_time_minutes") != 90:
        raise AssertionError("Agency update did not persist limits metadata.")

    archived = request(
        "DELETE",
        f"/api/agencies/{agency_id}/policy-editor/{agency_card['id']}",
        headers=OWNER_HEADERS,
        expect=200,
    )[1]["visual_policy_editor_card"]
    if archived.get("status") != "archived" or archived.get("archived") is not True:
        raise AssertionError("Agency archive did not persist archived metadata.")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("visual_policy_editor_foundation") or {}
    for flag in [
        "visual_policy_editor_enabled",
        "visual_policy_editor_cards_collection_enabled",
        "platform_visual_policy_editor_metadata_crud_enabled",
        "agency_policy_editor_metadata_crud_enabled",
        "platform_visual_policy_editor_ui_enabled",
        "agency_policy_editor_ui_enabled",
        "no_code_policy_sections_enabled",
        "metadata_only",
        "policy_execution_disabled",
        "rule_evaluation_disabled",
        "pricing_calculation_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "old_admin_routes_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if set(section.get("policy_families") or []) != set(POLICY_FAMILIES):
        raise AssertionError("Readiness did not expose supported policy families.")
    if section.get("visual_policy_editor_evidence_link_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted policy evidence links.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "visual-policy-editor" in lowered or "policy-editor" in lowered:
            for marker in ["execute-policy", "evaluate-rules", "calculate-pricing", "ai-generate", "background-worker"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden Visual Policy Editor execution route registered: {path}")

    for path in [
        ROOT / "backend/services/visual_policy_editor_service.py",
        ROOT / "backend/routers/platform_visual_policy_editor.py",
        ROOT / "backend/routers/agency_visual_policy_editor.py",
        ROOT / "frontend/src/pages/platform/VisualPolicyEditorPage.jsx",
        ROOT / "frontend/src/pages/agency/PolicyEditorPage.jsx",
    ]:
        for marker in [
            "BackgroundTasks",
            "asyncio.create_task",
            "httpx",
            "requests.",
            "openai",
            "ChatCompletion",
            "provider_client =",
            "def execute_policy",
            "def evaluate_rule",
            "def calculate_price",
            "def calculate_pricing",
            "@router.get(\"/admin",
            "@router.post(\"/admin",
            "\"/api/admin",
        ]:
            reject_text(path, marker)


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_crud_and_readiness()
    verify_boundaries()
    print("Visual policy editor foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Visual policy editor foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
