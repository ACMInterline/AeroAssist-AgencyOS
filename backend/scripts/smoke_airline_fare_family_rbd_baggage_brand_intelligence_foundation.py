#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    AirlineBaggageAllowanceRule,
    AirlineBaggageException,
    AirlineBookingClassMapping,
    AirlineBrandComparisonProfile,
    AirlineCommercialBundle,
    AirlineFareBrandAttribute,
    AirlineFareFamily,
    AirlineFareFamilyEvidenceLink,
)
from services.airline_fare_family_brand_intelligence_service import (
    ALLOWANCE_STATUSES,
    ATTRIBUTE_STATUSES,
    BAGGAGE_CONCEPTS,
    COMMERCIAL_ATTRIBUTE_CODES,
    ENTITY_CONFIG,
    FARE_BRAND_INTELLIGENCE_COLLECTIONS,
    MAPPING_STATUSES,
    PHASE_LABEL,
    AirlineFareFamilyBrandIntelligenceService,
)
from services.intelligent_offer_builder_service import IntelligentOfferBuilderService
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_0_canonical_journey_itinerary_representation_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/fare-brand-intelligence"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, value: str) -> None:
    if value not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {value}")


def reject_text(path: Path, value: str) -> None:
    if value.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains prohibited execution text: {value}")


def assert_agency_safe(value: object) -> None:
    restricted = {
        "internal_notes",
        "visible_agency_ids",
        "source_metadata_json",
        "metadata",
        "legacy_rbd_matrix_row_id",
        "evidence_source_id",
        "evidence_artifact_id",
        "evidence_assertion_id",
        "evidence_link_id",
        "evidence_link_ids",
        "internal_column_notes",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency fare-brand response leaked restricted field {key}")
            assert_agency_safe(child)
    elif isinstance(value, list):
        for child in value:
            assert_agency_safe(child)


def verify_models_collections_indexes_and_taxonomies() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 55.7 marker: {PHASE_LABEL}")
    expected_collections = {
        "airline_fare_families",
        "airline_fare_brand_attributes",
        "airline_booking_class_mappings",
        "airline_baggage_allowance_rules",
        "airline_baggage_exceptions",
        "airline_commercial_bundles",
        "airline_fare_family_evidence_links",
        "airline_brand_comparison_profiles",
    }
    if set(FARE_BRAND_INTELLIGENCE_COLLECTIONS) != expected_collections:
        raise AssertionError("Phase 55.7 collection constants are incomplete.")
    if not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Phase 55.7 agency-aware collection registration is incomplete.")
    if len(ENTITY_CONFIG) != 8:
        raise AssertionError("All governed fare-brand entity families are not registered.")
    if not {"known", "variable", "unknown"}.issubset(set(MAPPING_STATUSES)):
        raise AssertionError("RBD mapping uncertainty states are incomplete.")
    if not {"piece", "weight", "hybrid", "unknown"}.issubset(set(BAGGAGE_CONCEPTS)):
        raise AssertionError("Baggage concepts are incomplete.")
    if not {"known", "conditional", "variable", "unknown"}.issubset(set(ALLOWANCE_STATUSES)):
        raise AssertionError("Baggage allowance states are incomplete.")
    required_attributes = {
        "seat_selection",
        "changeability",
        "refundability",
        "same_day_change",
        "priority",
        "lounge",
        "meals",
        "fast_track",
        "mileage_accrual",
        "no_show_conditions",
        "ancillary_inclusion",
    }
    if set(COMMERCIAL_ATTRIBUTE_CODES) != required_attributes or "conditional" not in ATTRIBUTE_STATUSES:
        raise AssertionError("Commercial attribute taxonomy is incomplete.")

    family = AirlineFareFamily(airline_id="airline-model", family_code="FLEX", family_name="Flex")
    attribute = AirlineFareBrandAttribute(attribute_reference="AFA-MODEL", airline_code="LH", fare_family_id=family.id, attribute_code="changeability", attribute_label="Changes")
    mapping = AirlineBookingClassMapping(booking_class_mapping_reference="ABM-MODEL", airline_code="LH", rbd_code="Y")
    baggage = AirlineBaggageAllowanceRule(baggage_rule_reference="ABG-MODEL", airline_code="LH")
    exception = AirlineBaggageException(baggage_exception_reference="ABX-MODEL", airline_code="LH", exception_type="route")
    bundle = AirlineCommercialBundle(commercial_bundle_reference="ACB-MODEL", airline_code="LH", bundle_code="FLEX", bundle_name="Flex")
    evidence = AirlineFareFamilyEvidenceLink(fare_family_evidence_reference="AFE-MODEL", airline_code="LH", target_type="fare-families", target_id=family.id)
    comparison = AirlineBrandComparisonProfile(comparison_profile_reference="ABC-MODEL", profile_name="Economy brands")
    if not all(item.id and item.metadata_only for item in [family, attribute, mapping, baggage, exception, bundle, evidence, comparison]):
        raise AssertionError("Phase 55.7 model defaults are incomplete.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_fare_families_agency_airline_brand_lookup",
        "airline_fare_brand_attributes_agency_family_lookup",
        "airline_booking_class_mappings_agency_rbd_lookup",
        "airline_baggage_allowance_rules_context_lookup",
        "airline_baggage_exceptions_type_status_lookup",
        "airline_commercial_bundles_family_brand_lookup",
        "airline_fare_family_evidence_links_target_lookup",
        "airline_brand_comparison_profiles_scope_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


async def verify_service_behavior() -> None:
    db = Database()
    service = AirlineFareFamilyBrandIntelligenceService(db)
    agency_id = "agency-fare-brand-smoke"
    user = {"id": "platform-owner", "email": "owner@aeroassist.dev"}
    visible = {
        "agency_id": agency_id,
        "publication_status": "published",
        "approval_status": "approved",
        "agency_visibility_status": "selected_agencies",
        "visible_agency_ids": [agency_id],
        "freshness_status": "current",
        "confidence": "high",
    }
    await db.collection("airline_profiles").insert_one({"id": "airline-lh", "airline_code": "LH", "iata_code": "LH"})

    basic = (await service.create_record("fare-families", {
        "airline_id": "airline-lh",
        "airline_code": "LH",
        "family_code": "ECOLIGHT",
        "family_name": "Economy Light",
        "cabin": "economy",
        "display_order": 10,
        "distribution_channel_scope": ["amadeus", "direct_website"],
        "evidence_link_ids": ["evidence-family-light"],
        **visible,
    }, user))["item"]
    flex = (await service.create_record("fare-families", {
        "airline_id": "airline-lh",
        "airline_code": "LH",
        "family_code": "ECOFLEX",
        "family_name": "Economy Flex",
        "parent_fare_family_id": basic["id"],
        "cabin": "economy",
        "display_order": 20,
        "distribution_channel_scope": ["amadeus", "direct_website"],
        "evidence_link_ids": ["evidence-family-flex"],
        **visible,
    }, user))["item"]
    if flex["hierarchy_level"] != 1 or flex["parent_family_code"] != "ECOLIGHT":
        raise AssertionError("Fare-family hierarchy was not normalized.")

    for code, status, label in [
        ("changeability", "included", "Changes allowed"),
        ("refundability", "conditional", "Refunds subject to fare conditions"),
        ("seat_selection", "included", "Standard seat selection"),
        ("meals", "included", "Meal included"),
        ("lounge", "not_included", "Lounge not included"),
    ]:
        await service.create_record("attributes", {
            "airline_code": "LH",
            "fare_family_id": flex["id"],
            "attribute_code": code,
            "attribute_label": label,
            "attribute_status": status,
            "client_safe_label": label,
            "client_safe_value": status.replace("_", " ").title(),
            "evidence_link_ids": [f"evidence-{code}"],
            **visible,
        }, user)

    mapping = (await service.create_record("rbd-mappings", {
        "airline_code": "LH",
        "rbd_code": "Y",
        "cabin": "economy",
        "fare_family_id": flex["id"],
        "mapping_status": "known",
        "upgrade_to_rbd_codes": ["B"],
        "downgrade_to_rbd_codes": ["K"],
        "evidence_link_ids": ["evidence-rbd-y"],
        **visible,
    }, user))["item"]
    await service.create_record("rbd-mappings", {
        "airline_code": "LH",
        "rbd_code": "K",
        "cabin": "economy",
        "mapping_status": "variable",
        "variable_by_fare_basis": True,
        "known_restrictions": ["Confirm fare basis"],
        **visible,
    }, user)
    if (await service.resolve_rbd({"airline_code": "LH", "rbd_code": "Y"}))["fare_family"]["id"] != flex["id"]:
        raise AssertionError("Known RBD did not resolve to its governed fare family.")
    if not (await service.resolve_rbd({"airline_code": "LH", "rbd_code": "K"}))["manual_review_required"]:
        raise AssertionError("Variable RBD did not preserve manual review.")
    if (await service.update_record("rbd-mappings", mapping["id"], {"confidence": "official"}, user))["item"]["confidence"] != "official":
        raise AssertionError("RBD mapping update failed.")

    baggage_rule = (await service.create_record("baggage-rules", {
        "airline_code": "LH",
        "fare_family_id": flex["id"],
        "cabin": "economy",
        "allowance_status": "known",
        "baggage_concept": "piece",
        "personal_item_included": True,
        "cabin_baggage_pieces": 1,
        "cabin_baggage_weight_kg": 8,
        "checked_baggage_pieces": 1,
        "checked_baggage_weight_per_piece_kg": 23,
        "infant_allowance": {"checked_baggage_pieces": 0},
        "child_allowance": {"checked_baggage_pieces": 1},
        "status_member_exceptions": [{"status_tiers": ["senator"], "allowance_overrides": {"checked_baggage_pieces": 2}}],
        "special_item_inclusions": ["stroller"],
        "special_item_exclusions": ["sports_equipment"],
        "codeshare_interline_status": "conditional",
        "evidence_link_ids": ["evidence-baggage-flex"],
        **visible,
    }, user))["item"]
    await service.create_record("baggage-exceptions", {
        "airline_code": "LH",
        "baggage_rule_id": baggage_rule["id"],
        "fare_family_id": flex["id"],
        "exception_type": "route",
        "exception_status": "active",
        "route_scope": ["SOF-FRA"],
        "allowance_overrides": {"checked_baggage_pieces": 2},
        "warning_message": "Route-specific baggage allowance applied.",
        "client_safe_message": "This route has a documented baggage exception.",
        **visible,
    }, user)
    resolved = await service.resolve_baggage({"airline_code": "LH", "fare_family_id": flex["id"], "origin": "SOF", "destination": "FRA"})
    if resolved["allowance"]["checked_baggage_pieces"] != 2 or not resolved["applied_exceptions"]:
        raise AssertionError("Route baggage exception was not applied deterministically.")
    status_resolved = await service.resolve_baggage({"airline_code": "LH", "fare_family_id": flex["id"], "status_tier": "senator"})
    if status_resolved["allowance"]["checked_baggage_pieces"] != 2:
        raise AssertionError("Status-member baggage exception was not applied.")
    interline_unknown = await service.resolve_baggage({"airline_code": "LH", "fare_family_id": flex["id"], "marketing_carrier": "LH", "operating_carrier": "XX"})
    if not interline_unknown["manual_review_required"] or interline_unknown["interline_assessment"]["status"] != "unknown":
        raise AssertionError("Unknown interline baggage context did not remain manual review.")

    await service.create_record("commercial-bundles", {
        "airline_code": "LH",
        "bundle_code": "ECOFLEX",
        "bundle_name": "Economy Flex",
        "cabin": "economy",
        "fare_family_ids": [flex["id"]],
        "brand_codes": ["ECOFLEX"],
        "rbd_codes": ["Y"],
        "baggage_rule_ids": [baggage_rule["id"]],
        "ancillary_inclusions": ["seat_selection", "meal"],
        "bundle_status": "included",
        **visible,
    }, user)
    await service.create_record("evidence-links", {
        "airline_code": "LH",
        "target_type": "fare-families",
        "target_id": flex["id"],
        "evidence_source_id": "evidence-source-lh-fares",
        "evidence_status": "approved",
        "authority_level": "airline_official",
        "accessibility": "agency_visible",
        "agency_visible": True,
        "confidence": "official",
        "freshness_status": "current",
        "agency_id": agency_id,
        "internal_notes": "Restricted evidence handling note",
    }, user)
    await service.create_record("comparison-profiles", {
        "agency_id": agency_id,
        "profile_name": "LH Economy brands",
        "airline_codes": ["LH"],
        "fare_family_ids": [basic["id"], flex["id"]],
        "cabin_scope": ["economy"],
        "attribute_codes": ["changeability", "refundability", "seat_selection", "meals", "lounge"],
        "comparison_status": "approved",
        "client_safe_title": "Economy fare comparison",
        "client_safe_labels": {"changeability": "Changes"},
        "internal_column_notes": {"changeability": "Use fare-rule evidence"},
        **visible,
    }, user)

    comparison = await service.compare_brands({"airline_code": "LH", "fare_family_ids": [flex["id"]]}, agency_id=agency_id, agency_safe=True)
    if len(comparison["rows"]) != 1 or comparison["rows"][0]["attributes"]["changeability"]["status"] != "included":
        raise AssertionError("Fare-brand comparison did not calculate structured attributes.")
    if not comparison["rows"][0]["baggage_summary"]:
        raise AssertionError("Fare-brand comparison omitted baggage summary.")
    offer = await service.offer_builder_attributes({"airline_code": "LH", "fare_family_id": flex["id"], "rbd_code": "Y"}, agency_id=agency_id, agency_safe=True)
    if offer["fare_family"]["id"] != flex["id"] or offer["live_price_or_availability_asserted"]:
        raise AssertionError("Offer-builder projection is incomplete or asserted live data.")

    await db.collection("intelligent_offer_builder_packages").insert_one({
        "id": "offer-fare-brand-smoke",
        "agency_id": agency_id,
        "recommended_airlines": ["LH"],
        "metadata": {"fare_family_ids": [flex["id"]]},
    })
    package = await IntelligentOfferBuilderService(db).get_agency_package(agency_id, "offer-fare-brand-smoke")
    if package["fare_brand_intelligence"]["fare_family_count"] != 1:
        raise AssertionError("Intelligent Offer Builder did not consume published fare-brand metadata.")

    await service.create_record("fare-families", {
        "airline_id": "airline-lh",
        "airline_code": "LH",
        "family_code": "INTERNAL",
        "family_name": "Internal draft",
        "cabin": "economy",
        "publication_status": "draft",
        "internal_notes": "Never expose",
    }, user)
    agency = await service.agency_dashboard(agency_id, airline_code="LH")
    if any(item.get("family_code") == "INTERNAL" for item in agency["fare_families"]):
        raise AssertionError("Unpublished fare family leaked to agency visibility.")
    assert_agency_safe(agency)
    if (await service.agency_dashboard("foreign-agency", airline_code="LH"))["fare_families"]:
        raise AssertionError("Agency-scoped fare-brand records leaked across tenants.")


def verify_routes_ui_docs_and_readiness(paths: dict) -> None:
    expected = {
        "/api/platform/fare-brand-intelligence": {"get"},
        "/api/platform/fare-brand-intelligence/summary": {"get"},
        "/api/platform/fare-brand-intelligence/filters": {"get"},
        "/api/platform/fare-brand-intelligence/compare": {"post"},
        "/api/platform/fare-brand-intelligence/resolve-rbd": {"post"},
        "/api/platform/fare-brand-intelligence/resolve-baggage": {"post"},
        "/api/platform/fare-brand-intelligence/offer-builder-attributes": {"post"},
        "/api/platform/fare-brand-intelligence/{entity_type}": {"get", "post"},
        "/api/platform/fare-brand-intelligence/{entity_type}/{record_id}": {"get", "put"},
        "/api/agencies/{agency_id}/fare-brand-library": {"get"},
        "/api/agencies/{agency_id}/fare-brand-library/summary": {"get"},
        "/api/agencies/{agency_id}/fare-brand-library/compare": {"post"},
        "/api/agencies/{agency_id}/fare-brand-library/resolve-rbd": {"post"},
        "/api/agencies/{agency_id}/fare-brand-library/resolve-baggage": {"post"},
        "/api/agencies/{agency_id}/fare-brand-library/offer-builder-attributes": {"post"},
        "/api/agencies/{agency_id}/fare-brand-library/{entity_type}": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    agency_record_path = "/api/agencies/{agency_id}/fare-brand-library/{entity_type}"
    if set(paths.get(agency_record_path, {})) & {"post", "put", "patch", "delete"}:
        raise AssertionError("Agency fare-brand record routes expose mutation.")

    checks = [
        ("frontend/src/App.jsx", "/platform/fare-brand-intelligence"),
        ("frontend/src/App.jsx", "/agency/fare-brand-library"),
        ("frontend/src/lib/moduleCatalog.js", "Fare Brand Library"),
        ("frontend/src/pages/platform/FareBrandIntelligencePage.jsx", "Fare-family hierarchy editor"),
        ("frontend/src/pages/agency/FareBrandLibraryPage.jsx", "Offer-builder integration"),
        ("docs/architecture/airline-fare-family-rbd-baggage-brand-intelligence-foundation.md", "does not calculate a live fare"),
        ("BUILD_PHASES.md", "Implemented Phase 55.7"),
        ("README.md", "Phase 55.7 Fare Family, RBD, Baggage, and Brand Intelligence"),
        ("docs/architecture/current-model-inventory.md", "airline_booking_class_mappings"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/fare-brand-intelligence"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.7 Alignment"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.7 Fare Family, RBD, Baggage, and Brand Intelligence"),
        ("backend/services/blueprint_adoption_service.py", "Airline Fare Family RBD Baggage And Brand Intelligence"),
        ("backend/services/airline_policy_evidence_governance_service.py", '"fare_brand_attribute": "airline_fare_brand_attributes"'),
        ("backend/services/airline_knowledge_versioning_service.py", '"baggage_allowance_rule": "airline_baggage_allowance_rules"'),
        ("backend/services/intelligent_offer_builder_service.py", "consumes_fare_brand_intelligence"),
    ]
    for relative, value in checks:
        require_text(ROOT / relative, value)

    health = get("/api/health")
    readiness = get("/api/readiness")
    if health.get("phase") != EXPECTED_PHASE or readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Phase 55.7 marker is not active: {health.get('phase')} / {readiness.get('phase')}")
    section = readiness.get("airline_fare_family_rbd_baggage_brand_intelligence_foundation") or {}
    for key in [
        "airline_fare_family_rbd_baggage_brand_intelligence_enabled",
        "canonical_airline_fare_families_collection_reused",
        "fare_family_hierarchy_enabled",
        "rbd_mapping_with_unknown_states_enabled",
        "baggage_context_resolution_enabled",
        "interline_baggage_uncertainty_enabled",
        "commercial_attribute_comparison_enabled",
        "client_safe_labels_enabled",
        "internal_evidence_separation_enabled",
        "evidence_governance_integration_enabled",
        "knowledge_versioning_integration_enabled",
        "offer_builder_integration_enabled",
        "agency_published_read_only",
        "live_availability_disabled",
        "fare_pricing_engine_disabled",
        "provider_connectivity_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.7 flag {key}: {section}")
    for key in ["fare_brand_intelligence_collection_counts", "fare_family_count", "fare_brand_attribute_count", "rbd_mapping_count", "baggage_allowance_rule_count", "published_fare_family_count", "unknown_rbd_mapping_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.7 counter {key}")


def verify_live_routes() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.7 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    token = uuid4().hex[:8].upper()
    airline_code = f"F{token[:1]}"
    visibility = {
        "agency_id": agency_id,
        "publication_status": "published",
        "approval_status": "approved",
        "agency_visibility_status": "selected_agencies",
        "visible_agency_ids": [agency_id],
        "freshness_status": "current",
        "confidence": "high",
    }
    family = post(f"{PLATFORM_BASE}/fare-families", {
        "airline_id": f"airline-{token}",
        "airline_code": airline_code,
        "family_code": f"FLEX{token}",
        "family_name": "Smoke Flex",
        "cabin": "economy",
        "evidence_link_ids": [f"evidence-{token}"],
        **visibility,
    }, OWNER_HEADERS, 201)["item"]
    mapping = post(f"{PLATFORM_BASE}/rbd-mappings", {
        "airline_code": airline_code,
        "rbd_code": "Y",
        "cabin": "economy",
        "fare_family_id": family["id"],
        "mapping_status": "known",
        **visibility,
    }, OWNER_HEADERS, 201)["item"]
    if put(f"{PLATFORM_BASE}/rbd-mappings/{mapping['id']}", {"confidence": "official"}, OWNER_HEADERS).get("item", {}).get("confidence") != "official":
        raise AssertionError("Live RBD mapping update failed.")
    post(f"{PLATFORM_BASE}/baggage-rules", {
        "airline_code": airline_code,
        "fare_family_id": family["id"],
        "cabin": "economy",
        "allowance_status": "known",
        "baggage_concept": "piece",
        "personal_item_included": True,
        "cabin_baggage_pieces": 1,
        "checked_baggage_pieces": 1,
        "checked_baggage_weight_per_piece_kg": 23,
        "codeshare_interline_status": "unknown",
        **visibility,
    }, OWNER_HEADERS, 201)
    dashboard = get(f"{PLATFORM_BASE}?agency_id={agency_id}&airline_code={airline_code}", OWNER_HEADERS)
    if dashboard.get("summary", {}).get("fare_family_count") != 1:
        raise AssertionError("Platform fare-brand dashboard omitted the live family.")
    agency = get(f"/api/agencies/{agency_id}/fare-brand-library?airline_code={airline_code}", OWNER_HEADERS)
    if agency.get("read_only") is not True or len(agency.get("fare_families") or []) != 1:
        raise AssertionError("Agency fare-brand library projection is incomplete.")
    assert_agency_safe(agency)
    rbd = post(f"/api/agencies/{agency_id}/fare-brand-library/resolve-rbd", {"airline_code": airline_code, "rbd_code": "Y"}, OWNER_HEADERS)
    if rbd.get("fare_family", {}).get("id") != family["id"]:
        raise AssertionError("Agency RBD resolution did not return the published fare family.")
    baggage = post(f"/api/agencies/{agency_id}/fare-brand-library/resolve-baggage", {"airline_code": airline_code, "fare_family_id": family["id"]}, OWNER_HEADERS)
    if baggage.get("allowance", {}).get("checked_baggage_pieces") != 1:
        raise AssertionError("Agency baggage resolution omitted the published allowance.")
    request("POST", f"/api/agencies/{agency_id}/fare-brand-library/fare-families", {}, OWNER_HEADERS, 405)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    if len(agencies) > 1:
        foreign = get(f"/api/agencies/{agencies[1]['id']}/fare-brand-library?airline_code={airline_code}", OWNER_HEADERS)
        if foreign.get("fare_families"):
            raise AssertionError("Agency-scoped fare-brand metadata leaked across tenants.")


def verify_safety() -> None:
    flags = AirlineFareFamilyBrandIntelligenceService(None).safety_flags()  # type: ignore[arg-type]
    if any(value is not True for value in flags.values()):
        raise AssertionError(f"Fare-brand intelligence safety flag is disabled: {flags}")
    service_path = ROOT / "backend/services/airline_fare_family_brand_intelligence_service.py"
    for forbidden in [
        "requests.get(",
        "requests.post(",
        "httpx.",
        "openai",
        "backgroundtasks",
        "asyncio.create_task",
        ".delete_one(",
        ".delete_many(",
        "issue_ticket(",
        "create_pnr(",
        "live_availability(",
        "calculate_fare(",
    ]:
        reject_text(service_path, forbidden)


def main() -> int:
    verify_models_collections_indexes_and_taxonomies()
    verify_safety()
    asyncio.run(verify_service_behavior())
    paths = get("/openapi.json").get("paths") or {}
    verify_routes_ui_docs_and_readiness(paths)
    verify_live_routes()
    print("Phase 55.7 airline fare family, RBD, baggage, and brand intelligence foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
