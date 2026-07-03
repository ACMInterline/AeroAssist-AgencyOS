#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_export_release_readiness_foundation import create_preview_source, main as smoke_offer_decision_export_release_readiness_foundation
from smoke_offer_decision_pack_foundation import option_signature


EXPECTED_PHASE = "phase_39_1_airline_intelligence_data_pack_review_foundation"


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision export delivery count {key}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def create_release_readiness(agency_id: str, preview: dict, run_key: str) -> dict:
    base = f"/api/agencies/{agency_id}/offer-decision-export-releases"
    approval_response = post(
        f"{base}/approvals",
        {
            "preview_id": preview["id"],
            "approval_name": f"Smoke delivery approval {run_key}",
            "assigned_reviewer": "smoke-delivery-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    approval = approval_response["approval"]
    post(
        f"{base}/approvals/{approval['id']}/checkpoints",
        {
            "checkpoint_type": "manual_release_readiness",
            "checkpoint_status": "passed",
            "checkpoint_title": f"Smoke delivery manual release checkpoint {run_key}",
            "notes": "Human reviewer confirmed manual handoff can be prepared as metadata only.",
            "checkpoint_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    approval = post(
        f"{base}/approvals/{approval['id']}/status",
        {
            "approval_status": "approved",
            "status_reason": "Smoke approval for manual delivery handoff metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["approval"]
    readiness = post(
        f"{base}/readiness",
        {
            "approval_id": approval["id"],
            "readiness_name": f"Smoke delivery release readiness {run_key}",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["readiness"]
    return {"approval": approval, "readiness": readiness}


def main() -> int:
    run_key = uuid4().hex[:10]
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "offer-decision-export-deliveries" in path and any(token in path for token in ["/send", "/deliver", "/publish", "public-link", "/execute", "/issue", "/pay", "/invoice", "/settle", "/book", "/charge"]):
            raise AssertionError(f"Decision export delivery execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-export-deliveries/summary", "get"),
        ("/api/platform/offer-decision-export-deliveries/handoffs", "get"),
        ("/api/platform/offer-decision-export-deliveries/handoffs/{handoff_id}", "get"),
        ("/api/platform/offer-decision-export-deliveries/recipients", "get"),
        ("/api/platform/offer-decision-export-deliveries/attachments", "get"),
        ("/api/platform/offer-decision-export-deliveries/instructions", "get"),
        ("/api/platform/offer-decision-export-deliveries/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/status", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/recipients", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/recipients", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/recipients/{recipient_id}/status", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/attachments", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/attachments", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/instructions", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/instructions", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/instructions/{instruction_id}/completion", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff_id}/snapshots", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_manual_delivery_handoff_foundation") or {}
    for key in [
        "delivery_handoffs_enabled",
        "delivery_recipients_enabled",
        "delivery_attachment_metadata_enabled",
        "delivery_instructions_enabled",
        "immutable_delivery_snapshots_enabled",
        "agency_delivery_handoff_ui_enabled",
        "platform_delivery_handoff_ui_enabled",
        "manual_delivery_only_enabled",
        "automatic_sending_disabled",
        "sms_sending_disabled",
        "public_links_disabled",
        "real_pdf_delivery_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "ticket_emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["handoff_count", "recipient_count", "attachment_count", "instruction_count", "snapshot_count"]:
        require_count(section, key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, preview, export, option_ids, before_signature = create_preview_source(agency_id, run_key)
    release_context = create_release_readiness(agency_id, preview, run_key)
    approval = release_context["approval"]
    release_readiness = release_context["readiness"]
    base = f"/api/agencies/{agency_id}/offer-decision-export-deliveries"

    handoff_response = post(
        f"{base}/handoffs",
        {
            "export_id": export["id"],
            "preview_id": preview["id"],
            "approval_id": approval["id"],
            "release_readiness_id": release_readiness["id"],
            "title": f"Smoke manual delivery handoff {run_key}",
            "delivery_method": "manual_email",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    handoff = handoff_response["handoff"]
    if handoff.get("export_id") != export["id"] or handoff.get("preview_id") != preview["id"] or handoff.get("status") != "draft":
        raise AssertionError(f"Handoff not linked or draft: {handoff}")
    for key in ["manual_delivery_only_enabled", "automatic_sending_disabled", "sms_sending_disabled", "public_links_disabled", "real_pdf_delivery_disabled", "provider_execution_disabled", "booking_execution_disabled", "ticket_emd_issuance_disabled", "payment_invoice_settlement_disabled"]:
        if handoff.get(key) is not True or handoff_response.get(key) is not True:
            raise AssertionError(f"Handoff safety flag missing {key}: handoff={handoff} response={handoff_response}")

    recipient_response = post(
        f"{base}/handoffs/{handoff['id']}/recipients",
        {
            "recipient_type": "client",
            "display_name": f"Smoke Client Recipient {run_key}",
            "email_metadata": f"client-{run_key}@example.com metadata only",
            "phone_metadata": "+100000000 metadata only",
            "delivery_method": "manual_email",
            "notes": "Recipient metadata only. No email or SMS was sent.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    recipient = recipient_response["recipient"]
    if recipient.get("delivery_status") != "pending_manual_action" or recipient.get("automatic_sending_disabled") is not True:
        raise AssertionError(f"Recipient metadata has unsafe defaults: {recipient}")

    attachment_response = post(
        f"{base}/handoffs/{handoff['id']}/attachments",
        {
            "preview_id": preview["id"],
            "filename": f"smoke-decision-export-{run_key}.pdf metadata",
            "file_type": "pdf_metadata",
            "source_type": "preview_metadata",
            "size_label": "metadata only",
            "storage_reference_metadata": "no external storage provider was called",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    attachment = attachment_response["attachment"]
    if attachment.get("public_link_created") is not False or attachment.get("real_file_delivered") is not False:
        raise AssertionError(f"Attachment metadata violated delivery boundary: {attachment}")

    instruction_response = post(
        f"{base}/handoffs/{handoff['id']}/instructions",
        {
            "instruction_type": "compliance_note",
            "title": f"Smoke manual handoff instruction {run_key}",
            "body": "Human agent handles any external communication outside AgencyOS; no automatic sending is available here.",
            "required": True,
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    instruction = instruction_response["instruction"]
    if instruction.get("completed") is not False or instruction.get("required") is not True:
        raise AssertionError(f"Instruction metadata defaults changed: {instruction}")

    instruction = patch(
        f"{base}/instructions/{instruction['id']}/completion",
        {"completed": True, "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
    )["instruction"]
    if instruction.get("completed") is not True or not instruction.get("completed_at"):
        raise AssertionError(f"Instruction completion metadata failed: {instruction}")

    recipient = patch(
        f"{base}/recipients/{recipient['id']}/status",
        {"delivery_status": "manually_completed", "notes": "Human action recorded manually; AgencyOS did not send anything.", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
    )["recipient"]
    if recipient.get("delivery_status") != "manually_completed":
        raise AssertionError(f"Recipient manual status update failed: {recipient}")

    handoff = patch(
        f"{base}/handoffs/{handoff['id']}/status",
        {"status": "prepared", "status_reason": "Metadata handoff prepared for human action.", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
    )["handoff"]
    if handoff.get("status") != "prepared":
        raise AssertionError(f"Handoff status update failed: {handoff}")

    snapshot_response = post(
        f"{base}/handoffs/{handoff['id']}/snapshots",
        {"snapshot_type": "prepared", "created_by": "smoke-delivery-reviewer", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    snapshot = snapshot_response["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("metadata_only") is not True:
        raise AssertionError(f"Delivery snapshot was not immutable metadata: {snapshot}")

    detail = get(f"{base}/handoffs/{handoff['id']}", OWNER_HEADERS)
    if recipient["id"] not in ids(detail.get("recipients") or []) or attachment["id"] not in ids(detail.get("attachments") or []):
        raise AssertionError(f"Handoff detail missed recipient or attachment: {detail}")
    if instruction["id"] not in ids(detail.get("instructions") or []) or snapshot["id"] not in ids(detail.get("snapshots") or []):
        raise AssertionError(f"Handoff detail missed instruction or snapshot: {detail}")

    listed_handoffs = get(f"{base}/handoffs?export_id={export['id']}", OWNER_HEADERS)["items"]
    listed_recipients = get(f"{base}/handoffs/{handoff['id']}/recipients", OWNER_HEADERS)["items"]
    listed_attachments = get(f"{base}/handoffs/{handoff['id']}/attachments", OWNER_HEADERS)["items"]
    listed_instructions = get(f"{base}/handoffs/{handoff['id']}/instructions", OWNER_HEADERS)["items"]
    listed_snapshots = get(f"{base}/handoffs/{handoff['id']}/snapshots", OWNER_HEADERS)["items"]
    if handoff["id"] not in ids(listed_handoffs) or recipient["id"] not in ids(listed_recipients):
        raise AssertionError("Agency handoff/recipient lists missed created records.")
    if attachment["id"] not in ids(listed_attachments) or instruction["id"] not in ids(listed_instructions) or snapshot["id"] not in ids(listed_snapshots):
        raise AssertionError("Agency attachment/instruction/snapshot lists missed created records.")

    platform_summary = get("/api/platform/offer-decision-export-deliveries/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform delivery diagnostics changed execution boundary: {platform_summary}")
    platform_handoffs = get("/api/platform/offer-decision-export-deliveries/handoffs", OWNER_HEADERS)["items"]
    platform_recipients = get("/api/platform/offer-decision-export-deliveries/recipients", OWNER_HEADERS)["items"]
    platform_attachments = get("/api/platform/offer-decision-export-deliveries/attachments", OWNER_HEADERS)["items"]
    platform_instructions = get("/api/platform/offer-decision-export-deliveries/instructions", OWNER_HEADERS)["items"]
    platform_snapshots = get("/api/platform/offer-decision-export-deliveries/snapshots", OWNER_HEADERS)["items"]
    if handoff["id"] not in ids(platform_handoffs) or recipient["id"] not in ids(platform_recipients):
        raise AssertionError("Platform diagnostics missed handoff or recipient metadata.")
    if attachment["id"] not in ids(platform_attachments) or instruction["id"] not in ids(platform_instructions) or snapshot["id"] not in ids(platform_snapshots):
        raise AssertionError("Platform diagnostics missed attachment, instruction, or snapshot metadata.")
    platform_detail = get(f"/api/platform/offer-decision-export-deliveries/handoffs/{handoff['id']}", OWNER_HEADERS)
    if platform_detail.get("handoff", {}).get("id") != handoff["id"] or platform_detail.get("read_only") is not True:
        raise AssertionError(f"Platform handoff detail missing read-only metadata: {platform_detail}")
    blocked_status, _ = request(
        "POST",
        "/api/platform/offer-decision-export-deliveries/handoffs",
        {"export_id": export["id"]},
        OWNER_HEADERS,
        expect=405,
    )
    if blocked_status != 405:
        raise AssertionError(f"Platform delivery mutation route unexpectedly available: {blocked_status}")
    unsafe_status, _ = request(
        "POST",
        f"{base}/handoffs/{handoff['id']}/send",
        {"handoff_id": handoff["id"]},
        OWNER_HEADERS,
        expect=404,
    )
    if unsafe_status != 404:
        raise AssertionError(f"Agency send route unexpectedly available: {unsafe_status}")

    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if before_signature != after_signature:
        raise AssertionError(f"Manual delivery handoff mutated offer option pricing/status: before={before_signature} after={after_signature}")
    if any(item.get("status") == "recommended" for item in after_signature.values()):
        raise AssertionError(f"Manual delivery handoff auto-selected an option: {after_signature}")

    final_section = get("/api/readiness").get("offer_decision_export_manual_delivery_handoff_foundation") or {}
    for key in ["handoff_count", "recipient_count", "attachment_count", "instruction_count", "snapshot_count"]:
        if final_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created delivery handoff records: {final_section}")

    smoke_offer_decision_export_release_readiness_foundation()

    print("Offer decision export manual delivery handoff foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
