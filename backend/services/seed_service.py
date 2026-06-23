from datetime import date, datetime, timedelta, timezone
import re
from typing import Any, Dict, Iterable, List

from database import Database
from models import (
    Agency,
    AgencyEmailSettings,
    AgencyStaffMembership,
    AgencyWorkspace,
    AuditEvent,
    AuthIdentity,
    AgencyAirlineOverride,
    AirlineEmdRuleNote,
    AirlineKnowledgeItem,
    AirlineKnowledgeSource,
    AirlineProcedure,
    AirlineProfile,
    Booking,
    BookingPassenger,
    BookingSegment,
    BookingTimelineEvent,
    ClientPassengerRelationship,
    ClientProfile,
    DocumentAcknowledgement,
    DocumentDelivery,
    DocumentDeliveryAttempt,
    DocumentExport,
    DocumentTemplate,
    DocumentTimelineEvent,
    EMDRecord,
    GlobalReferenceRecord,
    Invoice,
    InvoiceLineItem,
    Offer,
    OfferFareOption,
    OfferPassenger,
    OfferPriceLine,
    OfferRouteAlternative,
    OfferSegment,
    OfferServiceCheck,
    OfferTimelineEvent,
    PaymentRecord,
    PassengerProfile,
    RefundExchangeCase,
    RefundExchangeFinancialLine,
    RefundExchangeItem,
    RefundExchangeMessage,
    RefundExchangeTimelineEvent,
    PlatformRole,
    PlatformUser,
    PortalAccessMapping,
    PortalActionEvent,
    RequestMessage,
    RequestPassenger,
    RequestSegment,
    RequestTask,
    RequestTimelineEvent,
    RequestedService,
    RenderedDocument,
    SubscriptionStatus,
    TicketRecord,
    TravelRequest,
)
from security import hash_password, normalize_email
from services.document_rendering_service import render_document_payload
from services.file_storage_service import get_export_bytes, save_export_bytes
from services.pdf_rendering_service import pdf_capabilities, render_pdf_from_html


DEMO_OWNER_EMAIL = "owner@aeroassist.dev"
DEMO_AGENCY_SLUG = "demo-aeroassist-travel"
DEMO_PASSWORD = "DemoPass123!"


def safe_seed_filename(value: str, suffix: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._").lower() or "document"
    if not base.endswith(suffix):
        base = f"{base}{suffix}"
    return base


def reference_record(domain: str, key: str, label: str, description: str = "", metadata: Dict[str, Any] | None = None) -> GlobalReferenceRecord:
    return GlobalReferenceRecord(
        domain=domain,
        key=key,
        label=label,
        description=description or None,
        metadata=metadata or {},
    )


def core_reference_records() -> Iterable[GlobalReferenceRecord]:
    records = [
        reference_record("countries", "SK", "Slovakia"),
        reference_record("countries", "CZ", "Czechia"),
        reference_record("countries", "US", "United States"),
        reference_record("currencies", "EUR", "Euro"),
        reference_record("currencies", "USD", "US Dollar"),
        reference_record("currencies", "CZK", "Czech Koruna"),
        reference_record("timezones", "Europe/Bratislava", "Europe/Bratislava"),
        reference_record("timezones", "UTC", "UTC"),
    ]

    for role in ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]:
        records.append(reference_record("platform_roles", role, role.replace("_", " ").title()))

    for role in ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]:
        records.append(reference_record("agency_roles", role, role.replace("_", " ").title()))

    for status in ["prospect", "onboarding", "active", "suspended", "cancelled", "archived"]:
        records.append(reference_record("agency_statuses", status, status.replace("_", " ").title()))

    for status in ["trial", "active", "past_due", "suspended", "cancelled"]:
        records.append(reference_record("subscription_statuses", status, status.replace("_", " ").title()))

    for status in ["not_configured", "draft", "active", "suspended"]:
        records.append(reference_record("website_statuses", status, status.replace("_", " ").title()))

    for status in ["not_configured", "active", "suspended"]:
        records.append(reference_record("portal_statuses", status, status.replace("_", " ").title()))

    return records


async def seed_core_data(db: Database) -> Dict[str, Any]:
    users = db.collection("platform_users")
    agencies = db.collection("agencies")
    workspaces = db.collection("agency_workspaces")
    memberships = db.collection("agency_staff_memberships")
    clients = db.collection("client_profiles")
    portal_mappings = db.collection("portal_access_mappings")
    passengers = db.collection("passenger_profiles")
    relationships = db.collection("client_passenger_relationships")
    requests = db.collection("travel_requests")
    request_passengers = db.collection("request_passengers")
    request_segments = db.collection("request_segments")
    requested_services = db.collection("requested_services")
    request_messages = db.collection("request_messages")
    request_tasks = db.collection("request_tasks")
    request_timeline = db.collection("request_timeline_events")
    offers = db.collection("offers")
    offer_passengers = db.collection("offer_passengers")
    offer_routes = db.collection("offer_route_alternatives")
    offer_segments = db.collection("offer_segments")
    offer_fares = db.collection("offer_fare_options")
    offer_price_lines = db.collection("offer_price_lines")
    offer_service_checks = db.collection("offer_service_checks")
    offer_timeline = db.collection("offer_timeline_events")
    bookings = db.collection("bookings")
    booking_passengers = db.collection("booking_passengers")
    booking_segments = db.collection("booking_segments")
    ticket_records = db.collection("ticket_records")
    emd_records = db.collection("emd_records")
    invoices = db.collection("invoices")
    invoice_line_items = db.collection("invoice_line_items")
    payment_records = db.collection("payment_records")
    booking_timeline = db.collection("booking_timeline_events")
    refund_exchange_cases = db.collection("refund_exchange_cases")
    refund_exchange_items = db.collection("refund_exchange_items")
    refund_exchange_financial_lines = db.collection("refund_exchange_financial_lines")
    refund_exchange_messages = db.collection("refund_exchange_messages")
    refund_exchange_timeline = db.collection("refund_exchange_timeline_events")
    airline_profiles = db.collection("airline_profiles")
    airline_knowledge_items = db.collection("airline_knowledge_items")
    airline_procedures = db.collection("airline_procedures")
    airline_emd_rule_notes = db.collection("airline_emd_rule_notes")
    airline_sources = db.collection("airline_knowledge_sources")
    airline_overrides = db.collection("agency_airline_overrides")
    document_templates = db.collection("document_templates")
    rendered_documents = db.collection("rendered_documents")
    document_exports = db.collection("document_exports")
    document_deliveries = db.collection("document_deliveries")
    document_delivery_attempts = db.collection("document_delivery_attempts")
    agency_email_settings = db.collection("agency_email_settings")
    document_timeline = db.collection("document_timeline_events")
    portal_action_events = db.collection("portal_action_events")
    document_acknowledgements = db.collection("document_acknowledgements")
    references = db.collection("global_reference_records")
    audits = db.collection("audit_events")
    auth_identities = db.collection("auth_identities")

    created: List[str] = []

    owner = await users.find_one({"email": DEMO_OWNER_EMAIL})
    if owner is None:
        owner_model = PlatformUser(
            email=DEMO_OWNER_EMAIL,
            full_name="Demo Platform Owner",
            global_role=PlatformRole.PLATFORM_OWNER,
        )
        owner = await users.insert_one(owner_model.model_dump(mode="json"))
        created.append("platform_user")

    agency = await agencies.find_one({"slug": DEMO_AGENCY_SLUG})
    if agency is None:
        agency_model = Agency(
            name="Demo AeroAssist Travel",
            slug=DEMO_AGENCY_SLUG,
            legal_name="Demo AeroAssist Travel s.r.o.",
            subscription_status=SubscriptionStatus.TRIAL,
        )
        agency = await agencies.insert_one(agency_model.model_dump(mode="json"))
        created.append("agency")

    workspace = await workspaces.find_one({"agency_id": agency["id"]})
    if workspace is None:
        workspace_model = AgencyWorkspace(
            agency_id=agency["id"],
            name=agency["name"],
            brand_name=agency["name"],
            default_currency=agency["default_currency"],
            timezone=agency["timezone"],
            primary_color="#2563eb",
            secondary_color="#0f172a",
        )
        await workspaces.insert_one(workspace_model.model_dump(mode="json"))
        created.append("agency_workspace")

    membership = await memberships.find_one({"agency_id": agency["id"], "user_id": owner["id"]})
    if membership is None:
        membership_model = AgencyStaffMembership(
            agency_id=agency["id"],
            user_id=owner["id"],
            agency_role="agency_owner",
            status="active",
            joined_at=owner["created_at"],
        )
        await memberships.insert_one(membership_model.model_dump(mode="json"))
        created.append("agency_staff_membership")

    async def ensure_platform_user(email: str, full_name: str, global_role: str | None = None) -> dict:
        existing_user = await users.find_one({"email": email})
        if existing_user:
            return existing_user
        user_model = PlatformUser(email=email, full_name=full_name, global_role=global_role, status="active")
        created_user = await users.insert_one(user_model.model_dump(mode="json"))
        created.append(f"platform_user:{email}")
        return created_user

    async def ensure_identity(email: str, identity_type: str) -> dict:
        normalized = normalize_email(email)
        existing_identity = await auth_identities.find_one({"normalized_email": normalized})
        if existing_identity:
            return existing_identity
        identity = AuthIdentity(
            email=email,
            normalized_email=normalized,
            password_hash=hash_password(DEMO_PASSWORD),
            identity_type=identity_type,
            status="active",
        )
        created_identity = await auth_identities.insert_one(identity.model_dump(mode="json"))
        created.append(f"auth_identity:{email}")
        return created_identity

    agency_owner_user = await ensure_platform_user("agency.owner@aeroassist.dev", "Demo Agency Owner")
    agency_agent_user = await ensure_platform_user("agency.agent@aeroassist.dev", "Demo Agency Agent")
    for staff_user, role in [(agency_owner_user, "agency_owner"), (agency_agent_user, "agency_agent")]:
        existing_staff = await memberships.find_one({"agency_id": agency["id"], "user_id": staff_user["id"]})
        if existing_staff is None:
            await memberships.insert_one(
                AgencyStaffMembership(
                    agency_id=agency["id"],
                    user_id=staff_user["id"],
                    agency_role=role,
                    status="active",
                    joined_at=staff_user["created_at"],
                ).model_dump(mode="json")
            )
            created.append(f"agency_staff_membership:{staff_user['email']}")

    await ensure_identity(DEMO_OWNER_EMAIL, "platform_user")
    await ensure_identity("agency.owner@aeroassist.dev", "agency_staff")
    await ensure_identity("agency.agent@aeroassist.dev", "agency_staff")

    for record in core_reference_records():
        existing = await references.find_one({"domain": record.domain, "key": record.key})
        if existing is None:
            await references.insert_one(record.model_dump(mode="json"))
            created.append(f"reference:{record.domain}:{record.key}")

    individual_client = await clients.find_one({"agency_id": agency["id"], "primary_email": "anna.client@example.com"})
    if individual_client is None:
        individual_model = ClientProfile(
            agency_id=agency["id"],
            client_type="individual",
            display_name="Anna Novak",
            legal_name="Anna Novak",
            primary_email="anna.client@example.com",
            primary_phone="+421 900 111 222",
            country="SK",
            city="Bratislava",
            preferred_language="sk",
            default_currency="EUR",
            portal_status="active",
            marketing_consent=True,
            data_processing_consent=True,
            client_visible_notes="Prefers concise travel summaries.",
        )
        individual_client = await clients.insert_one(individual_model.model_dump(mode="json"))
        created.append("client:individual")

    organization_client = await clients.find_one({"agency_id": agency["id"], "primary_email": "travel@orbitex.example.com"})
    if organization_client is None:
        organization_model = ClientProfile(
            agency_id=agency["id"],
            client_type="organization",
            display_name="Orbitex Consulting",
            legal_name="Orbitex Consulting s.r.o.",
            primary_email="travel@orbitex.example.com",
            primary_phone="+421 900 333 444",
            country="SK",
            city="Bratislava",
            preferred_language="en",
            default_currency="EUR",
            tax_id="SK-DEMO-001",
            company_registration_number="DEMO-456789",
            portal_status="no_portal_access",
            data_processing_consent=True,
            internal_notes="Demo company client for employee travel.",
        )
        organization_client = await clients.insert_one(organization_model.model_dump(mode="json"))
        created.append("client:organization")

    family_client = await clients.find_one({"agency_id": agency["id"], "primary_email": "family.guardian@example.com"})
    if family_client is None:
        family_model = ClientProfile(
            agency_id=agency["id"],
            client_type="family_household",
            display_name="Kovac Family",
            legal_name="Kovac Family",
            primary_email="family.guardian@example.com",
            primary_phone="+421 900 555 666",
            country="SK",
            city="Kosice",
            preferred_language="sk",
            default_currency="EUR",
            portal_status="invited",
            data_processing_consent=True,
        )
        family_client = await clients.insert_one(family_model.model_dump(mode="json"))
        created.append("client:family")

    portal_specs = [
        (individual_client, "anna.client@example.com", "Anna Novak"),
        (organization_client, "travel@orbitex.example.com", "Orbitex Travel Desk"),
    ]
    for client, user_email, display_name in portal_specs:
        existing_portal = await portal_mappings.find_one({"agency_id": agency["id"], "user_email": user_email})
        if existing_portal is None:
            portal_mapping = PortalAccessMapping(
                agency_id=agency["id"],
                client_id=client["id"],
                user_email=user_email,
                portal_status="active",
                display_name=display_name,
            )
            await portal_mappings.insert_one(portal_mapping.model_dump(mode="json"))
            created.append(f"portal_mapping:{user_email}")
        await ensure_identity(user_email, "client_portal")

    anna_passenger = await passengers.find_one({"agency_id": agency["id"], "display_name": "Anna Novak"})
    if anna_passenger is None:
        anna_model = PassengerProfile(
            agency_id=agency["id"],
            first_name="Anna",
            last_name="Novak",
            display_name="Anna Novak",
            date_of_birth=date(1988, 4, 12),
            passenger_type="ADT",
            nationality="SK",
            residence_country="SK",
            primary_language="sk",
            passport_country="SK",
            meal_preferences="Vegetarian meal when available.",
        )
        anna_passenger = await passengers.insert_one(anna_model.model_dump(mode="json"))
        created.append("passenger:anna")

    employee_passenger = await passengers.find_one({"agency_id": agency["id"], "display_name": "Martin Horvath"})
    if employee_passenger is None:
        employee_model = PassengerProfile(
            agency_id=agency["id"],
            first_name="Martin",
            last_name="Horvath",
            display_name="Martin Horvath",
            date_of_birth=date(1979, 9, 3),
            passenger_type="ADT",
            nationality="SK",
            residence_country="SK",
            primary_language="en",
            loyalty_numbers=[{"airline": "LH", "number": "DEMO12345"}],
        )
        employee_passenger = await passengers.insert_one(employee_model.model_dump(mode="json"))
        created.append("passenger:employee")

    child_passenger = await passengers.find_one({"agency_id": agency["id"], "display_name": "Eva Kovac"})
    if child_passenger is None:
        child_model = PassengerProfile(
            agency_id=agency["id"],
            first_name="Eva",
            last_name="Kovac",
            display_name="Eva Kovac",
            date_of_birth=date(2016, 6, 22),
            passenger_type="CHD",
            nationality="SK",
            residence_country="SK",
            primary_language="sk",
            known_assistance_needs="Child traveler; guardian manages profile.",
        )
        child_passenger = await passengers.insert_one(child_model.model_dump(mode="json"))
        created.append("passenger:child")

    relationship_specs = [
        (individual_client["id"], anna_passenger["id"], "self", True, True, True, True, True, True, "granted"),
        (organization_client["id"], employee_passenger["id"], "company_traveler", True, False, False, True, True, True, "not_required"),
        (family_client["id"], child_passenger["id"], "guardian", True, True, True, True, True, True, "granted"),
    ]
    for client_id, passenger_id, relationship_type, can_view, can_edit, can_upload, can_request, can_pay, can_notify, consent in relationship_specs:
        existing = await relationships.find_one({"agency_id": agency["id"], "client_id": client_id, "passenger_id": passenger_id})
        if existing is None:
            relationship_model = ClientPassengerRelationship(
                agency_id=agency["id"],
                client_id=client_id,
                passenger_id=passenger_id,
                relationship_type=relationship_type,
                can_view=can_view,
                can_edit=can_edit,
                can_upload_documents=can_upload,
                can_request_travel=can_request,
                can_pay=can_pay,
                can_receive_notifications=can_notify,
                consent_status=consent,
                notes="Seeded CRM relationship.",
            )
            await relationships.insert_one(relationship_model.model_dump(mode="json"))
            created.append(f"relationship:{relationship_type}")

    async def ensure_request_bundle(
        reference: str,
        client: dict,
        passenger: dict,
        title: str,
        route_summary: str,
        service_summary: str,
        source: str,
        priority: str,
        relationship_type: str,
    ) -> None:
        existing_request = await requests.find_one({"agency_id": agency["id"], "request_reference": reference})
        if existing_request is not None:
            return
        request_model = TravelRequest(
            agency_id=agency["id"],
            client_id=client["id"],
            created_by_user_id=owner["id"],
            request_reference=reference,
            title=title,
            status="triage",
            priority=priority,
            source=source,
            route_summary=route_summary,
            service_summary=service_summary,
            passenger_count=1,
            service_count=2,
            client_notes="Seeded request intake example.",
            internal_notes="Demo operational request; no offer exists yet.",
            client_visible_notes="We are reviewing your travel request.",
            assigned_user_id=owner["id"],
        )
        request_doc = await requests.insert_one(request_model.model_dump(mode="json"))
        relationship = await relationships.find_one({"agency_id": agency["id"], "client_id": client["id"], "passenger_id": passenger["id"]})
        request_passenger_model = RequestPassenger(
            agency_id=agency["id"],
            request_id=request_doc["id"],
            passenger_id=passenger["id"],
            client_passenger_relationship_id=relationship["id"] if relationship else None,
            role_in_request="traveler" if relationship_type != "guardian" else "beneficiary",
            is_primary_traveler=True,
            service_needs_summary="Review passenger profile and requested services.",
            snapshot_display_name=passenger["display_name"],
            snapshot_date_of_birth=passenger["date_of_birth"],
            snapshot_passenger_type=passenger["passenger_type"],
        )
        await request_passengers.insert_one(request_passenger_model.model_dump(mode="json"))
        segments = [
            RequestSegment(
                agency_id=agency["id"],
                request_id=request_doc["id"],
                sequence=1,
                origin_text="Bratislava or Vienna",
                origin_city="Bratislava",
                origin_country="SK",
                destination_text="London",
                destination_city="London",
                destination_country="GB",
                departure_time_window="morning preferred",
                cabin_preference="economy",
                notes="Intended segment only; not booked.",
            ),
            RequestSegment(
                agency_id=agency["id"],
                request_id=request_doc["id"],
                sequence=2,
                origin_text="London",
                origin_city="London",
                origin_country="GB",
                destination_text="Bratislava or Vienna",
                destination_city="Bratislava",
                destination_country="SK",
                departure_time_window="afternoon preferred",
                cabin_preference="economy",
                notes="Return date flexible.",
            ),
        ]
        for segment in segments:
            await request_segments.insert_one(segment.model_dump(mode="json"))
        services = [
            RequestedService(
                agency_id=agency["id"],
                request_id=request_doc["id"],
                passenger_id=passenger["id"],
                service_code="BAG",
                service_name="Checked baggage",
                service_category="baggage",
                details="Compare options with one checked bag.",
                client_visible_summary="Checked baggage requested.",
            ),
            RequestedService(
                agency_id=agency["id"],
                request_id=request_doc["id"],
                passenger_id=passenger["id"],
                service_code="SEAT",
                service_name="Seat preference",
                service_category="seating",
                details="Prefer aisle seating where possible.",
                client_visible_summary="Seat preference noted.",
            ),
        ]
        for service in services:
            await requested_services.insert_one(service.model_dump(mode="json"))
        messages = [
            RequestMessage(agency_id=agency["id"], request_id=request_doc["id"], sender_user_id=owner["id"], sender_type="staff", visibility="client_visible", message_text="We received your request and are reviewing options."),
            RequestMessage(agency_id=agency["id"], request_id=request_doc["id"], sender_user_id=owner["id"], sender_type="staff", visibility="internal", message_text="Check schedule alternatives manually before offer phase."),
        ]
        for message in messages:
            await request_messages.insert_one(message.model_dump(mode="json"))
        tasks = [
            RequestTask(agency_id=agency["id"], request_id=request_doc["id"], assigned_user_id=owner["id"], title="Review route alternatives", priority="normal", visibility="internal"),
            RequestTask(agency_id=agency["id"], request_id=request_doc["id"], assigned_user_id=owner["id"], title="Confirm passenger service needs", priority="high", visibility="internal"),
        ]
        for task in tasks:
            await request_tasks.insert_one(task.model_dump(mode="json"))
        timeline_events = [
            RequestTimelineEvent(agency_id=agency["id"], request_id=request_doc["id"], actor_user_id=owner["id"], event_type="request.created", title="Request created", summary=title),
            RequestTimelineEvent(agency_id=agency["id"], request_id=request_doc["id"], actor_user_id=owner["id"], event_type="request.seeded_context", title="Seeded request details", summary="Passengers, segments, services, messages, and tasks were added."),
        ]
        for event in timeline_events:
            await request_timeline.insert_one(event.model_dump(mode="json"))
        created.append(f"request:{reference}")

    await ensure_request_bundle("REQ-DEMO-0001", individual_client, anna_passenger, "Anna London trip inquiry", "Bratislava/Vienna to London return", "Baggage and seat preference", "staff_created", "normal", "self")
    await ensure_request_bundle("REQ-DEMO-0002", organization_client, employee_passenger, "Orbitex employee business trip", "Bratislava/Vienna to London return", "Checked baggage and schedule flexibility", "email", "high", "company_traveler")

    async def ensure_offer_bundle(reference: str, client: dict, passenger: dict, request_reference: str | None, title: str, source: str, status: str) -> None:
        existing_offer = await offers.find_one({"agency_id": agency["id"], "offer_reference": reference})
        if existing_offer is not None:
            return
        linked_request = await requests.find_one({"agency_id": agency["id"], "request_reference": request_reference}) if request_reference else None
        offer_model = Offer(
            agency_id=agency["id"],
            offer_reference=reference,
            client_id=client["id"],
            request_id=linked_request["id"] if linked_request else None,
            created_by_user_id=owner["id"],
            assigned_user_id=owner["id"],
            title=title,
            status=status,
            source=source,
            currency="EUR",
            client_language="en",
            client_visible_intro="Manually researched option prepared by your travel agent.",
            client_visible_terms="Prices must be verified before ticketing. No booking is created from this offer yet.",
            route_alternative_count=1,
            fare_option_count=2,
            total_min_amount=320,
            total_max_amount=470,
        )
        offer_doc = await offers.insert_one(offer_model.model_dump(mode="json"))
        offer_passenger = OfferPassenger(
            agency_id=agency["id"],
            offer_id=offer_doc["id"],
            passenger_id=passenger["id"],
            snapshot_display_name=passenger["display_name"],
            snapshot_date_of_birth=passenger["date_of_birth"],
            snapshot_passenger_type=passenger["passenger_type"],
            is_primary_traveler=True,
        )
        await offer_passengers.insert_one(offer_passenger.model_dump(mode="json"))
        route = OfferRouteAlternative(
            agency_id=agency["id"],
            offer_id=offer_doc["id"],
            sequence=1,
            label="A",
            title="Manual option A",
            status="complete",
            source_channel="manual",
            carrier_summary="Austrian / partner availability checked manually",
            route_summary="Vienna to London return",
            schedule_summary="Morning outbound, afternoon return",
            total_travel_time_minutes=150,
            stop_count=0,
            connection_quality="excellent",
            service_support_summary="Baggage and seat requests can be handled manually.",
            recommendation_label="Recommended",
            agent_recommendation_reason="Best balance of schedule and service support.",
            client_visible_notes="Manually researched option. Price must be verified before ticketing.",
        )
        route_doc = await offer_routes.insert_one(route.model_dump(mode="json"))
        segment = OfferSegment(
            agency_id=agency["id"],
            offer_id=offer_doc["id"],
            route_alternative_id=route_doc["id"],
            sequence=1,
            marketing_airline_code="OS",
            marketing_airline_name="Austrian",
            flight_number="OS451",
            origin_airport_code="VIE",
            origin_city="Vienna",
            destination_airport_code="LHR",
            destination_city="London",
            cabin="economy",
            booking_class="K",
            baggage_summary="1 cabin bag included; checked bag depends on fare option.",
        )
        await offer_segments.insert_one(segment.model_dump(mode="json"))
        fare_specs = [
            ("Basic", 220, 80, 0, 20, False),
            ("Standard", 290, 80, 60, 40, True),
        ]
        for idx, (label, base, taxes, airline_fee, agency_fee, recommended) in enumerate(fare_specs, start=1):
            total = base + taxes + airline_fee + agency_fee
            fare = OfferFareOption(
                agency_id=agency["id"],
                offer_id=offer_doc["id"],
                route_alternative_id=route_doc["id"],
                sequence=idx,
                label=label,
                branded_fare_name=label,
                status="complete",
                currency="EUR",
                base_fare_amount=base,
                taxes_amount=taxes,
                airline_fees_amount=airline_fee,
                agency_service_fee_amount=agency_fee,
                total_amount=total,
                refundable_status="unknown",
                changeability_status="changes_with_fee",
                baggage_summary="Basic excludes checked bag; Standard includes checked bag.",
                seat_selection_summary="Seat selection may be chargeable.",
                is_recommended=recommended,
            )
            fare_doc = await offer_fares.insert_one(fare.model_dump(mode="json"))
            for line_type, description, amount in [
                ("airfare", "Manual airfare quote", base),
                ("taxes", "Estimated taxes", taxes),
                ("airline_ancillary", "Airline ancillary fees", airline_fee),
                ("agency_service_fee", "Agency service fee", agency_fee),
            ]:
                if amount:
                    line = OfferPriceLine(
                        agency_id=agency["id"],
                        offer_id=offer_doc["id"],
                        route_alternative_id=route_doc["id"],
                        fare_option_id=fare_doc["id"],
                        line_type=line_type,
                        description=description,
                        quantity=1,
                        unit_amount=amount,
                        total_amount=amount,
                        currency="EUR",
                        supplier_pass_through=line_type != "agency_service_fee",
                    )
                    await offer_price_lines.insert_one(line.model_dump(mode="json"))
        check = OfferServiceCheck(
            agency_id=agency["id"],
            offer_id=offer_doc["id"],
            route_alternative_id=route_doc["id"],
            passenger_id=passenger["id"],
            service_code="BAG",
            service_name="Checked baggage",
            support_status="chargeable",
            client_visible_summary="Checked baggage available through Standard option.",
            internal_notes="Verify live fare family before ticketing.",
            estimated_fee_amount=60,
            currency="EUR",
        )
        await offer_service_checks.insert_one(check.model_dump(mode="json"))
        event = OfferTimelineEvent(agency_id=agency["id"], offer_id=offer_doc["id"], actor_user_id=owner["id"], event_type="offer.seeded", title="Seeded offer", summary="Manual offer demo data created.")
        await offer_timeline.insert_one(event.model_dump(mode="json"))
        created.append(f"offer:{reference}")

    await ensure_offer_bundle("OFF-DEMO-0001", individual_client, anna_passenger, "REQ-DEMO-0001", "Anna London manual offer", "request", "draft")
    await ensure_offer_bundle("OFF-DEMO-0002", organization_client, employee_passenger, None, "Orbitex manual business offer", "manual", "ready_to_send")

    async def ensure_phase_five_operations() -> None:
        source_offer = await offers.find_one({"agency_id": agency["id"], "offer_reference": "OFF-DEMO-0002"})
        source_route = await offer_routes.find_one({"agency_id": agency["id"], "offer_id": source_offer["id"]}) if source_offer else None
        source_fare = await offer_fares.find_one({"agency_id": agency["id"], "offer_id": source_offer["id"], "label": "Standard"}) if source_offer else None
        source_offer_passengers = await offer_passengers.find_many({"agency_id": agency["id"], "offer_id": source_offer["id"]}) if source_offer else []
        source_offer_segments = await offer_segments.find_many({"agency_id": agency["id"], "offer_id": source_offer["id"], "route_alternative_id": source_route["id"]}) if source_route else []
        source_price_lines = await offer_price_lines.find_many({"agency_id": agency["id"], "offer_id": source_offer["id"], "fare_option_id": source_fare["id"]}) if source_fare else []
        source_service_checks = await offer_service_checks.find_many({"agency_id": agency["id"], "offer_id": source_offer["id"]}) if source_offer else []

        offer_booking = await bookings.find_one({"agency_id": agency["id"], "booking_reference": "BKG-DEMO-0001"})
        if offer_booking is None and source_offer and source_route and source_fare:
            booking_model = Booking(
                agency_id=agency["id"],
                booking_reference="BKG-DEMO-0001",
                client_id=organization_client["id"],
                offer_id=source_offer["id"],
                selected_route_alternative_id=source_route["id"],
                selected_fare_option_id=source_fare["id"],
                created_by_user_id=owner["id"],
                assigned_user_id=owner["id"],
                status="ticketed",
                pnr="DEMO7X",
                validating_airline_code="OS",
                booking_channel="manual",
                currency="EUR",
                total_amount=470,
                amount_paid=470,
                amount_due=0,
                internal_notes="Manual tracking record. Booking and ticketing happened in external systems.",
                client_visible_notes="Issued externally by your travel agency.",
                booking_snapshot={
                    "source": "offer",
                    "offer_reference": source_offer["offer_reference"],
                    "offer_id": source_offer["id"],
                    "selected_route": source_route,
                    "selected_fare_option": source_fare,
                    "passengers": source_offer_passengers,
                    "segments": source_offer_segments,
                    "price_lines": source_price_lines,
                    "service_checks": source_service_checks,
                },
            )
            offer_booking = await bookings.insert_one(booking_model.model_dump(mode="json"))
            for offer_passenger in source_offer_passengers:
                passenger = BookingPassenger(
                    agency_id=agency["id"],
                    booking_id=offer_booking["id"],
                    passenger_id=offer_passenger.get("passenger_id"),
                    offer_passenger_id=offer_passenger["id"],
                    snapshot_display_name=offer_passenger["snapshot_display_name"],
                    snapshot_date_of_birth=offer_passenger.get("snapshot_date_of_birth"),
                    snapshot_passenger_type=offer_passenger.get("snapshot_passenger_type") or "ADT",
                    is_primary_traveler=offer_passenger.get("is_primary_traveler", False),
                    ticket_status="issued",
                )
                await booking_passengers.insert_one(passenger.model_dump(mode="json"))
            for segment in source_offer_segments:
                booking_segment = BookingSegment(
                    agency_id=agency["id"],
                    booking_id=offer_booking["id"],
                    offer_segment_id=segment["id"],
                    sequence=segment["sequence"],
                    marketing_airline_code=segment["marketing_airline_code"],
                    marketing_airline_name=segment.get("marketing_airline_name"),
                    flight_number=segment.get("flight_number"),
                    origin_airport_code=segment["origin_airport_code"],
                    origin_city=segment.get("origin_city"),
                    destination_airport_code=segment["destination_airport_code"],
                    destination_city=segment.get("destination_city"),
                    cabin=segment.get("cabin"),
                    booking_class=segment.get("booking_class"),
                    segment_status="confirmed",
                    baggage_summary=segment.get("baggage_summary"),
                    notes="Confirmed externally; tracked in AgencyOS.",
                )
                await booking_segments.insert_one(booking_segment.model_dump(mode="json"))
            await booking_timeline.insert_one(BookingTimelineEvent(agency_id=agency["id"], booking_id=offer_booking["id"], actor_user_id=owner["id"], event_type="booking.seeded_from_offer", title="Booking created from offer", summary="Seeded post-offer tracking record.").model_dump(mode="json"))
            created.append("booking:offer")

        manual_booking = await bookings.find_one({"agency_id": agency["id"], "booking_reference": "BKG-DEMO-0002"})
        if manual_booking is None:
            manual_model = Booking(
                agency_id=agency["id"],
                booking_reference="BKG-DEMO-0002",
                client_id=family_client["id"],
                created_by_user_id=owner["id"],
                assigned_user_id=owner["id"],
                status="reserved",
                pnr="FAM42K",
                booking_channel="phone",
                currency="EUR",
                total_amount=180,
                amount_paid=0,
                amount_due=180,
                internal_notes="Manual booking without linked offer.",
            )
            manual_booking = await bookings.insert_one(manual_model.model_dump(mode="json"))
            await booking_passengers.insert_one(BookingPassenger(agency_id=agency["id"], booking_id=manual_booking["id"], passenger_id=child_passenger["id"], snapshot_display_name=child_passenger["display_name"], snapshot_date_of_birth=child_passenger["date_of_birth"], snapshot_passenger_type=child_passenger["passenger_type"], is_primary_traveler=True, ticket_status="pending").model_dump(mode="json"))
            await booking_segments.insert_one(BookingSegment(agency_id=agency["id"], booking_id=manual_booking["id"], sequence=1, marketing_airline_code="FR", marketing_airline_name="Ryanair", flight_number="FR123", origin_airport_code="BTS", origin_city="Bratislava", destination_airport_code="CIA", destination_city="Rome", segment_status="booked", notes="Reserved externally by phone.").model_dump(mode="json"))
            await booking_timeline.insert_one(BookingTimelineEvent(agency_id=agency["id"], booking_id=manual_booking["id"], actor_user_id=owner["id"], event_type="booking.seeded_manual", title="Manual booking seeded", summary="No linked request or offer.").model_dump(mode="json"))
            created.append("booking:manual")

        if offer_booking:
            booking_passenger = await booking_passengers.find_one({"agency_id": agency["id"], "booking_id": offer_booking["id"]})
            ticket = await ticket_records.find_one({"agency_id": agency["id"], "booking_id": offer_booking["id"], "ticket_number": "2571234567890"})
            if ticket is None:
                ticket_model = TicketRecord(
                    agency_id=agency["id"],
                    booking_id=offer_booking["id"],
                    passenger_id=booking_passenger.get("passenger_id") if booking_passenger else employee_passenger["id"],
                    booking_passenger_id=booking_passenger.get("id") if booking_passenger else None,
                    ticket_number="2571234567890",
                    validating_airline_code="OS",
                    issue_date=date.today(),
                    status="issued",
                    base_fare_amount=290,
                    taxes_amount=80,
                    total_amount=370,
                    currency="EUR",
                    fare_basis="KDEMO",
                    coupon_summary="1 coupon, VIE-LHR",
                    client_visible_notes="Ticket issued externally.",
                )
                ticket = await ticket_records.insert_one(ticket_model.model_dump(mode="json"))
                created.append("ticket")

            emd = await emd_records.find_one({"agency_id": agency["id"], "booking_id": offer_booking["id"], "emd_number": "2579876543210"})
            if emd is None:
                emd_model = EMDRecord(
                    agency_id=agency["id"],
                    booking_id=offer_booking["id"],
                    passenger_id=booking_passenger.get("passenger_id") if booking_passenger else employee_passenger["id"],
                    booking_passenger_id=booking_passenger.get("id") if booking_passenger else None,
                    ticket_id=ticket["id"] if ticket else None,
                    service_code="BAG",
                    service_name="Checked baggage",
                    emd_number="2579876543210",
                    emd_type="emd_a",
                    reason_for_issuance="Checked baggage issued externally.",
                    issue_date=date.today(),
                    status="issued",
                    amount=60,
                    currency="EUR",
                    client_visible_notes="Ancillary service issued externally.",
                )
                emd = await emd_records.insert_one(emd_model.model_dump(mode="json"))
                created.append("emd")

            invoice = await invoices.find_one({"agency_id": agency["id"], "invoice_number": "INV-DEMO-0001"})
            if invoice is None:
                invoice_model = Invoice(
                    agency_id=agency["id"],
                    invoice_number="INV-DEMO-0001",
                    client_id=organization_client["id"],
                    booking_id=offer_booking["id"],
                    offer_id=source_offer["id"] if source_offer else None,
                    status="paid",
                    currency="EUR",
                    subtotal_amount=470,
                    tax_amount=80,
                    total_amount=470,
                    paid_amount=470,
                    due_amount=0,
                    issue_date=date.today(),
                    client_visible_notes="Manual tracking invoice. No payment gateway connected.",
                )
                invoice = await invoices.insert_one(invoice_model.model_dump(mode="json"))
                for line_type, description, amount, pass_through in [
                    ("airfare", "Ticket base fare", 290, True),
                    ("taxes", "Ticket taxes", 80, True),
                    ("airline_ancillary", "Checked baggage EMD", 60, True),
                    ("agency_service_fee", "Agency service fee", 40, False),
                ]:
                    line_model = InvoiceLineItem(
                        agency_id=agency["id"],
                        invoice_id=invoice["id"],
                        booking_id=offer_booking["id"],
                        ticket_id=ticket["id"] if line_type in {"airfare", "taxes"} and ticket else None,
                        emd_id=emd["id"] if line_type == "airline_ancillary" and emd else None,
                        line_type=line_type,
                        description=description,
                        quantity=1,
                        unit_amount=amount,
                        total_amount=amount,
                        currency="EUR",
                        supplier_pass_through=pass_through,
                    )
                    await invoice_line_items.insert_one(line_model.model_dump(mode="json"))
                await payment_records.insert_one(PaymentRecord(agency_id=agency["id"], invoice_id=invoice["id"], booking_id=offer_booking["id"], client_id=organization_client["id"], status="received", method="bank_transfer", amount=470, currency="EUR", received_at=datetime.now(timezone.utc), external_reference="DEMO-BANK-001", reconciliation_status="reconciled", reconciliation_notes="Seeded received payment.").model_dump(mode="json"))
                await booking_timeline.insert_one(BookingTimelineEvent(agency_id=agency["id"], booking_id=offer_booking["id"], actor_user_id=owner["id"], event_type="finance.seeded_invoice_payment", title="Invoice and payment seeded", summary="Invoice line items and one received payment were added.").model_dump(mode="json"))
                created.append("invoice:paid")

    await ensure_phase_five_operations()

    async def ensure_airline_intelligence() -> None:
        airline_specs = [
            {
                "airline_code": "NX",
                "icao_code": "NXC",
                "airline_name": "Demo Network Airways",
                "country": "DE",
                "alliance": "Demo Star Alliance",
                "website_url": "https://example.com/demo-network-airways",
                "notes": "Fake/demo major network carrier for Airline Intelligence examples.",
            },
            {
                "airline_code": "LC",
                "icao_code": "LCC",
                "airline_name": "Demo LowCost Air",
                "country": "SK",
                "website_url": "https://example.com/demo-lowcost-air",
                "notes": "Fake/demo low-cost carrier for manual servicing examples.",
            },
            {
                "airline_code": "RG",
                "icao_code": "RGA",
                "airline_name": "Demo Regional Connect",
                "country": "AT",
                "website_url": "https://example.com/demo-regional-connect",
                "notes": "Fake/demo regional carrier for special assistance examples.",
            },
        ]
        airline_by_code: Dict[str, dict] = {}
        for spec in airline_specs:
            existing = await airline_profiles.find_one({"airline_code": spec["airline_code"]})
            if existing is None:
                airline = AirlineProfile(status="active", **spec)
                existing = await airline_profiles.insert_one(airline.model_dump(mode="json"))
                created.append(f"airline:{spec['airline_code']}")
            airline_by_code[spec["airline_code"]] = existing

        async def ensure_source(airline_code: str, title: str, source_type: str, reliability: str, notes: str, url: str | None = None, document_reference: str | None = None) -> dict:
            airline = airline_by_code[airline_code]
            existing = await airline_sources.find_one({"airline_id": airline["id"], "title": title})
            if existing is not None:
                return existing
            source = AirlineKnowledgeSource(
                airline_id=airline["id"],
                source_type=source_type,
                title=title,
                url=url,
                document_reference=document_reference,
                source_date=date.today(),
                captured_by_user_id=owner["id"],
                reliability=reliability,
                notes=notes,
            )
            created_source = await airline_sources.insert_one(source.model_dump(mode="json"))
            created.append(f"airline_source:{title}")
            return created_source

        network_official = await ensure_source("NX", "DEMO official airline website placeholder", "airline_website", "official", "Fake/demo source record. Replace with reviewed official source before production use.", "https://example.com/demo-network-airways/policies")
        network_iata = await ensure_source("NX", "DEMO ATPCO/IATA reference note", "atpco_iata_reference", "high", "Fake/demo industry reference note for RFIC/RFISC handling.", document_reference="DEMO-IATA-RFIC-REF")
        lowcost_experience = await ensure_source("LC", "DEMO internal agency experience note", "agency_experience", "anecdotal", "Fake/demo agency experience. Agency-specific experience should stay private unless reviewed.")
        regional_official = await ensure_source("RG", "DEMO regional carrier support page", "airline_website", "official", "Fake/demo source record for regional accessibility process.", "https://example.com/demo-regional-connect/support")

        knowledge_specs = [
            ("NX", "pet_travel", "DEMO PETC cabin pet acceptance note", "PETC", "Published demo note for cabin pet handling.", "Demo Network Airways may require advance PETC confirmation, pet/container dimensions, passenger contact data, and route review. This is decision support only and must be verified before action.", ["petc", "pets", "ssr"], [network_official["id"]], True),
            ("NX", "accessibility", "DEMO WCHR/WCHS/WCHC assistance note", "WCHR", "Published demo accessibility note.", "Wheelchair assistance requests should identify the assistance level: WCHR for ramp, WCHS for steps, and WCHC for cabin seat assistance. Confirm timing and airport handling manually.", ["wchr", "wchs", "wchc", "prm"], [network_official["id"]], False),
            ("LC", "unaccompanied_minor", "DEMO UMNR handling note", "UMNR", "Published demo UMNR note for a low-cost carrier.", "Demo LowCost Air may restrict or not support unaccompanied minors on some routes. Agents must confirm availability directly before offer or booking commitments.", ["umnr", "minor", "manual_review"], [lowcost_experience["id"]], True),
            ("RG", "baggage", "DEMO regional baggage note", "BAG", "Published demo baggage note.", "Regional aircraft may have stricter cabin baggage limits. Checked baggage and mobility equipment handling should be confirmed for smaller aircraft.", ["baggage", "regional", "aircraft"], [regional_official["id"]], False),
            ("NX", "disruption", "DEMO disruption servicing note", None, "Published demo disruption note.", "For schedule disruption cases, gather PNR, ticket number, affected coupons, passenger contact, and preferred alternatives before contacting agency support.", ["schedule_change", "disruption", "servicing"], [network_official["id"]], False),
            ("NX", "emd", "DEMO PETC EMD support note", "PETC", "Published demo EMD note.", "PETC may require an ancillary EMD depending on route and fare handling. Use RFIC/RFISC placeholders until verified against the current source.", ["emd", "rfic", "rfisc", "petc"], [network_iata["id"]], True),
        ]
        knowledge_by_title: Dict[str, dict] = {}
        for airline_code, category, title, service_code, summary, detailed_text, tags, source_ids, warning in knowledge_specs:
            airline = airline_by_code[airline_code]
            existing = await airline_knowledge_items.find_one({"airline_id": airline["id"], "title": title})
            if existing is None:
                item = AirlineKnowledgeItem(
                    airline_id=airline["id"],
                    category=category,
                    title=title,
                    summary=summary,
                    detailed_text=detailed_text,
                    service_code=service_code,
                    review_status="published",
                    confidence="official_source" if airline_code != "LC" else "medium",
                    source_ids=source_ids,
                    tags=tags,
                    client_visible_allowed=False,
                    internal_warning=warning,
                    created_by_user_id=owner["id"],
                    reviewed_by_user_id=owner["id"],
                    published_at=datetime.now(timezone.utc),
                )
                existing = await airline_knowledge_items.insert_one(item.model_dump(mode="json"))
                created.append(f"airline_knowledge:{title}")
            knowledge_by_title[title] = existing

        procedure_specs = [
            ("NX", "special_service_request", "DEMO special service request channel", "gds", None, "SSR should be entered in the external GDS or airline portal, then monitored manually for confirmation.", ["PNR", "passenger name", "service code", "segment"], "24-48h demo SLA", [network_official["id"]]),
            ("NX", "agency_support", "DEMO agency support contact", "email", "demo-agency-support@example.com", "Use only for demo escalation. Include PNR, ticket number, passenger details, and requested handling.", ["PNR", "ticket number", "request summary"], "1 business day demo SLA", [network_official["id"]]),
            ("NX", "emd", "DEMO EMD handling procedure", "gds", None, "Confirm RFIC/RFISC and EMD-S versus EMD-A in the issuing system before collecting or issuing ancillary documents.", ["service code", "amount", "currency", "ticket link"], "Manual verification required", [network_iata["id"]]),
            ("RG", "wheelchair_assistance", "DEMO regional wheelchair assistance", "webform", "https://example.com/demo-regional-connect/wheelchair", "Submit assistance request and verify aircraft limitations for regional operations.", ["passenger mobility level", "flight number", "contact phone"], "48h demo SLA", [regional_official["id"]]),
        ]
        for airline_code, procedure_type, title, channel, contact_value, instructions, required_fields, response_time, source_ids in procedure_specs:
            airline = airline_by_code[airline_code]
            existing = await airline_procedures.find_one({"airline_id": airline["id"], "title": title})
            if existing is None:
                procedure = AirlineProcedure(
                    airline_id=airline["id"],
                    procedure_type=procedure_type,
                    title=title,
                    channel=channel,
                    contact_value=contact_value,
                    instructions=instructions,
                    required_fields=required_fields,
                    expected_response_time=response_time,
                    review_status="published",
                    confidence="high",
                    source_ids=source_ids,
                )
                await airline_procedures.insert_one(procedure.model_dump(mode="json"))
                created.append(f"airline_procedure:{title}")

        emd_specs = [
            ("NX", "PETC", "Pet in cabin", "C", "0BT", "emd_s", "Pet in cabin ancillary handling.", "petc", "Demo pricing is manually quoted.", "Verify RFIC/RFISC before issuance.", "Refundability follows current fare and ancillary conditions.", [network_iata["id"]]),
            ("NX", "WCHR", "Wheelchair ramp assistance", None, None, "unknown", "Wheelchair assistance service documentation.", "wchr", "Usually no fee in demo data.", "Record service confirmation; EMD usually not expected unless airline-specific handling says otherwise.", "No standalone refund value in demo data.", [network_official["id"]]),
            ("LC", "UMNR", "Unaccompanied minor service", "D", "0NN", "emd_s", "Unaccompanied minor handling where supported.", "umnr", "Demo low-cost carrier may require manual fee confirmation.", "Do not issue until airline confirms service availability.", "Refundability must be checked manually.", [lowcost_experience["id"]]),
        ]
        for airline_code, service_code, service_name, rfic, rfisc, emd_type, reason, applies_to, pricing, issuance, refundability, source_ids in emd_specs:
            airline = airline_by_code[airline_code]
            existing = await airline_emd_rule_notes.find_one({"airline_id": airline["id"], "service_code": service_code})
            if existing is None:
                note = AirlineEmdRuleNote(
                    airline_id=airline["id"],
                    service_code=service_code,
                    service_name=service_name,
                    rfic_code=rfic,
                    rfisc_code=rfisc,
                    emd_type=emd_type,
                    reason_for_issuance=reason,
                    applies_to=applies_to,
                    pricing_note=pricing,
                    issuance_note=issuance,
                    refundability_note=refundability,
                    source_ids=source_ids,
                    review_status="published",
                    confidence="medium",
                )
                await airline_emd_rule_notes.insert_one(note.model_dump(mode="json"))
                created.append(f"airline_emd_note:{service_code}")

        target = knowledge_by_title.get("DEMO PETC cabin pet acceptance note")
        if target:
            existing_override = await airline_overrides.find_one({"agency_id": agency["id"], "target_type": "knowledge_item", "target_id": target["id"]})
            if existing_override is None:
                override = AgencyAirlineOverride(
                    agency_id=agency["id"],
                    airline_id=target["airline_id"],
                    target_type="knowledge_item",
                    target_id=target["id"],
                    override_mode="annotate",
                    title="Demo agency PETC handling note",
                    override_text="Demo AeroAssist Travel has seen PETC confirmations take longer on Friday departures. Add an internal follow-up task after request submission.",
                    internal_warning=True,
                    created_by_user_id=owner["id"],
                )
                await airline_overrides.insert_one(override.model_dump(mode="json"))
                created.append("airline_override:petc_annotation")

    await ensure_airline_intelligence()

    async def ensure_documents() -> None:
        template_specs = [
            ("offer_summary", "Default offer summary", "Client-ready HTML offer summary preview."),
            ("booking_confirmation", "Default booking confirmation", "Agency-generated booking confirmation preview."),
            ("itinerary_summary", "Default itinerary summary", "Printable itinerary summary preview."),
            ("ticket_receipt_summary", "Default ticket receipt summary", "Ticket receipt summary from manually tracked ticket records."),
            ("emd_receipt_summary", "Default EMD receipt summary", "EMD receipt summary from manually tracked EMD records."),
            ("invoice_summary", "Default invoice summary", "Invoice summary from manually tracked invoice and payment records."),
        ]
        for document_type, name, description in template_specs:
            existing = await document_templates.find_one({"agency_id": None, "document_type": document_type, "name": name})
            if existing is None:
                template = DocumentTemplate(
                    agency_id=None,
                    template_scope="platform_default",
                    document_type=document_type,
                    name=name,
                    description=description,
                    status="active",
                    language="en",
                    version=1,
                    template_config={
                        "layout": "clean_printable_html",
                        "show_preview_label": True,
                        "show_snapshot_notice": True,
                        "demo": True,
                    },
                    created_by_user_id=owner["id"],
                )
                await document_templates.insert_one(template.model_dump(mode="json"))
                created.append(f"document_template:{document_type}")

        async def seed_rendered(source_type: str, source_id: str, document_type: str) -> None:
            existing = await rendered_documents.find_one({"agency_id": agency["id"], "source_entity_type": source_type, "source_entity_id": source_id, "document_type": document_type})
            if existing is not None:
                return
            rendered = await render_document_payload(db, agency["id"], source_type, source_id, document_type, None, "en")
            document = RenderedDocument(
                agency_id=agency["id"],
                rendered_by_user_id=owner["id"],
                client_visible=True,
                internal_notes="Seeded demo HTML preview. No PDF, email, or portal publishing.",
                **rendered,
            )
            created_document = await rendered_documents.insert_one(document.model_dump(mode="json"))
            await document_timeline.insert_one(DocumentTimelineEvent(agency_id=agency["id"], rendered_document_id=created_document["id"], actor_user_id=owner["id"], event_type="document.seeded", title="Seeded rendered document", summary=created_document["title"]).model_dump(mode="json"))
            created.append(f"rendered_document:{document_type}")

        offer = await offers.find_one({"agency_id": agency["id"], "offer_reference": "OFF-DEMO-0002"})
        if offer:
            await seed_rendered("offer", offer["id"], "offer_summary")
        booking = await bookings.find_one({"agency_id": agency["id"], "booking_reference": "BKG-DEMO-0001"})
        if booking:
            await seed_rendered("booking", booking["id"], "booking_confirmation")
            await seed_rendered("booking", booking["id"], "itinerary_summary")
        invoice = await invoices.find_one({"agency_id": agency["id"], "invoice_number": "INV-DEMO-0001"})
        if invoice:
            await seed_rendered("invoice", invoice["id"], "invoice_summary")

    await ensure_documents()

    async def ensure_document_export_delivery_examples() -> None:
        settings = await agency_email_settings.find_one({"agency_id": agency["id"], "status": "active"})
        if settings is None:
            settings = await agency_email_settings.insert_one(
                AgencyEmailSettings(
                    agency_id=agency["id"],
                    sender_name=agency["name"],
                    sender_email="demo-no-reply@aeroassist.dev",
                    reply_to_email=owner["email"],
                    mode="dev_console",
                    status="active",
                ).model_dump(mode="json")
            )
            created.append("agency_email_settings:dev_console")

        document = await rendered_documents.find_one({"agency_id": agency["id"], "client_visible": True})
        if document is None:
            return

        filename = safe_seed_filename(document["title"], ".html")
        export = await document_exports.find_one({"agency_id": agency["id"], "rendered_document_id": document["id"], "export_type": "print_html", "filename": filename})
        if export is None:
            html_data = (document.get("rendered_html") or "").encode("utf-8")
            generated_at = datetime.now(timezone.utc)
            export_model = DocumentExport(
                agency_id=agency["id"],
                rendered_document_id=document["id"],
                export_type="print_html",
                status="generated",
                filename=filename,
                content_type="text/html; charset=utf-8",
                storage_mode="file_path",
                retention_policy="keep_90_days",
                retention_expires_at=generated_at + timedelta(days=90),
                generated_by_user_id=owner["id"],
                generated_at=generated_at,
                generated_from_snapshot_at=document.get("rendered_at"),
                client_visible=True,
            )
            export_data = export_model.model_dump(mode="json")
            export_data.update(save_export_bytes(agency["id"], export_model.id, filename, "text/html; charset=utf-8", html_data))
            export = await document_exports.insert_one(export_data)
            await document_timeline.insert_one(
                DocumentTimelineEvent(
                    agency_id=agency["id"],
                    rendered_document_id=document["id"],
                    actor_user_id=owner["id"],
                    event_type="document_export.seeded",
                    title="Seeded printable export",
                    summary=filename,
                ).model_dump(mode="json")
            )
            created.append("document_export:print_html")
        elif export.get("storage_mode") == "file_path":
            try:
                get_export_bytes(export)
            except Exception:
                html_data = (document.get("rendered_html") or "").encode("utf-8")
                storage_updates = save_export_bytes(agency["id"], export["id"], export["filename"], export.get("content_type") or "text/html; charset=utf-8", html_data)
                storage_updates["status"] = "generated"
                storage_updates["error_message"] = None
                export = await document_exports.update_one({"agency_id": agency["id"], "id": export["id"]}, storage_updates)
                created.append("document_export:file_restored")

        pdf_caps = pdf_capabilities()
        if pdf_caps.get("available"):
            pdf_filename = safe_seed_filename(document["title"], ".pdf")
            pdf_export = await document_exports.find_one({"agency_id": agency["id"], "rendered_document_id": document["id"], "export_type": "pdf", "filename": pdf_filename})
            if pdf_export is None:
                pdf_result = render_pdf_from_html(document.get("rendered_html") or "", document.get("title") or "Document", agency["id"], document["id"])
                if pdf_result.ok and pdf_result.data:
                    generated_at = datetime.now(timezone.utc)
                    pdf_model = DocumentExport(
                        agency_id=agency["id"],
                        rendered_document_id=document["id"],
                        export_type="pdf",
                        status="generated",
                        filename=pdf_filename,
                        content_type="application/pdf",
                        storage_mode="file_path",
                        retention_policy="keep_90_days",
                        retention_expires_at=generated_at + timedelta(days=90),
                        generated_by_user_id=owner["id"],
                        generated_at=generated_at,
                        generated_from_snapshot_at=document.get("rendered_at"),
                        client_visible=True,
                    )
                    pdf_data = pdf_model.model_dump(mode="json")
                    pdf_data.update(save_export_bytes(agency["id"], pdf_model.id, pdf_filename, "application/pdf", pdf_result.data))
                    await document_exports.insert_one(pdf_data)
                    created.append("document_export:pdf")
            elif pdf_export.get("storage_mode") == "file_path":
                try:
                    get_export_bytes(pdf_export)
                except Exception:
                    pdf_result = render_pdf_from_html(document.get("rendered_html") or "", document.get("title") or "Document", agency["id"], document["id"])
                    if pdf_result.ok and pdf_result.data:
                        storage_updates = save_export_bytes(agency["id"], pdf_export["id"], pdf_export["filename"], "application/pdf", pdf_result.data)
                        storage_updates["status"] = "generated"
                        storage_updates["error_message"] = None
                        await document_exports.update_one({"agency_id": agency["id"], "id": pdf_export["id"]}, storage_updates)
                        created.append("document_export:pdf_file_restored")

        delivery = await document_deliveries.find_one(
            {
                "agency_id": agency["id"],
                "rendered_document_id": document["id"],
                "recipient_email": "anna.client@example.com",
                "subject": "Demo document delivery",
            }
        )
        if delivery is None:
            delivery = await document_deliveries.insert_one(
                DocumentDelivery(
                    agency_id=agency["id"],
                    rendered_document_id=document["id"],
                    export_id=export["id"],
                    delivery_type="email",
                    status="sent",
                    recipient_email="anna.client@example.com",
                    recipient_name="Anna Client",
                    subject="Demo document delivery",
                    message_text="Demo dev-console delivery for a stored rendered document snapshot.",
                    sent_by_user_id=owner["id"],
                    sent_at=datetime.now(timezone.utc),
                    provider="dev_console",
                    provider_message_id="seed:dev-console-document-delivery",
                    processing_state="completed",
                    attempt_count=1,
                    last_attempt_at=datetime.now(timezone.utc),
                    retry_status="none",
                    client_visible=True,
                ).model_dump(mode="json")
            )
            await document_delivery_attempts.insert_one(
                DocumentDeliveryAttempt(
                    agency_id=agency["id"],
                    delivery_id=delivery["id"],
                    rendered_document_id=document["id"],
                    export_id=export["id"],
                    attempt_number=1,
                    status="sent",
                    provider="dev_console",
                    provider_message_id="seed:dev-console-document-delivery",
                    started_at=delivery["sent_at"],
                    completed_at=delivery["sent_at"],
                ).model_dump(mode="json")
            )
            await document_timeline.insert_one(
                DocumentTimelineEvent(
                    agency_id=agency["id"],
                    rendered_document_id=document["id"],
                    actor_user_id=owner["id"],
                    event_type="document_delivery.seeded",
                    title="Seeded dev-console delivery",
                    summary="anna.client@example.com",
                ).model_dump(mode="json")
            )
            created.append("document_delivery:dev_console")
        existing_attempt = await document_delivery_attempts.find_one({"agency_id": agency["id"], "delivery_id": delivery["id"], "attempt_number": 1})
        if existing_attempt is None:
            sent_at = delivery.get("sent_at") or datetime.now(timezone.utc)
            await document_delivery_attempts.insert_one(
                DocumentDeliveryAttempt(
                    agency_id=agency["id"],
                    delivery_id=delivery["id"],
                    rendered_document_id=document["id"],
                    export_id=export["id"],
                    attempt_number=1,
                    status="sent" if delivery.get("status") == "sent" else "failed",
                    provider=delivery.get("provider") or "dev_console",
                    provider_message_id=delivery.get("provider_message_id"),
                    error_message=delivery.get("error_message"),
                    started_at=sent_at,
                    completed_at=sent_at,
                ).model_dump(mode="json")
            )
            created.append("document_delivery_attempt:seed")

    await ensure_document_export_delivery_examples()

    async def ensure_portal_action_examples() -> None:
        portal_request = await requests.find_one({"agency_id": agency["id"], "request_reference": "REQ-PORTAL-DEMO-0001"})
        if portal_request is None:
            portal_request_model = TravelRequest(
                agency_id=agency["id"],
                client_id=individual_client["id"],
                created_by_user_id=owner["id"],
                request_reference="REQ-PORTAL-DEMO-0001",
                title="Portal submitted Vienna assistance inquiry",
                status="new",
                priority="normal",
                source="client_portal",
                requested_departure_date=date.today(),
                route_summary="Vienna to Amsterdam one-way",
                service_summary="Wheelchair assistance; aisle seat preference",
                passenger_count=1,
                service_count=2,
                client_notes="Submitted from the demo client portal.",
                client_visible_notes="Your request was received and is waiting for agency review.",
            )
            portal_request = await requests.insert_one(portal_request_model.model_dump(mode="json"))
            relationship = await relationships.find_one({"agency_id": agency["id"], "client_id": individual_client["id"], "passenger_id": anna_passenger["id"]})
            await request_passengers.insert_one(
                RequestPassenger(
                    agency_id=agency["id"],
                    request_id=portal_request["id"],
                    passenger_id=anna_passenger["id"],
                    client_passenger_relationship_id=relationship["id"] if relationship else None,
                    is_primary_traveler=True,
                    snapshot_display_name=anna_passenger["display_name"],
                    snapshot_date_of_birth=anna_passenger["date_of_birth"],
                    snapshot_passenger_type=anna_passenger["passenger_type"],
                ).model_dump(mode="json")
            )
            for service_name in ["Wheelchair assistance", "Aisle seat preference"]:
                await requested_services.insert_one(
                    RequestedService(
                        agency_id=agency["id"],
                        request_id=portal_request["id"],
                        service_code="PORTAL",
                        service_name=service_name,
                        service_category="portal_request",
                        details=service_name,
                        client_visible_summary=service_name,
                    ).model_dump(mode="json")
                )
            await request_messages.insert_one(
                RequestMessage(
                    agency_id=agency["id"],
                    request_id=portal_request["id"],
                    sender_type="client",
                    visibility="client_visible",
                    message_text="Please confirm if wheelchair assistance is available.",
                ).model_dump(mode="json")
            )
            await request_tasks.insert_one(
                RequestTask(
                    agency_id=agency["id"],
                    request_id=portal_request["id"],
                    title="Review portal-submitted request",
                    description="Seeded portal action example for staff review.",
                    visibility="internal",
                ).model_dump(mode="json")
            )
            await request_timeline.insert_one(
                RequestTimelineEvent(
                    agency_id=agency["id"],
                    request_id=portal_request["id"],
                    event_type="portal.request_submitted",
                    title="Request submitted",
                    summary="Client submitted this request through the portal.",
                    visibility="client_visible",
                ).model_dump(mode="json")
            )
            created.append("portal_request")

        portal_request_action = await portal_action_events.find_one({"agency_id": agency["id"], "source_entity_id": portal_request["id"], "action_type": "request_submitted"})
        if portal_request_action is None:
            portal_mapping = await portal_mappings.find_one({"agency_id": agency["id"], "user_email": "anna.client@example.com"})
            await portal_action_events.insert_one(
                PortalActionEvent(
                    agency_id=agency["id"],
                    client_id=individual_client["id"],
                    portal_account_id=portal_mapping["id"] if portal_mapping else None,
                    action_type="request_submitted",
                    source_entity_type="request",
                    source_entity_id=portal_request["id"],
                    summary="Submitted request REQ-PORTAL-DEMO-0001.",
                    payload={"request_reference": portal_request["request_reference"], "seeded": True},
                ).model_dump(mode="json")
            )
            created.append("portal_action:request_submitted")

        document = await rendered_documents.find_one({"agency_id": agency["id"], "client_id": organization_client["id"], "client_visible": True})
        if document:
            existing_ack = await document_acknowledgements.find_one({"agency_id": agency["id"], "rendered_document_id": document["id"], "client_id": organization_client["id"]})
            portal_mapping = await portal_mappings.find_one({"agency_id": agency["id"], "user_email": "travel@orbitex.example.com"})
            if existing_ack is None:
                await document_acknowledgements.insert_one(
                    DocumentAcknowledgement(
                        agency_id=agency["id"],
                        rendered_document_id=document["id"],
                        client_id=organization_client["id"],
                        portal_account_id=portal_mapping["id"] if portal_mapping else None,
                        acknowledgement_type="acknowledged",
                        message="Seeded portal acknowledgement example.",
                    ).model_dump(mode="json")
                )
                await document_timeline.insert_one(
                    DocumentTimelineEvent(
                        agency_id=agency["id"],
                        rendered_document_id=document["id"],
                        event_type="portal.document_acknowledged",
                        title="Document acknowledged",
                        summary="Seeded portal acknowledgement example.",
                        visibility="client_visible",
                    ).model_dump(mode="json")
                )
                created.append("document_acknowledgement")
            ack_action = await portal_action_events.find_one({"agency_id": agency["id"], "source_entity_id": document["id"], "action_type": "document_acknowledged"})
            if ack_action is None:
                await portal_action_events.insert_one(
                    PortalActionEvent(
                        agency_id=agency["id"],
                        client_id=organization_client["id"],
                        portal_account_id=portal_mapping["id"] if portal_mapping else None,
                        action_type="document_acknowledged",
                        source_entity_type="document",
                        source_entity_id=document["id"],
                        summary=f"Acknowledged document {document['title']}.",
                        payload={"document_type": document["document_type"], "seeded": True},
                    ).model_dump(mode="json")
                )
                created.append("portal_action:document_acknowledged")

    await ensure_portal_action_examples()

    async def ensure_refund_exchange_examples() -> None:
        offer_booking = await bookings.find_one({"agency_id": agency["id"], "booking_reference": "BKG-DEMO-0001"})
        if offer_booking is None:
            return

        refund_ticket = await ticket_records.find_one({"agency_id": agency["id"], "booking_id": offer_booking["id"], "ticket_number": "2571234567890"})
        offer_invoice = await invoices.find_one({"agency_id": agency["id"], "invoice_number": "INV-DEMO-0001"})
        offer_payment = await payment_records.find_one({"agency_id": agency["id"], "invoice_id": offer_invoice["id"]}) if offer_invoice else None

        manual_booking = await bookings.find_one({"agency_id": agency["id"], "booking_reference": "BKG-DEMO-0002"})
        manual_ticket = await ticket_records.find_one({"agency_id": agency["id"], "booking_id": manual_booking["id"]}) if manual_booking else None

        refund_case = await refund_exchange_cases.find_one({"agency_id": agency["id"], "case_reference": "REC-SEED-0001"})
        if refund_case is None:
            refund_case = await refund_exchange_cases.insert_one(
                RefundExchangeCase(
                    agency_id=agency["id"],
                    case_reference="REC-SEED-0001",
                    case_type="refund",
                    client_id=offer_booking["client_id"],
                    booking_id=offer_booking["id"],
                    request_id=offer_booking.get("request_id"),
                    offer_id=offer_booking.get("offer_id"),
                    created_by_user_id=owner["id"],
                    assigned_user_id=owner["id"],
                    status="review_needed",
                    priority="high",
                    reason_category="wrong_name",
                    client_reason_text="Customer reported incorrect last name was entered in the ticketing output.",
                    internal_summary="Customer noticed last-name mismatch in issued ticket.",
                    client_visible_summary="We are checking this as a name correction request.",
                    supplier_reference="DEMO-SUP-REF-REFUND",
                    estimated_refund_amount=120,
                    estimated_penalty_amount=25,
                    estimated_exchange_difference_amount=0,
                    estimated_agency_fee_amount=15,
                    estimated_total_due_from_client=0,
                    estimated_total_due_to_client=95,
                    final_refund_amount=None,
                    final_penalty_amount=None,
                    currency="EUR",
                    client_visible=True,
                ).model_dump(mode="json")
            )
            created.append("refund_exchange_case:refund")

            if refund_ticket:
                await refund_exchange_items.insert_one(
                    RefundExchangeItem(
                        agency_id=agency["id"],
                        case_id=refund_case["id"],
                        item_type="ticket",
                        item_id=refund_ticket["id"],
                        passenger_id=refund_ticket.get("passenger_id"),
                        ticket_id=refund_ticket["id"],
                        description=f"Ticket {refund_ticket['ticket_number']}",
                        status="not_eligible",
                        estimated_amount=120,
                        currency="EUR",
                    ).model_dump(mode="json")
                )
                created.append("refund_exchange_item:ticket")

            if offer_invoice:
                await refund_exchange_items.insert_one(
                    RefundExchangeItem(
                        agency_id=agency["id"],
                        case_id=refund_case["id"],
                        item_type="invoice",
                        item_id=offer_invoice["id"],
                        invoice_id=offer_invoice["id"],
                        description=f"Invoice {offer_invoice['invoice_number']}",
                        status="pending",
                        estimated_amount=470,
                        currency="EUR",
                    ).model_dump(mode="json")
                )
                created.append("refund_exchange_item:invoice")

            if offer_payment:
                await refund_exchange_items.insert_one(
                    RefundExchangeItem(
                        agency_id=agency["id"],
                        case_id=refund_case["id"],
                        item_type="payment",
                        item_id=offer_payment["id"],
                        payment_id=offer_payment["id"],
                        description=f"Payment {offer_payment.get('external_reference', offer_payment['id'])}",
                        status="pending",
                        estimated_amount=470,
                        currency="EUR",
                    ).model_dump(mode="json")
                )
                created.append("refund_exchange_item:payment")

            for line_payload in [
                {
                    "line_type": "refundable_fare",
                    "description": "Refundable fare baseline",
                    "amount": 370,
                    "direction": "due_to_client",
                },
                {
                    "line_type": "airline_penalty",
                    "description": "Cancellation fee estimate",
                    "amount": 25,
                    "direction": "due_from_client",
                },
                {
                    "line_type": "agency_fee",
                    "description": "Agency handling fee",
                    "amount": 15,
                    "direction": "neutral",
                },
            ]:
                await refund_exchange_financial_lines.insert_one(
                    RefundExchangeFinancialLine(
                        agency_id=agency["id"],
                        case_id=refund_case["id"],
                        client_visible=True,
                        supplier_pass_through=False,
                        **line_payload,
                    ).model_dump(mode="json")
                )
            created.append("refund_exchange_financial_line:refund")

            await refund_exchange_messages.insert_one(
                RefundExchangeMessage(
                    agency_id=agency["id"],
                    case_id=refund_case["id"],
                    sender_type="staff",
                    visibility="internal",
                    message_text="Captured manual notes: first step is booking check with supplier.",
                ).model_dump(mode="json")
            )
            await refund_exchange_messages.insert_one(
                RefundExchangeMessage(
                    agency_id=agency["id"],
                    case_id=refund_case["id"],
                    sender_type="staff",
                    visibility="client_visible",
                    message_text="We are reviewing your refund request. We will update you once we confirm the exact amount.",
                ).model_dump(mode="json")
            )
            created.extend(["refund_exchange_message:internal", "refund_exchange_message:client_visible"])

            await refund_exchange_timeline.insert_one(
                RefundExchangeTimelineEvent(
                    agency_id=agency["id"],
                    case_id=refund_case["id"],
                    event_type="case.created",
                    actor_user_id=owner["id"],
                    title="Case created from booking",
                    summary="Manual review case created for ticket name correction.",
                    visibility="internal",
                ).model_dump(mode="json")
            )
            await refund_exchange_timeline.insert_one(
                RefundExchangeTimelineEvent(
                    agency_id=agency["id"],
                    case_id=refund_case["id"],
                    event_type="case.timeline.client_update",
                    actor_user_id=owner["id"],
                    title="Client visible summary added",
                    summary="Client-visible summary added for the request.",
                    visibility="client_visible",
                ).model_dump(mode="json")
            )
            created.append("refund_exchange_timeline:seed")

            await booking_timeline.insert_one(
                BookingTimelineEvent(
                    agency_id=agency["id"],
                    booking_id=offer_booking["id"],
                    actor_user_id=owner["id"],
                    event_type="refund_exchange.case_linked",
                    title="Refund/exchange case linked to booking",
                    summary=f"case {refund_case['case_reference']}",
                    visibility="internal",
                ).model_dump(mode="json")
            )

        exchange_case = await refund_exchange_cases.find_one({"agency_id": agency["id"], "case_reference": "REC-SEED-0002"})
        if exchange_case is None and manual_booking:
            exchange_case = await refund_exchange_cases.insert_one(
                RefundExchangeCase(
                    agency_id=agency["id"],
                    case_reference="REC-SEED-0002",
                    case_type="exchange",
                    client_id=manual_booking["client_id"],
                    booking_id=manual_booking["id"],
                    created_by_user_id=owner["id"],
                    assigned_user_id=owner["id"],
                    status="client_requested",
                    priority="normal",
                    reason_category="schedule_change",
                    client_reason_text="Customer asked to move first segment to alternative date.",
                    internal_summary="Need schedule change handling and fare difference update.",
                    client_visible_summary="We are handling your schedule change request.",
                    estimated_exchange_difference_amount=55,
                    estimated_refund_amount=0,
                    estimated_penalty_amount=10,
                    estimated_agency_fee_amount=20,
                    estimated_total_due_from_client=85,
                    estimated_total_due_to_client=0,
                    currency="EUR",
                    client_visible=True,
                ).model_dump(mode="json")
            )
            created.append("refund_exchange_case:exchange")

            if manual_ticket:
                await refund_exchange_items.insert_one(
                    RefundExchangeItem(
                        agency_id=agency["id"],
                        case_id=exchange_case["id"],
                        item_type="ticket",
                        item_id=manual_ticket["id"],
                        ticket_id=manual_ticket["id"],
                        description=f"Ticket {manual_ticket['ticket_number']}",
                        status="submitted",
                        estimated_amount=185,
                        currency="EUR",
                    ).model_dump(mode="json")
                )
                created.append("refund_exchange_item:exchange_ticket")

            await refund_exchange_items.insert_one(
                RefundExchangeItem(
                    agency_id=agency["id"],
                    case_id=exchange_case["id"],
                    item_type="other",
                    description="Requested new schedule on manual booking",
                    status="pending",
                    estimated_amount=85,
                    currency="EUR",
                ).model_dump(mode="json")
            )
            created.append("refund_exchange_item:exchange_other")

            await refund_exchange_financial_lines.insert_one(
                RefundExchangeFinancialLine(
                    agency_id=agency["id"],
                    case_id=exchange_case["id"],
                    line_type="exchange_fare_difference",
                    description="Fare difference estimate for reissue",
                    amount=55,
                    currency="EUR",
                    direction="due_from_client",
                    client_visible=True,
                    supplier_pass_through=False,
                ).model_dump(mode="json")
            )
            await refund_exchange_financial_lines.insert_one(
                RefundExchangeFinancialLine(
                    agency_id=agency["id"],
                    case_id=exchange_case["id"],
                    line_type="airline_penalty",
                    description="Fee estimate for date change request",
                    amount=10,
                    currency="EUR",
                    direction="due_from_client",
                    client_visible=True,
                    supplier_pass_through=False,
                ).model_dump(mode="json")
            )
            created.extend(["refund_exchange_financial_line:exchange", "refund_exchange_financial_line:exchange_penalty"])

            await refund_exchange_messages.insert_one(
                RefundExchangeMessage(
                    agency_id=agency["id"],
                    case_id=exchange_case["id"],
                    sender_type="staff",
                    visibility="client_visible",
                    message_text="Schedule change request is being prepared. We will confirm fare impact.",
                ).model_dump(mode="json")
            )
            created.append("refund_exchange_message:exchange_client")

            await refund_exchange_timeline.insert_one(
                RefundExchangeTimelineEvent(
                    agency_id=agency["id"],
                    case_id=exchange_case["id"],
                    event_type="case.created",
                    actor_user_id=owner["id"],
                    title="Case created from booking",
                    summary="Exchange case seeded for schedule change scenario.",
                    visibility="internal",
                ).model_dump(mode="json")
            )
            created.append("refund_exchange_timeline:exchange")

    await ensure_refund_exchange_examples()

    if created:
        event = AuditEvent(
            actor_user_id=owner["id"],
            event_type="seed.core_data",
            entity_type="platform",
            entity_id="core",
            summary="Seeded demo platform, agency, membership, CRM, and reference records.",
            metadata={"created": created},
        )
        await audits.insert_one(event.model_dump(mode="json"))

    return {
        "created": created,
        "demo_user_email": DEMO_OWNER_EMAIL,
        "demo_agency_slug": DEMO_AGENCY_SLUG,
    }
