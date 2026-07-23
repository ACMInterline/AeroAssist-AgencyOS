from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from database import Database
from models import (
    AgencyDashboardPreferences,
    AgencyEmailSettings,
    AgencyNotificationPreferences,
    AgencyOnboardingEmailStatusUpdate,
    AgencyOnboardingPreferencesUpdate,
    AgencyOnboardingProfile,
    AgencyOnboardingProfileUpdate,
    AuditEvent,
    now_utc,
)


PHASE_LABEL = "phase_58_1_commercial_pilot_agency_onboarding_foundation"
PROFILE_KEY = "commercial_pilot"
ONBOARDING_STEPS = [
    "agency_profile",
    "working_hours",
    "branding",
    "communications_preferences",
    "demo_workspace",
    "review",
]


class AgencyOnboardingError(ValueError):
    pass


def agency_onboarding_readiness_metadata() -> dict[str, Any]:
    return {
        "new_agency_only_enabled": True,
        "legacy_agencies_exempt": True,
        "resumable_wizard_enabled": True,
        "canonical_agency_profile_enabled": True,
        "default_branding_templates_preferences_enabled": True,
        "idempotent_synthetic_demo_workspace_enabled": True,
        "external_provider_execution_enabled": False,
        "automatic_production_seeding_enabled": False,
        "readiness_required": False,
    }


class AgencyOnboardingService:
    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _stable_id(agency_id: str, name: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"aeroassist:onboarding:{agency_id}:{name}"))

    async def _audit(self, agency_id: str, actor_user_id: str, event_type: str, summary: str, metadata: dict | None = None) -> None:
        event = AuditEvent(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type="agency_onboarding",
            entity_id=agency_id,
            summary=summary,
            metadata=metadata or {},
        )
        await self.database.collection("audit_events").insert_one(event.model_dump(mode="json"))

    async def initialize_for_new_agency(self, agency_id: str, actor_user_id: str) -> dict:
        existing = await self.database.collection("agency_onboarding_profiles").find_one(
            {"agency_id": agency_id, "profile_key": PROFILE_KEY}
        )
        if existing:
            return existing
        profile = AgencyOnboardingProfile(
            id=self._stable_id(agency_id, "profile"),
            agency_id=agency_id,
            onboarding_status="not_started",
            created_by_user_id=actor_user_id,
        )
        return await self.database.collection("agency_onboarding_profiles").insert_one(profile.model_dump(mode="json"))

    async def _require_profile(self, agency_id: str) -> dict:
        profile = await self.database.collection("agency_onboarding_profiles").find_one(
            {"agency_id": agency_id, "profile_key": PROFILE_KEY}
        )
        if profile is None:
            raise AgencyOnboardingError("This agency predates guided onboarding and is not required to complete it.")
        return profile

    @staticmethod
    def _validate_working_hours(items: list[dict]) -> list[dict]:
        valid_days = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        normalized: list[dict] = []
        seen: set[str] = set()
        for item in items:
            day = str(item.get("day", "")).strip().lower()
            if day not in valid_days or day in seen:
                raise AgencyOnboardingError("Working hours must contain unique named weekdays.")
            seen.add(day)
            enabled = bool(item.get("enabled", True))
            open_time = item.get("open_time")
            close_time = item.get("close_time")
            if enabled:
                try:
                    opens = time.fromisoformat(str(open_time))
                    closes = time.fromisoformat(str(close_time))
                except ValueError as exc:
                    raise AgencyOnboardingError("Enabled working days require valid HH:MM opening and closing times.") from exc
                if opens >= closes:
                    raise AgencyOnboardingError("Working-day closing time must be later than opening time.")
            normalized.append({"day": day, "enabled": enabled, "open_time": open_time, "close_time": close_time})
        if items and not any(item["enabled"] for item in normalized):
            raise AgencyOnboardingError("At least one working day must be enabled.")
        return normalized

    async def save_profile(self, agency_id: str, payload: AgencyOnboardingProfileUpdate, actor_user_id: str) -> dict:
        profile = await self._require_profile(agency_id)
        updates = payload.model_dump(exclude_unset=True, mode="json")
        current_step = updates.pop("current_step", None)
        if current_step is not None and current_step not in ONBOARDING_STEPS:
            raise AgencyOnboardingError("Unknown onboarding step.")
        if "timezone" in updates:
            try:
                ZoneInfo(str(updates["timezone"]))
            except ZoneInfoNotFoundError as exc:
                raise AgencyOnboardingError("Select a valid IANA time zone.") from exc
        if "default_currency" in updates:
            currency = str(updates["default_currency"]).strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise AgencyOnboardingError("Currency must be a three-letter ISO code.")
            updates["default_currency"] = currency
        if "working_hours" in updates:
            updates["working_hours"] = self._validate_working_hours(updates["working_hours"])
        for required_text in {"name", "legal_name"}:
            if required_text in updates and not str(updates[required_text]).strip():
                raise AgencyOnboardingError(f"{required_text.replace('_', ' ').title()} is required.")
        if updates:
            await self.database.collection("agencies").update_one({"id": agency_id}, updates)
        await self.database.collection("agency_onboarding_profiles").update_one(
            {"id": profile["id"]},
            {
                "onboarding_status": "in_progress",
                "current_step": current_step or profile.get("current_step", "agency_profile"),
                "started_at": profile.get("started_at") or now_utc(),
                "last_saved_at": now_utc(),
            },
        )
        await self._audit(agency_id, actor_user_id, "agency.onboarding.profile_saved", "Saved onboarding agency details.", {"fields": sorted(updates)})
        return await self.get_state(agency_id)

    async def save_email_status(self, agency_id: str, payload: AgencyOnboardingEmailStatusUpdate, actor_user_id: str) -> dict:
        await self._require_profile(agency_id)
        agency = await self.database.collection("agencies").find_one({"id": agency_id})
        existing = await self.database.collection("agency_email_settings").find_one({"agency_id": agency_id})
        values = payload.model_dump(exclude_unset=True, mode="json")
        values.setdefault("sender_name", agency.get("name") if agency else "AeroAssist Agency")
        values.setdefault("sender_email", (agency or {}).get("contact_email") or "onboarding@example.com")
        values.setdefault("mode", "disabled")
        values.setdefault("status", "active")
        if existing:
            await self.database.collection("agency_email_settings").update_one({"id": existing["id"]}, values)
        else:
            settings = AgencyEmailSettings(
                id=self._stable_id(agency_id, "email-settings"), agency_id=agency_id, **values
            )
            await self.database.collection("agency_email_settings").insert_one(settings.model_dump(mode="json"))
        await self._touch(agency_id, "communications_preferences")
        await self._audit(agency_id, actor_user_id, "agency.onboarding.email_status_saved", "Recorded email configuration status.", {"configuration_status": values["configuration_status"]})
        return await self.get_state(agency_id)

    async def save_preferences(self, agency_id: str, payload: AgencyOnboardingPreferencesUpdate, actor_user_id: str) -> dict:
        await self._require_profile(agency_id)
        values = payload.model_dump(mode="json")
        dashboard = AgencyDashboardPreferences(
            id=self._stable_id(agency_id, "dashboard-preferences"),
            agency_id=agency_id,
            landing_page=values["landing_page"],
            compact_mode=values["compact_mode"],
            dashboard_widgets=values["dashboard_widgets"],
            preferred_starting_view=values["preferred_starting_view"],
            visible_operations_sections=values["visible_operations_sections"],
            default_assignment_filter=values["default_assignment_filter"],
            default_urgency_filter=values["default_urgency_filter"],
            seeded_by_onboarding=True,
        ).model_dump(mode="json")
        notifications = AgencyNotificationPreferences(
            id=self._stable_id(agency_id, "notification-preferences"),
            agency_id=agency_id,
            in_app_notifications=values["in_app_notifications"],
            email_notifications=values["email_notifications"],
            assignment_notifications=values["assignment_notifications"],
            deadline_notifications=values["deadline_notifications"],
            service_notifications=values["service_notifications"],
            seeded_by_onboarding=True,
        ).model_dump(mode="json")
        await self._upsert("agency_dashboard_preferences", {"agency_id": agency_id, "preference_key": "default"}, dashboard)
        await self._upsert("agency_notification_preferences", {"agency_id": agency_id, "preference_key": "default"}, notifications)
        await self._touch(agency_id, "communications_preferences")
        await self._audit(agency_id, actor_user_id, "agency.onboarding.preferences_saved", "Saved dashboard and notification preferences.")
        return await self.get_state(agency_id)

    async def confirm_logo(self, agency_id: str, actor_user_id: str) -> dict:
        profile = await self._require_profile(agency_id)
        logo = await self.database.collection("agency_branding_assets").find_one({"agency_id": agency_id, "variant_key": "original"})
        if logo is None:
            logo = await self.database.collection("agency_branding_assets").find_one({"agency_id": agency_id})
        if logo is None:
            raise AgencyOnboardingError("Upload an agency logo before confirming this step.")
        await self.database.collection("agency_onboarding_profiles").update_one(
            {"id": profile["id"]}, {"logo_status": "uploaded", "current_step": "communications_preferences", "last_saved_at": now_utc()}
        )
        await self._audit(agency_id, actor_user_id, "agency.onboarding.logo_confirmed", "Confirmed the onboarding logo.", {"logo_asset_id": logo["id"]})
        return await self.get_state(agency_id)

    async def skip_logo(self, agency_id: str, actor_user_id: str) -> dict:
        profile = await self._require_profile(agency_id)
        await self.database.collection("agency_onboarding_profiles").update_one(
            {"id": profile["id"]}, {"logo_status": "skipped", "current_step": "communications_preferences", "last_saved_at": now_utc()}
        )
        await self._audit(agency_id, actor_user_id, "agency.onboarding.logo_skipped", "Kept the generated default branding without a logo.")
        return await self.get_state(agency_id)

    async def _upsert(self, collection_name: str, filters: dict, document: dict) -> dict:
        existing = await self.database.collection(collection_name).find_one(filters)
        if existing:
            return await self.database.collection(collection_name).update_one({"id": existing["id"]}, document) or existing
        return await self.database.collection(collection_name).insert_one(document)

    async def _touch(self, agency_id: str, current_step: str) -> None:
        profile = await self._require_profile(agency_id)
        await self.database.collection("agency_onboarding_profiles").update_one(
            {"id": profile["id"]},
            {"onboarding_status": "in_progress", "current_step": current_step, "started_at": profile.get("started_at") or now_utc(), "last_saved_at": now_utc()},
        )

    async def seed_defaults(self, agency_id: str, actor_user_id: str) -> dict:
        profile = await self._require_profile(agency_id)
        agency = await self.database.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise AgencyOnboardingError("Agency not found.")
        existing_workspace = await self.database.collection("agency_workspaces").find_one({"agency_id": agency_id})
        workspace = {
            "id": (existing_workspace or {}).get("id") or self._stable_id(agency_id, "agency-workspace"), "agency_id": agency_id,
            "name": agency["name"], "brand_name": agency["name"], "status": "active",
            "default_currency": agency.get("default_currency", "EUR"), "timezone": agency.get("timezone", "UTC"),
            "primary_color": "#2563eb", "secondary_color": "#0f172a", "font_family": "Inter",
            "website_status": "not_configured", "portal_status": "not_configured", "created_at": now_utc(), "updated_at": now_utc(),
        }
        branding = {
            "id": self._stable_id(agency_id, "branding"), "agency_id": agency_id, "workspace_id": workspace["id"],
            "brand_name": agency["name"], "font_family_key": "inter", "corner_radius_key": "subtle",
            "density_key": "comfortable", "theme_mode": "light", "color_palette_key": "aero_blue",
            "field_style_key": "outline", "button_style_key": "solid", "calendar_style_key": "native_polished",
            "card_style_key": "outline", "logo_fit_mode": "contain", "preferred_logo_usage": "horizontal",
            "logo_public_usage_allowed": True, "audit_metadata": {"seeded_by": PHASE_LABEL},
            "created_at": now_utc(), "updated_at": now_utc(),
        }
        await self._upsert("agency_workspaces", {"agency_id": agency_id, "id": workspace["id"]}, workspace)
        await self._upsert("agency_branding_settings", {"agency_id": agency_id}, branding)
        template_ids: list[str] = []
        for key, document_type, name in [
            ("onboarding_itinerary", "itinerary_summary", "Passenger itinerary"),
            ("onboarding_booking_confirmation", "booking_confirmation", "Booking confirmation"),
            ("onboarding_invoice", "invoice_summary", "Invoice summary"),
        ]:
            template_id = self._stable_id(agency_id, f"template:{key}")
            template_ids.append(template_id)
            template = {
                "id": template_id, "agency_id": agency_id, "template_scope": "agency_custom", "scope": "agency",
                "template_key": key, "template_type": document_type, "document_type": document_type, "name": name,
                "title": name, "description": "Onboarding default; review before client use.", "status": "active", "active": True,
                "language": "en", "locale": "en", "version": 1, "branding_profile_id": branding["id"],
                "template_config": {"seeded_by_onboarding": True}, "layout_json": {"density": "comfortable"},
                "content_blocks_json": [], "required_context_json": {}, "created_by_user_id": actor_user_id,
                "created_at": now_utc(), "updated_at": now_utc(),
            }
            await self._upsert("document_templates", {"agency_id": agency_id, "template_key": key}, template)
        default_preferences = AgencyOnboardingPreferencesUpdate(
            dashboard_widgets=["open_requests", "upcoming_departures", "deadlines", "work_queue"]
        )
        await self.save_preferences(agency_id, default_preferences, actor_user_id)
        email = await self.database.collection("agency_email_settings").find_one({"agency_id": agency_id})
        if email is None:
            await self.save_email_status(
                agency_id,
                AgencyOnboardingEmailStatusUpdate(
                    configuration_status="not_configured",
                    sender_name=agency["name"],
                    sender_email=agency.get("contact_email") or "onboarding@example.com",
                ),
                actor_user_id,
            )
        seeded = {**profile.get("seeded_record_ids", {}), "agency_workspace_id": workspace["id"], "branding_id": branding["id"], "document_template_ids": template_ids}
        await self.database.collection("agency_onboarding_profiles").update_one(
            {"id": profile["id"]}, {"defaults_seeded": True, "seeded_record_ids": seeded, "last_saved_at": now_utc()}
        )
        await self._audit(agency_id, actor_user_id, "agency.onboarding.defaults_seeded", "Seeded canonical onboarding defaults.", {"record_ids": seeded})
        return await self.get_state(agency_id)

    async def seed_demo_workspace(self, agency_id: str, actor_user_id: str) -> dict:
        profile = await self._require_profile(agency_id)
        agency = await self.database.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise AgencyOnboardingError("Agency not found.")
        token = self._stable_id(agency_id, "demo")[:8].upper()
        ids = {name: self._stable_id(agency_id, f"demo:{name}") for name in ["client", "passenger", "relationship", "operational_workspace", "request", "passenger_workspace", "flight_1", "flight_2", "trip", "offer", "booking"]}
        today = date.today()
        departure = today + timedelta(days=75)
        return_date = departure + timedelta(days=7)
        demo_meta = {"demo_data": True, "synthetic": True, "source": PHASE_LABEL}
        records: list[tuple[str, dict, dict]] = [
            ("client_profiles", {"id": ids["client"]}, {"id": ids["client"], "agency_id": agency_id, "client_type": "organization", "display_name": "Northstar Consulting (Demo)", "legal_name": "Northstar Consulting Demo Ltd", "primary_email": f"demo.aeroassist+{token.lower()}@example.com", "primary_phone": "+359 2 555 0100", "country": "BG", "city": "Sofia", "address_line_1": "1 Demo Aviation Square", "postal_code": "1000", "preferred_language": "en", "default_currency": agency.get("default_currency", "EUR"), "portal_status": "no_portal_access", "marketing_consent": False, "data_processing_consent": False, "internal_notes": "Synthetic onboarding client. Do not contact.", "status": "active", "created_at": now_utc(), "updated_at": now_utc()}),
            ("passenger_profiles", {"id": ids["passenger"]}, {"id": ids["passenger"], "agency_id": agency_id, "first_name": "Elena", "last_name": "Petrova", "display_name": "Elena Petrova (Demo)", "date_of_birth": date(1988, 4, 14), "passenger_type": "ADT", "gender": "female", "nationality": "BG", "residence_country": "BG", "primary_language": "en", "travel_document_notes": "Demo record: passport details intentionally omitted.", "known_assistance_needs": "WCHR assistance for long airport distances; manual airline confirmation required.", "medical_notes_internal": "Synthetic training data only.", "meal_preferences": "Vegetarian", "loyalty_numbers": [{"airline": "LH", "number": "DEMO-0001"}], "status": "active", "created_at": now_utc(), "updated_at": now_utc()}),
            ("client_passenger_relationships", {"id": ids["relationship"]}, {"id": ids["relationship"], "agency_id": agency_id, "client_id": ids["client"], "passenger_id": ids["passenger"], "relationship_type": "employee", "can_view": True, "can_edit": False, "can_upload_documents": False, "can_request_travel": True, "can_pay": False, "can_receive_notifications": False, "consent_status": "pending", "status": "active", "notes": "Synthetic onboarding relationship.", "created_at": now_utc(), "updated_at": now_utc()}),
            ("operational_travel_workspaces", {"id": ids["operational_workspace"]}, {"id": ids["operational_workspace"], "agency_id": agency_id, "workspace_reference": f"DEMO-OPS-{token}", "workspace_title": "Sofia to New York client visit (Demo)", "workspace_type": "general", "workspace_status": "open", "primary_client_id": ids["client"], "primary_passenger_id": ids["passenger"], "linked_request_ids": [ids["request"]], "linked_trip_ids": [ids["trip"]], "linked_offer_ids": [ids["offer"]], "linked_booking_ids": [ids["booking"]], "linked_ticket_ids": [], "linked_document_ids": [], "priority": "medium", "assigned_team": [], "travel_start_date": departure, "travel_end_date": return_date, "origin_summary": "Sofia (SOF)", "destination_summary": "New York (JFK)", "service_summary": "Business travel with WCHR assistance review", "operational_notes": "Synthetic onboarding workspace. No live supplier action.", "metadata": demo_meta, "metadata_only": True, "created_at": now_utc(), "updated_at": now_utc()}),
            ("travel_request_workspaces", {"id": ids["request"]}, {"id": ids["request"], "agency_id": agency_id, "operational_workspace_id": ids["operational_workspace"], "request_reference": f"DEMO-REQ-{token}", "request_title": "Sofia to New York business trip (Demo)", "request_type": "corporate", "request_status": "quoted", "request_priority": "medium", "client_id": ids["client"], "primary_passenger_id": ids["passenger"], "requester_name": "Elena Petrova (Demo)", "requester_email": f"demo.aeroassist+{token.lower()}@example.com", "requested_service_categories": ["flights", "wheelchair_assistance"], "requested_origin": "SOF", "requested_destination": "JFK", "requested_departure_date": departure, "requested_return_date": return_date, "passenger_count": 1, "passenger_type_summary": "1 adult", "flexibility_notes": "+/- 1 day", "special_service_notes": "WCHR request requires manual review and carrier confirmation.", "budget_notes": "Target budget EUR 3,000", "deadline": today + timedelta(days=10), "internal_notes": "Synthetic onboarding request.", "linked_trip_ids": [ids["trip"]], "linked_offer_ids": [ids["offer"]], "linked_document_ids": [], "metadata": demo_meta, "metadata_only": True, "created_at": now_utc(), "updated_at": now_utc()}),
            ("passenger_workspaces", {"id": ids["passenger_workspace"]}, {"id": ids["passenger_workspace"], "agency_id": agency_id, "operational_workspace_id": ids["operational_workspace"], "passenger_reference": f"DEMO-PAX-{token}", "passenger_status": "review", "title": "Ms", "first_name": "Elena", "last_name": "Petrova", "preferred_name": "Elena", "date_of_birth": date(1988, 4, 14), "nationality": "BG", "citizenship": "BG", "loyalty_programs": [{"airline": "LH", "status": "demo"}], "frequent_flyer_numbers": [{"airline": "LH", "number": "DEMO-0001"}], "mobility_profile": {"wchr": True, "manual_confirmation_required": True}, "dietary_profile": {"preference": "vegetarian"}, "assistance_profile": {"airport_distance_assistance": True}, "baggage_profile": {"checked_bags": 2}, "seating_preferences": {"aisle": True}, "language_preferences": ["en", "bg"], "contact_email": f"demo.aeroassist+{token.lower()}@example.com", "linked_request_ids": [ids["request"]], "linked_trip_ids": [ids["trip"]], "linked_offer_ids": [ids["offer"]], "linked_booking_ids": [ids["booking"]], "internal_notes": "Synthetic onboarding passenger workspace.", "metadata": demo_meta, "metadata_only": True, "created_at": now_utc(), "updated_at": now_utc()}),
        ]
        flight_specs = [
            ("flight_1", "LH1427", "SOF", "FRA", datetime.combine(departure, time(6, 10), tzinfo=timezone.utc), datetime.combine(departure, time(7, 35), tzinfo=timezone.utc), "Connection in Frankfurt: 2h 25m"),
            ("flight_2", "LH400", "FRA", "JFK", datetime.combine(departure, time(10, 0), tzinfo=timezone.utc), datetime.combine(departure, time(18, 20), tzinfo=timezone.utc), "Arrives New York same local day"),
        ]
        for key, flight_number, origin, destination, departs, arrives, connection in flight_specs:
            records.append(("flight_workspaces", {"id": ids[key]}, {"id": ids[key], "agency_id": agency_id, "operational_workspace_id": ids["operational_workspace"], "flight_reference": f"DEMO-{flight_number}-{token}", "flight_status": "schedule_review", "flight_type": "scheduled", "travel_direction": "outbound", "airline_code": "LH", "airline_name": "Lufthansa", "marketing_carrier": "LH", "operating_carrier": "LH", "flight_number": flight_number, "operating_flight_number": flight_number, "departure_airport": origin, "arrival_airport": destination, "departure_datetime": departs, "arrival_datetime": arrives, "aircraft_type": "Airbus/Boeing family - verify", "cabin_class": "business", "booking_class": "C", "fare_family": "Business Flex", "baggage_summary": "2 checked pieces; verify against accepted fare", "connection_summary": connection, "passenger_ids": [ids["passenger"]], "linked_request_ids": [ids["request"]], "linked_trip_ids": [ids["trip"]], "linked_offer_ids": [ids["offer"]], "linked_booking_ids": [ids["booking"]], "operational_notes": "Synthetic schedule; no live schedule synchronization.", "metadata": demo_meta, "metadata_only": True, "created_at": now_utc(), "updated_at": now_utc()}))
        records.extend([
            ("trip_workspaces", {"id": ids["trip"]}, {"id": ids["trip"], "agency_id": agency_id, "operational_workspace_id": ids["operational_workspace"], "trip_reference": f"DEMO-TRIP-{token}", "trip_status": "planning", "journey_type": "round_trip", "service_type": "corporate_air_travel", "client_id": ids["client"], "passenger_ids": [ids["passenger"]], "flight_workspace_ids": [ids["flight_1"], ids["flight_2"]], "travel_request_ids": [ids["request"]], "offer_ids": [ids["offer"]], "booking_ids": [ids["booking"]], "departure_country": "BG", "destination_country": "US", "departure_city": "Sofia", "destination_city": "New York", "origin_airport": "SOF", "destination_airport": "JFK", "departure_date": departure, "return_date": return_date, "travel_duration": "7 days", "passenger_count": 1, "itinerary_summary": "SOF-FRA-JFK outbound; return options require review.", "baggage_summary": "2 checked pieces proposed", "service_summary": "WCHR assistance requested", "operational_priority": "normal", "operational_notes": "Synthetic onboarding trip; incomplete by design for training.", "metadata": demo_meta, "metadata_only": True, "created_at": now_utc(), "updated_at": now_utc()}),
            ("offer_workspaces_v2", {"id": ids["offer"]}, {"id": ids["offer"], "agency_id": agency_id, "operational_workspace_id": ids["operational_workspace"], "trip_workspace_id": ids["trip"], "offer_reference": f"DEMO-OFFER-{token}", "offer_status": "review", "offer_type": "flight", "client_id": ids["client"], "passenger_ids": [ids["passenger"]], "flight_workspace_ids": [ids["flight_1"], ids["flight_2"]], "offer_title": "Business Flex via Frankfurt (Demo)", "offer_summary": "Illustrative option requiring live price and availability verification.", "destination_summary": "New York", "itinerary_summary": "SOF-FRA-JFK; return itinerary pending", "pricing_summary": "Illustrative metadata only", "currency": "EUR", "total_price": 2480.40, "taxes_summary": "EUR 412.40 illustrative taxes", "fees_summary": "EUR 45.00 agency service fee illustration", "ancillary_summary": "WCHR request pending airline confirmation", "baggage_summary": "2 checked pieces proposed", "seat_summary": "Aisle preference; no assignment", "meal_summary": "Vegetarian preference", "validity_date": today + timedelta(days=7), "agent_notes": "Use this record to explore the offer workflow.", "customer_notes": "Demo proposal only; not valid for travel.", "internal_notes": "No live price, booking, or provider call was made.", "linked_booking_ids": [ids["booking"]], "metadata": demo_meta, "metadata_only": True, "created_at": now_utc(), "updated_at": now_utc()}),
            ("booking_workspaces", {"id": ids["booking"]}, {"id": ids["booking"], "agency_id": agency_id, "operational_workspace_id": ids["operational_workspace"], "trip_workspace_id": ids["trip"], "source_context": "offer_readiness", "client_id": ids["client"], "passenger_ids": [ids["passenger"]], "flight_workspace_ids": [ids["flight_1"], ids["flight_2"]], "trip_id": ids["trip"], "request_id": ids["request"], "offer_workspace_id": ids["offer"], "workspace_number": f"DEMO-BKG-{token}", "booking_reference": None, "airline_pnr": None, "gds_record_locator": None, "supplier_reference": None, "title": "Booking readiness practice (Demo)", "status": "draft", "booking_status": "readiness_review", "booking_type": "manual_training", "booking_source": "synthetic_onboarding", "provider_target": "manual", "booking_deadline": today + timedelta(days=7), "payment_summary": "No payment collected", "booking_summary": "Draft workspace only; no PNR created", "operational_notes": "Synthetic onboarding booking workspace.", "source_snapshot_json": {"offer_workspace_id": ids["offer"], "synthetic": True}, "passengers_snapshot_json": [{"passenger_id": ids["passenger"], "name": "Elena Petrova (Demo)"}], "segments_snapshot_json": [{"flight_workspace_id": ids["flight_1"], "route": "SOF-FRA"}, {"flight_workspace_id": ids["flight_2"], "route": "FRA-JFK"}], "pricing_snapshot_json": {"currency": "EUR", "total": 2480.40, "illustrative": True}, "services_snapshot_json": {"wchr": "manual_review"}, "warnings_json": [{"code": "DEMO_ONLY", "message": "No live booking or price verification."}], "metadata": demo_meta, "metadata_only": True, "booking_workspace_metadata_only": True, "booking_execution_disabled": True, "live_booking_creation_disabled": True, "ticket_issuance_disabled": True, "gds_connectivity_disabled": True, "ndc_connectivity_disabled": True, "airline_api_calls_disabled": True, "payment_processing_disabled": True, "automation_disabled": True, "created_at": now_utc(), "updated_at": now_utc()}),
        ])
        for collection_name, filters, document in records:
            await self._upsert(collection_name, {"agency_id": agency_id, **filters}, document)
        seeded = {**profile.get("seeded_record_ids", {}), "demo": ids}
        await self.database.collection("agency_onboarding_profiles").update_one(
            {"id": profile["id"]}, {"demo_workspace_seeded": True, "seeded_record_ids": seeded, "current_step": "review", "last_saved_at": now_utc()}
        )
        await self._audit(agency_id, actor_user_id, "agency.onboarding.demo_workspace_seeded", "Created the synthetic onboarding travel workspace.", {"record_ids": ids, "synthetic": True})
        return await self.get_state(agency_id)

    async def complete(self, agency_id: str, actor_user_id: str) -> dict:
        state = await self.get_state(agency_id)
        if state.get("legacy_exempt"):
            raise AgencyOnboardingError("Legacy-exempt agencies do not require onboarding completion.")
        missing = [step["key"] for step in state["steps"] if step["key"] != "review" and not step["complete"]]
        if missing:
            raise AgencyOnboardingError(f"Complete these onboarding steps first: {', '.join(missing)}.")
        profile = state["profile"]
        completed_at = now_utc()
        await self.database.collection("agency_onboarding_profiles").update_one(
            {"id": profile["id"]},
            {"onboarding_status": "completed", "current_step": "review", "completed_steps": ONBOARDING_STEPS, "progress_percent": 100, "completed_at": completed_at, "completed_by_user_id": actor_user_id, "last_saved_at": completed_at},
        )
        await self.database.collection("agencies").update_one({"id": agency_id}, {"status": "active"})
        await self._audit(agency_id, actor_user_id, "agency.onboarding.completed", "Completed commercial pilot agency onboarding.")
        return await self.get_state(agency_id)

    async def get_state(self, agency_id: str) -> dict:
        agency = await self.database.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise AgencyOnboardingError("Agency not found.")
        profile = await self.database.collection("agency_onboarding_profiles").find_one({"agency_id": agency_id, "profile_key": PROFILE_KEY})
        if profile is None:
            return {"required": False, "legacy_exempt": True, "agency": agency, "profile": None, "progress_percent": 100, "steps": []}
        dashboard = await self.database.collection("agency_dashboard_preferences").find_one({"agency_id": agency_id, "preference_key": "default"})
        notifications = await self.database.collection("agency_notification_preferences").find_one({"agency_id": agency_id, "preference_key": "default"})
        email = await self.database.collection("agency_email_settings").find_one({"agency_id": agency_id})
        branding = await self.database.collection("agency_branding_settings").find_one({"agency_id": agency_id})
        profile_complete = all(str(agency.get(field) or "").strip() for field in ["name", "legal_name", "contact_name", "contact_email", "contact_phone", "address_line_1", "city", "country", "timezone", "default_currency"])
        hours_complete = bool(agency.get("working_hours")) and any(day.get("enabled") for day in agency.get("working_hours", []))
        preferences_complete = bool(dashboard and notifications and email and email.get("configuration_status"))
        completed = profile.get("onboarding_status") == "completed"
        flags = {
            "agency_profile": profile_complete,
            "working_hours": hours_complete,
            "branding": bool(branding and profile.get("logo_status") in {"uploaded", "skipped"}),
            "communications_preferences": bool(profile.get("defaults_seeded") and preferences_complete),
            "demo_workspace": bool(profile.get("demo_workspace_seeded")),
            "review": completed,
        }
        completed_steps = [key for key in ONBOARDING_STEPS if flags[key]]
        progress = 100 if completed else round(100 * sum(flags.values()) / len(ONBOARDING_STEPS))
        if completed_steps != profile.get("completed_steps") or progress != profile.get("progress_percent"):
            profile = await self.database.collection("agency_onboarding_profiles").update_one(
                {"id": profile["id"]}, {"completed_steps": completed_steps, "progress_percent": progress}
            ) or profile
        steps = [{"key": key, "label": key.replace("_", " ").title(), "complete": flags[key]} for key in ONBOARDING_STEPS]
        return {
            "required": not completed,
            "legacy_exempt": False,
            "agency": agency,
            "profile": profile,
            "progress_percent": progress,
            "steps": steps,
            "branding": branding,
            "dashboard_preferences": dashboard,
            "notification_preferences": notifications,
            "email_settings": email,
            "demo_workspace": profile.get("seeded_record_ids", {}).get("demo"),
            "safety": {"synthetic_only": True, "provider_execution": False, "booking_execution": False, "payment_execution": False},
        }
