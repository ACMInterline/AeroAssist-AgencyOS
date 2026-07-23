#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from database import Database
from models import Agency, AgencyDemoWorkspaceGenerateRequest
from scripts.phase_assertions import application_phase_is_at_least
from services.agency_demo_workspace_generator import (
    MAX_GENERATED_RECORDS,
    PHASE_LABEL,
    demo_profile_catalog,
)
from services.agency_onboarding_service import (
    AgencyOnboardingError,
    AgencyOnboardingService,
    complete_pilot_agency_experience_readiness_metadata,
)
from services.commercial_pilot_operations_command_centre_service import (
    CommercialPilotOperationsCommandCentreService,
)


MINIMUM_PHASE = PHASE_LABEL


async def create_agency(database: Database, agency_id: str, name: str) -> AgencyOnboardingService:
    agency = Agency(
        id=agency_id,
        name=name,
        slug=agency_id,
        legal_name=f"{name} Ltd",
        country="BG",
        timezone="UTC",
        default_currency="EUR",
    )
    await database.collection("agencies").insert_one(agency.model_dump(mode="json"))
    service = AgencyOnboardingService(database)
    await service.initialize_for_new_agency(agency_id, "platform-owner")
    return service


def assert_same_agency(document: dict, agency_id: str) -> None:
    assert document.get("agency_id") == agency_id, document


async def verify_generation() -> None:
    database = Database()
    service = await create_agency(database, "pilot-small", "Pilot Small")
    other_service = await create_agency(database, "pilot-corporate", "Pilot Corporate")

    profiles = await service.demo_workspace_profiles("pilot-small")
    assert {item["key"] for item in profiles["profiles"]} == {
        "small_agency",
        "medium_agency",
        "corporate_agency",
        "luxury_leisure_agency",
    }
    assert all(item["generated_operational_areas"] and item["scenario_preview"] for item in profiles["profiles"])

    request = AgencyDemoWorkspaceGenerateRequest(demo_profile="small_agency")
    first = await service.seed_demo_workspace("pilot-small", "agency-owner", request)
    first_summary = first["profile"]["demo_generation_summary"]
    manifest = first["demo_workspace"]
    counts_before = {
        collection: await database.collection(collection).count({"agency_id": "pilot-small"})
        for collection in first_summary["record_counts"]
        if collection != "audit_events"
    }
    second = await service.seed_demo_workspace("pilot-small", "agency-owner", request)
    second_summary = second["profile"]["demo_generation_summary"]
    counts_after = {
        collection: await database.collection(collection).count({"agency_id": "pilot-small"})
        for collection in first_summary["record_counts"]
        if collection != "audit_events"
    }
    assert first_summary == second_summary
    assert first["demo_workspace"] == second["demo_workspace"]
    assert counts_before == counts_after
    assert first_summary["record_count"] <= MAX_GENERATED_RECORDS
    assert first_summary["scenario_count"] == 8
    assert first_summary["deterministic"] is True
    assert first_summary["idempotent"] is True
    assert first_summary["provider_execution"] is False
    assert first_summary["payment_execution"] is False
    assert first_summary["airline_communication"] is False
    assert first_summary["ticket_issuance"] is False

    try:
        await service.seed_demo_workspace(
            "pilot-small",
            "agency-owner",
            AgencyDemoWorkspaceGenerateRequest(demo_profile="medium_agency"),
        )
    except AgencyOnboardingError as exc:
        assert "cannot be changed" in str(exc)
    else:
        raise AssertionError("A generated workspace was allowed to mix demo profiles.")

    corporate = await other_service.seed_demo_workspace(
        "pilot-corporate",
        "corporate-owner",
        AgencyDemoWorkspaceGenerateRequest(demo_profile="corporate_agency"),
    )
    corporate_summary = corporate["profile"]["demo_generation_summary"]
    assert corporate_summary["scenario_count"] == 10
    assert corporate_summary["record_count"] > first_summary["record_count"]
    assert corporate_summary["profile_label"] == "Corporate Agency"
    assert await database.collection("trip_workspaces").count({"agency_id": "pilot-corporate"}) == 10

    for collection in first_summary["record_counts"]:
        for document in await database.collection(collection).find_many({"agency_id": "pilot-small"}):
            assert_same_agency(document, "pilot-small")
        for document in await database.collection(collection).find_many({"agency_id": "pilot-corporate"}):
            assert_same_agency(document, "pilot-corporate")

    required_collections = {
        "client_profiles",
        "passenger_profiles",
        "client_passenger_relationships",
        "travel_requests",
        "travel_request_workspaces",
        "trip_workspaces",
        "flight_workspaces",
        "offer_workspaces",
        "offer_options",
        "offer_workspaces_v2",
        "offer_acceptances",
        "trip_accepted_offer_snapshots",
        "booking_readiness_packages",
        "offer_booking_handoffs",
        "booking_workspaces",
        "ticket_workspaces",
        "emd_workspaces",
        "ssr_osi_workspaces",
        "passenger_service_requests",
        "document_workspaces",
        "document_packages",
        "rendered_documents",
        "invoices",
        "payments",
        "operational_work_items",
        "operational_deadlines",
        "operational_timelines",
        "after_sales_cases",
    }
    assert required_collections.issubset(first_summary["record_counts"])
    assert all(first_summary["record_counts"][name] > 0 for name in required_collections)
    assert await database.collection("agency_branding_settings").find_one({"agency_id": "pilot-small"})
    assert await database.collection("document_templates").count({"agency_id": "pilot-small"}) == 3

    scenario = manifest["family_ready_ticketing"]
    trip = await database.collection("trip_workspaces").find_one({"id": scenario["trip_workspace_id"], "agency_id": "pilot-small"})
    request_record = await database.collection("travel_requests").find_one({"id": scenario["request_id"], "agency_id": "pilot-small"})
    booking = await database.collection("booking_workspaces").find_one({"id": scenario["booking_workspace_id"], "agency_id": "pilot-small"})
    package = await database.collection("document_packages").find_one({"id": scenario["document_package_id"], "agency_id": "pilot-small"})
    assert trip and request_record and booking and package
    assert request_record["trip_id"] == trip["id"]
    assert set(trip["passenger_ids"]) == set(booking["passenger_ids"])
    assert set(trip["flight_workspace_ids"]) == set(booking["flight_workspace_ids"])
    assert booking["offer_acceptance_id"] == scenario["offer_acceptance_id"]
    assert booking["booking_readiness_package_id"] == scenario["booking_readiness_package_id"]
    assert package["source_context_id"] == booking["id"]

    for scenario_key, ids in manifest.items():
        trip = await database.collection("trip_workspaces").find_one({"id": ids["trip_workspace_id"], "agency_id": "pilot-small"})
        assert trip
        assert set(ids["passenger_ids"]) == set(trip["passenger_ids"])
        assert set(ids["flight_workspace_ids"]) == set(trip["flight_workspace_ids"])
        assert ids["document_workspace_id"] in trip["document_ids"]

    service_codes = {
        item.get("ssr_code")
        for item in await database.collection("ssr_osi_workspaces").find_many({"agency_id": "pilot-small"})
    }
    assert {"UMNR", "WCHR", "WCHS", "WCHC", "MEDA", "PETC", "AVIH", "EXST", "VGML", "BLND", "DEAF", "SPEQ", "WCBD"}.issubset(service_codes)
    assert await database.collection("operational_timelines").count({"agency_id": "pilot-small"}) >= 24
    assert await database.collection("after_sales_cases").count({"agency_id": "pilot-small"}) >= 2
    assert await database.collection("ticket_workspaces").count({"agency_id": "pilot-small"}) >= 3
    assert await database.collection("emd_workspaces").count({"agency_id": "pilot-small"}) >= 2

    command = CommercialPilotOperationsCommandCentreService(database)
    home = await command.agency_home(
        "pilot-small",
        {"id": "agency-owner", "full_name": "Pilot Owner"},
        {"agency_role": "agency_owner", "status": "active", "team_codes": ["pilot-desk"]},
        due_period="all",
    )
    assert home["priorities"]["items"]
    assert any(item["count"] for item in home["queues"])
    assert home["timeline"]["events"]
    assert home["alerts"]
    assert home["recent_activity"]
    assert home["quick_actions"]
    queue_counts = {item["key"]: item["count"] for item in home["queues"]}
    for key in ["new_requests", "offers_awaiting_action", "waiting_client", "waiting_airline", "awaiting_approval", "ready_booking", "ready_ticketing", "special_services", "documents_to_send", "follow_ups", "overdue"]:
        assert queue_counts[key] > 0, (key, queue_counts)
    assert home["kpis"]["accepted_offers_awaiting_booking"] > 0
    assert home["kpis"]["bookings_awaiting_ticketing"] > 0
    assert home["kpis"]["after_sales_cases"] > 0
    assert home["kpis"]["payment_invoice_blockers"] > 0
    assert "pilot-corporate" not in str(home)


def verify_registration() -> None:
    assert application_phase_is_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="complete pilot agency experience smoke",
    )
    metadata = complete_pilot_agency_experience_readiness_metadata()
    for key in [
        "selectable_demo_profiles_enabled",
        "canonical_linked_demo_records_enabled",
        "deterministic_generation_enabled",
        "idempotent_safe_reruns_enabled",
        "tenant_scoped_generation_enabled",
        "bounded_generation_enabled",
        "operations_command_centre_population_enabled",
        "profile_preview_and_completion_summary_enabled",
    ]:
        assert metadata[key] is True, key
    for key in [
        "provider_execution_enabled",
        "payment_execution_enabled",
        "airline_communication_enabled",
        "ticket_issuance_enabled",
        "automatic_production_seeding_enabled",
    ]:
        assert metadata[key] is False, key
    assert len(demo_profile_catalog()) == 4

    expected = {
        ROOT / "backend/routers/agency_onboarding.py": [
            '@router.get("/demo-workspace/profiles")',
            "AgencyDemoWorkspaceGenerateRequest",
            "seed_demo_workspace(agency_id, user[\"id\"], payload)",
        ],
        ROOT / "backend/server.py": ["complete_pilot_agency_experience"],
        ROOT / "frontend/src/pages/agency/AgencyOnboardingPage.jsx": [
            "Complete pilot workspace",
            'useState("small_agency")',
            "Generating linked operational records",
            "Linked records",
        ],
        ROOT / "docs/architecture/complete-pilot-agency-experience.md": [
            "Determinism",
            "Tenant Isolation",
            "Limitations",
        ],
    }
    for path, needles in expected.items():
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle in content, f"Missing {needle!r} in {path.relative_to(ROOT)}"


async def main() -> None:
    verify_registration()
    await verify_generation()
    print("Complete pilot agency experience smoke passed.")


if __name__ == "__main__":
    asyncio.run(main())
