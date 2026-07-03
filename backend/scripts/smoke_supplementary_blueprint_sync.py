#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import Database
from smoke_booking_pnr_foundation import OWNER_HEADERS, get
from services.special_services_unified_facade import SpecialServicesUnifiedFacade


EXPECTED_PHASE = "phase_39_2_airline_intelligence_knowledge_versioning_foundation"
REQUIRED_CATEGORIES = {
    "RBAC",
    "Airline Intelligence",
    "GDS/Supplier",
    "Requests/Trips/Offers/Bookings",
    "Tickets/EMDs",
    "Documents",
    "AI systems",
    "Audit/Telemetry",
    "Special Services",
    "Service Taxonomy",
    "Service Mechanics",
}


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


async def assert_facade_safe() -> None:
    db = Database()
    db.mode = "memory"
    facade = SpecialServicesUnifiedFacade(db)
    trip_result = await facade.list_services_for_trip("agency-smoke", "trip-smoke")
    booking_result = await facade.list_services_for_booking("agency-smoke", "booking-record-smoke")
    normalized = facade.normalize_service_context({"service_type": "WCHR", "notes": "Wheelchair assistance"})
    preview = await facade.generate_ssr_osi_preview(normalized)
    evaluation = await facade.evaluate_service_context(normalized)
    if trip_result.get("items") != [] or booking_result.get("items") != []:
        raise AssertionError("Special services facade should return safe empty lists for empty data.")
    if normalized.get("service_type") != "WCHR":
        raise AssertionError("Special services facade did not normalize service context.")
    if "ssr" not in preview or "allowed" not in evaluation:
        raise AssertionError("Special services facade preview/evaluation did not return safe structures.")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/blueprint/adoption-map", "get"),
        ("/api/platform/blueprint/route-policy", "get"),
        ("/api/platform/blueprint/gaps", "get"),
        ("/api/platform/blueprint/next-phases", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    blueprint_sync = readiness.get("blueprint_sync") or {}
    for flag in [
        "supplementary_blueprint_adoption_map_enabled",
        "canonical_route_policy_enabled",
        "ai_trace_foundation_enabled",
        "adm_risk_event_foundation_enabled",
        "gds_parse_sample_foundation_enabled",
        "airline_brand_asset_foundation_enabled",
        "special_services_unified_facade_enabled",
        "platform_blueprint_ui_enabled",
        "supplementary_agent_admin_routes_rejected",
        "tickets_emd_phase_36_4_recognized",
        "booking_workspace_creation_entrypoint_recognized",
        "phase_36_5_documents_ready",
        "phase_36_6_gds_parser_ready",
    ]:
        if blueprint_sync.get(flag) is not True:
            raise AssertionError(f"Blueprint sync readiness missing flag: {flag}")
    for count_key in [
        "ai_trace_event_count",
        "adm_risk_event_count",
        "gds_parse_sample_count",
        "airline_brand_asset_count",
        "blueprint_adoption_item_count",
        "blueprint_gap_count",
        "blueprint_rejected_route_count",
    ]:
        if count_key not in blueprint_sync:
            raise AssertionError(f"Blueprint sync readiness missing count: {count_key}")
    if blueprint_sync.get("readiness_required") is not False:
        raise AssertionError("Blueprint sync should not be deployment-readiness required.")

    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    missing = REQUIRED_CATEGORIES - categories
    if missing:
        raise AssertionError(f"Blueprint adoption map missing categories: {sorted(missing)}")
    ticket_item = next((item for item in adoption.get("items", []) if item.get("category") == "Tickets/EMDs"), {})
    if ticket_item.get("status") != "built" or "Phase 36.4" not in ticket_item.get("action", ""):
        raise AssertionError("Blueprint adoption map did not recognize Phase 36.4 Tickets + EMD Foundation.")
    document_item = next((item for item in adoption.get("items", []) if item.get("category") == "Documents"), {})
    if document_item.get("status") != "built" or "Phase 36.5" not in document_item.get("action", ""):
        raise AssertionError("Blueprint adoption map did not recognize Phase 36.5 Document Foundation.")
    parser_item = next((item for item in adoption.get("items", []) if item.get("category") == "GDS/Supplier"), {})
    if parser_item.get("status") != "built" or "Phase 36.6" not in parser_item.get("action", ""):
        raise AssertionError("Blueprint adoption map did not recognize Phase 36.6 GDS Parser Foundation.")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    canonical_roots = {item.get("root") for item in route_policy.get("canonical_routes") or []}
    rejected_roots = {item.get("root") for item in route_policy.get("rejected_routes") or []}
    if "/platform/*" not in canonical_roots or "/agency/*" not in canonical_roots:
        raise AssertionError("Route policy did not keep /platform and /agency canonical.")
    if "/agent/*" not in rejected_roots or "/admin/*" not in rejected_roots:
        raise AssertionError("Route policy did not reject /agent and /admin roots.")
    if route_policy.get("aliases_added") is not False:
        raise AssertionError("Route policy should not add /agent or /admin aliases in this phase.")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Phase 37" not in gaps.get("next_immediate_phase", ""):
        raise AssertionError("Gap summary did not identify Phase 37 provider provenance as next.")
    if not any("Tickets + EMD Foundation" in item for item in gaps.get("already_built", [])):
        raise AssertionError("Gap summary did not recognize Tickets + EMD Foundation as already built.")
    if not any("Document foundation" in item for item in gaps.get("already_built", [])):
        raise AssertionError("Gap summary did not recognize Document Foundation as already built.")
    if not any("GDS parser foundation" in item for item in gaps.get("already_built", [])):
        raise AssertionError("Gap summary did not recognize GDS Parser Foundation as already built.")

    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not next_phases.get("items") or next_phases["items"][0].get("phase") != "Phase 37":
        raise AssertionError("Next phase recommendations did not start with Phase 37.")

    summary = get("/api/platform/summary", OWNER_HEADERS)
    for collection_name in ["ai_trace_events", "adm_risk_events", "gds_parse_samples", "gds_parser_runs", "gds_parse_training_samples", "airline_brand_assets"]:
        if collection_name not in (summary.get("counts") or {}):
            raise AssertionError(f"Platform summary missing collection count: {collection_name}")

    asyncio.run(assert_facade_safe())
    print("Supplementary blueprint sync smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Supplementary blueprint sync smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
