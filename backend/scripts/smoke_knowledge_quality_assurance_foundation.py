#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import KnowledgeQualityAssuranceReview, KnowledgeQualityAssuranceReviewCreate
from services.knowledge_quality_assurance_service import (
    APPROVAL_RECOMMENDATIONS,
    KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION,
    PHASE_LABEL,
    QA_CHECKS,
    QA_STATUSES,
    SEVERITY_LEVELS,
    TARGET_TYPES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]

REQUIRED_CHECKS = {
    "missing_evidence",
    "missing_effective_dates",
    "missing_pricing_applicability",
    "conflicting_support_status",
    "incomplete_service_parameters",
    "missing_documents",
    "unsupported_reference_values",
    "stale_review",
    "low_confidence",
    "operational_validation_pending",
    "duplicate_policy_card",
    "conflicting_rule",
    "incomplete_pricing_formula",
}


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "knowledge_quality_assurance_foundation",
        "auto_approval_disabled",
        "publishing_disabled",
        "rule_execution_disabled",
        "ai_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def review_payload(agency_id: str, reference: str, target_type: str = "visual_policy_card") -> dict:
    service_code = "PETC" if target_type != "operational_rule" else "WCHR"
    service_family = "pets_animals" if service_code == "PETC" else "passenger_assistance"
    return {
        "agency_id": agency_id,
        "review_reference": reference,
        "target_type": target_type,
        "target_id": f"{target_type.upper()}-SMOKE-526",
        "airline_code": "LH",
        "service_family": service_family,
        "service_code": service_code,
        "qa_status": "changes_requested",
        "issues": [
            {"check": "missing_evidence", "severity": "high", "message": "Evidence link is required before release."},
            {"check": "missing_effective_dates", "severity": "medium", "message": "Effective date range is incomplete."},
            {"check": "conflicting_rule" if target_type != "operational_rule" else "incomplete_service_parameters", "severity": "high"},
        ],
        "severity": "high",
        "reviewer": {"name": "Phase 52.6 QA Reviewer", "role": "platform_knowledge_editor"},
        "requested_changes": [
            {"field": "evidence_links", "change": "Add approved source evidence."},
            {"field": "effective_dates", "change": "Record effective_from and effective_to."},
        ],
        "approval_recommendation": "hold",
        "governance_links": ["KGV-SMOKE-526"],
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("knowledge_quality_assurance_reviews is not registered as agency-owned metadata.")
    if REQUIRED_CHECKS - set(QA_CHECKS):
        raise AssertionError(f"QA checks missing: {sorted(REQUIRED_CHECKS - set(QA_CHECKS))}")
    if "visual_policy_card" not in TARGET_TYPES or "operational_rule" not in TARGET_TYPES:
        raise AssertionError("Target type metadata is incomplete.")
    if "changes_requested" not in QA_STATUSES or "archived" not in QA_STATUSES:
        raise AssertionError("QA status metadata is incomplete.")
    if "high" not in SEVERITY_LEVELS or "blocking" not in SEVERITY_LEVELS:
        raise AssertionError("Severity metadata is incomplete.")
    if "hold" not in APPROVAL_RECOMMENDATIONS or "ready_for_human_approval" not in APPROVAL_RECOMMENDATIONS:
        raise AssertionError("Approval recommendation metadata is incomplete.")

    create = KnowledgeQualityAssuranceReviewCreate(**review_payload("agency-smoke", "KQA-SMOKE-MODEL"))
    record = KnowledgeQualityAssuranceReview(**create.model_dump(mode="json", exclude_none=True))
    if record.review_reference != "KQA-SMOKE-MODEL" or not record.issues or not record.requested_changes:
        raise AssertionError("KnowledgeQualityAssuranceReview model did not preserve QA metadata.")
    if record.knowledge_quality_assurance_foundation is not True or record.auto_approval_disabled is not True:
        raise AssertionError("KnowledgeQualityAssuranceReview model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION,
        "knowledge_quality_assurance_reviews_reference_unique",
        "knowledge_quality_assurance_reviews_agency_target_lookup",
        "knowledge_quality_assurance_reviews_target_lookup",
        "knowledge_quality_assurance_reviews_airline_lookup",
        "knowledge_quality_assurance_reviews_service_family_lookup",
        "knowledge_quality_assurance_reviews_service_code_lookup",
        "knowledge_quality_assurance_reviews_status_lookup",
        "knowledge_quality_assurance_reviews_severity_lookup",
        "knowledge_quality_assurance_reviews_issue_check_lookup",
        "knowledge_quality_assurance_reviews_approval_recommendation_lookup",
        "knowledge_quality_assurance_reviews_governance_lookup",
        "knowledge_quality_assurance_reviews_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/knowledge-quality-assurance", "get"),
        ("/api/platform/knowledge-quality-assurance", "post"),
        ("/api/platform/knowledge-quality-assurance/summary", "get"),
        ("/api/platform/knowledge-quality-assurance/{review_id}", "get"),
        ("/api/platform/knowledge-quality-assurance/{review_id}", "put"),
        ("/api/platform/knowledge-quality-assurance/{review_id}", "delete"),
        ("/api/agencies/{agency_id}/knowledge-quality-assurance", "get"),
        ("/api/agencies/{agency_id}/knowledge-quality-assurance", "post"),
        ("/api/agencies/{agency_id}/knowledge-quality-assurance/summary", "get"),
        ("/api/agencies/{agency_id}/knowledge-quality-assurance/{review_id}", "get"),
        ("/api/agencies/{agency_id}/knowledge-quality-assurance/{review_id}", "put"),
        ("/api/agencies/{agency_id}/knowledge-quality-assurance/{review_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith("/api/admin") or path.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/knowledge-quality-assurance"),
        (ROOT / "frontend/src/App.jsx", "/agency/knowledge-quality-assurance"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge QA"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "knowledge_quality_assurance"),
        (ROOT / "frontend/src/pages/platform/KnowledgeQualityAssurancePage.jsx", "Requested Changes"),
        (ROOT / "frontend/src/pages/agency/KnowledgeQualityAssurancePage.jsx", "Reviewer / Recommendation"),
        (ROOT / "backend/services/saas_subscription_service.py", "knowledge_quality_assurance"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Knowledge Quality Assurance"),
        (ROOT / "docs/architecture/knowledge-quality-assurance-foundation.md", "Phase 52.6"),
        (ROOT / "docs/architecture/current-model-inventory.md", "knowledge_quality_assurance_reviews"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/knowledge-quality-assurance"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Knowledge Quality Assurance"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Knowledge quality assurance"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "knowledge_quality_assurance_reviews"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Knowledge Quality Assurance Alignment"),
        (ROOT / "docs/architecture/reference-data-engine-foundation.md", "Knowledge Quality Assurance Relationship"),
        (ROOT / "docs/architecture/knowledge-import-templates-foundation.md", "knowledge_quality_assurance_reviews"),
        (ROOT / "docs/architecture/visual-policy-editor-foundation.md", "Knowledge QA"),
        (ROOT / "docs/architecture/pricing-formula-builder-foundation.md", "Knowledge Quality Assurance"),
        (ROOT / "docs/architecture/operational-rule-composer-foundation.md", "Knowledge Quality Assurance"),
        (ROOT / "docs/architecture/intelligent-offer-builder-integration-foundation.md", "Phase 52.6 Knowledge Quality Assurance"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.6"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Phase 52.6"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Knowledge Quality Assurance"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.6"),
        (ROOT / "README.md", "knowledge QA review records"),
    ]:
        require_text(path, text)


def verify_crud_and_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]

    platform_reference = run_ref("KQA-SMOKE-PLATFORM")
    created = post(
        "/api/platform/knowledge-quality-assurance",
        review_payload(agency_id, platform_reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    platform_review = created["knowledge_quality_assurance_review"]
    assert_safety_flags(platform_review)
    if platform_review.get("target_type") != "visual_policy_card" or len(platform_review.get("issues") or []) < 2:
        raise AssertionError("Platform QA review did not preserve issue metadata.")
    if platform_review.get("issues_section", {}).get("issue_count") < 2:
        raise AssertionError("Platform QA projection did not expose issue section.")

    listed = get(
        "/api/platform/knowledge-quality-assurance?target_type=visual_policy_card&airline_code=LH&service_code=PETC&qa_status=changes_requested&issue_check=missing_evidence&approval_recommendation=hold&search=evidence",
        OWNER_HEADERS,
    )
    if not any(item.get("review_reference") == platform_reference for item in listed.get("items", [])):
        raise AssertionError("Platform filtered list did not include created QA review.")
    summary = get("/api/platform/knowledge-quality-assurance/summary", OWNER_HEADERS)
    if summary.get("summary", {}).get("issue_count", 0) < 1:
        raise AssertionError("Platform summary did not count QA issues.")

    updated = put(
        f"/api/platform/knowledge-quality-assurance/{platform_review['id']}",
        {
            "qa_status": "in_review",
            "severity": "critical",
            "approval_recommendation": "ready_for_human_approval",
            "requested_changes": platform_review["requested_changes"] + [{"field": "support_status", "change": "Resolve conflicting support status."}],
        },
        OWNER_HEADERS,
    )["knowledge_quality_assurance_review"]
    if updated.get("qa_status") != "in_review" or updated.get("severity") != "critical":
        raise AssertionError("Platform update did not persist status and severity metadata.")
    if updated.get("approval_recommendation") != "ready_for_human_approval":
        raise AssertionError("Platform update did not persist approval recommendation metadata.")

    agency_reference = run_ref("KQA-SMOKE-AGENCY")
    agency_created = post(
        f"/api/agencies/{agency_id}/knowledge-quality-assurance",
        review_payload(agency_id, agency_reference, target_type="operational_rule"),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(agency_created)
    agency_review = agency_created["knowledge_quality_assurance_review"]
    if agency_review.get("agency_id") != agency_id or agency_review.get("target_type") != "operational_rule":
        raise AssertionError("Agency QA review did not preserve agency scope.")

    agency_list = get(
        f"/api/agencies/{agency_id}/knowledge-quality-assurance?target_type=operational_rule&service_code=WCHR&issue_check=incomplete_service_parameters",
        OWNER_HEADERS,
    )
    if not any(item.get("review_reference") == agency_reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency filtered list did not include created QA review.")

    agency_updated = put(
        f"/api/agencies/{agency_id}/knowledge-quality-assurance/{agency_review['id']}",
        {
            "qa_status": "blocked",
            "governance_links": ["KGV-SMOKE-526", "KGV-WCHR-SMOKE-526"],
            "requested_changes": [{"field": "parameter_taxonomy_links", "change": "Add missing WCHR parameter reference."}],
        },
        OWNER_HEADERS,
    )["knowledge_quality_assurance_review"]
    if agency_updated.get("qa_status") != "blocked" or len(agency_updated.get("governance_links") or []) < 2:
        raise AssertionError("Agency update did not persist QA governance metadata.")

    archived = request(
        "DELETE",
        f"/api/agencies/{agency_id}/knowledge-quality-assurance/{agency_review['id']}",
        headers=OWNER_HEADERS,
        expect=200,
    )[1]["knowledge_quality_assurance_review"]
    if archived.get("qa_status") != "archived" or archived.get("archived") is not True:
        raise AssertionError("Agency archive did not persist archived metadata.")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("knowledge_quality_assurance_foundation") or {}
    for flag in [
        "knowledge_quality_assurance_enabled",
        "knowledge_quality_assurance_reviews_collection_enabled",
        "platform_knowledge_quality_assurance_metadata_crud_enabled",
        "agency_knowledge_quality_assurance_metadata_crud_enabled",
        "platform_knowledge_qa_ui_enabled",
        "agency_knowledge_qa_ui_enabled",
        "qa_review_layer_enabled",
        "qa_checks_metadata_enabled",
        "issues_metadata_enabled",
        "reviewer_metadata_enabled",
        "requested_changes_metadata_enabled",
        "approval_recommendation_metadata_enabled",
        "governance_links_metadata_enabled",
        "target_metadata_enabled",
        "airline_service_metadata_enabled",
        "qa_status_metadata_enabled",
        "severity_metadata_enabled",
        "metadata_only",
        "auto_approval_disabled",
        "publishing_disabled",
        "rule_execution_disabled",
        "ai_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if set(section.get("qa_checks") or []) != set(QA_CHECKS):
        raise AssertionError("Readiness did not expose supported QA checks.")
    if section.get("knowledge_quality_assurance_issue_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted QA issues.")
    if section.get("knowledge_quality_assurance_requested_change_count", 0) < 1:
        raise AssertionError("Readiness did not count requested changes.")
    if section.get("knowledge_quality_assurance_governance_link_count", 0) < 1:
        raise AssertionError("Readiness did not count governance links.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "knowledge-quality-assurance" in lowered:
            for marker in ["auto-approve", "publish", "execute", "evaluate", "ai-generate", "background-worker"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden Knowledge QA execution route registered: {path}")

    for path in [
        ROOT / "backend/services/knowledge_quality_assurance_service.py",
        ROOT / "backend/routers/platform_knowledge_quality_assurance.py",
        ROOT / "backend/routers/agency_knowledge_quality_assurance.py",
        ROOT / "frontend/src/pages/platform/KnowledgeQualityAssurancePage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeQualityAssurancePage.jsx",
    ]:
        for marker in [
            "import requests",
            "import httpx",
            "from openai",
            "import openai",
            "BackgroundTasks",
            "asyncio.create_task(",
            "def auto_approve",
            "def approve_and_publish",
            "def publish",
            "def execute_rule",
            "def evaluate_rule",
            "auto_approval_enabled",
            "publishing_enabled",
            "provider_client =",
            "@router.post(\"/api/platform/knowledge-quality-assurance/approve",
            "@router.post(\"/api/platform/knowledge-quality-assurance/publish",
            "@router.post(\"/api/agencies/{agency_id}/knowledge-quality-assurance/approve",
            "@router.post(\"/api/agencies/{agency_id}/knowledge-quality-assurance/publish",
            "@router.get(\"/admin",
            "@router.post(\"/admin",
            "\"/api/admin",
        ]:
            reject_text(path, marker)


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_crud_and_readiness()
    verify_boundaries()
    print("Knowledge quality assurance foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Knowledge quality assurance foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
