#!/usr/bin/env python3
from pathlib import Path
import sys
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (  # noqa: E402
    AirlineIntelligenceAgencyConsumptionNote,
    AirlineIntelligenceAgencyConsumptionProfile,
    AirlineIntelligenceAgencyConsumptionSnapshot,
    AirlineIntelligenceAgencyKnowledgeAssignmentView,
    AirlineIntelligenceAgencyUsageReadiness,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


from phase_assertions import application_phase_is_at_least


MINIMUM_PHASE = "phase_39_3_airline_intelligence_agency_consumption_bridge"


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def has_key(data: object, key: str) -> bool:
    if isinstance(data, dict):
        return key in data or any(has_key(value, key) for value in data.values())
    if isinstance(data, list):
        return any(has_key(item, key) for item in data)
    return False


def has_value(data: object, text: str) -> bool:
    if isinstance(data, dict):
        return any(has_value(value, text) for value in data.values())
    if isinstance(data, list):
        return any(has_value(item, text) for item in data)
    return data == text


def verify_model_and_collection_registration() -> None:
    for model in [
        AirlineIntelligenceAgencyConsumptionProfile,
        AirlineIntelligenceAgencyKnowledgeAssignmentView,
        AirlineIntelligenceAgencyUsageReadiness,
        AirlineIntelligenceAgencyConsumptionNote,
        AirlineIntelligenceAgencyConsumptionSnapshot,
    ]:
        if not hasattr(model, "model_fields"):
            raise AssertionError(f"Model import failed for {model}")
    for collection in [
        "airline_intelligence_agency_consumption_profiles",
        "airline_intelligence_agency_knowledge_assignment_views",
        "airline_intelligence_agency_usage_readiness",
        "airline_intelligence_agency_consumption_notes",
        "airline_intelligence_agency_consumption_snapshots",
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Collection not registered for Mongo index setup: {collection}")


def main() -> int:
    verify_model_and_collection_registration()
    run_key = uuid4().hex[:10]
    health = get("/api/health")
    if not application_phase_is_at_least(health.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if ("airline-intelligence-consumption" in path or "airline-intelligence-agency-consumption" in path) and any(
            token in path
            for token in [
                "/publish",
                "/scrape",
                "/external",
                "/ai/",
                "/recommend",
                "/execute",
                "/book",
                "/pnr",
                "/ticket",
                "/emd",
                "/pay",
                "/invoice",
                "/settle",
                "/send",
                "public-link",
            ]
        ):
            raise AssertionError(f"Agency consumption execution route introduced: {path}")

    for path, method in [
        ("/api/platform/airline-intelligence-agency-consumption/summary", "get"),
        ("/api/platform/airline-intelligence-agency-consumption/profiles", "get"),
        ("/api/platform/airline-intelligence-agency-consumption/profiles", "post"),
        ("/api/platform/airline-intelligence-agency-consumption/profiles/{profile_id}", "get"),
        ("/api/platform/airline-intelligence-agency-consumption/profiles/{profile_id}", "patch"),
        ("/api/platform/airline-intelligence-agency-consumption/agencies/{agency_id}/assignments", "get"),
        ("/api/platform/airline-intelligence-agency-consumption/agencies/{agency_id}/usage-readiness", "get"),
        ("/api/platform/airline-intelligence-agency-consumption/agencies/{agency_id}/usage-readiness", "post"),
        ("/api/platform/airline-intelligence-agency-consumption/notes", "get"),
        ("/api/platform/airline-intelligence-agency-consumption/notes", "post"),
        ("/api/platform/airline-intelligence-agency-consumption/snapshots", "get"),
        ("/api/platform/airline-intelligence-agency-consumption/snapshots", "post"),
        ("/api/agencies/{agency_id}/airline-intelligence-consumption/summary", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-consumption/assigned-knowledge", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-consumption/usage-readiness", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-consumption/notes", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-consumption/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if not application_phase_is_at_least(readiness.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_intelligence_agency_consumption_bridge") or {}
    for key in [
        "consumption_profiles_enabled",
        "agency_assignment_visibility_enabled",
        "crm_readiness_metadata_enabled",
        "cms_readiness_metadata_enabled",
        "client_portal_readiness_metadata_enabled",
        "offer_builder_readiness_metadata_enabled",
        "agency_plain_language_ui_enabled",
        "platform_governance_ui_enabled",
        "metadata_only_consumption_enabled",
        "automatic_publishing_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
        "recommendations_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "external_ai_disabled",
        "external_api_calls_disabled",
        "scraping_disabled",
        "automatic_sending_disabled",
    ]:
        require_flag(section, key)
    for key in [
        "profile_count",
        "assignment_view_count",
        "usage_readiness_count",
        "note_count",
        "snapshot_count",
        "agency_visible_profile_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing agency consumption count {key}")

    version_base = "/api/platform/airline-intelligence-knowledge-versions"
    bridge_base = "/api/platform/airline-intelligence-agency-consumption"
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    version = post(
        f"{version_base}/versions",
        {
            "version_code": f"ACB-{run_key}",
            "title": "Smoke agency consumption knowledge version",
            "description": "Metadata-only knowledge version for agency consumption bridge smoke.",
            "coverage_summary": "Smoke airline intelligence coverage for agency consumption.",
            "agency_visibility_mode": "visible",
            "crm_safe": True,
            "cms_safe": True,
            "client_portal_safe": False,
            "offer_builder_safe": True,
        },
        OWNER_HEADERS,
        201,
    )["version"]
    channel = post(
        f"{version_base}/release-channels",
        {
            "channel_code": f"smoke-agency-consumption-{run_key}",
            "name": "Smoke agency consumption channel",
            "description": "Metadata-only agency consumption bridge channel.",
            "audience": "pilot_agencies",
            "is_active": True,
        },
        OWNER_HEADERS,
        201,
    )["release_channel"]
    profile = post(
        f"{bridge_base}/profiles",
        {
            "agency_id": agency_id,
            "knowledge_version_id": version["id"],
            "release_channel_id": channel["id"],
            "status": "review",
            "crm_safe": True,
            "cms_safe": True,
            "client_portal_safe": False,
            "offer_builder_safe": True,
            "plain_language_summary": "Smoke agency can use reviewed airline intelligence metadata in safe work areas.",
            "allowed_usage_notes": "CRM, agency website, and offer builder are safe for metadata consumption.",
            "blocked_usage_notes": "Client portal display remains blocked pending platform review.",
            "internal_owner_notes": f"Internal platform-only note {run_key}",
            "visible_to_agency": False,
        },
        OWNER_HEADERS,
        201,
    )["profile"]
    profile = patch(
        f"{bridge_base}/profiles/{profile['id']}",
        {"status": "visible", "visible_to_agency": True, "updated_by": "smoke"},
        OWNER_HEADERS,
    )["profile"]
    if profile.get("status") != "visible" or profile.get("visible_to_agency") is not True:
        raise AssertionError(f"Profile was not made visible: {profile}")

    readiness_result = post(
        f"{bridge_base}/agencies/{agency_id}/usage-readiness",
        {"profile_id": profile["id"], "knowledge_version_id": version["id"], "calculated_by": "smoke"},
        OWNER_HEADERS,
        201,
    )
    readiness_items = readiness_result["items"]
    by_area = {item["usage_area"]: item for item in readiness_items}
    for area in ["crm", "cms", "offer_builder"]:
        if by_area.get(area, {}).get("status") != "ready":
            raise AssertionError(f"{area} readiness was not ready: {readiness_items}")
    if by_area.get("client_portal", {}).get("status") != "not_available":
        raise AssertionError(f"Client portal readiness should remain not available: {readiness_items}")

    internal_note_text = f"Do not expose internal bridge note {run_key}"
    visible_note_text = f"Agency-visible consumption guidance {run_key}"
    post(
        f"{bridge_base}/notes",
        {
            "agency_id": agency_id,
            "knowledge_version_id": version["id"],
            "release_channel_id": channel["id"],
            "profile_id": profile["id"],
            "note_type": "platform_internal",
            "note": internal_note_text,
            "visible_to_agency": False,
        },
        OWNER_HEADERS,
        201,
    )
    visible_note = post(
        f"{bridge_base}/notes",
        {
            "agency_id": agency_id,
            "knowledge_version_id": version["id"],
            "release_channel_id": channel["id"],
            "profile_id": profile["id"],
            "note_type": "agency_guidance",
            "note": visible_note_text,
            "visible_to_agency": True,
        },
        OWNER_HEADERS,
        201,
    )["note"]
    snapshot = post(
        f"{bridge_base}/snapshots",
        {
            "agency_id": agency_id,
            "knowledge_version_id": version["id"],
            "profile_id": profile["id"],
            "snapshot_type": "manual",
            "snapshot_json": {"plain_language_summary": "Smoke immutable agency consumption snapshot."},
            "created_by": "smoke",
        },
        OWNER_HEADERS,
        201,
    )["snapshot"]

    summary = get(f"{bridge_base}/summary", OWNER_HEADERS)
    if summary.get("profile_count", 0) < 1 or summary.get("agency_visible_profile_count", 0) < 1:
        raise AssertionError(f"Platform summary did not include created profile: {summary}")
    if profile["id"] not in ids(get(f"{bridge_base}/profiles", OWNER_HEADERS)["items"]):
        raise AssertionError("Profile list did not include created profile.")
    if not get(f"{bridge_base}/profiles/{profile['id']}", OWNER_HEADERS).get("profile", {}).get("internal_owner_notes"):
        raise AssertionError("Platform profile detail did not include internal owner notes.")
    if visible_note["id"] not in ids(get(f"{bridge_base}/notes?agency_id={agency_id}", OWNER_HEADERS)["items"]):
        raise AssertionError("Platform notes list did not include visible note.")
    if snapshot["id"] not in ids(get(f"{bridge_base}/snapshots?agency_id={agency_id}", OWNER_HEADERS)["items"]):
        raise AssertionError("Platform snapshots list did not include manual snapshot.")

    agency_base = f"/api/agencies/{agency_id}/airline-intelligence-consumption"
    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or agency_summary.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency summary is not read-only: {agency_summary}")
    cards = {item["usage_area"]: item for item in agency_summary.get("usage_cards", [])}
    if cards.get("crm", {}).get("available") is not True or cards.get("offer_builder", {}).get("available") is not True:
        raise AssertionError(f"Agency safe-use cards did not show expected availability: {cards}")
    if cards.get("client_portal", {}).get("available") is True:
        raise AssertionError(f"Client portal card should not be available: {cards}")

    assigned = get(f"{agency_base}/assigned-knowledge", OWNER_HEADERS)
    if profile["id"] not in {item.get("profile_id") for item in assigned["items"]}:
        raise AssertionError(f"Agency assigned knowledge did not include profile view: {assigned}")
    agency_readiness = get(f"{agency_base}/usage-readiness", OWNER_HEADERS)
    if len(agency_readiness.get("items", [])) < 4:
        raise AssertionError(f"Agency readiness missing calculated records: {agency_readiness}")
    agency_notes = get(f"{agency_base}/notes", OWNER_HEADERS)
    if has_value(agency_notes, internal_note_text) or has_key(agency_notes, "internal_owner_notes"):
        raise AssertionError(f"Agency notes exposed internal platform-only metadata: {agency_notes}")
    if not has_value(agency_notes, visible_note_text):
        raise AssertionError(f"Agency notes did not include visible guidance: {agency_notes}")
    agency_snapshots = get(f"{agency_base}/snapshots", OWNER_HEADERS)
    if has_key(agency_snapshots, "snapshot_json"):
        raise AssertionError(f"Agency snapshots exposed raw snapshot payload: {agency_snapshots}")
    request("POST", f"{agency_base}/assigned-knowledge", {"blocked": True}, OWNER_HEADERS, 405)
    request("PATCH", f"{agency_base}/usage-readiness", {"blocked": True}, OWNER_HEADERS, 405)

    readiness_after = get("/api/readiness")
    section_after = readiness_after.get("airline_intelligence_agency_consumption_bridge") or {}
    for key in [
        "profile_count",
        "assignment_view_count",
        "usage_readiness_count",
        "note_count",
        "snapshot_count",
        "agency_visible_profile_count",
    ]:
        if section_after.get(key, 0) < 1:
            raise AssertionError(f"Readiness count did not increment for {key}: {section_after}")
    for key in [
        "automatic_publishing_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
        "recommendations_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "external_ai_disabled",
        "external_api_calls_disabled",
        "scraping_disabled",
        "automatic_sending_disabled",
    ]:
        require_flag(section_after, key)

    print("Airline intelligence agency consumption bridge smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
