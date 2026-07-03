#!/usr/bin/env python3
import sys

from smoke_booking_pnr_foundation import OWNER_HEADERS, flatten_service_snapshot, get, post
from smoke_ticket_emd_foundation import create_booking_record, service_key


EXPECTED_PHASE = "phase_38_0_offer_decision_export_audit_review_foundation"


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def render_document(agency_id: str, document_type: str, source_context_type: str, source_context_id: str) -> dict:
    result = post(
        f"/api/agencies/{agency_id}/documents/render-jobs",
        {
            "document_type": document_type,
            "source_context_type": source_context_type,
            "source_context_id": source_context_id,
            "render_format": "html",
        },
        OWNER_HEADERS,
        201,
    )
    job = result.get("render_job") or {}
    if not job.get("id") or job.get("render_status") != "rendered":
        raise AssertionError(f"{document_type} render job was not rendered: {job}")
    if "<html" not in (job.get("rendered_html") or ""):
        raise AssertionError(f"{document_type} render did not include HTML output.")
    if result.get("live_delivery_disabled") is not True or result.get("pdf_export_required") is not False:
        raise AssertionError(f"{document_type} render changed disabled delivery/export flags.")
    return job


def assert_context_preview(agency_id: str, source_context_type: str, source_context_id: str) -> dict:
    preview = post(
        f"/api/agencies/{agency_id}/documents/context-preview",
        {"source_context_type": source_context_type, "source_context_id": source_context_id},
        OWNER_HEADERS,
    )
    context = preview.get("context") or {}
    if not context.get("source_context_type") or not context.get("source_context_id"):
        raise AssertionError(f"{source_context_type} context preview did not include a normalized source.")
    if "warnings_json" not in context:
        raise AssertionError(f"{source_context_type} context preview did not include warnings_json.")
    return context


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/documents/templates", "get"),
        ("/api/platform/documents/templates/seed-defaults", "post"),
        ("/api/agencies/{agency_id}/documents/templates", "get"),
        ("/api/agencies/{agency_id}/documents/templates/{template_id}", "get"),
        ("/api/agencies/{agency_id}/documents/context-preview", "post"),
        ("/api/agencies/{agency_id}/documents/render-jobs", "get"),
        ("/api/agencies/{agency_id}/documents/render-jobs", "post"),
        ("/api/agencies/{agency_id}/documents/render-jobs/{render_job_id}", "get"),
        ("/api/agencies/{agency_id}/documents/render-jobs/{render_job_id}/rerender", "post"),
        ("/api/agencies/{agency_id}/documents/packages", "get"),
        ("/api/agencies/{agency_id}/documents/packages", "post"),
        ("/api/agencies/{agency_id}/documents/packages/{package_id}", "get"),
        ("/api/agencies/{agency_id}/documents/share-records", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    document_foundation = readiness.get("document_foundation") or {}
    for flag in [
        "document_template_foundation_enabled",
        "default_document_templates_enabled",
        "document_context_builder_enabled",
        "document_render_job_enabled",
        "document_package_enabled",
        "document_share_record_foundation_enabled",
        "agency_documents_ui_enabled",
        "trip_documents_entrypoint_enabled",
        "booking_documents_entrypoint_enabled",
        "ticket_emd_documents_entrypoint_enabled",
        "offer_documents_entrypoint_enabled",
        "import_review_document_entrypoint_enabled",
        "html_document_preview_enabled",
        "live_delivery_disabled",
        "e_signature_disabled",
        "payment_invoice_accounting_disabled",
    ]:
        if document_foundation.get(flag) is not True:
            raise AssertionError(f"Readiness missing document foundation flag: {flag}")
    for count_key in [
        "document_template_count",
        "document_render_job_count",
        "document_package_count",
        "document_share_record_count",
        "rendered_document_count",
        "document_export_count",
    ]:
        if count_key not in document_foundation:
            raise AssertionError(f"Readiness missing document foundation count: {count_key}")
    if document_foundation.get("pdf_export_required") is not False or document_foundation.get("readiness_required") is not False:
        raise AssertionError("Document foundation changed export/readiness requirements.")

    seeded = post("/api/platform/documents/templates/seed-defaults", {}, OWNER_HEADERS, 201)
    if seeded.get("default_document_templates_enabled") is not True:
        raise AssertionError("Default document template seed endpoint did not report enabled defaults.")

    platform_templates = get("/api/platform/documents/templates", OWNER_HEADERS)
    if len(platform_templates.get("items") or []) < 10:
        raise AssertionError("Platform document templates were not seeded.")

    agency_id, booking_readiness, booking_workspace, booking_record = create_booking_record()
    agency_templates = get(f"/api/agencies/{agency_id}/documents/templates", OWNER_HEADERS)
    if len(agency_templates.get("items") or []) < 10:
        raise AssertionError("Agency document templates did not include platform defaults.")
    first_template_id = agency_templates["items"][0]["id"]
    if not get(f"/api/agencies/{agency_id}/documents/templates/{first_template_id}", OWNER_HEADERS).get("template"):
        raise AssertionError("Agency document template detail did not return a template.")

    trip_id = booking_workspace.get("trip_id") or booking_readiness.get("trip_id")
    trip_context = assert_context_preview(agency_id, "trip", trip_id)
    booking_context = assert_context_preview(agency_id, "booking_workspace", booking_workspace["id"])
    if booking_context.get("booking_summary", {}).get("booking_workspace_id") != booking_workspace["id"]:
        raise AssertionError("Booking workspace context preview did not include booking summary.")
    trip_job = render_document(agency_id, "trip_confirmation", "trip", trip_id)
    booking_job = render_document(agency_id, "booking_confirmation", "booking_workspace", booking_workspace["id"])

    ticket_created = post(
        f"/api/agencies/{agency_id}/tickets/from-booking-record",
        {"booking_record_id": booking_record["id"], "create_coupons": True},
        OWNER_HEADERS,
        201,
    )
    ticket = ticket_created.get("ticket") or {}
    if not ticket.get("id"):
        raise AssertionError("Ticket mirror setup failed for document smoke.")
    ticket_context = assert_context_preview(agency_id, "ticket_record", ticket["id"])
    if ticket_context.get("ticket_summary", {}).get("id") != ticket["id"]:
        raise AssertionError("Ticket context preview did not include ticket summary.")
    ticket_job = render_document(agency_id, "ticket_receipt", "ticket_record", ticket["id"])

    service_items = flatten_service_snapshot(booking_readiness.get("services_snapshot_json") or {})
    selected_service = service_items[0] if service_items else {}
    emd_created = post(
        f"/api/agencies/{agency_id}/emds/from-booking-service",
        {
            "booking_record_id": booking_record["id"],
            "ticket_record_id": ticket["id"],
            "service_key": service_key(selected_service) or "WCHR",
            "create_coupons": True,
        },
        OWNER_HEADERS,
        201,
    )
    emd = emd_created.get("emd") or {}
    if not emd.get("id"):
        raise AssertionError("EMD mirror setup failed for document smoke.")
    emd_context = assert_context_preview(agency_id, "emd_record", emd["id"])
    if emd_context.get("emd_summary", {}).get("id") != emd["id"]:
        raise AssertionError("EMD context preview did not include EMD summary.")
    emd_job = render_document(agency_id, "emd_receipt", "emd_record", emd["id"])

    import_draft = post(
        f"/api/agencies/{agency_id}/booking-import-drafts",
        {
            "source_type": "cryptic_gds",
            "import_context": "existing_trip_change",
            "linked_trip_id": trip_id,
            "raw_text": "RP/SOF1A0980/SOF1A0980 AA/SU 30JUN26/0915Z ABC123\n1.SMOKE/TRAVELER MR\n2 LH1703 Y 13DEC SOFFRA HK1 0600 0725\nTK 2201234567890",
        },
        OWNER_HEADERS,
        201,
    )["draft"]
    parsed_import = post(
        f"/api/agencies/{agency_id}/booking-import-drafts/{import_draft['id']}/parse",
        {},
        OWNER_HEADERS,
    )
    import_context = assert_context_preview(agency_id, "booking_import_draft", import_draft["id"])
    if import_context.get("import_summary", {}).get("id") != import_draft["id"] or not parsed_import.get("draft"):
        raise AssertionError("Import review context preview did not include import summary.")
    import_job = render_document(agency_id, "import_review_summary", "booking_import_draft", import_draft["id"])

    trip_change = post(
        f"/api/agencies/{agency_id}/trips/{trip_id}/change-operations",
        {
            "operation_type": "itinerary_change",
            "reason": "Document foundation smoke change summary.",
            "source_booking_workspace_id": booking_workspace["id"],
            "source_booking_record_id": booking_record["id"],
            "change_summary_json": {
                "summary_text": "Move departure later for the same trip.",
                "proposed_change_notes": "Internal mirror only.",
            },
            "original_snapshot_json": {"booking_record_id": booking_record["id"], "pnr_locator": booking_record.get("pnr_locator")},
            "proposed_snapshot_json": {"requested_departure_window": "afternoon"},
        },
        OWNER_HEADERS,
        201,
    )["operation"]
    change_context = assert_context_preview(agency_id, "trip_change_operation", trip_change["id"])
    if change_context.get("change_exchange_summary", {}).get("id") != trip_change["id"]:
        raise AssertionError("Trip change context preview did not include change summary.")
    change_job = render_document(agency_id, "trip_change_summary", "trip_change_operation", trip_change["id"])

    missing_source_job = render_document(agency_id, "internal_case_summary", "trip", "missing-document-source")
    if not any(item.get("code") == "source_context_missing" for item in missing_source_job.get("warnings_json") or []):
        raise AssertionError("Missing source render did not store a warning.")

    rerendered = post(
        f"/api/agencies/{agency_id}/documents/render-jobs/{booking_job['id']}/rerender",
        {},
        OWNER_HEADERS,
    )
    if rerendered.get("render_job", {}).get("id") != booking_job["id"]:
        raise AssertionError("Rerender did not update the original render job.")

    package = post(
        f"/api/agencies/{agency_id}/documents/packages",
        {
            "package_type": "booking_package",
            "title": "Document foundation smoke package",
            "source_context_type": "booking_workspace",
            "source_context_id": booking_workspace["id"],
            "document_render_job_ids": [trip_job["id"], booking_job["id"], ticket_job["id"], emd_job["id"], import_job["id"], change_job["id"]],
        },
        OWNER_HEADERS,
        201,
    ).get("package") or {}
    if package.get("status") != "ready" or len(package.get("document_render_job_ids") or []) != 6:
        raise AssertionError(f"Document package was not ready with rendered jobs: {package}")

    package_detail = get(f"/api/agencies/{agency_id}/documents/packages/{package['id']}", OWNER_HEADERS)
    if len(package_detail.get("items") or []) != 6:
        raise AssertionError("Document package detail did not include rendered job items.")

    share = post(
        f"/api/agencies/{agency_id}/documents/share-records",
        {
            "document_package_id": package["id"],
            "share_status": "ready",
            "share_channel": "internal",
            "recipient_snapshot_json": {"mode": "internal_manual_record"},
        },
        OWNER_HEADERS,
        201,
    )
    if share.get("live_delivery_disabled") is not True or share.get("share_record", {}).get("share_status") != "ready":
        raise AssertionError("Document share record did not remain an internal/manual record.")

    listed_jobs = get(f"/api/agencies/{agency_id}/documents/render-jobs?source_context_type=booking_workspace", OWNER_HEADERS)
    if not any(item["id"] == booking_job["id"] for item in listed_jobs.get("items", [])):
        raise AssertionError("Render job list did not include the booking render job.")
    listed_packages = get(f"/api/agencies/{agency_id}/documents/packages?source_context_type=booking_workspace", OWNER_HEADERS)
    if not any(item["id"] == package["id"] for item in listed_packages.get("items", [])):
        raise AssertionError("Package list did not include the created package.")

    final_readiness = get("/api/readiness").get("document_foundation") or {}
    if final_readiness.get("live_delivery_disabled") is not True or final_readiness.get("pdf_export_required") is not False:
        raise AssertionError("Document foundation readiness disabled flags changed unexpectedly.")
    if final_readiness.get("document_render_job_count", 0) < 7 or final_readiness.get("document_package_count", 0) < 1:
        raise AssertionError("Document foundation readiness did not count rendered jobs/packages.")

    print("Document foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Document foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
