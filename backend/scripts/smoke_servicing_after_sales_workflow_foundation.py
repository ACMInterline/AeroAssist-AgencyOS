#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    AfterSalesCase,
    AfterSalesCaseItem,
    AfterSalesCommunicationRecord,
    AfterSalesDecision,
    AfterSalesFinancialImpact,
    AfterSalesResolution,
)
from services.after_sales_workflow_service import (
    AFTER_SALES_CASE_ITEMS_COLLECTION,
    AFTER_SALES_CASES_COLLECTION,
    AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION,
    AFTER_SALES_DECISIONS_COLLECTION,
    AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION,
    AFTER_SALES_RESOLUTIONS_COLLECTION,
    CASE_STATUSES,
    CASE_TYPES,
    PHASE_LABEL,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8").lower()
    if text.lower() in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_no_forbidden_execution_text() -> None:
    service_path = ROOT / "backend/services/after_sales_workflow_service.py"
    for forbidden in [
        "requests.get(",
        "requests.post(",
        "httpx.",
        "urllib.request",
        "openai",
        "stripe",
        "send_email",
        "send_sms",
        "BackgroundTasks",
        "asyncio.create_task",
        "ticket_workspaces\").update_one",
        "emd_workspaces\").update_one",
        "payment_records\").insert_one",
    ]:
        reject_text(service_path, forbidden)


def assert_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "servicing_after_sales_workflow_foundation",
        "ticket_mutation_disabled",
        "emd_mutation_disabled",
        "financial_commitment_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "background_workers_disabled",
        "ai_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Missing after-sales safety flag {flag}: {payload}")


def verify_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service PHASE_LABEL mismatch: {PHASE_LABEL}")
    for collection in [
        AFTER_SALES_CASES_COLLECTION,
        AFTER_SALES_CASE_ITEMS_COLLECTION,
        AFTER_SALES_DECISIONS_COLLECTION,
        AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION,
        AFTER_SALES_RESOLUTIONS_COLLECTION,
        AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Missing agency-owned collection registration: {collection}")
        require_text(ROOT / "backend/database.py", collection)
    for index_name in [
        "after_sales_cases_reference_unique",
        "after_sales_cases_agency_idempotency_lookup",
        "after_sales_case_items_agency_case_lookup",
        "after_sales_decisions_reference_unique",
        "after_sales_financial_impacts_reference_unique",
        "after_sales_resolutions_reference_unique",
        "after_sales_communication_records_reference_unique",
    ]:
        require_text(ROOT / "backend/database.py", index_name)
    for case_type in [
        "voluntary_change",
        "schedule_change",
        "cancellation",
        "refund",
        "ticket_exchange",
        "emd_exchange_refund",
        "claim",
        "service_amendment",
        "passenger_document_amendment",
        "disruption_irregular_operation",
    ]:
        if case_type not in CASE_TYPES:
            raise AssertionError(f"Missing after-sales case type: {case_type}")
    for status in [
        "opened",
        "assessing",
        "information_required",
        "supplier_contact_required",
        "client_decision_required",
        "quote_preparation",
        "awaiting_approval",
        "processing",
        "partially_resolved",
        "resolved",
        "rejected",
        "cancelled",
        "archived",
    ]:
        if status not in CASE_STATUSES:
            raise AssertionError(f"Missing after-sales case status: {status}")
    samples = [
        AfterSalesCase(agency_id="agency", case_reference="ASC-SMOKE", case_type="refund", case_title="Refund metadata"),
        AfterSalesCaseItem(agency_id="agency", case_id="case", item_type="ticket", source_entity_type="ticket_workspace", source_entity_id="ticket"),
        AfterSalesDecision(agency_id="agency", case_id="case", decision_reference="ASD-SMOKE"),
        AfterSalesFinancialImpact(agency_id="agency", case_id="case", impact_reference="ASF-SMOKE"),
        AfterSalesResolution(agency_id="agency", case_id="case", resolution_reference="ASR-SMOKE"),
        AfterSalesCommunicationRecord(agency_id="agency", case_id="case", communication_reference="ASCMM-SMOKE"),
    ]
    for sample in samples:
        dumped = sample.model_dump(mode="json")
        if dumped.get("metadata_only") is not True:
            raise AssertionError(f"After-sales model is not metadata-only: {dumped}")
    assert_no_forbidden_execution_text()


def verify_routes_and_docs(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected = {
        "/api/platform/after-sales": {"get"},
        "/api/platform/after-sales/summary": {"get"},
        "/api/platform/after-sales/items": {"get"},
        "/api/platform/after-sales/decisions": {"get"},
        "/api/platform/after-sales/financial-impacts": {"get"},
        "/api/platform/after-sales/resolutions": {"get"},
        "/api/platform/after-sales/communications": {"get"},
        "/api/platform/after-sales/{case_id}": {"get"},
        "/api/agencies/{agency_id}/after-sales": {"get", "post"},
        "/api/agencies/{agency_id}/after-sales/summary": {"get"},
        "/api/agencies/{agency_id}/after-sales/{case_id}": {"get", "put"},
        "/api/agencies/{agency_id}/after-sales/{case_id}/items": {"get", "post"},
        "/api/agencies/{agency_id}/after-sales/{case_id}/decisions": {"get", "post"},
        "/api/agencies/{agency_id}/after-sales/{case_id}/financial-impacts": {"get", "post"},
        "/api/agencies/{agency_id}/after-sales/{case_id}/resolutions": {"get", "post"},
        "/api/agencies/{agency_id}/after-sales/{case_id}/communications": {"get", "post"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    platform_methods = set(paths.get("/api/platform/after-sales", {}).keys())
    if platform_methods & {"post", "put", "patch", "delete"}:
        raise AssertionError(f"Platform after-sales diagnostics should be read-only at root: {platform_methods}")
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/agency/after-sales"),
        (ROOT / "frontend/src/App.jsx", "/platform/after-sales"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "After-Sales"),
        (ROOT / "frontend/src/pages/agency/AfterSalesPage.jsx", "does not mutate tickets or EMDs"),
        (ROOT / "frontend/src/pages/platform/AfterSalesDiagnosticsPage.jsx", "Read-only platform visibility"),
        (ROOT / "docs/architecture/servicing-after-sales-workflow-foundation.md", "Servicing and After-Sales Workflow Foundation"),
        (ROOT / "README.md", "servicing/after-sales workflow records"),
        (ROOT / "BUILD_PHASES.md", "Phase 54.7: Servicing and after-sales workflow foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "after_sales_cases"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 54.7 adds servicing and after-sales workflow APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Servicing and after-sales workflow"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Servicing and After-Sales Workflow"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Servicing and After-Sales Workflow"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Servicing and After-Sales Workflow"),
    ]:
        require_text(path, text)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("servicing_after_sales_workflow_foundation") or {}
    for flag in [
        "servicing_after_sales_workflow_enabled",
        "after_sales_cases_collection_enabled",
        "after_sales_case_items_collection_enabled",
        "after_sales_decisions_collection_enabled",
        "after_sales_financial_impacts_collection_enabled",
        "after_sales_resolutions_collection_enabled",
        "after_sales_communication_records_collection_enabled",
        "agency_after_sales_workspace_enabled",
        "platform_after_sales_governance_diagnostics_enabled",
        "coupon_status_awareness_enabled",
        "financial_placeholders_enabled",
        "client_approval_guard_enabled",
        "workflow_integration_enabled",
        "work_queue_integration_enabled",
        "task_automation_integration_enabled",
        "deadline_integration_enabled",
        "timeline_integration_enabled",
        "ticket_mutation_disabled",
        "emd_mutation_disabled",
        "financial_commitment_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "background_workers_disabled",
        "ai_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing after-sales flag {flag}: {section}")
    for key in [
        "case_statuses",
        "case_types",
        "after_sales_case_count",
        "after_sales_case_item_count",
        "after_sales_decision_count",
        "after_sales_financial_impact_count",
        "after_sales_resolution_count",
        "after_sales_communication_record_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing after-sales key {key}: {section}")


def agency_ids() -> list[str]:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("No agencies available after seed.")
    return [agency["id"] for agency in agencies]


def case_payload(case_type: str) -> dict:
    token = ref(case_type.upper()[:3])
    return {
        "case_type": case_type,
        "case_priority": "high" if case_type in {"disruption_irregular_operation", "claim"} else "normal",
        "case_title": f"{case_type.replace('_', ' ').title()} smoke {token}",
        "case_summary": "Metadata-only after-sales servicing case for smoke validation.",
        "trip_workspace_id": f"trip-{token}",
        "booking_workspace_id": f"booking-{token}",
        "ticket_workspace_ids": [f"ticket-{token}"],
        "emd_workspace_ids": [f"emd-{token}"],
        "passenger_workspace_ids": [f"passenger-{token}"],
        "document_workspace_ids": [f"document-{token}"],
        "ssr_osi_workspace_ids": [f"ssr-{token}"],
        "affected_segment_refs": ["seg-1"],
        "residual_value_summary": "Residual value placeholder only.",
        "penalty_summary": "Penalty requires manual supplier review.",
        "fare_difference_summary": "Fare difference is not calculated in this phase.",
        "service_fee_summary": "Service fee metadata placeholder.",
        "refundability_summary": "Refundability requires human review.",
        "document_requirements_json": [{"document_type": "airline_approval", "status": "required", "metadata_only": True}],
        "supplier_communication_required": True,
        "client_approval_required": True,
        "generated_advice_json": {"advice_status": "draft_metadata", "no_sending": True},
        "internal_message_json": {"summary": "Internal after-sales note."},
        "client_message_json": {"summary": "Client-facing draft message metadata."},
        "financial_estimate_json": {"estimate_status": "placeholder", "no_commitment": True},
        "idempotency_key": f"smoke:{case_type}:{token}",
    }


def verify_live_api(paths: dict) -> None:
    verify_routes_and_docs(paths)
    verify_readiness()
    primary_agency_id = agency_ids()[0]
    created_cases = []
    for case_type in CASE_TYPES:
        response = post(f"/api/agencies/{primary_agency_id}/after-sales", case_payload(case_type), AGENCY_AGENT_HEADERS, 201)
        case = response.get("case") or {}
        assert_flags(response)
        assert_flags(case)
        if case.get("case_type") != case_type:
            raise AssertionError(f"Case type mismatch: {case}")
        if not case.get("items") or not case.get("financial_impacts") or not case.get("decisions") or not case.get("resolutions"):
            raise AssertionError(f"Missing child metadata in after-sales case response: {case}")
        if not case.get("workflow_instance_id") or not case.get("work_item_ids") or not case.get("deadline_ids") or not case.get("timeline_entry_ids"):
            raise AssertionError(f"Missing workflow/queue/SLA/timeline integration ids: {case}")
        if case.get("decisions", [{}])[0].get("approval_guard_json", {}).get("no_ticket_or_emd_mutation") is not True:
            raise AssertionError(f"Missing approval guard metadata: {case.get('decisions')}")
        if (case.get("financial_impacts") or [{}])[0].get("financial_placeholder_only") is not True:
            raise AssertionError(f"Missing financial placeholder flag: {case.get('financial_impacts')}")
        if (case.get("impact_scope_json") or {}).get("warnings") is None:
            raise AssertionError(f"Missing missing-link warning metadata: {case.get('impact_scope_json')}")
        created_cases.append(case)

    case = created_cases[0]
    detail = get(f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}", AGENCY_AGENT_HEADERS).get("case") or {}
    if detail.get("id") != case["id"]:
        raise AssertionError(f"Agency case detail mismatch: {detail}")
    updated = put(f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}", {"case_status": "assessing"}, AGENCY_AGENT_HEADERS).get("case") or {}
    if updated.get("case_status") != "assessing":
        raise AssertionError(f"Case status update failed: {updated}")
    post(
        f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}/items",
        {"item_type": "ticket", "source_entity_type": "ticket_workspace", "source_entity_id": "ticket-extra", "coupon_number": "1", "coupon_status": "open_for_use"},
        AGENCY_AGENT_HEADERS,
        201,
    )
    post(
        f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}/decisions",
        {"decision_type": "client_approval", "decision_status": "needs_client_approval", "requires_client_approval": True},
        AGENCY_AGENT_HEADERS,
        201,
    )
    post(
        f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}/financial-impacts",
        {"impact_type": "fare_difference", "estimate_status": "placeholder", "placeholder_notes": "Manual quote required."},
        AGENCY_AGENT_HEADERS,
        201,
    )
    post(
        f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}/communications",
        {"communication_type": "internal_note", "summary": "Follow-up required.", "internal_message": "Internal note only."},
        AGENCY_AGENT_HEADERS,
        201,
    )
    request(
        "POST",
        f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}/resolutions",
        {"resolution_type": "ticket_exchange", "ticket_mutation_authorized": True},
        AGENCY_AGENT_HEADERS,
        400,
    )
    request(
        "POST",
        f"/api/agencies/{primary_agency_id}/after-sales/{case['id']}/communications",
        {"communication_type": "client_message", "summary": "Should not send.", "sent_externally": True},
        AGENCY_AGENT_HEADERS,
        400,
    )
    platform = get("/api/platform/after-sales", OWNER_HEADERS)
    if not platform.get("platform_read_only_diagnostics") or not platform.get("items"):
        raise AssertionError(f"Platform after-sales diagnostics failed: {platform}")
    get(f"/api/platform/after-sales/{case['id']}", OWNER_HEADERS)
    request("POST", "/api/platform/after-sales", {"case_type": "refund"}, OWNER_HEADERS, 405)
    request("GET", f"/api/agencies/other-agency/after-sales/{case['id']}", None, AGENCY_AGENT_HEADERS, 404)


def main() -> None:
    verify_static_contracts()
    paths = get("/openapi.json").get("paths", {})
    verify_live_api(paths)
    print("Phase 54.7 servicing and after-sales workflow foundation smoke passed.")


if __name__ == "__main__":
    main()
