#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from models import (  # noqa: E402
    AirlineIntelligenceProfile,
    AirlineRulesCore,
    PassengerServiceRequest,
    UnifiedExceptionRule,
)


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
EXPECTED_PHASE = "phase_39_3_airline_intelligence_agency_consumption_bridge"


def request(method: str, path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", method=method, data=data, headers={**(headers or {}), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            payload = response.read().decode("utf-8")
            status = response.status
            result = json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        status = exc.code
        result = json.loads(payload) if payload else {}
    if expect is not None and status != expect:
        raise AssertionError(f"{method} {path} expected {expect}, got {status}: {result}")
    if expect is None and status >= 400:
        raise AssertionError(f"{method} {path} failed with {status}: {result}")
    return status, result


def get(path: str, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("GET", path, None, headers, expect)[1]


def post(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("POST", path, body or {}, headers, expect)[1]


def put(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PUT", path, body or {}, headers, expect)[1]


def builder_payload(email: str) -> dict:
    return {
        "client": {"name": "Phase 36 Services Client", "email": email, "phone": "+421900000036"},
        "passengers": [{"first_name": "Policy", "last_name": "Traveler", "passenger_type": "adult"}],
        "trip_type": "one_way",
        "segments": [
            {
                "sequence": 1,
                "origin_text": "SOF",
                "destination_text": "FRA",
                "departure_date": "2026-11-15",
                "marketing_airline": "LH",
                "operating_airline": "LH",
                "flight_number": "LH1703",
            }
        ],
        "services": [
            {
                "category": "mobility_assistance",
                "service_code": "WCHR",
                "details": {"confirmed_ssr_code": "WCHR"},
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
            }
        ],
        "title": "Phase 36 rules services smoke",
        "status": "new",
        "priority": "normal",
        "source": "staff_created",
    }


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def main() -> int:
    for model in [AirlineIntelligenceProfile, AirlineRulesCore, UnifiedExceptionRule, PassengerServiceRequest]:
        if not getattr(model, "model_fields", None):
            raise AssertionError(f"Model import failed for {model.__name__}")

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    assert_openapi_path(paths, "/api/platform/airline-intelligence/airlines", "get")
    assert_openapi_path(paths, "/api/platform/rules-services/airlines/{airline_id}/rules", "put")
    assert_openapi_path(paths, "/api/platform/rules-services/simulate", "post")
    assert_openapi_path(paths, "/api/agencies/{agency_id}/requests/{request_id}/special-services", "post")
    assert_openapi_path(paths, "/api/agencies/{agency_id}/special-services/{service_id}/generate-ssr-osi", "post")

    readiness = get("/api/readiness")
    rules_readiness = readiness.get("rules_and_services") or {}
    for key in [
        "rules_services_registry_enabled",
        "airline_rules_core_enabled",
        "exception_engine_enabled",
        "ssr_osi_generator_enabled",
        "passenger_service_requests_enabled",
        "platform_rules_services_console_enabled",
        "agency_special_services_workspace_enabled",
    ]:
        if rules_readiness.get(key) is not True:
            raise AssertionError(f"Readiness missing rules/services flag: {key}")
    for legacy_section in ["reference_data", "platform_reference_console", "trip_dossiers"]:
        if not readiness.get(legacy_section):
            raise AssertionError(f"Readiness missing legacy section: {legacy_section}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    airlines = get("/api/platform/airlines", OWNER_HEADERS)["items"]
    if not airlines:
        raise AssertionError("No platform airline available for rules smoke.")
    airline = next((item for item in airlines if item.get("airline_code") == "NX"), airlines[0])
    airline_id = airline["id"]
    iata_code = airline["airline_code"]

    profile = put(
        f"/api/platform/airline-intelligence/airlines/{airline_id}",
        {
            "airline_id": airline_id,
            "iata_code": iata_code,
            "legal_name": airline["airline_name"],
            "base_country": airline["country"],
            "governance_status": "draft",
        },
        OWNER_HEADERS,
    )["profile"]
    if profile.get("iata_code") != iata_code:
        raise AssertionError("Airline intelligence profile upsert did not persist IATA code.")

    rules = put(
        f"/api/platform/rules-services/airlines/{airline_id}/rules",
        {
            "airline_id": airline_id,
            "iata_code": iata_code,
            "prm_rules_json": {"wheelchair_codes": ["WCHR", "WCHS", "WCHC"]},
            "medical_rules_json": {"medif_required": True},
            "pets_service_animals_rules_json": {"documents_required": True},
            "general_notes": "Phase 36 smoke create.",
            "governance_status": "draft",
        },
        OWNER_HEADERS,
    )["rules"]
    updated_rules = put(
        f"/api/platform/rules-services/airlines/{airline_id}/rules",
        {
            "airline_id": airline_id,
            "iata_code": iata_code,
            "prm_rules_json": rules.get("prm_rules_json") or {},
            "medical_rules_json": rules.get("medical_rules_json") or {},
            "pets_service_animals_rules_json": rules.get("pets_service_animals_rules_json") or {},
            "general_notes": "Phase 36 smoke update.",
            "governance_status": "published",
        },
        OWNER_HEADERS,
    )["rules"]
    if updated_rules["general_notes"] != "Phase 36 smoke update.":
        raise AssertionError("AirlineRulesCore update did not persist.")

    rule = post(
        "/api/platform/rules-services/exception-rules",
        {
            "category": "PRM",
            "airline_id": airline_id,
            "iata_code": iata_code,
            "condition_expression": {"path": "service_type", "equals": "WCHR"},
            "action": "WARN",
            "required_documents_json": [],
            "notes": "Smoke PRM manual verification warning.",
            "priority": 5,
            "active": True,
        },
        OWNER_HEADERS,
        201,
    )["rule"]
    listed_rules = get(f"/api/platform/rules-services/exception-rules?category=PRM&airline_id={airline_id}", OWNER_HEADERS)["items"]
    if rule["id"] not in {item["id"] for item in listed_rules}:
        raise AssertionError("Created exception rule was not listed.")

    simulation = post(
        "/api/platform/rules-services/simulate",
        {
            "airline_id": airline_id,
            "iata_code": iata_code,
            "route_origin": "SOF",
            "route_destination": "FRA",
            "service_category": "PRM",
            "service_type": "WCHR",
            "service_payload_json": {"notes": "Needs wheelchair for distance."},
        },
        OWNER_HEADERS,
    )
    if "rules_fired" not in simulation or "warnings" not in simulation or "ssr_preview" not in simulation:
        raise AssertionError("Simulator response did not include structured rules/SSR output.")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    created_request = post(f"/api/agencies/{agency_id}/requests/builder", builder_payload(f"phase36.{int(time.time())}@example.com"), OWNER_HEADERS, 201)
    request_id = created_request["request"]["id"]
    detail = get(f"/api/agencies/{agency_id}/requests/{request_id}", OWNER_HEADERS)
    segment_id = detail["segments"][0]["id"]
    passenger_id = detail["passengers"][0]["id"]

    service = post(
        f"/api/agencies/{agency_id}/requests/{request_id}/special-services",
        {
            "passenger_id": passenger_id,
            "segment_id": segment_id,
            "category": "PRM",
            "service_type": "WCHR",
            "metadata_json": {"notes": "Needs wheelchair for distance.", "iata_code": iata_code},
        },
        OWNER_HEADERS,
        201,
    )["service"]
    request_services = get(f"/api/agencies/{agency_id}/requests/{request_id}/special-services", OWNER_HEADERS)["items"]
    if service["id"] not in {item["id"] for item in request_services}:
        raise AssertionError("PassengerServiceRequest was not listed for request.")
    evaluated = post(f"/api/agencies/{agency_id}/special-services/{service['id']}/evaluate", {}, OWNER_HEADERS)
    if "allowed" not in evaluated.get("result", {}):
        raise AssertionError("Special service evaluation result missing allowed.")
    generated = post(f"/api/agencies/{agency_id}/special-services/{service['id']}/generate-ssr-osi", {}, OWNER_HEADERS)
    if "ssr" not in generated.get("result", {}):
        raise AssertionError("Special service SSR/OSI generation missing SSR list.")

    trip = post(f"/api/agencies/{agency_id}/trips/from-request/{request_id}", {}, OWNER_HEADERS, 201)["trip"]
    trip_service = post(
        f"/api/agencies/{agency_id}/trips/{trip['id']}/special-services",
        {"category": "MEDICAL", "service_type": "MEDIF", "metadata_json": {"iata_code": iata_code, "medical_text": "MEDIF required"}},
        OWNER_HEADERS,
        201,
    )["service"]
    trip_generated = post(f"/api/agencies/{agency_id}/trips/{trip['id']}/generate-ssr-osi", {}, OWNER_HEADERS)
    if trip_service["id"] not in {item["service"]["id"] for item in trip_generated.get("items", [])}:
        raise AssertionError("Trip SSR/OSI generation did not process the trip service.")

    put(f"/api/platform/rules-services/airlines/{airline_id}/rules", {"general_notes": "Agency should fail."}, AGENCY_AGENT_HEADERS, 403)

    print("Rules and Services foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Rules and Services foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
