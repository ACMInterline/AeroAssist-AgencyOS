#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    AirlineBaggageResponsibilityRule,
    AirlineCarrierRelationship,
    AirlineCodeshareRule,
    AirlineInterlineAgreementProfile,
    AirlineInterlineEmdRule,
    AirlineOperatingCarrierPolicyRule,
    AirlineServiceResponsibilityRule,
    AirlineThroughCheckRule,
    AirlineValidatingCarrierRule,
)
from services.interline_codeshare_intelligence_service import (
    CARRIER_ROLES,
    ENTITY_CONFIG,
    INTERLINE_INTELLIGENCE_COLLECTIONS,
    JOURNEY_CAPABILITIES,
    PHASE_LABEL,
    RELATIONSHIP_TYPES,
    RESPONSIBILITY_AREAS,
    RULE_STATUSES,
    InterlineCodeshareIntelligenceService,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_3_journey_comparison_client_presentation_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/interline-codeshare-intelligence"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, value: str) -> None:
    if value not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {value}")


def reject_text(path: Path, value: str) -> None:
    if value.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains prohibited execution text: {value}")


def assert_agency_safe(value: object) -> None:
    restricted = {"internal_notes", "visible_agency_ids", "legacy_interline_agreement_id", "legacy_emd_interline_rule_id"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency interline response leaked restricted field {key}")
            assert_agency_safe(child)
    elif isinstance(value, list):
        for child in value:
            assert_agency_safe(child)


def verify_models_collections_indexes_and_taxonomies() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 55.6 marker: {PHASE_LABEL}")
    expected_collections = {
        "airline_carrier_relationships",
        "airline_interline_agreement_profiles",
        "airline_codeshare_rules",
        "airline_operating_carrier_policy_rules",
        "airline_validating_carrier_rules",
        "airline_through_check_rules",
        "airline_baggage_responsibility_rules",
        "airline_service_responsibility_rules",
        "airline_interline_emd_rules",
    }
    if set(INTERLINE_INTELLIGENCE_COLLECTIONS) != expected_collections or not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Phase 55.6 collection registration is incomplete.")
    if set(CARRIER_ROLES) != {"marketing_carrier", "operating_carrier", "validating_carrier", "ticketing_carrier", "plating_carrier", "handling_carrier"}:
        raise AssertionError("Carrier role taxonomy is incomplete.")
    if set(RELATIONSHIP_TYPES) != {"codeshare", "interline", "spa", "alliance", "wet_lease", "franchise", "regional_affiliate"}:
        raise AssertionError("Commercial relationship taxonomy is incomplete.")
    if not {"supported", "unsupported", "conditional", "manual_only", "unknown"}.issubset(set(RULE_STATUSES)):
        raise AssertionError("Rule states do not preserve supported, unsupported, conditional, manual, and unknown outcomes.")
    if not {"policy_owner", "ssr_request_owner", "service_confirmation_owner", "ancillary_pricing_owner", "ticket_issue_owner", "emd_issuer", "airport_fulfillment_owner", "baggage_rule_owner", "medical_pet_rule_owner", "contact_desk_owner"}.issubset(set(RESPONSIBILITY_AREAS)):
        raise AssertionError("Operational responsibility areas are incomplete.")
    if not {"through_check_in", "through_baggage", "seat_assignment_continuity", "special_service_continuity", "emd_interline_support"}.issubset(set(JOURNEY_CAPABILITIES)):
        raise AssertionError("Journey capability dimensions are incomplete.")
    if len(ENTITY_CONFIG) != 9:
        raise AssertionError("All Phase 55.6 governed entity families are not registered.")

    relationship = AirlineCarrierRelationship(relationship_reference="ACR-MODEL", carrier_a_code="LH", carrier_b_code="UA", relationship_type="codeshare")
    agreement = AirlineInterlineAgreementProfile(agreement_profile_reference="AIA-MODEL", airline_code="LH", partner_airline_code="UA")
    codeshare = AirlineCodeshareRule(codeshare_rule_reference="ACRUL-MODEL", marketing_carrier_code="LH", operating_carrier_code="UA")
    operating = AirlineOperatingCarrierPolicyRule(operating_policy_rule_reference="AOP-MODEL", operating_carrier_code="UA")
    validating = AirlineValidatingCarrierRule(validating_carrier_rule_reference="AVC-MODEL", validating_carrier_code="LH")
    through = AirlineThroughCheckRule(through_check_rule_reference="ATC-MODEL", airline_code="LH", partner_airline_code="UA")
    baggage = AirlineBaggageResponsibilityRule(baggage_responsibility_rule_reference="ABR-MODEL", operating_carrier_code="UA")
    service = AirlineServiceResponsibilityRule(service_responsibility_rule_reference="ASR-MODEL", operating_carrier_code="UA", service_family="pets", service_code="PETC")
    emd = AirlineInterlineEmdRule(interline_emd_rule_reference="AER-MODEL", airline_code="UA", partner_airline_code="LH")
    if not all(item.id and item.metadata_only for item in [relationship, agreement, codeshare, operating, validating, through, baggage, service, emd]):
        raise AssertionError("Phase 55.6 model defaults are incomplete.")
    if not emd.emd_execution_disabled:
        raise AssertionError("Interline EMD model did not preserve the no-execution boundary.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_carrier_relationships_agency_carriers_lookup",
        "airline_interline_agreement_profiles_agency_pair_lookup",
        "airline_codeshare_rules_agency_carriers_lookup",
        "airline_operating_carrier_policy_rules_service_lookup",
        "airline_validating_carrier_rules_stock_plating_lookup",
        "airline_through_check_rules_status_lookup",
        "airline_baggage_responsibility_rules_owner_status_lookup",
        "airline_service_responsibility_rules_service_lookup",
        "airline_interline_emd_rules_rfic_rfisc_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


async def verify_service_behavior() -> None:
    db = Database()
    service = InterlineCodeshareIntelligenceService(db)
    agency_id = "agency-interline-smoke"
    user = {"id": "platform-owner", "email": "owner@aeroassist.dev"}
    visible = {"agency_id": agency_id, "publication_status": "published", "approval_status": "approved", "agency_visibility_status": "selected_agencies", "visible_agency_ids": [agency_id], "freshness_status": "current", "confidence": "high"}

    relationship = (await service.create_record("relationships", {"relationship_reference": "ACR-LH-UA", "carrier_a_code": "LH", "carrier_b_code": "UA", "relationship_type": "codeshare", "relationship_status": "supported", "marketing_carrier_code": "LH", "operating_carrier_code": "UA", "evidence_link_ids": ["evidence-relationship"], **visible}, user))["item"]
    await service.create_record("interline-agreements", {"airline_code": "LH", "partner_airline_code": "UA", "relationship_id": relationship["id"], "agreement_status": "supported", "ticketing_status": "supported", "through_check_status": "conditional", "through_baggage_status": "supported", "special_service_status": "conditional", "emd_interline_status": "conditional", "ticket_stock_scope": ["220"], "evidence_link_ids": ["evidence-interline"], **visible}, user)
    codeshare = (await service.create_record("codeshare-rules", {"marketing_carrier_code": "LH", "operating_carrier_code": "UA", "relationship_id": relationship["id"], "rule_status": "supported", "policy_owner_carrier_code": "UA", "ssr_request_owner_carrier_code": "LH", "service_confirmation_owner_carrier_code": "UA", "ancillary_pricing_owner_carrier_code": "LH", "emd_issuer_carrier_code": "LH", "airport_fulfillment_owner_carrier_code": "UA", "baggage_rule_owner_carrier_code": "UA", "medical_pet_rule_owner_carrier_code": "UA", "route_scope": ["FRA-IAD"], "evidence_link_ids": ["evidence-codeshare"], **visible}, user))["item"]
    await service.create_record("operating-carrier-rules", {"marketing_carrier_code": "LH", "operating_carrier_code": "UA", "rule_status": "supported", "policy_owner_carrier_code": "UA", "medical_rule_owner_carrier_code": "UA", "pet_rule_owner_carrier_code": "UA", "service_confirmation_owner_carrier_code": "UA", "airport_fulfillment_owner_carrier_code": "UA", "service_code_scope": ["PETC"], "route_scope": ["FRA-IAD"], "evidence_link_ids": ["evidence-operating"], **visible}, user)
    await service.create_record("validating-carrier-rules", {"validating_carrier_code": "LH", "marketing_carrier_code": "LH", "operating_carrier_code": "UA", "ticketing_carrier_code": "LH", "plating_carrier_code": "LH", "ticket_stock": "220", "rule_status": "supported", "ticket_issue_owner_carrier_code": "LH", "exchange_owner_carrier_code": "LH", "refund_owner_carrier_code": "LH", "disruption_owner_carrier_code": "UA", "route_scope": ["FRA-IAD"], "evidence_link_ids": ["evidence-validating"], **visible}, user)
    await service.create_record("through-check-rules", {"airline_code": "LH", "partner_airline_code": "UA", "relationship_id": relationship["id"], "rule_status": "conditional", "through_check_in_status": "supported", "through_baggage_status": "supported", "seat_assignment_continuity_status": "conditional", "special_service_continuity_status": "conditional", "airport_handling_owner_carrier_code": "UA", "evidence_link_ids": ["evidence-through"], **visible}, user)
    await service.create_record("baggage-rules", {"marketing_carrier_code": "LH", "operating_carrier_code": "UA", "validating_carrier_code": "LH", "rule_status": "supported", "baggage_rule_owner_carrier_code": "UA", "baggage_collection_owner_carrier_code": "UA", "baggage_transfer_owner_carrier_code": "UA", "through_baggage_status": "supported", "route_scope": ["FRA-IAD"], "evidence_link_ids": ["evidence-baggage"], **visible}, user)
    await service.create_record("service-responsibility-rules", {"marketing_carrier_code": "LH", "operating_carrier_code": "UA", "validating_carrier_code": "LH", "service_family": "pets", "service_code": "PETC", "rule_status": "supported", "policy_owner_carrier_code": "UA", "ssr_request_owner_carrier_code": "LH", "service_confirmation_owner_carrier_code": "UA", "pricing_owner_carrier_code": "LH", "emd_issuer_carrier_code": "LH", "airport_fulfillment_owner_carrier_code": "UA", "contact_desk_owner_carrier_code": "UA", "route_scope": ["FRA-IAD"], "recommended_action": "Confirm PETC with operating carrier.", "evidence_link_ids": ["evidence-service"], **visible}, user)
    await service.create_record("interline-emd-rules", {"airline_code": "UA", "partner_airline_code": "LH", "validating_carrier_code": "LH", "issuing_carrier_code": "LH", "operating_carrier_code": "UA", "rule_status": "conditional", "emd_a_status": "conditional", "emd_s_status": "supported", "interline_emd_status": "conditional", "emd_issuer_carrier_code": "LH", "fulfillment_owner_carrier_code": "UA", "rfic_scope": ["C"], "rfisc_scope": ["0B5"], "service_scope": ["PETC"], "evidence_link_ids": ["evidence-emd"], **visible}, user)
    await service.create_record("relationships", {"carrier_a_code": "LH", "carrier_b_code": "XX", "relationship_type": "interline", "relationship_status": "unknown", "publication_status": "draft", "internal_notes": "Unpublished relationship"}, user)

    updated = await service.update_record("codeshare-rules", codeshare["id"], {"confidence": "official"}, user)
    if updated["item"]["confidence"] != "official":
        raise AssertionError("Codeshare rule update failed.")
    if (await service.get_record("relationships", relationship["id"]))["item"]["relationship_type"] != "codeshare":
        raise AssertionError("Carrier relationship detail failed.")

    await db.collection("operational_constraints").insert_one({"id": "constraint-interline", "agency_id": agency_id, "airline_code": "UA"})
    await db.collection("passenger_service_feasibilities").insert_one({"id": "feasibility-interline", "agency_id": agency_id, "operating_carrier": "UA"})
    await db.collection("airline_recommendations").insert_one({"id": "recommendation-interline", "agency_id": agency_id, "airline_codes": ["LH", "UA"]})
    await db.collection("intelligent_offer_builder_packages").insert_one({"id": "offer-intelligence-interline", "agency_id": agency_id, "marketing_carrier": "LH"})

    evaluation = await service.evaluate_itinerary({
        "travel_date": "2026-10-01",
        "segments": [
            {"segment_reference": "SEG-1", "marketing_carrier": "LH", "operating_carrier": "LH", "validating_carrier": "LH", "origin": "SOF", "destination": "FRA"},
            {"segment_reference": "SEG-2", "marketing_carrier": "LH", "operating_carrier": "UA", "validating_carrier": "LH", "ticketing_carrier": "LH", "plating_carrier": "LH", "handling_carrier": "UA", "origin": "FRA", "destination": "IAD", "service_requirements": ["PETC"]},
        ],
    }, agency_id=agency_id, agency_safe=True)
    second = evaluation["segments"][1]
    if second["responsibilities"]["policy_owner"] != "UA" or second["responsibilities"]["ssr_request_owner"] != "LH":
        raise AssertionError(f"Policy or SSR ownership was not resolved: {second}")
    if second["responsibilities"]["emd_issuer"] != "LH" or second["responsibilities"]["baggage_rule_owner"] != "UA":
        raise AssertionError("EMD or baggage responsibility was not resolved.")
    if second["journey_capabilities"]["through_check_in"] != "supported" or second["journey_capabilities"]["through_baggage"] != "supported":
        raise AssertionError("Multi-segment through-check or baggage intelligence was not applied.")
    if evaluation["foundation_context"]["operational_constraint_ids"] != ["constraint-interline"]:
        raise AssertionError("Operational constraint foundation was not linked by reference.")
    if not evaluation["manual_review_requirements"]:
        raise AssertionError("Conditional and unresolved responsibility did not produce manual review.")
    assert_agency_safe(evaluation)

    unknown = await service.evaluate_itinerary({"segments": [{"marketing_carrier": "ZZ", "operating_carrier": "YY", "origin": "AAA", "destination": "BBB"}]}, agency_id=agency_id, agency_safe=True)
    if unknown["evaluation_status"] != "manual_review_required" or not unknown["warnings"]:
        raise AssertionError("Unknown carrier combination did not remain an explicit manual-review outcome.")
    await service.create_record("relationships", {"carrier_a_code": "BA", "carrier_b_code": "AA", "relationship_type": "interline", "relationship_status": "unsupported", "evidence_link_ids": ["evidence-unsupported"], **visible}, user)
    unsupported = await service.evaluate_itinerary({"segments": [{"marketing_carrier": "BA", "operating_carrier": "AA", "origin": "LHR", "destination": "JFK"}]}, agency_id=agency_id, agency_safe=True)
    if unsupported["evaluation_status"] != "unsupported_combination" or not unsupported["unsupported_combinations"]:
        raise AssertionError("Unsupported interline combination was not preserved and surfaced.")
    agency = await service.agency_dashboard(agency_id, airline_code="LH")
    if any(item.get("carrier_b_code") == "XX" for item in agency["relationships"]):
        raise AssertionError("Unpublished relationship leaked to agency visibility.")
    assert_agency_safe(agency)
    if (await service.agency_dashboard("foreign-agency", airline_code="LH"))["relationships"]:
        raise AssertionError("Agency-scoped interline records leaked across tenants.")


def verify_routes_ui_docs_and_readiness(paths: dict) -> None:
    expected = {
        "/api/platform/interline-codeshare-intelligence": {"get"},
        "/api/platform/interline-codeshare-intelligence/summary": {"get"},
        "/api/platform/interline-codeshare-intelligence/filters": {"get"},
        "/api/platform/interline-codeshare-intelligence/evaluate": {"post"},
        "/api/platform/interline-codeshare-intelligence/{entity_type}": {"get", "post"},
        "/api/platform/interline-codeshare-intelligence/{entity_type}/{record_id}": {"get", "put"},
        "/api/agencies/{agency_id}/interline-codeshare-advisor": {"get"},
        "/api/agencies/{agency_id}/interline-codeshare-advisor/summary": {"get"},
        "/api/agencies/{agency_id}/interline-codeshare-advisor/evaluate": {"post"},
        "/api/agencies/{agency_id}/interline-codeshare-advisor/{entity_type}": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    agency_record_path = "/api/agencies/{agency_id}/interline-codeshare-advisor/{entity_type}"
    if set(paths.get(agency_record_path, {})) & {"post", "put", "patch", "delete"}:
        raise AssertionError("Agency carrier intelligence record routes expose mutation.")

    checks = [
        ("frontend/src/App.jsx", "/platform/interline-codeshare-intelligence"),
        ("frontend/src/App.jsx", "/agency/interline-codeshare-advisor"),
        ("frontend/src/lib/moduleCatalog.js", "Interline & Codeshare Advisor"),
        ("frontend/src/pages/platform/InterlineCodeshareIntelligencePage.jsx", "Special-service responsibility matrix"),
        ("frontend/src/pages/agency/InterlineCodeshareAdvisorPage.jsx", "Responsibility explanation"),
        ("docs/architecture/interline-codeshare-operating-carrier-intelligence-foundation.md", "Missing evidence never causes a guessed owner"),
        ("BUILD_PHASES.md", "Implemented Phase 55.6"),
        ("README.md", "Phase 55.6 Interline Codeshare and Operating Carrier Intelligence"),
        ("docs/architecture/current-model-inventory.md", "airline_service_responsibility_rules"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/interline-codeshare-intelligence"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.6 Alignment"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.6 Interline Codeshare and Operating Carrier Intelligence"),
        ("backend/services/blueprint_adoption_service.py", "Interline Codeshare And Operating Carrier Intelligence"),
        ("backend/services/airline_policy_evidence_governance_service.py", '"service_responsibility_rule": "airline_service_responsibility_rules"'),
        ("backend/services/airline_knowledge_versioning_service.py", '"codeshare_rule": "airline_codeshare_rules"'),
        ("backend/services/saas_subscription_service.py", "interline_codeshare_intelligence"),
    ]
    for relative, value in checks:
        require_text(ROOT / relative, value)

    health = get("/api/health")
    readiness = get("/api/readiness")
    if health.get("phase") != EXPECTED_PHASE or readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Phase 55.6 marker is not active: {health.get('phase')} / {readiness.get('phase')}")
    section = readiness.get("interline_codeshare_operating_carrier_intelligence_foundation") or {}
    for key in [
        "interline_codeshare_operating_carrier_intelligence_enabled",
        "carrier_role_mapping_enabled",
        "policy_ownership_intelligence_enabled",
        "ssr_responsibility_intelligence_enabled",
        "emd_responsibility_intelligence_enabled",
        "baggage_responsibility_intelligence_enabled",
        "multi_segment_advisory_evaluation_enabled",
        "unknown_state_preserved",
        "unsupported_certainty_disabled",
        "legacy_interline_truth_preserved",
        "operational_constraint_integration_enabled",
        "feasibility_integration_enabled",
        "recommendation_integration_enabled",
        "offer_intelligence_integration_enabled",
        "agency_published_read_only",
        "provider_connectivity_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.6 flag {key}: {section}")
    for key in ["interline_intelligence_collection_counts", "carrier_relationship_count", "interline_agreement_profile_count", "responsibility_rule_count", "published_interline_record_count", "unknown_interline_record_count", "manual_review_interline_record_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.6 counter {key}")


def verify_live_routes() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.6 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    token = uuid4().hex[:8].upper()
    marketing = f"M{token[:1]}"
    operating = f"O{token[1:2]}"
    visibility = {"agency_id": agency_id, "publication_status": "published", "approval_status": "approved", "agency_visibility_status": "selected_agencies", "visible_agency_ids": [agency_id], "freshness_status": "current", "confidence": "high"}
    relationship = post(f"{PLATFORM_BASE}/relationships", {"relationship_reference": f"ACR-{token}", "carrier_a_code": marketing, "carrier_b_code": operating, "relationship_type": "codeshare", "relationship_status": "supported", "marketing_carrier_code": marketing, "operating_carrier_code": operating, **visibility}, OWNER_HEADERS, 201)["item"]
    rule = post(f"{PLATFORM_BASE}/codeshare-rules", {"codeshare_rule_reference": f"ACRUL-{token}", "marketing_carrier_code": marketing, "operating_carrier_code": operating, "relationship_id": relationship["id"], "rule_status": "supported", "policy_owner_carrier_code": operating, "ssr_request_owner_carrier_code": marketing, "service_confirmation_owner_carrier_code": operating, **visibility}, OWNER_HEADERS, 201)["item"]
    if put(f"{PLATFORM_BASE}/codeshare-rules/{rule['id']}", {"confidence": "official"}, OWNER_HEADERS).get("item", {}).get("confidence") != "official":
        raise AssertionError("Live codeshare rule update failed.")
    dashboard = get(f"{PLATFORM_BASE}?agency_id={agency_id}&airline_code={marketing}", OWNER_HEADERS)
    if dashboard.get("summary", {}).get("relationship_count") != 1:
        raise AssertionError("Platform carrier relationship dashboard omitted the live record.")
    agency = get(f"/api/agencies/{agency_id}/interline-codeshare-advisor?airline_code={marketing}", OWNER_HEADERS)
    if agency.get("read_only") is not True or len(agency.get("relationships") or []) != 1:
        raise AssertionError("Agency carrier intelligence projection is incomplete.")
    assert_agency_safe(agency)
    evaluation = post(f"/api/agencies/{agency_id}/interline-codeshare-advisor/evaluate", {"segments": [{"marketing_carrier": marketing, "operating_carrier": operating, "origin": "SOF", "destination": "FRA"}]}, OWNER_HEADERS)
    if evaluation.get("segments", [{}])[0].get("responsibilities", {}).get("policy_owner") != operating:
        raise AssertionError("Agency itinerary advisor did not resolve the published policy owner.")
    request("POST", f"/api/agencies/{agency_id}/interline-codeshare-advisor/relationships", {}, OWNER_HEADERS, 405)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    if len(agencies) > 1:
        foreign = get(f"/api/agencies/{agencies[1]['id']}/interline-codeshare-advisor?airline_code={marketing}", OWNER_HEADERS)
        if foreign.get("relationships"):
            raise AssertionError("Agency-scoped carrier intelligence leaked across tenants.")


def verify_safety() -> None:
    flags = InterlineCodeshareIntelligenceService(None).safety_flags()  # type: ignore[arg-type]
    if any(value is not True for value in flags.values()):
        raise AssertionError(f"Interline intelligence safety flag is disabled: {flags}")
    service_path = ROOT / "backend/services/interline_codeshare_intelligence_service.py"
    for forbidden in ["requests.get(", "requests.post(", "httpx.", "openai", "backgroundtasks", "asyncio.create_task", ".delete_one(", ".delete_many(", "issue_ticket(", "issue_emd(", "create_pnr("]:
        reject_text(service_path, forbidden)


def main() -> int:
    verify_models_collections_indexes_and_taxonomies()
    verify_safety()
    asyncio.run(verify_service_behavior())
    paths = get("/openapi.json").get("paths") or {}
    verify_routes_ui_docs_and_readiness(paths)
    verify_live_routes()
    print("Phase 55.6 interline codeshare and operating carrier intelligence foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
