#!/usr/bin/env python3
from uuid import uuid4

from smoke_airline_policy_ingestion_foundation import main as policy_ingestion_smoke_main
from smoke_ancillary_pricing_exception_foundation import main as pricing_smoke_main
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_policy_advisor_integration_foundation import create_offer_workspace
from smoke_policy_comparison_service_advisor_foundation import main as comparison_smoke_main, seed_airline_facts
from smoke_service_mechanics_mapping_foundation import main as mechanics_smoke_main
from smoke_service_taxonomy_foundation import main as taxonomy_smoke_main


EXPECTED_PHASE = "phase_37_9_offer_decision_export_manual_delivery_outcome_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision pack count {key}")


def create_advisor_snapshot(agency_id: str, workspace: dict, run_key: str, domain_code: str, family_code: str, variant_code: str) -> tuple[dict, dict, dict]:
    context_response = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/build",
        {
            "offer_workspace_id": workspace["id"],
            "context_name": f"Smoke decision pack advisor context {run_key}",
            "airline_codes": ["ZX", "QY"],
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "route_context_json": {"direct_vs_connecting": "direct", "origin_airport": "SOF", "destination_airport": "FRA"},
            "passenger_context_json": {"passenger_type": "adult", "passenger_age": 34},
            "service_context_json": {"service_code": "WCHR"},
        },
        OWNER_HEADERS,
        201,
    )
    context = context_response["context"]
    evaluation = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}/evaluate",
        {},
        OWNER_HEADERS,
        201,
    )
    attached = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}/attach",
        {
            "policy_comparison_snapshot_id": evaluation["advisor"]["comparison_snapshot"]["id"],
            "advisor_scenario_id": evaluation["advisor"]["scenario"]["id"],
            "advisor_result_id": evaluation["advisor"]["result"]["id"],
            "quote_result_ids": [item["result"]["id"] for item in evaluation.get("quote_results") or []],
        },
        OWNER_HEADERS,
    )["context"]
    snapshot = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}/saved-snapshots",
        {"snapshot_name": f"Smoke decision pack advisor snapshot {run_key}"},
        OWNER_HEADERS,
        201,
    )["saved_snapshot"]
    return attached, snapshot, evaluation


def option_signature(workspace_detail: dict, option_ids: set[str]) -> dict:
    return {
        option["id"]: {
            "status": option.get("status"),
            "pricing_summary_json": option.get("pricing_summary_json") or {},
            "main_airline_code": option.get("main_airline_code"),
        }
        for option in workspace_detail.get("options") or []
        if option.get("id") in option_ids
    }


def main() -> int:
    run_key = uuid4().hex[:10]
    domain_code = f"smoke_decision_pack_{run_key}"
    family_code = f"wheelchair_pack_{run_key}"
    variant_code = f"wchr_pack_{run_key}"

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "offer-decision-packs" in path and any(token in path for token in ["/execute", "/issue", "/pay", "/invoice", "/settle", "/book"]):
            raise AssertionError(f"Decision pack execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-packs/summary", "get"),
        ("/api/platform/offer-decision-packs/packs", "get"),
        ("/api/platform/offer-decision-packs/packs/{pack_id}", "get"),
        ("/api/platform/offer-decision-packs/evidence", "get"),
        ("/api/platform/offer-decision-packs/warnings", "get"),
        ("/api/platform/offer-decision-packs/review-notes", "get"),
        ("/api/platform/offer-decision-packs/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/packs", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/packs/build", "post"),
        ("/api/agencies/{agency_id}/offer-decision-packs/packs/{pack_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/packs/{pack_id}/attach-advisor-evidence", "post"),
        ("/api/agencies/{agency_id}/offer-decision-packs/packs/{pack_id}/review-notes", "post"),
        ("/api/agencies/{agency_id}/offer-decision-packs/packs/{pack_id}/review-notes/{note_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-packs/packs/{pack_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/offer-decision-packs/options", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/evidence", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/warnings", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/review-notes", "get"),
        ("/api/agencies/{agency_id}/offer-decision-packs/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_builder_advisor_consumption_decision_pack_foundation") or {}
    for key in [
        "decision_packs_enabled",
        "option_evidence_enabled",
        "decision_pack_warnings_enabled",
        "review_notes_enabled",
        "immutable_snapshots_enabled",
        "advisor_snapshot_consumption_enabled",
        "offer_builder_consumption_enabled",
        "agency_decision_pack_ui_enabled",
        "platform_decision_pack_ui_enabled",
        "human_review_required_enabled",
        "auto_recommendation_disabled",
        "offer_price_mutation_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "ticket_emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["decision_pack_count", "option_evidence_count", "warning_count", "review_note_count", "saved_snapshot_count"]:
        require_count(section, key)

    for airline_code, amount in [("ZX", 35.0), ("QY", 55.0)]:
        seed_airline_facts(airline_code, domain_code, family_code, variant_code, amount, run_key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, options = create_offer_workspace(agency_id, run_key)
    option_ids = {option["id"] for option in options}
    before_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    advisor_context, advisor_snapshot, evaluation = create_advisor_snapshot(agency_id, workspace, run_key, domain_code, family_code, variant_code)

    decision_pack_response = post(
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/build",
        {
            "offer_workspace_id": workspace["id"],
            "pack_name": f"Smoke decision pack {run_key}",
            "advisor_context_ids": [advisor_context["id"]],
            "advisor_saved_snapshot_ids": [advisor_snapshot["id"]],
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    pack = decision_pack_response["pack"]
    if pack.get("metadata_only") is not True or pack.get("auto_recommendation_disabled") is not True:
        raise AssertionError(f"Decision pack safety flags missing: {pack}")
    if pack.get("offer_workspace_id") != workspace["id"] or pack.get("evidence_count", 0) < 2:
        raise AssertionError(f"Decision pack did not consume offer advisor evidence: {decision_pack_response}")
    if decision_pack_response.get("offer_price_mutation_disabled") is not True or decision_pack_response.get("provider_execution_disabled") is not True:
        raise AssertionError(f"Decision pack response changed execution boundary: {decision_pack_response}")

    options_created = decision_pack_response.get("options") or []
    if len(options_created) != 2 or any(option.get("manual_review_required") is not True for option in options_created):
        raise AssertionError(f"Decision pack option rows were not created for human review: {options_created}")
    if not any(item.get("evidence_type") == "advisor_snapshot" for item in decision_pack_response.get("evidence") or []):
        raise AssertionError(f"Decision pack did not include saved advisor snapshot evidence: {decision_pack_response.get('evidence')}")

    attached = post(
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/{pack['id']}/attach-advisor-evidence",
        {
            "advisor_context_id": advisor_context["id"],
            "advisor_saved_snapshot_id": advisor_snapshot["id"],
            "offer_option_id": options[0]["id"],
            "airline_code": options[0]["main_airline_code"],
            "metadata_json": {"run_key": run_key, "attachment": "smoke"},
        },
        OWNER_HEADERS,
    )
    if len(attached.get("evidence") or []) < 2:
        raise AssertionError(f"Decision pack advisor attach did not create evidence: {attached}")

    note = post(
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/{pack['id']}/review-notes",
        {
            "offer_option_id": options[1]["id"],
            "airline_code": options[1]["main_airline_code"],
            "note_title": f"Smoke decision pack review {run_key}",
            "note_body": "Human review recorded. No airline was auto-ranked or auto-selected.",
            "note_status": "recorded",
        },
        OWNER_HEADERS,
        201,
    )["review_note"]
    if note.get("auto_recommendation_disabled") is not True or note.get("human_reviewed") is not True:
        raise AssertionError(f"Decision pack review note safety flags missing: {note}")
    updated_note = request(
        "PATCH",
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/{pack['id']}/review-notes/{note['id']}",
        {"note_status": "reviewed"},
        OWNER_HEADERS,
        expect=200,
    )[1]["review_note"]
    if updated_note.get("note_status") != "reviewed":
        raise AssertionError(f"Decision pack review note did not update: {updated_note}")

    snapshot = post(
        f"/api/agencies/{agency_id}/offer-decision-packs/packs/{pack['id']}/snapshots",
        {"snapshot_name": f"Smoke decision pack snapshot {run_key}"},
        OWNER_HEADERS,
        201,
    )["snapshot"]
    if snapshot.get("decision_pack_id") != pack["id"] or snapshot.get("immutable") is not True or not snapshot.get("evidence_ids"):
        raise AssertionError(f"Decision pack snapshot was not immutable or complete: {snapshot}")

    detail = get(f"/api/agencies/{agency_id}/offer-decision-packs/packs/{pack['id']}", OWNER_HEADERS)
    if len(detail.get("review_notes") or []) < 1 or len(detail.get("snapshots") or []) < 1:
        raise AssertionError(f"Decision pack detail missed notes or snapshots: {detail}")
    if detail.get("auto_recommendation_disabled") is not True or detail.get("booking_execution_disabled") is not True:
        raise AssertionError(f"Decision pack detail safety flags changed: {detail}")

    platform_summary = get("/api/platform/offer-decision-packs/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform decision pack diagnostics changed execution boundary: {platform_summary}")
    platform_packs = get("/api/platform/offer-decision-packs/packs", OWNER_HEADERS)["items"]
    if pack["id"] not in {item["id"] for item in platform_packs}:
        raise AssertionError("Platform diagnostics did not list decision pack.")
    platform_snapshots = get("/api/platform/offer-decision-packs/snapshots", OWNER_HEADERS)["items"]
    if snapshot["id"] not in {item["id"] for item in platform_snapshots}:
        raise AssertionError("Platform diagnostics did not list decision pack snapshot.")

    blocked_status, _ = request(
        "POST",
        f"/api/platform/offer-decision-packs/packs/{pack['id']}",
        {"snapshot_name": "blocked"},
        OWNER_HEADERS,
        expect=405,
    )
    if blocked_status != 405:
        raise AssertionError(f"Platform mutation route unexpectedly available: {blocked_status}")

    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if before_signature != after_signature:
        raise AssertionError(f"Decision pack mutated offer option pricing/status: before={before_signature} after={after_signature}")
    if any(item.get("status") == "recommended" for item in after_signature.values()):
        raise AssertionError(f"Decision pack auto-selected an option: {after_signature}")
    if not any((row.get("quote_result_id") for row in evaluation.get("airline_rows") or [])):
        raise AssertionError("Advisor quote evidence was not created before decision pack consumption.")

    final_section = get("/api/readiness").get("offer_builder_advisor_consumption_decision_pack_foundation") or {}
    for key in ["decision_pack_count", "option_evidence_count", "warning_count", "review_note_count", "saved_snapshot_count"]:
        if final_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created decision pack records: {final_section}")

    comparison_smoke_main()
    pricing_smoke_main()
    mechanics_smoke_main()
    taxonomy_smoke_main()
    policy_ingestion_smoke_main()

    print("Offer decision pack foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
