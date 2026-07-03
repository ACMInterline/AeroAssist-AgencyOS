#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_export_audit_review_foundation import (
    create_audit_source,
    main as smoke_offer_decision_export_audit_review_foundation,
    outcome_signature,
)
from smoke_offer_decision_pack_foundation import option_signature


EXPECTED_PHASE = "phase_38_2_offer_decision_export_compliance_foundation"


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision export governance count {key}")


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
        if "offer-decision-export-governance" in path and any(
            token in path
            for token in [
                "/send",
                "/sms",
                "/publish",
                "public-link",
                "/execute",
                "/ticket",
                "/emd",
                "/pay",
                "/invoice",
                "/settle",
                "/book",
                "/charge",
                "/pnr",
                "/gds",
                "/recommend",
            ]
        ):
            raise AssertionError(f"Decision export governance execution route introduced: {path}")

    for path, method in [
        ("/api/platform/offer-decision-export-governance/summary", "get"),
        ("/api/platform/offer-decision-export-governance/diagnostics", "get"),
        ("/api/platform/offer-decision-export-governance/governance-records", "get"),
        ("/api/platform/offer-decision-export-governance/governance-records/{record_id}", "get"),
        ("/api/platform/offer-decision-export-governance/rules", "get"),
        ("/api/platform/offer-decision-export-governance/retention-policies", "get"),
        ("/api/platform/offer-decision-export-governance/legal-bases", "get"),
        ("/api/platform/offer-decision-export-governance/archive-statuses", "get"),
        ("/api/platform/offer-decision-export-governance/governance-exceptions", "get"),
        ("/api/platform/offer-decision-export-governance/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}/rules", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/rules", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/rules/{rule_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}/retention-policies", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/retention-policies", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/retention-policies/{policy_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}/legal-bases", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/legal-bases", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/legal-bases/{basis_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}/archive-statuses", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/archive-statuses", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/archive-statuses/{status_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}/governance-exceptions", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-exceptions", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-exceptions/{exception_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/governance-records/{record_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-governance/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_governance_foundation") or {}
    for key in [
        "governance_records_enabled",
        "governance_rules_enabled",
        "retention_policies_enabled",
        "legal_bases_enabled",
        "archive_status_metadata_enabled",
        "governance_exceptions_enabled",
        "immutable_governance_snapshots_enabled",
        "agency_governance_ui_enabled",
        "platform_governance_ui_enabled",
        "metadata_only_governance_enabled",
        "automatic_sending_disabled",
        "sms_sending_disabled",
        "public_links_disabled",
        "real_pdf_delivery_disabled",
        "offer_mutation_disabled",
        "price_mutation_disabled",
        "recommendation_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_disabled",
        "invoice_disabled",
        "settlement_disabled",
        "scraping_disabled",
        "external_ai_disabled",
    ]:
        require_flag(section, key)
    require_flag(section, "readiness_required", False)
    for key in [
        "governance_record_count",
        "rule_count",
        "retention_policy_count",
        "legal_basis_count",
        "archive_status_count",
        "exception_count",
        "snapshot_count",
    ]:
        require_count(section, key)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    workspace, export, outcome_detail, option_ids, before_signature = create_audit_source(agency_id, run_key)
    before_outcome_signature = outcome_signature(outcome_detail)
    outcome = outcome_detail["outcome"]
    audit_base = f"/api/agencies/{agency_id}/offer-decision-export-audit-reviews"
    review = post(
        f"{audit_base}/reviews",
        {
            "outcome_id": outcome["id"],
            "title": f"Smoke governance source audit review {run_key}",
            "review_scope": "full_lifecycle",
            "reviewed_by": "smoke-governance-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["review"]

    base = f"/api/agencies/{agency_id}/offer-decision-export-governance"
    record_response = post(
        f"{base}/governance-records",
        {
            "audit_review_id": review["id"],
            "governance_scope": "audit_review",
            "title": f"Smoke export governance record {run_key}",
            "owner_label": "smoke-governance-owner",
            "policy_summary_json": {"run_key": run_key, "source": "smoke"},
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    record = record_response["governance_record"]
    if record.get("audit_review_id") != review["id"] or record.get("export_id") != export["id"]:
        raise AssertionError(f"Governance record not linked to review/export: {record}")
    if record.get("governance_status") != "draft" or record.get("metadata_only") is not True:
        raise AssertionError(f"Governance record was not draft metadata-only: {record}")
    for key in [
        "automatic_sending_disabled",
        "sms_sending_disabled",
        "public_links_disabled",
        "real_pdf_delivery_disabled",
        "offer_mutation_disabled",
        "price_mutation_disabled",
        "recommendation_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_disabled",
        "invoice_disabled",
        "settlement_disabled",
        "scraping_disabled",
        "external_ai_disabled",
    ]:
        if record.get(key) is not True or record_response.get(key) is not True:
            raise AssertionError(f"Governance safety flag missing {key}: record={record} response={record_response}")

    record = patch(
        f"{base}/governance-records/{record['id']}",
        {
            "governance_status": "active",
            "status_reason": "Human governance review started.",
            "metadata_json": {"run_key": run_key, "status_update": True},
        },
        OWNER_HEADERS,
    )["governance_record"]
    if record.get("governance_status") != "active":
        raise AssertionError(f"Governance record status update failed: {record}")

    rule = post(
        f"{base}/governance-records/{record['id']}/rules",
        {
            "rule_type": "retention",
            "rule_status": "active",
            "rule_name": f"Smoke governance retention rule {run_key}",
            "rule_text": "Retain export review evidence for manual governance review.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["rule"]
    rule = patch(
        f"{base}/rules/{rule['id']}",
        {
            "rule_status": "retired",
            "rule_text": "Retired by smoke metadata review; no destructive cleanup performed.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["rule"]
    if rule.get("rule_status") != "retired":
        raise AssertionError(f"Governance rule update failed: {rule}")

    retention_policy = post(
        f"{base}/governance-records/{record['id']}/retention-policies",
        {
            "policy_name": f"Smoke retention policy {run_key}",
            "retention_period_days": 730,
            "retention_action": "review",
            "notes": "Metadata-only retention review.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["retention_policy"]
    retention_policy = patch(
        f"{base}/retention-policies/{retention_policy['id']}",
        {
            "retention_action": "hold",
            "review_required": True,
            "notes": "Hold metadata only; no deletion or archive execution.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["retention_policy"]
    if retention_policy.get("retention_action") != "hold" or retention_policy.get("destructive_delete_disabled") is not True:
        raise AssertionError(f"Retention policy metadata update failed: {retention_policy}")

    legal_basis = post(
        f"{base}/governance-records/{record['id']}/legal-bases",
        {
            "basis_type": "agency_policy",
            "basis_label": f"Smoke legal basis {run_key}",
            "notes": "Human-reviewed legal basis metadata only.",
            "evidence_reference_metadata": "Internal policy reference metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["legal_basis"]
    legal_basis = patch(
        f"{base}/legal-bases/{legal_basis['id']}",
        {
            "notes": "Legal basis note updated by human reviewer metadata.",
            "evidence_reference_metadata": "Updated internal reference metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["legal_basis"]
    if legal_basis.get("basis_type") != "agency_policy":
        raise AssertionError(f"Legal basis metadata update failed: {legal_basis}")

    archive_status = post(
        f"{base}/governance-records/{record['id']}/archive-statuses",
        {
            "archive_status": "eligible_for_metadata_archive",
            "status_reason": "Smoke archive eligibility metadata only.",
            "reviewed_by": "smoke-governance-reviewer",
            "archive_reference_metadata": "No real archive action performed.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["archive_status"]
    archive_status = patch(
        f"{base}/archive-statuses/{archive_status['id']}",
        {
            "archive_status": "hold",
            "status_reason": "Metadata-only hold.",
            "reviewed_by": "smoke-governance-reviewer",
            "archive_reference_metadata": "Still no archive execution.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["archive_status"]
    if archive_status.get("archive_status") != "hold" or archive_status.get("real_archive_execution_disabled") is not True:
        raise AssertionError(f"Archive status metadata update failed: {archive_status}")

    exception = post(
        f"{base}/governance-records/{record['id']}/governance-exceptions",
        {
            "exception_type": "legal_basis_gap",
            "severity": "medium",
            "title": f"Smoke governance exception {run_key}",
            "description": "Open governance exception metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["governance_exception"]
    exception = patch(
        f"{base}/governance-exceptions/{exception['id']}",
        {
            "exception_status": "resolved",
            "resolved_by": "smoke-governance-reviewer",
            "resolution_notes": "Resolved in governance metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["governance_exception"]
    if exception.get("exception_status") != "resolved" or not exception.get("resolved_at"):
        raise AssertionError(f"Governance exception resolution failed: {exception}")

    snapshot = post(
        f"{base}/governance-records/{record['id']}/snapshots",
        {
            "snapshot_type": "policy_review",
            "created_by": "smoke-governance-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("metadata_only") is not True:
        raise AssertionError(f"Governance snapshot was not immutable metadata: {snapshot}")

    detail = get(f"{base}/governance-records/{record['id']}", OWNER_HEADERS)
    detail_record = detail["governance_record"]
    if detail_record.get("rule_count") < 1 or detail_record.get("retention_policy_count") < 1 or detail_record.get("legal_basis_count") < 1:
        raise AssertionError(f"Governance detail counts did not refresh: {detail_record}")
    if detail_record.get("archive_status_count") < 1 or detail_record.get("exception_count") < 1 or detail_record.get("snapshot_count") < 1:
        raise AssertionError(f"Governance detail counts missing archive/exception/snapshot: {detail_record}")

    if record["id"] not in ids(get(f"{base}/governance-records?status=active", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency governance record status filter did not return created record.")
    if rule["id"] not in ids(get(f"{base}/rules?governance_record_id={record['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency governance rules list did not return created rule.")
    if retention_policy["id"] not in ids(get(f"{base}/retention-policies?governance_record_id={record['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency retention policies list did not return created policy.")
    if legal_basis["id"] not in ids(get(f"{base}/legal-bases?governance_record_id={record['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency legal bases list did not return created basis.")
    if archive_status["id"] not in ids(get(f"{base}/archive-statuses?governance_record_id={record['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency archive statuses list did not return created status.")
    if exception["id"] not in ids(get(f"{base}/governance-exceptions?governance_record_id={record['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency governance exceptions list did not return created exception.")
    if snapshot["id"] not in ids(get(f"{base}/snapshots?governance_record_id={record['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency governance snapshots list did not return created snapshot.")

    platform_base = "/api/platform/offer-decision-export-governance"
    platform_summary = get(f"{platform_base}/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform governance summary is not read-only/safe: {platform_summary}")
    if record["id"] not in ids(get(f"{platform_base}/governance-records", OWNER_HEADERS)["items"]):
        raise AssertionError("Platform governance diagnostics did not include created record.")
    platform_detail = get(f"{platform_base}/governance-records/{record['id']}", OWNER_HEADERS)
    if platform_detail.get("read_only") is not True or platform_detail.get("governance_record", {}).get("id") != record["id"]:
        raise AssertionError(f"Platform governance detail was not read-only: {platform_detail}")
    for path in ["/diagnostics", "/rules", "/retention-policies", "/legal-bases", "/archive-statuses", "/governance-exceptions", "/snapshots"]:
        result = get(f"{platform_base}{path}", OWNER_HEADERS)
        if result.get("read_only") is not True:
            raise AssertionError(f"Platform governance diagnostics endpoint not read-only: {path} {result}")
    request("POST", f"{platform_base}/governance-records", {"audit_review_id": review["id"]}, OWNER_HEADERS, 405)
    request("POST", f"{base}/governance-records/{record['id']}/send", {}, OWNER_HEADERS, 404)

    after_outcome_signature = outcome_signature(get(f"/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome['id']}", OWNER_HEADERS))
    if after_outcome_signature != before_outcome_signature:
        raise AssertionError(f"Governance mutated delivery outcome counts/status: before={before_outcome_signature} after={after_outcome_signature}")
    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if after_signature != before_signature:
        raise AssertionError("Governance mutated offer option pricing/status.")

    readiness_after = get("/api/readiness")
    governance_section = readiness_after.get("offer_decision_export_governance_foundation") or {}
    for key in [
        "governance_record_count",
        "rule_count",
        "retention_policy_count",
        "legal_basis_count",
        "archive_status_count",
        "exception_count",
        "snapshot_count",
    ]:
        if governance_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness governance count did not increment for {key}: {governance_section}")

    smoke_offer_decision_export_audit_review_foundation()
    print("Offer decision export governance foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
