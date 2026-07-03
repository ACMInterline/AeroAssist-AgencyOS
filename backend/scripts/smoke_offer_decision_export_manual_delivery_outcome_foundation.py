#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_export_manual_delivery_handoff_foundation import create_release_readiness, main as smoke_offer_decision_export_manual_delivery_handoff_foundation
from smoke_offer_decision_export_release_readiness_foundation import create_preview_source
from smoke_offer_decision_pack_foundation import option_signature


EXPECTED_PHASE = "phase_39_0_airline_intelligence_data_pack_foundation"


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision export delivery outcome count {key}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def create_handoff(agency_id: str, preview: dict, export: dict, approval: dict, release_readiness: dict, run_key: str) -> dict:
    base = f"/api/agencies/{agency_id}/offer-decision-export-deliveries"
    response = post(
        f"{base}/handoffs",
        {
            "export_id": export["id"],
            "preview_id": preview["id"],
            "approval_id": approval["id"],
            "release_readiness_id": release_readiness["id"],
            "title": f"Smoke manual delivery handoff for outcome {run_key}",
            "delivery_method": "manual_email",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    handoff = response["handoff"]
    post(
        f"{base}/handoffs/{handoff['id']}/recipients",
        {
            "recipient_type": "client",
            "display_name": f"Smoke outcome recipient {run_key}",
            "email_metadata": f"client-{run_key}@example.com metadata only",
            "delivery_method": "manual_email",
            "notes": "Recipient metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    return get(f"{base}/handoffs/{handoff['id']}", OWNER_HEADERS)["handoff"]


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
        if "offer-decision-export-delivery-outcomes" in path and any(token in path for token in ["/send", "/publish", "public-link", "/execute", "/ticket", "/emd", "/pay", "/invoice", "/settle", "/book", "/charge"]):
            raise AssertionError(f"Decision export delivery outcome execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-export-delivery-outcomes/summary", "get"),
        ("/api/platform/offer-decision-export-delivery-outcomes/outcomes", "get"),
        ("/api/platform/offer-decision-export-delivery-outcomes/outcomes/{outcome_id}", "get"),
        ("/api/platform/offer-decision-export-delivery-outcomes/events", "get"),
        ("/api/platform/offer-decision-export-delivery-outcomes/receipts", "get"),
        ("/api/platform/offer-decision-export-delivery-outcomes/issues", "get"),
        ("/api/platform/offer-decision-export-delivery-outcomes/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome_id}/events", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/events", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome_id}/receipts", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/receipts", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome_id}/issues", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/issues/{issue_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/issues", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_manual_delivery_outcome_foundation") or {}
    for key in [
        "delivery_outcomes_enabled",
        "delivery_outcome_events_enabled",
        "delivery_receipts_enabled",
        "delivery_issues_enabled",
        "immutable_outcome_snapshots_enabled",
        "agency_delivery_outcome_ui_enabled",
        "platform_delivery_outcome_ui_enabled",
        "manual_tracking_only_enabled",
        "automatic_sending_disabled",
        "sms_sending_disabled",
        "public_links_disabled",
        "real_pdf_delivery_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticket_emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["outcome_count", "event_count", "receipt_count", "issue_count", "snapshot_count"]:
        require_count(section, key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, preview, export, option_ids, before_signature = create_preview_source(agency_id, run_key)
    release_context = create_release_readiness(agency_id, preview, run_key)
    handoff = create_handoff(agency_id, preview, export, release_context["approval"], release_context["readiness"], run_key)
    handoff_signature = {
        "status": handoff.get("status"),
        "recipient_count": handoff.get("recipient_count"),
        "attachment_count": handoff.get("attachment_count"),
        "instruction_count": handoff.get("instruction_count"),
        "snapshot_count": handoff.get("snapshot_count"),
    }
    base = f"/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes"

    outcome_response = post(
        f"{base}/outcomes",
        {
            "handoff_id": handoff["id"],
            "title": f"Smoke manual delivery outcome {run_key}",
            "outcome_status": "pending",
            "actor_type": "agency_user",
            "recorded_by": "smoke-outcome-agent",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    outcome = outcome_response["outcome"]
    if outcome.get("handoff_id") != handoff["id"] or outcome.get("outcome_status") != "pending":
        raise AssertionError(f"Outcome not linked or pending: {outcome}")
    for key in ["manual_tracking_only_enabled", "automatic_sending_disabled", "sms_sending_disabled", "public_links_disabled", "real_pdf_delivery_disabled", "provider_execution_disabled", "booking_execution_disabled", "pnr_mutation_disabled", "ticket_emd_issuance_disabled", "payment_invoice_settlement_disabled"]:
        if outcome.get(key) is not True or outcome_response.get(key) is not True:
            raise AssertionError(f"Outcome safety flag missing {key}: outcome={outcome} response={outcome_response}")

    outcome = patch(
        f"{base}/outcomes/{outcome['id']}",
        {
            "outcome_status": "manually_sent",
            "status_reason": "Human recorded external delivery outcome. AgencyOS did not send anything.",
            "actor_type": "agency_user",
            "recorded_by": "smoke-outcome-agent",
            "metadata_json": {"run_key": run_key, "manual_status_only": True},
        },
        OWNER_HEADERS,
    )["outcome"]
    if outcome.get("outcome_status") != "manually_sent":
        raise AssertionError(f"Outcome status was not updated: {outcome}")

    event = post(
        f"{base}/outcomes/{outcome['id']}/events",
        {
            "event_type": "sent_recorded",
            "actor_type": "agency_user",
            "actor_label": "smoke-outcome-agent",
            "event_title": f"Smoke manual outcome event {run_key}",
            "event_note": "Human-recorded event only. No email, SMS, file delivery, or provider execution occurred.",
            "event_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["event"]
    if event.get("event_type") != "sent_recorded" or event.get("metadata_only") is not True:
        raise AssertionError(f"Unexpected outcome event: {event}")

    receipt = post(
        f"{base}/outcomes/{outcome['id']}/receipts",
        {
            "receipt_type": "client_acknowledgement",
            "reference_label": f"Smoke receipt reference {run_key}",
            "received_from": "metadata-only client reference",
            "notes": "Receipt metadata only; no public link or delivered file was created.",
            "external_reference_metadata": "external reference text only",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["receipt"]
    if receipt.get("receipt_type") != "client_acknowledgement" or receipt.get("public_links_disabled") is not True:
        raise AssertionError(f"Unexpected receipt metadata: {receipt}")

    issue = post(
        f"{base}/outcomes/{outcome['id']}/issues",
        {
            "issue_type": "delivery_failed",
            "severity": "medium",
            "title": f"Smoke manual delivery issue {run_key}",
            "description": "Issue metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["issue"]
    if issue.get("issue_status") != "open":
        raise AssertionError(f"Issue not opened: {issue}")
    issue = patch(
        f"{base}/issues/{issue['id']}",
        {
            "issue_status": "resolved",
            "resolved_by": "smoke-outcome-agent",
            "resolution_notes": "Human-recorded resolution metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["issue"]
    if issue.get("issue_status") != "resolved" or issue.get("resolved_at") is None:
        raise AssertionError(f"Issue not resolved: {issue}")

    snapshot = post(
        f"{base}/outcomes/{outcome['id']}/snapshots",
        {
            "snapshot_type": "outcome_recorded",
            "created_by": "smoke-outcome-agent",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("metadata_only") is not True:
        raise AssertionError(f"Outcome snapshot not immutable metadata: {snapshot}")

    detail = get(f"{base}/outcomes/{outcome['id']}", OWNER_HEADERS)
    if event["id"] not in ids(detail["events"]) or receipt["id"] not in ids(detail["receipts"]) or issue["id"] not in ids(detail["issues"]) or snapshot["id"] not in ids(detail["snapshots"]):
        raise AssertionError(f"Outcome detail missing child metadata: {detail}")
    if detail["outcome"].get("event_count") < 1 or detail["outcome"].get("receipt_count") < 1 or detail["outcome"].get("issue_count") < 1 or detail["outcome"].get("snapshot_count") < 1:
        raise AssertionError(f"Outcome counts were not refreshed: {detail['outcome']}")

    if outcome["id"] not in ids(get(f"{base}/outcomes?status=manually_sent", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency outcome status filter did not return created outcome.")
    if event["id"] not in ids(get(f"{base}/events?outcome_id={outcome['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency event list did not return created event.")
    if receipt["id"] not in ids(get(f"{base}/receipts?outcome_id={outcome['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency receipt list did not return created receipt.")
    if issue["id"] not in ids(get(f"{base}/issues?outcome_id={outcome['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency issue list did not return created issue.")
    if snapshot["id"] not in ids(get(f"{base}/snapshots?outcome_id={outcome['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency snapshot list did not return created snapshot.")

    platform_base = "/api/platform/offer-decision-export-delivery-outcomes"
    platform_summary = get(f"{platform_base}/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("manual_tracking_only_enabled") is not True:
        raise AssertionError(f"Platform summary not read-only/safe: {platform_summary}")
    if outcome["id"] not in ids(get(f"{platform_base}/outcomes", OWNER_HEADERS)["items"]):
        raise AssertionError("Platform outcome diagnostics did not include created outcome.")
    platform_detail = get(f"{platform_base}/outcomes/{outcome['id']}", OWNER_HEADERS)
    if platform_detail.get("read_only") is not True or platform_detail.get("outcome", {}).get("id") != outcome["id"]:
        raise AssertionError(f"Platform outcome detail not read-only: {platform_detail}")
    for path in ["/events", "/receipts", "/issues", "/snapshots"]:
        result = get(f"{platform_base}{path}", OWNER_HEADERS)
        if result.get("read_only") is not True:
            raise AssertionError(f"Platform diagnostics endpoint not read-only: {path} {result}")
    request("POST", f"{platform_base}/outcomes", {"handoff_id": handoff["id"]}, OWNER_HEADERS, 405)
    request("POST", f"{base}/outcomes/{outcome['id']}/send", {}, OWNER_HEADERS, 404)

    after_handoff = get(f"/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff['id']}", OWNER_HEADERS)["handoff"]
    after_handoff_signature = {
        "status": after_handoff.get("status"),
        "recipient_count": after_handoff.get("recipient_count"),
        "attachment_count": after_handoff.get("attachment_count"),
        "instruction_count": after_handoff.get("instruction_count"),
        "snapshot_count": after_handoff.get("snapshot_count"),
    }
    if after_handoff_signature != handoff_signature:
        raise AssertionError(f"Outcome tracking mutated handoff counts/status: before={handoff_signature} after={after_handoff_signature}")
    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if after_signature != before_signature:
        raise AssertionError("Offer option/pricing signature changed during outcome tracking.")

    readiness_after = get("/api/readiness")
    outcome_section = readiness_after.get("offer_decision_export_manual_delivery_outcome_foundation") or {}
    for key in ["outcome_count", "event_count", "receipt_count", "issue_count", "snapshot_count"]:
        if outcome_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness outcome count did not increment for {key}: {outcome_section}")

    smoke_offer_decision_export_manual_delivery_handoff_foundation()
    print("Offer decision export manual delivery outcome foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
