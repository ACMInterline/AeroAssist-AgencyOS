#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_export_manual_delivery_handoff_foundation import create_release_readiness
from smoke_offer_decision_export_manual_delivery_outcome_foundation import (
    create_handoff,
    main as smoke_offer_decision_export_manual_delivery_outcome_foundation,
)
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
        raise AssertionError(f"Readiness missing offer decision export audit review count {key}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def outcome_signature(outcome_detail: dict) -> dict:
    outcome = outcome_detail["outcome"]
    return {
        "outcome_status": outcome.get("outcome_status"),
        "event_count": outcome.get("event_count"),
        "receipt_count": outcome.get("receipt_count"),
        "issue_count": outcome.get("issue_count"),
        "unresolved_issue_count": outcome.get("unresolved_issue_count"),
        "snapshot_count": outcome.get("snapshot_count"),
    }


def create_audit_source(agency_id: str, run_key: str) -> tuple[dict, dict, dict, set[str], dict]:
    workspace, preview, export, option_ids, before_signature = create_preview_source(agency_id, run_key)
    release_context = create_release_readiness(agency_id, preview, run_key)
    handoff = create_handoff(agency_id, preview, export, release_context["approval"], release_context["readiness"], run_key)

    post(
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/{export['decision_pack_id']}/snapshots",
        {"snapshot_name": f"Smoke audit review decision pack snapshot {run_key}"},
        OWNER_HEADERS,
        201,
    )
    post(
        f"/api/agencies/{agency_id}/offer-decision-export-releases/readiness/{release_context['readiness']['id']}/snapshots",
        {"snapshot_name": f"Smoke audit review release snapshot {run_key}", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    post(
        f"/api/agencies/{agency_id}/offer-decision-export-deliveries/handoffs/{handoff['id']}/snapshots",
        {"snapshot_type": "prepared", "created_by": "smoke-audit-reviewer", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )

    outcome_base = f"/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes"
    outcome = post(
        f"{outcome_base}/outcomes",
        {
            "handoff_id": handoff["id"],
            "title": f"Smoke audit review outcome {run_key}",
            "outcome_status": "manually_sent",
            "actor_type": "agency_user",
            "recorded_by": "smoke-audit-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["outcome"]
    post(
        f"{outcome_base}/outcomes/{outcome['id']}/events",
        {
            "event_type": "sent_recorded",
            "actor_type": "agency_user",
            "actor_label": "smoke-audit-reviewer",
            "event_title": f"Smoke audit review manual event {run_key}",
            "event_note": "Human-recorded delivery event only.",
            "event_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    post(
        f"{outcome_base}/outcomes/{outcome['id']}/receipts",
        {
            "receipt_type": "client_acknowledgement",
            "reference_label": f"Smoke audit receipt {run_key}",
            "received_from": "metadata-only recipient acknowledgement",
            "notes": "Receipt metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    issue = post(
        f"{outcome_base}/outcomes/{outcome['id']}/issues",
        {
            "issue_type": "client_correction_requested",
            "severity": "medium",
            "title": f"Smoke unresolved audit review issue {run_key}",
            "description": "Open issue metadata lets the audit review surface unresolved outcome trail work.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["issue"]
    if issue.get("issue_status") != "open":
        raise AssertionError(f"Audit source issue was not open: {issue}")
    post(
        f"{outcome_base}/outcomes/{outcome['id']}/snapshots",
        {"snapshot_type": "manual", "created_by": "smoke-audit-reviewer", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    return workspace, export, get(f"{outcome_base}/outcomes/{outcome['id']}", OWNER_HEADERS), option_ids, before_signature


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
        if "offer-decision-export-audit-reviews" in path and any(token in path for token in ["/send", "/publish", "public-link", "/execute", "/ticket", "/emd", "/pay", "/invoice", "/settle", "/book", "/charge", "/pnr"]):
            raise AssertionError(f"Decision export audit review execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-export-audit-reviews/summary", "get"),
        ("/api/platform/offer-decision-export-audit-reviews/diagnostics", "get"),
        ("/api/platform/offer-decision-export-audit-reviews/reviews", "get"),
        ("/api/platform/offer-decision-export-audit-reviews/reviews/{review_id}", "get"),
        ("/api/platform/offer-decision-export-audit-reviews/findings", "get"),
        ("/api/platform/offer-decision-export-audit-reviews/checklist-items", "get"),
        ("/api/platform/offer-decision-export-audit-reviews/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/status", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/findings", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/findings/{finding_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/findings", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/checklist-items", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/checklist-items/{item_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/checklist-items", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/reviews/{review_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-audit-reviews/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_audit_review_foundation") or {}
    for key in [
        "audit_reviews_enabled",
        "audit_review_findings_enabled",
        "audit_review_checklists_enabled",
        "immutable_audit_review_snapshots_enabled",
        "agency_audit_review_ui_enabled",
        "platform_audit_review_ui_enabled",
        "metadata_only_review_enabled",
        "automatic_sending_disabled",
        "sms_sending_disabled",
        "public_links_disabled",
        "real_pdf_delivery_disabled",
        "offer_price_mutation_disabled",
        "automatic_recommendation_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticket_emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["review_count", "finding_count", "checklist_item_count", "snapshot_count"]:
        require_count(section, key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, export, outcome_detail, option_ids, before_signature = create_audit_source(agency_id, run_key)
    before_outcome_signature = outcome_signature(outcome_detail)
    outcome = outcome_detail["outcome"]
    base = f"/api/agencies/{agency_id}/offer-decision-export-audit-reviews"

    review_response = post(
        f"{base}/reviews",
        {
            "outcome_id": outcome["id"],
            "title": f"Smoke export audit review {run_key}",
            "review_scope": "full_lifecycle",
            "reviewed_by": "smoke-audit-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    review = review_response["review"]
    if review.get("outcome_id") != outcome["id"] or review.get("export_id") != export["id"] or review.get("review_status") != "draft":
        raise AssertionError(f"Audit review not linked or draft: {review}")
    for key in ["metadata_only_review_enabled", "automatic_sending_disabled", "sms_sending_disabled", "public_links_disabled", "real_pdf_delivery_disabled", "offer_price_mutation_disabled", "automatic_recommendation_disabled", "provider_execution_disabled", "booking_execution_disabled", "pnr_mutation_disabled", "ticket_emd_issuance_disabled", "payment_invoice_settlement_disabled", "scraping_disabled", "external_ai_disabled"]:
        if review_response.get(key) is not True:
            raise AssertionError(f"Audit review response missing safety flag {key}: {review_response}")

    detail = get(f"{base}/reviews/{review['id']}", OWNER_HEADERS)
    if detail["review"].get("checklist_count", 0) < 10 or not detail.get("checklist_items"):
        raise AssertionError(f"Audit review did not create lifecycle checklist items: {detail}")
    source_summary = detail.get("source_summary") or {}
    if source_summary.get("unresolved_delivery_issue_count") != 1:
        raise AssertionError(f"Audit review did not detect unresolved delivery issue: {source_summary}")
    if any(count < 1 for count in (source_summary.get("snapshot_counts") or {}).values()):
        raise AssertionError(f"Audit review did not detect full immutable snapshot coverage: {source_summary}")
    finding_types = {item.get("finding_type") for item in detail.get("findings") or []}
    if "unresolved_delivery_issue" not in finding_types:
        raise AssertionError(f"Audit review did not create unresolved issue finding: {detail.get('findings')}")

    review = patch(
        f"{base}/reviews/{review['id']}/status",
        {
            "review_status": "in_review",
            "status_reason": "Human audit review started.",
            "reviewed_by": "smoke-audit-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["review"]
    if review.get("review_status") != "in_review":
        raise AssertionError(f"Audit review status update failed: {review}")

    manual_finding_response = post(
        f"{base}/reviews/{review['id']}/findings",
        {
            "finding_type": "metadata_gap",
            "severity": "low",
            "title": f"Smoke manual audit finding {run_key}",
            "description": "Human-entered audit review metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    manual_finding = manual_finding_response["finding"]
    manual_finding = patch(
        f"{base}/findings/{manual_finding['id']}",
        {
            "finding_status": "resolved",
            "resolved_by": "smoke-audit-reviewer",
            "resolution_notes": "Resolved in audit review metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["finding"]
    if manual_finding.get("finding_status") != "resolved" or not manual_finding.get("resolved_at"):
        raise AssertionError(f"Audit finding resolution failed: {manual_finding}")

    checklist_response = post(
        f"{base}/reviews/{review['id']}/checklist-items",
        {
            "item_key": f"manual_policy_review_{run_key}",
            "label": "Manual policy review complete",
            "item_status": "pending",
            "required": True,
            "notes": "Human audit checklist metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    checklist_item = patch(
        f"{base}/checklist-items/{checklist_response['checklist_item']['id']}",
        {
            "item_status": "passed",
            "notes": "Human reviewer marked this checklist item as passed.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["checklist_item"]
    if checklist_item.get("item_status") != "passed":
        raise AssertionError(f"Audit checklist update failed: {checklist_item}")

    snapshot_response = post(
        f"{base}/reviews/{review['id']}/snapshots",
        {
            "snapshot_type": "checklist_review",
            "created_by": "smoke-audit-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    snapshot = snapshot_response["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("metadata_only") is not True or snapshot.get("review_id") != review["id"]:
        raise AssertionError(f"Audit review snapshot was not immutable metadata: {snapshot}")

    if review["id"] not in ids(get(f"{base}/reviews?status=in_review", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency audit review status filter did not return created review.")
    if manual_finding["id"] not in ids(get(f"{base}/findings?review_id={review['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency audit review finding list did not return manual finding.")
    if checklist_item["id"] not in ids(get(f"{base}/checklist-items?review_id={review['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency audit review checklist list did not return manual item.")
    if snapshot["id"] not in ids(get(f"{base}/snapshots?review_id={review['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency audit review snapshot list did not return review snapshot.")

    platform_base = "/api/platform/offer-decision-export-audit-reviews"
    platform_summary = get(f"{platform_base}/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform audit review summary is not read-only/safe: {platform_summary}")
    if review["id"] not in ids(get(f"{platform_base}/reviews", OWNER_HEADERS)["items"]):
        raise AssertionError("Platform audit review diagnostics did not include created review.")
    platform_detail = get(f"{platform_base}/reviews/{review['id']}", OWNER_HEADERS)
    if platform_detail.get("read_only") is not True or platform_detail.get("review", {}).get("id") != review["id"]:
        raise AssertionError(f"Platform audit review detail was not read-only: {platform_detail}")
    for path in ["/diagnostics", "/findings", "/checklist-items", "/snapshots"]:
        result = get(f"{platform_base}{path}", OWNER_HEADERS)
        if result.get("read_only") is not True:
            raise AssertionError(f"Platform audit review diagnostics endpoint not read-only: {path} {result}")
    request("POST", f"{platform_base}/reviews", {"outcome_id": outcome["id"]}, OWNER_HEADERS, 405)
    request("POST", f"{base}/reviews/{review['id']}/send", {}, OWNER_HEADERS, 404)

    after_outcome_signature = outcome_signature(get(f"/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome['id']}", OWNER_HEADERS))
    if after_outcome_signature != before_outcome_signature:
        raise AssertionError(f"Audit review mutated delivery outcome counts/status: before={before_outcome_signature} after={after_outcome_signature}")
    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if after_signature != before_signature:
        raise AssertionError("Audit review mutated offer option pricing/status.")

    readiness_after = get("/api/readiness")
    audit_section = readiness_after.get("offer_decision_export_audit_review_foundation") or {}
    for key in ["review_count", "finding_count", "checklist_item_count", "snapshot_count"]:
        if audit_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness audit review count did not increment for {key}: {audit_section}")

    smoke_offer_decision_export_manual_delivery_outcome_foundation()
    print("Offer decision export audit review foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
