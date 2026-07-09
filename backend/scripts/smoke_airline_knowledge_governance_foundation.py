#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    AirlineKnowledgeRelease,
    AirlineKnowledgeReleaseCreate,
    AirlineKnowledgeVersion,
    AirlineKnowledgeVersionCreate,
)
from services.airline_knowledge_governance_service import (
    AIRLINE_KNOWLEDGE_RELEASE_COLLECTION,
    AIRLINE_KNOWLEDGE_VERSION_COLLECTION,
    APPROVAL_STATUSES,
    CHANGE_TYPES,
    KNOWLEDGE_LIFECYCLE_STATUSES,
    KNOWLEDGE_SCOPES,
    PHASE_LABEL,
    RELEASE_STATUSES,
    REVIEW_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_52_1_reference_data_engine_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-knowledge-governance"


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time())}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def disabled_flags() -> list[str]:
    return [
        "live_rule_evaluation_disabled",
        "ai_reasoning_disabled",
        "parser_execution_disabled",
        "recommendation_engine_disabled",
        "pricing_calculation_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "automatic_publication_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def version_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "knowledge_version_reference": reference,
        "version_number": 504,
        "version_label": "Phase 50.4 Smoke Knowledge Version",
        "semantic_version": "50.4.0-smoke",
        "lifecycle_status": "under_review",
        "submitted_for_review_at": "2028-04-01T09:00:00Z",
        "reviewed_at": "2028-04-02T09:00:00Z",
        "author": "Knowledge Author",
        "reviewer": "Knowledge Reviewer",
        "approver": "Knowledge Approver",
        "publisher": "Knowledge Publisher",
        "review_status": "under_review",
        "review_notes": "Review queue metadata only.",
        "requested_changes": ["Confirm effective date metadata."],
        "approval_status": "pending",
        "approval_notes": "Approval queue metadata only.",
        "publication_channel": "platform_console",
        "publication_scope": "agency_visibility",
        "publication_notes": "Publication metadata only; no automatic publication.",
        "knowledge_scope": ["evidence", "policy", "pricing", "capability", "operational_constraints", "operational_procedures"],
        "evidence_ids": ["EVID-SMOKE-001"],
        "policy_ids": ["POL-SMOKE-001"],
        "pricing_ids": ["PRICE-SMOKE-001"],
        "capability_ids": ["CAP-SMOKE-001"],
        "constraint_ids": ["OC-SMOKE-001"],
        "procedure_ids": ["PROC-SMOKE-001"],
        "previous_version_id": "AKV-PREVIOUS-SMOKE",
        "supersedes_version_ids": ["AKV-SUPERSEDED-SMOKE"],
        "change_type": "policy_update",
        "change_description": "Smoke governance record for policy, pricing, capability, constraints, and procedures.",
        "change_reason": "Regression coverage for Phase 50.4 metadata.",
        "added_objects": [{"object_type": "policy", "object_id": "POL-SMOKE-001"}],
        "modified_objects": [{"object_type": "constraint", "object_id": "OC-SMOKE-001"}],
        "removed_objects": [{"object_type": "procedure", "object_id": "PROC-OLD-SMOKE"}],
        "comparison_base_version_id": "AKV-PREVIOUS-SMOKE",
        "comparison_target_version_id": reference,
        "changed_effective_dates": [{"field": "effective_from", "from": "2028-03-01", "to": "2028-04-01"}],
        "changed_pricing": [{"pricing_id": "PRICE-SMOKE-001", "change": "metadata update"}],
        "changed_capability": [{"capability_id": "CAP-SMOKE-001", "change": "metadata update"}],
        "changed_operational_constraints": [{"constraint_id": "OC-SMOKE-001", "change": "metadata update"}],
        "changed_procedures": [{"procedure_id": "PROC-SMOKE-001", "change": "metadata update"}],
        "rollback_from_version_id": reference,
        "rollback_to_version_id": "AKV-PREVIOUS-SMOKE",
        "rollback_reason": "Rollback metadata only.",
        "rollback_notes": "No rollback execution.",
        "historical_lookup_tags": ["phase-50-4-smoke", "governance"],
        "internal_notes": "No live rule evaluation, AI reasoning, parser execution, recommendations, pricing calculation, provider calls, workers, or automatic publication.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def release_payload(agency_id: str, version_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "release_reference": reference,
        "release_name": "Phase 50.4 Smoke Release",
        "release_description": "Grouped airline operational knowledge release metadata.",
        "release_status": "under_review",
        "release_version": "50.4.0-smoke-release",
        "release_notes": "Release metadata only.",
        "included_version_ids": [version_id],
        "approved_at": "2028-04-03T10:00:00Z",
        "published_at": "2028-04-04T10:00:00Z",
        "airline_codes": ["LH", "AF"],
        "countries": ["DE", "FR"],
        "service_domains": ["animal_transport", "mobility_assistance"],
        "release_author": "Knowledge Author",
        "release_reviewer": "Knowledge Reviewer",
        "release_approver": "Knowledge Approver",
        "evaluation_ready": True,
        "recommendation_ready": True,
        "rollback_release_id": "AKR-ROLLBACK-SMOKE",
        "superseded_release_ids": ["AKR-SUPERSEDED-SMOKE"],
        "replaced_by_release_id": "AKR-REPLACEMENT-SMOKE",
        "historical_lookup_tags": ["phase-50-4-smoke", "release"],
        "internal_notes": "No live publication, recommendation engine, provider call, or worker.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    for collection in [AIRLINE_KNOWLEDGE_VERSION_COLLECTION, AIRLINE_KNOWLEDGE_RELEASE_COLLECTION]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"{collection} is not registered as agency-owned metadata.")

    version_create = AirlineKnowledgeVersionCreate(**version_payload("agency-smoke", "AKV-SMOKE-MODEL"))
    version_record = AirlineKnowledgeVersion(**version_create.model_dump(mode="json", exclude_none=True))
    if version_record.knowledge_scope != KNOWLEDGE_SCOPES:
        raise AssertionError("Knowledge version model did not preserve all knowledge scopes.")
    if version_record.lifecycle_status != "under_review" or version_record.approval_status != "pending":
        raise AssertionError("Knowledge version model did not preserve lifecycle governance metadata.")
    if not version_record.changed_pricing or not version_record.changed_operational_constraints:
        raise AssertionError("Knowledge version model did not preserve comparison metadata.")
    if version_record.metadata_only is not True or version_record.live_rule_evaluation_disabled is not True:
        raise AssertionError("Knowledge version model is not metadata-only.")

    release_create = AirlineKnowledgeReleaseCreate(**release_payload("agency-smoke", "AKV-SMOKE-MODEL", "AKR-SMOKE-MODEL"))
    release_record = AirlineKnowledgeRelease(**release_create.model_dump(mode="json", exclude_none=True))
    if release_record.included_version_ids != ["AKV-SMOKE-MODEL"]:
        raise AssertionError("Knowledge release model did not preserve included versions.")
    if release_record.evaluation_ready is not True or release_record.recommendation_ready is not True:
        raise AssertionError("Knowledge release model did not preserve future AOIE readiness metadata.")
    if release_record.metadata_only is not True or release_record.automatic_publication_disabled is not True:
        raise AssertionError("Knowledge release model is not metadata-only.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_knowledge_versions_id_unique",
        "airline_knowledge_versions_reference_unique",
        "airline_knowledge_versions_agency_lifecycle_lookup",
        "airline_knowledge_versions_review_status_lookup",
        "airline_knowledge_versions_approval_status_lookup",
        "airline_knowledge_versions_publication_lookup",
        "airline_knowledge_versions_scope_lookup",
        "airline_knowledge_versions_comparison_lookup",
        "airline_knowledge_versions_rollback_lookup",
        "airline_knowledge_releases_id_unique",
        "airline_knowledge_releases_reference_unique",
        "airline_knowledge_releases_agency_status_lookup",
        "airline_knowledge_releases_included_versions_lookup",
        "airline_knowledge_releases_future_aoie_lookup",
        "airline_knowledge_releases_rollback_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Airline knowledge governance index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    expected_methods = {
        "/api/platform/airline-knowledge-governance": {"get"},
        "/api/platform/airline-knowledge-governance/summary": {"get"},
        "/api/platform/airline-knowledge-governance/versions": {"get", "post"},
        "/api/platform/airline-knowledge-governance/versions/{version_id}": {"get", "put", "delete"},
        "/api/platform/airline-knowledge-governance/releases": {"get", "post"},
        "/api/platform/airline-knowledge-governance/releases/{release_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/airline-knowledge-governance": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-governance/summary": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-governance/versions": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-governance/versions/{version_id}": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-governance/releases": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-governance/releases/{release_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)

    for path in [
        "/api/agencies/{agency_id}/airline-knowledge-governance",
        "/api/agencies/{agency_id}/airline-knowledge-governance/summary",
        "/api/agencies/{agency_id}/airline-knowledge-governance/versions",
        "/api/agencies/{agency_id}/airline-knowledge-governance/versions/{version_id}",
        "/api/agencies/{agency_id}/airline-knowledge-governance/releases",
        "/api/agencies/{agency_id}/airline-knowledge-governance/releases/{release_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency governance route is not read-only: {path} {sorted(blocked_methods)}")

    for path in paths:
        if "airline-knowledge-governance" in path and any(term in path for term in ["evaluate", "execute", "score", "recommend", "calculate"]):
            raise AssertionError(f"Live governance execution route should not exist: {path}")
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/airline-knowledge-governance"),
        (ROOT / "frontend/src/App.jsx", "/platform/airline-knowledge-releases"),
        (ROOT / "frontend/src/App.jsx", "/agency/knowledge-governance"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge Governance"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge Releases"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Knowledge Versions"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Knowledge Releases"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Review Queue"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Approval Queue"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Publication Queue"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Historical Versions"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Version Comparison"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Superseded Knowledge"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx", "Archived Knowledge"),
        (ROOT / "frontend/src/pages/agency/KnowledgeGovernancePage.jsx", "Read-only lifecycle"),
        (ROOT / "docs/architecture/airline-operational-knowledge-governance-foundation.md", "Airline Operational Knowledge Governance"),
        (ROOT / "docs/architecture/airline-operational-knowledge-governance-foundation.md", "Phase 50.4"),
        (ROOT / "docs/architecture/airline-operational-knowledge-governance-foundation.md", "metadata-only"),
        (ROOT / "docs/architecture/current-model-inventory.md", "airline_knowledge_versions"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/airline-knowledge-governance"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Airline operational knowledge governance"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Airline Knowledge Governance"),
        (ROOT / "README.md", "Phase 50.4 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 50.4: Airline Operational Knowledge Governance & Version Control Foundation"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 50.4"),
    ]:
        require_text(path, text)

    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeGovernancePage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeGovernancePage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_no_forbidden_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/airline_knowledge_governance_service.py",
        ROOT / "backend/routers/platform_airline_knowledge_governance.py",
        ROOT / "backend/routers/agency_airline_knowledge_governance.py",
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeGovernancePage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeGovernancePage.jsx",
    ]
    forbidden_terms = [
        "BackgroundTasks",
        "httpx",
        "requests.",
        "urllib.",
        "openai",
        "AsyncClient",
        "Scheduler",
        "schedule.",
        "scrapy",
        "selenium",
        "BeautifulSoup",
        "crawl(",
        "scrape(",
        "evaluate_rules(",
        "run_evaluation(",
        "execute_parser(",
        "calculate_price(",
        "provider_client",
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden implementation term: {term}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE or PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_operational_knowledge_governance_foundation") or {}
    for flag in [
        "airline_operational_knowledge_governance_enabled",
        "airline_knowledge_versions_collection_enabled",
        "airline_knowledge_releases_collection_enabled",
        "knowledge_lifecycle_metadata_enabled",
        "independent_knowledge_versioning_enabled",
        "evidence_versioning_enabled",
        "policy_versioning_enabled",
        "pricing_versioning_enabled",
        "capability_versioning_enabled",
        "operational_constraint_versioning_enabled",
        "operational_procedure_versioning_enabled",
        "knowledge_release_metadata_enabled",
        "version_comparison_metadata_enabled",
        "rollback_metadata_enabled",
        "superseded_metadata_enabled",
        "historical_lookup_metadata_enabled",
        "review_queue_metadata_enabled",
        "approval_queue_metadata_enabled",
        "publication_queue_metadata_enabled",
        "platform_airline_knowledge_governance_metadata_crud_enabled",
        "agency_airline_knowledge_governance_read_only_enabled",
        "platform_airline_knowledge_governance_ui_enabled",
        "agency_knowledge_governance_ui_enabled",
        *disabled_flags(),
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Governance readiness missing flag {flag}: {section}")
    for count_key in [
        "airline_knowledge_version_count",
        "airline_knowledge_release_count",
        "airline_knowledge_version_lifecycle_counts",
        "airline_knowledge_version_review_counts",
        "airline_knowledge_version_approval_counts",
        "airline_knowledge_release_status_counts",
        "airline_knowledge_version_scope_counts",
        "airline_knowledge_version_change_type_counts",
        "airline_knowledge_review_queue_count",
        "airline_knowledge_approval_queue_count",
        "airline_knowledge_publication_queue_count",
        "airline_knowledge_historical_version_count",
        "airline_knowledge_superseded_version_count",
        "airline_knowledge_archived_version_count",
        "airline_knowledge_comparison_metadata_count",
        "airline_knowledge_rollback_metadata_count",
        "airline_knowledge_release_evaluation_ready_count",
        "airline_knowledge_release_recommendation_ready_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Governance readiness missing count: {count_key}")
    if section.get("knowledge_lifecycle_statuses") != KNOWLEDGE_LIFECYCLE_STATUSES:
        raise AssertionError("Governance readiness lifecycle statuses do not match service constants.")
    if section.get("knowledge_release_statuses") != RELEASE_STATUSES:
        raise AssertionError("Governance readiness release statuses do not match service constants.")
    if section.get("knowledge_review_statuses") != REVIEW_STATUSES:
        raise AssertionError("Governance readiness review statuses do not match service constants.")
    if section.get("knowledge_approval_statuses") != APPROVAL_STATUSES:
        raise AssertionError("Governance readiness approval statuses do not match service constants.")
    if section.get("knowledge_scopes") != KNOWLEDGE_SCOPES:
        raise AssertionError("Governance readiness scopes do not match service constants.")
    if section.get("knowledge_change_types") != CHANGE_TYPES:
        raise AssertionError("Governance readiness change types do not match service constants.")
    if section.get("readiness_required") is not False:
        raise AssertionError("Governance readiness should not be deployment-readiness required.")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Airline Knowledge Governance" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Airline Knowledge Governance category: {categories}")
    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    route_mappings = route_policy.get("route_mappings") or []
    if not any(item.get("agencyos") == "/platform/airline-knowledge-governance" for item in route_mappings):
        raise AssertionError("Route policy missing platform governance mapping.")
    if not any(item.get("agencyos") == "/agency/knowledge-governance" for item in route_mappings):
        raise AssertionError("Route policy missing agency governance mapping.")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Airline operational knowledge governance and version control foundation built in Phase 50.4" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gaps missing Phase 50.4 built marker: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")
    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not next_phases.get("items") or next_phases["items"][0].get("phase") != "Phase 50.9":
        raise AssertionError(f"Next recommendations did not start with Phase 50.9: {next_phases}")


def assert_version_shape(item: dict, agency_view: bool = False) -> None:
    required_fields = [
        "id",
        "agency_id",
        "knowledge_version_reference",
        "version_label",
        "semantic_version",
        "lifecycle_status",
        "review_status",
        "approval_status",
        "publication_channel",
        "publication_scope",
        "knowledge_scope",
        "evidence_ids",
        "policy_ids",
        "pricing_ids",
        "capability_ids",
        "constraint_ids",
        "procedure_ids",
        "previous_version_id",
        "supersedes_version_ids",
        "change_type",
        "added_objects",
        "modified_objects",
        "removed_objects",
        "version_comparison",
        "lifecycle_timeline",
        "governed_knowledge_summary",
        "rollback_to_version_id",
        "historical_lookup_tags",
    ]
    for field in required_fields:
        if field not in item:
            raise AssertionError(f"Knowledge version field missing {field}: {item}")
    if item.get("metadata_only") is not True:
        raise AssertionError(f"Knowledge version is not metadata-only: {item}")
    if not item.get("version_comparison", {}).get("changed_pricing"):
        raise AssertionError(f"Knowledge version missing comparison pricing metadata: {item}")
    if item.get("governed_knowledge_summary", {}).get("evidence") != 1:
        raise AssertionError(f"Knowledge version summary missing evidence count: {item}")
    if agency_view and item.get("read_only") is not True:
        raise AssertionError(f"Agency knowledge version should be read-only: {item}")


def assert_release_shape(item: dict, agency_view: bool = False) -> None:
    required_fields = [
        "id",
        "agency_id",
        "release_reference",
        "release_name",
        "release_status",
        "release_version",
        "release_notes",
        "included_version_ids",
        "included_version_count",
        "airline_codes",
        "countries",
        "service_domains",
        "release_author",
        "release_reviewer",
        "release_approver",
        "evaluation_ready",
        "recommendation_ready",
        "rollback_release_id",
        "superseded_release_ids",
        "historical_lookup_tags",
    ]
    for field in required_fields:
        if field not in item:
            raise AssertionError(f"Knowledge release field missing {field}: {item}")
    if item.get("metadata_only") is not True:
        raise AssertionError(f"Knowledge release is not metadata-only: {item}")
    if item.get("included_version_count") != len(item.get("included_version_ids") or []):
        raise AssertionError(f"Knowledge release included version count mismatch: {item}")
    if agency_view and item.get("read_only") is not True:
        raise AssertionError(f"Agency knowledge release should be read-only: {item}")


def assert_summary_shape(payload: dict, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary did not preserve agency id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "version_count",
        "release_count",
        "by_lifecycle_status",
        "by_review_status",
        "by_approval_status",
        "by_release_status",
        "by_knowledge_scope",
        "by_change_type",
        "review_queue_count",
        "approval_queue_count",
        "publication_queue_count",
        "historical_version_count",
        "version_comparison_count",
        "rollback_metadata_count",
        "release_evaluation_ready_count",
        "release_recommendation_ready_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Governance summary missing {key}: {payload}")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    version_reference = run_ref("AKV-SMOKE")
    release_reference = run_ref("AKR-SMOKE")

    created_version_response = post(f"{PLATFORM_BASE}/versions", version_payload(agency_id, version_reference), OWNER_HEADERS, 201)
    assert_disabled_response(created_version_response)
    version = created_version_response.get("airline_knowledge_version") or {}
    assert_version_shape(version)
    version_id = version.get("id")
    if not version_id:
        raise AssertionError(f"Knowledge version id missing: {created_version_response}")

    updated_version_response = put(
        f"{PLATFORM_BASE}/versions/{version_id}",
        {
            "lifecycle_status": "effective",
            "review_status": "reviewed",
            "approval_status": "approved",
            "approved_at": "2028-04-05T10:00:00Z",
            "published_at": "2028-04-06T10:00:00Z",
            "effective_from": "2028-04-07T00:00:00Z",
            "effective_until": "2029-04-07T00:00:00Z",
            "review_notes": "Reviewed metadata only.",
            "approval_notes": "Approved metadata only.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated_version_response)
    version = updated_version_response.get("airline_knowledge_version") or {}
    assert_version_shape(version)
    if version.get("lifecycle_status") != "effective" or version.get("approval_status") != "approved":
        raise AssertionError(f"Knowledge version update did not persist governance metadata: {updated_version_response}")

    for filter_query in [
        f"agency_id={agency_id}",
        "lifecycle_status=effective",
        "review_status=reviewed",
        "approval_status=approved",
        "publication_channel=platform_console",
        "publication_scope=agency_visibility",
        "knowledge_scope=policy",
        "change_type=policy_update",
    ]:
        filtered = get(f"{PLATFORM_BASE}/versions?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == version_id for item in filtered.get("versions") or []):
            raise AssertionError(f"Knowledge version filter {filter_query} missing created record: {filtered}")

    created_release_response = post(f"{PLATFORM_BASE}/releases", release_payload(agency_id, version_id, release_reference), OWNER_HEADERS, 201)
    assert_disabled_response(created_release_response)
    release = created_release_response.get("airline_knowledge_release") or {}
    assert_release_shape(release)
    release_id = release.get("id")
    if not release_id:
        raise AssertionError(f"Knowledge release id missing: {created_release_response}")

    updated_release_response = put(
        f"{PLATFORM_BASE}/releases/{release_id}",
        {
            "release_status": "published",
            "release_notes": "Published metadata only; no automatic publication.",
            "evaluation_ready": True,
            "recommendation_ready": True,
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated_release_response)
    release = updated_release_response.get("airline_knowledge_release") or {}
    assert_release_shape(release)
    if release.get("release_status") != "published":
        raise AssertionError(f"Knowledge release update did not persist release metadata: {updated_release_response}")

    for filter_query in [
        f"agency_id={agency_id}",
        "release_status=published",
        "airline_code=LH",
        "country=DE",
        "service_domain=animal_transport",
    ]:
        filtered = get(f"{PLATFORM_BASE}/releases?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == release_id for item in filtered.get("releases") or []):
            raise AssertionError(f"Knowledge release filter {filter_query} missing created record: {filtered}")

    platform_response = get(
        f"{PLATFORM_BASE}?agency_id={agency_id}&lifecycle_status=effective&release_status=published&knowledge_scope=policy&airline_code=LH",
        OWNER_HEADERS,
    )
    assert_disabled_response(platform_response)
    assert_summary_shape(platform_response)
    if not any(item.get("id") == version_id for item in platform_response.get("versions") or []):
        raise AssertionError(f"Platform governance response missing created version: {platform_response}")
    if not any(item.get("id") == release_id for item in platform_response.get("releases") or []):
        raise AssertionError(f"Platform governance response missing created release: {platform_response}")

    platform_summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)
    platform_version_detail = get(f"{PLATFORM_BASE}/versions/{version_id}", OWNER_HEADERS)
    assert_disabled_response(platform_version_detail)
    assert_version_shape(platform_version_detail.get("airline_knowledge_version") or {})
    platform_release_detail = get(f"{PLATFORM_BASE}/releases/{release_id}", OWNER_HEADERS)
    assert_disabled_response(platform_release_detail)
    assert_release_shape(platform_release_detail.get("airline_knowledge_release") or {})

    agency_response = get(
        f"/api/agencies/{agency_id}/airline-knowledge-governance?lifecycle_status=effective&release_status=published&knowledge_scope=policy&airline_code=LH",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_response)
    if agency_response.get("read_only") is not True:
        raise AssertionError(f"Agency governance response should be read-only: {agency_response}")
    agency_version = next((item for item in agency_response.get("versions") or [] if item.get("id") == version_id), None)
    agency_release = next((item for item in agency_response.get("releases") or [] if item.get("id") == release_id), None)
    if not agency_version or not agency_release:
        raise AssertionError(f"Agency governance response missing created metadata: {agency_response}")
    assert_version_shape(agency_version, agency_view=True)
    assert_release_shape(agency_release, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/airline-knowledge-governance/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency governance summary should be read-only: {agency_summary}")
    agency_versions = get(f"/api/agencies/{agency_id}/airline-knowledge-governance/versions?knowledge_scope=policy", OWNER_HEADERS)
    assert_disabled_response(agency_versions)
    if not any(item.get("id") == version_id for item in agency_versions.get("versions") or []):
        raise AssertionError(f"Agency versions response missing created version: {agency_versions}")
    agency_releases = get(f"/api/agencies/{agency_id}/airline-knowledge-governance/releases?airline_code=LH", OWNER_HEADERS)
    assert_disabled_response(agency_releases)
    if not any(item.get("id") == release_id for item in agency_releases.get("releases") or []):
        raise AssertionError(f"Agency releases response missing created release: {agency_releases}")
    agency_version_detail = get(f"/api/agencies/{agency_id}/airline-knowledge-governance/versions/{version_id}", OWNER_HEADERS)
    assert_disabled_response(agency_version_detail)
    assert_version_shape(agency_version_detail.get("airline_knowledge_version") or {}, agency_view=True)
    agency_release_detail = get(f"/api/agencies/{agency_id}/airline-knowledge-governance/releases/{release_id}", OWNER_HEADERS)
    assert_disabled_response(agency_release_detail)
    assert_release_shape(agency_release_detail.get("airline_knowledge_release") or {}, agency_view=True)

    request("POST", f"/api/agencies/{agency_id}/airline-knowledge-governance/versions", version_payload(agency_id, run_ref("AKV-AGENCY-FORBIDDEN")), OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/airline-knowledge-governance/versions/{version_id}", {"review_status": "rejected"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/airline-knowledge-governance/versions/{version_id}", {}, OWNER_HEADERS, 405)
    request("POST", f"/api/agencies/{agency_id}/airline-knowledge-governance/releases", release_payload(agency_id, version_id, run_ref("AKR-AGENCY-FORBIDDEN")), OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/airline-knowledge-governance/releases/{release_id}", {"release_status": "archived"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/airline-knowledge-governance/releases/{release_id}", {}, OWNER_HEADERS, 405)

    archived_version = request("DELETE", f"{PLATFORM_BASE}/versions/{version_id}", None, OWNER_HEADERS)[1]
    assert_disabled_response(archived_version)
    if archived_version.get("archived") is not True or archived_version.get("physical_delete_disabled") is not True:
        raise AssertionError(f"Platform version archive did not return soft archive markers: {archived_version}")
    archived_release = request("DELETE", f"{PLATFORM_BASE}/releases/{release_id}", None, OWNER_HEADERS)[1]
    assert_disabled_response(archived_release)
    if archived_release.get("archived") is not True or archived_release.get("physical_delete_disabled") is not True:
        raise AssertionError(f"Platform release archive did not return soft archive markers: {archived_release}")


def main() -> None:
    verify_model_and_collection_registration()
    paths = get("/openapi.json").get("paths", {})
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_no_forbidden_implementation()
    verify_readiness()
    verify_blueprint_adoption()
    verify_endpoint_behavior()
    print("Phase 50.4 airline operational knowledge governance foundation smoke passed.")


if __name__ == "__main__":
    main()
