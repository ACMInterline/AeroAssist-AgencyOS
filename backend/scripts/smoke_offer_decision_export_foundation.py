#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_pack_foundation import create_advisor_snapshot, option_signature
from smoke_offer_policy_advisor_integration_foundation import create_offer_workspace
from smoke_policy_comparison_service_advisor_foundation import seed_airline_facts


from phase_assertions import application_phase_is_at_least


MINIMUM_PHASE = "phase_37_5_offer_decision_export_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision export count {key}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def create_explanation_records(agency_id: str, pack: dict, options: list[dict], run_key: str) -> dict:
    base = f"/api/agencies/{agency_id}/offer-decision-explanations"
    explanation = post(
        f"{base}/explanations",
        {
            "decision_pack_id": pack["id"],
            "offer_option_id": options[0]["id"],
            "title": f"Smoke export explanation {run_key}",
            "explanation_type": "summary",
            "explanation_text": "Human review explanation for export smoke. No airline was auto-selected.",
            "finalized": True,
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["explanation"]
    reason = post(
        f"{base}/reasons",
        {
            "decision_pack_id": pack["id"],
            "offer_option_id": options[0]["id"],
            "reason_category": "manual",
            "importance": "high",
            "text": f"Smoke export decision reason {run_key}",
        },
        OWNER_HEADERS,
        201,
    )["reason"]
    timeline_event = post(
        f"{base}/timeline-events",
        {
            "decision_pack_id": pack["id"],
            "offer_option_id": options[1]["id"],
            "event_type": "review_completed",
            "actor": "smoke-agent",
            "actor_type": "agency",
            "description": f"Smoke export timeline review {run_key}",
        },
        OWNER_HEADERS,
        201,
    )["timeline_event"]
    acknowledgement = post(
        f"{base}/acknowledgements",
        {
            "decision_pack_id": pack["id"],
            "acknowledged_by": "smoke-agent",
            "acknowledgement_type": "reviewed",
            "notes": f"Smoke export acknowledgement {run_key}",
        },
        OWNER_HEADERS,
        201,
    )["acknowledgement"]
    audit_snapshot = post(
        f"{base}/snapshots",
        {
            "decision_pack_id": pack["id"],
            "snapshot_name": f"Smoke export explanation audit snapshot {run_key}",
        },
        OWNER_HEADERS,
        201,
    )["snapshot"]
    return {
        "explanation": explanation,
        "reason": reason,
        "timeline_event": timeline_event,
        "acknowledgement": acknowledgement,
        "audit_snapshot": audit_snapshot,
    }


def main() -> int:
    run_key = uuid4().hex[:10]
    domain_code = f"smoke_export_{run_key}"
    family_code = f"wheelchair_export_{run_key}"
    variant_code = f"wchr_export_{run_key}"

    health = get("/api/health")
    if not application_phase_is_at_least(health.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "offer-decision-exports" in path and any(token in path for token in ["/execute", "/issue", "/pay", "/invoice", "/settle", "/book", "/send", "public-link"]):
            raise AssertionError(f"Decision export execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-exports/summary", "get"),
        ("/api/platform/offer-decision-exports/exports", "get"),
        ("/api/platform/offer-decision-exports/exports/{export_id}", "get"),
        ("/api/platform/offer-decision-exports/artifacts", "get"),
        ("/api/platform/offer-decision-exports/audit-events", "get"),
        ("/api/agencies/{agency_id}/offer-decision-exports/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-exports/exports", "get"),
        ("/api/agencies/{agency_id}/offer-decision-exports/exports/{export_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-exports/generate", "post"),
        ("/api/agencies/{agency_id}/offer-decision-exports/artifacts", "get"),
        ("/api/agencies/{agency_id}/offer-decision-exports/recipient-drafts", "get"),
        ("/api/agencies/{agency_id}/offer-decision-exports/audit-events", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if not application_phase_is_at_least(readiness.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_foundation") or {}
    for key in [
        "decision_exports_enabled",
        "export_sections_enabled",
        "export_artifacts_enabled",
        "recipient_drafts_enabled",
        "export_audit_events_enabled",
        "pdf_export_metadata_enabled",
        "automatic_sending_disabled",
        "public_links_disabled",
        "offer_price_mutation_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "ticket_emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["export_count", "section_count", "artifact_count", "recipient_draft_count", "audit_event_count"]:
        require_count(section, key)

    for airline_code, amount in [("ZX", 35.0), ("QY", 55.0)]:
        seed_airline_facts(airline_code, domain_code, family_code, variant_code, amount, run_key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, options = create_offer_workspace(agency_id, run_key)
    option_ids = {option["id"] for option in options}
    before_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    advisor_context, advisor_snapshot, _ = create_advisor_snapshot(agency_id, workspace, run_key, domain_code, family_code, variant_code)

    decision_pack_response = post(
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/build",
        {
            "offer_workspace_id": workspace["id"],
            "pack_name": f"Smoke export decision pack {run_key}",
            "advisor_context_ids": [advisor_context["id"]],
            "advisor_saved_snapshot_ids": [advisor_snapshot["id"]],
            "metadata_json": {"run_key": run_key, "phase": "37.5"},
        },
        OWNER_HEADERS,
        201,
    )
    pack = decision_pack_response["pack"]
    explanation_records = create_explanation_records(agency_id, pack, options, run_key)
    if not explanation_records.get("audit_snapshot", {}).get("immutable"):
        raise AssertionError(f"Explanation audit snapshot missing before export: {explanation_records}")

    base = f"/api/agencies/{agency_id}/offer-decision-exports"
    export_response = post(
        f"{base}/generate",
        {
            "decision_pack_id": pack["id"],
            "export_name": f"Smoke decision export {run_key}",
            "include_recipient_draft": True,
            "recipient_type": "client_review",
            "recipient_name": "Smoke Reviewer",
            "recipient_email": f"review-{run_key}@example.com",
            "subject": f"Smoke decision export {run_key}",
            "message_body": "Draft only. No automatic sending or public link was created.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    export = export_response["export"]
    if export.get("decision_pack_id") != pack["id"] or export.get("metadata_only") is not True:
        raise AssertionError(f"Offer decision export not linked or metadata-only: {export}")
    for key in ["automatic_sending_disabled", "public_links_disabled", "offer_price_mutation_disabled", "provider_execution_disabled", "booking_execution_disabled", "ticket_emd_issuance_disabled", "payment_invoice_settlement_disabled"]:
        if export.get(key) is not True or export_response.get(key) is not True:
            raise AssertionError(f"Export safety flag missing {key}: export={export} response={export_response}")
    if export.get("section_count", 0) < 10 or export.get("artifact_count") != 2 or export.get("recipient_draft_count") != 1:
        raise AssertionError(f"Export counts were incomplete: {export}")

    section_keys = {item.get("section_key") for item in export_response.get("sections") or []}
    expected_sections = {"decision_pack", "options", "evidence", "warnings", "review_notes", "explanations", "timeline", "reasons", "acknowledgements", "audit_snapshots"}
    if expected_sections - section_keys:
        raise AssertionError(f"Export missing sections: {expected_sections - section_keys}")

    artifacts = export_response.get("artifacts") or []
    artifact_types = {item.get("artifact_type") for item in artifacts}
    if artifact_types != {"pdf_metadata", "review_json_snapshot"}:
        raise AssertionError(f"Export artifacts missing PDF metadata or JSON snapshot: {artifacts}")
    if any(item.get("file_generated") is not False or item.get("public_link_created") is not False or item.get("automatic_sending_disabled") is not True for item in artifacts):
        raise AssertionError(f"Export artifact violated metadata-only boundary: {artifacts}")

    recipient_drafts = export_response.get("recipient_drafts") or []
    if len(recipient_drafts) != 1 or recipient_drafts[0].get("delivery_status") != "draft" or recipient_drafts[0].get("sent_at") is not None:
        raise AssertionError(f"Recipient draft was sent or incomplete: {recipient_drafts}")
    if recipient_drafts[0].get("automatic_sending_disabled") is not True or recipient_drafts[0].get("public_links_disabled") is not True:
        raise AssertionError(f"Recipient draft safety flags missing: {recipient_drafts[0]}")

    audit_event_types = {item.get("event_type") for item in export_response.get("audit_events") or []}
    if "generated" not in audit_event_types or "recipient_draft_created" not in audit_event_types:
        raise AssertionError(f"Export audit events missing generated/draft events: {export_response.get('audit_events')}")

    detail = get(f"{base}/exports/{export['id']}", OWNER_HEADERS)
    if detail.get("export", {}).get("id") != export["id"] or len(detail.get("sections") or []) < 10:
        raise AssertionError(f"Export detail missed sections: {detail}")
    listed_exports = get(f"{base}/exports?decision_pack_id={pack['id']}", OWNER_HEADERS)["items"]
    listed_artifacts = get(f"{base}/artifacts?export_id={export['id']}", OWNER_HEADERS)["items"]
    listed_drafts = get(f"{base}/recipient-drafts?export_id={export['id']}", OWNER_HEADERS)["items"]
    listed_audit = get(f"{base}/audit-events?export_id={export['id']}", OWNER_HEADERS)["items"]
    if export["id"] not in ids(listed_exports) or {item["id"] for item in artifacts} - ids(listed_artifacts):
        raise AssertionError("Agency export/artifact lists missed created records.")
    if recipient_drafts[0]["id"] not in ids(listed_drafts) or not listed_audit:
        raise AssertionError("Agency recipient draft/audit lists missed created records.")

    platform_summary = get("/api/platform/offer-decision-exports/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform export diagnostics changed execution boundary: {platform_summary}")
    platform_exports = get("/api/platform/offer-decision-exports/exports", OWNER_HEADERS)["items"]
    platform_artifacts = get("/api/platform/offer-decision-exports/artifacts", OWNER_HEADERS)["items"]
    platform_audit = get("/api/platform/offer-decision-exports/audit-events", OWNER_HEADERS)["items"]
    if export["id"] not in ids(platform_exports):
        raise AssertionError("Platform diagnostics did not list offer decision export.")
    if {item["id"] for item in artifacts} - ids(platform_artifacts) or not platform_audit:
        raise AssertionError("Platform diagnostics missed export artifacts or audit events.")

    platform_blocked_status, _ = request(
        "POST",
        "/api/platform/offer-decision-exports/exports",
        {"decision_pack_id": pack["id"]},
        OWNER_HEADERS,
        expect=405,
    )
    if platform_blocked_status != 405:
        raise AssertionError(f"Platform export mutation route unexpectedly available: {platform_blocked_status}")
    agency_artifact_blocked_status, _ = request(
        "POST",
        f"{base}/artifacts",
        {"export_id": export["id"]},
        OWNER_HEADERS,
        expect=405,
    )
    if agency_artifact_blocked_status != 405:
        raise AssertionError(f"Agency artifact mutation route unexpectedly available: {agency_artifact_blocked_status}")

    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if before_signature != after_signature:
        raise AssertionError(f"Decision export mutated offer option pricing/status: before={before_signature} after={after_signature}")
    if any(item.get("status") == "recommended" for item in after_signature.values()):
        raise AssertionError(f"Decision export auto-selected an option: {after_signature}")

    final_section = get("/api/readiness").get("offer_decision_export_foundation") or {}
    for key in ["export_count", "section_count", "artifact_count", "recipient_draft_count", "audit_event_count"]:
        if final_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created export records: {final_section}")

    print("Offer decision export foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
