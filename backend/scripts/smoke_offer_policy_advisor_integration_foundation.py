#!/usr/bin/env python3
from uuid import uuid4

from smoke_airline_policy_ingestion_foundation import main as policy_ingestion_smoke_main
from smoke_ancillary_pricing_exception_foundation import main as pricing_smoke_main
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_builder_foundation import builder_payload
from smoke_policy_comparison_service_advisor_foundation import main as comparison_smoke_main, seed_airline_facts
from smoke_service_mechanics_mapping_foundation import main as mechanics_smoke_main
from smoke_service_taxonomy_foundation import main as taxonomy_smoke_main


EXPECTED_PHASE = "phase_37_8_offer_decision_export_manual_delivery_handoff_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer policy advisor count {key}")


def create_offer_workspace(agency_id: str, run_key: str) -> tuple[dict, list[dict]]:
    created_request = post(
        f"/api/agencies/{agency_id}/requests/builder",
        builder_payload(f"phase372.{run_key}@example.com"),
        OWNER_HEADERS,
        201,
    )
    request_id = created_request["request"]["id"]
    trip = post(f"/api/agencies/{agency_id}/trips/from-request/{request_id}", {}, OWNER_HEADERS, 201)["trip"]
    workspace = post(f"/api/agencies/{agency_id}/requests/{request_id}/offer-workspace", {}, OWNER_HEADERS, 201)["workspace"]
    if workspace.get("trip_id") not in {None, trip["id"]}:
        raise AssertionError(f"Workspace trip link drifted: {workspace}")

    options = []
    for airline_code, label in [("ZX", "ZX advisory economy"), ("QY", "QY advisory economy")]:
        option = post(
            f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}/options",
            {
                "label": f"{label} {run_key}",
                "option_type": "flight",
                "main_airline_code": airline_code,
                "provider_name": "manual",
            },
            OWNER_HEADERS,
            201,
        )["option"]
        post(
            f"/api/agencies/{agency_id}/offer-options/{option['id']}/segments",
            {
                "sequence": 1,
                "marketing_airline_code": airline_code,
                "operating_airline_code": airline_code,
                "flight_number": f"{airline_code}372",
                "origin_airport": "SOF",
                "destination_airport": "FRA",
                "departure_at": "2027-03-21T06:00:00Z",
                "arrival_at": "2027-03-21T07:25:00Z",
                "aircraft_type": "A320",
                "cabin_class": "economy",
                "booking_class": "Y",
                "fare_basis": f"{airline_code}SMOKE",
            },
            OWNER_HEADERS,
            201,
        )
        post(
            f"/api/agencies/{agency_id}/offer-options/{option['id']}/pricing-lines",
            {"line_type": "base_fare", "label": f"{airline_code} base fare", "amount": 120.0, "currency": "EUR"},
            OWNER_HEADERS,
            201,
        )
        options.append(option)
    return workspace, options


def main() -> int:
    run_key = uuid4().hex[:10]
    domain_code = f"smoke_offer_advisor_{run_key}"
    family_code = f"wheelchair_offer_{run_key}"
    variant_code = f"wchr_{run_key}"
    airline_codes = ["ZX", "QY"]

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-policy-advisor/summary", "get"),
        ("/api/platform/offer-policy-advisor/contexts", "get"),
        ("/api/platform/offer-policy-advisor/contexts/{context_id}", "get"),
        ("/api/platform/offer-policy-advisor/airline-rows", "get"),
        ("/api/platform/offer-policy-advisor/warnings", "get"),
        ("/api/platform/offer-policy-advisor/decision-notes", "get"),
        ("/api/platform/offer-policy-advisor/saved-snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/summary", "get"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/contexts", "get"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/contexts/build", "post"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context_id}", "get"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context_id}/evaluate", "post"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context_id}/attach", "post"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context_id}/decision-notes", "post"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context_id}/saved-snapshots", "post"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/airline-rows", "get"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/warnings", "get"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/decision-notes", "get"),
        ("/api/agencies/{agency_id}/offer-policy-advisor/saved-snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_policy_advisor_integration_foundation") or {}
    for key in [
        "offer_advisor_contexts_enabled",
        "offer_advisor_airline_rows_enabled",
        "offer_advisor_warnings_enabled",
        "offer_advisor_decision_notes_enabled",
        "offer_advisor_saved_snapshots_enabled",
        "platform_offer_policy_advisor_ui_enabled",
        "agency_offer_policy_advisor_ui_enabled",
        "deterministic_offer_advisor_integration_enabled",
        "auto_recommendation_disabled",
        "provider_execution_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "agency_global_mutation_blocked",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in ["context_count", "airline_row_count", "warning_count", "decision_note_count", "saved_snapshot_count"]:
        require_count(section, key)

    for airline_code, amount in [("ZX", 35.0), ("QY", 55.0)]:
        seed_airline_facts(airline_code, domain_code, family_code, variant_code, amount, run_key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, options = create_offer_workspace(agency_id, run_key)
    context_response = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/build",
        {
            "offer_workspace_id": workspace["id"],
            "context_name": f"Smoke offer advisor context {run_key}",
            "airline_codes": airline_codes,
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
    if context.get("offer_workspace_id") != workspace["id"] or context.get("auto_recommendation_disabled") is not True:
        raise AssertionError(f"Advisor context was not safely linked: {context}")

    evaluation = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}/evaluate",
        {},
        OWNER_HEADERS,
        201,
    )
    rows = evaluation.get("airline_rows") or []
    if len(rows) != 2 or {row.get("airline_code") for row in rows} != set(airline_codes):
        raise AssertionError(f"Offer advisor evaluation did not create two airline rows: {evaluation}")
    if evaluation.get("offer_pricing_unchanged") is not True or evaluation.get("provider_execution_disabled") is not True:
        raise AssertionError(f"Offer advisor changed safety boundaries: {evaluation}")
    if not any((row.get("quote_result_id") for row in rows)):
        raise AssertionError(f"Offer advisor rows did not link quote results: {rows}")

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
    if attached.get("context_status") != "attached":
        raise AssertionError(f"Attach did not mark context attached: {attached}")

    note = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}/decision-notes",
        {
            "airline_code": "QY",
            "note_title": f"Smoke manual decision note {run_key}",
            "note_body": "Human reviewed QY warning metadata; no airline was auto-selected.",
            "note_status": "recorded",
        },
        OWNER_HEADERS,
        201,
    )["decision_note"]
    if note.get("auto_recommendation_disabled") is not True or note.get("human_reviewed") is not True:
        raise AssertionError(f"Decision note did not preserve human review boundary: {note}")

    snapshot = post(
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}/saved-snapshots",
        {"snapshot_name": f"Smoke offer advisor snapshot {run_key}"},
        OWNER_HEADERS,
        201,
    )["saved_snapshot"]
    if snapshot.get("context_id") != context["id"] or not snapshot.get("airline_row_ids"):
        raise AssertionError(f"Saved snapshot did not preserve advisor rows: {snapshot}")

    warnings = get(f"/api/agencies/{agency_id}/offer-policy-advisor/warnings?context_id={context['id']}", OWNER_HEADERS)["items"]
    if not warnings:
        raise AssertionError("Offer advisor warning creation was not observed.")
    listed_rows = get(f"/api/agencies/{agency_id}/offer-policy-advisor/airline-rows?context_id={context['id']}", OWNER_HEADERS)["items"]
    if len(listed_rows) < 2:
        raise AssertionError(f"Offer advisor airline rows were not listed: {listed_rows}")
    detail = get(f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}", OWNER_HEADERS)
    if len(detail.get("decision_notes") or []) < 1 or len(detail.get("saved_snapshots") or []) < 1:
        raise AssertionError(f"Offer advisor detail missed notes or snapshots: {detail}")

    platform_summary = get("/api/platform/offer-policy-advisor/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform diagnostics changed execution boundary: {platform_summary}")
    platform_contexts = get("/api/platform/offer-policy-advisor/contexts", OWNER_HEADERS)["items"]
    if context["id"] not in {item["id"] for item in platform_contexts}:
        raise AssertionError("Platform diagnostics did not list offer advisor context.")
    platform_snapshots = get("/api/platform/offer-policy-advisor/saved-snapshots", OWNER_HEADERS)["items"]
    if snapshot["id"] not in {item["id"] for item in platform_snapshots}:
        raise AssertionError("Platform diagnostics did not list saved offer advisor snapshot.")

    blocked_status, _ = request(
        "PATCH",
        f"/api/agencies/{agency_id}/offer-policy-advisor/contexts/{context['id']}",
        {"context_status": "archived"},
        OWNER_HEADERS,
        expect=405,
    )
    if blocked_status != 405:
        raise AssertionError(f"Agency mutation route unexpectedly available: {blocked_status}")

    final_section = get("/api/readiness").get("offer_policy_advisor_integration_foundation") or {}
    for key in ["context_count", "airline_row_count", "warning_count", "decision_note_count", "saved_snapshot_count"]:
        if final_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created records: {final_section}")

    option_after = get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS)["options"]
    statuses = {item["id"]: item.get("status") for item in option_after if item["id"] in {option["id"] for option in options}}
    if any(status == "recommended" for status in statuses.values()):
        raise AssertionError(f"Offer advisor auto-selected an option: {statuses}")

    comparison_smoke_main()
    pricing_smoke_main()
    mechanics_smoke_main()
    taxonomy_smoke_main()
    policy_ingestion_smoke_main()

    print("Offer policy advisor integration foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
