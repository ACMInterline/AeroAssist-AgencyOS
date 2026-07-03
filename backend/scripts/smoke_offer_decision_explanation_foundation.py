#!/usr/bin/env python3
from uuid import uuid4

from smoke_airline_policy_ingestion_foundation import main as policy_ingestion_smoke_main
from smoke_ancillary_pricing_exception_foundation import main as pricing_smoke_main
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_pack_foundation import create_advisor_snapshot, main as decision_pack_smoke_main, option_signature
from smoke_offer_policy_advisor_integration_foundation import create_offer_workspace, main as offer_advisor_smoke_main
from smoke_policy_comparison_service_advisor_foundation import main as comparison_smoke_main, seed_airline_facts
from smoke_service_mechanics_mapping_foundation import main as mechanics_smoke_main
from smoke_service_taxonomy_foundation import main as taxonomy_smoke_main


EXPECTED_PHASE = "phase_38_0_offer_decision_export_audit_review_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision explanation count {key}")


def list_ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def main() -> int:
    run_key = uuid4().hex[:10]
    domain_code = f"smoke_explanation_{run_key}"
    family_code = f"wheelchair_explanation_{run_key}"
    variant_code = f"wchr_explanation_{run_key}"

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "offer-decision-explanations" in path and any(token in path for token in ["/execute", "/issue", "/pay", "/invoice", "/settle", "/book"]):
            raise AssertionError(f"Decision explanation execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-explanations/summary", "get"),
        ("/api/platform/offer-decision-explanations/explanations", "get"),
        ("/api/platform/offer-decision-explanations/timeline", "get"),
        ("/api/platform/offer-decision-explanations/evidence", "get"),
        ("/api/platform/offer-decision-explanations/reasons", "get"),
        ("/api/platform/offer-decision-explanations/acknowledgements", "get"),
        ("/api/platform/offer-decision-explanations/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/explanations", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/explanations", "post"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/explanations/{explanation_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/timeline", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/timeline-events", "post"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/evidence", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/reasons", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/reasons", "post"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/reasons/{reason_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/acknowledgements", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/acknowledgements", "post"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-explanations/snapshots", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_explanation_foundation") or {}
    for key in [
        "decision_explanations_enabled",
        "decision_timeline_enabled",
        "decision_reasons_enabled",
        "evidence_reference_enabled",
        "acknowledgements_enabled",
        "immutable_snapshots_enabled",
        "agency_ui_enabled",
        "platform_ui_enabled",
        "human_review_only_enabled",
        "provider_execution_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "emd_disabled",
        "payment_disabled",
        "invoice_disabled",
        "settlement_disabled",
        "automatic_recommendation_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["explanations", "timeline_events", "reasons", "evidence_references", "acknowledgements", "snapshots"]:
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
            "pack_name": f"Smoke explanation decision pack {run_key}",
            "advisor_context_ids": [advisor_context["id"]],
            "advisor_saved_snapshot_ids": [advisor_snapshot["id"]],
            "metadata_json": {"run_key": run_key, "phase": "37.4"},
        },
        OWNER_HEADERS,
        201,
    )
    pack = decision_pack_response["pack"]

    base = f"/api/agencies/{agency_id}/offer-decision-explanations"
    summary = get(f"{base}/summary", OWNER_HEADERS)
    if summary.get("metadata_only") is not True or summary.get("provider_execution_disabled") is not True:
        raise AssertionError(f"Agency explanation summary changed safety boundary: {summary}")

    explanation_response = post(
        f"{base}/explanations",
        {
            "decision_pack_id": pack["id"],
            "offer_option_id": options[0]["id"],
            "title": f"Smoke decision explanation {run_key}",
            "explanation_type": "policy",
            "explanation_text": "Human-reviewed policy explanation. No airline was auto-ranked, priced, booked, or selected.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    explanation = explanation_response["explanation"]
    if explanation.get("metadata_only") is not True or explanation.get("automatic_recommendation_disabled") is not True:
        raise AssertionError(f"Decision explanation safety flags missing: {explanation}")
    if not explanation_response.get("evidence_references"):
        raise AssertionError(f"Decision explanation did not derive evidence references: {explanation_response}")
    if explanation_response.get("provider_execution_disabled") is not True:
        raise AssertionError(f"Decision explanation response changed execution boundary: {explanation_response}")

    finalized = request(
        "PATCH",
        f"{base}/explanations/{explanation['id']}",
        {"finalized": True},
        OWNER_HEADERS,
        expect=200,
    )[1]["explanation"]
    if finalized.get("finalized") is not True or not finalized.get("finalized_at"):
        raise AssertionError(f"Decision explanation did not finalize: {finalized}")
    immutable_status, _ = request(
        "PATCH",
        f"{base}/explanations/{explanation['id']}",
        {"title": "Blocked finalized update"},
        OWNER_HEADERS,
        expect=400,
    )
    if immutable_status != 400:
        raise AssertionError(f"Finalized decision explanation was mutable: {immutable_status}")
    archived = request(
        "PATCH",
        f"{base}/explanations/{explanation['id']}",
        {"archived": True},
        OWNER_HEADERS,
        expect=200,
    )[1]["explanation"]
    if archived.get("archived") is not True:
        raise AssertionError(f"Finalized explanation archive state did not update: {archived}")

    reason = post(
        f"{base}/reasons",
        {
            "decision_pack_id": pack["id"],
            "offer_option_id": options[0]["id"],
            "reason_category": "policy",
            "importance": "high",
            "text": f"Smoke policy reason {run_key}",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["reason"]
    if reason.get("ai_generated") is not False or reason.get("metadata_only") is not True:
        raise AssertionError(f"Decision reason safety flags missing: {reason}")
    updated_reason = request(
        "PATCH",
        f"{base}/reasons/{reason['id']}",
        {"importance": "critical"},
        OWNER_HEADERS,
        expect=200,
    )[1]["reason"]
    if updated_reason.get("importance") != "critical":
        raise AssertionError(f"Decision reason did not update: {updated_reason}")

    timeline_event = post(
        f"{base}/timeline-events",
        {
            "decision_pack_id": pack["id"],
            "offer_option_id": options[1]["id"],
            "event_type": "manual_override_recorded",
            "actor": "smoke-agent",
            "actor_type": "agency",
            "description": f"Smoke manual review timeline event {run_key}",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["timeline_event"]
    if timeline_event.get("workflow_automation_disabled") is not True:
        raise AssertionError(f"Timeline event changed workflow boundary: {timeline_event}")

    acknowledgement = post(
        f"{base}/acknowledgements",
        {
            "decision_pack_id": pack["id"],
            "acknowledged_by": "smoke-agent",
            "acknowledgement_type": "reviewed",
            "notes": f"Smoke acknowledgement {run_key}",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["acknowledgement"]
    if acknowledgement.get("human_review_only") is not True:
        raise AssertionError(f"Decision acknowledgement safety flags missing: {acknowledgement}")

    snapshot = post(
        f"{base}/snapshots",
        {
            "decision_pack_id": pack["id"],
            "snapshot_name": f"Smoke decision explanation snapshot {run_key}",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("decision_pack_id") != pack["id"]:
        raise AssertionError(f"Decision explanation snapshot was not immutable or linked: {snapshot}")
    if not snapshot.get("explanation_ids") or not snapshot.get("timeline_event_ids") or not snapshot.get("evidence_reference_ids"):
        raise AssertionError(f"Decision explanation snapshot missing audit ids: {snapshot}")

    explanations = get(f"{base}/explanations?decision_pack_id={pack['id']}", OWNER_HEADERS)["items"]
    timeline = get(f"{base}/timeline?decision_pack_id={pack['id']}", OWNER_HEADERS)["items"]
    evidence = get(f"{base}/evidence?decision_pack_id={pack['id']}", OWNER_HEADERS)["items"]
    reasons = get(f"{base}/reasons?decision_pack_id={pack['id']}", OWNER_HEADERS)["items"]
    acknowledgements = get(f"{base}/acknowledgements?decision_pack_id={pack['id']}", OWNER_HEADERS)["items"]
    snapshots = get(f"{base}/snapshots?decision_pack_id={pack['id']}", OWNER_HEADERS)["items"]
    if explanation["id"] not in list_ids(explanations) or reason["id"] not in list_ids(reasons):
        raise AssertionError("Agency explanation/reason lists missed created records.")
    if acknowledgement["id"] not in list_ids(acknowledgements) or snapshot["id"] not in list_ids(snapshots):
        raise AssertionError("Agency acknowledgement/snapshot lists missed created records.")
    if not timeline or not evidence:
        raise AssertionError("Agency timeline or evidence list missed created records.")

    platform_summary = get("/api/platform/offer-decision-explanations/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform explanation diagnostics changed execution boundary: {platform_summary}")
    platform_explanations = get("/api/platform/offer-decision-explanations/explanations", OWNER_HEADERS)["items"]
    platform_snapshots = get("/api/platform/offer-decision-explanations/snapshots", OWNER_HEADERS)["items"]
    if explanation["id"] not in list_ids(platform_explanations):
        raise AssertionError("Platform diagnostics did not list decision explanation.")
    if snapshot["id"] not in list_ids(platform_snapshots):
        raise AssertionError("Platform diagnostics did not list explanation audit snapshot.")

    blocked_status, _ = request(
        "POST",
        "/api/platform/offer-decision-explanations/explanations",
        {"decision_pack_id": pack["id"], "title": "blocked", "explanation_text": "blocked"},
        OWNER_HEADERS,
        expect=405,
    )
    if blocked_status != 405:
        raise AssertionError(f"Platform mutation route unexpectedly available: {blocked_status}")

    blocked_evidence_status, _ = request(
        "POST",
        f"{base}/evidence",
        {"decision_pack_id": pack["id"]},
        OWNER_HEADERS,
        expect=405,
    )
    if blocked_evidence_status != 405:
        raise AssertionError(f"Agency evidence mutation route unexpectedly available: {blocked_evidence_status}")

    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if before_signature != after_signature:
        raise AssertionError(f"Decision explanations mutated offer option pricing/status: before={before_signature} after={after_signature}")
    if any(item.get("status") == "recommended" for item in after_signature.values()):
        raise AssertionError(f"Decision explanations auto-selected an option: {after_signature}")

    final_section = get("/api/readiness").get("offer_decision_explanation_foundation") or {}
    for key in ["explanations", "timeline_events", "reasons", "evidence_references", "acknowledgements", "snapshots"]:
        if final_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created explanation records: {final_section}")

    decision_pack_smoke_main()
    offer_advisor_smoke_main()
    comparison_smoke_main()
    pricing_smoke_main()
    mechanics_smoke_main()
    taxonomy_smoke_main()
    policy_ingestion_smoke_main()

    print("Offer decision explanation foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
