from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from database import Database
from models import (
    AfterSalesCase,
    AfterSalesCaseItem,
    AfterSalesFinancialImpact,
    AuditEvent,
    BookingReadinessPackage,
    BookingTimelineEvent,
    BookingWorkspace,
    ClientPassengerRelationship,
    ClientProfile,
    DocumentDelivery,
    DocumentPackage,
    DocumentWorkspace,
    EmdWorkspace,
    FlightWorkspace,
    Invoice,
    InvoiceLineItem,
    OfferAcceptance,
    OfferBookingHandoff,
    OfferOption,
    OfferWorkspace,
    OfferWorkspaceV2,
    OperationalDeadline,
    OperationalTimeline,
    OperationalTravelWorkspace,
    OperationalWorkflowEvent,
    OperationalWorkflowInstance,
    OperationalWorkItem,
    PassengerProfile,
    PassengerServiceRequest,
    PassengerWorkspace,
    PaymentRecord,
    RequestTask,
    RenderedDocument,
    SsrOsiWorkspace,
    TicketWorkspace,
    TravelRequest,
    TravelRequestWorkspace,
    TripAcceptedOfferSnapshot,
    TripWorkspace,
)
from services.canonical_commercial_lifecycle_service import canonical_json_hash


PHASE_LABEL = "phase_58_3_complete_pilot_agency_experience"
GENERATOR_VERSION = 1
MAX_GENERATED_RECORDS = 400

OPERATIONAL_AREAS = [
    "Clients and associated passengers",
    "Requests, trips, and multi-segment itineraries",
    "Offer comparison, acceptance, and booking readiness",
    "Booking, ticket, and EMD mirrors",
    "Passenger services and SSR/OSI review",
    "Documents and document packages",
    "Invoice and payment lifecycle examples",
    "Tasks, deadlines, timelines, and communications",
    "Disruption, change, exchange, and refund cases",
    "Operations Command Centre queues and alerts",
]

PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "small_agency": {
        "label": "Small Agency",
        "description": "A compact owner-operated agency with eight varied active and historical cases.",
        "scenario_count": 8,
        "estimated_record_count": 305,
        "team_code": "pilot-desk",
        "fare_multiplier": 1.0,
        "client_mix": "leisure and small business",
    },
    "medium_agency": {
        "label": "Medium Agency",
        "description": "A multi-consultant agency with additional group and follow-up workload.",
        "scenario_count": 10,
        "estimated_record_count": 365,
        "team_code": "operations",
        "fare_multiplier": 1.05,
        "client_mix": "leisure, family, and managed business",
    },
    "corporate_agency": {
        "label": "Corporate Agency",
        "description": "A managed-travel desk emphasizing approvals, deadlines, and complex servicing.",
        "scenario_count": 10,
        "estimated_record_count": 365,
        "team_code": "corporate-travel",
        "fare_multiplier": 1.12,
        "client_mix": "corporate and executive travel",
    },
    "luxury_leisure_agency": {
        "label": "Luxury Leisure Agency",
        "description": "A high-touch leisure portfolio with premium fares and detailed service follow-up.",
        "scenario_count": 10,
        "estimated_record_count": 365,
        "team_code": "concierge",
        "fare_multiplier": 1.35,
        "client_mix": "premium family and leisure travel",
    },
}

SCENARIOS: list[dict[str, Any]] = [
    {
        "key": "family_ready_ticketing",
        "label": "Family booking ready for ticketing",
        "route": [("SOF", "FRA", "LH1427"), ("FRA", "JFK", "LH400")],
        "departure_offset": 2,
        "request_status": "quoted",
        "offer_status": "accepted",
        "booking_status": "confirmed",
        "trip_status": "ready",
        "passenger_count": 3,
        "services": ["WCHR", "VGML"],
        "accepted": True,
        "booking": True,
        "ticket_state": None,
        "queue": "ready_ticketing",
    },
    {
        "key": "corporate_medical_waiting_airline",
        "label": "Corporate medical case waiting for airline",
        "route": [("LHR", "ZRH", "LX317"), ("ZRH", "SIN", "LX176")],
        "departure_offset": 7,
        "request_status": "waiting",
        "offer_status": "accepted",
        "booking_status": "blocked",
        "trip_status": "planning",
        "passenger_count": 1,
        "services": ["WCHC", "MEDA"],
        "accepted": True,
        "booking": True,
        "ticket_state": None,
        "queue": "waiting_airline",
    },
    {
        "key": "offer_expiry_waiting_customer",
        "label": "Leisure offer expiring today",
        "route": [("AMS", "MAD", "KL1503"), ("MAD", "LPA", "IB3832")],
        "departure_offset": 21,
        "request_status": "quoted",
        "offer_status": "draft",
        "booking_status": None,
        "trip_status": "planning",
        "passenger_count": 1,
        "services": ["WCHS", "BLND"],
        "accepted": False,
        "booking": False,
        "ticket_state": None,
        "queue": "waiting_client",
    },
    {
        "key": "umnr_missing_documents",
        "label": "Unaccompanied minor missing documents",
        "route": [("DUB", "CDG", "AF1617")],
        "departure_offset": 14,
        "request_status": "triage",
        "offer_status": "declined",
        "booking_status": None,
        "trip_status": "planning",
        "passenger_count": 1,
        "services": ["UMNR", "DEAF"],
        "accepted": False,
        "booking": False,
        "ticket_state": None,
        "queue": "awaiting_approval",
    },
    {
        "key": "pets_multicity",
        "label": "Multi-city pet travel awaiting booking",
        "route": [("FCO", "VIE", "OS502"), ("VIE", "YYZ", "OS071"), ("YYZ", "YUL", "AC424")],
        "departure_offset": 35,
        "request_status": "quoted",
        "offer_status": "accepted",
        "booking_status": None,
        "trip_status": "planning",
        "passenger_count": 1,
        "services": ["PETC", "AVIH"],
        "accepted": True,
        "booking": False,
        "ticket_state": None,
        "queue": "waiting_supplier",
    },
    {
        "key": "adaptive_sports_completed",
        "label": "Completed adaptive sports journey",
        "route": [("MUC", "OSL", "LH2452")],
        "departure_offset": -18,
        "request_status": "completed",
        "offer_status": "accepted",
        "booking_status": "ticketed",
        "trip_status": "completed",
        "passenger_count": 1,
        "services": ["EXST", "SPORTS_BAGGAGE", "WHEELCHAIR_EQUIPMENT"],
        "accepted": True,
        "booking": True,
        "ticket_state": "flown",
        "queue": "completed",
    },
    {
        "key": "cancelled_flight_refund",
        "label": "Cancelled flight with refund and voucher review",
        "route": [("CDG", "LIS", "AF1124")],
        "departure_offset": 1,
        "request_status": "open",
        "offer_status": "accepted",
        "booking_status": "cancelled",
        "trip_status": "active",
        "passenger_count": 1,
        "services": [],
        "accepted": True,
        "booking": True,
        "ticket_state": "refunded",
        "queue": "disruption",
        "after_sales": "disruption_irregular_operation",
    },
    {
        "key": "schedule_change_partial_ticket",
        "label": "Schedule change with partial ticketing",
        "route": [("BRU", "IST", "TK1942"), ("IST", "NBO", "TK607")],
        "departure_offset": 4,
        "request_status": "open",
        "offer_status": "accepted",
        "booking_status": "ticketing_pending",
        "trip_status": "active",
        "passenger_count": 2,
        "services": [],
        "accepted": True,
        "booking": True,
        "ticket_state": "open_for_use",
        "queue": "workflow_blocker",
        "after_sales": "schedule_change",
    },
    {
        "key": "completed_archived",
        "label": "Completed journey retained as an archived record",
        "route": [("CPH", "KEF", "FI205")],
        "departure_offset": -60,
        "request_status": "archived",
        "offer_status": "archived",
        "booking_status": "ticketed",
        "trip_status": "archived",
        "passenger_count": 1,
        "services": [],
        "accepted": True,
        "booking": True,
        "ticket_state": "closed",
        "queue": "completed",
    },
    {
        "key": "outstanding_follow_up",
        "label": "Premium itinerary with outstanding supplier follow-up",
        "route": [("JFK", "LHR", "BA178"), ("LHR", "MLE", "BA061")],
        "departure_offset": 42,
        "request_status": "researching",
        "offer_status": "ready",
        "booking_status": None,
        "trip_status": "planning",
        "passenger_count": 1,
        "services": [],
        "accepted": False,
        "booking": False,
        "ticket_state": None,
        "queue": "waiting_supplier",
    },
]

SYNTHETIC_PEOPLE = [
    ("Elena", "Petrova", date(1988, 4, 14)),
    ("Daniel", "Meyer", date(1979, 11, 3)),
    ("Sofia", "Alvarez", date(1992, 6, 22)),
    ("Marek", "Novak", date(2012, 9, 18)),
    ("Chiara", "Romano", date(1985, 2, 8)),
    ("Ingrid", "Larsen", date(1990, 8, 27)),
    ("Amelie", "Laurent", date(1983, 1, 12)),
    ("Jonas", "De Smet", date(1976, 7, 5)),
    ("Klara", "Jensen", date(1994, 3, 30)),
    ("Noah", "Williams", date(1981, 12, 9)),
]


def demo_profile_catalog() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": config["label"],
            "description": config["description"],
            "estimated_record_count": config["estimated_record_count"],
            "scenario_count": config["scenario_count"],
            "client_mix": config["client_mix"],
            "generated_operational_areas": OPERATIONAL_AREAS,
            "scenario_preview": [item["label"] for item in SCENARIOS[: config["scenario_count"]]],
        }
        for key, config in PROFILE_CATALOG.items()
    ]


class AgencyDemoWorkspaceGenerator:
    def __init__(
        self,
        database: Database,
        *,
        agency: dict[str, Any],
        actor_user_id: str,
        demo_profile: str,
        anchor_date: date,
    ) -> None:
        if demo_profile not in PROFILE_CATALOG:
            raise ValueError("Unknown demo workspace profile.")
        self.database = database
        self.agency = agency
        self.agency_id = str(agency["id"])
        self.actor_user_id = actor_user_id
        self.demo_profile = demo_profile
        self.profile = PROFILE_CATALOG[demo_profile]
        self.anchor_date = anchor_date
        self.anchor = datetime.combine(anchor_date, time(9, 0), tzinfo=timezone.utc)
        self.records: list[tuple[str, str, dict[str, Any]]] = []
        self.ids: dict[str, Any] = {}

    def stable_id(self, name: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"aeroassist:onboarding:{self.agency_id}:{name}"))

    def _key(self, scenario: dict[str, Any], entity: str, suffix: str | int | None = None) -> str:
        legacy = {
            "client": "demo:client",
            "passenger": "demo:passenger",
            "relationship": "demo:relationship",
            "operational_workspace": "demo:operational_workspace",
            "request_workspace": "demo:request",
            "passenger_workspace": "demo:passenger_workspace",
            "flight": "demo:flight_1",
            "trip": "demo:trip",
            "offer_v2": "demo:offer",
            "booking": "demo:booking",
        }
        if scenario["key"] == SCENARIOS[0]["key"] and suffix in {None, 0} and entity in legacy:
            return legacy[entity]
        tail = f":{suffix}" if suffix is not None else ""
        return f"demo:case:{scenario['key']}:{entity}{tail}"

    def _add(self, collection: str, model: Any, key: str, values: dict[str, Any], *, scenario: str | None = None) -> str:
        record_id = self.stable_id(key)
        data = {
            "id": record_id,
            "created_at": values.pop("created_at", self.anchor - timedelta(days=2)),
            **values,
        }
        if "updated_at" in model.model_fields:
            data.setdefault("updated_at", self.anchor - timedelta(hours=1))
        if "metadata" in model.model_fields:
            data["metadata"] = {
                **data.get("metadata", {}),
                "demo_data": True,
                "synthetic": True,
                "source": PHASE_LABEL,
                "generator_version": GENERATOR_VERSION,
                "demo_profile": self.demo_profile,
                "scenario": scenario,
            }
        document = model.model_validate(data).model_dump(mode="json")
        self.records.append((collection, record_id, document))
        return record_id

    async def _persist(self) -> None:
        if len(self.records) > MAX_GENERATED_RECORDS:
            raise ValueError(f"Demo generation exceeded its {MAX_GENERATED_RECORDS}-record safety bound.")
        for collection, record_id, document in self.records:
            filters = {"agency_id": self.agency_id, "id": record_id} if "agency_id" in document else {"id": record_id}
            existing = await self.database.collection(collection).find_one(filters)
            if existing:
                await self.database.collection(collection).update_one(filters, document)
            else:
                await self.database.collection(collection).insert_one(document)

    def _passenger_count(self, scenario: dict[str, Any]) -> int:
        return int(scenario.get("passenger_count") or 1)

    def _person(self, scenario_index: int, passenger_index: int) -> tuple[str, str, date]:
        if scenario_index == 0 and passenger_index == 1:
            return "Nikolai", "Petrov", date(1986, 10, 2)
        if scenario_index == 0 and passenger_index == 2:
            return "Mila", "Petrova", date(2014, 5, 19)
        if scenario_index == 7 and passenger_index == 1:
            return "Eva", "De Smet", date(1978, 2, 11)
        return SYNTHETIC_PEOPLE[scenario_index % len(SYNTHETIC_PEOPLE)]

    def _service_definition(self, code: str) -> dict[str, Any]:
        definitions = {
            "UMNR": ("unaccompanied_minor", "UMNR", "unaccompanied_minor", "UMNR handling and guardian details"),
            "WCHR": ("mobility", "PRM", "wheelchair_ramp", "Wheelchair assistance for long airport distances"),
            "WCHS": ("mobility", "PRM", "wheelchair_steps", "Wheelchair assistance including stairs"),
            "WCHC": ("mobility", "PRM", "wheelchair_cabin", "Passenger requires wheelchair to cabin seat"),
            "MEDA": ("medical", "MEDICAL", "medical_clearance", "Medical clearance and MEDIF review"),
            "PETC": ("pet", "PETS", "pet_in_cabin", "Pet in cabin request"),
            "AVIH": ("pet", "PETS", "animal_in_hold", "Animal in hold request"),
            "EXST": ("seating", "SEATING", "extra_seat", "Extra seat requirement"),
            "VGML": ("dietary", "MEAL", "vegetarian_meal", "Vegetarian meal request"),
            "BLND": ("visual_impairment", "PRM", "visual_assistance", "Visual impairment assistance"),
            "DEAF": ("hearing_impairment", "PRM", "hearing_assistance", "Hearing impairment assistance"),
            "SPORTS_BAGGAGE": ("sports_equipment", "OTHER", "sports_baggage", "Oversized sports baggage review"),
            "WHEELCHAIR_EQUIPMENT": ("mobility", "PRM", "wheelchair_equipment", "Wheelchair dimensions and battery details"),
        }
        need, category, service_type, label = definitions[code]
        return {"need_category": need, "category": category, "service_type": service_type, "label": label}

    def _build_scenario(self, scenario: dict[str, Any], index: int) -> None:
        scenario_key = scenario["key"]
        token = self.stable_id(f"demo:token:{scenario_key}").replace("-", "")[:6].upper()
        departure = self.anchor_date + timedelta(days=int(scenario["departure_offset"]))
        return_date = departure + timedelta(days=max(3, len(scenario["route"]) + 2))
        currency = str(self.agency.get("default_currency") or "EUR").upper()
        multiplier = float(self.profile["fare_multiplier"])
        base_fare = round((680 + index * 145) * multiplier, 2)
        taxes = round(base_fare * 0.19, 2)
        total = round(base_fare + taxes + 45, 2)
        status = scenario["trip_status"]
        client_id = self._add(
            "client_profiles",
            ClientProfile,
            self._key(scenario, "client"),
            {
                "agency_id": self.agency_id,
                "client_type": "organization" if index in {1, 9} or self.demo_profile == "corporate_agency" else "family_household",
                "display_name": f"{scenario['label']} Client (Demo)",
                "legal_name": f"Synthetic {self.profile['label']} Client {index + 1}",
                "primary_email": f"pilot-demo-{token.lower()}@example.com",
                "primary_phone": f"+359 2 555 {1000 + index:04d}",
                "country": "BG",
                "city": "Sofia",
                "address_line_1": f"{index + 1} Synthetic Aviation Square",
                "postal_code": "1000",
                "preferred_language": "en",
                "default_currency": currency,
                "portal_status": "no_portal_access",
                "marketing_consent": False,
                "data_processing_consent": False,
                "internal_notes": "Synthetic pilot client. Never contact.",
                "client_visible_notes": "Training workspace only.",
                "status": "active",
            },
            scenario=scenario_key,
        )
        operational_id = self.stable_id(self._key(scenario, "operational_workspace"))
        request_workspace_id = self.stable_id(self._key(scenario, "request_workspace"))
        request_id = self.stable_id(self._key(scenario, "request"))
        trip_id = self.stable_id(self._key(scenario, "trip"))
        offer_workspace_id = self.stable_id(self._key(scenario, "offer"))
        offer_v2_id = self.stable_id(self._key(scenario, "offer_v2"))
        booking_id = self.stable_id(self._key(scenario, "booking")) if scenario["booking"] else None
        passenger_ids: list[str] = []
        passenger_workspace_ids: list[str] = []
        for passenger_index in range(self._passenger_count(scenario)):
            first_name, last_name, dob = self._person(index, passenger_index)
            passenger_id = self._add(
                "passenger_profiles",
                PassengerProfile,
                self._key(scenario, "passenger", passenger_index if passenger_index else None),
                {
                    "agency_id": self.agency_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "display_name": f"{first_name} {last_name} (Demo)",
                    "date_of_birth": dob,
                    "passenger_type": "CHD" if dob.year > 2010 else "ADT",
                    "gender": "unspecified",
                    "nationality": "BG",
                    "residence_country": "BG",
                    "primary_language": "en",
                    "travel_document_notes": "Synthetic passport details intentionally omitted.",
                    "known_assistance_needs": ", ".join(scenario["services"]) or "None recorded",
                    "medical_notes_internal": "Synthetic training data only.",
                    "meal_preferences": "Vegetarian" if "VGML" in scenario["services"] else None,
                    "loyalty_numbers": [{"airline": scenario["route"][0][2][:2], "number": f"DEMO-{token}-{passenger_index + 1}"}],
                    "status": "active",
                },
                scenario=scenario_key,
            )
            passenger_ids.append(passenger_id)
            relationship_id = self._add(
                "client_passenger_relationships",
                ClientPassengerRelationship,
                self._key(scenario, "relationship", passenger_index if passenger_index else None),
                {
                    "agency_id": self.agency_id,
                    "client_id": client_id,
                    "passenger_id": passenger_id,
                    "relationship_type": "child" if dob.year > 2010 else ("employee" if index in {1, 9} else "self"),
                    "can_view": True,
                    "can_edit": False,
                    "can_upload_documents": False,
                    "can_request_travel": True,
                    "can_pay": passenger_index == 0,
                    "can_receive_notifications": False,
                    "consent_status": "pending",
                    "status": "active",
                    "notes": "Synthetic onboarding relationship.",
                },
                scenario=scenario_key,
            )
            passenger_workspace_id = self._add(
                "passenger_workspaces",
                PassengerWorkspace,
                self._key(scenario, "passenger_workspace", passenger_index if passenger_index else None),
                {
                    "agency_id": self.agency_id,
                    "operational_workspace_id": operational_id,
                    "passenger_reference": f"DEMO-PAX-{token}-{passenger_index + 1}",
                    "passenger_status": "incomplete" if scenario_key == "umnr_missing_documents" else "ready",
                    "first_name": first_name,
                    "last_name": last_name,
                    "preferred_name": first_name,
                    "date_of_birth": dob,
                    "nationality": "BG",
                    "citizenship": "BG",
                    "identity_document_type": "passport",
                    "loyalty_programs": [{"carrier": scenario["route"][0][2][:2], "status": "synthetic"}],
                    "mobility_profile": {"requirements": [code for code in scenario["services"] if code.startswith("WCH")]},
                    "medical_profile": {"meda_review": "MEDA" in scenario["services"]},
                    "dietary_profile": {"vgml": "VGML" in scenario["services"]},
                    "assistance_profile": {"ssr_codes": scenario["services"]},
                    "baggage_profile": {"sports_equipment": "SPORTS_BAGGAGE" in scenario["services"]},
                    "seating_preferences": {"extra_seat": "EXST" in scenario["services"], "aisle": True},
                    "language_preferences": ["en"],
                    "contact_email": f"pilot-demo-{token.lower()}-{passenger_index + 1}@example.com",
                    "linked_request_ids": [request_workspace_id],
                    "linked_trip_ids": [trip_id],
                    "linked_offer_ids": [offer_v2_id],
                    "linked_booking_ids": [booking_id] if booking_id else [],
                    "internal_notes": f"Synthetic profile linked by relationship {relationship_id}.",
                },
                scenario=scenario_key,
            )
            passenger_workspace_ids.append(passenger_workspace_id)

        segment_ids: list[str] = []
        for segment_index, (origin, destination, flight_number) in enumerate(scenario["route"]):
            departure_dt = datetime.combine(departure, time(7 + segment_index * 4, 15), tzinfo=timezone.utc)
            arrival_dt = departure_dt + timedelta(hours=2 + segment_index * 2)
            flight_id = self._add(
                "flight_workspaces",
                FlightWorkspace,
                self._key(scenario, "flight", segment_index),
                {
                    "agency_id": self.agency_id,
                    "operational_workspace_id": operational_id,
                    "flight_reference": f"DEMO-{flight_number}-{token}",
                    "flight_status": "schedule_review" if scenario_key in {"cancelled_flight_refund", "schedule_change_partial_ticket"} else ("flown" if departure < self.anchor_date else "ready"),
                    "flight_type": "scheduled",
                    "travel_direction": "outbound",
                    "airline_code": flight_number[:2],
                    "airline_name": {"LH": "Lufthansa", "LX": "SWISS", "KL": "KLM", "IB": "Iberia", "AF": "Air France", "OS": "Austrian Airlines", "AC": "Air Canada", "TK": "Turkish Airlines", "FI": "Icelandair", "BA": "British Airways"}.get(flight_number[:2], "Demo Airline"),
                    "marketing_carrier": flight_number[:2],
                    "operating_carrier": flight_number[:2],
                    "flight_number": flight_number,
                    "operating_flight_number": flight_number,
                    "departure_airport": origin,
                    "arrival_airport": destination,
                    "departure_datetime": departure_dt,
                    "arrival_datetime": arrival_dt,
                    "aircraft_type": "Aircraft family requires live verification",
                    "cabin_class": "business" if index in {1, 9} or self.demo_profile == "luxury_leisure_agency" else "economy",
                    "booking_class": "C" if index in {1, 9} else "Y",
                    "fare_family": "Flex",
                    "baggage_summary": "Illustrative allowance; verify accepted fare and operating carrier.",
                    "connection_summary": "Protected connection in synthetic itinerary" if len(scenario["route"]) > 1 else None,
                    "passenger_ids": passenger_ids,
                    "linked_request_ids": [request_workspace_id],
                    "linked_trip_ids": [trip_id],
                    "linked_offer_ids": [offer_v2_id],
                    "linked_booking_ids": [booking_id] if booking_id else [],
                    "operational_notes": "Cancelled by synthetic schedule-change scenario." if scenario_key == "cancelled_flight_refund" else "No live schedule lookup was performed.",
                },
                scenario=scenario_key,
            )
            segment_ids.append(flight_id)

        document_id = self.stable_id(self._key(scenario, "document"))
        ticket_id = self.stable_id(self._key(scenario, "ticket")) if scenario["ticket_state"] else None
        emd_id = self.stable_id(self._key(scenario, "emd")) if scenario_key in {"pets_multicity", "adaptive_sports_completed"} else None
        offer_status = scenario["offer_status"]
        self._add(
            "operational_travel_workspaces",
            OperationalTravelWorkspace,
            self._key(scenario, "operational_workspace"),
            {
                "agency_id": self.agency_id,
                "workspace_reference": f"DEMO-OPS-{token}",
                "workspace_title": scenario["label"],
                "workspace_type": "disruption" if scenario["queue"] == "disruption" else "general",
                "workspace_status": "archived" if status == "archived" else ("completed" if status == "completed" else "active"),
                "primary_client_id": client_id,
                "primary_passenger_id": passenger_ids[0],
                "linked_request_ids": [request_workspace_id],
                "linked_trip_ids": [trip_id],
                "linked_offer_ids": [offer_v2_id],
                "linked_booking_ids": [booking_id] if booking_id else [],
                "linked_ticket_ids": [ticket_id] if ticket_id else [],
                "linked_document_ids": [document_id],
                "priority": "high" if scenario["queue"] in {"disruption", "waiting_airline", "workflow_blocker"} else "medium",
                "assigned_team": [self.profile["team_code"]],
                "assigned_agent": self.actor_user_id,
                "travel_start_date": departure,
                "travel_end_date": return_date,
                "origin_summary": scenario["route"][0][0],
                "destination_summary": scenario["route"][-1][1],
                "service_summary": ", ".join(scenario["services"]) or "Standard air travel",
                "operational_notes": "Synthetic linked pilot scenario; all supplier actions remain manual placeholders.",
            },
            scenario=scenario_key,
        )
        self._add(
            "travel_request_workspaces",
            TravelRequestWorkspace,
            self._key(scenario, "request_workspace"),
            {
                "agency_id": self.agency_id,
                "operational_workspace_id": operational_id,
                "request_reference": f"DEMO-REQ-{token}",
                "request_title": scenario["label"],
                "request_type": "corporate" if index in {1, 9} else "leisure",
                "request_status": scenario["request_status"] if scenario["request_status"] in {"draft", "new", "triage", "open", "researching", "waiting", "quoted", "completed", "archived"} else "open",
                "request_priority": "urgent" if scenario["queue"] == "disruption" else "medium",
                "client_id": client_id,
                "primary_passenger_id": passenger_ids[0],
                "requester_name": f"{self._person(index, 0)[0]} {self._person(index, 0)[1]} (Demo)",
                "requester_email": f"pilot-demo-{token.lower()}@example.com",
                "requested_service_categories": ["flights", *scenario["services"]],
                "requested_origin": scenario["route"][0][0],
                "requested_destination": scenario["route"][-1][1],
                "requested_departure_date": departure,
                "requested_return_date": return_date,
                "passenger_count": len(passenger_ids),
                "passenger_type_summary": f"{len(passenger_ids)} synthetic traveller(s)",
                "flexibility_notes": "Dates may vary by one day.",
                "special_service_notes": ", ".join(scenario["services"]) or "No special service requested.",
                "budget_notes": f"Illustrative target {currency} {round(total * 1.15, 2):,.2f}",
                "deadline": self.anchor_date if scenario["queue"] in {"waiting_customer", "waiting_documents"} else self.anchor_date + timedelta(days=2),
                "assigned_agent": self.actor_user_id,
                "internal_notes": "Synthetic intake; do not communicate externally.",
                "linked_trip_ids": [trip_id],
                "linked_offer_ids": [offer_v2_id],
                "linked_document_ids": [document_id],
            },
            scenario=scenario_key,
        )
        self._add(
            "travel_requests",
            TravelRequest,
            self._key(scenario, "request"),
            {
                "agency_id": self.agency_id,
                "workspace_id": operational_id,
                "client_id": client_id,
                "created_by_user_id": self.actor_user_id,
                "trip_id": trip_id,
                "request_reference": f"DEMO-REQ-{token}",
                "title": scenario["label"],
                "status": {
                    "quoted": "offer_created",
                    "waiting": "waiting_for_client",
                    "open": "in_progress",
                    "researching": "in_progress",
                    "completed": "closed",
                }.get(scenario["request_status"], scenario["request_status"]),
                "priority": "urgent" if scenario["queue"] == "disruption" else "normal",
                "source": "internal",
                "requested_departure_date": departure,
                "requested_return_date": return_date,
                "trip_type": "multi_city" if len(scenario["route"]) > 2 else "round_trip",
                "route_summary": f"{scenario['route'][0][0]} to {scenario['route'][-1][1]}",
                "service_summary": ", ".join(scenario["services"]) or "Standard air travel",
                "passenger_count": len(passenger_ids),
                "service_count": len(scenario["services"]),
                "special_service_count": len(scenario["services"]),
                "origin_summary": scenario["route"][0][0],
                "destination_summary": scenario["route"][-1][1],
                "first_departure_date": departure,
                "last_arrival_date": return_date,
                "requires_medical_review": "MEDA" in scenario["services"],
                "requires_airline_policy_review": bool(scenario["services"]),
                "requires_document_followup": scenario_key in {"umnr_missing_documents", "corporate_medical_waiting_airline", "pets_multicity"},
                "has_existing_passenger_links": True,
                "urgency_reason": "Operational exception" if scenario["queue"] in {"disruption", "workflow_blocker"} else None,
                "client_notes": "Synthetic client request.",
                "internal_notes": "Canonical request linked to the synthetic workspace representation.",
                "assigned_user_id": self.actor_user_id,
                "source_entry_path": "/agency/onboarding",
                "submission_channel": "staff_console",
                "canonical_alignment_notes": {"summary": "Linked to canonical client, passengers, trip, and workspace records."},
                "intake_payload_snapshot": {"synthetic": True, "profile": self.demo_profile},
            },
            scenario=scenario_key,
        )
        self._add(
            "trip_workspaces",
            TripWorkspace,
            self._key(scenario, "trip"),
            {
                "agency_id": self.agency_id,
                "operational_workspace_id": operational_id,
                "trip_reference": f"DEMO-TRIP-{token}",
                "trip_status": status,
                "journey_type": "multi_city" if len(scenario["route"]) > 2 else "round_trip",
                "service_type": "corporate_air_travel" if index in {1, 9} else "leisure_air_travel",
                "client_id": client_id,
                "passenger_ids": passenger_ids,
                "flight_workspace_ids": segment_ids,
                "travel_request_ids": [request_workspace_id],
                "offer_ids": [offer_v2_id],
                "booking_ids": [booking_id] if booking_id else [],
                "ticket_ids": [ticket_id] if ticket_id else [],
                "emd_ids": [emd_id] if emd_id else [],
                "document_ids": [document_id],
                "departure_country": "XX",
                "destination_country": "XX",
                "departure_city": scenario["route"][0][0],
                "destination_city": scenario["route"][-1][1],
                "origin_airport": scenario["route"][0][0],
                "destination_airport": scenario["route"][-1][1],
                "departure_date": departure,
                "return_date": return_date,
                "travel_duration": f"{(return_date - departure).days} days",
                "passenger_count": len(passenger_ids),
                "itinerary_summary": " / ".join(f"{a}-{b} {f}" for a, b, f in scenario["route"]),
                "baggage_summary": "Illustrative fare-family baggage; operating-carrier check required.",
                "service_summary": ", ".join(scenario["services"]) or "Standard service",
                "operational_priority": "critical" if scenario["queue"] == "disruption" else "normal",
                "assigned_agent": self.actor_user_id,
                "assigned_team": [self.profile["team_code"]],
                "operational_notes": "Synthetic canonical trip shell; no itinerary generation or booking execution.",
            },
            scenario=scenario_key,
        )
        self._add(
            "offer_workspaces",
            OfferWorkspace,
            self._key(scenario, "offer"),
            {
                "agency_id": self.agency_id,
                "request_id": request_id,
                "trip_id": trip_id,
                "offer_purpose": "new_booking",
                "title": f"{scenario['label']} comparison",
                "status": "accepted" if scenario["accepted"] else ("rejected" if offer_status == "declined" else "shared"),
                "currency": currency,
                "client_summary_json": {"client_id": client_id, "passenger_ids": passenger_ids},
                "internal_notes": "Two synthetic options for operational comparison.",
                "created_by_user_id": self.actor_user_id,
                "updated_by_user_id": self.actor_user_id,
            },
            scenario=scenario_key,
        )
        option_ids = []
        for option_index in range(2):
            option_ids.append(self._add(
                "offer_options",
                OfferOption,
                self._key(scenario, "offer_option", option_index),
                {
                    "agency_id": self.agency_id,
                    "workspace_id": offer_workspace_id,
                    "request_id": request_id,
                    "trip_id": trip_id,
                    "offer_purpose": "new_booking",
                    "label": "Recommended flexible option" if option_index == 0 else "Lower-cost alternative",
                    "option_type": "flight",
                    "status": "recommended" if option_index == 0 else "alternate",
                    "recommendation_rank": option_index + 1,
                    "recommendation_tag": "operational_fit" if option_index == 0 else "lower_price",
                    "main_airline_code": scenario["route"][0][2][:2],
                    "provider_name": "manual",
                    "source_payload_json": {"synthetic": True, "segments": segment_ids},
                    "rules_summary_json": {"policy": "Illustrative airline policy evidence; verify before action", "approval_required": bool(scenario["services"])},
                    "service_feasibility_json": {"status": "conditional" if scenario["services"] else "feasible", "service_codes": scenario["services"]},
                    "pricing_summary_json": {"currency": currency, "base_fare": round(base_fare * (1 if option_index == 0 else 0.9), 2), "taxes": taxes, "total": round(total * (1 if option_index == 0 else 0.92), 2), "live_price": False},
                    "warnings_json": [{"code": "SYNTHETIC_PRICE", "message": "Illustrative comparison only."}],
                    "internal_notes": "No live availability or fare calculation.",
                },
                scenario=scenario_key,
            ))
        validity_date = self.anchor_date if scenario_key == "offer_expiry_waiting_customer" else self.anchor_date + timedelta(days=5)
        self._add(
            "offer_workspaces_v2",
            OfferWorkspaceV2,
            self._key(scenario, "offer_v2"),
            {
                "agency_id": self.agency_id,
                "operational_workspace_id": operational_id,
                "trip_workspace_id": trip_id,
                "offer_reference": f"DEMO-OFFER-{token}",
                "offer_status": offer_status,
                "offer_type": "flight",
                "client_id": client_id,
                "passenger_ids": passenger_ids,
                "flight_workspace_ids": segment_ids,
                "offer_title": scenario["label"],
                "offer_summary": "Synthetic operational option with canonical comparison and policy snapshots.",
                "destination_summary": scenario["route"][-1][1],
                "itinerary_summary": " / ".join(f"{a}-{b}" for a, b, _ in scenario["route"]),
                "pricing_summary": f"Illustrative {currency} {total:,.2f}; no live pricing",
                "currency": currency,
                "total_price": total,
                "taxes_summary": f"{currency} {taxes:,.2f} illustrative taxes",
                "fees_summary": f"{currency} 45.00 illustrative agency fee",
                "ancillary_summary": ", ".join(scenario["services"]) or "No ancillary requested",
                "baggage_summary": "One checked piece proposed; verify fare and carrier.",
                "seat_summary": "Adjacent seating requested" if len(passenger_ids) > 1 else "Aisle preference",
                "meal_summary": "VGML requested" if "VGML" in scenario["services"] else None,
                "validity_date": validity_date,
                "assigned_agent": self.actor_user_id,
                "agent_notes": "Use the linked comparison options to evaluate the offer workflow.",
                "customer_notes": "Synthetic proposal; not valid for travel.",
                "internal_notes": "Internal policy, pricing, and uncertainty details remain separate from customer notes.",
                "linked_booking_ids": [booking_id] if booking_id else [],
                "linked_ticket_ids": [ticket_id] if ticket_id else [],
                "linked_document_ids": [document_id],
            },
            scenario=scenario_key,
        )

        acceptance_id = None
        readiness_id = None
        handoff_id = None
        if scenario["accepted"]:
            accepted_pricing = {
                "currency": currency,
                "base_fare": base_fare,
                "taxes": taxes,
                "total": total,
                "immutable": True,
            }
            accepted_routing = {
                "segment_ids": segment_ids,
                "route": scenario["route"],
            }
            accepted_fare_bundle = {
                "brand": "Flex",
                "baggage": "1 checked piece illustrative",
            }
            accepted_services = {
                "service_codes": scenario["services"],
                "manual_confirmation": bool(scenario["services"]),
            }
            accepted_rules = {
                "result": "conditional" if scenario["services"] else "feasible",
                "evidence_required": True,
            }
            accepted_client_summary = {
                "title": scenario["label"],
                "total": total,
                "currency": currency,
            }
            accepted_payload = {
                "agency_id": self.agency_id,
                "request_id": request_id,
                "trip_id": trip_id,
                "offer_id": offer_workspace_id,
                "offer_version": 1,
                "option_id": option_ids[0],
                "option_version": 1,
                "passengers": [{"passenger_id": item} for item in passenger_ids],
                "itinerary_segments": [
                    {"flight_workspace_id": item} for item in segment_ids
                ],
                "fare": accepted_fare_bundle,
                "pricing": accepted_pricing,
                "services": accepted_services,
                "rules_feasibility": accepted_rules,
                "client_visible_summary": accepted_client_summary,
                "created_by": self.actor_user_id,
                "synthetic": True,
            }
            accepted_payload_hash = canonical_json_hash(accepted_payload)
            snapshot_id = self.stable_id(
                self._key(scenario, "accepted_snapshot")
            )
            acceptance_id = self._add(
                "offer_acceptances",
                OfferAcceptance,
                self._key(scenario, "acceptance"),
                {
                    "agency_id": self.agency_id,
                    "workspace_id": offer_workspace_id,
                    "option_id": option_ids[0],
                    "offer_version": 1,
                    "option_version": 1,
                    "idempotency_key": (
                        f"demo:{self.agency_id}:{scenario_key}:offer-acceptance"
                    ),
                    "request_id": request_id,
                    "trip_id": trip_id,
                    "accepted_by_user_id": self.actor_user_id,
                    "accepted_at": self.anchor - timedelta(days=1),
                    "channel": "synthetic_demo",
                    "acceptance_terms_version": "synthetic-demo-v1",
                    "acceptance_source": "internal",
                    "status": "accepted",
                    "accepted_pricing_snapshot_json": accepted_pricing,
                    "accepted_routing_snapshot_json": accepted_routing,
                    "accepted_fare_bundle_snapshot_json": accepted_fare_bundle,
                    "accepted_services_snapshot_json": accepted_services,
                    "rules_feasibility_snapshot_json": accepted_rules,
                    "client_visible_summary_json": accepted_client_summary,
                    "accepted_payload_hash": accepted_payload_hash,
                    "accepted_snapshot_id": snapshot_id,
                    "reconciliation_status": "canonical",
                    "internal_notes": "Frozen synthetic acceptance snapshot; mutable offer data is not reconstructed.",
                },
                scenario=scenario_key,
            )
            snapshot_id = self._add(
                "trip_accepted_offer_snapshots",
                TripAcceptedOfferSnapshot,
                self._key(scenario, "accepted_snapshot"),
                {
                    "agency_id": self.agency_id,
                    "trip_id": trip_id,
                    "request_id": request_id,
                    "workspace_id": offer_workspace_id,
                    "option_id": option_ids[0],
                    "acceptance_id": acceptance_id,
                    "offer_version": 1,
                    "option_version": 1,
                    "confirmed_segments_json": [{"flight_workspace_id": item} for item in segment_ids],
                    "confirmed_passengers_json": [{"passenger_id": item} for item in passenger_ids],
                    "confirmed_fare_bundle_json": accepted_fare_bundle,
                    "confirmed_pricing_json": accepted_pricing,
                    "confirmed_services_json": accepted_services,
                    "booking_readiness_json": {"status": "blocked" if scenario["booking_status"] == "blocked" else "ready"},
                    "total_snapshot_json": {
                        "total_amount": total,
                        "currency": currency,
                        "server_derived": True,
                    },
                    "currency": currency,
                    "terms_snapshot_json": {
                        "acceptance_terms_version": "synthetic-demo-v1",
                        "synthetic": True,
                    },
                    "policy_readiness_snapshot_json": {
                        "rules_feasibility": accepted_rules,
                    },
                    "source_hash": accepted_payload_hash,
                    "created_by_user_id": self.actor_user_id,
                    "immutable": True,
                },
                scenario=scenario_key,
            )
            readiness_id = self._add(
                "booking_readiness_packages",
                BookingReadinessPackage,
                self._key(scenario, "booking_readiness"),
                {
                    "agency_id": self.agency_id,
                    "trip_id": trip_id,
                    "request_id": request_id,
                    "workspace_id": offer_workspace_id,
                    "option_id": option_ids[0],
                    "acceptance_id": acceptance_id,
                    "status": "blocked" if scenario["booking_status"] == "blocked" else "ready",
                    "provider_target": "manual",
                    "passengers_snapshot_json": [{"passenger_id": item} for item in passenger_ids],
                    "segments_snapshot_json": [{"flight_workspace_id": item} for item in segment_ids],
                    "pricing_snapshot_json": {"currency": currency, "total": total, "resolved": True},
                    "services_snapshot_json": {"service_codes": scenario["services"]},
                    "ssr_json": [{"code": code, "transmitted": False} for code in scenario["services"]],
                    "warnings_json": [{"code": "MANUAL_PROVIDER_PATH", "message": "No provider execution is configured."}],
                    "required_documents_json": [{"document_workspace_id": document_id, "status": "missing" if scenario_key == "umnr_missing_documents" else "reviewed"}],
                    "policy_violations_json": [],
                    "readiness_checks_json": {"accepted_snapshot": True, "passenger_mapping": True, "segment_mapping": True, "manual_review": scenario["booking_status"] == "blocked"},
                    "created_by_user_id": self.actor_user_id,
                },
                scenario=scenario_key,
            )
            handoff_id = self._add(
                "offer_booking_handoffs",
                OfferBookingHandoff,
                self._key(scenario, "booking_handoff"),
                {
                    "agency_id": self.agency_id,
                    "handoff_reference": f"DEMO-HANDOFF-{token}",
                    "acceptance_id": acceptance_id,
                    "booking_readiness_package_id": readiness_id,
                    "trip_accepted_offer_snapshot_id": snapshot_id,
                    "trip_id": trip_id,
                    "request_id": request_id,
                    "offer_workspace_id": offer_workspace_id,
                    "offer_option_id": option_ids[0],
                    "booking_workspace_id": booking_id,
                    "handoff_status": "blocked" if scenario["booking_status"] == "blocked" else ("ready" if not booking_id else "booking_created"),
                    "readiness_status": "blocked" if scenario["booking_status"] == "blocked" else "ready",
                    "provider_target": "manual",
                    "booking_mode": "manual",
                    "idempotency_key": f"demo-handoff:{self.agency_id}:{scenario_key}",
                    "blocker_count": 1 if scenario["booking_status"] == "blocked" else 0,
                    "warning_count": 1,
                    "check_count": 5,
                    "mapping_count": len(passenger_ids) + len(segment_ids),
                    "instruction_count": 1,
                    "accepted_offer_snapshot_json": {"snapshot_id": snapshot_id, "immutable": True},
                    "readiness_snapshot_json": {"package_id": readiness_id, "status": "blocked" if scenario["booking_status"] == "blocked" else "ready"},
                    "policy_trace_json": {"manual_evidence_review": bool(scenario["services"])},
                    "pricing_trace_json": {"currency": currency, "total": total},
                    "internal_trace_json": {"synthetic": True, "supplier_action": "disabled"},
                    "client_trace_json": {"status": "accepted"},
                    "booking_execution_snapshot_json": {"execution_performed": False},
                    "created_by": self.actor_user_id,
                    "updated_by": self.actor_user_id,
                },
                scenario=scenario_key,
            )

        booking_timeline_ids: list[str] = []
        if booking_id:
            booking_timeline_id = self._add(
                "booking_timeline_events",
                BookingTimelineEvent,
                self._key(scenario, "booking_timeline"),
                {
                    "agency_id": self.agency_id,
                    "booking_workspace_id": booking_id,
                    "trip_id": trip_id,
                    "event_type": "booking_workspace_created",
                    "actor_user_id": self.actor_user_id,
                    "title": "Synthetic booking workspace created",
                    "description": "Created from the frozen accepted offer snapshot without provider execution.",
                    "summary": scenario["label"],
                    "visibility": "internal",
                    "payload_json": {"handoff_id": handoff_id, "synthetic": True},
                    "metadata": {"demo_data": True, "synthetic": True},
                },
                scenario=scenario_key,
            )
            booking_timeline_ids.append(booking_timeline_id)
            self._add(
                "booking_workspaces",
                BookingWorkspace,
                self._key(scenario, "booking"),
                {
                    "agency_id": self.agency_id,
                    "operational_workspace_id": operational_id,
                    "trip_workspace_id": trip_id,
                    "source_context": "offer_readiness",
                    "client_id": client_id,
                    "passenger_ids": passenger_ids,
                    "flight_workspace_ids": segment_ids,
                    "trip_id": trip_id,
                    "request_id": request_id,
                    "offer_workspace_id": offer_workspace_id,
                    "offer_option_id": option_ids[0],
                    "offer_acceptance_id": acceptance_id,
                    "booking_readiness_package_id": readiness_id,
                    "workspace_number": f"DEMO-BKG-{token}",
                    "booking_reference": f"D{token[:5]}",
                    "title": scenario["label"],
                    "status": "blocked" if scenario["booking_status"] == "blocked" else ("cancelled" if scenario["booking_status"] == "cancelled" else "booked"),
                    "booking_status": scenario["booking_status"],
                    "booking_type": "manual_training",
                    "booking_source": "synthetic_onboarding",
                    "booking_owner": self.actor_user_id,
                    "airline_pnr": f"D{token[:5]}",
                    "gds_record_locator": f"G{token[:5]}",
                    "supplier_reference": f"SUP-{token}",
                    "booking_created_date": self.anchor_date - timedelta(days=1),
                    "booking_deadline": self.anchor_date if scenario["booking_status"] in {"confirmed", "ticketing_pending"} else self.anchor_date + timedelta(days=2),
                    "provider_target": "manual",
                    "ticket_ids": [ticket_id] if ticket_id else [],
                    "emd_ids": [emd_id] if emd_id else [],
                    "ssr_ids": [],
                    "document_ids": [document_id],
                    "timeline_ids": booking_timeline_ids,
                    "payment_summary": "Synthetic payment lifecycle linked below; no payment execution.",
                    "booking_summary": "Partially ticketed: one passenger remains" if scenario_key == "schedule_change_partial_ticket" else "Synthetic booking mirror",
                    "operational_notes": "No PNR creation, provider call, or ticket issuance was performed.",
                    "source_snapshot_json": {"acceptance_id": acceptance_id, "immutable": True},
                    "passengers_snapshot_json": [{"passenger_id": item} for item in passenger_ids],
                    "segments_snapshot_json": [{"flight_workspace_id": item} for item in segment_ids],
                    "pricing_snapshot_json": {"currency": currency, "total": total},
                    "services_snapshot_json": {"service_codes": scenario["services"]},
                    "required_documents_json": [{"document_workspace_id": document_id}],
                    "warnings_json": [{"code": "SYNTHETIC_BOOKING", "message": "Operational mirror only."}],
                    "created_by_user_id": self.actor_user_id,
                },
                scenario=scenario_key,
            )

        if ticket_id:
            ticket_state = scenario["ticket_state"]
            document_status = "refunded" if ticket_state == "refunded" else "issued"
            self._add(
                "ticket_workspaces",
                TicketWorkspace,
                self._key(scenario, "ticket"),
                {
                    "agency_id": self.agency_id,
                    "operational_workspace_id": operational_id,
                    "trip_workspace_id": trip_id,
                    "offer_workspace_id": offer_v2_id,
                    "booking_workspace_id": booking_id,
                    "ticket_reference": f"DEMO-TKT-{token}",
                    "ticket_status": "archived" if status == "archived" else "ready",
                    "ticket_document_status": document_status,
                    "ticket_type": "electronic_mirror",
                    "ticket_number": f"125-0000{index + 1:06d}",
                    "validating_carrier": scenario["route"][0][2][:2],
                    "issuing_agent": "Synthetic mirror",
                    "issuing_office": "DEMO",
                    "issue_date": self.anchor_date - timedelta(days=5),
                    "passenger_id": passenger_ids[0],
                    "passenger_name": f"{self._person(index, 0)[0]} {self._person(index, 0)[1]} (Demo)",
                    "flight_workspace_ids": segment_ids,
                    "booking_reference": f"D{token[:5]}",
                    "airline_pnr": f"D{token[:5]}",
                    "gds_record_locator": f"G{token[:5]}",
                    "fare_basis_summary": "Coupon-level fare bases below",
                    "fare_amount": base_fare,
                    "taxes_amount": taxes,
                    "total_amount": total,
                    "currency": currency,
                    "fare_calculation_line": "SYNTHETIC FARE CONSTRUCTION - NOT VALID FOR TICKETING",
                    "tax_breakdown": [{"code": "XT", "amount": taxes, "currency": currency}],
                    "coupon_status_summary": f"{len(segment_ids)} synthetic coupon(s): {ticket_state}",
                    "coupon_details": [
                        {
                            "coupon_number": str(segment_index + 1),
                            "flight_workspace_id": flight_id,
                            "segment_reference": f"SEG-{segment_index + 1}",
                            "origin": scenario["route"][segment_index][0],
                            "destination": scenario["route"][segment_index][1],
                            "marketing_carrier": scenario["route"][segment_index][2][:2],
                            "operating_carrier": scenario["route"][segment_index][2][:2],
                            "fare_basis": "YDEMO",
                            "fare_component_reference": f"FC-{segment_index + 1}",
                            "pricing_unit_reference": "PU-1",
                            "coupon_status": ticket_state,
                            "baggage_summary": "Illustrative allowance",
                            "remarks": "Synthetic coupon metadata only",
                        }
                        for segment_index, flight_id in enumerate(segment_ids)
                    ],
                    "linked_emd_ids": [emd_id] if emd_id else [],
                    "linked_document_ids": [document_id],
                    "refund_reference_ids": [f"DEMO-REFUND-{token}"] if ticket_state == "refunded" else [],
                    "lifecycle_notes": "Synthetic ticket mirror. No issuance, exchange, refund, or coupon validation occurred.",
                    "operational_notes": "Use for workspace evaluation only.",
                },
                scenario=scenario_key,
            )
        if emd_id:
            service_code = "PETC" if scenario_key == "pets_multicity" else "SPORTS_BAGGAGE"
            self._add(
                "emd_workspaces",
                EmdWorkspace,
                self._key(scenario, "emd"),
                {
                    "agency_id": self.agency_id,
                    "operational_workspace_id": operational_id,
                    "trip_workspace_id": trip_id,
                    "offer_workspace_id": offer_v2_id,
                    "booking_workspace_id": booking_id,
                    "ticket_workspace_id": ticket_id,
                    "emd_reference": f"DEMO-EMD-{token}",
                    "emd_status": "ready",
                    "emd_document_status": "issued",
                    "emd_type": "associated",
                    "emd_number": f"125-0001{index + 1:06d}",
                    "emd_a_or_s": "EMD-A",
                    "validating_carrier": scenario["route"][0][2][:2],
                    "issue_date": self.anchor_date - timedelta(days=3),
                    "passenger_id": passenger_ids[0],
                    "passenger_name": f"{self._person(index, 0)[0]} {self._person(index, 0)[1]} (Demo)",
                    "booking_reference": f"D{token[:5]}" if booking_id else None,
                    "associated_ticket_number": f"125-0000{index + 1:06d}" if ticket_id else None,
                    "associated_flight_workspace_ids": segment_ids,
                    "rfic": "C",
                    "rfisc": "0B5",
                    "service_reason": service_code,
                    "service_description": "Synthetic ancillary service mirror",
                    "service_category": "ancillary",
                    "service_status": "confirmed_metadata",
                    "service_quantity": 1,
                    "emd_coupon_status_summary": "Open for use metadata",
                    "emd_coupon_details": [{"coupon_number": "1", "coupon_status": "open_for_use", "flight_workspace_id": segment_ids[0], "origin": scenario["route"][0][0], "destination": scenario["route"][0][1], "rfic": "C", "rfisc": "0B5", "service_description": service_code, "amount": 120.0, "currency": currency}],
                    "fare_amount": 120.0,
                    "total_amount": 120.0,
                    "currency": currency,
                    "linked_document_ids": [document_id],
                    "lifecycle_notes": "Synthetic EMD mirror; no issuance or servicing action.",
                },
                scenario=scenario_key,
            )

        service_ids: list[str] = []
        for service_index, service_code in enumerate(scenario["services"]):
            definition = self._service_definition(service_code)
            service_id = self.stable_id(self._key(scenario, "service", service_index))
            pending = service_code in {"WCHC", "MEDA", "UMNR", "PETC", "AVIH", "WHEELCHAIR_EQUIPMENT"}
            doc_required = service_code in {"MEDA", "UMNR", "PETC", "AVIH", "WHEELCHAIR_EQUIPMENT"}
            self._add(
                "ssr_osi_workspaces",
                SsrOsiWorkspace,
                self._key(scenario, "service", service_index),
                {
                    "agency_id": self.agency_id,
                    "operational_workspace_id": operational_id,
                    "passenger_workspace_id": passenger_workspace_ids[0],
                    "travel_request_workspace_id": request_workspace_id,
                    "trip_workspace_id": trip_id,
                    "booking_workspace_id": booking_id,
                    "ticket_workspace_id": ticket_id,
                    "emd_workspace_id": emd_id,
                    "workspace_reference": f"DEMO-SSR-{token}-{service_index + 1}",
                    "operational_status": "review" if pending else "ready",
                    "operational_priority": "high" if pending else "normal",
                    "need_category": definition["need_category"],
                    "need_subcategory": definition["service_type"],
                    "need_description": definition["label"],
                    "passenger_statement": "Synthetic passenger service requirement.",
                    "service_family": definition["category"],
                    "service_type": definition["service_type"],
                    "ssr_code": service_code if service_code not in {"SPORTS_BAGGAGE", "WHEELCHAIR_EQUIPMENT"} else ("SPEQ" if service_code == "SPORTS_BAGGAGE" else "WCBD"),
                    "ssr_description": definition["label"],
                    "ssr_status": "pending" if pending else "confirmed_metadata",
                    "ssr_confirmation_status": "not_transmitted",
                    "osi_required": service_code in {"MEDA", "PETC", "AVIH", "WHEELCHAIR_EQUIPMENT"},
                    "osi_text": f"SYNTHETIC {service_code} DETAILS FOR MANUAL REVIEW",
                    "osi_status": "draft",
                    "airline_code": scenario["route"][0][2][:2],
                    "approval_required": pending,
                    "approval_status": "pending" if pending else "not_required",
                    "approval_reference": f"DEMO-APR-{token}-{service_index + 1}" if pending else None,
                    "approval_deadline": self.anchor_date + timedelta(days=1),
                    "departure_station": scenario["route"][0][0],
                    "arrival_station": scenario["route"][-1][1],
                    "station_status": "manual_review" if pending else "not_required",
                    "emd_required": service_code in {"PETC", "AVIH", "EXST", "SPORTS_BAGGAGE"},
                    "emd_workspace_ids": [emd_id] if emd_id else [],
                    "document_requirements": ["supporting_document_missing"] if doc_required else [],
                    "medif_required": service_code == "MEDA",
                    "medical_certificate_required": service_code == "MEDA",
                    "veterinary_documents_required": service_code in {"PETC", "AVIH"},
                    "readiness_status": "awaiting_documents" if doc_required else ("awaiting_airline" if pending else "ready"),
                    "missing_requirements": ["Supporting document"] if doc_required else [],
                    "unresolved_items": ["Airline confirmation"] if pending else [],
                    "flight_workspace_ids": segment_ids,
                    "linked_document_ids": [document_id],
                    "agent_notes": "Use the canonical policy and service reference snapshots; verify against current airline evidence.",
                    "passenger_notes": "We are reviewing this request.",
                    "airline_notes": "Supplier communication placeholder only; nothing was sent.",
                    "internal_notes": "Internal operational instructions remain separate from passenger-facing notes.",
                    "created_by": self.actor_user_id,
                },
                scenario=scenario_key,
            )
            self._add(
                "passenger_service_requests",
                PassengerServiceRequest,
                self._key(scenario, "passenger_service_request", service_index),
                {
                    "agency_id": self.agency_id,
                    "request_id": request_id,
                    "trip_id": trip_id,
                    "booking_workspace_id": booking_id,
                    "ssr_osi_workspace_id": service_id,
                    "ticket_record_ids": [ticket_id] if ticket_id else [],
                    "emd_record_ids": [emd_id] if emd_id else [],
                    "document_workspace_ids": [document_id],
                    "passenger_id": passenger_ids[0],
                    "segment_id": segment_ids[0],
                    "service_key": definition["service_type"],
                    "service_label": definition["label"],
                    "service_catalogue_category": definition["category"],
                    "service_catalogue_snapshot_json": {"code": service_code, "label": definition["label"], "canonical_reference": True},
                    "category": definition["category"],
                    "service_type": definition["service_type"],
                    "ssr_code": service_code if len(service_code) <= 4 else None,
                    "metadata_json": {"synthetic": True, "reference_service_example": True},
                    "gds_text": None,
                    "required_documents_json": [{"document_workspace_id": document_id, "required": doc_required}],
                    "warnings_json": [{"code": "MANUAL_CONFIRMATION", "message": "No airline request has been sent."}] if pending else [],
                    "policy_violations_json": [{"code": "EVIDENCE_REVIEW", "message": "Illustrative policy must be checked against published evidence."}] if pending else [],
                    "generated_ssr_json": [{"code": service_code, "transmitted": False}],
                    "generated_osi_json": [],
                    "evaluation_result_json": {"status": "conditional" if pending else "ready", "advisory_only": True},
                    "airline_confirmation_status": "pending" if pending else "not_required",
                    "external_manual_status": "not_started",
                    "fulfilment_result": "pending" if pending else "fulfilled",
                    "next_action": "Review supporting evidence and contact the airline manually" if pending else "No action required",
                    "due_at": self.anchor + timedelta(hours=4),
                    "departure_deadline": datetime.combine(departure - timedelta(days=2), time(12, 0), tzinfo=timezone.utc),
                    "status": "requested" if pending else "confirmed",
                },
                scenario=scenario_key,
            )
            service_ids.append(service_id)

        document_type = "unaccompanied_minor_form" if scenario_key == "umnr_missing_documents" else ("medif" if "MEDA" in scenario["services"] else ("veterinary_certificate" if "PETC" in scenario["services"] else ("voucher" if scenario_key == "cancelled_flight_refund" else "itinerary")))
        missing_document = scenario_key in {"umnr_missing_documents", "corporate_medical_waiting_airline"}
        package_id = self.stable_id(self._key(scenario, "document_package"))
        rendered_document_id = self.stable_id(self._key(scenario, "rendered_document")) if index in {0, 2} else None
        self._add(
            "document_workspaces",
            DocumentWorkspace,
            self._key(scenario, "document"),
            {
                "agency_id": self.agency_id,
                "operational_workspace_id": operational_id,
                "passenger_workspace_id": passenger_workspace_ids[0],
                "travel_request_workspace_id": request_workspace_id,
                "trip_workspace_id": trip_id,
                "booking_workspace_id": booking_id,
                "ticket_workspace_id": ticket_id,
                "emd_workspace_id": emd_id,
                "ssr_osi_workspace_id": service_ids[0] if service_ids else None,
                "document_reference": f"DEMO-DOC-{token}",
                "document_status": "required" if missing_document else "verified",
                "document_type": document_type,
                "document_category": "travel_requirement" if missing_document else "travel_document",
                "document_title": f"{scenario['label']} document",
                "document_description": "Synthetic document metadata without a real passenger file.",
                "passenger_id": passenger_ids[0],
                "passenger_name": f"{self._person(index, 0)[0]} {self._person(index, 0)[1]} (Demo)",
                "booking_reference": f"D{token[:5]}" if booking_id else None,
                "related_service_requirement": scenario["services"][0] if scenario["services"] else None,
                "related_ssr_code": scenario["services"][0] if scenario["services"] and len(scenario["services"][0]) <= 4 else None,
                "related_emd_number": f"125-0001{index + 1:06d}" if emd_id else None,
                "related_ticket_number": f"125-0000{index + 1:06d}" if ticket_id else None,
                "required_for_travel": missing_document or bool(scenario["services"]),
                "required_by_airline": bool(scenario["services"]),
                "required_by_airport": False,
                "required_by_authority": document_type in {"unaccompanied_minor_form", "veterinary_certificate"},
                "requirement_deadline": self.anchor_date,
                "received_status": "missing" if missing_document else "received_metadata",
                "verification_status": "not_received" if missing_document else "verified_metadata",
                "language": "en",
                "storage_reference": None,
                "document_package_ids": [package_id],
                "rendered_document_ids": [rendered_document_id] if rendered_document_id else [],
                "customer_visible": not missing_document,
                "airline_visible": False,
                "internal_only": missing_document,
                "missing_reason": "Required synthetic supporting document intentionally absent." if missing_document else None,
                "operational_notes": "No PDF, file upload, storage write, signature, or delivery occurred.",
                "created_by": self.actor_user_id,
            },
            scenario=scenario_key,
        )
        if rendered_document_id:
            self._add(
                "rendered_documents",
                RenderedDocument,
                self._key(scenario, "rendered_document"),
                {
                    "agency_id": self.agency_id,
                    "document_type": "itinerary_summary",
                    "source_entity_type": "booking" if booking_id else "offer",
                    "source_entity_id": booking_id or offer_workspace_id,
                    "client_id": client_id,
                    "passenger_id": passenger_ids[0],
                    "title": f"{scenario['label']} document preview",
                    "status": "draft",
                    "language": "en",
                    "brand_snapshot": {"agency_id": self.agency_id, "synthetic": True},
                    "source_snapshot": {"document_workspace_id": document_id, "package_id": package_id},
                    "rendered_html": "<p>Synthetic pilot document preview. Not valid for travel.</p>",
                    "client_visible": False,
                    "internal_notes": "Static synthetic preview; no PDF generation or delivery.",
                    "rendered_by_user_id": self.actor_user_id,
                },
                scenario=scenario_key,
            )
        self._add(
            "document_packages",
            DocumentPackage,
            self._key(scenario, "document_package"),
            {
                "agency_id": self.agency_id,
                "package_type": "booking_package" if booking_id else "trip_package",
                "title": f"{scenario['label']} package (Demo)",
                "source_context_type": "booking_workspace" if booking_id else "trip",
                "source_context_id": booking_id or trip_id,
                "source_context_ids_json": {"document_workspace_ids": [document_id], "trip_workspace_id": trip_id, "booking_workspace_id": booking_id},
                "document_render_job_ids": [],
                "status": "ready" if not missing_document else "draft",
                "created_by_user_id": self.actor_user_id,
            },
            scenario=scenario_key,
        )
        if index in {0, 2}:
            self._add(
                "document_deliveries",
                DocumentDelivery,
                self._key(scenario, "document_delivery"),
                {
                    "agency_id": self.agency_id,
                    "rendered_document_id": rendered_document_id,
                    "delivery_type": "email",
                    "status": "draft",
                    "recipient_email": f"pilot-demo-{token.lower()}@example.com",
                    "recipient_name": "Synthetic passenger",
                    "subject": f"Demo travel documents {token}",
                    "message_text": "Synthetic delivery placeholder. No message has been sent.",
                    "provider": "none",
                    "processing_state": "manual_only",
                    "client_visible": False,
                },
                scenario=scenario_key,
            )

        invoice_id = None
        payment_id = None
        if booking_id:
            invoice_id = self._add(
                "invoices",
                Invoice,
                self._key(scenario, "invoice"),
                {
                    "agency_id": self.agency_id,
                    "invoice_number": f"DEMO-INV-{token}",
                    "client_id": client_id,
                    "booking_workspace_id": booking_id,
                    "offer_id": offer_workspace_id,
                    "status": "overdue" if scenario_key == "corporate_medical_waiting_airline" else ("paid" if status in {"completed", "archived"} else "issued"),
                    "currency": currency,
                    "subtotal_amount": base_fare + 45,
                    "tax_amount": taxes,
                    "total_amount": total,
                    "paid_amount": total if status in {"completed", "archived"} else 0,
                    "due_amount": 0 if status in {"completed", "archived"} else total,
                    "issue_date": self.anchor_date - timedelta(days=2),
                    "due_date": self.anchor_date if scenario_key in {"corporate_medical_waiting_airline", "schedule_change_partial_ticket"} else self.anchor_date + timedelta(days=5),
                    "client_visible_notes": "Synthetic invoice for pilot evaluation only.",
                    "internal_notes": "No payment request or invoice delivery occurred.",
                },
                scenario=scenario_key,
            )
            for line_index, (line_type, description, amount) in enumerate([
                ("airfare", "Illustrative airfare", base_fare),
                ("taxes", "Illustrative taxes", taxes),
                ("agency_service_fee", "Illustrative agency service fee", 45.0),
            ]):
                self._add(
                    "invoice_line_items",
                    InvoiceLineItem,
                    self._key(scenario, "invoice_line", line_index),
                    {
                        "agency_id": self.agency_id,
                        "invoice_id": invoice_id,
                        "booking_id": booking_id,
                        "ticket_id": ticket_id,
                        "emd_id": emd_id,
                        "line_type": line_type,
                        "description": description,
                        "quantity": 1,
                        "unit_amount": amount,
                        "total_amount": amount,
                        "currency": currency,
                        "supplier_pass_through": line_type != "agency_service_fee",
                        "client_visible": True,
                        "status": "active",
                    },
                    scenario=scenario_key,
                )
            payment_status = "refunded" if scenario_key == "cancelled_flight_refund" else ("received" if status in {"completed", "archived"} else "pending")
            payment_id = self._add(
                "payments",
                PaymentRecord,
                self._key(scenario, "payment"),
                {
                    "agency_id": self.agency_id,
                    "invoice_id": invoice_id,
                    "booking_id": booking_id,
                    "client_id": client_id,
                    "status": payment_status,
                    "method": "bank_transfer",
                    "amount": total if payment_status in {"received", "refunded"} else 0,
                    "currency": currency,
                    "received_at": self.anchor - timedelta(days=1) if payment_status in {"received", "refunded"} else None,
                    "external_reference": f"DEMO-PAY-{token}",
                    "reconciliation_status": "reconciled" if payment_status == "received" else "unreconciled",
                    "reconciliation_notes": "Synthetic payment-state example; no transaction exists.",
                    "internal_notes": "No payment execution.",
                },
                scenario=scenario_key,
            )

        workflow_id = self._add(
            "operational_workflow_instances",
            OperationalWorkflowInstance,
            self._key(scenario, "workflow"),
            {
                "agency_id": self.agency_id,
                "workflow_definition_id": "passenger-service-case-v1",
                "entity_type": "trip_workspace",
                "entity_id": trip_id,
                "current_state": "case_closed" if status in {"completed", "archived"} else ("booking_ready" if scenario["booking"] else "offer_preparation"),
                "previous_state": "requirements_collected",
                "workflow_status": "completed" if status in {"completed", "archived"} else "active",
                "context_snapshot_json": {"request_id": request_id, "client_id": client_id, "passenger_ids": passenger_ids},
                "active_blockers_json": [{"code": scenario["queue"], "summary": scenario["label"]}] if scenario["queue"] in {"waiting_airline", "waiting_documents", "disruption", "workflow_blocker"} else [],
                "active_warnings_json": [{"code": "SYNTHETIC_DATA", "summary": "Pilot demonstration data"}],
                "started_at": self.anchor - timedelta(days=3),
                "completed_at": self.anchor - timedelta(days=1) if status in {"completed", "archived"} else None,
                "created_by": self.actor_user_id,
                "updated_by": self.actor_user_id,
            },
            scenario=scenario_key,
        )
        self._add(
            "operational_workflow_events",
            OperationalWorkflowEvent,
            self._key(scenario, "workflow_event"),
            {
                "agency_id": self.agency_id,
                "workflow_instance_id": workflow_id,
                "event_type": "state_recorded",
                "event_code": f"demo_{scenario_key}",
                "event_status": "recorded",
                "source_module": "agency_onboarding",
                "source_entity_type": "trip_workspace",
                "source_entity_id": trip_id,
                "payload_json": {"synthetic": True, "no_automatic_transition": True},
                "occurred_at": self.anchor - timedelta(hours=index + 1),
            },
            scenario=scenario_key,
        )

        if scenario["queue"] != "completed":
            queue_code = scenario["queue"]
            blocker_status = "waiting_payment" if scenario_key == "corporate_medical_waiting_airline" else ("blocked" if queue_code in {"disruption", "workflow_blocker"} else queue_code)
            due_at = self.anchor - timedelta(hours=2) if queue_code in {"disruption", "workflow_blocker"} else self.anchor + timedelta(hours=index + 1)
            work_item_id = self._add(
                "operational_work_items",
                OperationalWorkItem,
                self._key(scenario, "work_item"),
                {
                    "agency_id": self.agency_id,
                    "work_item_code": f"DEMO-WI-{token}",
                    "work_item_type": queue_code,
                    "source_entity_type": "request" if index < 4 else ("booking_workspace" if booking_id else "trip_workspace"),
                    "source_entity_id": request_id if index < 4 else (booking_id or trip_id),
                    "workflow_instance_id": workflow_id,
                    "title": scenario["label"],
                    "summary": f"Review the {scenario['label'].lower()} scenario.",
                    "status": "waiting" if queue_code.startswith("waiting") else "open",
                    "priority": "critical" if queue_code == "disruption" else ("high" if queue_code in {"waiting_airline", "workflow_blocker"} else "normal"),
                    "severity": "critical" if queue_code == "disruption" else ("high" if queue_code in {"waiting_airline", "workflow_blocker"} else "medium"),
                    "queue_code": queue_code,
                    "assigned_user_id": self.actor_user_id if index % 2 == 0 else None,
                    "assigned_team_code": self.profile["team_code"],
                    "due_at": due_at,
                    "sla_status": "overdue" if due_at < self.anchor else "due_soon",
                    "blocker_status": blocker_status,
                    "client_impact": "high" if queue_code == "disruption" else "medium",
                    "internal_context_json": {"client_id": client_id, "passenger_id": passenger_ids[0], "route_summary": f"{scenario['route'][0][0]} to {scenario['route'][-1][1]}", "internal_only": True},
                    "compatibility_mapping_json": {"request_id": request_id, "trip_workspace_id": trip_id, "booking_workspace_id": booking_id},
                    "source_fingerprint": f"demo:{self.agency_id}:{scenario_key}:work",
                    "created_by": self.actor_user_id,
                    "updated_by": self.actor_user_id,
                },
                scenario=scenario_key,
            )
            self._add(
                "operational_deadlines",
                OperationalDeadline,
                self._key(scenario, "deadline"),
                {
                    "agency_id": self.agency_id,
                    "deadline_reference": f"DEMO-DL-{token}",
                    "source_entity_type": "work_item",
                    "source_entity_id": work_item_id,
                    "workflow_instance_id": workflow_id,
                    "work_item_id": work_item_id,
                    "deadline_type": "ticketing_deadline" if queue_code == "ready_ticketing" else ("offer_expiry" if queue_code == "waiting_client" else "task_deadline"),
                    "priority": "critical" if queue_code == "disruption" else "normal",
                    "service_family": scenario["services"][0] if scenario["services"] else None,
                    "started_at": self.anchor - timedelta(days=1),
                    "original_due_at": due_at,
                    "calculated_due_at": due_at,
                    "due_at": due_at,
                    "status": "overdue" if due_at < self.anchor else "due_soon",
                    "breach_state": "breached" if due_at < self.anchor else "due_soon",
                    "explanation": f"Synthetic operational deadline for {scenario['label'].lower()}.",
                    "calculation_snapshot_json": {"anchor_date": self.anchor_date.isoformat(), "deterministic": True, "business_hours_applied": False},
                    "source_snapshot_json": {"scenario": scenario_key, "synthetic": True},
                    "created_by": self.actor_user_id,
                    "updated_by": self.actor_user_id,
                },
                scenario=scenario_key,
            )
            self._add(
                "request_tasks",
                RequestTask,
                self._key(scenario, "request_task"),
                {
                    "agency_id": self.agency_id,
                    "request_id": request_id,
                    "assigned_user_id": self.actor_user_id,
                    "title": f"Follow up: {scenario['label']}",
                    "description": "Synthetic follow-up task generated through onboarding.",
                    "status": "open",
                    "priority": "high" if queue_code in {"disruption", "waiting_airline"} else "normal",
                    "due_at": due_at,
                    "visibility": "internal",
                },
                scenario=scenario_key,
            )

        timeline_ids = []
        for event_index, event in enumerate([
            ("travel_request_received", "internal_note", "Request and linked passenger context reviewed", True, False),
            ("customer_contacted", "customer_message", "Client-facing status placeholder recorded; no message sent", False, True),
            ("airline_contacted", "airline_message", "Supplier communication placeholder recorded; no airline contact made", True, False),
        ]):
            event_type, communication_type, summary, internal_only, passenger_visible = event
            timeline_ids.append(self._add(
                "operational_timelines",
                OperationalTimeline,
                self._key(scenario, "timeline", event_index),
                {
                    "agency_id": self.agency_id,
                    "timeline_reference": f"DEMO-TL-{token}-{event_index + 1}",
                    "created_by": self.actor_user_id,
                    "passenger_workspace_id": passenger_workspace_ids[0],
                    "travel_request_workspace_id": request_workspace_id,
                    "trip_workspace_id": trip_id,
                    "booking_workspace_id": booking_id,
                    "ticket_workspace_id": ticket_id,
                    "emd_workspace_id": emd_id,
                    "ssr_osi_workspace_id": service_ids[0] if service_ids else None,
                    "document_workspace_id": document_id,
                    "event_type": event_type,
                    "event_category": "communication" if event_index else "operations",
                    "event_source": "synthetic_onboarding",
                    "event_status": "recorded",
                    "event_priority": "high" if scenario["queue"] == "disruption" else "normal",
                    "operational_stage": "servicing" if scenario.get("after_sales") else "planning",
                    "related_airline": scenario["route"][0][2][:2],
                    "communication_type": communication_type,
                    "communication_direction": "outbound" if event_index else "internal",
                    "communication_channel": "metadata_placeholder",
                    "sender": "Agency team",
                    "recipient": "Synthetic recipient" if event_index else "Internal team",
                    "subject": scenario["label"],
                    "summary": summary,
                    "due_date": self.anchor_date if event_index == 1 else None,
                    "reminder_required": event_index == 1,
                    "internal_only": internal_only,
                    "passenger_visible": passenger_visible,
                    "airline_visible": False,
                    "operational_notes": "No communication was transmitted.",
                    "created_at": self.anchor - timedelta(hours=8 - event_index),
                },
                scenario=scenario_key,
            ))

        if scenario.get("after_sales"):
            case_id = self.stable_id(self._key(scenario, "after_sales"))
            impact_id = self.stable_id(self._key(scenario, "after_sales_impact"))
            self._add(
                "after_sales_cases",
                AfterSalesCase,
                self._key(scenario, "after_sales"),
                {
                    "agency_id": self.agency_id,
                    "case_reference": f"DEMO-AS-{token}",
                    "case_type": scenario["after_sales"],
                    "case_status": "assessing",
                    "case_priority": "urgent" if scenario["after_sales"] == "disruption_irregular_operation" else "high",
                    "case_title": scenario["label"],
                    "case_summary": "Synthetic change/refund case requiring authorized manual review.",
                    "operational_workspace_id": operational_id,
                    "travel_request_workspace_id": request_workspace_id,
                    "trip_workspace_id": trip_id,
                    "booking_workspace_id": booking_id,
                    "workflow_instance_id": workflow_id,
                    "source_entity_type": "booking_workspace",
                    "source_entity_id": booking_id,
                    "idempotency_key": f"demo-after-sales:{self.agency_id}:{scenario_key}",
                    "ticket_workspace_ids": [ticket_id] if ticket_id else [],
                    "emd_workspace_ids": [emd_id] if emd_id else [],
                    "passenger_workspace_ids": passenger_workspace_ids,
                    "document_workspace_ids": [document_id],
                    "invoice_ids": [invoice_id] if invoice_id else [],
                    "payment_record_ids": [payment_id] if payment_id else [],
                    "accepted_offer_snapshot_id": self.stable_id(self._key(scenario, "accepted_snapshot")),
                    "booking_reference": f"D{token[:5]}",
                    "affected_segment_refs": [f"SEG-{item + 1}" for item in range(len(segment_ids))],
                    "timeline_entry_ids": timeline_ids,
                    "financial_impact_ids": [impact_id],
                    "item_count": 1,
                    "financial_impact_count": 1,
                    "impact_scope_json": {"trip_workspace_id": trip_id, "booking_workspace_id": booking_id, "ticket_workspace_ids": [ticket_id] if ticket_id else []},
                    "coupon_status_snapshot_json": {"status": scenario["ticket_state"] or "unknown", "immutable": True},
                    "residual_value_summary": "Manual calculation required",
                    "penalty_summary": "Unknown until supplier review",
                    "fare_difference_summary": "Not calculated",
                    "service_fee_summary": "Agency fee pending approval",
                    "refundability_summary": "Refund placeholder; no commitment",
                    "supplier_communication_required": True,
                    "client_approval_required": True,
                    "approval_status": "pending",
                    "generated_advice_json": {"advisory_only": True, "next_action": "Review with supplier and client"},
                    "internal_message_json": {"summary": "Internal servicing review required"},
                    "client_message_json": {"summary": "We are reviewing available options"},
                    "financial_estimate_json": {"status": "placeholder", "currency": currency},
                    "assigned_agent": self.actor_user_id,
                    "assigned_team": self.profile["team_code"],
                    "opened_at": self.anchor - timedelta(hours=6),
                    "created_by": self.actor_user_id,
                    "updated_by": self.actor_user_id,
                },
                scenario=scenario_key,
            )
            self._add(
                "after_sales_case_items",
                AfterSalesCaseItem,
                self._key(scenario, "after_sales_item"),
                {
                    "agency_id": self.agency_id,
                    "case_id": case_id,
                    "case_reference": f"DEMO-AS-{token}",
                    "item_type": "ticket_coupon" if ticket_id else "flight_segment",
                    "source_entity_type": "ticket_workspace" if ticket_id else "flight_workspace",
                    "source_entity_id": ticket_id or segment_ids[0],
                    "trip_workspace_id": trip_id,
                    "booking_workspace_id": booking_id,
                    "ticket_workspace_id": ticket_id,
                    "passenger_workspace_id": passenger_workspace_ids[0],
                    "segment_reference": "SEG-1",
                    "coupon_number": "1" if ticket_id else None,
                    "coupon_status": scenario["ticket_state"],
                    "impact_type": scenario["after_sales"],
                    "impact_status": "requires_review",
                    "impact_summary": "Synthetic affected record linkage.",
                    "snapshot_json": {"immutable": True, "synthetic": True},
                    "created_by": self.actor_user_id,
                    "updated_by": self.actor_user_id,
                },
                scenario=scenario_key,
            )
            self._add(
                "after_sales_financial_impacts",
                AfterSalesFinancialImpact,
                self._key(scenario, "after_sales_impact"),
                {
                    "agency_id": self.agency_id,
                    "case_id": case_id,
                    "impact_reference": f"DEMO-FI-{token}",
                    "impact_type": "refund" if scenario["after_sales"] == "disruption_irregular_operation" else "fare_difference",
                    "amount_category": "unknown",
                    "estimate_status": "placeholder",
                    "currency": currency,
                    "direction": "credit" if scenario["after_sales"] == "disruption_irregular_operation" else "neutral",
                    "calculation_basis": "Manual supplier quote required",
                    "placeholder_notes": "No financial commitment, refund, or exchange was executed.",
                    "invoice_ids": [invoice_id] if invoice_id else [],
                    "payment_record_ids": [payment_id] if payment_id else [],
                    "ticket_record_ids": [ticket_id] if ticket_id else [],
                    "accepted_offer_snapshot_id": self.stable_id(self._key(scenario, "accepted_snapshot")),
                    "booking_reference": f"D{token[:5]}",
                    "original_financial_snapshot_json": {"currency": currency, "total": total},
                    "proposed_financial_impact_snapshot_json": {"status": "unknown"},
                    "approval_state": "not_reviewed",
                    "settlement_state": "not_settled",
                    "reconciliation_state": "unreconciled",
                    "linked_financial_records": bool(invoice_id),
                    "manual_unreconciled": True,
                    "created_by": self.actor_user_id,
                    "updated_by": self.actor_user_id,
                },
                scenario=scenario_key,
            )

        self._add(
            "audit_events",
            AuditEvent,
            self._key(scenario, "audit"),
            {
                "agency_id": self.agency_id,
                "actor_user_id": self.actor_user_id,
                "event_type": "agency.onboarding.demo_scenario_generated",
                "entity_type": "trip_workspace",
                "entity_id": trip_id,
                "summary": f"Generated synthetic scenario: {scenario['label']}.",
                "metadata": {"synthetic": True, "demo_profile": self.demo_profile, "scenario": scenario_key},
                "created_at": self.anchor - timedelta(minutes=index + 1),
            },
            scenario=scenario_key,
        )
        self.ids[scenario_key] = {
            "client_id": client_id,
            "passenger_ids": passenger_ids,
            "passenger_workspace_ids": passenger_workspace_ids,
            "operational_workspace_id": operational_id,
            "request_id": request_id,
            "request_workspace_id": request_workspace_id,
            "trip_workspace_id": trip_id,
            "flight_workspace_ids": segment_ids,
            "offer_workspace_id": offer_workspace_id,
            "offer_workspace_v2_id": offer_v2_id,
            "offer_option_ids": option_ids,
            "offer_acceptance_id": acceptance_id,
            "booking_readiness_package_id": readiness_id,
            "booking_handoff_id": handoff_id,
            "booking_workspace_id": booking_id,
            "ticket_workspace_id": ticket_id,
            "emd_workspace_id": emd_id,
            "document_workspace_id": document_id,
            "document_package_id": package_id,
            "passenger_service_workspace_ids": service_ids,
            "workflow_instance_id": workflow_id,
            "invoice_id": invoice_id,
            "payment_id": payment_id,
        }

    async def generate(self) -> dict[str, Any]:
        for index, scenario in enumerate(SCENARIOS[: int(self.profile["scenario_count"])]):
            self._build_scenario(scenario, index)
        await self._persist()
        counts = Counter(collection for collection, _, _ in self.records)
        return {
            "generator_version": GENERATOR_VERSION,
            "demo_profile": self.demo_profile,
            "profile_label": self.profile["label"],
            "anchor_date": self.anchor_date.isoformat(),
            "record_count": len(self.records),
            "record_counts": dict(sorted(counts.items())),
            "scenario_count": len(self.ids),
            "scenarios": [
                {"key": item["key"], "label": item["label"], "status": item["trip_status"]}
                for item in SCENARIOS[: int(self.profile["scenario_count"])]
            ],
            "generated_operational_areas": OPERATIONAL_AREAS,
            "record_ids": self.ids,
            "deterministic": True,
            "idempotent": True,
            "tenant_scoped": True,
            "bounded_execution": True,
            "provider_execution": False,
            "payment_execution": False,
            "airline_communication": False,
            "ticket_issuance": False,
        }
