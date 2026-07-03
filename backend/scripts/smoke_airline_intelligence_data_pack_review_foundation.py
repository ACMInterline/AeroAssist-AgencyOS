#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_39_5_saas_subscription_entitlement_foundation"


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


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
        if "airline-intelligence-data-pack-reviews" in path and any(
            token in path
            for token in [
                "/scrape",
                "/external",
                "/ai/",
                "/promote/",
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
                "/publish",
                "public-link",
            ]
        ):
            raise AssertionError(f"Airline data pack review execution route introduced: {path}")

    for path, method in [
        ("/api/platform/airline-intelligence-data-pack-reviews/summary", "get"),
        ("/api/platform/airline-intelligence-data-pack-reviews/reviews", "get"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/reviews", "post"),
        ("/api/platform/airline-intelligence-data-pack-reviews/reviews/{review_id}", "get"),
        ("/api/platform/airline-intelligence-data-pack-reviews/reviews/{review_id}", "patch"),
        ("/api/platform/airline-intelligence-data-pack-reviews/reviews/{review_id}/checklist-items", "get"),
        ("/api/platform/airline-intelligence-data-pack-reviews/reviews/{review_id}/checklist-items", "post"),
        ("/api/platform/airline-intelligence-data-pack-reviews/checklist-items/{checklist_item_id}", "patch"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/field-mappings", "get"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/field-mappings", "post"),
        ("/api/platform/airline-intelligence-data-pack-reviews/field-mappings/{mapping_id}", "patch"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/detect-conflicts", "post"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/conflicts", "get"),
        ("/api/platform/airline-intelligence-data-pack-reviews/conflicts/{conflict_id}", "patch"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/promotion-readiness", "post"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/promotion-readiness", "get"),
        ("/api/platform/airline-intelligence-data-pack-reviews/reviews/{review_id}/snapshots", "post"),
        ("/api/platform/airline-intelligence-data-pack-reviews/packs/{pack_id}/snapshots", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews/summary", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews/coverage", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews/reviews", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews/reviews/{review_id}", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews/packs/{pack_id}/promotion-readiness", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_intelligence_data_pack_review_foundation") or {}
    for key in [
        "review_checklists_enabled",
        "field_mappings_enabled",
        "duplicate_conflict_detection_enabled",
        "promotion_readiness_metadata_enabled",
        "safe_consumption_flags_enabled",
        "agency_plain_language_coverage_enabled",
        "platform_review_ui_enabled",
        "agency_review_coverage_ui_enabled",
        "metadata_only_review_enabled",
        "automatic_promotion_disabled",
        "scraping_disabled",
        "external_api_calls_disabled",
        "external_ai_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
        "recommendations_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
    ]:
        require_flag(section, key)
    for key in [
        "review_count",
        "review_checklist_item_count",
        "field_mapping_count",
        "conflict_count",
        "open_conflict_count",
        "promotion_readiness_count",
        "promotion_ready_count",
        "review_snapshot_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing review count {key}")

    pack_base = "/api/platform/airline-intelligence-data-packs"
    review_base = "/api/platform/airline-intelligence-data-pack-reviews"
    pack = post(
        f"{pack_base}/packs",
        {
            "name": f"Smoke review data pack {run_key}",
            "slug": f"smoke-review-data-pack-{run_key}",
            "description": "Operationally verified staged data for review smoke.",
            "pack_type": "airline_profile_pack",
            "airline_codes": ["ZR"],
            "target_domains": ["airline_profile"],
            "source_type": "curated",
            "source_reference": f"Smoke reviewed source {run_key}",
            "version_label": "review-v1",
            "is_demo_data": False,
            "is_operationally_verified": True,
            "safe_for_agency_internal_crm": True,
            "safe_for_agency_display": True,
            "safe_for_cms_display": True,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": True,
            "verification_status": "reviewed",
            "confidence_score": 0.91,
            "human_summary": "Reviewed airline profile coverage for smoke validation.",
            "operator_guidance": "Safe for internal review surfaces only.",
        },
        OWNER_HEADERS,
        201,
    )["pack"]
    item = post(
        f"{pack_base}/packs/{pack['id']}/items",
        {
            "airline_iata_code": "ZR",
            "target_domain": "airline_profile",
            "display_name": "Smoke reviewed airline profile",
            "plain_language_summary": "Reviewed airline profile metadata for agency coverage.",
            "proposed_action": "review_only",
            "payload": {"airline_name": "Smoke Review Air", "country": "Test"},
            "normalized_payload": {"airline_name": "Smoke Review Air"},
            "source_reference": f"Smoke item source {run_key}",
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
            "review_title": f"Smoke review {run_key}",
            "plain_language_coverage_summary": "Reviewed airline profile coverage for agency use.",
            "safe_for_agency_internal_crm": True,
            "safe_for_agency_display": True,
            "safe_for_cms_display": True,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": True,
        },
        OWNER_HEADERS,
        201,
    )["review"]
    if review.get("pack_id") != pack["id"] or review.get("status") != "in_review":
        raise AssertionError(f"Review was not created correctly: {review}")

    detail = get(f"{review_base}/reviews/{review['id']}", OWNER_HEADERS)
    checklist = detail.get("checklist_items", [])
    if len(checklist) < 2 or item["id"] not in {entry.get("item_id") for entry in checklist if entry.get("item_id")}:
        raise AssertionError(f"Default review checklist was not created for pack and item: {detail}")
    if item["id"] not in ids(detail.get("items", [])):
        raise AssertionError("Review detail did not include staged item for platform mapping review.")

    mapping = post(
        f"{review_base}/packs/{pack['id']}/field-mappings",
        {
            "item_id": item["id"],
            "source_payload_path": "payload.airline_name",
            "target_collection": "airline_intelligence_profiles",
            "target_field_path": "name",
            "target_record_key": "ZR",
            "mapping_status": "approved",
            "mapping_confidence": 0.95,
            "would_create_record": False,
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
    if mapping.get("mapping_status") != "approved" or mapping.get("automatic_promotion_disabled") is not True:
        raise AssertionError(f"Field mapping did not preserve metadata-only safety: {mapping}")

    for checklist_item in checklist:
        updated = patch(
            f"{review_base}/checklist-items/{checklist_item['id']}",
            {"status": "passed", "completed_by": "smoke"},
            OWNER_HEADERS,
        )["checklist_item"]
        if updated.get("status") != "passed":
            raise AssertionError(f"Checklist item did not pass: {updated}")

    conflicts = post(f"{review_base}/packs/{pack['id']}/detect-conflicts", {}, OWNER_HEADERS)["conflicts"]
    open_conflicts = get(f"{review_base}/packs/{pack['id']}/conflicts?status=open", OWNER_HEADERS)["items"]
    if conflicts or open_conflicts:
        raise AssertionError(f"Reviewed mapped pack should not have open conflicts: {conflicts} / {open_conflicts}")

    approved_review = patch(
        f"{review_base}/reviews/{review['id']}",
        {"status": "approved", "approved_by": "smoke"},
        OWNER_HEADERS,
    )["review"]
    if approved_review.get("status") != "approved":
        raise AssertionError(f"Review approval failed: {approved_review}")

    readiness_record = post(
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
    if readiness_record.get("ready_for_promotion") is not True or readiness_record.get("status") != "ready":
        raise AssertionError(f"Promotion-readiness metadata was not ready: {readiness_record}")

    snapshot = post(
        f"{review_base}/reviews/{review['id']}/snapshots",
        {"snapshot_type": "readiness_marked", "created_by": "smoke", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )["snapshot"]
    if snapshot.get("immutable") is not True:
        raise AssertionError(f"Review snapshot was not immutable metadata: {snapshot}")

    platform_summary = get(f"{review_base}/summary", OWNER_HEADERS)
    if platform_summary.get("promotion_ready_count", 0) < 1 or platform_summary.get("automatic_promotion_disabled") is not True:
        raise AssertionError(f"Platform review summary missing readiness/safety state: {platform_summary}")
    if review["id"] not in ids(get(f"{review_base}/reviews", OWNER_HEADERS)["items"]):
        raise AssertionError("Review list did not include created review.")
    if mapping["id"] not in ids(get(f"{review_base}/packs/{pack['id']}/field-mappings", OWNER_HEADERS)["items"]):
        raise AssertionError("Field mapping list did not include created mapping.")
    if snapshot["id"] not in ids(get(f"{review_base}/packs/{pack['id']}/snapshots", OWNER_HEADERS)["items"]):
        raise AssertionError("Review snapshot list did not include created snapshot.")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_base = f"/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews"
    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or agency_summary.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency review summary is not read-only: {agency_summary}")
    agency_coverage = get(f"{agency_base}/coverage", OWNER_HEADERS)
    if agency_coverage.get("read_only") is not True or agency_coverage.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency coverage is not read-only: {agency_coverage}")
    agency_reviews = get(f"{agency_base}/reviews", OWNER_HEADERS)["items"]
    if review["id"] not in ids(agency_reviews):
        raise AssertionError("Agency review list did not include created review.")
    agency_detail = get(f"{agency_base}/reviews/{review['id']}", OWNER_HEADERS)
    if agency_detail.get("payloads_hidden") is not True or "field_mappings" in agency_detail:
        raise AssertionError(f"Agency review detail exposed platform mapping payload: {agency_detail}")
    agency_readiness = get(f"{agency_base}/packs/{pack['id']}/promotion-readiness", OWNER_HEADERS)["items"]
    if not agency_readiness or agency_readiness[0].get("ready_for_promotion") is not True:
        raise AssertionError(f"Agency promotion-readiness view missing ready metadata: {agency_readiness}")
    request("POST", f"{agency_base}/reviews", {"pack_id": pack["id"]}, OWNER_HEADERS, 405)
    request("PATCH", f"{agency_base}/reviews/{review['id']}", {"status": "approved"}, OWNER_HEADERS, 405)

    readiness_after = get("/api/readiness")
    section_after = readiness_after.get("airline_intelligence_data_pack_review_foundation") or {}
    for key in ["review_count", "review_checklist_item_count", "field_mapping_count", "promotion_readiness_count", "promotion_ready_count", "review_snapshot_count"]:
        if section_after.get(key, 0) < 1:
            raise AssertionError(f"Readiness review count did not increment for {key}: {section_after}")

    print("Airline intelligence data pack review foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
