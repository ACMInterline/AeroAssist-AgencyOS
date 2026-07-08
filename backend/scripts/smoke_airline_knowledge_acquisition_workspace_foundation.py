#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AirlineKnowledgeAcquisition, AirlineKnowledgeAcquisitionCreate
from services.airline_knowledge_acquisition_service import (
    ACQUISITION_STATUSES,
    AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION,
    APPROVAL_STATUSES,
    FUTURE_AOIE_FEEDS,
    KNOWLEDGE_GRAPH_PILLARS,
    REVIEW_STATUSES,
    SOURCE_TYPES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_50_3_airline_knowledge_normalisation_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-knowledge-acquisition"


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
        "ai_parsing_disabled",
        "automatic_extraction_disabled",
        "web_scraping_disabled",
        "web_crawling_disabled",
        "airline_website_automation_disabled",
        "provider_integrations_disabled",
        "live_airline_apis_disabled",
        "recommendation_engine_disabled",
        "feasibility_engine_disabled",
        "pricing_calculation_engine_disabled",
        "background_workers_disabled",
        "parser_execution_disabled",
        "automation_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def acquisition_payload(agency_id: str, reference: str = "AKA-SMOKE-001") -> dict:
    return {
        "agency_id": agency_id,
        "acquisition_reference": reference,
        "acquisition_status": "captured",
        "acquisition_type": "manual_official_source_capture",
        "acquisition_version": "1.0",
        "airline_code": "LH",
        "airline_name": "Lufthansa",
        "validating_carrier": "LH",
        "operating_carrier": "LH",
        "source_title": "Official wheelchair assistance policy",
        "source_type": "airline_website",
        "source_url": "https://example.test/lh/accessibility",
        "source_publication_date": "2028-01-02",
        "source_effective_date": "2028-02-01",
        "source_retrieved_date": "2028-02-02",
        "source_language": "en",
        "source_country": "DE",
        "source_region": "EU",
        "source_confidence": "official",
        "official_source_flag": True,
        "raw_source_text": "Official airline source text manually pasted by a human reviewer. No parser, scraping, crawling, AI extraction, or worker collected this text.",
        "source_excerpt": "Passengers requiring wheelchair assistance should request service before travel.",
        "source_notes": "Manual evidence capture for future review.",
        "source_hash": "manual-source-hash-smoke",
        "source_attachment_ids": ["source-attachment-smoke"],
        "service_domain": "passenger_assistance",
        "service_family": "mobility_assistance",
        "service_variant": "wheelchair_assistance",
        "ssr_code": "WCHR",
        "osi_relevance": "possible",
        "rfic": "E",
        "rfisc": "0B5",
        "ancillary_category": "assistance",
        "passenger_need_category": "mobility",
        "review_status": "in_review",
        "reviewer": "Policy Reviewer",
        "review_notes": "Review metadata only.",
        "approval_status": "pending",
        "previous_acquisition_id": "aka-previous-smoke",
        "supersedes_acquisition_ids": ["aka-superseded-smoke"],
        "change_summary": "Initial smoke evidence capture.",
        "detected_change_type": "manual_entry",
        "parser_run_ids": ["future-parser-run-smoke"],
        "normalized_rule_ids": ["future-normalized-rule-smoke"],
        "knowledge_version_ids": ["future-knowledge-version-smoke"],
        "capability_matrix_ids": ["future-capability-matrix-smoke"],
        "operational_feasibility_relevance": "future_review",
        "ssr_osi_workspace_ids": ["ssr-osi-workspace-smoke"],
        "emd_workspace_ids": ["emd-workspace-smoke"],
        "ticket_workspace_ids": ["ticket-workspace-smoke"],
        "document_workspace_ids": ["document-workspace-smoke"],
        "knowledge_graph_pillars": KNOWLEDGE_GRAPH_PILLARS,
        "evidence": {
            "official_source": "official",
            "source_title": "Official wheelchair assistance policy",
            "source_type": "airline_website",
            "source_url": "https://example.test/lh/accessibility",
            "publication_date": "2028-01-02",
            "effective_date": "2028-02-01",
            "retrieved_date": "2028-02-02",
            "original_text": "Official airline source text manually pasted by a human reviewer.",
            "source_confidence": "official",
            "human_reviewer": "Policy Reviewer",
            "version": "1.0",
            "attachment_ids": ["source-attachment-smoke"],
            "notes": "Manual evidence capture for future review.",
        },
        "policy": {
            "service_allowed": "allowed_with_review",
            "approval_required": "yes",
            "document_requirements": ["mobility assistance request"],
            "ssr_required": "yes",
            "ssr_codes": ["WCHR"],
            "osi_required": "possible",
            "osi_notes": "Use OSI for free-text assistance context when required.",
            "emd_required": "no",
            "medif_required": "conditional",
            "advance_notice": "48 hours",
            "policy_notes": "Policy metadata only.",
            "policy_references": ["AKA-SMOKE-001"],
        },
        "pricing": {
            "pricing_model": "manual_quotation",
            "fee_basis": "service_specific",
            "currency": "EUR",
            "amount": 0,
            "manual_quote_required": "no",
            "tax_rules": ["taxes not calculated in Phase 50.1"],
            "refundability": "not_applicable",
            "exchangeability": "not_applicable",
            "pricing_notes": "No pricing calculation is performed.",
            "extra_seat_pricing_schema": "airfare_only",
            "pricing_components": [
                {
                    "component_reference": "pricing-component-smoke",
                    "component_type": "service_fee",
                    "currency": "EUR",
                    "amount": 0,
                    "basis": "metadata_only",
                    "notes": "Stored only.",
                }
            ],
        },
        "capabilities": [
            {
                "capability_type": "wheelchair_assistance",
                "aircraft_family": "A320",
                "cabin": "economy",
                "onboard_wheelchair": "available",
                "ground_handling_capability": "station dependent",
                "crew_capability": "standard assistance",
                "connection_capability": "manual review",
                "capability_notes": "Capability metadata only; not a policy decision.",
            }
        ],
        "operational_constraints": [
            {
                "condition": "connection_time",
                "operator": "<",
                "value": "45m",
                "outcome": "manual_review",
                "reason": "Mobility assistance connection may need more handling time.",
                "notes": "No enforcement.",
                "condition_group": "mobility_connection",
                "applies_to": "WCHR",
                "source_reference": "AKA-SMOKE-001",
            }
        ],
        "animal_transport": {
            "species": "dog",
            "breed": "French Bulldog",
            "brachycephalic": "yes",
            "dangerous_breed": "no",
            "service_animal": "conditional",
            "emotional_support": "not_supported",
            "destination_restrictions": ["destination rules metadata only"],
            "temperature_embargo": "manual review above 29C",
            "carrier_dimensions": "metadata only",
            "carrier_weight": "metadata only",
            "adjacent_seat_policy": "not applicable",
            "purchased_exst_policy": "metadata only",
            "operational_handling_notes": "Animal transport metadata only.",
            "constraints": [
                {
                    "condition": "breed",
                    "operator": "=",
                    "value": "French Bulldog",
                    "outcome": "embargo_review",
                    "reason": "Brachycephalic handling may be restricted.",
                }
            ],
        },
        "extra_seat": [
            {
                "extra_seat_type": "passenger_of_size",
                "adjacent_seat": "required",
                "fixed_armrests": "avoid",
                "business_cabin": "aircraft dependent",
                "premium_economy": "aircraft dependent",
                "aircraft_exceptions": ["A321 business cabin"],
                "refund_if_aircraft_not_full": "metadata only",
                "refund_if_airline_accommodates_without_exst": "metadata only",
                "route_restrictions": ["route-specific metadata only"],
                "policy": {"service_allowed": "conditional", "approval_required": "manual_review"},
                "pricing": {"pricing_model": "airfare_only", "pricing_notes": "No fare calculation."},
                "capability": {"capability_type": "extra_seat", "adjacent_seats": "required"},
                "operational_constraints": [
                    {
                        "condition": "cabin",
                        "operator": "=",
                        "value": "business",
                        "outcome": "manual_review",
                        "reason": "Seat construction may prevent adjacent EXST.",
                    }
                ],
                "refund_conditions": ["metadata only"],
                "notes": "Extra seat metadata only.",
            }
        ],
        "cabin_capabilities": [
            {
                "cabin": "economy",
                "seat_configuration": "3-3",
                "seat_map": "future-seatmap-reference",
                "armrests": "mixed",
                "adjacent_seats": "available",
                "bassinet": "limited",
                "wheelchair": "onboard available",
                "lavatory": "standard",
                "petc": "conditional",
                "cbbg": "conditional",
                "exst": "conditional",
                "medical_equipment": "manual review",
                "crew_handling": "standard",
                "cabin_notes": "Cabin capability metadata only.",
                "constraints": [
                    {
                        "condition": "seat_row",
                        "operator": "=",
                        "value": "exit",
                        "outcome": "not_allowed",
                        "reason": "Assistance passenger seating restriction metadata.",
                    }
                ],
            }
        ],
        "operational_procedures": [
            {
                "procedure_reference": "procedure-smoke",
                "procedure_title": "Manual assistance review",
                "procedure_notes": "Procedure metadata only; no workflow execution.",
            }
        ],
        "internal_notes": "Metadata-only acquisition evidence.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Airline knowledge acquisitions collection is not registered as agency-owned metadata.")
    create_payload = AirlineKnowledgeAcquisitionCreate(**acquisition_payload("agency-smoke", "AKA-SMOKE-MODEL"))
    record = AirlineKnowledgeAcquisition(**create_payload.model_dump(mode="json", exclude_none=True))
    if record.raw_source_text is None or "Official airline source text" not in record.raw_source_text:
        raise AssertionError("Airline knowledge acquisition model did not preserve raw source text.")
    if record.review_status != "in_review" or record.approval_status != "pending":
        raise AssertionError("Airline knowledge acquisition model did not preserve review/approval metadata.")
    if record.knowledge_graph_pillars != KNOWLEDGE_GRAPH_PILLARS:
        raise AssertionError("Airline knowledge acquisition model did not preserve knowledge graph pillars.")
    if record.policy.service_allowed != "allowed_with_review":
        raise AssertionError("Airline knowledge acquisition model did not preserve policy metadata.")
    if record.pricing.extra_seat_pricing_schema != "airfare_only":
        raise AssertionError("Airline knowledge acquisition model did not preserve pricing metadata.")
    if not record.capabilities or record.capabilities[0].capability_notes is None:
        raise AssertionError("Airline knowledge acquisition model did not preserve capability metadata.")
    if not record.operational_constraints or record.operational_constraints[0].outcome != "manual_review":
        raise AssertionError("Airline knowledge acquisition model did not preserve operational constraints.")
    if record.animal_transport.brachycephalic != "yes":
        raise AssertionError("Airline knowledge acquisition model did not preserve animal transport metadata.")
    if not record.extra_seat or record.extra_seat[0].extra_seat_type != "passenger_of_size":
        raise AssertionError("Airline knowledge acquisition model did not preserve extra-seat metadata.")
    if not record.cabin_capabilities or record.cabin_capabilities[0].cabin != "economy":
        raise AssertionError("Airline knowledge acquisition model did not preserve cabin capability metadata.")
    if record.metadata_only is not True or record.ai_parsing_disabled is not True:
        raise AssertionError("Airline knowledge acquisition model is not metadata-only.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_knowledge_acquisitions_id_unique",
        "airline_knowledge_acquisitions_reference_unique",
        "airline_knowledge_acquisitions_agency_status_lookup",
        "airline_knowledge_acquisitions_agency_airline_lookup",
        "airline_knowledge_acquisitions_agency_source_type_lookup",
        "airline_knowledge_acquisitions_agency_review_status_lookup",
        "airline_knowledge_acquisitions_agency_approval_status_lookup",
        "airline_knowledge_acquisitions_service_classification_lookup",
        "airline_knowledge_acquisitions_ssr_code_lookup",
        "airline_knowledge_acquisitions_rfic_rfisc_lookup",
        "airline_knowledge_acquisitions_effective_date_lookup",
        "airline_knowledge_acquisitions_official_source_lookup",
        "airline_knowledge_acquisitions_previous_lookup",
        "airline_knowledge_acquisitions_parser_run_lookup",
        "airline_knowledge_acquisitions_normalized_rule_lookup",
        "airline_knowledge_acquisitions_knowledge_version_lookup",
        "airline_knowledge_acquisitions_capability_matrix_lookup",
        "airline_knowledge_acquisitions_ssr_osi_workspace_lookup",
        "airline_knowledge_acquisitions_emd_workspace_lookup",
        "airline_knowledge_acquisitions_ticket_workspace_lookup",
        "airline_knowledge_acquisitions_document_workspace_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Airline knowledge acquisition index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    expected_methods = {
        "/api/platform/airline-knowledge-acquisition": {"get", "post"},
        "/api/platform/airline-knowledge-acquisition/summary": {"get"},
        "/api/platform/airline-knowledge-acquisition/{acquisition_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/airline-knowledge-acquisition": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-acquisition/summary": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-acquisition/{acquisition_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/airline-knowledge-acquisition",
        "/api/agencies/{agency_id}/airline-knowledge-acquisition/summary",
        "/api/agencies/{agency_id}/airline-knowledge-acquisition/{acquisition_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency airline knowledge acquisition route is not read-only: {path} {sorted(blocked_methods)}")
    for path in paths:
        if "airline-knowledge-acquisition" in path and "parser" in path:
            raise AssertionError(f"Parser route should not exist for acquisition workspace: {path}")
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Airline Knowledge Acquisition"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge Acquisition"),
        (ROOT / "frontend/src/App.jsx", "/platform/airline-knowledge-acquisition"),
        (ROOT / "frontend/src/App.jsx", "/agency/knowledge-acquisition"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeAcquisitionPage.jsx", "No parser execution"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeAcquisitionPage.jsx", "Operational Knowledge Graph"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeAcquisitionPage.jsx", "Operational Constraints"),
        (ROOT / "frontend/src/pages/agency/KnowledgeAcquisitionPage.jsx", "Read-only airline source evidence metadata"),
        (ROOT / "frontend/src/pages/agency/KnowledgeAcquisitionPage.jsx", "Extra Seat"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Official airline source -> Human copy/paste or manual entry"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Airline Operational Knowledge Graph"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Evidence"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Policy"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Pricing"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Capability"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Operational Constraints"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "50.2 Operational Constraint Engine"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Phase 50.1 adds the `airline_knowledge_acquisitions` evidence intake collection"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Future AOIE does not reason over text alone"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Phase 50.1 adds the Airline Knowledge Acquisition Workspace"),
        (ROOT / "BUILD_PHASES.md", "Phase 50.1: Airline Knowledge Acquisition Workspace Foundation"),
        (ROOT / "README.md", "Phase 50.1 Includes"),
        (ROOT / "docs/architecture/current-model-inventory.md", "airline_knowledge_acquisitions"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/airline-knowledge-acquisition"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Airline knowledge acquisition"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Airline Knowledge Acquisition"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeAcquisitionPage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeAcquisitionPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeAcquisitionPage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeAcquisitionPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Airline Knowledge Acquisition" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Airline Knowledge Acquisition category: {categories}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Airline knowledge acquisition workspace foundation built in Phase 50.1" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gaps missing Phase 50.1 built marker: {gaps}")
    if "Phase 50.4" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.4 next intelligence phase: {gaps}")
    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if next_phases["items"][0].get("phase") != "Phase 50.4":
        raise AssertionError(f"Next recommendations did not start with Phase 50.4: {next_phases}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_knowledge_acquisition_workspace_foundation") or {}
    for flag in [
        "airline_knowledge_acquisition_enabled",
        "airline_knowledge_acquisition_workspace_enabled",
        "manual_source_evidence_intake_enabled",
        "source_evidence_metadata_enabled",
        "airline_operational_knowledge_graph_foundation_enabled",
        "operational_knowledge_graph_pillars_enabled",
        "policy_metadata_pillar_enabled",
        "pricing_metadata_pillar_enabled",
        "capability_metadata_pillar_enabled",
        "operational_constraints_metadata_pillar_enabled",
        "animal_transport_knowledge_metadata_enabled",
        "extra_seat_knowledge_metadata_enabled",
        "cabin_capability_knowledge_metadata_enabled",
        "policy_pricing_capability_constraints_separated",
        "platform_airline_knowledge_acquisition_metadata_crud_enabled",
        "agency_airline_knowledge_acquisition_read_only_enabled",
        "platform_airline_knowledge_acquisition_ui_enabled",
        "agency_knowledge_acquisition_ui_enabled",
        "filter_by_airline_enabled",
        "filter_by_service_domain_enabled",
        "filter_by_service_family_enabled",
        "filter_by_ssr_code_enabled",
        "filter_by_rfic_enabled",
        "filter_by_rfisc_enabled",
        "filter_by_source_type_enabled",
        "filter_by_review_status_enabled",
        "filter_by_approval_status_enabled",
        "filter_by_effective_date_enabled",
        "filter_by_official_source_flag_enabled",
        "review_metadata_enabled",
        "approval_metadata_enabled",
        "versioning_metadata_enabled",
        "future_aoie_link_metadata_enabled",
        "operational_link_metadata_enabled",
        "feeds_policy_text_parser_metadata",
        "feeds_service_rule_normalisation_metadata",
        "feeds_knowledge_version_review_metadata",
        "feeds_capability_matrix_metadata",
        "feeds_passenger_service_feasibility_metadata",
        "feeds_airline_itinerary_recommendation_metadata",
        "feeds_total_journey_cost_comparison_metadata",
        "metadata_only",
        "evidence_intake_only",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Airline knowledge acquisition readiness missing flag {flag}: {section}")
    for flag in disabled_flags():
        if section.get(flag) is not True:
            raise AssertionError(f"Airline knowledge acquisition readiness missing disabled flag {flag}: {section}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Airline knowledge acquisition readiness should not be deployment-readiness required.")
    for count_key in [
        "airline_knowledge_acquisition_count",
        "airline_knowledge_acquisition_status_counts",
        "airline_knowledge_acquisition_source_type_counts",
        "airline_knowledge_acquisition_review_status_counts",
        "airline_knowledge_acquisition_approval_status_counts",
        "airline_knowledge_acquisition_official_source_count",
        "airline_knowledge_acquisition_raw_source_text_count",
        "airline_knowledge_acquisition_version_link_count",
        "airline_knowledge_acquisition_future_aoie_link_count",
        "airline_knowledge_acquisition_operational_link_count",
        "airline_knowledge_graph_pillars",
        "airline_knowledge_acquisition_policy_count",
        "airline_knowledge_acquisition_pricing_count",
        "airline_knowledge_acquisition_capability_count",
        "airline_knowledge_acquisition_operational_constraint_count",
        "airline_knowledge_acquisition_animal_transport_count",
        "airline_knowledge_acquisition_extra_seat_count",
        "airline_knowledge_acquisition_cabin_capability_count",
        "airline_knowledge_acquisition_operational_procedure_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Airline knowledge acquisition readiness missing count: {count_key}")
    if section.get("airline_knowledge_graph_pillars") != KNOWLEDGE_GRAPH_PILLARS:
        raise AssertionError(f"Readiness missing knowledge graph pillars: {section}")
    if not set(ACQUISITION_STATUSES).issubset(set((section.get("airline_knowledge_acquisition_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing acquisition statuses: {section}")
    if not set(SOURCE_TYPES).issubset(set((section.get("airline_knowledge_acquisition_source_type_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing source types: {section}")
    if not set(REVIEW_STATUSES).issubset(set((section.get("airline_knowledge_acquisition_review_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing review statuses: {section}")
    if not set(APPROVAL_STATUSES).issubset(set((section.get("airline_knowledge_acquisition_approval_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing approval statuses: {section}")


def verify_no_forbidden_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/airline_knowledge_acquisition_service.py",
        ROOT / "backend/routers/platform_airline_knowledge_acquisition.py",
        ROOT / "backend/routers/agency_airline_knowledge_acquisition.py",
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeAcquisitionPage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeAcquisitionPage.jsx",
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
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden implementation term: {term}")


def assert_acquisition_shape(item: dict, agency_view: bool = False) -> None:
    required_fields = [
        "id",
        "agency_id",
        "acquisition_reference",
        "acquisition_status",
        "airline_code",
        "source_title",
        "source_type",
        "source_effective_date",
        "official_source_flag",
        "raw_source_text",
        "source_excerpt",
        "service_domain",
        "service_family",
        "ssr_code",
        "rfic",
        "rfisc",
        "review_status",
        "approval_status",
        "previous_acquisition_id",
        "supersedes_acquisition_ids",
        "parser_run_ids",
        "normalized_rule_ids",
        "knowledge_version_ids",
        "capability_matrix_ids",
        "ssr_osi_workspace_ids",
        "emd_workspace_ids",
        "ticket_workspace_ids",
        "document_workspace_ids",
        "knowledge_graph_pillars",
        "evidence",
        "policy",
        "pricing",
        "capabilities",
        "operational_constraints",
        "animal_transport",
        "extra_seat",
        "cabin_capabilities",
        "operational_procedures",
    ]
    for field in required_fields:
        if field not in item:
            raise AssertionError(f"Airline knowledge acquisition field missing {field}: {item}")
    if "Official airline source text" not in item.get("raw_source_text", ""):
        raise AssertionError(f"Raw official-source text missing from acquisition: {item}")
    if item.get("metadata_only") is not True or item.get("evidence_intake_only") is not True:
        raise AssertionError(f"Acquisition is not metadata evidence only: {item}")
    if item.get("knowledge_graph_pillars") != KNOWLEDGE_GRAPH_PILLARS:
        raise AssertionError(f"Acquisition missing knowledge graph pillars: {item}")
    if (item.get("policy") or {}).get("service_allowed") != "allowed_with_review":
        raise AssertionError(f"Acquisition missing policy metadata: {item}")
    if (item.get("pricing") or {}).get("extra_seat_pricing_schema") != "airfare_only":
        raise AssertionError(f"Acquisition missing pricing metadata: {item}")
    if not item.get("capabilities"):
        raise AssertionError(f"Acquisition missing capability metadata: {item}")
    if not item.get("operational_constraints"):
        raise AssertionError(f"Acquisition missing operational constraints: {item}")
    if not item.get("extra_seat") or not item.get("cabin_capabilities"):
        raise AssertionError(f"Acquisition missing extra-seat or cabin capability metadata: {item}")
    if agency_view and item.get("read_only") is not True:
        raise AssertionError(f"Agency acquisition should be read-only: {item}")


def assert_summary_shape(payload: dict, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary did not preserve agency id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "by_acquisition_status",
        "by_source_type",
        "by_review_status",
        "by_approval_status",
        "official_source_count",
        "raw_source_text_count",
        "version_link_count",
        "future_aoie_link_count",
        "operational_link_count",
        "knowledge_graph_pillars",
        "policy_count",
        "pricing_count",
        "capability_count",
        "operational_constraint_count",
        "animal_transport_count",
        "extra_seat_count",
        "cabin_capability_count",
        "operational_procedure_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Airline knowledge acquisition summary missing {key}: {payload}")
    if summary.get("knowledge_graph_pillars") != KNOWLEDGE_GRAPH_PILLARS:
        raise AssertionError(f"Airline knowledge acquisition summary missing graph pillars: {payload}")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    created = post(PLATFORM_BASE, acquisition_payload(agency_id), OWNER_HEADERS, 201)
    assert_disabled_response(created)
    acquisition = created.get("airline_knowledge_acquisition") or {}
    assert_acquisition_shape(acquisition)
    acquisition_id = acquisition.get("id")
    if not acquisition_id:
        raise AssertionError(f"Airline knowledge acquisition id missing: {created}")

    updated = put(
        f"{PLATFORM_BASE}/{acquisition_id}",
        {
            "acquisition_status": "reviewed",
            "review_status": "reviewed",
            "approval_status": "approved",
            "approved_by": "Policy Approver",
            "approved_at": "2028-02-03T12:00:00Z",
            "review_notes": "Approved metadata-only evidence.",
            "internal_notes": "Updated metadata only; no parser, scraping, worker, provider call, or AI interpretation.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_acquisition = updated.get("airline_knowledge_acquisition") or {}
    assert_acquisition_shape(updated_acquisition)
    if updated_acquisition.get("review_status") != "reviewed" or updated_acquisition.get("approval_status") != "approved":
        raise AssertionError(f"Airline knowledge acquisition update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "airline=LH",
        "service_domain=passenger_assistance",
        "service_family=mobility_assistance",
        "ssr_code=WCHR",
        "rfic=E",
        "rfisc=0B5",
        "source_type=airline_website",
        "review_status=reviewed",
        "approval_status=approved",
        "effective_date=2028-02-01",
        "official_source_flag=true",
    ]:
        filtered = get(f"{PLATFORM_BASE}?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == acquisition_id for item in filtered.get("items") or []):
            raise AssertionError(f"Airline knowledge acquisition filter {filter_query} missing created record: {filtered}")

    platform_summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"{PLATFORM_BASE}/{acquisition_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_acquisition_shape(platform_detail.get("airline_knowledge_acquisition") or {})

    agency_list = get(
        f"/api/agencies/{agency_id}/airline-knowledge-acquisition?airline=LH&service_domain=passenger_assistance&service_family=mobility_assistance&ssr_code=WCHR&rfic=E&rfisc=0B5&source_type=airline_website&review_status=reviewed&approval_status=approved&effective_date=2028-02-01&official_source_flag=true",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency acquisition list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == acquisition_id), None)
    if not agency_item:
        raise AssertionError(f"Agency acquisition list missing created record: {agency_list}")
    assert_acquisition_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/airline-knowledge-acquisition/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency acquisition summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/airline-knowledge-acquisition/{acquisition_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency acquisition detail should be read-only: {agency_detail}")
    assert_acquisition_shape(agency_detail.get("airline_knowledge_acquisition") or {}, agency_view=True)

    request("POST", f"/api/agencies/{agency_id}/airline-knowledge-acquisition", acquisition_payload(agency_id, "AKA-AGENCY-FORBIDDEN"), OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/airline-knowledge-acquisition/{acquisition_id}", {"review_status": "rejected"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/airline-knowledge-acquisition/{acquisition_id}", {}, OWNER_HEADERS, 405)

    archived = request("DELETE", f"{PLATFORM_BASE}/{acquisition_id}", None, OWNER_HEADERS)[1]
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
    print("Phase 50.1 airline knowledge acquisition workspace foundation smoke passed.")


if __name__ == "__main__":
    main()
