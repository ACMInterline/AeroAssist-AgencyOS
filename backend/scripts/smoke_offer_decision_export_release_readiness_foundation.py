#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_export_preview_foundation import main as smoke_offer_decision_export_preview_foundation
from smoke_offer_decision_export_foundation import create_explanation_records
from smoke_offer_decision_pack_foundation import create_advisor_snapshot, option_signature
from smoke_offer_policy_advisor_integration_foundation import create_offer_workspace
from smoke_policy_comparison_service_advisor_foundation import seed_airline_facts


EXPECTED_PHASE = "phase_39_2_airline_intelligence_knowledge_versioning_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision export release count {key}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def create_preview_source(agency_id: str, run_key: str) -> tuple[dict, dict, dict, set[str], dict]:
    domain_code = f"smoke_release_{run_key}"
    family_code = f"wheelchair_release_{run_key}"
    variant_code = f"wchr_release_{run_key}"
    for airline_code, amount in [("RX", 35.0), ("RY", 55.0)]:
        seed_airline_facts(airline_code, domain_code, family_code, variant_code, amount, run_key)

    workspace, options = create_offer_workspace(agency_id, run_key)
    option_ids = {option["id"] for option in options}
    before_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    advisor_context, advisor_snapshot, _ = create_advisor_snapshot(agency_id, workspace, run_key, domain_code, family_code, variant_code)

    decision_pack_response = post(
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/build",
        {
            "offer_workspace_id": workspace["id"],
            "pack_name": f"Smoke release readiness decision pack {run_key}",
            "advisor_context_ids": [advisor_context["id"]],
            "advisor_saved_snapshot_ids": [advisor_snapshot["id"]],
            "metadata_json": {"run_key": run_key, "phase": "37.7"},
        },
        OWNER_HEADERS,
        201,
    )
    pack = decision_pack_response["pack"]
    create_explanation_records(agency_id, pack, options, run_key)

    export_base = f"/api/agencies/{agency_id}/offer-decision-exports"
    export_response = post(
        f"{export_base}/generate",
        {
            "decision_pack_id": pack["id"],
            "export_name": f"Smoke release readiness export source {run_key}",
            "include_recipient_draft": True,
            "recipient_type": "agency_review",
            "recipient_name": "Release Reviewer",
            "recipient_email": f"release-{run_key}@example.com",
            "subject": f"Smoke release source {run_key}",
            "message_body": "Draft only. No automatic sending or public link was created.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    export = export_response["export"]
    artifact_ids = [item["id"] for item in export_response.get("artifacts") or []]

    preview_base = f"/api/agencies/{agency_id}/offer-decision-export-previews"
    preview_response = post(
        f"{preview_base}/generate",
        {
            "export_id": export["id"],
            "render_profile": "manual_release_review",
            "template_profile": "smoke_release_metadata_preview",
            "reviewed_by": "smoke-release-reviewer",
            "source_artifact_ids": artifact_ids,
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    preview = preview_response["preview"]
    post(
        f"{preview_base}/previews/{preview['id']}/validate",
        {"internal_reviewer": "smoke-release-reviewer", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    post(
        f"{preview_base}/previews/{preview['id']}/snapshots",
        {"snapshot_name": f"Smoke release preview snapshot {run_key}", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    return workspace, preview, export, option_ids, before_signature


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
        if "offer-decision-export-releases" in path and any(token in path for token in ["/execute", "/issue", "/pay", "/invoice", "/settle", "/book", "/send", "public-link"]):
            raise AssertionError(f"Decision export release execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-export-releases/summary", "get"),
        ("/api/platform/offer-decision-export-releases/approvals", "get"),
        ("/api/platform/offer-decision-export-releases/readiness", "get"),
        ("/api/platform/offer-decision-export-releases/holds", "get"),
        ("/api/platform/offer-decision-export-releases/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/approvals", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/approvals", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/approvals/{approval_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/approvals/{approval_id}/checkpoints", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/approvals/{approval_id}/checkpoints", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/approvals/{approval_id}/status", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness/{readiness_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness/{readiness_id}/holds", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness/{readiness_id}/holds", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness/{readiness_id}/holds/{hold_id}/release", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness/{readiness_id}/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-releases/readiness/{readiness_id}/snapshots", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_release_readiness_foundation") or {}
    for key in [
        "export_approvals_enabled",
        "approval_checkpoints_enabled",
        "release_readiness_enabled",
        "release_holds_enabled",
        "immutable_release_snapshots_enabled",
        "agency_export_release_ui_enabled",
        "platform_export_release_ui_enabled",
        "human_approval_required_enabled",
        "automatic_sending_disabled",
        "public_links_disabled",
        "real_pdf_delivery_disabled",
        "offer_price_mutation_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "ticket_emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["approval_count", "checkpoint_count", "readiness_count", "hold_count", "snapshot_count"]:
        require_count(section, key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, preview, export, option_ids, before_signature = create_preview_source(agency_id, run_key)
    base = f"/api/agencies/{agency_id}/offer-decision-export-releases"

    approval_response = post(
        f"{base}/approvals",
        {
            "preview_id": preview["id"],
            "approval_name": f"Smoke manual release approval {run_key}",
            "assigned_reviewer": "smoke-release-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    approval = approval_response["approval"]
    if approval.get("preview_id") != preview["id"] or approval.get("export_id") != export["id"] or approval.get("approval_status") != "draft":
        raise AssertionError(f"Approval not linked to preview/export: {approval}")
    for key in ["automatic_sending_disabled", "public_links_disabled", "real_pdf_delivery_disabled", "offer_price_mutation_disabled", "provider_execution_disabled", "booking_execution_disabled", "ticket_emd_issuance_disabled", "payment_invoice_settlement_disabled"]:
        if approval.get(key) is not True or approval_response.get(key) is not True:
            raise AssertionError(f"Approval safety flag missing {key}: approval={approval} response={approval_response}")

    checkpoint_response = post(
        f"{base}/approvals/{approval['id']}/checkpoints",
        {
            "checkpoint_type": "safety_boundary_review",
            "checkpoint_status": "passed",
            "checkpoint_title": f"Smoke release safety review {run_key}",
            "notes": "Human reviewer confirmed metadata-only release readiness boundaries.",
            "checkpoint_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    checkpoint = checkpoint_response["checkpoint"]
    if checkpoint.get("approval_id") != approval["id"] or checkpoint.get("sequence_order") != 1 or checkpoint.get("metadata_only") is not True:
        raise AssertionError(f"Checkpoint not linked or ordered: {checkpoint}")

    approved_response = post(
        f"{base}/approvals/{approval['id']}/status",
        {
            "approval_status": "approved",
            "status_reason": "Smoke human approval for manual release readiness.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )
    approval = approved_response["approval"]
    if approval.get("approval_status") != "approved" or approval.get("checkpoint_count", 0) < 1:
        raise AssertionError(f"Approval status update failed: {approval}")

    readiness_response = post(
        f"{base}/readiness",
        {
            "approval_id": approval["id"],
            "readiness_name": f"Smoke manual release readiness {run_key}",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    release_readiness = readiness_response["readiness"]
    if release_readiness.get("readiness_status") != "ready_for_manual_release" or release_readiness.get("ready_for_manual_release") is not True:
        raise AssertionError(f"Approved readiness was not ready: {release_readiness}")
    for key in ["automatic_sending_disabled", "public_links_disabled", "real_pdf_delivery_disabled", "offer_price_mutation_disabled", "provider_execution_disabled", "booking_execution_disabled", "ticket_emd_issuance_disabled", "payment_invoice_settlement_disabled"]:
        if release_readiness.get(key) is not True or readiness_response.get(key) is not True:
            raise AssertionError(f"Readiness safety flag missing {key}: readiness={release_readiness} response={readiness_response}")

    hold_response = post(
        f"{base}/readiness/{release_readiness['id']}/holds",
        {
            "hold_type": "manual_review",
            "severity": "medium",
            "title": f"Smoke manual release hold {run_key}",
            "reason": "Temporary hold for smoke release readiness review.",
            "hold_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    hold = hold_response["hold"]
    release_readiness = hold_response["readiness"]
    if hold.get("hold_status") != "active" or release_readiness.get("active_hold_count") != 1 or release_readiness.get("ready_for_manual_release") is not False:
        raise AssertionError(f"Release hold did not block readiness: hold={hold} readiness={release_readiness}")

    release_response = post(
        f"{base}/readiness/{release_readiness['id']}/holds/{hold['id']}/release",
        {"release_notes": "Smoke hold released after manual metadata review.", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
    )
    hold = release_response["hold"]
    release_readiness = release_response["readiness"]
    if hold.get("hold_status") != "released" or release_readiness.get("active_hold_count") != 0 or release_readiness.get("ready_for_manual_release") is not True:
        raise AssertionError(f"Release hold did not restore readiness: hold={hold} readiness={release_readiness}")

    snapshot_response = post(
        f"{base}/readiness/{release_readiness['id']}/snapshots",
        {"snapshot_name": f"Smoke release readiness snapshot {run_key}", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    snapshot = snapshot_response["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("metadata_only") is not True:
        raise AssertionError(f"Release snapshot was not immutable metadata: {snapshot}")

    approval_detail = get(f"{base}/approvals/{approval['id']}", OWNER_HEADERS)
    readiness_detail = get(f"{base}/readiness/{release_readiness['id']}", OWNER_HEADERS)
    if checkpoint["id"] not in ids(approval_detail.get("checkpoints") or []):
        raise AssertionError(f"Approval detail missed checkpoint: {approval_detail}")
    if hold["id"] not in ids(readiness_detail.get("holds") or []) or snapshot["id"] not in ids(readiness_detail.get("snapshots") or []):
        raise AssertionError(f"Readiness detail missed hold or snapshot: {readiness_detail}")

    listed_approvals = get(f"{base}/approvals?preview_id={preview['id']}", OWNER_HEADERS)["items"]
    listed_checkpoints = get(f"{base}/approvals/{approval['id']}/checkpoints", OWNER_HEADERS)["items"]
    listed_readiness = get(f"{base}/readiness?approval_id={approval['id']}", OWNER_HEADERS)["items"]
    listed_holds = get(f"{base}/readiness/{release_readiness['id']}/holds", OWNER_HEADERS)["items"]
    listed_snapshots = get(f"{base}/readiness/{release_readiness['id']}/snapshots", OWNER_HEADERS)["items"]
    if approval["id"] not in ids(listed_approvals) or checkpoint["id"] not in ids(listed_checkpoints):
        raise AssertionError("Agency approval/checkpoint lists missed created records.")
    if release_readiness["id"] not in ids(listed_readiness) or hold["id"] not in ids(listed_holds) or snapshot["id"] not in ids(listed_snapshots):
        raise AssertionError("Agency readiness/hold/snapshot lists missed created records.")

    platform_summary = get("/api/platform/offer-decision-export-releases/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform release diagnostics changed execution boundary: {platform_summary}")
    platform_approvals = get("/api/platform/offer-decision-export-releases/approvals", OWNER_HEADERS)["items"]
    platform_readiness = get("/api/platform/offer-decision-export-releases/readiness", OWNER_HEADERS)["items"]
    platform_holds = get("/api/platform/offer-decision-export-releases/holds", OWNER_HEADERS)["items"]
    platform_snapshots = get("/api/platform/offer-decision-export-releases/snapshots", OWNER_HEADERS)["items"]
    if approval["id"] not in ids(platform_approvals) or release_readiness["id"] not in ids(platform_readiness):
        raise AssertionError("Platform diagnostics did not list approval/readiness records.")
    if hold["id"] not in ids(platform_holds) or snapshot["id"] not in ids(platform_snapshots):
        raise AssertionError("Platform diagnostics missed hold or snapshot records.")
    platform_blocked_status, _ = request(
        "POST",
        "/api/platform/offer-decision-export-releases/approvals",
        {"preview_id": preview["id"]},
        OWNER_HEADERS,
        expect=405,
    )
    if platform_blocked_status != 405:
        raise AssertionError(f"Platform release mutation route unexpectedly available: {platform_blocked_status}")
    agency_send_status, _ = request(
        "POST",
        f"{base}/readiness/{release_readiness['id']}/send",
        {"readiness_id": release_readiness["id"]},
        OWNER_HEADERS,
        expect=404,
    )
    if agency_send_status != 404:
        raise AssertionError(f"Agency release send route unexpectedly available: {agency_send_status}")

    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if before_signature != after_signature:
        raise AssertionError(f"Decision export release readiness mutated offer option pricing/status: before={before_signature} after={after_signature}")
    if any(item.get("status") == "recommended" for item in after_signature.values()):
        raise AssertionError(f"Decision export release readiness auto-selected an option: {after_signature}")

    final_section = get("/api/readiness").get("offer_decision_export_release_readiness_foundation") or {}
    for key in ["approval_count", "checkpoint_count", "readiness_count", "hold_count", "snapshot_count"]:
        if final_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created release records: {final_section}")

    smoke_offer_decision_export_preview_foundation()

    print("Offer decision export release readiness foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
