#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AirlineKnowledgeNormalisation, AirlineKnowledgeNormalisationCreate
from services.airline_knowledge_normalisation_service import (
    AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION,
    APPROVAL_STATUSES,
    NORMALISATION_STATUSES,
    NORMALISATION_TYPES,
    REVIEW_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-knowledge-normalisation"


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
        "live_evaluation_disabled",
        "ai_parsing_disabled",
        "recommendation_engine_disabled",
        "feasibility_scoring_disabled",
        "pricing_calculation_disabled",
        "scraping_disabled",
        "background_workers_disabled",
        "provider_integrations_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def normalisation_payload(agency_id: str, reference: str = "AKN-SMOKE-001") -> dict:
    return {
        "agency_id": agency_id,
        "normalisation_reference": reference,
        "normalisation_status": "captured",
        "normalisation_type": "animal_taxonomy",
        "canonical_code": "ANIMAL_DOG_FRENCH_BULLDOG",
        "canonical_name": "French Bulldog",
        "canonical_description": "Canonical animal taxonomy metadata for future airline comparison.",
        "taxonomy_domain": "animal",
        "taxonomy_family": "dog",
        "taxonomy_variant": "breed",
        "parent_canonical_id": "ANIMAL_DOG",
        "hierarchy_path": ["animal", "dog", "brachycephalic", "french_bulldog"],
        "hierarchy_level": 4,
        "aliases": ["Frenchie", "Bouledogue Francais"],
        "abbreviations": ["FRBD"],
        "airline_specific_terms": ["snub-nosed dog"],
        "gds_terms": ["PETC DOG"],
        "commercial_terms": ["French Bulldog pet in cabin"],
        "operational_terms": ["brachycephalic breed"],
        "airline_codes": ["LH", "AF"],
        "country_codes": ["DE", "FR"],
        "airport_codes": ["FRA", "CDG"],
        "aircraft_types": ["A321neo"],
        "cabin_codes": ["J", "Y"],
        "service_codes": ["PETC"],
        "ssr_codes": ["PETC"],
        "rfic_codes": ["C"],
        "rfisc_codes": ["0BT"],
        "species": "Dog",
        "breed": "French Bulldog",
        "breed_group": "Brachycephalic",
        "brachycephalic_flag": True,
        "restricted_breed_flag": True,
        "service_animal_flag": False,
        "emotional_support_animal_flag": False,
        "animal_notes": "Metadata-only animal taxonomy note.",
        "aircraft_family": "A320 Family",
        "aircraft_subtype": "A321neo",
        "cabin_family": "Premium Cabin",
        "cabin_name": "Business",
        "seat_type": "standard_business",
        "fixed_armrest_flag": True,
        "adjacent_seat_relevance": "extra_seat_review",
        "under_seat_space_relevance": "pet_carrier_review",
        "cabin_notes": "Aircraft and cabin metadata only.",
        "passenger_need_category": "animal_transport",
        "service_domain": "animal_transport",
        "service_family": "pet_transport",
        "service_variant": "pet_in_cabin",
        "related_ssr_code": "PETC",
        "related_osi_relevance": "manual_note_possible",
        "related_emd_relevance": "emd_may_apply_later",
        "related_document_relevance": "pet_document_may_apply_later",
        "unit_type": "weight",
        "canonical_unit": "kg",
        "unit_aliases": ["kilogram", "kgs"],
        "conversion_notes": "Unit metadata only; no conversion engine runs.",
        "acquisition_ids": ["AKA-SMOKE-001"],
        "constraint_ids": ["OC-SMOKE-001"],
        "evidence_reference_ids": ["EVID-SMOKE-001"],
        "policy_reference_ids": ["POL-SMOKE-001"],
        "pricing_reference_ids": ["PRICE-SMOKE-001"],
        "capability_reference_ids": ["CAP-SMOKE-001"],
        "review_status": "in_review",
        "approval_status": "pending",
        "reviewer": "Normalisation Reviewer",
        "review_notes": "Governance metadata only.",
        "internal_notes": "No live evaluation, AI parsing, scraping, provider calls, or workers.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Airline knowledge normalisations collection is not registered as agency-owned metadata.")
    create_payload = AirlineKnowledgeNormalisationCreate(**normalisation_payload("agency-smoke", "AKN-SMOKE-MODEL"))
    record = AirlineKnowledgeNormalisation(**create_payload.model_dump(mode="json", exclude_none=True))
    if record.hierarchy_path != ["animal", "dog", "brachycephalic", "french_bulldog"]:
        raise AssertionError("Normalisation model did not preserve taxonomy hierarchy.")
    if "Frenchie" not in record.aliases or "PETC DOG" not in record.gds_terms:
        raise AssertionError("Normalisation model did not preserve aliases and terms.")
    if record.breed != "French Bulldog" or record.brachycephalic_flag is not True:
        raise AssertionError("Normalisation model did not preserve animal taxonomy.")
    if record.aircraft_family != "A320 Family" or record.cabin_family != "Premium Cabin":
        raise AssertionError("Normalisation model did not preserve aircraft/cabin taxonomy.")
    if record.service_domain != "animal_transport" or record.related_ssr_code != "PETC":
        raise AssertionError("Normalisation model did not preserve service taxonomy.")
    if record.acquisition_ids != ["AKA-SMOKE-001"] or record.constraint_ids != ["OC-SMOKE-001"]:
        raise AssertionError("Normalisation model did not preserve knowledge links.")
    if record.metadata_only is not True or record.live_evaluation_disabled is not True:
        raise AssertionError("Normalisation model is not metadata-only.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_knowledge_normalisations_id_unique",
        "airline_knowledge_normalisations_reference_unique",
        "airline_knowledge_normalisations_agency_status_lookup",
        "airline_knowledge_normalisations_agency_type_lookup",
        "airline_knowledge_normalisations_canonical_code_lookup",
        "airline_knowledge_normalisations_taxonomy_lookup",
        "airline_knowledge_normalisations_alias_lookup",
        "airline_knowledge_normalisations_airline_lookup",
        "airline_knowledge_normalisations_ssr_lookup",
        "airline_knowledge_normalisations_rfic_rfisc_lookup",
        "airline_knowledge_normalisations_animal_lookup",
        "airline_knowledge_normalisations_aircraft_taxonomy_lookup",
        "airline_knowledge_normalisations_service_taxonomy_lookup",
        "airline_knowledge_normalisations_unit_lookup",
        "airline_knowledge_normalisations_acquisition_lookup",
        "airline_knowledge_normalisations_constraint_lookup",
        "airline_knowledge_normalisations_evidence_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Airline knowledge normalisation index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    expected_methods = {
        "/api/platform/airline-knowledge-normalisation": {"get", "post"},
        "/api/platform/airline-knowledge-normalisation/summary": {"get"},
        "/api/platform/airline-knowledge-normalisation/{normalisation_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/airline-knowledge-normalisation": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-normalisation/summary": {"get"},
        "/api/agencies/{agency_id}/airline-knowledge-normalisation/{normalisation_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/airline-knowledge-normalisation",
        "/api/agencies/{agency_id}/airline-knowledge-normalisation/summary",
        "/api/agencies/{agency_id}/airline-knowledge-normalisation/{normalisation_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency normalisation route is not read-only: {path} {sorted(blocked_methods)}")
    for path in paths:
        if "airline-knowledge-normalisation" in path and any(term in path for term in ["evaluate", "execute", "score", "recommend"]):
            raise AssertionError(f"Live normalisation execution route should not exist: {path}")
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/airline-knowledge-normalisation"),
        (ROOT / "frontend/src/App.jsx", "/agency/knowledge-normalisation"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Airline Knowledge Normalisation"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge Normalisation"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeNormalisationPage.jsx", "Canonical Record"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeNormalisationPage.jsx", "Taxonomy Hierarchy"),
        (ROOT / "frontend/src/pages/platform/AirlineKnowledgeNormalisationPage.jsx", "Aircraft / Cabin Taxonomy"),
        (ROOT / "frontend/src/pages/agency/KnowledgeNormalisationPage.jsx", "Read-only canonical vocabulary metadata"),
        (ROOT / "docs/architecture/airline-knowledge-normalisation-foundation.md", "Airline Knowledge Normalisation Foundation"),
        (ROOT / "docs/architecture/airline-knowledge-normalisation-foundation.md", "Normalisation does not evaluate rules."),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Phase 50.3 adds the `airline_knowledge_normalisations` collection"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "50.3 Airline Operational Knowledge Normalisation"),
        (ROOT / "docs/architecture/operational-constraint-engine-foundation.md", "Phase 50.3 Airline Operational Knowledge Normalisation"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Phase 50.3 adds metadata-only Airline Operational Knowledge Normalisation"),
        (ROOT / "BUILD_PHASES.md", "Phase 50.3: Airline Operational Knowledge Normalisation Foundation"),
        (ROOT / "README.md", "Phase 50.3 Includes"),
        (ROOT / "docs/architecture/current-model-inventory.md", "airline_knowledge_normalisations"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/airline-knowledge-normalisation"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Airline knowledge normalisation"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Airline Knowledge Normalisation"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeNormalisationPage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeNormalisationPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeNormalisationPage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeNormalisationPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Airline Knowledge Normalisation" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Airline Knowledge Normalisation category: {categories}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Airline operational knowledge normalisation foundation built in Phase 50.3" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gaps missing Phase 50.3 built marker: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")
    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not next_phases.get("items") or next_phases["items"][0].get("phase") != "Phase 50.9":
        raise AssertionError(f"Next recommendations did not start with Phase 50.9: {next_phases}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_knowledge_normalisation_foundation") or {}
    for flag in [
        "airline_knowledge_normalisation_enabled",
        "airline_knowledge_normalisations_collection_enabled",
        "canonical_operational_vocabulary_enabled",
        "taxonomy_hierarchy_metadata_enabled",
        "aliases_terms_metadata_enabled",
        "applicability_metadata_enabled",
        "animal_taxonomy_metadata_enabled",
        "aircraft_cabin_taxonomy_metadata_enabled",
        "service_taxonomy_metadata_enabled",
        "unit_normalisation_metadata_enabled",
        "knowledge_links_metadata_enabled",
        "governance_metadata_enabled",
        "platform_airline_knowledge_normalisation_metadata_crud_enabled",
        "agency_airline_knowledge_normalisation_read_only_enabled",
        "platform_airline_knowledge_normalisation_ui_enabled",
        "agency_knowledge_normalisation_ui_enabled",
        "metadata_only",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Normalisation readiness missing flag {flag}: {section}")
    for flag in disabled_flags():
        if section.get(flag) is not True:
            raise AssertionError(f"Normalisation readiness missing disabled flag {flag}: {section}")
    if section.get("normalisation_statuses") != NORMALISATION_STATUSES:
        raise AssertionError(f"Readiness missing normalisation statuses: {section}")
    if section.get("normalisation_types") != NORMALISATION_TYPES:
        raise AssertionError(f"Readiness missing normalisation types: {section}")
    for count_key in [
        "airline_knowledge_normalisation_count",
        "airline_knowledge_normalisation_status_counts",
        "airline_knowledge_normalisation_type_counts",
        "airline_knowledge_normalisation_review_status_counts",
        "airline_knowledge_normalisation_approval_status_counts",
        "airline_knowledge_normalisation_hierarchy_count",
        "airline_knowledge_normalisation_alias_count",
        "airline_knowledge_normalisation_applicability_count",
        "airline_knowledge_normalisation_animal_taxonomy_count",
        "airline_knowledge_normalisation_aircraft_cabin_taxonomy_count",
        "airline_knowledge_normalisation_service_taxonomy_count",
        "airline_knowledge_normalisation_unit_count",
        "airline_knowledge_normalisation_knowledge_link_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Normalisation readiness missing count: {count_key}")
    if not set(REVIEW_STATUSES).issubset(set((section.get("airline_knowledge_normalisation_review_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing review statuses: {section}")
    if not set(APPROVAL_STATUSES).issubset(set((section.get("airline_knowledge_normalisation_approval_status_counts") or {}).keys())):
        raise AssertionError(f"Readiness missing approval statuses: {section}")


def verify_no_forbidden_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/airline_knowledge_normalisation_service.py",
        ROOT / "backend/routers/platform_airline_knowledge_normalisation.py",
        ROOT / "backend/routers/agency_airline_knowledge_normalisation.py",
        ROOT / "frontend/src/pages/platform/AirlineKnowledgeNormalisationPage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgeNormalisationPage.jsx",
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
        "score_feasibility(",
        "calculate_price(",
        "execute_normalisation(",
        "evaluate_normalisation(",
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden implementation term: {term}")


def assert_normalisation_shape(item: dict, agency_view: bool = False) -> None:
    required_fields = [
        "id",
        "agency_id",
        "normalisation_reference",
        "normalisation_status",
        "normalisation_type",
        "canonical_code",
        "canonical_name",
        "taxonomy_domain",
        "taxonomy_family",
        "taxonomy_variant",
        "parent_canonical_id",
        "hierarchy_path",
        "hierarchy_level",
        "aliases",
        "abbreviations",
        "airline_specific_terms",
        "gds_terms",
        "commercial_terms",
        "operational_terms",
        "airline_codes",
        "ssr_codes",
        "rfic_codes",
        "rfisc_codes",
        "species",
        "breed",
        "brachycephalic_flag",
        "aircraft_family",
        "cabin_family",
        "service_domain",
        "service_family",
        "related_ssr_code",
        "unit_type",
        "canonical_unit",
        "acquisition_ids",
        "constraint_ids",
        "evidence_reference_ids",
        "review_status",
        "approval_status",
    ]
    for field in required_fields:
        if field not in item:
            raise AssertionError(f"Normalisation field missing {field}: {item}")
    if item.get("metadata_only") is not True:
        raise AssertionError(f"Normalisation is not metadata-only: {item}")
    if item.get("hierarchy_path") != ["animal", "dog", "brachycephalic", "french_bulldog"]:
        raise AssertionError(f"Taxonomy hierarchy did not persist: {item}")
    if "Frenchie" not in (item.get("aliases") or []) or "PETC DOG" not in (item.get("gds_terms") or []):
        raise AssertionError(f"Aliases did not persist: {item}")
    if item.get("species") != "Dog" or item.get("breed") != "French Bulldog":
        raise AssertionError(f"Animal taxonomy did not persist: {item}")
    if item.get("aircraft_family") != "A320 Family" or item.get("cabin_family") != "Premium Cabin":
        raise AssertionError(f"Aircraft/cabin taxonomy did not persist: {item}")
    if item.get("service_domain") != "animal_transport" or item.get("related_ssr_code") != "PETC":
        raise AssertionError(f"Service taxonomy did not persist: {item}")
    if item.get("acquisition_ids") != ["AKA-SMOKE-001"] or item.get("constraint_ids") != ["OC-SMOKE-001"]:
        raise AssertionError(f"Knowledge links did not persist: {item}")
    if agency_view and item.get("read_only") is not True:
        raise AssertionError(f"Agency normalisation should be read-only: {item}")


def assert_summary_shape(payload: dict, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary did not preserve agency id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "by_normalisation_status",
        "by_normalisation_type",
        "by_review_status",
        "by_approval_status",
        "hierarchy_count",
        "alias_count",
        "applicability_count",
        "animal_taxonomy_count",
        "aircraft_cabin_taxonomy_count",
        "service_taxonomy_count",
        "unit_normalisation_count",
        "knowledge_link_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Normalisation summary missing {key}: {payload}")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    created = post(PLATFORM_BASE, normalisation_payload(agency_id), OWNER_HEADERS, 201)
    assert_disabled_response(created)
    normalisation = created.get("airline_knowledge_normalisation") or {}
    assert_normalisation_shape(normalisation)
    normalisation_id = normalisation.get("id")
    if not normalisation_id:
        raise AssertionError(f"Normalisation id missing: {created}")

    updated = put(
        f"{PLATFORM_BASE}/{normalisation_id}",
        {
            "normalisation_status": "approved",
            "review_status": "reviewed",
            "approval_status": "approved",
            "approved_by": "Normalisation Approver",
            "approved_at": "2028-03-04T09:30:00Z",
            "review_notes": "Approved metadata only; no live evaluation.",
            "internal_notes": "Updated normalisation metadata only.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_normalisation = updated.get("airline_knowledge_normalisation") or {}
    assert_normalisation_shape(updated_normalisation)
    if updated_normalisation.get("review_status") != "reviewed" or updated_normalisation.get("approval_status") != "approved":
        raise AssertionError(f"Normalisation update did not persist governance metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "normalisation_status=approved",
        "normalisation_type=animal_taxonomy",
        "canonical_code=ANIMAL_DOG_FRENCH_BULLDOG",
        "taxonomy_domain=animal",
        "taxonomy_family=dog",
        "taxonomy_variant=breed",
        "airline=LH",
        "ssr_code=PETC",
        "rfic=C",
        "rfisc=0BT",
        "review_status=reviewed",
        "approval_status=approved",
    ]:
        filtered = get(f"{PLATFORM_BASE}?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == normalisation_id for item in filtered.get("items") or []):
            raise AssertionError(f"Normalisation filter {filter_query} missing created record: {filtered}")

    platform_summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"{PLATFORM_BASE}/{normalisation_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_normalisation_shape(platform_detail.get("airline_knowledge_normalisation") or {})

    agency_list = get(
        f"/api/agencies/{agency_id}/airline-knowledge-normalisation?normalisation_status=approved&normalisation_type=animal_taxonomy&canonical_code=ANIMAL_DOG_FRENCH_BULLDOG&taxonomy_domain=animal&taxonomy_family=dog&taxonomy_variant=breed&airline=LH&ssr_code=PETC&rfic=C&rfisc=0BT&review_status=reviewed&approval_status=approved",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency normalisation list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == normalisation_id), None)
    if not agency_item:
        raise AssertionError(f"Agency normalisation list missing created record: {agency_list}")
    assert_normalisation_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/airline-knowledge-normalisation/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency normalisation summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/airline-knowledge-normalisation/{normalisation_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency normalisation detail should be read-only: {agency_detail}")
    assert_normalisation_shape(agency_detail.get("airline_knowledge_normalisation") or {}, agency_view=True)

    request("POST", f"/api/agencies/{agency_id}/airline-knowledge-normalisation", normalisation_payload(agency_id, "AKN-AGENCY-FORBIDDEN"), OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/airline-knowledge-normalisation/{normalisation_id}", {"review_status": "rejected"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/airline-knowledge-normalisation/{normalisation_id}", {}, OWNER_HEADERS, 405)

    archived = request("DELETE", f"{PLATFORM_BASE}/{normalisation_id}", None, OWNER_HEADERS)[1]
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
    print("Phase 50.3 airline knowledge normalisation foundation smoke passed.")


if __name__ == "__main__":
    main()
