#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    ClientMasterRecord,
    ClientMasterRecordCreate,
    ClientPassengerMasterLink,
    ClientPortalAccessProfile,
    PassengerKnownDocument,
    PassengerMasterRecord,
    PassengerMasterRecordCreate,
    PassengerOperationalPreference,
    PassengerServiceHistoryRecord,
)
from services.client_passenger_master_service import (
    CLIENT_MASTER_RECORDS_COLLECTION,
    CLIENT_PASSENGER_LINKS_COLLECTION,
    CLIENT_PORTAL_ACCESS_PROFILES_COLLECTION,
    MASTER_COLLECTIONS,
    PASSENGER_KNOWN_DOCUMENTS_COLLECTION,
    PASSENGER_MASTER_RECORDS_COLLECTION,
    PASSENGER_OPERATIONAL_PREFERENCES_COLLECTION,
    PASSENGER_SERVICE_HISTORY_COLLECTION,
    PHASE_LABEL,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_7_servicing_after_sales_workflow_foundation"
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


def assert_disabled_response(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "client_passenger_master_foundation",
        "client_is_commercial_owner",
        "passenger_is_operational_identity",
        "many_to_many_relationships_supported",
        "passenger_history_reusable",
        "crm_sales_pipeline_disabled",
        "marketing_automation_disabled",
        "provider_integrations_disabled",
        "ai_llm_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "payment_gateway_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def client_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "client_master_reference": reference,
        "client_status": "active",
        "client_version": "51.3.0-smoke",
        "source_client_profile_id": "CLIENT-PROFILE-SMOKE-513",
        "commercial_owner_type": "individual",
        "profile": {"display_name": "Phase 51.3 Client", "primary_email": "client513@example.com"},
        "contacts": [{"name": "Client Contact", "email": "client513@example.com", "role": "owner"}],
        "portal_status": "active",
        "permissions": {"can_view_passenger_documents": True, "can_request_travel": True},
        "linked_passenger_ids": ["PXM-SMOKE-513"],
        "request_ids": ["REQ-SMOKE-513"],
        "trip_ids": ["TRIP-SMOKE-513"],
        "offer_ids": ["OFFER-SMOKE-513"],
        "invoice_ids": ["INV-SMOKE-513"],
        "communication_ids": ["COMM-SMOKE-513"],
        "document_ids": ["DOC-SMOKE-513"],
        "relationship_graph": [{"passenger_master_record_id": "PXM-SMOKE-513", "relationship_type": "self"}],
        "client_overview": {"commercial_owner": True, "summary": "Commercial owner for smoke passenger."},
        "internal_notes": "Metadata-only client master smoke.",
        "agent_notes": "Human authority remains final.",
        "metadata": {"smoke": True, "phase": "51.3"},
    }


def passenger_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "passenger_master_reference": reference,
        "passenger_status": "active",
        "passenger_version": "51.3.0-smoke",
        "source_passenger_profile_id": "PASSENGER-PROFILE-SMOKE-513",
        "operational_profile": {"display_name": "Phase 51.3 Passenger", "passenger_type": "ADT"},
        "service_history_ids": ["PSH-SMOKE-513"],
        "mobility_profile": {"wheelchair": "WCHR"},
        "medical_profile": {"medif_required": False},
        "pets": [{"species": "dog", "service_code": "PETC"}],
        "special_items": [{"item_category": "musical_instrument"}],
        "document_ids": ["DOC-SMOKE-513"],
        "trip_ids": ["TRIP-SMOKE-513"],
        "booking_ids": ["BKG-SMOKE-513"],
        "ticket_ids": ["TKT-SMOKE-513"],
        "emd_ids": ["EMD-SMOKE-513"],
        "operational_evaluation_ids": ["OKE-SMOKE-513"],
        "feasibility_ids": ["PSF-SMOKE-513"],
        "recommendation_ids": ["ARE-SMOKE-513"],
        "preferred_airlines": ["LH", "OS"],
        "preferred_cabins": ["Economy"],
        "preferred_seats": ["aisle"],
        "relationship_graph": [{"client_master_record_id": "CLM-SMOKE-513", "relationship_type": "self"}],
        "passenger_overview": {"operational_identity": True, "summary": "Reusable operational beneficiary."},
        "internal_notes": "Passenger history is reusable metadata only.",
        "agent_notes": "Review before client presentation.",
        "metadata": {"smoke": True, "phase": "51.3"},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    for collection in MASTER_COLLECTIONS:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"{collection} is not registered as agency-owned metadata.")

    client_create = ClientMasterRecordCreate(**client_payload("agency-smoke", "CLM-SMOKE-MODEL"))
    client_record = ClientMasterRecord(**client_create.model_dump(mode="json", exclude_none=True))
    if client_record.client_master_reference != "CLM-SMOKE-MODEL" or not client_record.linked_passenger_ids:
        raise AssertionError("Client master model did not preserve relationship metadata.")
    if client_record.client_is_commercial_owner is not True or client_record.crm_sales_pipeline_disabled is not True:
        raise AssertionError("Client master model did not preserve metadata-only safety flags.")

    passenger_create = PassengerMasterRecordCreate(**passenger_payload("agency-smoke", "PXM-SMOKE-MODEL"))
    passenger_record = PassengerMasterRecord(**passenger_create.model_dump(mode="json", exclude_none=True))
    if passenger_record.passenger_master_reference != "PXM-SMOKE-MODEL" or not passenger_record.operational_evaluation_ids:
        raise AssertionError("Passenger master model did not preserve reusable operational history.")
    if passenger_record.passenger_is_operational_identity is not True or passenger_record.payment_gateway_disabled is not True:
        raise AssertionError("Passenger master model did not preserve disabled payment/automation flags.")

    link = ClientPassengerMasterLink(
        link_reference="CPL-SMOKE-MODEL",
        agency_id="agency-smoke",
        client_master_record_id="CLM-SMOKE-MODEL",
        passenger_master_record_id="PXM-SMOKE-MODEL",
    )
    history = PassengerServiceHistoryRecord(
        history_reference="PSH-SMOKE-MODEL",
        agency_id="agency-smoke",
        passenger_master_record_id="PXM-SMOKE-MODEL",
        service_family="mobility",
        service_code="WCHR",
        ssr_code="WCHR",
    )
    preference = PassengerOperationalPreference(
        preference_reference="POP-SMOKE-MODEL",
        agency_id="agency-smoke",
        passenger_master_record_id="PXM-SMOKE-MODEL",
        preferred_airlines=["LH"],
    )
    document = PassengerKnownDocument(
        document_reference="PKD-SMOKE-MODEL",
        agency_id="agency-smoke",
        passenger_master_record_id="PXM-SMOKE-MODEL",
        document_type="passport",
    )
    portal = ClientPortalAccessProfile(
        portal_access_reference="CPA-SMOKE-MODEL",
        agency_id="agency-smoke",
        client_master_record_id="CLM-SMOKE-MODEL",
        contact_email="portal513@example.com",
    )
    for record, field in [
        (link, "client_master_record_id"),
        (history, "passenger_master_record_id"),
        (preference, "preferred_airlines"),
        (document, "document_type"),
        (portal, "client_master_record_id"),
    ]:
        if not getattr(record, field):
            raise AssertionError(f"Child metadata model did not preserve {field}.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        CLIENT_MASTER_RECORDS_COLLECTION,
        PASSENGER_MASTER_RECORDS_COLLECTION,
        CLIENT_PASSENGER_LINKS_COLLECTION,
        PASSENGER_SERVICE_HISTORY_COLLECTION,
        PASSENGER_OPERATIONAL_PREFERENCES_COLLECTION,
        PASSENGER_KNOWN_DOCUMENTS_COLLECTION,
        CLIENT_PORTAL_ACCESS_PROFILES_COLLECTION,
        "client_master_records_reference_unique",
        "passenger_master_records_reference_unique",
        "client_passenger_links_client_master_lookup",
        "passenger_service_history_passenger_master_lookup",
        "passenger_operational_preferences_passenger_master_lookup",
        "passenger_known_documents_passenger_master_lookup",
        "client_portal_access_profiles_client_master_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths", {})
    for path, method in [
        ("/api/platform/client-master", "get"),
        ("/api/platform/client-master", "post"),
        ("/api/platform/client-master/{record_id}", "get"),
        ("/api/platform/client-master/{record_id}", "put"),
        ("/api/platform/client-master/{record_id}", "delete"),
        ("/api/platform/passenger-master", "get"),
        ("/api/platform/passenger-master", "post"),
        ("/api/platform/passenger-master/{record_id}", "get"),
        ("/api/platform/passenger-master/{record_id}", "put"),
        ("/api/platform/passenger-master/{record_id}", "delete"),
        ("/api/platform/client-passenger-links", "post"),
        ("/api/platform/passenger-service-history", "post"),
        ("/api/platform/passenger-operational-preferences", "post"),
        ("/api/platform/passenger-known-documents", "post"),
        ("/api/platform/client-portal-access-profiles", "post"),
        ("/api/agencies/{agency_id}/client-master", "get"),
        ("/api/agencies/{agency_id}/client-master", "post"),
        ("/api/agencies/{agency_id}/client-master/{record_id}", "get"),
        ("/api/agencies/{agency_id}/client-master/{record_id}", "put"),
        ("/api/agencies/{agency_id}/client-master/{record_id}", "delete"),
        ("/api/agencies/{agency_id}/passenger-master", "get"),
        ("/api/agencies/{agency_id}/passenger-master", "post"),
        ("/api/agencies/{agency_id}/passenger-master/{record_id}", "get"),
        ("/api/agencies/{agency_id}/passenger-master/{record_id}", "put"),
        ("/api/agencies/{agency_id}/passenger-master/{record_id}", "delete"),
        ("/api/agencies/{agency_id}/client-passenger-links", "post"),
        ("/api/agencies/{agency_id}/passenger-service-history", "post"),
        ("/api/agencies/{agency_id}/passenger-operational-preferences", "post"),
        ("/api/agencies/{agency_id}/passenger-known-documents", "post"),
        ("/api/agencies/{agency_id}/client-portal-access-profiles", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/client-master"),
        (ROOT / "frontend/src/App.jsx", "/platform/passenger-master"),
        (ROOT / "frontend/src/App.jsx", "/agency/clients"),
        (ROOT / "frontend/src/App.jsx", "/agency/passengers"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Client Master"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Passenger Master"),
        (ROOT / "frontend/src/components/ClientPassengerMasterRecordList.jsx", "Client Overview"),
        (ROOT / "frontend/src/components/ClientPassengerMasterRecordList.jsx", "Passenger Overview"),
        (ROOT / "frontend/src/components/ClientPassengerMasterRecordList.jsx", "Service History"),
        (ROOT / "frontend/src/components/ClientPassengerMasterRecordList.jsx", "Known Operational Profile"),
        (ROOT / "frontend/src/components/ClientPassengerMasterRecordList.jsx", "Known Preferences"),
        (ROOT / "frontend/src/components/ClientPassengerMasterRecordList.jsx", "Portal Access"),
        (ROOT / "frontend/src/components/ClientPassengerMasterRecordList.jsx", "Relationship Graph"),
        (ROOT / "docs/architecture/client-passenger-master-workspace-foundation.md", "Phase 51.3 is metadata-only"),
        (ROOT / "docs/architecture/current-model-inventory.md", "client_master_records"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/client-master"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 51.3 implements metadata-only Client & Passenger Master Workspace Consolidation"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 51.3"),
        (ROOT / "README.md", "metadata-only client/passenger master workspace records"),
    ]:
        require_text(path, text)

    for path in [
        ROOT / "frontend/src/pages/platform/ClientMasterPage.jsx",
        ROOT / "frontend/src/pages/platform/PassengerMasterPage.jsx",
        ROOT / "frontend/src/pages/agency/ClientMasterPage.jsx",
        ROOT / "frontend/src/pages/agency/PassengerMasterPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")
        reject_text(path, "apiDelete")
        for forbidden in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, forbidden)


def verify_runtime_metadata() -> None:
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    ref = run_ref("513")
    client = post(
        "/api/platform/client-master",
        client_payload(agency_id, f"CLM-SMOKE-{ref}"),
        OWNER_HEADERS,
        expect=201,
    )
    assert_disabled_response(client)
    client_record = client["client_master_record"]
    client_id = client_record["id"]

    passenger = post(
        "/api/platform/passenger-master",
        passenger_payload(agency_id, f"PXM-SMOKE-{ref}"),
        OWNER_HEADERS,
        expect=201,
    )
    assert_disabled_response(passenger)
    passenger_record = passenger["passenger_master_record"]
    passenger_id = passenger_record["id"]
    if passenger_record["service_history_section"]["passenger_history_reusable"] is not True:
        raise AssertionError(f"Passenger reusable history metadata missing: {passenger_record}")

    link = post(
        "/api/platform/client-passenger-links",
        {
            "agency_id": agency_id,
            "link_reference": f"CPL-SMOKE-{ref}",
            "client_master_record_id": client_id,
            "passenger_master_record_id": passenger_id,
            "relationship_type": "self",
            "permissions": {"can_view": True},
            "request_ids": ["REQ-SMOKE-513"],
            "trip_ids": ["TRIP-SMOKE-513"],
            "document_ids": ["DOC-SMOKE-513"],
        },
        OWNER_HEADERS,
        expect=201,
    )
    assert_disabled_response(link)

    history = post(
        "/api/platform/passenger-service-history",
        {
            "agency_id": agency_id,
            "history_reference": f"PSH-SMOKE-{ref}",
            "passenger_master_record_id": passenger_id,
            "service_family": "mobility",
            "service_code": "WCHR",
            "ssr_code": "WCHR",
            "request_ids": ["REQ-SMOKE-513"],
            "trip_ids": ["TRIP-SMOKE-513"],
            "booking_ids": ["BKG-SMOKE-513"],
            "ticket_ids": ["TKT-SMOKE-513"],
            "emd_ids": ["EMD-SMOKE-513"],
            "operational_evaluation_ids": ["OKE-SMOKE-513"],
            "feasibility_ids": ["PSF-SMOKE-513"],
            "recommendation_ids": ["ARE-SMOKE-513"],
            "evidence_trace": [{"source": "human_review"}],
        },
        OWNER_HEADERS,
        expect=201,
    )
    assert_disabled_response(history)

    preference = post(
        "/api/platform/passenger-operational-preferences",
        {
            "agency_id": agency_id,
            "preference_reference": f"POP-SMOKE-{ref}",
            "passenger_master_record_id": passenger_id,
            "preferred_airlines": ["LH"],
            "preferred_cabins": ["Economy"],
            "preferred_seats": ["aisle"],
        },
        OWNER_HEADERS,
        expect=201,
    )
    assert_disabled_response(preference)

    known_document = post(
        "/api/platform/passenger-known-documents",
        {
            "agency_id": agency_id,
            "document_reference": f"PKD-SMOKE-{ref}",
            "passenger_master_record_id": passenger_id,
            "document_type": "passport",
            "document_name": "Passport smoke metadata",
            "document_ids": ["DOC-SMOKE-513"],
            "verification_status": "needs_review",
        },
        OWNER_HEADERS,
        expect=201,
    )
    assert_disabled_response(known_document)

    portal = post(
        "/api/platform/client-portal-access-profiles",
        {
            "agency_id": agency_id,
            "portal_access_reference": f"CPA-SMOKE-{ref}",
            "client_master_record_id": client_id,
            "portal_status": "active",
            "contact_email": "portal513@example.com",
            "display_name": "Portal Smoke",
            "linked_passenger_ids": [passenger_id],
            "visible_request_ids": ["REQ-SMOKE-513"],
            "visible_trip_ids": ["TRIP-SMOKE-513"],
            "visible_document_ids": ["DOC-SMOKE-513"],
        },
        OWNER_HEADERS,
        expect=201,
    )
    if portal.get("metadata_only") is not True or portal.get("human_authority_final") is not True:
        raise AssertionError(f"Portal access profile response missing metadata flags: {portal}")

    updated_client = put(
        f"/api/platform/client-master/{client_id}",
        {"client_status": "needs_review", "agent_notes": "Updated by smoke."},
        OWNER_HEADERS,
    )["client_master_record"]
    if updated_client["client_status"] != "needs_review" or updated_client["agent_notes"] != "Updated by smoke.":
        raise AssertionError(f"Platform client update did not persist metadata: {updated_client}")

    updated_passenger = put(
        f"/api/platform/passenger-master/{passenger_id}",
        {"preferred_airlines": ["LH", "OS", "LX"], "passenger_status": "needs_review"},
        OWNER_HEADERS,
    )["passenger_master_record"]
    if "LX" not in updated_passenger["preferred_airlines"] or updated_passenger["passenger_status"] != "needs_review":
        raise AssertionError(f"Platform passenger update did not persist metadata: {updated_passenger}")

    platform_clients = get(f"/api/platform/client-master?agency_id={agency_id}&passenger=PXM-SMOKE-513", OWNER_HEADERS)
    if not any(item["id"] == client_id for item in platform_clients.get("items", [])):
        raise AssertionError(f"Platform client filters did not return created record: {platform_clients}")

    platform_passengers = get(f"/api/platform/passenger-master?agency_id={agency_id}&service=pet", OWNER_HEADERS)
    if not any(item["id"] == passenger_id for item in platform_passengers.get("items", [])):
        raise AssertionError(f"Platform passenger filters did not return created record: {platform_passengers}")

    agency_client = post(
        f"/api/agencies/{agency_id}/client-master",
        client_payload(agency_id, f"CLM-AGENCY-SMOKE-{ref}"),
        OWNER_HEADERS,
        expect=201,
    )["client_master_record"]
    agency_passenger = post(
        f"/api/agencies/{agency_id}/passenger-master",
        passenger_payload(agency_id, f"PXM-AGENCY-SMOKE-{ref}"),
        OWNER_HEADERS,
        expect=201,
    )["passenger_master_record"]
    if agency_client["agency_id"] != agency_id or agency_passenger["agency_id"] != agency_id:
        raise AssertionError("Agency master create did not preserve agency scope.")

    agency_update = put(
        f"/api/agencies/{agency_id}/client-master/{agency_client['id']}",
        {"client_status": "in_review"},
        OWNER_HEADERS,
    )["client_master_record"]
    if agency_update["client_status"] != "in_review":
        raise AssertionError(f"Agency client update did not persist metadata: {agency_update}")

    request("DELETE", f"/api/agencies/{agency_id}/passenger-master/{agency_passenger['id']}", None, OWNER_HEADERS)
    archived = request("DELETE", f"/api/platform/client-master/{client_id}", None, OWNER_HEADERS)[1]["client_master_record"]
    if archived["client_status"] != "archived" or archived["archived"] is not True:
        raise AssertionError(f"Platform archive did not soft-archive client master metadata: {archived}")

    health = get("/api/health", OWNER_HEADERS)
    readiness = get("/api/readiness", OWNER_HEADERS)
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"health phase mismatch: {health.get('phase')}")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"readiness phase mismatch: {readiness.get('phase')}")
    section = readiness.get("client_passenger_master_workspace_foundation")
    if not section:
        raise AssertionError(f"readiness missing client/passenger master readiness section: {readiness}")
    if section.get("client_master_records_collection_enabled") is not True or section.get("passenger_master_records_collection_enabled") is not True:
        raise AssertionError(f"readiness missing collection flags: {section}")
    if section.get("client_master_record_count", 0) < 1 or section.get("passenger_master_record_count", 0) < 1:
        raise AssertionError(f"readiness did not report persisted master metadata counts: {section}")
    if section.get("passenger_history_reusable") is not True or section.get("human_authority_final") is not True:
        raise AssertionError(f"readiness missing safety boundary flags: {section}")

    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Client Passenger Master Workspace" not in str(adoption):
        raise AssertionError(f"Blueprint adoption missing client passenger master foundation: {adoption}")
    for supplementary, agencyos in [
        ("/admin/client-master", "/platform/client-master"),
        ("/admin/passenger-master", "/platform/passenger-master"),
        ("/agent/clients", "/agency/clients"),
        ("/agent/passengers", "/agency/passengers"),
    ]:
        if not any(item.get("supplementary") == supplementary and item.get("agencyos") == agencyos for item in route_policy.get("route_mappings", [])):
            raise AssertionError(f"Route policy missing mapping {supplementary} -> {agencyos}: {route_policy}")
    if "Client passenger master workspace foundation built in Phase 51.3" not in str(gaps):
        raise AssertionError(f"Gap summary missing Phase 51.3 marker: {gaps}")


def verify_no_forbidden_execution_surfaces() -> None:
    for path in [
        ROOT / "backend/services/client_passenger_master_service.py",
        ROOT / "backend/routers/platform_client_passenger_master.py",
        ROOT / "backend/routers/agency_client_passenger_master.py",
        ROOT / "frontend/src/pages/platform/ClientMasterPage.jsx",
        ROOT / "frontend/src/pages/platform/PassengerMasterPage.jsx",
        ROOT / "frontend/src/pages/agency/ClientMasterPage.jsx",
        ROOT / "frontend/src/pages/agency/PassengerMasterPage.jsx",
    ]:
        for forbidden in [
            "BackgroundTasks",
            "asyncio.create_task",
            "httpx",
            "requests.",
            "urllib.",
            "openai",
            "ChatCompletion",
            "provider_client",
            "create_booking",
            "issue_ticket",
            "issue_emd",
            "charge_card",
            "stripe.",
        ]:
            reject_text(path, forbidden)


def main() -> None:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_runtime_metadata()
    verify_no_forbidden_execution_surfaces()
    print("Phase 51.3 client passenger master workspace foundation smoke passed.")


if __name__ == "__main__":
    main()
