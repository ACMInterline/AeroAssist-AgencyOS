#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import OperationalConstraint, OperationalConstraintCreate
from services.operational_constraint_engine_service import (
    APPROVAL_STATUSES,
    CONDITION_OPERATORS,
    CONSTRAINT_STATUSES,
    OPERATIONAL_CONSTRAINT_COLLECTION,
    OUTCOME_TYPES,
    REVIEW_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_2_agent_work_queue_assignment_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/operational-constraints"


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
        "live_rule_execution_disabled",
        "ai_reasoning_disabled",
        "recommendation_engine_disabled",
        "feasibility_scoring_disabled",
        "pricing_calculation_disabled",
        "parser_execution_disabled",
        "scraping_disabled",
        "background_workers_disabled",
        "provider_integrations_disabled",
        "evaluation_endpoint_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def constraint_payload(agency_id: str, reference: str = "OC-SMOKE-001") -> dict:
    return {
        "agency_id": agency_id,
        "constraint_reference": reference,
        "constraint_status": "captured",
        "constraint_version": "1.0",
        "constraint_name": "Bird transport to Qatar during exhibition season",
        "constraint_description": "Metadata-only conditional operational constraint for future AOIE reasoning.",
        "acquisition_id": "AKA-SMOKE-001",
        "airline_code": "LH",
        "service_domain": "animal_transport",
        "service_family": "pet_transport",
        "service_variant": "bird_transport",
        "ssr_code": "PETC",
        "rfic": "C",
        "rfisc": "0BT",
        "condition_logic": "all",
        "condition_groups": [
            {
                "group_reference": "group-destination-season",
                "group_name": "Destination and event season",
                "group_logic": "all",
                "conditions": [
                    {
                        "condition_field": "species",
                        "condition_operator": "equals",
                        "condition_value": "Bird",
                        "condition_value_type": "string",
                        "condition_scope": "animal_transport",
                        "condition_notes": "Species metadata only.",
                    },
                    {
                        "condition_field": "destination_country",
                        "condition_operator": "equals",
                        "condition_value": "Qatar",
                        "condition_value_type": "string",
                        "condition_scope": "route",
                    },
                    {
                        "condition_field": "season",
                        "condition_operator": "equals",
                        "condition_value": "Bird Exhibition",
                        "condition_value_type": "string",
                        "condition_scope": "seasonal",
                    },
                ],
                "group_notes": "Condition group persists without evaluation.",
            }
        ],
        "conditions": [
            {
                "condition_field": "temperature",
                "condition_operator": "greater_than",
                "condition_value": 29,
                "condition_value_type": "number",
                "condition_unit": "C",
                "condition_scope": "weather_metadata",
                "condition_notes": "Stored for future evaluation only.",
            }
        ],
        "outcome_type": "manual_review_required",
        "outcome_value": "service_allowed_pending_review",
        "outcome_severity": "warning",
        "outcome_reason": "Bird transport may depend on destination and event season.",
        "outcome_notes": "No decision is executed in Phase 50.2.",
        "airline_applicability": ["LH"],
        "route_applicability": ["FRA-DOH"],
        "origin_country_applicability": ["DE"],
        "destination_country_applicability": ["QA"],
        "airport_applicability": ["FRA", "DOH"],
        "aircraft_applicability": ["A350"],
        "cabin_applicability": ["economy"],
        "passenger_type_applicability": ["adult"],
        "species_applicability": ["Bird"],
        "breed_applicability": ["Falcon"],
        "seasonal_applicability": ["Bird Exhibition"],
        "date_range_applicability": "2028-01-01/2028-02-01",
        "constraint_priority": "high",
        "conflict_resolution_hint": "manual_review_wins",
        "precedence_group": "animal_transport_destination_rules",
        "evidence_reference_ids": ["AKA-SMOKE-001"],
        "review_status": "in_review",
        "approval_status": "pending",
        "reviewer": "Constraint Reviewer",
        "review_notes": "Governance metadata only.",
        "evaluation_ready": True,
        "evaluation_notes": "Ready metadata does not execute evaluation.",
        "future_engine_compatibility": "aoie_constraint_language_v1",
        "ssr_osi_workspace_ids": ["ssr-osi-smoke"],
        "emd_workspace_ids": ["emd-smoke"],
        "document_workspace_ids": ["document-smoke"],
        "workflow_ids": ["workflow-smoke"],
        "timeline_ids": ["timeline-smoke"],
        "internal_notes": "Metadata-only operational constraint.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if OPERATIONAL_CONSTRAINT_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Operational constraints collection is not registered as agency-owned metadata.")
    create_payload = OperationalConstraintCreate(**constraint_payload("agency-smoke", "OC-SMOKE-MODEL"))
    record = OperationalConstraint(**create_payload.model_dump(mode="json", exclude_none=True))
    if not record.condition_groups or record.condition_groups[0].conditions[0].condition_operator != "equals":
        raise AssertionError("Operational constraint model did not preserve condition groups/operators.")
    if not record.conditions or record.conditions[0].condition_operator != "greater_than":
        raise AssertionError("Operational constraint model did not preserve direct condition operators.")
    if record.outcome_type != "manual_review_required":
        raise AssertionError("Operational constraint model did not preserve outcome metadata.")
    if record.destination_country_applicability != ["QA"] or record.evidence_reference_ids != ["AKA-SMOKE-001"]:
        raise AssertionError("Operational constraint model did not preserve applicability/governance metadata.")
    if record.metadata_only is not True or record.live_rule_execution_disabled is not True:
        raise AssertionError("Operational constraint model is not metadata-only.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "operational_constraints_id_unique",
        "operational_constraints_reference_unique",
        "operational_constraints_agency_status_lookup",
        "operational_constraints_agency_airline_lookup",
        "operational_constraints_acquisition_lookup",
        "operational_constraints_service_classification_lookup",
        "operational_constraints_ssr_code_lookup",
        "operational_constraints_rfic_rfisc_lookup",
        "operational_constraints_outcome_type_lookup",
        "operational_constraints_review_status_lookup",
        "operational_constraints_approval_status_lookup",
        "operational_constraints_evaluation_ready_lookup",
        "operational_constraints_evidence_reference_lookup",
        "operational_constraints_ssr_osi_workspace_lookup",
        "operational_constraints_emd_workspace_lookup",
        "operational_constraints_document_workspace_lookup",
        "operational_constraints_workflow_lookup",
        "operational_constraints_timeline_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Operational constraint index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    expected_methods = {
        "/api/platform/operational-constraints": {"get", "post"},
        "/api/platform/operational-constraints/summary": {"get"},
        "/api/platform/operational-constraints/{constraint_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/operational-constraints": {"get"},
        "/api/agencies/{agency_id}/operational-constraints/summary": {"get"},
        "/api/agencies/{agency_id}/operational-constraints/{constraint_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/operational-constraints",
        "/api/agencies/{agency_id}/operational-constraints/summary",
        "/api/agencies/{agency_id}/operational-constraints/{constraint_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency operational constraint route is not read-only: {path} {sorted(blocked_methods)}")
    for path in paths:
        if "operational-constraints" in path and any(term in path for term in ["evaluate", "evaluation", "execute", "score", "recommend"]):
            raise AssertionError(f"Live evaluation route should not exist: {path}")
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/operational-constraints"),
        (ROOT / "frontend/src/App.jsx", "/agency/operational-constraints"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Constraints"),
        (ROOT / "frontend/src/pages/platform/OperationalConstraintsPage.jsx", "Constraint Overview"),
        (ROOT / "frontend/src/pages/platform/OperationalConstraintsPage.jsx", "No live evaluation"),
        (ROOT / "frontend/src/pages/agency/OperationalConstraintsPage.jsx", "Read-only AOIE constraint language metadata"),
        (ROOT / "docs/architecture/operational-constraint-engine-foundation.md", "Operational Constraint Engine Foundation"),
        (ROOT / "docs/architecture/operational-constraint-engine-foundation.md", "There is no evaluation route."),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Phase 50.2 adds the `operational_constraints` collection"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "50.2 Operational Constraint Engine"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Phase 50.2 adds the metadata-only Operational Constraint Engine language"),
        (ROOT / "BUILD_PHASES.md", "Phase 50.2: Operational Constraint Engine Foundation"),
        (ROOT / "README.md", "Phase 50.2 Includes"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_constraints"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/operational-constraints"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operational constraint engine"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operational Constraint Engine"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/OperationalConstraintsPage.jsx",
        ROOT / "frontend/src/pages/agency/OperationalConstraintsPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/OperationalConstraintsPage.jsx",
        ROOT / "frontend/src/pages/agency/OperationalConstraintsPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Operational Constraint Engine" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Operational Constraint Engine category: {categories}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Operational constraint engine foundation built in Phase 50.2" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gaps missing Phase 50.2 built marker: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("operational_constraint_engine_foundation") or {}
    for flag in [
        "operational_constraint_engine_enabled",
        "operational_constraints_collection_enabled",
        "constraint_language_foundation_enabled",
        "condition_groups_metadata_enabled",
        "conditions_metadata_enabled",
        "outcome_metadata_enabled",
        "applicability_metadata_enabled",
        "priority_precedence_metadata_enabled",
        "governance_metadata_enabled",
        "future_evaluation_metadata_enabled",
        "operational_links_metadata_enabled",
        "platform_operational_constraints_metadata_crud_enabled",
        "agency_operational_constraints_read_only_enabled",
        "platform_operational_constraints_ui_enabled",
        "agency_operational_constraints_ui_enabled",
        "metadata_only",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Operational constraint readiness missing flag {flag}: {section}")
    for flag in disabled_flags():
        if section.get(flag) is not True:
            raise AssertionError(f"Operational constraint readiness missing disabled flag {flag}: {section}")
    if section.get("supported_condition_operators") != CONDITION_OPERATORS:
        raise AssertionError(f"Readiness missing supported operators: {section}")
    for count_key in [
        "operational_constraint_count",
        "operational_constraint_status_counts",
        "operational_constraint_outcome_type_counts",
        "operational_constraint_review_status_counts",
        "operational_constraint_approval_status_counts",
        "operational_constraint_condition_count",
        "operational_constraint_condition_group_count",
        "operational_constraint_evidence_link_count",
        "operational_constraint_operational_link_count",
        "operational_constraint_evaluation_ready_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Operational constraint readiness missing count: {count_key}")
    if not set(CONSTRAINT_STATUSES).issubset(set((section.get("operational_constraint_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing constraint statuses: {section}")
    if not set(OUTCOME_TYPES).issubset(set((section.get("operational_constraint_outcome_type_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing outcome types: {section}")
    if not set(REVIEW_STATUSES).issubset(set((section.get("operational_constraint_review_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing review statuses: {section}")
    if not set(APPROVAL_STATUSES).issubset(set((section.get("operational_constraint_approval_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing approval statuses: {section}")


def verify_no_forbidden_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/operational_constraint_engine_service.py",
        ROOT / "backend/routers/platform_operational_constraints.py",
        ROOT / "backend/routers/agency_operational_constraints.py",
        ROOT / "frontend/src/pages/platform/OperationalConstraintsPage.jsx",
        ROOT / "frontend/src/pages/agency/OperationalConstraintsPage.jsx",
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
        "parse_policy(",
        "extract_policy(",
        "score_feasibility(",
        "calculate_price(",
        "execute_constraint(",
        "evaluate_constraint(",
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden implementation term: {term}")


def assert_constraint_shape(item: dict, agency_view: bool = False) -> None:
    required_fields = [
        "id",
        "agency_id",
        "constraint_reference",
        "constraint_status",
        "constraint_version",
        "constraint_name",
        "acquisition_id",
        "airline_code",
        "service_domain",
        "service_family",
        "ssr_code",
        "rfic",
        "rfisc",
        "condition_logic",
        "condition_groups",
        "conditions",
        "outcome_type",
        "outcome_value",
        "outcome_severity",
        "outcome_reason",
        "airline_applicability",
        "route_applicability",
        "destination_country_applicability",
        "constraint_priority",
        "evidence_reference_ids",
        "review_status",
        "approval_status",
        "evaluation_ready",
        "evaluation_notes",
        "future_engine_compatibility",
        "ssr_osi_workspace_ids",
        "emd_workspace_ids",
        "document_workspace_ids",
        "workflow_ids",
        "timeline_ids",
    ]
    for field in required_fields:
        if field not in item:
            raise AssertionError(f"Operational constraint field missing {field}: {item}")
    if item.get("metadata_only") is not True:
        raise AssertionError(f"Operational constraint is not metadata-only: {item}")
    group_conditions = (item.get("condition_groups") or [{}])[0].get("conditions") or []
    if not group_conditions or group_conditions[0].get("condition_operator") != "equals":
        raise AssertionError(f"Condition group operator did not persist: {item}")
    if not item.get("conditions") or item["conditions"][0].get("condition_operator") != "greater_than":
        raise AssertionError(f"Direct condition operator did not persist: {item}")
    if item.get("outcome_type") != "manual_review_required":
        raise AssertionError(f"Outcome metadata did not persist: {item}")
    if agency_view and item.get("read_only") is not True:
        raise AssertionError(f"Agency constraint should be read-only: {item}")


def assert_summary_shape(payload: dict, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary did not preserve agency id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "by_constraint_status",
        "by_outcome_type",
        "by_review_status",
        "by_approval_status",
        "condition_count",
        "condition_group_count",
        "evidence_link_count",
        "operational_link_count",
        "evaluation_ready_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Operational constraint summary missing {key}: {payload}")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    created = post(PLATFORM_BASE, constraint_payload(agency_id), OWNER_HEADERS, 201)
    assert_disabled_response(created)
    constraint = created.get("operational_constraint") or {}
    assert_constraint_shape(constraint)
    constraint_id = constraint.get("id")
    if not constraint_id:
        raise AssertionError(f"Operational constraint id missing: {created}")

    updated = put(
        f"{PLATFORM_BASE}/{constraint_id}",
        {
            "constraint_status": "approved",
            "review_status": "reviewed",
            "approval_status": "approved",
            "approved_by": "Constraint Approver",
            "approved_at": "2028-02-03T12:00:00Z",
            "review_notes": "Approved metadata only; no evaluation.",
            "internal_notes": "Updated metadata only; no live rule execution, AI reasoning, parser, scraping, or worker.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_constraint = updated.get("operational_constraint") or {}
    assert_constraint_shape(updated_constraint)
    if updated_constraint.get("review_status") != "reviewed" or updated_constraint.get("approval_status") != "approved":
        raise AssertionError(f"Operational constraint update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "acquisition_id=AKA-SMOKE-001",
        "airline=LH",
        "service_domain=animal_transport",
        "service_family=pet_transport",
        "ssr_code=PETC",
        "rfic=C",
        "rfisc=0BT",
        "constraint_status=approved",
        "outcome_type=manual_review_required",
        "review_status=reviewed",
        "approval_status=approved",
        "evaluation_ready=true",
    ]:
        filtered = get(f"{PLATFORM_BASE}?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == constraint_id for item in filtered.get("items") or []):
            raise AssertionError(f"Operational constraint filter {filter_query} missing created record: {filtered}")

    platform_summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"{PLATFORM_BASE}/{constraint_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_constraint_shape(platform_detail.get("operational_constraint") or {})

    agency_list = get(
        f"/api/agencies/{agency_id}/operational-constraints?acquisition_id=AKA-SMOKE-001&airline=LH&service_domain=animal_transport&service_family=pet_transport&ssr_code=PETC&rfic=C&rfisc=0BT&constraint_status=approved&outcome_type=manual_review_required&review_status=reviewed&approval_status=approved&evaluation_ready=true",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency constraint list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == constraint_id), None)
    if not agency_item:
        raise AssertionError(f"Agency constraint list missing created record: {agency_list}")
    assert_constraint_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/operational-constraints/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency constraint summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/operational-constraints/{constraint_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency constraint detail should be read-only: {agency_detail}")
    assert_constraint_shape(agency_detail.get("operational_constraint") or {}, agency_view=True)

    request("POST", f"/api/agencies/{agency_id}/operational-constraints", constraint_payload(agency_id, "OC-AGENCY-FORBIDDEN"), OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/operational-constraints/{constraint_id}", {"review_status": "rejected"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/operational-constraints/{constraint_id}", {}, OWNER_HEADERS, 405)

    archived = request("DELETE", f"{PLATFORM_BASE}/{constraint_id}", None, OWNER_HEADERS)[1]
    assert_disabled_response(archived)
    if archived.get("archived") is not True:
        raise AssertionError(f"Platform archive did not return archived marker: {archived}")


def main() -> None:
    verify_model_and_collection_registration()
    paths = get("/openapi.json").get("paths", {})
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_no_forbidden_implementation()
    verify_readiness()
    verify_blueprint_adoption()
    verify_endpoint_behavior()
    print("Phase 50.2 operational constraint engine foundation smoke passed.")


if __name__ == "__main__":
    main()
