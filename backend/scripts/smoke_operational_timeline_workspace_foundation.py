#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import OperationalTimeline, OperationalTimelineCreate
from services.timeline_workspace_service import COMMUNICATION_TYPES, TIMELINE_EVENT_TYPES
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_50_1_airline_knowledge_acquisition_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
EVENT_TYPES = {
    "passenger_created",
    "passenger_updated",
    "travel_request_received",
    "offer_created",
    "offer_accepted",
    "booking_created",
    "ticket_linked",
    "emd_linked",
    "ssr_created",
    "ssr_confirmed",
    "osi_added",
    "medif_requested",
    "medif_received",
    "document_uploaded",
    "document_verified",
    "approval_requested",
    "approval_received",
    "approval_rejected",
    "airport_handling_confirmed",
    "customer_contacted",
    "airline_contacted",
    "internal_note",
    "task_completed",
    "reminder",
    "deadline_reached",
    "other",
}
COMM_TYPES = {
    "email",
    "phone",
    "chat",
    "letter",
    "meeting",
    "internal_note",
    "airline_message",
    "airport_message",
    "customer_message",
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
        "email_sending_disabled",
        "sms_sending_disabled",
        "whatsapp_disabled",
        "teams_disabled",
        "slack_disabled",
        "live_airline_messaging_disabled",
        "live_customer_messaging_disabled",
        "ai_summarization_disabled",
        "background_workers_disabled",
        "provider_integrations_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "email_sending_enabled",
        "sms_sending_enabled",
        "whatsapp_enabled",
        "teams_enabled",
        "slack_enabled",
        "live_airline_messaging_enabled",
        "live_customer_messaging_enabled",
        "ai_summarization_enabled",
        "background_workers_enabled",
        "provider_integrations_enabled",
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


def timeline_payload(
    agency_id: str,
    reference: str = "TL-SMOKE-001",
    *,
    event_type: str = "document_uploaded",
    subject: str = "Document uploaded metadata",
    status: str = "open",
) -> dict:
    return {
        "agency_id": agency_id,
        "timeline_reference": reference,
        "created_by": "timeline-smoke-user",
        "passenger_workspace_id": "timeline-passenger-smoke",
        "travel_request_workspace_id": "timeline-request-smoke",
        "trip_workspace_id": "timeline-trip-smoke",
        "booking_workspace_id": "timeline-booking-smoke",
        "ticket_workspace_id": "timeline-ticket-smoke",
        "emd_workspace_id": "timeline-emd-smoke",
        "ssr_osi_workspace_id": "timeline-ssr-smoke",
        "document_workspace_id": "timeline-document-smoke",
        "event_type": event_type,
        "event_category": "document",
        "event_source": "manual_metadata",
        "event_status": status,
        "event_priority": "high",
        "operational_stage": "document_review",
        "operational_result": "metadata_recorded",
        "related_airline": "LH",
        "related_airport": "SOF",
        "communication_type": "email",
        "communication_direction": "outbound",
        "communication_channel": "manual_metadata",
        "sender": "Agency operations",
        "recipient": "Customer",
        "subject": subject,
        "summary": "Metadata-only operational history entry; no message was sent.",
        "attachment_ids": ["timeline-attachment-smoke"],
        "approval_reference": "timeline-approval-smoke",
        "approval_status": "pending",
        "due_date": "2028-06-01",
        "completed_date": "2028-06-02" if status == "completed" else None,
        "reminder_required": True,
        "internal_only": False,
        "passenger_visible": True,
        "airline_visible": True,
        "operational_notes": "No email, SMS, WhatsApp, Teams, Slack, live messaging, AI summary, worker, provider, or automation action.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if set(TIMELINE_EVENT_TYPES) != EVENT_TYPES:
        raise AssertionError("Operational timeline event type constants changed unexpectedly.")
    if set(COMMUNICATION_TYPES) != COMM_TYPES:
        raise AssertionError("Operational timeline communication type constants changed unexpectedly.")

    create_payload = OperationalTimelineCreate(**timeline_payload("agency-smoke", "TL-SMOKE-MODEL"))
    entry = OperationalTimeline(**create_payload.model_dump(mode="json", exclude_none=True))
    if entry.event_type != "document_uploaded" or entry.communication_type != "email":
        raise AssertionError("Operational timeline model did not preserve event/communication metadata.")
    if entry.ticket_workspace_id != "timeline-ticket-smoke" or entry.emd_workspace_id != "timeline-emd-smoke":
        raise AssertionError("Operational timeline relationship fields were not preserved.")
    if entry.metadata_only is not True or entry.email_sending_disabled is not True:
        raise AssertionError("Operational timeline model is not metadata-only.")
    if "operational_timelines" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Operational timelines collection is not registered as agency-owned metadata.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "operational_timelines_id_unique",
        "operational_timelines_reference_unique",
        "operational_timelines_agency_created_lookup",
        "operational_timelines_agency_event_type_lookup",
        "operational_timelines_agency_status_lookup",
        "operational_timelines_agency_priority_lookup",
        "operational_timelines_agency_communication_type_lookup",
        "operational_timelines_agency_airline_lookup",
        "operational_timelines_agency_airport_lookup",
        "operational_timelines_passenger_workspace_lookup",
        "operational_timelines_booking_workspace_lookup",
        "operational_timelines_ticket_workspace_lookup",
        "operational_timelines_emd_workspace_lookup",
        "operational_timelines_ssr_osi_workspace_lookup",
        "operational_timelines_document_workspace_lookup",
        "operational_timelines_approval_reference_lookup",
        "operational_timelines_attachment_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Operational timeline index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/operational-timelines": {"get", "post"},
        "/api/platform/operational-timelines/summary": {"get"},
        "/api/platform/operational-timelines/{timeline_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/operational-timelines": {"get"},
        "/api/agencies/{agency_id}/operational-timelines/summary": {"get"},
        "/api/agencies/{agency_id}/operational-timelines/{timeline_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/operational-timelines",
        "/api/agencies/{agency_id}/operational-timelines/summary",
        "/api/agencies/{agency_id}/operational-timelines/{timeline_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency operational timeline route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Timelines"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Timeline"),
        (ROOT / "frontend/src/App.jsx", "/platform/operational-timelines"),
        (ROOT / "frontend/src/App.jsx", "/agency/timeline"),
        (ROOT / "frontend/src/pages/platform/OperationalTimelinesPage.jsx", "Operational Timelines"),
        (ROOT / "frontend/src/pages/platform/OperationalTimelinesPage.jsx", "No messaging"),
        (ROOT / "frontend/src/pages/platform/OperationalTimelinesPage.jsx", "No AI summaries"),
        (ROOT / "frontend/src/pages/agency/TimelinePage.jsx", "Timeline"),
        (ROOT / "frontend/src/pages/agency/TimelinePage.jsx", "Read-only operational history metadata"),
        (ROOT / "docs/architecture/operational-timeline-workspace-foundation.md", "Operational Timeline Workspace Foundation"),
        (ROOT / "README.md", "Phase 42.1 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 42.1: Operational Timeline Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_timelines"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/operational-timelines"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operational timelines"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operational timelines"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Phase 42.1 adds the Operational Timeline Workspace"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/OperationalTimelinesPage.jsx",
        ROOT / "frontend/src/pages/agency/TimelinePage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/OperationalTimelinesPage.jsx",
        ROOT / "frontend/src/pages/agency/TimelinePage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Operational Timelines" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Operational Timelines category: {categories}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Operational timeline workspace foundation built in Phase 42.1" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gaps missing Operational Timeline foundation marker: {gaps}")
    if "Phase 42.2" not in gaps.get("next_operational_phase", ""):
        raise AssertionError(f"Blueprint gaps missing Phase 42.2 operational marker: {gaps}")
    chapter_41 = gaps.get("chapter_41_operational_workspaces") or []
    if "Operational timelines" not in chapter_41:
        raise AssertionError(f"Chapter 41/42 operational map missing Operational timelines: {gaps}")
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
    section = readiness.get("operational_timeline_workspace_foundation") or {}
    for flag in [
        "operational_timelines_enabled",
        "operational_timeline_metadata_enabled",
        "platform_operational_timeline_metadata_crud_enabled",
        "agency_operational_timeline_read_only_enabled",
        "platform_operational_timelines_ui_enabled",
        "agency_timeline_ui_enabled",
        "chronological_timeline_enabled",
        "filter_by_passenger_enabled",
        "filter_by_booking_enabled",
        "filter_by_ticket_enabled",
        "filter_by_emd_enabled",
        "filter_by_ssr_enabled",
        "filter_by_airline_enabled",
        "filter_by_communication_type_enabled",
        "filter_by_event_type_enabled",
        "filter_by_priority_enabled",
        "filter_by_status_enabled",
        "filter_by_date_enabled",
        "passenger_workspace_link_enabled",
        "travel_request_workspace_link_enabled",
        "trip_workspace_link_enabled",
        "booking_workspace_link_enabled",
        "ticket_workspace_link_enabled",
        "emd_workspace_link_enabled",
        "ssr_osi_workspace_link_enabled",
        "document_workspace_link_enabled",
        "communication_metadata_enabled",
        "approval_metadata_enabled",
        "attachment_metadata_enabled",
        "visibility_metadata_enabled",
        "metadata_only",
        "timeline_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "operational_timeline_count",
        "operational_timeline_event_type_counts",
        "operational_timeline_communication_type_counts",
        "operational_timeline_status_count",
        "operational_timeline_priority_count",
        "operational_timeline_category_count",
        "operational_timeline_passenger_workspace_count",
        "operational_timeline_travel_request_workspace_count",
        "operational_timeline_trip_workspace_count",
        "operational_timeline_booking_workspace_count",
        "operational_timeline_ticket_workspace_count",
        "operational_timeline_emd_workspace_count",
        "operational_timeline_ssr_osi_workspace_count",
        "operational_timeline_document_workspace_count",
        "operational_timeline_attachment_count",
        "operational_timeline_approval_reference_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Operational timeline readiness missing count: {count_key}")
    if not EVENT_TYPES.issubset(set((section.get("operational_timeline_event_type_counts") or {}).keys())):
        raise AssertionError(f"Operational timeline readiness missing event types: {section}")
    if not COMM_TYPES.issubset(set((section.get("operational_timeline_communication_type_counts") or {}).keys())):
        raise AssertionError(f"Operational timeline readiness missing communication types: {section}")
    previous_section = readiness.get("document_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Document workspace section should remain metadata-only.")


def verify_no_forbidden_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/timeline_workspace_service.py",
        ROOT / "backend/routers/platform_operational_timelines.py",
        ROOT / "backend/routers/agency_operational_timelines.py",
        ROOT / "frontend/src/pages/platform/OperationalTimelinesPage.jsx",
        ROOT / "frontend/src/pages/agency/TimelinePage.jsx",
    ]
    forbidden_terms = [
        "BackgroundTasks",
        "send_email",
        "send_sms",
        "whatsapp_client",
        "teams_client",
        "slack_client",
        "live_airline_message(",
        "live_customer_message(",
        "ai_summary",
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

    first = post("/api/platform/operational-timelines", timeline_payload(agency_id), OWNER_HEADERS, 201)
    assert_disabled_response(first)
    first_entry = first.get("timeline_entry") or {}
    assert_timeline_shape(first_entry)
    first_id = first_entry.get("id")
    if not first_id:
        raise AssertionError(f"Operational timeline id missing: {first}")

    second = post(
        "/api/platform/operational-timelines",
        timeline_payload(
            agency_id,
            "TL-SMOKE-002",
            event_type="document_verified",
            subject="Document verified metadata",
            status="completed",
        ),
        OWNER_HEADERS,
        201,
    )
    assert_disabled_response(second)
    second_entry = second.get("timeline_entry") or {}
    assert_timeline_shape(second_entry)
    second_id = second_entry.get("id")
    if not second_id:
        raise AssertionError(f"Operational timeline id missing: {second}")

    updated = put(
        f"/api/platform/operational-timelines/{second_id}",
        {
            "event_status": "completed",
            "approval_status": "received",
            "operational_notes": "Updated metadata only; no message was sent.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_entry = updated.get("timeline_entry") or {}
    assert_timeline_shape(updated_entry)
    if updated_entry.get("approval_status") != "received":
        raise AssertionError(f"Operational timeline update did not persist metadata: {updated}")

    chronological = get(
        f"/api/platform/operational-timelines?agency_id={agency_id}&passenger=timeline-passenger-smoke",
        OWNER_HEADERS,
    )
    assert_disabled_response(chronological)
    ids = [item.get("id") for item in chronological.get("items") or [] if item.get("id") in {first_id, second_id}]
    if ids != [first_id, second_id]:
        raise AssertionError(f"Operational timeline entries are not chronological ascending: {chronological}")

    filter_queries = [
        f"agency_id={agency_id}",
        "passenger=timeline-passenger-smoke",
        "booking=timeline-booking-smoke",
        "ticket=timeline-ticket-smoke",
        "emd=timeline-emd-smoke",
        "ssr=timeline-ssr-smoke",
        "airline=LH",
        "communication_type=email",
        "event_type=document_verified",
        "priority=high",
        "status=completed",
        f"date={updated_entry.get('created_at', '')[:10]}",
    ]
    for filter_query in filter_queries:
        filtered = get(f"/api/platform/operational-timelines?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == second_id for item in filtered.get("items") or []):
            raise AssertionError(f"Operational timeline filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/operational-timelines/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/operational-timelines/{second_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_timeline_shape(platform_detail.get("timeline_entry") or {})

    agency_list = get(
        f"/api/agencies/{agency_id}/operational-timelines?passenger=timeline-passenger-smoke&booking=timeline-booking-smoke&ticket=timeline-ticket-smoke&emd=timeline-emd-smoke&ssr=timeline-ssr-smoke&airline=LH&communication_type=email&event_type=document_verified&priority=high&status=completed",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency timeline list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == second_id), None)
    if not agency_item:
        raise AssertionError(f"Agency timeline list missing created record: {agency_list}")
    assert_timeline_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/operational-timelines/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency timeline summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/operational-timelines/{second_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency timeline detail should be read-only: {agency_detail}")
    assert_timeline_shape(agency_detail.get("timeline_entry") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/operational-timelines/{first_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or (deleted.get("timeline_entry") or {}).get("event_status") != "archived":
        raise AssertionError(f"Operational timeline delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/operational-timelines?agency_id={agency_id}&passenger=timeline-passenger-smoke", OWNER_HEADERS)
    if any(item.get("id") == first_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default timeline list should exclude archived metadata: {after_delete}")
    include_archived = get(
        f"/api/platform/operational-timelines?agency_id={agency_id}&passenger=timeline-passenger-smoke&include_archived=true",
        OWNER_HEADERS,
    )
    if not any(item.get("id") == first_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose archived timeline metadata: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/operational-timelines", {"event_type": "internal_note"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/operational-timelines/{second_id}", {"event_status": "closed"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/operational-timelines/{second_id}", {}, OWNER_HEADERS, 405)


def assert_timeline_shape(entry: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "timeline_reference",
        "created_by",
        "passenger_workspace_id",
        "travel_request_workspace_id",
        "trip_workspace_id",
        "booking_workspace_id",
        "ticket_workspace_id",
        "emd_workspace_id",
        "ssr_osi_workspace_id",
        "document_workspace_id",
        "event_type",
        "event_category",
        "event_source",
        "event_status",
        "event_priority",
        "operational_stage",
        "operational_result",
        "related_airline",
        "related_airport",
        "communication_type",
        "communication_direction",
        "communication_channel",
        "sender",
        "recipient",
        "subject",
        "summary",
        "attachment_ids",
        "approval_reference",
        "approval_status",
        "due_date",
        "reminder_required",
        "internal_only",
        "passenger_visible",
        "airline_visible",
        "operational_notes",
        "timeline_display_name",
        "metadata_only",
        "timeline_workspace_metadata_only",
    ]:
        if key not in entry:
            raise AssertionError(f"Operational timeline missing {key}: {entry}")
    if entry.get("ticket_workspace_id") != "timeline-ticket-smoke":
        raise AssertionError(f"Ticket workspace link missing: {entry}")
    if entry.get("emd_workspace_id") != "timeline-emd-smoke":
        raise AssertionError(f"EMD workspace link missing: {entry}")
    if entry.get("ssr_osi_workspace_id") != "timeline-ssr-smoke":
        raise AssertionError(f"SSR / OSI workspace link missing: {entry}")
    if entry.get("document_workspace_id") != "timeline-document-smoke":
        raise AssertionError(f"Document workspace link missing: {entry}")
    if "timeline-attachment-smoke" not in (entry.get("attachment_ids") or []):
        raise AssertionError(f"Attachment reference missing: {entry}")
    if agency_view and entry.get("read_only") is not True:
        raise AssertionError(f"Agency timeline entry should be read-only: {entry}")
    for flag in disabled_flags():
        if entry.get(flag) is not True:
            raise AssertionError(f"Operational timeline missing disabled flag {flag}: {entry}")
    if entry.get("metadata_only") is not True:
        raise AssertionError(f"Operational timeline should be metadata-only: {entry}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary has wrong agency id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_event_type",
        "by_communication_type",
        "by_status",
        "by_priority",
        "by_category",
        "ticket_workspace_count",
        "emd_workspace_count",
        "ssr_osi_workspace_count",
        "document_workspace_count",
        "attachment_count",
        "approval_reference_count",
        "reminder_required_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Operational timeline summary missing {key}: {payload}")
    if not EVENT_TYPES.issubset(set((summary.get("by_event_type") or {}).keys())):
        raise AssertionError(f"Operational timeline summary missing event types: {payload}")
    if not COMM_TYPES.issubset(set((summary.get("by_communication_type") or {}).keys())):
        raise AssertionError(f"Operational timeline summary missing communication types: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths", {}))
    verify_no_forbidden_implementation()
    verify_frontend_and_docs()
    verify_readiness()
    verify_blueprint_adoption()
    verify_endpoint_behavior()
    print("Phase 42.1 operational timeline workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
