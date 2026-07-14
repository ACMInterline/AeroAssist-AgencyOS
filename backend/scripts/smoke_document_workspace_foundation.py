#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import DocumentWorkspace, DocumentWorkspaceCreate, DocumentWorkspaceStatus, DocumentWorkspaceType
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_8_airline_contact_communication_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_STATUSES = {
    "draft_metadata",
    "required",
    "requested",
    "received",
    "under_review",
    "verified",
    "rejected",
    "expired",
    "waived",
    "not_required",
    "archived",
}
DOCUMENT_TYPES = {
    "itinerary",
    "booking_confirmation",
    "ticket_receipt",
    "emd_receipt",
    "invoice",
    "voucher",
    "medif",
    "medical_certificate",
    "veterinary_certificate",
    "pet_passport",
    "battery_declaration",
    "mobility_aid_form",
    "unaccompanied_minor_form",
    "consent_form",
    "visa_document",
    "passport_copy",
    "assistance_confirmation",
    "airline_approval",
    "airport_handling_confirmation",
    "service_instruction",
    "other",
}


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
        "live_document_delivery_disabled",
        "e_signature_disabled",
        "public_share_links_disabled",
        "automatic_pdf_generation_disabled",
        "payment_invoice_generation_disabled",
        "external_storage_integrations_disabled",
        "background_workers_disabled",
        "ai_document_generation_disabled",
        "automation_disabled",
        "phase_36_5_document_foundation_not_duplicated",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "live_document_delivery_enabled",
        "e_signature_enabled",
        "public_share_links_enabled",
        "automatic_pdf_generation_enabled",
        "payment_invoice_generation_enabled",
        "external_storage_integrations_enabled",
        "background_workers_enabled",
        "ai_document_generation_enabled",
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


def document_payload(agency_id: str, reference: str = "DOCW-SMOKE-ENDPOINT") -> dict:
    return {
        "agency_id": agency_id,
        "operational_workspace_id": "operational-smoke",
        "passenger_workspace_id": "passenger-smoke",
        "travel_request_workspace_id": "request-smoke",
        "trip_workspace_id": "trip-smoke",
        "booking_workspace_id": "booking-smoke",
        "ticket_workspace_id": "ticket-smoke",
        "emd_workspace_id": "emd-smoke",
        "ssr_osi_workspace_id": "ssr-osi-smoke",
        "operational_intelligence_record_ids": ["aoie-smoke"],
        "document_reference": reference,
        "document_status": "required",
        "document_type": "medif",
        "document_category": "medical",
        "document_title": "MEDIF clearance metadata",
        "document_description": "Metadata-only passenger service document record.",
        "passenger_id": "passenger-profile-smoke",
        "passenger_name": "Document Passenger",
        "booking_reference": "BKG-DOC-SMOKE",
        "airline_pnr": "LH1DOC",
        "gds_record_locator": "1DOC2A",
        "related_service_requirement": "wheelchair assistance",
        "related_ssr_code": "WCHR",
        "related_emd_number": "2208200000001",
        "related_ticket_number": "2201234567890",
        "required_for_travel": True,
        "required_by_airline": True,
        "required_by_airport": True,
        "required_by_authority": False,
        "requirement_deadline": "2028-05-01",
        "received_status": "pending",
        "verification_status": "awaiting_review",
        "validity_start_date": "2028-05-01",
        "validity_end_date": "2028-05-20",
        "issuing_authority": "Medical provider metadata",
        "language": "en",
        "file_name": "medif-smoke.pdf",
        "file_type": "application/pdf",
        "file_size": 128000,
        "storage_reference": "storage://metadata-only/document-smoke",
        "document_package_ids": ["package-smoke"],
        "render_job_ids": ["render-smoke"],
        "share_record_ids": ["share-smoke"],
        "customer_visible": True,
        "airline_visible": True,
        "internal_only": False,
        "missing_reason": "Awaiting received document metadata.",
        "rejection_reason": None,
        "operational_notes": "No delivery, e-signature, public link, PDF generation, storage integration, worker, or AI action.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if {item.value for item in DocumentWorkspaceStatus} != DOCUMENT_STATUSES:
        raise AssertionError("Document workspace status enum values changed unexpectedly.")
    if {item.value for item in DocumentWorkspaceType} != DOCUMENT_TYPES:
        raise AssertionError("Document workspace type enum values changed unexpectedly.")

    create_payload = DocumentWorkspaceCreate(**document_payload("agency-smoke", "DOCW-SMOKE-MODEL"))
    workspace = DocumentWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    if workspace.document_status != DocumentWorkspaceStatus.REQUIRED:
        raise AssertionError("Document workspace status did not normalize to enum.")
    if workspace.document_type != DocumentWorkspaceType.MEDIF:
        raise AssertionError("Document workspace type did not normalize to enum.")
    if workspace.ssr_osi_workspace_id != "ssr-osi-smoke" or workspace.emd_workspace_id != "emd-smoke":
        raise AssertionError("Document workspace linkage fields were not preserved.")
    if workspace.metadata_only is not True or workspace.live_document_delivery_disabled is not True:
        raise AssertionError("Document workspace model is not metadata-only.")
    if "document_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Document workspaces collection is not registered as agency-owned metadata.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "document_workspaces_id_unique",
        "document_workspaces_reference_unique",
        "document_workspaces_agency_type_lookup",
        "document_workspaces_agency_status_lookup",
        "document_workspaces_agency_passenger_workspace_lookup",
        "document_workspaces_agency_booking_reference_lookup",
        "document_workspaces_agency_related_service_lookup",
        "document_workspaces_agency_required_for_travel_lookup",
        "document_workspaces_agency_verification_status_lookup",
        "document_workspaces_agency_deadline_lookup",
        "document_workspaces_ticket_workspace_lookup",
        "document_workspaces_emd_workspace_lookup",
        "document_workspaces_ssr_osi_workspace_lookup",
        "document_workspaces_operational_intelligence_lookup",
        "document_workspaces_package_lookup",
        "document_workspaces_render_job_lookup",
        "document_workspaces_share_record_lookup",
        "document_workspaces_storage_reference_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Document workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/document-workspaces": {"get", "post"},
        "/api/platform/document-workspaces/summary": {"get"},
        "/api/platform/document-workspaces/{workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/document-workspaces": {"get"},
        "/api/agencies/{agency_id}/document-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/document-workspaces/{workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/document-workspaces",
        "/api/agencies/{agency_id}/document-workspaces/summary",
        "/api/agencies/{agency_id}/document-workspaces/{workspace_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency document workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Document Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/document-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/document-workspaces"),
        (ROOT / "frontend/src/pages/platform/DocumentWorkspacesPage.jsx", "Document Workspaces"),
        (ROOT / "frontend/src/pages/platform/DocumentWorkspacesPage.jsx", "No duplicate render layer"),
        (ROOT / "frontend/src/pages/agency/DocumentWorkspacesPage.jsx", "Read-only operational document workspace metadata"),
        (ROOT / "docs/architecture/document-workspace-foundation.md", "Document Workspace Foundation"),
        (ROOT / "docs/architecture/document-workspace-foundation.md", "Phase 36.5"),
        (ROOT / "README.md", "Phase 42.0 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 42.0: Document Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "document_workspaces"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/document-workspaces"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Document workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Document workspaces"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Phase 42.0 adds the Document Workspace"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/DocumentWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/DocumentWorkspacesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/DocumentWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/DocumentWorkspacesPage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Document Workspaces" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Document Workspaces category: {categories}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Document workspace foundation built in Phase 42.0" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gaps missing Document Workspace foundation marker: {gaps}")
    if "Phase 42.2" not in gaps.get("next_operational_phase", ""):
        raise AssertionError(f"Blueprint gaps missing Phase 42.2 operational marker: {gaps}")
    chapter_41 = gaps.get("chapter_41_operational_workspaces") or []
    if "Document workspaces" not in chapter_41:
        raise AssertionError(f"Chapter 41/42 operational map missing Document workspaces: {gaps}")
    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not any(item.get("phase") == "Phase 42.2" for item in next_phases.get("items", [])):
        raise AssertionError(f"Next recommendations missing Phase 42.2: {next_phases}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("document_workspace_foundation") or {}
    for flag in [
        "document_workspaces_enabled",
        "document_workspace_metadata_enabled",
        "platform_document_workspace_metadata_crud_enabled",
        "agency_document_workspace_read_only_enabled",
        "platform_document_workspaces_ui_enabled",
        "agency_documents_workspace_ui_enabled",
        "filter_by_document_type_enabled",
        "filter_by_document_status_enabled",
        "filter_by_passenger_enabled",
        "filter_by_booking_reference_enabled",
        "filter_by_related_service_enabled",
        "filter_by_required_for_travel_enabled",
        "filter_by_verification_status_enabled",
        "filter_by_deadline_enabled",
        "operational_document_workspace_layer_enabled",
        "passenger_workspace_link_enabled",
        "travel_request_workspace_link_enabled",
        "trip_workspace_link_enabled",
        "booking_workspace_link_enabled",
        "ticket_workspace_link_enabled",
        "emd_workspace_link_enabled",
        "ssr_osi_workspace_link_enabled",
        "operational_intelligence_record_link_enabled",
        "phase_36_5_document_foundation_not_duplicated",
        "document_requirement_metadata_enabled",
        "document_verification_metadata_enabled",
        "document_validity_metadata_enabled",
        "document_storage_reference_metadata_enabled",
        "document_package_reference_metadata_enabled",
        "document_visibility_metadata_enabled",
        "metadata_only",
        "document_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "document_workspace_count",
        "document_workspace_status_counts",
        "document_workspace_type_counts",
        "document_workspace_verification_status_count",
        "document_workspace_required_for_travel_count",
        "document_workspace_required_by_airline_count",
        "document_workspace_required_by_airport_count",
        "document_workspace_required_by_authority_count",
        "document_workspace_customer_visible_count",
        "document_workspace_airline_visible_count",
        "document_workspace_internal_only_count",
        "document_workspace_passenger_workspace_count",
        "document_workspace_travel_request_workspace_count",
        "document_workspace_trip_workspace_count",
        "document_workspace_booking_workspace_count",
        "document_workspace_ticket_workspace_count",
        "document_workspace_emd_workspace_count",
        "document_workspace_ssr_osi_workspace_count",
        "document_workspace_operational_intelligence_record_count",
        "document_workspace_package_count",
        "document_workspace_render_job_count",
        "document_workspace_share_record_count",
        "document_workspace_storage_reference_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Document workspace readiness missing count: {count_key}")
    if not DOCUMENT_STATUSES.issubset(set((section.get("document_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Document workspace readiness missing statuses: {section}")
    if not DOCUMENT_TYPES.issubset(set((section.get("document_workspace_type_counts") or {}).keys())):
        raise AssertionError(f"Document workspace readiness missing document types: {section}")
    previous_section = readiness.get("ssr_osi_operational_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous SSR / OSI workspace section should remain metadata-only.")


def verify_no_forbidden_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/document_workspace_service.py",
        ROOT / "backend/routers/platform_document_workspaces.py",
        ROOT / "backend/routers/agency_document_workspaces.py",
        ROOT / "frontend/src/pages/platform/DocumentWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/DocumentWorkspacesPage.jsx",
    ]
    forbidden_terms = [
        "BackgroundTasks",
        "send_email",
        "send_sms",
        "sign_document",
        "create_public_link",
        "generate_pdf",
        "charge",
        "stripe",
        "openai",
        "requests.post",
        "httpx.",
        "schedule_job",
        "celery",
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            if term.lower() in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden implementation term: {term}")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    created = post("/api/platform/document-workspaces", document_payload(agency_id), OWNER_HEADERS, 201)
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    workspace = created.get("document_workspace") or {}
    assert_workspace_shape(workspace)
    workspace_id = workspace.get("id")
    if not workspace_id:
        raise AssertionError(f"Document workspace id missing: {created}")

    updated = put(
        f"/api/platform/document-workspaces/{workspace_id}",
        {
            "document_status": "verified",
            "received_status": "received",
            "verification_status": "verified",
            "missing_reason": "",
            "rejection_reason": "",
            "operational_notes": "Updated metadata only; no document delivery.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_workspace = updated.get("document_workspace") or {}
    assert_workspace_shape(updated_workspace)
    if updated_workspace.get("document_status") != "verified" or updated_workspace.get("verification_status") != "verified":
        raise AssertionError(f"Document workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "document_type=medif",
        "document_status=verified",
        "passenger=passenger-smoke",
        "booking_reference=BKG-DOC-SMOKE",
        "related_service=WCHR",
        "required_for_travel=true",
        "verification_status=verified",
        "deadline=2028-05-01",
    ]:
        filtered = get(f"/api/platform/document-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Document workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/document-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/document-workspaces/{workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_workspace_shape(platform_detail.get("document_workspace") or {})

    agency_list = get(
        f"/api/agencies/{agency_id}/document-workspaces?document_type=medif&document_status=verified&passenger=passenger-smoke&booking_reference=BKG-DOC-SMOKE&related_service=WCHR&required_for_travel=true&verification_status=verified&deadline=2028-05-01",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency document list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency document list missing created record: {agency_list}")
    assert_workspace_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/document-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency document summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/document-workspaces/{workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency document detail should be read-only: {agency_detail}")
    assert_workspace_shape(agency_detail.get("document_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/document-workspaces/{workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or (deleted.get("document_workspace") or {}).get("document_status") != "archived":
        raise AssertionError(f"Document workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/document-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default document list should exclude archived metadata: {after_delete}")
    include_archived = get(f"/api/platform/document-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose archived document workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/document-workspaces", {"document_type": "medif"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/document-workspaces/{workspace_id}", {"document_status": "verified"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/document-workspaces/{workspace_id}", {}, OWNER_HEADERS, 405)


def assert_workspace_shape(workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "passenger_workspace_id",
        "travel_request_workspace_id",
        "trip_workspace_id",
        "booking_workspace_id",
        "ticket_workspace_id",
        "emd_workspace_id",
        "ssr_osi_workspace_id",
        "operational_intelligence_record_ids",
        "document_reference",
        "document_status",
        "document_type",
        "document_category",
        "document_title",
        "document_description",
        "passenger_id",
        "passenger_name",
        "booking_reference",
        "airline_pnr",
        "gds_record_locator",
        "related_service_requirement",
        "related_ssr_code",
        "related_emd_number",
        "related_ticket_number",
        "required_for_travel",
        "required_by_airline",
        "required_by_airport",
        "required_by_authority",
        "requirement_deadline",
        "received_status",
        "verification_status",
        "validity_start_date",
        "validity_end_date",
        "issuing_authority",
        "language",
        "file_name",
        "file_type",
        "file_size",
        "storage_reference",
        "document_package_ids",
        "render_job_ids",
        "share_record_ids",
        "customer_visible",
        "airline_visible",
        "internal_only",
        "missing_reason",
        "operational_notes",
        "document_display_name",
    ]:
        if key not in workspace:
            raise AssertionError(f"Document workspace missing {key}: {workspace}")
    if workspace.get("ticket_workspace_id") != "ticket-smoke":
        raise AssertionError(f"Ticket workspace link missing: {workspace}")
    if workspace.get("emd_workspace_id") != "emd-smoke":
        raise AssertionError(f"EMD workspace link missing: {workspace}")
    if workspace.get("ssr_osi_workspace_id") != "ssr-osi-smoke":
        raise AssertionError(f"SSR / OSI workspace link missing: {workspace}")
    if "aoie-smoke" not in (workspace.get("operational_intelligence_record_ids") or []):
        raise AssertionError(f"Operational intelligence link missing: {workspace}")
    if not {"package-smoke"}.issubset(set(workspace.get("document_package_ids") or [])):
        raise AssertionError(f"Document package link missing: {workspace}")
    if not {"render-smoke"}.issubset(set(workspace.get("render_job_ids") or [])):
        raise AssertionError(f"Render job link missing: {workspace}")
    if not {"share-smoke"}.issubset(set(workspace.get("share_record_ids") or [])):
        raise AssertionError(f"Share record link missing: {workspace}")
    if agency_view and workspace.get("read_only") is not True:
        raise AssertionError(f"Agency document workspace item should be read-only: {workspace}")
    for flag in disabled_flags():
        if workspace.get(flag) is not True:
            raise AssertionError(f"Document workspace missing disabled flag {flag}: {workspace}")
    if workspace.get("metadata_only") is not True:
        raise AssertionError(f"Document workspace should be metadata-only: {workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary has wrong agency id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_document_status",
        "by_document_type",
        "by_verification_status",
        "ticket_workspace_count",
        "emd_workspace_count",
        "ssr_osi_workspace_count",
        "document_package_count",
        "render_job_count",
        "share_record_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Document workspace summary missing {key}: {payload}")
    if not DOCUMENT_STATUSES.issubset(set((summary.get("by_document_status") or {}).keys())):
        raise AssertionError(f"Document workspace summary missing statuses: {payload}")
    if not DOCUMENT_TYPES.issubset(set((summary.get("by_document_type") or {}).keys())):
        raise AssertionError(f"Document workspace summary missing document types: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths", {}))
    verify_no_forbidden_implementation()
    verify_frontend_and_docs()
    verify_readiness()
    verify_blueprint_adoption()
    verify_endpoint_behavior()
    print("Phase 42.0 document workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
