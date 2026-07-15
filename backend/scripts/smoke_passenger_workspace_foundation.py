#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import PassengerWorkspace, PassengerWorkspaceCreate, PassengerWorkspaceStatus
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
PASSENGER_STATUSES = {"draft", "active", "incomplete", "review", "ready", "archived"}


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def disabled_flags() -> list[str]:
    return [
        "booking_execution_disabled",
        "ticket_issuance_disabled",
        "gds_connectivity_disabled",
        "gds_live_connectivity_disabled",
        "ndc_connectivity_disabled",
        "payment_processing_disabled",
        "supplier_integrations_disabled",
        "ai_disabled",
        "ai_automation_disabled",
        "email_disabled",
        "email_sending_disabled",
        "sms_disabled",
        "sms_sending_disabled",
        "background_workers_disabled",
        "external_api_calls_disabled",
        "automatic_profile_matching_disabled",
        "automatic_document_validation_disabled",
        "document_validation_disabled",
        "airline_communication_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "booking_execution_enabled",
        "ticket_issuance_enabled",
        "gds_connectivity_enabled",
        "gds_live_connectivity_enabled",
        "ndc_connectivity_enabled",
        "payment_processing_enabled",
        "supplier_integrations_enabled",
        "ai_enabled",
        "ai_automation_enabled",
        "email_enabled",
        "email_sending_enabled",
        "sms_enabled",
        "sms_sending_enabled",
        "background_workers_enabled",
        "external_api_calls_enabled",
        "automatic_profile_matching_enabled",
        "automatic_document_validation_enabled",
        "document_validation_enabled",
        "airline_communication_enabled",
        "automation_enabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")
    for flag in forbidden_enabled_flags():
        if payload.get(flag) is True:
            raise AssertionError(f"Payload exposes forbidden enabled flag {flag}: {payload}")


def verify_model_and_collection_registration() -> None:
    create_payload = PassengerWorkspaceCreate(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        passenger_reference="PXW-SMOKE-MODEL",
        passenger_status=PassengerWorkspaceStatus.ACTIVE,
        title="Ms",
        first_name="Passenger",
        middle_name="Meta",
        last_name="Workspace",
        preferred_name="Pax",
        gender="unspecified",
        date_of_birth="1990-01-05",
        nationality="BG",
        citizenship="BG",
        passport_number="P1234567",
        passport_expiry="2030-01-05",
        passport_country="BG",
        identity_document_type="passport",
        loyalty_programs=[{"program": "Demo Miles", "number": "DM123"}],
        frequent_flyer_numbers=[{"airline": "ZZ", "number": "ZZ123"}],
        known_traveler_numbers=["KTN123"],
        emergency_contact={"name": "Emergency Contact", "phone": "+359888111111"},
        mobility_profile={"profile": "wheelchair", "notes": "WCHR"},
        medical_profile={"notes": "None"},
        dietary_profile={"meal": "vegetarian"},
        assistance_profile={"profile": "wheelchair", "level": "airport"},
        baggage_profile={"checked_bags": "1"},
        seating_preferences={"seat": "aisle"},
        language_preferences=["en", "bg"],
        contact_email="passenger@example.com",
        contact_phone="+359888000000",
        linked_request_ids=["request-smoke"],
        linked_trip_ids=["trip-smoke"],
        linked_offer_ids=["offer-smoke"],
        linked_booking_ids=["booking-smoke"],
        linked_ticket_ids=["ticket-smoke"],
        linked_document_ids=["document-smoke"],
        internal_notes="Metadata-only passenger workspace smoke.",
        metadata={"smoke": True},
    )
    passenger_workspace = PassengerWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = passenger_workspace.model_dump(mode="json")
    if dumped.get("passenger_status") != "active" or dumped.get("nationality") != "BG":
        raise AssertionError(f"Passenger workspace dimensions were not preserved: {dumped}")
    for key in ["metadata_only", "passenger_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Passenger workspace model missing disabled flag {key}: {dumped}")
    if "passenger_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Passenger workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "passenger_workspaces_id_unique",
        "passenger_workspaces_reference_unique",
        "passenger_workspaces_agency_status_lookup",
        "passenger_workspaces_agency_nationality_lookup",
        "passenger_workspaces_agency_citizenship_lookup",
        "passenger_workspaces_operational_workspace_lookup",
        "passenger_workspaces_status_lookup",
        "passenger_workspaces_nationality_lookup",
        "passenger_workspaces_citizenship_lookup",
        "passenger_workspaces_assistance_profile_lookup",
        "passenger_workspaces_date_of_birth_lookup",
        "passenger_workspaces_passport_expiry_lookup",
        "passenger_workspaces_request_lookup",
        "passenger_workspaces_trip_lookup",
        "passenger_workspaces_offer_lookup",
        "passenger_workspaces_booking_lookup",
        "passenger_workspaces_ticket_lookup",
        "passenger_workspaces_document_lookup",
        "passenger_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Passenger workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/passenger-workspaces": {"get", "post"},
        "/api/platform/passenger-workspaces/summary": {"get"},
        "/api/platform/passenger-workspaces/{passenger_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/passenger-workspaces": {"get"},
        "/api/agencies/{agency_id}/passenger-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/passenger-workspaces/{passenger_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/passenger-workspaces",
        "/api/agencies/{agency_id}/passenger-workspaces/summary",
        "/api/agencies/{agency_id}/passenger-workspaces/{passenger_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency passenger workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Passenger Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/passenger-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/passenger-workspaces"),
        (ROOT / "frontend/src/pages/platform/PassengerWorkspacesPage.jsx", "Passenger Workspaces"),
        (ROOT / "frontend/src/pages/platform/PassengerWorkspacesPage.jsx", "No matching or validation"),
        (ROOT / "frontend/src/pages/platform/PassengerWorkspacesPage.jsx", "Travel documents"),
        (ROOT / "frontend/src/pages/agency/PassengerWorkspacesPage.jsx", "Passengers"),
        (ROOT / "frontend/src/pages/agency/PassengerWorkspacesPage.jsx", "Read-only passenger workspace metadata"),
        (ROOT / "docs/architecture/passenger-workspace-foundation.md", "Passenger Workspace Foundation"),
        (ROOT / "README.md", "Phase 41.2 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.2: Passenger Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.2 adds passenger workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.2 adds passenger workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Passenger workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Passenger workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Passenger Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/PassengerWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/PassengerWorkspacesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/PassengerWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/PassengerWorkspacesPage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("passenger_workspace_foundation") or {}
    for flag in [
        "passenger_workspaces_enabled",
        "passenger_workspace_metadata_enabled",
        "platform_passenger_workspace_metadata_crud_enabled",
        "agency_passenger_workspace_read_only_enabled",
        "passenger_workspace_filter_by_status_enabled",
        "passenger_workspace_filter_by_nationality_enabled",
        "passenger_workspace_filter_by_citizenship_enabled",
        "passenger_workspace_filter_by_assistance_profile_enabled",
        "passenger_workspace_filter_by_travel_date_enabled",
        "passenger_workspace_filter_by_operational_workspace_enabled",
        "personal_information_metadata_enabled",
        "travel_document_metadata_enabled",
        "loyalty_membership_metadata_enabled",
        "known_traveler_metadata_enabled",
        "emergency_contact_metadata_enabled",
        "mobility_profile_metadata_enabled",
        "medical_profile_metadata_enabled",
        "dietary_profile_metadata_enabled",
        "assistance_profile_metadata_enabled",
        "baggage_profile_metadata_enabled",
        "seating_preference_metadata_enabled",
        "language_preference_metadata_enabled",
        "linked_request_metadata_enabled",
        "linked_trip_metadata_enabled",
        "linked_offer_metadata_enabled",
        "linked_booking_metadata_enabled",
        "linked_ticket_metadata_enabled",
        "linked_document_metadata_enabled",
        "internal_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "passenger_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "passenger_workspace_count",
        "passenger_workspace_status_counts",
        "passenger_workspace_nationality_count",
        "passenger_workspace_citizenship_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Passenger workspace readiness missing count: {count_key}")
    if not PASSENGER_STATUSES.issubset(set((section.get("passenger_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Passenger workspace readiness status counts missing statuses: {section}")
    previous_section = readiness.get("travel_request_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous travel request workspace section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    workspace_created = post(
        "/api/platform/operational-travel-workspaces",
        {
            "agency_id": agency_id,
            "workspace_title": "Phase 41.2 parent operational workspace smoke",
            "workspace_type": "trip",
            "workspace_status": "open",
            "priority": "high",
            "assigned_team": ["passenger-support"],
            "assigned_agent": "Avery Agent",
            "travel_start_date": "2027-09-10",
            "travel_end_date": "2027-09-20",
            "origin_summary": "SOF",
            "destination_summary": "LHR",
            "service_summary": "Passenger workspace parent metadata",
            "operational_notes": "Metadata-only parent workspace for passenger smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    operational_workspace_id = (workspace_created.get("workspace") or {}).get("id")
    if not operational_workspace_id:
        raise AssertionError(f"Parent operational workspace id missing: {workspace_created}")

    request_created = post(
        "/api/platform/travel-request-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "request_title": "Phase 41.2 linked request workspace smoke",
            "request_type": "flight",
            "request_status": "open",
            "request_priority": "medium",
            "requested_origin": "SOF",
            "requested_destination": "LHR",
            "requested_departure_date": "2027-09-10",
            "requested_return_date": "2027-09-20",
            "passenger_count": 1,
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    linked_request_id = (request_created.get("request_workspace") or {}).get("id") or "request-smoke"

    created = post(
        "/api/platform/passenger-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "passenger_status": "active",
            "title": "Ms",
            "first_name": "Passenger",
            "middle_name": "Meta",
            "last_name": "Workspace",
            "preferred_name": "Pax",
            "gender": "unspecified",
            "date_of_birth": "1990-01-05",
            "nationality": "BG",
            "citizenship": "BG",
            "passport_number": "P1234567",
            "passport_expiry": "2030-01-05",
            "passport_country": "BG",
            "identity_document_type": "passport",
            "loyalty_programs": [{"program": "Demo Miles", "number": "DM123"}],
            "frequent_flyer_numbers": [{"airline": "ZZ", "number": "ZZ123"}],
            "known_traveler_numbers": ["KTN123"],
            "emergency_contact": {"name": "Emergency Contact", "phone": "+359888111111"},
            "mobility_profile": {"profile": "wheelchair", "notes": "WCHR"},
            "medical_profile": {"notes": "No validation performed"},
            "dietary_profile": {"meal": "vegetarian"},
            "assistance_profile": {"profile": "wheelchair", "level": "airport"},
            "baggage_profile": {"checked_bags": "1"},
            "seating_preferences": {"seat": "aisle"},
            "language_preferences": ["en", "bg"],
            "contact_email": "passenger@example.com",
            "contact_phone": "+359888000000",
            "linked_request_ids": [linked_request_id],
            "linked_trip_ids": ["trip-smoke"],
            "linked_offer_ids": ["offer-smoke"],
            "linked_booking_ids": ["booking-smoke"],
            "linked_ticket_ids": ["ticket-smoke"],
            "linked_document_ids": ["document-smoke"],
            "internal_notes": "Metadata-only passenger workspace smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    passenger_workspace = created.get("passenger_workspace") or {}
    assert_passenger_shape(passenger_workspace)
    passenger_workspace_id = passenger_workspace.get("id")
    if not passenger_workspace_id:
        raise AssertionError(f"Passenger workspace id missing: {created}")

    updated = put(
        f"/api/platform/passenger-workspaces/{passenger_workspace_id}",
        {
            "passenger_status": "ready",
            "assistance_profile": {"profile": "wheelchair", "level": "airport", "review": "metadata only"},
            "internal_notes": "Updated metadata only; no matching or document validation.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_passenger = updated.get("passenger_workspace") or {}
    assert_passenger_shape(updated_passenger)
    if updated_passenger.get("passenger_status") != "ready":
        raise AssertionError(f"Passenger workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=ready",
        "nationality=BG",
        "citizenship=BG",
        "assistance_profile=wheelchair",
        "travel_date=2027-09-15",
        f"operational_workspace_id={operational_workspace_id}",
    ]:
        filtered = get(f"/api/platform/passenger-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == passenger_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Passenger workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/passenger-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/passenger-workspaces/{passenger_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_passenger_shape(platform_detail.get("passenger_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/passenger-workspaces?status=ready&nationality=BG", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency passenger workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == passenger_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency passenger workspace list missing created record: {agency_list}")
    assert_passenger_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/passenger-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency passenger workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/passenger-workspaces/{passenger_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency passenger workspace detail should be read-only: {agency_detail}")
    assert_passenger_shape(agency_detail.get("passenger_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/passenger-workspaces/{passenger_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("passenger_workspace") or {}).get("passenger_status") != "archived":
        raise AssertionError(f"Passenger workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/passenger-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == passenger_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default passenger workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/passenger-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == passenger_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived passenger workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/passenger-workspaces", {"first_name": "Blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/passenger-workspaces/{passenger_workspace_id}", {"passenger_status": "active"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/passenger-workspaces/{passenger_workspace_id}", {}, OWNER_HEADERS, 405)


def assert_passenger_shape(passenger_workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "passenger_reference",
        "passenger_status",
        "title",
        "first_name",
        "middle_name",
        "last_name",
        "preferred_name",
        "gender",
        "date_of_birth",
        "nationality",
        "citizenship",
        "passport_number",
        "passport_expiry",
        "passport_country",
        "identity_document_type",
        "loyalty_programs",
        "frequent_flyer_numbers",
        "known_traveler_numbers",
        "emergency_contact",
        "mobility_profile",
        "medical_profile",
        "dietary_profile",
        "assistance_profile",
        "baggage_profile",
        "seating_preferences",
        "language_preferences",
        "contact_email",
        "contact_phone",
        "linked_request_ids",
        "linked_trip_ids",
        "linked_offer_ids",
        "linked_booking_ids",
        "linked_ticket_ids",
        "linked_document_ids",
        "internal_notes",
        "display_name",
        "operational_workspace",
        "linked_requests",
        "linked_trips",
        "linked_offers",
        "linked_bookings",
        "linked_tickets",
        "linked_documents",
    ]:
        if key not in passenger_workspace:
            raise AssertionError(f"Passenger workspace missing {key}: {passenger_workspace}")
    if passenger_workspace.get("metadata_only") is not True or passenger_workspace.get("passenger_workspace_metadata_only") is not True:
        raise AssertionError(f"Passenger workspace is not metadata-only: {passenger_workspace}")
    if agency_view and passenger_workspace.get("read_only") is not True:
        raise AssertionError(f"Agency passenger workspace should be read-only: {passenger_workspace}")
    for flag in disabled_flags():
        if passenger_workspace.get(flag) is not True:
            raise AssertionError(f"Passenger workspace missing disabled flag {flag}: {passenger_workspace}")
    if not passenger_workspace.get("linked_requests") or not passenger_workspace.get("linked_bookings") or not passenger_workspace.get("linked_documents"):
        raise AssertionError(f"Passenger workspace linked metadata shape missing references: {passenger_workspace}")
    if not passenger_workspace.get("operational_workspace"):
        raise AssertionError(f"Passenger workspace missing operational workspace context: {passenger_workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary not scoped to agency: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_status",
        "by_nationality",
        "by_citizenship",
        "agency_count",
        "operational_workspace_count",
        "assistance_profile_count",
        "linked_request_count",
        "linked_trip_count",
        "linked_offer_count",
        "linked_booking_count",
        "linked_ticket_count",
        "linked_document_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"Passenger workspace summary missing {key}: {payload}")
    if not PASSENGER_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Passenger workspace summary missing statuses: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.2 passenger workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
