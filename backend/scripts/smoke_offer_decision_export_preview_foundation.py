#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_export_foundation import create_explanation_records, main as smoke_offer_decision_export_foundation
from smoke_offer_decision_pack_foundation import create_advisor_snapshot, main as smoke_offer_decision_pack_foundation, option_signature
from smoke_offer_policy_advisor_integration_foundation import create_offer_workspace, main as smoke_offer_policy_advisor_integration_foundation
from smoke_policy_comparison_service_advisor_foundation import main as smoke_policy_comparison_service_advisor_foundation, seed_airline_facts
from smoke_ancillary_pricing_exception_foundation import main as smoke_ancillary_pricing_exception_foundation
from smoke_service_mechanics_mapping_foundation import main as smoke_service_mechanics_mapping_foundation
from smoke_service_taxonomy_foundation import main as smoke_service_taxonomy_foundation
from smoke_airline_policy_ingestion_foundation import main as smoke_airline_policy_ingestion_foundation


from phase_assertions import application_phase_is_at_least


MINIMUM_PHASE = "phase_37_6_offer_decision_export_preview_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision export preview count {key}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def main() -> int:
    run_key = uuid4().hex[:10]
    domain_code = f"smoke_preview_{run_key}"
    family_code = f"wheelchair_preview_{run_key}"
    variant_code = f"wchr_preview_{run_key}"

    health = get("/api/health")
    if not application_phase_is_at_least(health.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "offer-decision-export-previews" in path and any(token in path for token in ["/execute", "/issue", "/pay", "/invoice", "/settle", "/book", "/send", "public-link"]):
            raise AssertionError(f"Decision export preview execution route introduced: {path}")
    for path, method in [
        ("/api/platform/offer-decision-export-previews/summary", "get"),
        ("/api/platform/offer-decision-export-previews/previews", "get"),
        ("/api/platform/offer-decision-export-previews/previews/{preview_id}", "get"),
        ("/api/platform/offer-decision-export-previews/sections", "get"),
        ("/api/platform/offer-decision-export-previews/blocks", "get"),
        ("/api/platform/offer-decision-export-previews/validations", "get"),
        ("/api/platform/offer-decision-export-previews/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/previews", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/previews/{preview_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/generate", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/sections", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/blocks", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/validations", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/previews/{preview_id}/validate", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/previews/{preview_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-previews/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if not application_phase_is_at_least(readiness.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_preview_foundation") or {}
    for key in [
        "export_previews_enabled",
        "preview_sections_enabled",
        "preview_blocks_enabled",
        "preview_validations_enabled",
        "immutable_preview_snapshots_enabled",
        "agency_export_preview_ui_enabled",
        "platform_export_preview_ui_enabled",
        "metadata_only_rendering_enabled",
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
    for key in ["preview_count", "section_count", "block_count", "validation_count", "snapshot_count"]:
        require_count(section, key)

    for airline_code, amount in [("PX", 35.0), ("RV", 55.0)]:
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
            "pack_name": f"Smoke preview decision pack {run_key}",
            "advisor_context_ids": [advisor_context["id"]],
            "advisor_saved_snapshot_ids": [advisor_snapshot["id"]],
            "metadata_json": {"run_key": run_key, "phase": "37.6"},
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
            "export_name": f"Smoke decision export preview source {run_key}",
            "include_recipient_draft": True,
            "recipient_type": "agency_review",
            "recipient_name": "Preview Reviewer",
            "recipient_email": f"preview-{run_key}@example.com",
            "subject": f"Smoke preview source {run_key}",
            "message_body": "Draft only. No automatic sending or public link was created.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    export = export_response["export"]
    artifact_ids = [item["id"] for item in export_response.get("artifacts") or []]

    base = f"/api/agencies/{agency_id}/offer-decision-export-previews"
    preview_response = post(
        f"{base}/generate",
        {
            "export_id": export["id"],
            "render_profile": "internal_review",
            "template_profile": "smoke_metadata_preview",
            "reviewed_by": "smoke-internal-reviewer",
            "source_artifact_ids": artifact_ids,
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    preview = preview_response["preview"]
    if preview.get("export_id") != export["id"] or preview.get("metadata_only_rendering_enabled") is not True:
        raise AssertionError(f"Preview not linked or metadata-only: {preview}")
    for key in ["automatic_sending_disabled", "public_links_disabled", "real_pdf_delivery_disabled", "offer_price_mutation_disabled", "provider_execution_disabled", "booking_execution_disabled", "ticket_emd_issuance_disabled", "payment_invoice_settlement_disabled"]:
        if preview.get(key) is not True or preview_response.get(key) is not True:
            raise AssertionError(f"Preview safety flag missing {key}: preview={preview} response={preview_response}")
    if preview.get("section_count", 0) < 12 or preview.get("block_count", 0) < 12:
        raise AssertionError(f"Preview counts incomplete: {preview}")

    section_keys = {item.get("section_key") for item in preview_response.get("sections") or []}
    expected_sections = {
        "executive_summary",
        "selected_decision_pack_overview",
        "option_comparison",
        "advisor_evidence",
        "warnings",
        "human_review_notes",
        "explanation_narrative",
        "decision_timeline",
        "acknowledgement_status",
        "export_artifact_metadata",
        "recipient_draft_metadata",
        "audit_trail",
    }
    if expected_sections - section_keys:
        raise AssertionError(f"Preview missing sections: {expected_sections - section_keys}")

    block_types = {item.get("block_type") for item in preview_response.get("blocks") or []}
    for required_type in ["heading", "key_value_table", "safety_disclaimer", "artifact_reference", "recipient_draft"]:
        if required_type not in block_types:
            raise AssertionError(f"Preview missing block type {required_type}: {block_types}")

    validation_response = post(
        f"{base}/previews/{preview['id']}/validate",
        {"internal_reviewer": "smoke-internal-reviewer", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    validations = validation_response.get("validations") or []
    validation_keys = {item.get("validation_key") for item in validations}
    expected_validation_keys = {
        "missing_decision_pack",
        "missing_explanation",
        "missing_timeline",
        "missing_acknowledgements",
        "missing_recipient_draft",
        "missing_artifact_metadata",
        "missing_internal_reviewer",
        "safety_boundary_reminder",
    }
    if expected_validation_keys - validation_keys:
        raise AssertionError(f"Preview validations missing keys: {expected_validation_keys - validation_keys}")
    if any(item.get("validation_key") != "safety_boundary_reminder" and item.get("validation_status") != "pass" for item in validations):
        raise AssertionError(f"Preview metadata validation unexpectedly failed: {validations}")

    snapshot_response = post(
        f"{base}/previews/{preview['id']}/snapshots",
        {"snapshot_name": f"Smoke preview snapshot {run_key}", "metadata_json": {"run_key": run_key}},
        OWNER_HEADERS,
        201,
    )
    snapshot = snapshot_response["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("metadata_only") is not True:
        raise AssertionError(f"Preview snapshot was not immutable metadata: {snapshot}")

    detail = get(f"{base}/previews/{preview['id']}", OWNER_HEADERS)
    if detail.get("preview", {}).get("id") != preview["id"] or len(detail.get("sections") or []) < 12 or len(detail.get("blocks") or []) < 12:
        raise AssertionError(f"Preview detail missed sections/blocks: {detail}")
    listed_previews = get(f"{base}/previews?export_id={export['id']}", OWNER_HEADERS)["items"]
    listed_sections = get(f"{base}/sections?preview_id={preview['id']}", OWNER_HEADERS)["items"]
    listed_blocks = get(f"{base}/blocks?preview_id={preview['id']}", OWNER_HEADERS)["items"]
    listed_validations = get(f"{base}/validations?preview_id={preview['id']}", OWNER_HEADERS)["items"]
    listed_snapshots = get(f"{base}/snapshots?preview_id={preview['id']}", OWNER_HEADERS)["items"]
    if preview["id"] not in ids(listed_previews) or not listed_sections or not listed_blocks:
        raise AssertionError("Agency preview/section/block lists missed created records.")
    if {item["id"] for item in validations} - ids(listed_validations) or snapshot["id"] not in ids(listed_snapshots):
        raise AssertionError("Agency validation/snapshot lists missed created records.")

    platform_summary = get("/api/platform/offer-decision-export-previews/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform preview diagnostics changed execution boundary: {platform_summary}")
    platform_previews = get("/api/platform/offer-decision-export-previews/previews", OWNER_HEADERS)["items"]
    platform_validations = get("/api/platform/offer-decision-export-previews/validations", OWNER_HEADERS)["items"]
    platform_snapshots = get("/api/platform/offer-decision-export-previews/snapshots", OWNER_HEADERS)["items"]
    if preview["id"] not in ids(platform_previews):
        raise AssertionError("Platform diagnostics did not list offer decision export preview.")
    if {item["id"] for item in validations} - ids(platform_validations) or snapshot["id"] not in ids(platform_snapshots):
        raise AssertionError("Platform diagnostics missed preview validations or snapshots.")
    platform_blocked_status, _ = request(
        "POST",
        "/api/platform/offer-decision-export-previews/previews",
        {"export_id": export["id"]},
        OWNER_HEADERS,
        expect=405,
    )
    if platform_blocked_status != 405:
        raise AssertionError(f"Platform preview mutation route unexpectedly available: {platform_blocked_status}")
    agency_block_blocked_status, _ = request(
        "POST",
        f"{base}/blocks",
        {"preview_id": preview["id"]},
        OWNER_HEADERS,
        expect=405,
    )
    if agency_block_blocked_status != 405:
        raise AssertionError(f"Agency preview block mutation route unexpectedly available: {agency_block_blocked_status}")

    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if before_signature != after_signature:
        raise AssertionError(f"Decision export preview mutated offer option pricing/status: before={before_signature} after={after_signature}")
    if any(item.get("status") == "recommended" for item in after_signature.values()):
        raise AssertionError(f"Decision export preview auto-selected an option: {after_signature}")

    final_section = get("/api/readiness").get("offer_decision_export_preview_foundation") or {}
    for key in ["preview_count", "section_count", "block_count", "validation_count", "snapshot_count"]:
        if final_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created preview records: {final_section}")

    for regression in [
        smoke_offer_decision_export_foundation,
        smoke_offer_decision_pack_foundation,
        smoke_offer_policy_advisor_integration_foundation,
        smoke_policy_comparison_service_advisor_foundation,
        smoke_ancillary_pricing_exception_foundation,
        smoke_service_mechanics_mapping_foundation,
        smoke_service_taxonomy_foundation,
        smoke_airline_policy_ingestion_foundation,
    ]:
        regression()

    print("Offer decision export preview foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
