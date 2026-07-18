#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS
from models import BookingExecutionInstruction, OfferBookingHandoff, OfferBookingHandoffCheck, OfferBookingHandoffMapping
from services.offer_to_booking_handoff_service import (
    BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION,
    BOOKING_MODES,
    HANDOFF_CHECK_STATUSES,
    HANDOFF_MAPPING_TYPES,
    HANDOFF_STATUSES,
    OFFER_BOOKING_HANDOFF_CHECKS_COLLECTION,
    OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION,
    OFFER_BOOKING_HANDOFFS_COLLECTION,
    PHASE_LABEL,
    OfferToBookingHandoffService,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_acceptance_booking_readiness import builder_payload, create_priced_option


from phase_assertions import application_phase_is_at_least


MINIMUM_PHASE = "phase_54_6_offer_to_booking_handoff_readiness_foundation"
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
        "offer_to_booking_handoff_readiness_foundation",
        "accepted_offer_snapshot_required",
        "mutable_offer_reconstruction_disabled",
        "booking_execution_disabled",
        "provider_execution_disabled",
        "ticket_issuance_disabled",
        "payment_processing_disabled",
        "external_api_calls_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Missing offer-to-booking handoff safety flag {flag}: {payload}")


def assert_no_forbidden_execution_text() -> None:
    service_path = ROOT / "backend/services/offer_to_booking_handoff_service.py"
    for forbidden in [
        "requests.get(",
        "requests.post(",
        "httpx.",
        "urllib.request",
        "openai",
        "stripe",
        "send_email",
        "send_sms",
        "BackgroundTasks",
        "asyncio.create_task",
    ]:
        reject_text(service_path, forbidden)


def assert_status_calculation() -> None:
    service = OfferToBookingHandoffService.__new__(OfferToBookingHandoffService)
    if service._status_from_checks([{"status": "passed"}]) != "ready":
        raise AssertionError("Ready handoff state calculation failed.")
    if service._status_from_checks([{"status": "warning"}]) != "conditional":
        raise AssertionError("Conditional handoff state calculation failed.")
    if service._status_from_checks([{"status": "blocked"}]) != "blocked":
        raise AssertionError("Blocked handoff state calculation failed.")


def verify_static_contracts() -> None:
    if not application_phase_is_at_least(PHASE_LABEL, MINIMUM_PHASE):
        raise AssertionError(f"Service PHASE_LABEL mismatch: {PHASE_LABEL}")
    for collection in [
        OFFER_BOOKING_HANDOFFS_COLLECTION,
        OFFER_BOOKING_HANDOFF_CHECKS_COLLECTION,
        OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION,
        BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Missing agency-owned collection registration: {collection}")
        require_text(ROOT / "backend/database.py", collection)
    for index_name in [
        "offer_booking_handoffs_reference_unique",
        "offer_booking_handoffs_agency_idempotency_lookup",
        "offer_booking_handoff_checks_agency_status_lookup",
        "offer_booking_handoff_mappings_agency_type_lookup",
        "booking_execution_instructions_reference_unique",
    ]:
        require_text(ROOT / "backend/database.py", index_name)
    for status in ["draft", "assessing", "blocked", "conditional", "ready", "handed_off", "booking_created", "failed", "cancelled"]:
        if status not in HANDOFF_STATUSES:
            raise AssertionError(f"Missing handoff status: {status}")
    for status in ["pending", "passed", "warning", "blocked"]:
        if status not in HANDOFF_CHECK_STATUSES:
            raise AssertionError(f"Missing handoff check status: {status}")
    for mapping_type in [
        "accepted_offer_to_readiness",
        "passenger_to_booking_passenger",
        "segment_to_booking_segment",
        "service_to_booking_service",
        "pricing_trace_to_booking",
        "handoff_to_booking_workspace",
    ]:
        if mapping_type not in HANDOFF_MAPPING_TYPES:
            raise AssertionError(f"Missing handoff mapping type: {mapping_type}")
    for mode in ["manual", "pnr_import", "imported_gds", "imported_confirmation", "supplier_reference"]:
        if mode not in BOOKING_MODES:
            raise AssertionError(f"Missing booking mode: {mode}")
    samples = [
        OfferBookingHandoff(agency_id="agency", handoff_reference="OBH-SMOKE", idempotency_key="agency:acceptance:readiness:manual"),
        OfferBookingHandoffCheck(agency_id="agency", handoff_id="handoff", check_key="accepted_offer_snapshot", label="Accepted offer snapshot"),
        OfferBookingHandoffMapping(
            agency_id="agency",
            handoff_id="handoff",
            mapping_type="passenger_to_booking_passenger",
            source_entity_type="accepted_offer_passenger",
            source_entity_id="pax-1",
            target_entity_type="booking_passenger_snapshot",
            target_entity_id="pax-1",
        ),
        BookingExecutionInstruction(agency_id="agency", handoff_id="handoff", instruction_reference="BXI-SMOKE", title="Instruction metadata"),
    ]
    for sample in samples:
        dumped = sample.model_dump(mode="json")
        if dumped.get("metadata_only") is not True or dumped.get("offer_to_booking_handoff_readiness_foundation") is not True:
            raise AssertionError(f"Model missing metadata-only handoff flags: {dumped}")
    assert_status_calculation()
    assert_no_forbidden_execution_text()
    offer_detail_text = (ROOT / "frontend/src/pages/agency/OfferWorkspaceDetailPage.jsx").read_text(encoding="utf-8")
    if "booking-workspaces/from-readiness" in offer_detail_text:
        raise AssertionError("Primary Offer UI still bypasses the canonical booking handoff.")
    if "/agency/booking-handoffs" not in offer_detail_text or "Continue to booking handoff" not in offer_detail_text:
        raise AssertionError("Primary Offer UI does not direct accepted offers through the booking handoff.")
    booking_router_text = (ROOT / "backend/routers/agency_booking_workspaces.py").read_text(encoding="utf-8")
    if "compatibility_only" not in booking_router_text:
        raise AssertionError("Legacy readiness-to-booking endpoint is not marked compatibility-only.")
    booking_service_text = (ROOT / "backend/services/booking_workspace_service.py").read_text(encoding="utf-8")
    if "Booking creation requires the immutable accepted-offer snapshot" not in booking_service_text:
        raise AssertionError("Compatibility booking creation does not require immutable acceptance evidence.")


def verify_routes_and_docs(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    for path, methods in {
        "/api/platform/booking-handoffs": {"get"},
        "/api/platform/booking-handoffs/summary": {"get"},
        "/api/platform/booking-handoffs/checks": {"get"},
        "/api/platform/booking-handoffs/mappings": {"get"},
        "/api/platform/booking-handoffs/instructions": {"get"},
        "/api/platform/booking-handoffs/{handoff_id}": {"get"},
        "/api/agencies/{agency_id}/booking-handoffs": {"get", "post"},
        "/api/agencies/{agency_id}/booking-handoffs/checks": {"get"},
        "/api/agencies/{agency_id}/booking-handoffs/mappings": {"get"},
        "/api/agencies/{agency_id}/booking-handoffs/instructions": {"get"},
        "/api/agencies/{agency_id}/booking-handoffs/{handoff_id}": {"get"},
        "/api/agencies/{agency_id}/booking-handoffs/{handoff_id}/assess": {"post"},
        "/api/agencies/{agency_id}/booking-handoffs/{handoff_id}/create-booking-workspace": {"post"},
    }.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    platform_methods = set(paths.get("/api/platform/booking-handoffs", {}).keys())
    if platform_methods & {"post", "put", "patch", "delete"}:
        raise AssertionError(f"Platform handoff diagnostics should be read-only at root: {platform_methods}")
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/agency/booking-handoffs"),
        (ROOT / "frontend/src/App.jsx", "/platform/booking-handoffs"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Booking Handoffs"),
        (ROOT / "frontend/src/pages/agency/BookingHandoffsPage.jsx", "Accepted-offer to booking readiness metadata"),
        (ROOT / "frontend/src/pages/platform/BookingHandoffDiagnosticsPage.jsx", "Read-only platform visibility"),
        (ROOT / "frontend/src/pages/agency/OfferBuilderPage.jsx", "Booking Handoff"),
        (ROOT / "frontend/src/pages/agency/TripDetailPage.jsx", "Open booking handoff"),
        (ROOT / "docs/architecture/offer-to-booking-handoff-readiness-foundation.md", "Offer-to-Booking Handoff and Booking Readiness Foundation"),
        (ROOT / "README.md", "Phase 54.6 adds the metadata-only Offer-to-Booking Handoff"),
        (ROOT / "BUILD_PHASES.md", "Phase 54.6: Offer-to-booking handoff and booking readiness foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "offer_booking_handoffs"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 54.6 adds offer-to-booking handoff APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Offer-to-booking handoff readiness"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Offer-to-Booking Handoff Readiness"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Frozen Accepted Offer Snapshot"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Offer-to-Booking Handoff Readiness"),
    ]:
        require_text(path, text)


def verify_readiness() -> None:
    health = get("/api/health")
    if not application_phase_is_at_least(health.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if not application_phase_is_at_least(readiness.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_to_booking_handoff_readiness_foundation") or {}
    for flag in [
        "offer_to_booking_handoff_enabled",
        "accepted_offer_snapshot_usage_enabled",
        "mutable_offer_reconstruction_disabled",
        "booking_readiness_package_reuse_enabled",
        "readiness_checklist_enabled",
        "internal_client_trace_separation_enabled",
        "duplicate_handoff_prevention_enabled",
        "booking_workspace_link_creation_enabled",
        "workflow_integration_enabled",
        "work_queue_integration_enabled",
        "task_automation_integration_enabled",
        "deadline_integration_enabled",
        "timeline_integration_enabled",
        "booking_execution_disabled",
        "provider_execution_disabled",
        "ticket_issuance_disabled",
        "payment_processing_disabled",
        "external_api_calls_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing handoff flag {flag}: {section}")
    for key in [
        "handoff_statuses",
        "handoff_check_statuses",
        "handoff_mapping_types",
        "booking_modes",
        "booking_instruction_types",
        "offer_booking_handoff_count",
        "offer_booking_handoff_check_count",
        "offer_booking_handoff_mapping_count",
        "booking_execution_instruction_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing handoff key {key}: {section}")


def create_acceptance_fixture(agency_id: str) -> tuple[dict, dict]:
    email = f"phase546.{int(time.time())}@example.com"
    created_request = post(f"/api/agencies/{agency_id}/requests/builder", builder_payload(email), OWNER_HEADERS, 201)
    request_id = created_request["request"]["id"]
    workspace = post(f"/api/agencies/{agency_id}/requests/{request_id}/offer-workspace", {}, OWNER_HEADERS, 201)["workspace"]
    option = create_priced_option(agency_id, workspace["id"])
    accepted = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}/options/{option['id']}/accept",
        {"acceptance_source": "internal", "provider_target": "manual"},
        OWNER_HEADERS,
        201,
    )
    acceptance = accepted.get("acceptance") or {}
    readiness = accepted.get("booking_readiness") or {}
    if acceptance.get("status") != "accepted":
        raise AssertionError(f"Accepted offer was not accepted: {accepted}")
    if not readiness.get("id"):
        raise AssertionError(f"Accepted offer did not produce booking readiness metadata: {accepted}")
    if not accepted.get("trip_snapshot"):
        raise AssertionError("Accepted offer did not produce a trip accepted-offer snapshot.")
    return acceptance, readiness


def ensure_second_agency() -> str:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if len(agencies) > 1:
        return agencies[1]["id"]
    slug = run_ref("booking-handoff-isolation").lower()
    return post(
        "/api/agencies",
        {
            "name": "Booking Handoff Isolation Smoke Agency",
            "slug": slug,
            "legal_name": "Booking Handoff Isolation Smoke Agency Ltd",
            "status": "active",
            "subscription_status": "trial",
            "default_currency": "EUR",
            "country": "BG",
            "timezone": "UTC",
        },
        OWNER_HEADERS,
        201,
    )["agency"]["id"]


def verify_handoff_flow() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    acceptance, readiness = create_acceptance_fixture(agency_id)

    build_payload = {
        "acceptance_id": acceptance["id"],
        "booking_readiness_package_id": readiness["id"],
        "booking_mode": "manual",
        "notes": "Phase 54.6 smoke handoff.",
        "metadata": {"smoke": True},
    }
    created = post(f"/api/agencies/{agency_id}/booking-handoffs", build_payload, OWNER_HEADERS, 201)
    assert_safety_flags(created)
    handoff = created.get("handoff") or {}
    checks = created.get("checks") or []
    mappings = created.get("mappings") or []
    instructions = created.get("instructions") or []
    if handoff.get("handoff_status") not in {"ready", "conditional"}:
        raise AssertionError(f"Expected ready or conditional handoff, got {handoff.get('handoff_status')}: {created}")
    if handoff.get("accepted_offer_snapshot_json", {}).get("captured_from_frozen_acceptance") is not True:
        raise AssertionError(f"Handoff did not preserve frozen accepted snapshot: {handoff}")
    if handoff.get("accepted_offer_snapshot_json", {}).get("mutable_offer_reconstruction_disabled") is not True:
        raise AssertionError("Handoff did not disable mutable offer reconstruction.")
    if handoff.get("client_trace_json", {}).get("internal_notes_excluded") is not True:
        raise AssertionError("Client trace did not exclude internal notes.")
    if not handoff.get("internal_trace_json", {}).get("checks"):
        raise AssertionError("Internal trace did not keep readiness checks.")
    required_check_keys = {
        "accepted_offer_snapshot",
        "trip_linkage",
        "booking_readiness_package",
        "passenger_mapping",
        "segment_mapping",
        "pricing_resolution",
        "policy_evaluation",
        "passenger_service_feasibility",
        "documents_and_approvals",
        "booking_mode",
    }
    check_keys = {item.get("check_key") for item in checks}
    missing_checks = required_check_keys - check_keys
    if missing_checks:
        raise AssertionError(f"Handoff missing checks: {sorted(missing_checks)}")
    required_mapping_types = {"accepted_offer_to_readiness", "passenger_to_booking_passenger", "segment_to_booking_segment", "service_to_booking_service", "pricing_trace_to_booking"}
    mapping_types = {item.get("mapping_type") for item in mappings}
    missing_mappings = required_mapping_types - mapping_types
    if missing_mappings:
        raise AssertionError(f"Handoff missing mappings: {sorted(missing_mappings)}")
    if not instructions or instructions[0].get("manual_execution_required") is not True:
        raise AssertionError(f"Handoff did not create manual booking instruction metadata: {instructions}")
    integrations = created.get("integrations") or {}
    for key in ["workflow_instance_id", "workflow_event_id", "work_item_id", "deadline_id", "timeline_entry_id"]:
        if not integrations.get(key):
            raise AssertionError(f"Handoff missing integration {key}: {integrations}")

    duplicate = post(f"/api/agencies/{agency_id}/booking-handoffs", build_payload, OWNER_HEADERS, 201)
    if duplicate.get("idempotent_reused") is not True:
        raise AssertionError(f"Duplicate handoff was not idempotently reused: {duplicate}")
    if duplicate.get("handoff", {}).get("id") != handoff.get("id"):
        raise AssertionError("Duplicate handoff did not return the original handoff id.")

    blocked = post(
        f"/api/agencies/{agency_id}/booking-handoffs",
        {
            "trip_id": f"missing-trip-{run_ref('phase546')}",
            "booking_mode": "manual",
            "idempotency_key": run_ref("blocked-handoff"),
            "metadata": {"smoke_blocked": True},
        },
        OWNER_HEADERS,
        201,
    )
    if blocked.get("handoff", {}).get("handoff_status") != "blocked":
        raise AssertionError(f"Blocked handoff state was not produced: {blocked}")

    detail = get(f"/api/agencies/{agency_id}/booking-handoffs/{handoff['id']}", OWNER_HEADERS)
    if detail.get("handoff", {}).get("id") != handoff["id"]:
        raise AssertionError(f"Agency detail did not return handoff: {detail}")
    list_response = get(
        f"/api/agencies/{agency_id}/booking-handoffs?{urlencode({'acceptance_id': acceptance['id']})}",
        OWNER_HEADERS,
    )
    if not any(item.get("id") == handoff["id"] for item in list_response.get("items") or []):
        raise AssertionError("Agency list did not include handoff.")
    checks_response = get(f"/api/agencies/{agency_id}/booking-handoffs/checks?handoff_id={handoff['id']}", OWNER_HEADERS)
    if len(checks_response.get("items") or []) < len(required_check_keys):
        raise AssertionError("Agency checks endpoint did not return handoff checks.")
    platform_response = get(f"/api/platform/booking-handoffs?{urlencode({'agency_id': agency_id})}", OWNER_HEADERS)
    if not any(item.get("id") == handoff["id"] for item in platform_response.get("items") or []):
        raise AssertionError("Platform diagnostics did not include handoff.")
    request("POST", "/api/platform/booking-handoffs", {}, OWNER_HEADERS, 405)

    second_agency_id = ensure_second_agency()
    if second_agency_id != agency_id:
        try:
            status, _ = request("GET", f"/api/agencies/{second_agency_id}/booking-handoffs/{handoff['id']}", None, AGENCY_AGENT_HEADERS, 403)
        except AssertionError:
            status, _ = request("GET", f"/api/agencies/{second_agency_id}/booking-handoffs/{handoff['id']}", None, AGENCY_AGENT_HEADERS, 404)
        if status not in {403, 404}:
            raise AssertionError(f"Agency isolation failed for handoff detail, got {status}.")

    booking_created = post(
        f"/api/agencies/{agency_id}/booking-handoffs/{handoff['id']}/create-booking-workspace",
        {"provider_target": "manual", "booking_mode": "manual", "internal_notes": "Phase 54.6 metadata-only booking workspace creation."},
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(booking_created)
    if not booking_created.get("booking_workspace", {}).get("id"):
        raise AssertionError(f"Booking workspace metadata was not created: {booking_created}")
    if booking_created.get("handoff", {}).get("handoff_status") != "booking_created":
        raise AssertionError(f"Handoff was not marked booking_created: {booking_created}")
    reused_booking = post(
        f"/api/agencies/{agency_id}/booking-handoffs/{handoff['id']}/create-booking-workspace",
        {"provider_target": "manual", "booking_mode": "manual"},
        OWNER_HEADERS,
        201,
    )
    if reused_booking.get("idempotent_reused") is not True:
        raise AssertionError(f"Booking workspace duplicate creation was not idempotent: {reused_booking}")


def main() -> int:
    verify_static_contracts()
    openapi = get("/openapi.json")
    verify_routes_and_docs(openapi.get("paths") or {})
    verify_readiness()
    verify_handoff_flow()
    print("Offer-to-booking handoff readiness foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Offer-to-booking handoff readiness foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
