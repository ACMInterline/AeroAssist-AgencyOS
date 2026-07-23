#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from scripts.phase_assertions import application_phase_is_at_least
from database import Database
from models import (
    Agency,
    AgencyBrandingSettings,
    AgencyDashboardPreferences,
    AgencyEmailSettings,
    AgencyNotificationPreferences,
    AgencyOnboardingEmailStatusUpdate,
    AgencyOnboardingProfileUpdate,
    AgencyWorkspace,
    BookingWorkspace,
    ClientPassengerRelationship,
    ClientProfile,
    DocumentTemplate,
    FlightWorkspace,
    OfferWorkspaceV2,
    OperationalTravelWorkspace,
    PassengerProfile,
    PassengerWorkspace,
    TravelRequestWorkspace,
    TripWorkspace,
)
from services.agency_onboarding_service import (
    AgencyOnboardingError,
    AgencyOnboardingService,
    agency_onboarding_readiness_metadata,
)


MINIMUM_PHASE = "phase_58_1_commercial_pilot_agency_onboarding_foundation"


async def verify_service() -> None:
    database = Database()
    service = AgencyOnboardingService(database)
    legacy = Agency(id="legacy-agency", name="Legacy Agency", slug="legacy-agency", legal_name="Legacy Agency Ltd")
    new = Agency(id="new-agency", name="Skybridge Travel", slug="skybridge-travel", legal_name="Skybridge Travel Ltd", country="BG", timezone="Europe/Sofia", default_currency="EUR")
    other = Agency(id="other-agency", name="Other Agency", slug="other-agency", legal_name="Other Agency Ltd")
    for agency in [legacy, new, other]:
        await database.collection("agencies").insert_one(agency.model_dump(mode="json"))

    legacy_state = await service.get_state(legacy.id)
    assert legacy_state["legacy_exempt"] is True and legacy_state["required"] is False
    await service.initialize_for_new_agency(new.id, "platform-owner")
    initial = await service.get_state(new.id)
    assert initial["required"] is True and initial["profile"]["resumable"] is True

    await service.save_profile(
        new.id,
        AgencyOnboardingProfileUpdate(
            contact_name="Mila Ivanova",
            contact_email="mila@example.com",
            contact_phone="+359 2 555 0101",
            address_line_1="12 Vitosha Boulevard",
            city="Sofia",
            country="BG",
            timezone="Europe/Sofia",
            default_currency="EUR",
            working_hours=[
                {"day": "monday", "enabled": True, "open_time": "09:00", "close_time": "17:30"},
                {"day": "saturday", "enabled": False},
            ],
        ),
        "agency-owner",
    )
    await service.skip_logo(new.id, "agency-owner")
    await service.save_email_status(
        new.id,
        AgencyOnboardingEmailStatusUpdate(
            configuration_status="configuration_pending",
            sender_name="Skybridge Travel",
            sender_email="mila@example.com",
        ),
        "agency-owner",
    )
    await service.seed_defaults(new.id, "agency-owner")
    first = await service.seed_demo_workspace(new.id, "agency-owner")
    second = await service.seed_demo_workspace(new.id, "agency-owner")
    assert first["demo_workspace"] == second["demo_workspace"]
    for collection_name in [
        "client_profiles", "passenger_profiles", "operational_travel_workspaces", "travel_request_workspaces",
        "passenger_workspaces", "trip_workspaces", "offer_workspaces_v2", "booking_workspaces",
    ]:
        assert await database.collection(collection_name).count({"agency_id": new.id}) == 1
        assert await database.collection(collection_name).count({"agency_id": other.id}) == 0
    assert await database.collection("flight_workspaces").count({"agency_id": new.id}) == 2
    for collection_name, model in [
        ("client_profiles", ClientProfile),
        ("passenger_profiles", PassengerProfile),
        ("client_passenger_relationships", ClientPassengerRelationship),
        ("operational_travel_workspaces", OperationalTravelWorkspace),
        ("travel_request_workspaces", TravelRequestWorkspace),
        ("passenger_workspaces", PassengerWorkspace),
        ("flight_workspaces", FlightWorkspace),
        ("trip_workspaces", TripWorkspace),
        ("offer_workspaces_v2", OfferWorkspaceV2),
        ("booking_workspaces", BookingWorkspace),
    ]:
        for document in await database.collection(collection_name).find_many({"agency_id": new.id}):
            model(**document)
    demo_booking = await database.collection("booking_workspaces").find_one({"agency_id": new.id})
    assert demo_booking["metadata"]["synthetic"] is True
    assert demo_booking["booking_execution_disabled"] is True
    assert demo_booking["airline_pnr"] is None
    assert demo_booking["payment_summary"] == "No payment collected"

    completed = await service.complete(new.id, "agency-owner")
    assert completed["profile"]["onboarding_status"] == "completed"
    assert completed["progress_percent"] == 100 and completed["required"] is False
    assert (await database.collection("agencies").find_one({"id": new.id}))["status"] == "active"
    assert await database.collection("document_templates").count({"agency_id": new.id}) == 3
    AgencyWorkspace(**(await database.collection("agency_workspaces").find_one({"agency_id": new.id})))
    AgencyBrandingSettings(**(await database.collection("agency_branding_settings").find_one({"agency_id": new.id})))
    AgencyDashboardPreferences(**(await database.collection("agency_dashboard_preferences").find_one({"agency_id": new.id})))
    AgencyNotificationPreferences(**(await database.collection("agency_notification_preferences").find_one({"agency_id": new.id})))
    AgencyEmailSettings(**(await database.collection("agency_email_settings").find_one({"agency_id": new.id})))
    for template in await database.collection("document_templates").find_many({"agency_id": new.id}):
        DocumentTemplate(**template)
    assert await database.collection("audit_events").count({"agency_id": new.id}) >= 6

    await service.initialize_for_new_agency(other.id, "platform-owner")
    try:
        await service.complete(other.id, "other-owner")
    except AgencyOnboardingError as exc:
        assert "Complete these onboarding steps" in str(exc)
    else:
        raise AssertionError("Incomplete onboarding was allowed to complete.")


def verify_registration() -> None:
    if not application_phase_is_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE):
        raise AssertionError(f"Expected Phase 58.1 or later marker, got {CURRENT_BUILD_PHASE}.")
    metadata = agency_onboarding_readiness_metadata()
    assert metadata["resumable_wizard_enabled"] is True
    assert metadata["legacy_agencies_exempt"] is True
    assert metadata["automatic_production_seeding_enabled"] is False
    assert metadata["external_provider_execution_enabled"] is False

    expected = {
        ROOT / "backend/routers/agency_onboarding.py": [
            'prefix="/api/agencies/{agency_id}/onboarding"',
            '@router.get("")',
            '@router.put("/profile")',
            '@router.post("/demo-workspace")',
            '@router.post("/complete")',
        ],
        ROOT / "backend/server.py": ["agency_onboarding.router", "commercial_pilot_agency_onboarding_foundation"],
        ROOT / "backend/database.py": ["agency_onboarding_profiles_agency_profile_unique", "agency_dashboard_preferences_agency_key_unique", "agency_notification_preferences_agency_key_unique"],
        ROOT / "frontend/src/App.jsx": ["AgencyOnboardingPage", '"/agency/onboarding"'],
        ROOT / "frontend/src/lib/agency.js": ["onboarding.required", "/agency/onboarding?agency_id="],
        ROOT / "frontend/src/pages/agency/AgencyOnboardingPage.jsx": ["Progress is saved after each step", "Create demo workspace", "Complete onboarding"],
        ROOT / "docs/architecture/commercial-pilot-agency-onboarding-foundation.md": ["newly created agencies", "Legacy agencies", "synthetic"],
    }
    for path, needles in expected.items():
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"Missing {needle!r} in {path.relative_to(ROOT)}"


async def main() -> None:
    verify_registration()
    await verify_service()
    print("Commercial pilot agency onboarding foundation smoke passed.")


if __name__ == "__main__":
    asyncio.run(main())
