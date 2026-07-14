#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import RequestTripConversionIssue, RequestTripConversionPlan, RequestTripConversionRun, RequestTripEntityMapping
from services.request_to_trip_conversion_service import (
    CONVERSION_MAPPING_TYPES,
    PHASE_LABEL,
    REQUEST_TRIP_CONVERSION_ISSUES_COLLECTION,
    REQUEST_TRIP_CONVERSION_PLANS_COLLECTION,
    REQUEST_TRIP_CONVERSION_RUNS_COLLECTION,
    REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_55_4_airline_service_coverage_gap_management_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8").lower()
    if text.lower() in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "request_to_trip_operational_conversion_foundation",
        "request_remains_intake_origin",
        "trip_becomes_operational_shell",
        "never_use_request_id_as_trip_id",
        "source_snapshots_preserved",
        "idempotent_safe_retry_enabled",
        "booking_execution_disabled",
        "ticketing_disabled",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "background_workers_disabled",
        "automatic_production_seeding_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Missing conversion safety flag {flag}: {payload}")


def request_payload(reference: str, *, critical: bool = False) -> dict:
    if critical:
        return {
            "client": {"name": f"Conversion Critical {reference}", "email": f"{reference}@example.com", "phone": "+421900054501"},
            "segments": [
                {
                    "segment_key": "seg-1",
                    "sequence": 1,
                    "origin_text": "Sofia",
                    "destination_text": "Frankfurt",
                    "departure_date": "2026-12-14",
                }
            ],
            "title": "Phase 54.5 critical conversion request",
            "status": "new",
            "priority": "urgent",
            "source": "staff_created",
        }
    return {
        "client": {"name": f"Conversion Client {reference}", "email": f"{reference}@example.com", "phone": "+421900054502"},
        "passengers": [
            {
                "request_passenger_key": "pax-1",
                "first_name": "Conversion",
                "last_name": "Traveler",
                "passenger_type": "adult",
                "mobility_notes": "Segment precision should produce warning only.",
            }
        ],
        "trip_type": "round_trip",
        "segments": [
            {
                "segment_key": "seg-1",
                "sequence": 1,
                "origin_text": "Sofia",
                "destination_text": "Frankfurt",
                "departure_date": "2026-12-14",
                "marketing_airline": "LH",
                "operating_airline": "LH",
                "flight_number": "LH1703",
                "cabin_preference": "economy",
            },
            {
                "segment_key": "seg-2",
                "sequence": 2,
                "origin_text": "Frankfurt",
                "destination_text": "Sofia",
                "departure_date": "2026-12-21",
                "marketing_airline": "LH",
                "operating_airline": "LH",
                "flight_number": "LH1704",
                "cabin_preference": "economy",
            },
        ],
        "services": [
            {
                "category": "mobility_assistance",
                "service_code": "WCHR",
                "details": {"notes": "Conversion smoke wheelchair service."},
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
            }
        ],
        "pets": [
            {
                "pet_key": "pet-1",
                "request_passenger_key": "pax-1",
                "pet_name": "Scout",
                "species": "dog",
                "requested_transport_mode": "petc",
                "segment_transports": [
                    {"segment_key": "seg-1", "requested_transport_mode": "petc"},
                    {"segment_key": "seg-2", "requested_transport_mode": "petc"},
                ],
            }
        ],
        "special_items": [
            {
                "item_key": "item-1",
                "request_passenger_key": "pax-1",
                "item_category_code": "musical_instrument",
                "item_name": "Violin",
                "description": "Cabin violin case",
                "transport_location": "passenger_cabin",
                "segment_transports": [{"segment_key": "seg-1", "transport_location": "passenger_cabin"}],
            }
        ],
        "title": "Phase 54.5 request-to-trip conversion request",
        "status": "new",
        "priority": "urgent",
        "source": "staff_created",
        "internal_notes": "Conversion smoke internal notes.",
        "client_visible_notes": "Conversion smoke client notes.",
    }


def create_request(agency_id: str, *, critical: bool = False) -> dict:
    reference = run_ref("request-trip-conversion").lower()
    return post(f"/api/agencies/{agency_id}/requests/builder", request_payload(reference, critical=critical), AGENCY_AGENT_HEADERS, 201)["request"]


def ensure_second_agency(existing_agencies: list[dict]) -> str:
    if len(existing_agencies) > 1:
        return existing_agencies[1]["id"]
    slug = run_ref("request-trip-conversion-smoke-agency").lower()
    created = post(
        "/api/agencies",
        {
            "name": "Request Trip Conversion Smoke Isolation Agency",
            "slug": slug,
            "legal_name": "Request Trip Conversion Smoke Isolation Agency Ltd",
            "status": "active",
            "subscription_status": "trial",
            "default_currency": "EUR",
            "country": "BG",
            "timezone": "UTC",
        },
        OWNER_HEADERS,
        201,
    )
    return created["agency"]["id"]


def validate_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service PHASE_LABEL mismatch: {PHASE_LABEL}")
    for collection in [
        REQUEST_TRIP_CONVERSION_PLANS_COLLECTION,
        REQUEST_TRIP_CONVERSION_RUNS_COLLECTION,
        REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION,
        REQUEST_TRIP_CONVERSION_ISSUES_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Missing agency-owned collection registration: {collection}")
        require_text(ROOT / "backend/database.py", collection)
    model_samples = [
        RequestTripConversionPlan(agency_id="agency", plan_reference="plan", request_id="request", idempotency_key="key"),
        RequestTripConversionRun(agency_id="agency", run_reference="run", request_id="request", idempotency_key="key"),
        RequestTripEntityMapping(
            agency_id="agency",
            run_id="run",
            request_id="request",
            trip_id="trip",
            mapping_type="request_segment_to_trip_segment",
            source_entity_type="request_segment",
            source_entity_id="segment",
            target_entity_type="trip_segment",
            target_entity_id="trip-segment",
        ),
        RequestTripConversionIssue(agency_id="agency", request_id="request", issue_code="warning", title="warning"),
    ]
    for model_sample in model_samples:
        dumped = model_sample.model_dump()
        if dumped.get("metadata_only") is not True or dumped.get("request_to_trip_operational_conversion_foundation") is not True:
            raise AssertionError(f"Model missing metadata flags: {model_sample.__class__.__name__}")
    paths = get("/openapi.json").get("paths") or {}
    for path, method in [
        ("/api/platform/request-trip-conversion", "get"),
        ("/api/platform/request-trip-conversion/plans", "get"),
        ("/api/platform/request-trip-conversion/runs", "get"),
        ("/api/platform/request-trip-conversion/mappings", "get"),
        ("/api/platform/request-trip-conversion/issues", "get"),
        ("/api/agencies/{agency_id}/request-trip-conversion", "get"),
        ("/api/agencies/{agency_id}/request-trip-conversion/preview", "post"),
        ("/api/agencies/{agency_id}/request-trip-conversion/validate", "post"),
        ("/api/agencies/{agency_id}/request-trip-conversion/execute", "post"),
        ("/api/agencies/{agency_id}/request-trip-conversion/plans", "get"),
        ("/api/agencies/{agency_id}/request-trip-conversion/runs", "get"),
        ("/api/agencies/{agency_id}/request-trip-conversion/mappings", "get"),
        ("/api/agencies/{agency_id}/request-trip-conversion/issues", "get"),
    ]:
        assert_openapi_path(paths, path, method)
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/agency/request-trip-conversion"),
        (ROOT / "frontend/src/App.jsx", "/platform/request-trip-conversion"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Request-to-Trip Conversion"),
        (ROOT / "backend/services/saas_subscription_service.py", "request_trip_conversion"),
        (ROOT / "docs/architecture/request-to-trip-operational-conversion-foundation.md", "A request id must never be reused as a trip id"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/agencies/{agency_id}/request-trip-conversion"),
        (ROOT / "docs/architecture/current-model-inventory.md", "request_trip_conversion_runs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Request-to-trip operational conversion"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Request-to-Trip Operational Conversion"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "RequestTripConversionRun"),
    ]:
        require_text(path, text)
    service_text = (ROOT / "backend/services/request_to_trip_conversion_service.py").read_text(encoding="utf-8")
    for rejected in ["requests.get(", "urllib.request", "openai", "BackgroundTasks", "send_email", "send_sms", "stripe"]:
        if rejected.lower() in service_text.lower():
            raise AssertionError(f"Forbidden execution semantic found in request-to-trip service: {rejected}")
    reject_text(ROOT / "frontend/src/App.jsx", "/admin/request-trip-conversion")
    reject_text(ROOT / "frontend/src/App.jsx", "/agent/request-trip-conversion")


def validate_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("request_to_trip_operational_conversion_foundation") or {}
    for flag in [
        "request_to_trip_operational_conversion_enabled",
        "conversion_preview_enabled",
        "critical_validation_enabled",
        "safe_warning_conversion_enabled",
        "new_trip_creation_enabled",
        "explicit_existing_trip_attachment_enabled",
        "idempotency_enabled",
        "source_request_snapshot_preservation_enabled",
        "request_id_as_trip_id_forbidden",
        "workflow_start_metadata_enabled",
        "task_generation_integration_enabled",
        "deadline_generation_integration_enabled",
        "timeline_event_integration_enabled",
        "metadata_only",
        "booking_execution_disabled",
        "ticketing_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "automatic_production_seeding_disabled",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing conversion flag {flag}: {section}")
    for previous_section in [
        "operational_workflow_orchestration_foundation",
        "agent_work_queue_assignment_foundation",
        "sla_operational_deadline_engine_foundation",
        "task_automation_dependency_orchestration_foundation",
    ]:
        if previous_section not in readiness:
            raise AssertionError(f"Previous readiness section missing after Phase 54.5: {previous_section}")


def validate_conversion_flow(agency_id: str, other_agency_id: str) -> None:
    critical_request = create_request(agency_id, critical=True)
    critical_execute = post(
        f"/api/agencies/{agency_id}/request-trip-conversion/execute",
        {"request_id": critical_request["id"], "idempotency_key": run_ref("critical-conversion")},
        AGENCY_AGENT_HEADERS,
    )
    if not critical_execute.get("conversion_blocked") or critical_execute["run"].get("run_status") != "blocked":
        raise AssertionError("Critical conversion did not produce blocked run metadata.")
    if not critical_execute.get("validation", {}).get("critical_issues"):
        raise AssertionError("Critical conversion did not record critical issues.")

    conversion_request = create_request(agency_id)
    before_detail = get(f"/api/agencies/{agency_id}/requests/{conversion_request['id']}", AGENCY_AGENT_HEADERS)
    post(f"/api/agencies/{agency_id}/requests/{conversion_request['id']}/offer-workspace", {}, AGENCY_AGENT_HEADERS, 201)
    idempotency_key = run_ref("conversion-key")
    preview = post(
        f"/api/agencies/{agency_id}/request-trip-conversion/preview",
        {"request_id": conversion_request["id"], "idempotency_key": idempotency_key},
        AGENCY_AGENT_HEADERS,
    )
    assert_safety_flags(preview)
    if preview.get("validation", {}).get("summary", {}).get("can_execute") is not True:
        raise AssertionError("Valid conversion preview should be executable.")
    if not preview.get("validation", {}).get("warnings"):
        raise AssertionError("Warning conversion preview should include unresolved/missing-data warnings.")

    validated = post(
        f"/api/agencies/{agency_id}/request-trip-conversion/validate",
        {"request_id": conversion_request["id"], "idempotency_key": f"{idempotency_key}:validate"},
        AGENCY_AGENT_HEADERS,
    )
    if validated.get("validation_only") is not True:
        raise AssertionError("Validation endpoint did not mark validation_only.")

    executed = post(
        f"/api/agencies/{agency_id}/request-trip-conversion/execute",
        {"request_id": conversion_request["id"], "idempotency_key": idempotency_key},
        AGENCY_AGENT_HEADERS,
    )
    assert_safety_flags(executed)
    trip = executed.get("trip") or {}
    run = executed.get("run") or {}
    if not trip.get("id") or trip["id"] == conversion_request["id"]:
        raise AssertionError("Conversion failed to create a distinct trip dossier shell.")
    if run.get("run_status") != "executed":
        raise AssertionError(f"Expected executed run status, got {run.get('run_status')}")

    after_detail = get(f"/api/agencies/{agency_id}/requests/{conversion_request['id']}", AGENCY_AGENT_HEADERS)
    for field in ["id", "request_reference", "title", "client_id", "route_summary", "service_summary"]:
        if before_detail["request"].get(field) != after_detail["request"].get(field):
            raise AssertionError(f"Immutable request origin field changed during conversion: {field}")
    if after_detail["request"].get("trip_id") != trip["id"]:
        raise AssertionError("Request was not linked to the converted trip metadata.")

    trip_detail = get(f"/api/agencies/{agency_id}/trips/{trip['id']}", AGENCY_AGENT_HEADERS)
    if len(trip_detail.get("passengers") or []) < 1 or len(trip_detail.get("segments") or []) < 2 or len(trip_detail.get("services") or []) < 1:
        raise AssertionError("Converted trip did not receive passenger, segment, and service metadata.")

    mapping_types = {item.get("mapping_type") for item in executed.get("mappings") or []}
    for expected_type in [
        "request_passenger_to_trip_passenger",
        "request_segment_to_trip_segment",
        "request_service_to_trip_service",
        "pet_applicability_carry_forward",
        "special_item_applicability_carry_forward",
        "request_offer_linkage",
    ]:
        if expected_type not in mapping_types:
            raise AssertionError(f"Conversion mapping missing {expected_type}: {mapping_types}")
    if not set(mapping_types).issubset(set(CONVERSION_MAPPING_TYPES)):
        raise AssertionError(f"Unexpected mapping type returned: {mapping_types}")

    result_snapshot = run.get("result_snapshot_json") or {}
    for key in ["workflow_instance_id", "task_automation_run_id", "deadline_id"]:
        if not result_snapshot.get(key):
            raise AssertionError(f"Conversion result missing integration reference {key}: {result_snapshot}")
    workflow_events = get(f"/api/agencies/{agency_id}/operational-workflows/instances/{result_snapshot['workflow_instance_id']}/events", AGENCY_AGENT_HEADERS)["events"]
    if not any(event.get("event_code") == "request_trip_conversion_started_trip_workflow" for event in workflow_events):
        raise AssertionError("Workflow start event was not recorded for conversion.")
    deadline = get(f"/api/agencies/{agency_id}/deadlines/{result_snapshot['deadline_id']}", AGENCY_AGENT_HEADERS)["deadline"]
    if deadline.get("source_entity_id") != trip["id"]:
        raise AssertionError("Conversion deadline is not linked to the converted trip.")
    work_queue = get(f"/api/agencies/{agency_id}/work-queue?{urlencode({'include_completed': 'true'})}", AGENCY_AGENT_HEADERS)
    if not work_queue.get("items"):
        raise AssertionError("Conversion did not leave work queue metadata through task/deadline integration.")
    request_timeline = get(f"/api/agencies/{agency_id}/requests/{conversion_request['id']}/timeline", AGENCY_AGENT_HEADERS)["items"]
    if not any(item.get("event_type") == "request_trip_conversion_executed" for item in request_timeline):
        raise AssertionError("Request timeline did not record conversion event.")

    reused = post(
        f"/api/agencies/{agency_id}/request-trip-conversion/execute",
        {"request_id": conversion_request["id"], "idempotency_key": idempotency_key},
        AGENCY_AGENT_HEADERS,
    )
    if reused.get("idempotent_reused") is not True or (reused.get("trip") or {}).get("id") != trip["id"]:
        raise AssertionError("Idempotent conversion retry did not reuse the original run/trip.")

    second_request = create_request(agency_id)
    manual_trip = post(
        f"/api/agencies/{agency_id}/trips",
        {
            "primary_client_id": second_request["client_id"],
            "trip_title": "Explicit existing trip conversion smoke",
            "trip_status": "draft",
            "trip_type": "round_trip",
            "route_summary": "SOF-FRA",
        },
        AGENCY_AGENT_HEADERS,
        201,
    )["trip"]
    attached = post(
        f"/api/agencies/{agency_id}/request-trip-conversion/execute",
        {"request_id": second_request["id"], "existing_trip_id": manual_trip["id"], "idempotency_key": run_ref("existing-trip-conversion")},
        AGENCY_AGENT_HEADERS,
    )
    if (attached.get("trip") or {}).get("id") != manual_trip["id"]:
        raise AssertionError("Explicit existing-trip attachment did not use selected trip.")
    if attached.get("run", {}).get("conversion_mode") != "existing_trip":
        raise AssertionError("Existing-trip conversion mode was not recorded.")

    agency_dashboard = get(f"/api/agencies/{agency_id}/request-trip-conversion", AGENCY_AGENT_HEADERS)
    if agency_dashboard.get("summary", {}).get("run_count", 0) < 2:
        raise AssertionError("Agency dashboard did not include conversion runs.")
    platform_dashboard = get(f"/api/platform/request-trip-conversion?{urlencode({'agency_id': agency_id})}", OWNER_HEADERS)
    if platform_dashboard.get("summary", {}).get("mapping_count", 0) < len(executed.get("mappings") or []):
        raise AssertionError("Platform diagnostics did not include conversion mappings.")
    request("GET", f"/api/platform/request-trip-conversion", None, AGENCY_AGENT_HEADERS, expect=403)
    request("GET", f"/api/agencies/{other_agency_id}/request-trip-conversion", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> int:
    validate_static_contracts()
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS)["items"]
    if not agencies:
        raise AssertionError("No agency available for request-to-trip conversion smoke.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)
    validate_readiness()
    validate_conversion_flow(agency_id, other_agency_id)
    print("Request-to-trip operational conversion foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Request-to-trip operational conversion foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
