#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_offer_decision_export_audit_review_foundation import create_audit_source, outcome_signature
from smoke_offer_decision_export_governance_foundation import main as smoke_offer_decision_export_governance_foundation
from smoke_offer_decision_pack_foundation import option_signature


EXPECTED_PHASE = "phase_39_2_airline_intelligence_knowledge_versioning_foundation"


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing offer decision export compliance count {key}")


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
        if "offer-decision-export-compliance" in path and any(
            token in path
            for token in [
                "/send",
                "/sms",
                "/notify",
                "/publish",
                "public-link",
                "/execute",
                "/ticket",
                "/emd",
                "/pay",
                "/invoice",
                "/settle",
                "/book",
                "/reserve",
                "/charge",
                "/pnr",
                "/gds",
                "/recommend",
                "/ai",
            ]
        ):
            raise AssertionError(f"Decision export compliance execution route introduced: {path}")

    for path, method in [
        ("/api/platform/offer-decision-export-compliance/summary", "get"),
        ("/api/platform/offer-decision-export-compliance/diagnostics", "get"),
        ("/api/platform/offer-decision-export-compliance/evidence", "get"),
        ("/api/platform/offer-decision-export-compliance/evidence/{evidence_id}", "get"),
        ("/api/platform/offer-decision-export-compliance/requirements", "get"),
        ("/api/platform/offer-decision-export-compliance/checks", "get"),
        ("/api/platform/offer-decision-export-compliance/results", "get"),
        ("/api/platform/offer-decision-export-compliance/exceptions", "get"),
        ("/api/platform/offer-decision-export-compliance/snapshots", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/summary", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence/{evidence_id}", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence/{evidence_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence/{evidence_id}/requirements", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/requirements", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/requirements/{requirement_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence/{evidence_id}/checks", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/checks", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/checks/{check_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence/{evidence_id}/results", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/results", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/results/{result_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence/{evidence_id}/exceptions", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/exceptions", "get"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/exceptions/{exception_id}", "patch"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/evidence/{evidence_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/offer-decision-export-compliance/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("offer_decision_export_compliance_foundation") or {}
    for key in [
        "compliance_evidence_enabled",
        "compliance_requirements_enabled",
        "compliance_checks_enabled",
        "compliance_results_enabled",
        "compliance_exceptions_enabled",
        "immutable_compliance_snapshots_enabled",
        "agency_compliance_ui_enabled",
        "platform_compliance_ui_enabled",
        "metadata_only_enabled",
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
    for key in ["evidence_count", "requirement_count", "check_count", "result_count", "exception_count", "snapshot_count"]:
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
            "title": f"Smoke compliance source audit review {run_key}",
            "review_scope": "full_lifecycle",
            "reviewed_by": "smoke-compliance-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["review"]

    governance_base = f"/api/agencies/{agency_id}/offer-decision-export-governance"
    governance_record = post(
        f"{governance_base}/governance-records",
        {
            "audit_review_id": review["id"],
            "governance_scope": "audit_review",
            "title": f"Smoke compliance governance record {run_key}",
            "owner_label": "smoke-compliance-owner",
            "policy_summary_json": {"run_key": run_key, "source": "compliance_smoke"},
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["governance_record"]

    base = f"/api/agencies/{agency_id}/offer-decision-export-compliance"
    evidence_response = post(
        f"{base}/evidence",
        {
            "governance_record_id": governance_record["id"],
            "evidence_scope": "governance_record",
            "title": f"Smoke compliance evidence {run_key}",
            "owner_label": "smoke-compliance-reviewer",
            "evidence_summary_json": {"run_key": run_key, "source": "smoke"},
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )
    evidence = evidence_response["evidence"]
    if evidence.get("governance_record_id") != governance_record["id"] or evidence.get("export_id") != export["id"]:
        raise AssertionError(f"Compliance evidence not linked to governance/export: {evidence}")
    if evidence.get("evidence_status") != "draft" or evidence.get("metadata_only") is not True:
        raise AssertionError(f"Compliance evidence was not draft metadata-only: {evidence}")
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
        if evidence.get(key) is not True or evidence_response.get(key) is not True:
            raise AssertionError(f"Compliance safety flag missing {key}: evidence={evidence} response={evidence_response}")

    evidence = patch(
        f"{base}/evidence/{evidence['id']}",
        {
            "evidence_status": "in_review",
            "status_reason": "Human compliance evidence review started.",
            "metadata_json": {"run_key": run_key, "status_update": True},
        },
        OWNER_HEADERS,
    )["evidence"]
    if evidence.get("evidence_status") != "in_review":
        raise AssertionError(f"Compliance evidence status update failed: {evidence}")

    requirement = post(
        f"{base}/evidence/{evidence['id']}/requirements",
        {
            "requirement_type": "governance_rule",
            "requirement_status": "pending",
            "requirement_name": f"Smoke compliance requirement {run_key}",
            "description": "Requirement metadata proves why governance is satisfied.",
            "source_reference_metadata": "Governance record metadata reference.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["requirement"]
    requirement = patch(
        f"{base}/requirements/{requirement['id']}",
        {
            "requirement_status": "satisfied",
            "description": "Satisfied by human-reviewed metadata evidence.",
            "source_reference_metadata": "Updated governance metadata reference.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["requirement"]
    if requirement.get("requirement_status") != "satisfied":
        raise AssertionError(f"Compliance requirement update failed: {requirement}")

    check = post(
        f"{base}/evidence/{evidence['id']}/checks",
        {
            "requirement_id": requirement["id"],
            "check_type": "manual_review",
            "check_status": "passed",
            "check_name": f"Smoke compliance check {run_key}",
            "check_metadata_json": {"reviewed": True},
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["check"]
    check = patch(
        f"{base}/checks/{check['id']}",
        {
            "check_status": "failed",
            "check_metadata_json": {"failure_recorded": True},
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["check"]
    if check.get("check_status") != "failed" or not check.get("performed_at"):
        raise AssertionError(f"Compliance check update failed: {check}")

    result = post(
        f"{base}/evidence/{evidence['id']}/results",
        {
            "requirement_id": requirement["id"],
            "check_id": check["id"],
            "result_status": "failed",
            "result_name": f"Smoke compliance result {run_key}",
            "result_summary": "Failure metadata recorded for human review.",
            "evidence_reference_metadata": "Compliance evidence reference metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["result"]
    result = patch(
        f"{base}/results/{result['id']}",
        {
            "result_status": "passed",
            "result_summary": "Human reviewer recorded passing compliance evidence metadata.",
            "evidence_reference_metadata": "Updated compliance reference metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["result"]
    if result.get("result_status") != "passed" or not result.get("evaluated_at"):
        raise AssertionError(f"Compliance result update failed: {result}")

    exception = post(
        f"{base}/evidence/{evidence['id']}/exceptions",
        {
            "requirement_id": requirement["id"],
            "check_id": check["id"],
            "exception_type": "check_failure",
            "severity": "medium",
            "title": f"Smoke compliance exception {run_key}",
            "description": "Open compliance exception metadata only.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["exception"]
    exception = patch(
        f"{base}/exceptions/{exception['id']}",
        {
            "exception_status": "resolved",
            "resolved_by": "smoke-compliance-reviewer",
            "resolution_notes": "Resolved in compliance metadata.",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
    )["exception"]
    if exception.get("exception_status") != "resolved" or not exception.get("resolved_at"):
        raise AssertionError(f"Compliance exception resolution failed: {exception}")

    snapshot = post(
        f"{base}/evidence/{evidence['id']}/snapshots",
        {
            "snapshot_type": "result_review",
            "created_by": "smoke-compliance-reviewer",
            "metadata_json": {"run_key": run_key},
        },
        OWNER_HEADERS,
        201,
    )["snapshot"]
    if snapshot.get("immutable") is not True or snapshot.get("metadata_only") is not True:
        raise AssertionError(f"Compliance snapshot was not immutable metadata: {snapshot}")

    detail = get(f"{base}/evidence/{evidence['id']}", OWNER_HEADERS)
    detail_evidence = detail["evidence"]
    if detail_evidence.get("requirement_count") < 1 or detail_evidence.get("check_count") < 1 or detail_evidence.get("result_count") < 1:
        raise AssertionError(f"Compliance detail counts did not refresh: {detail_evidence}")
    if detail_evidence.get("failed_check_count") < 1 or detail_evidence.get("exception_count") < 1 or detail_evidence.get("snapshot_count") < 1:
        raise AssertionError(f"Compliance detail counts missing failed check/exception/snapshot: {detail_evidence}")

    if evidence["id"] not in ids(get(f"{base}/evidence?status=in_review", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency compliance evidence status filter did not return created evidence.")
    if requirement["id"] not in ids(get(f"{base}/requirements?evidence_id={evidence['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency compliance requirements list did not return created requirement.")
    if check["id"] not in ids(get(f"{base}/checks?evidence_id={evidence['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency compliance checks list did not return created check.")
    if result["id"] not in ids(get(f"{base}/results?evidence_id={evidence['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency compliance results list did not return created result.")
    if exception["id"] not in ids(get(f"{base}/exceptions?evidence_id={evidence['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency compliance exceptions list did not return created exception.")
    if snapshot["id"] not in ids(get(f"{base}/snapshots?evidence_id={evidence['id']}", OWNER_HEADERS)["items"]):
        raise AssertionError("Agency compliance snapshots list did not return created snapshot.")

    platform_base = "/api/platform/offer-decision-export-compliance"
    platform_summary = get(f"{platform_base}/summary", OWNER_HEADERS)
    if platform_summary.get("platform_read_only_diagnostics") is not True or platform_summary.get("operational_execution_disabled") is not True:
        raise AssertionError(f"Platform compliance summary is not read-only/safe: {platform_summary}")
    if evidence["id"] not in ids(get(f"{platform_base}/evidence", OWNER_HEADERS)["items"]):
        raise AssertionError("Platform compliance diagnostics did not include created evidence.")
    platform_detail = get(f"{platform_base}/evidence/{evidence['id']}", OWNER_HEADERS)
    if platform_detail.get("read_only") is not True or platform_detail.get("evidence", {}).get("id") != evidence["id"]:
        raise AssertionError(f"Platform compliance detail was not read-only: {platform_detail}")
    for path in ["/diagnostics", "/requirements", "/checks", "/results", "/exceptions", "/snapshots"]:
        response = get(f"{platform_base}{path}", OWNER_HEADERS)
        if response.get("read_only") is not True:
            raise AssertionError(f"Platform compliance diagnostics endpoint not read-only: {path} {response}")
    request("POST", f"{platform_base}/evidence", {"governance_record_id": governance_record["id"]}, OWNER_HEADERS, 405)
    request("POST", f"{base}/evidence/{evidence['id']}/send", {}, OWNER_HEADERS, 404)

    after_outcome_signature = outcome_signature(get(f"/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/outcomes/{outcome['id']}", OWNER_HEADERS))
    if after_outcome_signature != before_outcome_signature:
        raise AssertionError(f"Compliance mutated delivery outcome counts/status: before={before_outcome_signature} after={after_outcome_signature}")
    after_signature = option_signature(get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace['id']}", OWNER_HEADERS), option_ids)
    if after_signature != before_signature:
        raise AssertionError("Compliance mutated offer option pricing/status.")

    readiness_after = get("/api/readiness")
    compliance_section = readiness_after.get("offer_decision_export_compliance_foundation") or {}
    for key in ["evidence_count", "requirement_count", "check_count", "result_count", "exception_count", "snapshot_count"]:
        if compliance_section.get(key, 0) < 1:
            raise AssertionError(f"Readiness compliance count did not increment for {key}: {compliance_section}")

    smoke_offer_decision_export_governance_foundation()
    print("Offer decision export compliance foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
