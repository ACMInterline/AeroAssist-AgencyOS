#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    AirlineDistributionCapability,
    AirlineDistributionChannel,
    AirlineDistributionEvidenceLink,
    AirlineDistributionRestriction,
    AirlineFulfillmentCapability,
    AirlineGdsParticipation,
    AirlineNdcCapability,
    AirlinePssProfile,
    AirlineServicingCapability,
)
from services.airline_distribution_capability_service import (
    CAPABILITY_PHASE,
    CAPABILITY_CATALOG,
    CAPABILITY_STATUSES,
    DISTRIBUTION_CHANNEL_CODES,
    DISTRIBUTION_COLLECTIONS,
    PHASE_LABEL,
    PROVIDER_READINESS_STAGES,
    AirlineDistributionCapabilityError,
    AirlineDistributionCapabilityService,
)
from services.offer_to_booking_handoff_service import OfferToBookingHandoffService
from phase_assertions import assert_application_phase_at_least
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


MINIMUM_PHASE = "phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-distribution-capabilities"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    if text.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_agency_safe(value: object) -> None:
    restricted = {
        "internal_notes",
        "evidence_source_id",
        "evidence_artifact_id",
        "evidence_assertion_id",
        "evidence_link_id",
        "visible_agency_ids",
        "legacy_pss_parameters_id",
        "legacy_gds_parameters_id",
        "distribution_channel_profile_id",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency distribution response leaked restricted field {key}")
            assert_agency_safe(child)
    elif isinstance(value, list):
        for item in value:
            assert_agency_safe(item)


def verify_models_collections_indexes_and_taxonomies() -> None:
    if CAPABILITY_PHASE != MINIMUM_PHASE:
        raise AssertionError(f"Unexpected Phase 55.5 capability provenance: {CAPABILITY_PHASE}")
    assert_application_phase_at_least(PHASE_LABEL, MINIMUM_PHASE, source="Phase 55.5 service")
    expected_collections = {
        "airline_distribution_channels",
        "airline_distribution_capabilities",
        "airline_pss_profiles",
        "airline_gds_participations",
        "airline_ndc_capabilities",
        "airline_fulfillment_capabilities",
        "airline_servicing_capabilities",
        "airline_distribution_restrictions",
        "airline_distribution_evidence_links",
    }
    if set(DISTRIBUTION_COLLECTIONS) != expected_collections or not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Phase 55.5 tenant-aware collection registration is incomplete.")
    required_channels = {"direct_website", "call_center", "airport_desk", "amadeus", "sabre", "travelport", "ndc_aggregator", "airline_direct_ndc", "consolidator", "tour_operator", "manual_offline_process"}
    if set(DISTRIBUTION_CHANNEL_CODES) != required_channels:
        raise AssertionError("Distribution channel taxonomy is incomplete.")
    if set(CAPABILITY_STATUSES) != {"supported", "unsupported", "conditional", "manual_only", "unknown", "provider_specific", "route_specific", "market_specific"}:
        raise AssertionError("Distribution capability status taxonomy is incomplete.")
    if PROVIDER_READINESS_STAGES != ["documented_capability", "configured_provider", "tested_sandbox", "production_enabled_provider"]:
        raise AssertionError("Provider readiness stages do not preserve the required progression.")
    required_capabilities = {
        "shopping": {"schedule", "availability", "fares", "branded_fares", "ancillaries", "seat_maps", "special_service_visibility"},
        "booking": {"pnr_creation", "multi_passenger", "ssr", "osi", "apis_documents", "special_seats", "pets", "medical_requests", "groups", "interline_codeshare"},
        "fulfillment": {"ticket_issuance", "emd_a", "emd_s", "rfic_rfisc_availability", "exchanges", "refunds", "voids", "revalidation", "residual_value"},
        "servicing": {"voluntary_changes", "involuntary_changes", "schedule_changes", "split_pnr", "name_correction", "ancillary_modification", "disruption_handling"},
    }
    if {key: set(value) for key, value in CAPABILITY_CATALOG.items()} != required_capabilities:
        raise AssertionError("Shopping, booking, fulfillment, or servicing capability dimensions are incomplete.")

    channel = AirlineDistributionChannel(channel_reference="ADC-MODEL", airline_code="LH", channel_code="amadeus", channel_name="Amadeus")
    capability = AirlineDistributionCapability(capability_reference="ADP-MODEL", airline_code="LH", channel_id=channel.id, channel_code="amadeus", capability_area="booking", capability_code="pnr_creation")
    pss = AirlinePssProfile(pss_profile_reference="APS-MODEL", airline_code="LH")
    gds = AirlineGdsParticipation(gds_participation_reference="AGD-MODEL", airline_code="LH", gds_code="amadeus")
    ndc = AirlineNdcCapability(ndc_capability_reference="AND-MODEL", airline_code="LH")
    fulfillment = AirlineFulfillmentCapability(fulfillment_capability_reference="AFC-MODEL", airline_code="LH", capability_code="ticket_issuance")
    servicing = AirlineServicingCapability(servicing_capability_reference="ASC-MODEL", airline_code="LH", capability_code="voluntary_changes")
    restriction = AirlineDistributionRestriction(restriction_reference="ADR-MODEL", airline_code="LH", restriction_type="market", title="Market restriction", description="Market specific.")
    evidence = AirlineDistributionEvidenceLink(distribution_evidence_reference="ADE-MODEL", airline_code="LH", target_type="channels", target_id=channel.id)
    if not all(item.id for item in [channel, capability, pss, gds, ndc, fulfillment, servicing, restriction, evidence]):
        raise AssertionError("Phase 55.5 models did not preserve canonical ids.")
    if channel.credentials_stored or ndc.credentials_stored or gds.credentials_stored:
        raise AssertionError("Distribution models indicate credential storage.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_distribution_channels_airline_channel_lookup",
        "airline_distribution_channels_status_stage_lookup",
        "airline_distribution_capabilities_channel_area_lookup",
        "airline_pss_profiles_host_lookup",
        "airline_gds_participations_airline_gds_lookup",
        "airline_ndc_capabilities_type_provider_lookup",
        "airline_fulfillment_capabilities_rfic_rfisc_lookup",
        "airline_servicing_capabilities_channel_code_lookup",
        "airline_distribution_restrictions_status_review_lookup",
        "airline_distribution_evidence_links_governance_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


async def verify_service_behavior_and_handoff_integration() -> None:
    db = Database()
    service = AirlineDistributionCapabilityService(db)
    agency_id = "agency-distribution-smoke"
    user = {"id": "platform-owner", "email": "owner@aeroassist.dev"}
    visibility = {"publication_status": "published", "approval_status": "approved", "agency_visibility_status": "selected_agencies", "visible_agency_ids": [agency_id], "freshness_status": "current"}

    channel = (await service.create_record("channels", {
        "channel_reference": "ADC-LH-AMADEUS",
        "agency_id": agency_id,
        "airline_code": "LH",
        "channel_code": "amadeus",
        "capability_status": "supported",
        "provider_stage": "production_enabled_provider",
        "provider_name": "Amadeus planning record",
        "fallback_method": "Manual airline support desk review",
        "provider_specific_notes": "Published provider-specific handling note.",
        **visibility,
    }, user))["item"]
    capability = (await service.create_record("capabilities", {
        "capability_reference": "ADP-LH-PNR",
        "agency_id": agency_id,
        "airline_code": "LH",
        "channel_id": channel["id"],
        "capability_area": "booking",
        "capability_code": "pnr_creation",
        "capability_status": "supported",
        "provider_stage": "production_enabled_provider",
        **visibility,
    }, user))["item"]
    await service.create_record("pss-profiles", {"agency_id": agency_id, "airline_code": "LH", "known_pss": "Altéa", "reservation_host": "Published host context", "ticketing_host": "Published ticketing context", "emd_host": "Published EMD context", **visibility}, user)
    await service.create_record("gds-participations", {"agency_id": agency_id, "airline_code": "LH", "channel_id": channel["id"], "gds_code": "amadeus", "participation_status": "supported", "shopping_status": "supported", "booking_status": "supported", "ticketing_status": "conditional", "servicing_status": "manual_only", "provider_stage": "production_enabled_provider", **visibility}, user)
    await service.create_record("ndc-capabilities", {"agency_id": agency_id, "airline_code": "LH", "ndc_type": "airline_direct_ndc", "provider_name": "Published NDC planning context", "capability_status": "conditional", "provider_stage": "tested_sandbox", "shopping_status": "supported", "booking_status": "conditional", "fulfillment_status": "unknown", "servicing_status": "manual_only", **visibility}, user)
    await service.create_record("fulfillment-capabilities", {"agency_id": agency_id, "airline_code": "LH", "channel_id": channel["id"], "capability_code": "emd_a", "capability_status": "conditional", "provider_stage": "production_enabled_provider", "rfic_scope": ["C"], "rfisc_scope": ["0B5"], **visibility}, user)
    await service.create_record("servicing-capabilities", {"agency_id": agency_id, "airline_code": "LH", "channel_id": channel["id"], "capability_code": "voluntary_changes", "capability_status": "manual_only", "provider_stage": "production_enabled_provider", **visibility}, user)
    restriction = (await service.create_record("restrictions", {"agency_id": agency_id, "airline_code": "LH", "channel_id": channel["id"], "restriction_type": "market_specific", "title": "Point-of-sale restriction", "description": "Human review is required outside the documented market.", "fallback_method": "Use manual airline support desk review", **visibility}, user))["item"]
    await service.create_record("evidence-links", {"agency_id": agency_id, "airline_code": "LH", "target_type": "channels", "target_id": channel["id"], "evidence_assertion_id": "assertion-lh-amadeus", "evidence_status": "approved", "authority_level": "official_airline_controlled", "confidence": "high", "freshness_status": "current", "accessibility": "agency_visible", "agency_visible": True}, user)
    await service.create_record("channels", {"agency_id": agency_id, "airline_code": "LH", "channel_code": "call_center", "capability_status": "unknown", "provider_stage": "documented_capability", **visibility}, user)
    await service.create_record("channels", {"agency_id": agency_id, "airline_code": "LH", "channel_code": "sabre", "capability_status": "supported", "provider_stage": "configured_provider", "publication_status": "draft", "internal_notes": "Unpublished provider detail"}, user)

    updated = await service.update_record("capabilities", capability["id"], {"capability_status": "provider_specific", "provider_specific_notes": "Published conditions apply."}, user)
    if updated["item"]["capability_status"] != "provider_specific":
        raise AssertionError("Distribution capability metadata update failed.")
    detail = await service.get_record("restrictions", restriction["id"])
    if detail["item"]["channel_id"] != channel["id"]:
        raise AssertionError("Distribution restriction detail lost channel linkage.")

    agency = await service.agency_dashboard(agency_id, airline_code="LH")
    if agency["summary"]["channel_count"] != 2 or agency["booking_handoff"]["available_channel_count"] != 1:
        raise AssertionError(f"Agency distribution planning availability is incorrect: {agency}")
    if any(item.get("channel_code") == "sabre" for item in agency["operational_channels"]):
        raise AssertionError("Unpublished configured-provider record leaked to the agency view.")
    if not agency["warnings"] or not agency["fallback_methods"]:
        raise AssertionError("Unknown/manual/fallback planning guidance is incomplete.")
    if any(item.get("live_connectivity_confirmed") is not False for item in agency["operational_channels"]):
        raise AssertionError("Agency distribution records implied live connectivity.")
    assert_agency_safe(agency)
    foreign = await service.agency_dashboard("foreign-agency", airline_code="LH")
    if foreign["operational_channels"]:
        raise AssertionError("Agency-scoped distribution intelligence leaked to another agency.")

    try:
        await service.create_record("channels", {"airline_code": "BA", "channel_code": "travelport", "api_key": "forbidden"}, user)
    except AirlineDistributionCapabilityError:
        pass
    else:
        raise AssertionError("Credential-like distribution payload was accepted.")

    await db.collection("offer_acceptances").insert_one({"id": "acceptance-lh", "agency_id": agency_id, "status": "accepted", "trip_id": "trip-lh"})
    await db.collection("booking_readiness_packages").insert_one({"id": "readiness-lh", "agency_id": agency_id, "acceptance_id": "acceptance-lh", "trip_id": "trip-lh", "provider_target": "amadeus", "segments_snapshot_json": [{"id": "segment-lh", "marketing_carrier": "LH", "operating_carrier": "LH"}], "passengers_snapshot_json": [{"id": "passenger-lh"}], "pricing_snapshot_json": {"total_amount": 100, "currency": "EUR"}})
    context = await OfferToBookingHandoffService(db)._resolve_context({"agency_id": agency_id, "acceptance_id": "acceptance-lh", "booking_readiness_package_id": "readiness-lh", "provider_target": "amadeus"})
    handoff_distribution = context.get("distribution_capability") or {}
    if handoff_distribution.get("available_channel_count") != 1 or handoff_distribution.get("live_connectivity_confirmed") is not False:
        raise AssertionError("Booking handoff did not receive agency-safe non-executing distribution planning metadata.")


def verify_routes_ui_docs_and_readiness(paths: dict) -> None:
    expected = {
        "/api/platform/airline-distribution-capabilities": {"get"},
        "/api/platform/airline-distribution-capabilities/summary": {"get"},
        "/api/platform/airline-distribution-capabilities/filters": {"get"},
        "/api/platform/airline-distribution-capabilities/{entity_type}": {"get", "post"},
        "/api/platform/airline-distribution-capabilities/{entity_type}/{record_id}": {"get", "put"},
        "/api/agencies/{agency_id}/distribution-capabilities": {"get"},
        "/api/agencies/{agency_id}/distribution-capabilities/summary": {"get"},
        "/api/agencies/{agency_id}/distribution-capabilities/booking-handoff": {"get"},
        "/api/agencies/{agency_id}/distribution-capabilities/{entity_type}": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [value for value in expected if value.startswith("/api/agencies/")]:
        if set(paths.get(path, {})) & {"post", "put", "patch", "delete"}:
            raise AssertionError(f"Agency distribution capability route is not read-only: {path}")

    checks = [
        ("frontend/src/App.jsx", "/platform/airline-distribution-capabilities"),
        ("frontend/src/App.jsx", "/agency/distribution-capabilities"),
        ("frontend/src/lib/moduleCatalog.js", "Distribution Capabilities"),
        ("frontend/src/pages/platform/AirlineDistributionCapabilitiesPage.jsx", "Airline × channel matrix"),
        ("frontend/src/pages/platform/AirlineDistributionCapabilitiesPage.jsx", "PSS and host summary"),
        ("frontend/src/pages/agency/AirlineDistributionCapabilitiesPage.jsx", "Operationally available channels"),
        ("frontend/src/pages/agency/AirlineDistributionCapabilitiesPage.jsx", "Booking handoff context"),
        ("docs/architecture/airline-distribution-pss-gds-ndc-capability-intelligence-foundation.md", "planning assertion"),
        ("BUILD_PHASES.md", "Implemented Phase 55.5"),
        ("README.md", "Phase 55.5 Airline Distribution PSS GDS NDC Capability Intelligence"),
        ("docs/architecture/current-model-inventory.md", "airline_distribution_capabilities"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/airline-distribution-capabilities"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.5 Alignment"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.5 Airline Distribution Capability Intelligence"),
        ("backend/services/blueprint_adoption_service.py", "Airline Distribution PSS GDS NDC Capability Intelligence"),
        ("backend/services/airline_policy_evidence_governance_service.py", '"ndc_capability": "airline_ndc_capabilities"'),
        ("backend/services/airline_knowledge_versioning_service.py", '"gds_participation": "airline_gds_participations"'),
        ("backend/services/airline_service_coverage_gap_service.py", '"distribution_channels": "airline_distribution_channels"'),
        ("backend/services/offer_to_booking_handoff_service.py", "distribution_capability_planning"),
        ("backend/services/saas_subscription_service.py", "airline_distribution_capabilities"),
    ]
    for relative, text in checks:
        require_text(ROOT / relative, text)

    health = get("/api/health")
    readiness = get("/api/readiness")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    assert_application_phase_at_least(readiness.get("phase"), MINIMUM_PHASE, source="readiness")
    section = readiness.get("airline_distribution_pss_gds_ndc_capability_intelligence_foundation") or {}
    for key in [
        "airline_distribution_pss_gds_ndc_capability_intelligence_enabled",
        "distribution_channel_matrix_enabled",
        "provider_channel_distinction_enabled",
        "documented_configured_sandbox_production_distinction_enabled",
        "unknown_capability_handling_enabled",
        "evidence_governance_integration_enabled",
        "service_coverage_integration_enabled",
        "booking_handoff_planning_integration_enabled",
        "agency_published_read_only",
        "credential_storage_disabled",
        "planning_record_does_not_imply_live_capability",
        "live_provider_connectivity_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.5 flag {key}: {section}")
    for key in ["distribution_collection_counts", "distribution_channel_count", "distribution_capability_count", "documented_capability_count", "configured_provider_count", "tested_sandbox_count", "production_enabled_provider_count", "unknown_capability_count", "credential_record_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.5 counter {key}")


def verify_live_routes() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.5 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    token = uuid4().hex[:8].upper()
    airline_code = f"D{token[:2]}"
    channel = post(
        f"{PLATFORM_BASE}/channels",
        {"channel_reference": f"ADC-{token}", "agency_id": agency_id, "airline_code": airline_code, "channel_code": "travelport", "channel_name": "Travelport", "capability_status": "conditional", "provider_stage": "configured_provider", "fallback_method": "Manual offline review", "freshness_status": "current", "approval_status": "approved", "publication_status": "published", "agency_visibility_status": "selected_agencies", "visible_agency_ids": [agency_id]},
        OWNER_HEADERS,
        201,
    )["item"]
    capability = post(
        f"{PLATFORM_BASE}/capabilities",
        {"capability_reference": f"ADP-{token}", "agency_id": agency_id, "airline_code": airline_code, "channel_id": channel["id"], "capability_area": "shopping", "capability_code": "branded_fares", "capability_status": "provider_specific", "provider_stage": "configured_provider", "approval_status": "approved", "publication_status": "published", "agency_visibility_status": "selected_agencies", "visible_agency_ids": [agency_id]},
        OWNER_HEADERS,
        201,
    )["item"]
    updated = put(f"{PLATFORM_BASE}/capabilities/{capability['id']}", {"freshness_status": "review_due"}, OWNER_HEADERS)
    if updated.get("item", {}).get("freshness_status") != "review_due":
        raise AssertionError("Live distribution capability update failed.")
    matrix = get(f"{PLATFORM_BASE}?agency_id={agency_id}&airline_code={airline_code}", OWNER_HEADERS)
    if matrix.get("summary", {}).get("channel_count") != 1 or not matrix.get("matrix"):
        raise AssertionError("Platform distribution capability matrix omitted the live smoke record.")
    agency = get(f"/api/agencies/{agency_id}/distribution-capabilities?airline_code={airline_code}", OWNER_HEADERS)
    if agency.get("read_only") is not True or len(agency.get("operational_channels") or []) != 1 or not agency.get("warnings"):
        raise AssertionError(f"Agency distribution capability projection is incomplete: {agency}")
    assert_agency_safe(agency)
    handoff = get(f"/api/agencies/{agency_id}/distribution-capabilities/booking-handoff?airline_code={airline_code}&channel_code=travelport", OWNER_HEADERS)
    if handoff.get("booking_handoff", {}).get("live_connectivity_confirmed") is not False:
        raise AssertionError("Booking handoff endpoint implied live provider connectivity.")
    request("POST", f"/api/agencies/{agency_id}/distribution-capabilities", {}, OWNER_HEADERS, 405)
    request("POST", f"{PLATFORM_BASE}/channels", {"airline_code": airline_code, "channel_code": "sabre", "client_secret": "forbidden"}, OWNER_HEADERS, 400)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    if len(agencies) > 1:
        request(
            "GET",
            f"/api/agencies/{agencies[1]['id']}/distribution-capabilities?airline_code={airline_code}",
            None,
            OWNER_HEADERS,
            403,
        )


def verify_safety() -> None:
    flags = AirlineDistributionCapabilityService(None).safety_flags()  # type: ignore[arg-type]
    if any(value is not True for value in flags.values()):
        raise AssertionError(f"Distribution capability safety flag is disabled: {flags}")
    service_path = ROOT / "backend/services/airline_distribution_capability_service.py"
    for forbidden in ["requests.get(", "requests.post(", "httpx.", "openai", "backgroundtasks", "asyncio.create_task", ".delete_one(", ".delete_many(", "seed_core_data", "create_pnr(", "issue_ticket(", "issue_emd("]:
        reject_text(service_path, forbidden)


def main() -> int:
    verify_models_collections_indexes_and_taxonomies()
    verify_safety()
    asyncio.run(verify_service_behavior_and_handoff_integration())
    paths = get("/openapi.json").get("paths") or {}
    verify_routes_ui_docs_and_readiness(paths)
    verify_live_routes()
    print("Phase 55.5 airline distribution PSS GDS NDC capability intelligence foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
