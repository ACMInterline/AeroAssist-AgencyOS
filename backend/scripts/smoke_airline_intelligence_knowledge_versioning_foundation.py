#!/usr/bin/env python3
from pathlib import Path
import sys
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (  # noqa: E402
    AirlineIntelligenceKnowledgeReleaseAssignment,
    AirlineIntelligenceKnowledgeReleaseChannel,
    AirlineIntelligenceKnowledgeRollbackPlan,
    AirlineIntelligenceKnowledgeVersion,
    AirlineIntelligenceKnowledgeVersionComparison,
    AirlineIntelligenceKnowledgeVersionItem,
    AirlineIntelligenceKnowledgeVersionSnapshot,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_39_4_platform_agency_ux_consolidation"


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


def verify_model_and_collection_registration() -> None:
    for model in [
        AirlineIntelligenceKnowledgeVersion,
        AirlineIntelligenceKnowledgeVersionItem,
        AirlineIntelligenceKnowledgeReleaseChannel,
        AirlineIntelligenceKnowledgeReleaseAssignment,
        AirlineIntelligenceKnowledgeVersionComparison,
        AirlineIntelligenceKnowledgeRollbackPlan,
        AirlineIntelligenceKnowledgeVersionSnapshot,
    ]:
        if not hasattr(model, "model_fields"):
            raise AssertionError(f"Model import failed for {model}")
    for collection in [
        "airline_intelligence_knowledge_versions",
        "airline_intelligence_knowledge_version_items",
        "airline_intelligence_knowledge_release_channels",
        "airline_intelligence_knowledge_release_assignments",
        "airline_intelligence_knowledge_version_comparisons",
        "airline_intelligence_knowledge_rollback_plans",
        "airline_intelligence_knowledge_version_snapshots",
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Collection not registered for Mongo index setup: {collection}")


def main() -> int:
    verify_model_and_collection_registration()
    run_key = uuid4().hex[:10]
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "airline-intelligence-knowledge-versions" in path and any(
            token in path
            for token in [
                "/scrape",
                "/external",
                "/ai/",
                "/promote",
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
            raise AssertionError(f"Airline knowledge version execution route introduced: {path}")

    for path, method in [
        ("/api/platform/airline-intelligence-knowledge-versions/summary", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}", "patch"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}/items", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}/items", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/version-items/{version_item_id}", "patch"),
        ("/api/platform/airline-intelligence-knowledge-versions/version-items/{version_item_id}", "delete"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}/freeze", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}/approve", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}/mark-published-metadata", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/release-channels", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/release-channels", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/release-assignments", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/release-assignments", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/comparisons", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/comparisons", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/rollback-plans", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/rollback-plans", "post"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}/snapshots", "get"),
        ("/api/platform/airline-intelligence-knowledge-versions/versions/{version_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/airline-intelligence-knowledge-versions/summary", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-knowledge-versions/current", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-knowledge-versions/preview", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-knowledge-versions/versions", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-knowledge-versions/versions/{version_id}", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_intelligence_knowledge_versioning_foundation") or {}
    for key in [
        "metadata_only_versioning_enabled",
        "operational_promotion_disabled",
        "automatic_promotion_disabled",
        "scraping_disabled",
        "external_ai_disabled",
        "external_api_calls_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "automatic_sending_disabled",
    ]:
        require_flag(section, key)
    for key in [
        "knowledge_version_count",
        "version_item_count",
        "release_channel_count",
        "release_assignment_count",
        "comparison_count",
        "rollback_plan_count",
        "snapshot_count",
        "frozen_version_count",
        "approved_version_count",
        "published_metadata_version_count",
        "agency_visible_version_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing knowledge version count {key}")

    pack_base = "/api/platform/airline-intelligence-data-packs"
    review_base = "/api/platform/airline-intelligence-data-pack-reviews"
    version_base = "/api/platform/airline-intelligence-knowledge-versions"

    pack = post(
        f"{pack_base}/packs",
        {
            "name": f"Smoke knowledge data pack {run_key}",
            "slug": f"smoke-knowledge-data-pack-{run_key}",
            "description": "Reviewed staged data for knowledge version smoke.",
            "pack_type": "airline_profile_pack",
            "airline_codes": ["KV"],
            "target_domains": ["airline_profile"],
            "source_type": "curated",
            "source_reference": f"Smoke version source {run_key}",
            "version_label": "knowledge-v1",
            "is_demo_data": False,
            "is_operationally_verified": True,
            "safe_for_agency_internal_crm": True,
            "safe_for_agency_display": True,
            "safe_for_cms_display": True,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": True,
            "verification_status": "reviewed",
            "confidence_score": 0.94,
            "human_summary": "Reviewed airline profile coverage for versioning smoke.",
            "operator_guidance": "Safe for metadata-only versioning smoke.",
        },
        OWNER_HEADERS,
        201,
    )["pack"]
    item = post(
        f"{pack_base}/packs/{pack['id']}/items",
        {
            "airline_iata_code": "KV",
            "target_domain": "airline_profile",
            "display_name": "Smoke knowledge airline profile",
            "plain_language_summary": "Knowledge version airline profile metadata for agency visibility.",
            "proposed_action": "review_only",
            "payload": {"airline_name": "Smoke Knowledge Air", "country": "Test"},
            "normalized_payload": {"airline_name": "Smoke Knowledge Air"},
            "source_reference": f"Smoke knowledge item {run_key}",
            "is_demo_data": False,
            "is_operationally_verified": True,
            "safe_for_agency_internal_crm": True,
            "safe_for_agency_display": True,
            "safe_for_cms_display": True,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": True,
            "validation_status": "valid",
            "verification_status": "reviewed",
        },
        OWNER_HEADERS,
        201,
    )["item"]
    review = post(
        f"{review_base}/packs/{pack['id']}/reviews",
        {
            "review_title": f"Smoke knowledge review {run_key}",
            "plain_language_coverage_summary": "Reviewed airline profile coverage for versioning.",
            "safe_for_agency_internal_crm": True,
            "safe_for_agency_display": True,
            "safe_for_cms_display": True,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": True,
        },
        OWNER_HEADERS,
        201,
    )["review"]
    detail = get(f"{review_base}/reviews/{review['id']}", OWNER_HEADERS)
    mapping = post(
        f"{review_base}/packs/{pack['id']}/field-mappings",
        {
            "item_id": item["id"],
            "source_payload_path": "payload.airline_name",
            "target_collection": "airline_intelligence_profiles",
            "target_field_path": "name",
            "target_record_key": "KV",
            "mapping_status": "approved",
            "mapping_confidence": 0.98,
            "would_update_record": True,
            "safe_for_agency_internal_crm": True,
            "safe_for_agency_display": True,
            "safe_for_cms_display": True,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": True,
        },
        OWNER_HEADERS,
        201,
    )["field_mapping"]
    for checklist_item in detail.get("checklist_items", []):
        patch(f"{review_base}/checklist-items/{checklist_item['id']}", {"status": "passed"}, OWNER_HEADERS)
    conflicts = post(f"{review_base}/packs/{pack['id']}/detect-conflicts", {}, OWNER_HEADERS)
    if conflicts.get("conflicts"):
        raise AssertionError(f"Expected no conflicts for versioning smoke pack: {conflicts}")
    review = patch(f"{review_base}/reviews/{review['id']}", {"status": "approved"}, OWNER_HEADERS)["review"]
    readiness = post(
        f"{review_base}/packs/{pack['id']}/promotion-readiness",
        {
            "review_id": review["id"],
            "safe_for_agency_internal_crm": True,
            "safe_for_agency_display": True,
            "safe_for_cms_display": True,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": True,
        },
        OWNER_HEADERS,
        201,
    )["promotion_readiness"]
    if readiness.get("ready_for_promotion") is not True:
        raise AssertionError(f"Promotion readiness was not ready: {readiness}")

    base_version = post(
        f"{version_base}/versions",
        {
            "version_code": f"KV-{run_key}-base",
            "title": "Smoke baseline knowledge version",
            "source_pack_ids": [pack["id"]],
            "source_review_ids": [review["id"]],
            "source_promotion_readiness_ids": [readiness["id"]],
            "coverage_summary": "Baseline preview knowledge version for smoke comparison.",
            "agency_visibility_mode": "preview",
            "crm_safe": True,
            "cms_safe": True,
            "client_portal_safe": False,
            "offer_builder_safe": True,
        },
        OWNER_HEADERS,
        201,
    )["version"]
    version = post(
        f"{version_base}/versions",
        {
            "version_code": f"KV-{run_key}-release",
            "title": "Smoke release knowledge version",
            "source_pack_ids": [pack["id"]],
            "source_review_ids": [review["id"]],
            "source_promotion_readiness_ids": [readiness["id"]],
            "coverage_summary": "Release knowledge version for smoke validation.",
            "agency_visibility_mode": "hidden",
            "crm_safe": True,
            "cms_safe": True,
            "client_portal_safe": False,
            "offer_builder_safe": True,
        },
        OWNER_HEADERS,
        201,
    )["version"]
    version_item = post(
        f"{version_base}/versions/{version['id']}/items",
        {
            "source_pack_item_id": item["id"],
            "target_domain": "airline_profile",
            "target_record_key": "KV",
            "target_airline_code": "KV",
            "field_mapping_id": mapping["id"],
            "conflict_ids": [],
            "readiness_id": readiness["id"],
            "inclusion_status": "included",
            "inclusion_reason": "Included for versioning smoke.",
            "normalized_payload_preview": {"airline_name": "Smoke Knowledge Air"},
            "agency_plain_language_summary": "Smoke Knowledge Air profile is visible in this knowledge version.",
        },
        OWNER_HEADERS,
        201,
    )["version_item"]
    if version_item.get("source_pack_item_id") != item["id"]:
        raise AssertionError(f"Version item was not linked to staged item: {version_item}")

    frozen = post(f"{version_base}/versions/{version['id']}/freeze", {}, OWNER_HEADERS)["version"]
    if frozen.get("status") != "frozen" or not frozen.get("frozen_at"):
        raise AssertionError(f"Version was not frozen: {frozen}")
    approved = post(f"{version_base}/versions/{version['id']}/approve", {"approved_by": "smoke"}, OWNER_HEADERS)["version"]
    if approved.get("status") != "approved" or approved.get("approved_by") != "smoke":
        raise AssertionError(f"Version was not approved: {approved}")
    published = post(
        f"{version_base}/versions/{version['id']}/mark-published-metadata",
        {"published_by": "smoke", "agency_visibility_mode": "visible"},
        OWNER_HEADERS,
    )["version"]
    if published.get("status") != "published" or published.get("agency_visibility_mode") != "visible":
        raise AssertionError(f"Version was not marked published metadata-only: {published}")

    channel = post(
        f"{version_base}/release-channels",
        {
            "channel_code": f"smoke-knowledge-{run_key}",
            "name": "Smoke knowledge channel",
            "description": "Metadata-only smoke release channel.",
            "audience": "all_agencies",
            "is_active": True,
        },
        OWNER_HEADERS,
        201,
    )["release_channel"]
    assignment = post(
        f"{version_base}/release-assignments",
        {
            "channel_id": channel["id"],
            "version_id": version["id"],
            "status": "active",
            "notes": "Metadata-only release assignment.",
        },
        OWNER_HEADERS,
        201,
    )["release_assignment"]
    if assignment.get("status") != "active":
        raise AssertionError(f"Release assignment was not active: {assignment}")

    comparison = post(
        f"{version_base}/comparisons",
        {"base_version_id": base_version["id"], "compare_version_id": version["id"]},
        OWNER_HEADERS,
        201,
    )["comparison"]
    if not comparison.get("added_items"):
        raise AssertionError(f"Comparison did not report added version item: {comparison}")
    rollback = post(
        f"{version_base}/rollback-plans",
        {
            "from_version_id": version["id"],
            "to_version_id": base_version["id"],
            "channel_id": channel["id"],
            "reason": "Smoke rollback plan metadata.",
        },
        OWNER_HEADERS,
        201,
    )["rollback_plan"]
    if rollback.get("status") != "draft":
        raise AssertionError(f"Rollback plan was not created as draft: {rollback}")
    snapshot = post(
        f"{version_base}/versions/{version['id']}/snapshots",
        {"snapshot_type": "manual", "metadata_json": {"smoke": run_key}},
        OWNER_HEADERS,
        201,
    )["snapshot"]

    summary = get(f"{version_base}/summary", OWNER_HEADERS)
    if summary.get("knowledge_version_count", 0) < 2 or summary.get("published_metadata_version_count", 0) < 1:
        raise AssertionError(f"Versioning summary did not include created records: {summary}")
    if version["id"] not in ids(get(f"{version_base}/versions", OWNER_HEADERS)["items"]):
        raise AssertionError("Version list did not include created version.")
    if version_item["id"] not in ids(get(f"{version_base}/versions/{version['id']}/items", OWNER_HEADERS)["items"]):
        raise AssertionError("Version item list did not include created item.")
    if channel["id"] not in ids(get(f"{version_base}/release-channels", OWNER_HEADERS)["items"]):
        raise AssertionError("Release channel list did not include created channel.")
    if assignment["id"] not in ids(get(f"{version_base}/release-assignments", OWNER_HEADERS)["items"]):
        raise AssertionError("Release assignment list did not include created assignment.")
    if comparison["id"] not in ids(get(f"{version_base}/comparisons", OWNER_HEADERS)["items"]):
        raise AssertionError("Comparison list did not include created comparison.")
    if rollback["id"] not in ids(get(f"{version_base}/rollback-plans", OWNER_HEADERS)["items"]):
        raise AssertionError("Rollback plan list did not include created plan.")
    if snapshot["id"] not in ids(get(f"{version_base}/versions/{version['id']}/snapshots", OWNER_HEADERS)["items"]):
        raise AssertionError("Snapshot list did not include created version snapshot.")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_base = f"/api/agencies/{agency_id}/airline-intelligence-knowledge-versions"
    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or agency_summary.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency knowledge summary is not read-only: {agency_summary}")
    agency_current = get(f"{agency_base}/current", OWNER_HEADERS)
    if not agency_current.get("version") or agency_current["version"].get("id") != version["id"]:
        raise AssertionError(f"Agency current version did not expose published metadata version: {agency_current}")
    agency_preview = get(f"{agency_base}/preview", OWNER_HEADERS)
    if not agency_preview.get("version"):
        raise AssertionError(f"Agency preview version missing: {agency_preview}")
    agency_versions = get(f"{agency_base}/versions", OWNER_HEADERS)["items"]
    if version["id"] not in ids(agency_versions):
        raise AssertionError("Agency version list did not include visible version.")
    agency_detail = get(f"{agency_base}/versions/{version['id']}", OWNER_HEADERS)
    if agency_detail.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency version detail did not mark payloads hidden: {agency_detail}")
    for forbidden_key in ["normalized_payload_preview", "frozen_payload", "source_pack_item_id"]:
        if has_key(agency_detail, forbidden_key):
            raise AssertionError(f"Agency version detail exposed raw platform metadata key {forbidden_key}: {agency_detail}")
    request("POST", f"{agency_base}/versions", {"version_code": "blocked"}, OWNER_HEADERS, 405)
    request("PATCH", f"{agency_base}/versions/{version['id']}", {"status": "published"}, OWNER_HEADERS, 405)

    readiness_after = get("/api/readiness")
    section_after = readiness_after.get("airline_intelligence_knowledge_versioning_foundation") or {}
    for key in [
        "knowledge_version_count",
        "version_item_count",
        "release_channel_count",
        "release_assignment_count",
        "comparison_count",
        "rollback_plan_count",
        "snapshot_count",
        "published_metadata_version_count",
        "agency_visible_version_count",
    ]:
        if section_after.get(key, 0) < 1:
            raise AssertionError(f"Readiness knowledge version count did not increment for {key}: {section_after}")
    for key in [
        "operational_promotion_disabled",
        "automatic_promotion_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "scraping_disabled",
        "external_ai_disabled",
        "external_api_calls_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
    ]:
        require_flag(section_after, key)

    print("Airline intelligence knowledge versioning foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
