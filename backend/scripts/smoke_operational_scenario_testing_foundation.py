#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import OperationalScenarioTest, OperationalScenarioTestCreate
from services.operational_scenario_testing_service import (
    EXPECTED_RECOMMENDATION_LEVELS,
    OPERATIONAL_SCENARIO_TESTS_COLLECTION,
    PHASE_LABEL,
    SCENARIO_FAMILIES,
    SCENARIO_TEST_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_5_request_to_trip_operational_conversion_foundation"
ROOT = Path(__file__).resolve().parents[2]


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
        "operational_scenario_testing_foundation",
        "scenario_execution_disabled",
        "live_provider_execution_disabled",
        "ai_disabled",
        "automated_test_execution_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def scenario_payload(agency_id: str, reference: str, status: str = "ready_for_review") -> dict:
    return {
        "agency_id": agency_id,
        "scenario_reference": reference,
        "scenario_name": "Phase 52.8 PETC passenger service scenario",
        "scenario_family": "PETC",
        "passenger_context": {
            "passenger_type": "adult",
            "need_summary": "Passenger wants to travel with a small dog in cabin.",
            "assistance_profile": "none",
        },
        "itinerary_context": {
            "origin": "SOF",
            "destination": "FRA",
            "departure_date": "2026-11-10",
            "cabin": "economy",
        },
        "airline_context": {
            "airline_code": "LH",
            "airline_name": "Lufthansa",
            "operating_carrier": "LH",
        },
        "service_requirements": [
            {
                "code": "PETC",
                "family": "pets_animals",
                "description": "Pet in cabin request with carrier and document requirements.",
            }
        ],
        "pets": [
            {
                "species": "dog",
                "weight_kg": 6,
                "container_type": "soft_sided_carrier",
            }
        ],
        "special_items": [],
        "documents": [
            {
                "document_type": "pet_passport",
                "required": True,
                "review_status": "expected",
            }
        ],
        "expected_policy_outcome": {
            "support_status": "conditional",
            "approval_required": True,
            "notes": "Policy should require carrier, weight, and document checks.",
        },
        "expected_pricing_behavior": {
            "charge_expected": True,
            "pricing_reference": "RFIC-C-RFISC-0BT",
            "manual_confirmation": True,
        },
        "expected_feasibility": {
            "outcome": "conditionally_feasible",
            "manual_review": True,
            "blocker_expected": False,
        },
        "expected_recommendation_level": "recommended",
        "expected_required_actions": [
            {"action": "create_ssr", "code": "PETC"},
            {"action": "verify_document", "document": "pet_passport"},
        ],
        "evidence_links": [
            {
                "reference": "EVID-SMOKE-528",
                "source": "manual_policy_review",
            }
        ],
        "test_status": status,
        "review_notes": "Metadata-only scenario record for human review.",
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if OPERATIONAL_SCENARIO_TESTS_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("operational_scenario_tests is not registered as agency-owned metadata.")
    for value in ["petc", "avih", "svan", "exst_passenger_of_size", "cbbg", "wchc", "medif", "poc", "umnr"]:
        if value not in SCENARIO_FAMILIES:
            raise AssertionError(f"Missing scenario family: {value}")
    for value in ["draft", "ready_for_review", "reviewed", "approved", "archived"]:
        if value not in SCENARIO_TEST_STATUSES:
            raise AssertionError(f"Missing scenario status: {value}")
    for value in ["recommended", "use_with_caution", "not_recommended"]:
        if value not in EXPECTED_RECOMMENDATION_LEVELS:
            raise AssertionError(f"Missing expected recommendation level: {value}")

    create = OperationalScenarioTestCreate(**scenario_payload("agency-smoke", "OST-SMOKE-MODEL"))
    record = OperationalScenarioTest(**create.model_dump(mode="json", exclude_none=True))
    if record.scenario_reference != "OST-SMOKE-MODEL" or not record.expected_required_actions:
        raise AssertionError("OperationalScenarioTest model did not preserve scenario metadata.")
    if record.operational_scenario_testing_foundation is not True or record.scenario_execution_disabled is not True:
        raise AssertionError("OperationalScenarioTest model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        OPERATIONAL_SCENARIO_TESTS_COLLECTION,
        "operational_scenario_tests_reference_unique",
        "operational_scenario_tests_agency_status_lookup",
        "operational_scenario_tests_family_lookup",
        "operational_scenario_tests_status_lookup",
        "operational_scenario_tests_airline_lookup",
        "operational_scenario_tests_destination_lookup",
        "operational_scenario_tests_service_code_lookup",
        "operational_scenario_tests_recommendation_level_lookup",
        "operational_scenario_tests_expected_feasibility_lookup",
        "operational_scenario_tests_evidence_lookup",
        "operational_scenario_tests_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/operational-scenario-testing", "get"),
        ("/api/platform/operational-scenario-testing", "post"),
        ("/api/platform/operational-scenario-testing/summary", "get"),
        ("/api/platform/operational-scenario-testing/{scenario_id}", "get"),
        ("/api/platform/operational-scenario-testing/{scenario_id}", "put"),
        ("/api/platform/operational-scenario-testing/{scenario_id}", "delete"),
        ("/api/agencies/{agency_id}/operational-scenario-testing", "get"),
        ("/api/agencies/{agency_id}/operational-scenario-testing/summary", "get"),
        ("/api/agencies/{agency_id}/operational-scenario-testing/{scenario_id}", "get"),
    ]:
        assert_openapi_path(paths, path, method)
    for path, method in [
        ("/api/agencies/{agency_id}/operational-scenario-testing", "post"),
        ("/api/agencies/{agency_id}/operational-scenario-testing/{scenario_id}", "put"),
        ("/api/agencies/{agency_id}/operational-scenario-testing/{scenario_id}", "delete"),
    ]:
        if method in paths.get(path, {}):
            raise AssertionError(f"Agency Scenario Testing must remain read-only: {method.upper()} {path}")
    for path in paths:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")
        if "operational-scenario-testing" in lowered:
            for marker in ["/run", "/execute", "/evaluate-live", "/provider", "/ai"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden scenario execution route registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/operational-scenario-testing"),
        (ROOT / "frontend/src/App.jsx", "/agency/scenario-testing"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Scenario Testing"),
        (ROOT / "frontend/src/pages/platform/OperationalScenarioTestingPage.jsx", "Scenario Test Cases"),
        (ROOT / "frontend/src/pages/agency/ScenarioTestingPage.jsx", "Read-only passenger service scenario metadata"),
        (ROOT / "backend/services/saas_subscription_service.py", "operational_scenario_testing"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Operational Scenario Testing"),
        (ROOT / "docs/architecture/operational-scenario-testing-foundation.md", "Phase 52.8"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_scenario_tests"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/operational-scenario-testing"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operational Scenario Testing"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operational scenario testing"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.8"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Phase 52.8"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Operational Scenario Testing"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.8"),
        (ROOT / "README.md", "operational scenario test records"),
    ]:
        require_text(path, text)


def verify_crud_read_only_and_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]

    reference = run_ref("OST-SMOKE")
    created = post(
        "/api/platform/operational-scenario-testing",
        scenario_payload(agency_id, reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    scenario = created["operational_scenario_test"]
    assert_safety_flags(scenario)
    if scenario.get("scenario_family") != "petc" or scenario.get("airline_context", {}).get("airline_code") != "LH":
        raise AssertionError("Scenario creation did not normalize family or airline metadata.")
    for field in [
        "passenger_context",
        "itinerary_context",
        "airline_context",
        "service_requirements",
        "pets",
        "documents",
        "expected_policy_outcome",
        "expected_pricing_behavior",
        "expected_feasibility",
        "expected_required_actions",
        "evidence_links",
    ]:
        if not scenario.get(field):
            raise AssertionError(f"Scenario missing persisted field {field}.")
    for section in [
        "scenario_section",
        "passenger_context_section",
        "operational_context_section",
        "expected_outcome_section",
        "evidence_section",
        "review_section",
        "boundary_section",
    ]:
        if section not in scenario:
            raise AssertionError(f"Projected scenario missing section {section}.")

    filtered = get(
        "/api/platform/operational-scenario-testing?scenario_family=PETC&test_status=ready_for_review&airline_code=LH&service_code=PETC&expected_recommendation_level=recommended&search=pet_passport",
        OWNER_HEADERS,
    )
    if not any(item.get("scenario_reference") == reference for item in filtered.get("items", [])):
        raise AssertionError("Platform Scenario Testing filters did not return created metadata.")

    summary = get("/api/platform/operational-scenario-testing/summary", OWNER_HEADERS).get("summary") or {}
    if summary.get("operational_scenario_test_count", 0) < 1:
        raise AssertionError("Platform Scenario Testing summary did not count records.")
    if summary.get("service_requirement_count", 0) < 1 or summary.get("evidence_link_count", 0) < 1:
        raise AssertionError("Platform Scenario Testing summary did not count linked scenario metadata.")

    detail = get(f"/api/platform/operational-scenario-testing/{scenario['id']}", OWNER_HEADERS)["operational_scenario_test"]
    if detail.get("scenario_reference") != reference:
        raise AssertionError("Platform Scenario Testing detail did not return created metadata.")

    updated = put(
        f"/api/platform/operational-scenario-testing/{scenario['id']}",
        {"test_status": "reviewed", "review_notes": "Human reviewer confirmed metadata shape."},
        OWNER_HEADERS,
    )["operational_scenario_test"]
    if updated.get("test_status") != "reviewed":
        raise AssertionError("Platform Scenario Testing update did not persist review metadata.")

    agency_list = get(
        f"/api/agencies/{agency_id}/operational-scenario-testing?scenario_family=petc&test_status=reviewed&airline_code=LH&service_code=PETC&expected_recommendation_level=recommended",
        OWNER_HEADERS,
    )
    if agency_list.get("read_only") is not True:
        raise AssertionError("Agency Scenario Testing response must be read-only.")
    if not any(item.get("scenario_reference") == reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency Scenario Testing filters did not return agency-scoped metadata.")

    agency_detail = get(
        f"/api/agencies/{agency_id}/operational-scenario-testing/{scenario['id']}",
        OWNER_HEADERS,
    )
    if agency_detail.get("read_only") is not True:
        raise AssertionError("Agency Scenario Testing detail must be read-only.")
    if agency_detail.get("operational_scenario_test", {}).get("agency_id") != agency_id:
        raise AssertionError("Agency Scenario Testing detail leaked or lost agency scope.")

    agency_summary = get(f"/api/agencies/{agency_id}/operational-scenario-testing/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True:
        raise AssertionError("Agency Scenario Testing summary must be read-only.")

    request("POST", f"/api/agencies/{agency_id}/operational-scenario-testing", scenario_payload(agency_id, "OST-AGENCY-FORBIDDEN"), OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/operational-scenario-testing/{scenario['id']}", {"test_status": "approved"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/operational-scenario-testing/{scenario['id']}", None, OWNER_HEADERS, 405)

    readiness = get("/api/readiness", OWNER_HEADERS)
    section = readiness.get("operational_scenario_testing_foundation") or {}
    for flag in [
        "operational_scenario_testing_enabled",
        "operational_scenario_tests_collection_enabled",
        "platform_operational_scenario_testing_metadata_crud_enabled",
        "agency_operational_scenario_testing_read_only_enabled",
        "scenario_execution_disabled",
        "live_provider_execution_disabled",
        "ai_disabled",
        "automated_test_execution_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if section.get("operational_scenario_service_requirement_count", 0) < 1:
        raise AssertionError("Readiness did not count scenario service requirements.")
    if section.get("operational_scenario_evidence_link_count", 0) < 1:
        raise AssertionError("Readiness did not count scenario evidence links.")
    if section.get("operational_scenario_supported_family_count", 0) < len(SCENARIO_FAMILIES):
        raise AssertionError("Readiness did not expose supported scenario families.")

    archived = request(
        "DELETE",
        f"/api/platform/operational-scenario-testing/{scenario['id']}",
        None,
        OWNER_HEADERS,
        200,
    )[1]
    if archived.get("archived") is not True:
        raise AssertionError("Platform Scenario Testing archive did not return archived metadata.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "operational-scenario-testing" in lowered:
            for marker in ["/run", "/execute", "/evaluate-live", "/provider", "/ai"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden Operational Scenario Testing execution route registered: {path}")

    for path in [
        ROOT / "backend/services/operational_scenario_testing_service.py",
        ROOT / "backend/routers/platform_operational_scenario_testing.py",
        ROOT / "backend/routers/agency_operational_scenario_testing.py",
        ROOT / "frontend/src/pages/platform/OperationalScenarioTestingPage.jsx",
        ROOT / "frontend/src/pages/agency/ScenarioTestingPage.jsx",
    ]:
        for marker in [
            "import requests",
            "import httpx",
            "from openai",
            "import openai",
            "BackgroundTasks",
            "asyncio.create_task(",
            "provider_client =",
            "@router.post(\"/api/platform/operational-scenario-testing/run",
            "@router.post(\"/api/platform/operational-scenario-testing/execute",
            "@router.post(\"/api/agencies/{agency_id}/operational-scenario-testing",
            "@router.put(\"/api/agencies/{agency_id}/operational-scenario-testing",
            "@router.delete(\"/api/agencies/{agency_id}/operational-scenario-testing",
            "@router.get(\"/admin",
            "@router.post(\"/admin",
            "\"/api/admin",
        ]:
            reject_text(path, marker)


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_crud_read_only_and_readiness()
    verify_boundaries()
    print("Operational scenario testing foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Operational scenario testing foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
