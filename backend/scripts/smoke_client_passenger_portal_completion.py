#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import base64
import inspect
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Awaitable, Callable


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

STORAGE_ROOT = Path(tempfile.mkdtemp(prefix="aeroassist-portal-smoke-"))
os.environ["AEROASSIST_DB_MODE"] = "memory"
os.environ["APP_ENV"] = "development"
os.environ["DOCUMENT_EXPORT_STORAGE_DIR"] = str(STORAGE_ROOT)
os.environ["DEMO_AUTH_ENABLED"] = "false"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["SEED_ENDPOINT_ENABLED"] = "false"
os.environ["LOG_LEVEL"] = "CRITICAL"

from build_phase import CURRENT_BUILD_PHASE
from database import Database
from models import RequestV4Payload
from phase_assertions import assert_application_phase_at_least
from routers.portal import submit_offer_decision
from server import app
from services.operational_collaboration_service import (
    OperationalCollaborationService,
)
from services.portal_projection_service import (
    PortalProjectionError,
    PortalProjectionService,
)
from services.request_v4_service import create_request_v4


AGENCY_A = "portal-completion-agency-a"
AGENCY_B = "portal-completion-agency-b"
CLIENT_A = "portal-completion-client-a"
CLIENT_B = "portal-completion-client-b"
PASSENGER_A = "portal-completion-passenger-a"
PASSENGER_A2 = "portal-completion-passenger-a2"
PASSENGER_B = "portal-completion-passenger-b"
TRIP_A = "portal-completion-trip-a"
TRIP_B = "portal-completion-trip-b"
BOOKING_A = "portal-completion-booking-a"
MINIMUM_PHASE = "phase_59_0_product_experience_recovery"


class Checks:
    def __init__(self) -> None:
        self.items: list[str] = []

    def check(self, name: str, condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(f"{name}: {message}")
        self.items.append(name)


async def insert(db: Database, collection: str, item: dict[str, Any]) -> dict[str, Any]:
    return await db.collection(collection).insert_one(item)


async def expect_portal_error(
    operation: Callable[[], Awaitable[Any]], code: str
) -> PortalProjectionError:
    try:
        await operation()
    except PortalProjectionError as exc:
        if exc.code != code:
            raise AssertionError(f"Expected {code}, received {exc.code}.") from exc
        return exc
    raise AssertionError(f"Expected PortalProjectionError {code}.")


def request_payload() -> RequestV4Payload:
    return RequestV4Payload.model_validate(
        {
            "request_version": 4,
            "contact": {
                "first_name": "Casey",
                "last_name": "Client",
                "email": "casey.portal@example.com",
            },
            "trip": {
                "trip_label": "Portal draft journey",
                "trip_purpose": "leisure",
                "quote_mode": "one_way",
                "preferred_cabin": "Y",
            },
            "itinerary_segments": [
                {
                    "segment_local_id": "segment-1",
                    "segment_order": 1,
                    "origin_label": "Sofia",
                    "origin_iata": "SOF",
                    "destination_label": "London Heathrow",
                    "destination_iata": "LHR",
                    "departure_date": "2031-06-10",
                    "departure_time": "09:30",
                    "arrival_date": "2031-06-10",
                    "arrival_time": "11:00",
                    "cabin": "Y",
                }
            ],
            "passengers": [
                {
                    "passenger_local_id": "traveler-1",
                    "identity_status": "unresolved",
                    "passenger_type_code": "ADT",
                    "passenger_type_label": "Adult",
                    "first_name": "Casey",
                    "last_name": "Client",
                    "date_of_birth": "1990-03-12",
                    "selected_services": [],
                    "service_details": {},
                }
            ],
            "pets": [],
            "special_items": [],
            "request_level_notes": "Portal request draft.",
            "admin_metadata": {
                "source": "portal_client",
                "status": "draft",
                "priority": "normal",
            },
        }
    )


def client_context() -> dict[str, Any]:
    return {
        "account": {
            "id": "portal-completion-client-mapping",
            "agency_id": AGENCY_A,
            "auth_identity_id": "portal-completion-client-identity",
            "client_profile_id": CLIENT_A,
        },
        "identity": {
            "id": "portal-completion-client-identity",
            "email": "casey.portal@example.com",
        },
        "subject_type": "client",
        "client": {"id": CLIENT_A, "display_name": "Casey Client"},
        "agency": {"id": AGENCY_A, "name": "Portal Completion Agency"},
    }


def passenger_context() -> dict[str, Any]:
    return {
        "account": {
            "id": "portal-completion-passenger-mapping",
            "agency_id": AGENCY_A,
            "auth_identity_id": "portal-completion-passenger-identity",
            "passenger_profile_id": PASSENGER_A,
        },
        "identity": {
            "id": "portal-completion-passenger-identity",
            "email": "parker.portal@example.com",
        },
        "subject_type": "passenger",
        "passenger": {
            "id": PASSENGER_A,
            "display_name": "Parker Passenger",
        },
        "agency": {"id": AGENCY_A, "name": "Portal Completion Agency"},
    }


async def seed(db: Database) -> dict[str, Any]:
    for agency_id in (AGENCY_A, AGENCY_B):
        await insert(
            db,
            "agencies",
            {
                "id": agency_id,
                "name": agency_id.replace("-", " ").title(),
                "slug": agency_id,
                "status": "active",
            },
        )
        await insert(
            db,
            "agency_workspaces",
            {
                "id": f"{agency_id}-workspace",
                "agency_id": agency_id,
                "name": "Operations",
                "status": "active",
            },
        )

    for identity_id, identity_type, email in (
        (
            "portal-completion-client-identity",
            "client_portal",
            "casey.portal@example.com",
        ),
        (
            "portal-completion-passenger-identity",
            "passenger_portal",
            "parker.portal@example.com",
        ),
        (
            "portal-completion-passenger-two-identity",
            "passenger_portal",
            "second.portal@example.com",
        ),
        (
            "portal-completion-agent-identity",
            "agency_staff",
            "agent.portal@example.com",
        ),
    ):
        await insert(
            db,
            "auth_identities",
            {
                "id": identity_id,
                "identity_type": identity_type,
                "email": email,
                "normalized_email": email,
                "status": "active",
            },
        )

    await insert(
        db,
        "platform_users",
        {
            "id": "portal-completion-agent",
            "identity_id": "portal-completion-agent-identity",
            "email": "agent.portal@example.com",
            "full_name": "Portal Completion Agent",
            "status": "active",
        },
    )
    await insert(
        db,
        "agency_staff_memberships",
        {
            "id": "portal-completion-agent-membership",
            "agency_id": AGENCY_A,
            "workspace_id": f"{AGENCY_A}-workspace",
            "user_id": "portal-completion-agent",
            "identity_id": "portal-completion-agent-identity",
            "agency_role": "agency_agent",
            "status": "active",
        },
    )

    await insert(
        db,
        "client_profiles",
        {
            "id": CLIENT_A,
            "agency_id": AGENCY_A,
            "display_name": "Casey Client",
            "primary_email": "casey.portal@example.com",
            "status": "active",
        },
    )
    await insert(
        db,
        "client_profiles",
        {
            "id": CLIENT_B,
            "agency_id": AGENCY_B,
            "display_name": "Other Client",
            "primary_email": "other.portal@example.com",
            "status": "active",
        },
    )
    for passenger_id, agency_id, name in (
        (PASSENGER_A, AGENCY_A, "Parker Passenger"),
        (PASSENGER_A2, AGENCY_A, "Taylor Passenger"),
        (PASSENGER_B, AGENCY_B, "Other Passenger"),
    ):
        await insert(
            db,
            "passenger_profiles",
            {
                "id": passenger_id,
                "agency_id": agency_id,
                "display_name": name,
                "first_name": name.split()[0],
                "last_name": name.split()[-1],
                "passenger_type": "ADT",
                "status": "active",
            },
        )
    for passenger_id, upload_allowed in (
        (PASSENGER_A, True),
        (PASSENGER_A2, False),
    ):
        await insert(
            db,
            "client_passenger_relationships",
            {
                "id": f"relationship-{passenger_id}",
                "agency_id": AGENCY_A,
                "client_id": CLIENT_A,
                "passenger_id": passenger_id,
                "relationship_type": "traveler",
                "can_view": True,
                "can_upload_documents": upload_allowed,
                "status": "active",
            },
        )
    await insert(
        db,
        "portal_access_mappings",
        {
            "id": "portal-completion-client-mapping",
            "agency_id": AGENCY_A,
            "auth_identity_id": "portal-completion-client-identity",
            "subject_type": "client",
            "client_profile_id": CLIENT_A,
            "status": "active",
        },
    )
    await insert(
        db,
        "portal_access_mappings",
        {
            "id": "portal-completion-passenger-mapping",
            "agency_id": AGENCY_A,
            "auth_identity_id": "portal-completion-passenger-identity",
            "subject_type": "passenger",
            "passenger_profile_id": PASSENGER_A,
            "status": "active",
        },
    )
    await insert(
        db,
        "portal_access_mappings",
        {
            "id": "portal-completion-legacy-mapping",
            "agency_id": AGENCY_A,
            "subject_type": "client",
            "client_profile_id": CLIENT_A,
            "user_email": "legacy.portal@example.com",
            "linkage_version": "legacy_email",
            "status": "revoked",
        },
    )

    request_detail = await create_request_v4(
        db,
        AGENCY_A,
        request_payload(),
        "portal-completion-client-identity",
        allow_legacy_ptc=True,
    )
    request = request_detail["request"]

    await insert(
        db,
        "trip_dossiers",
        {
            "id": TRIP_A,
            "agency_id": AGENCY_A,
            "primary_client_id": CLIENT_A,
            "primary_request_id": request["id"],
            "linked_request_ids": [request["id"]],
            "trip_reference": "TRIP-PORTAL-001",
            "trip_title": "London journey",
            "trip_status": "confirmed",
            "journey_type": "one_way",
            "route_summary": "Sofia to London",
        },
    )
    await insert(
        db,
        "trip_dossiers",
        {
            "id": TRIP_B,
            "agency_id": AGENCY_B,
            "primary_client_id": CLIENT_B,
            "trip_reference": "TRIP-OTHER-001",
            "trip_title": "Other journey",
            "trip_status": "confirmed",
        },
    )
    for passenger_id, order in ((PASSENGER_A, 1), (PASSENGER_A2, 2)):
        await insert(
            db,
            "trip_passengers",
            {
                "id": f"trip-passenger-{passenger_id}",
                "agency_id": AGENCY_A,
                "trip_id": TRIP_A,
                "passenger_id": passenger_id,
                "passenger_profile_id": passenger_id,
                "display_name": (
                    "Parker Passenger"
                    if passenger_id == PASSENGER_A
                    else "Taylor Passenger"
                ),
                "passenger_type": "ADT",
                "sort_order": order,
                "status": "active",
            },
        )
    await insert(
        db,
        "trip_segments",
        {
            "id": "portal-completion-trip-segment",
            "agency_id": AGENCY_A,
            "trip_id": TRIP_A,
            "segment_order": 1,
            "origin_airport_code": "SOF",
            "destination_airport_code": "LHR",
            "departure_date": "2031-06-10",
            "marketing_airline_code": "BA",
            "flight_number": "893",
            "segment_status": "confirmed",
        },
    )
    for passenger_id, service_code in (
        (PASSENGER_A, "WCHR"),
        (PASSENGER_A2, "PETC"),
    ):
        await insert(
            db,
            "trip_service_items",
            {
                "id": f"service-{passenger_id}",
                "agency_id": AGENCY_A,
                "trip_id": TRIP_A,
                "passenger_ids": [passenger_id],
                "service_code": service_code,
                "service_label": service_code,
                "status": "requested",
                "notes": "Internal handling note.",
            },
        )

    await insert(
        db,
        "booking_records",
        {
            "id": BOOKING_A,
            "agency_id": AGENCY_A,
            "client_id": CLIENT_A,
            "trip_id": TRIP_A,
            "request_id": request["id"],
            "booking_workspace_id": "portal-completion-booking-workspace",
            "pnr_locator": "AB12CD",
            "booking_status": "confirmed",
            "passenger_ids": [PASSENGER_A, PASSENGER_A2],
            "passengers_json": [
                {
                    "passenger_profile_id": PASSENGER_A,
                    "display_name": "Parker Passenger",
                },
                {
                    "passenger_profile_id": PASSENGER_A2,
                    "display_name": "Taylor Passenger",
                },
            ],
            "segments_json": [
                {
                    "id": "booking-segment-1",
                    "origin": "SOF",
                    "destination": "LHR",
                    "marketing_carrier": "BA",
                }
            ],
            "services_json": [
                {"passenger_id": PASSENGER_A, "service_code": "WCHR"},
                {"passenger_id": PASSENGER_A2, "service_code": "PETC"},
            ],
            "provider_status": "provider_secret",
            "reconciliation_status": "internal_review",
            "warnings_json": [{"message": "Internal document review detail."}],
        },
    )
    for passenger_id, suffix in ((PASSENGER_A, "1"), (PASSENGER_A2, "2")):
        await insert(
            db,
            "ticket_records",
            {
                "id": f"portal-completion-ticket-{suffix}",
                "agency_id": AGENCY_A,
                "booking_record_id": BOOKING_A,
                "trip_id": TRIP_A,
                "passenger_id": passenger_id,
                "ticket_number": f"125000000000{suffix}",
                "issue_status": "issued",
                "currency": "EUR",
                "total_amount": 250,
            },
        )
        await insert(
            db,
            "ticket_coupons",
            {
                "id": f"portal-completion-ticket-coupon-{suffix}",
                "agency_id": AGENCY_A,
                "ticket_record_id": f"portal-completion-ticket-{suffix}",
                "coupon_number": 1,
                "coupon_status": "open_for_use",
                "origin_airport_code": "SOF",
                "destination_airport_code": "LHR",
                "fare_basis": "YPORTAL",
            },
        )
        await insert(
            db,
            "emd_records",
            {
                "id": f"portal-completion-emd-{suffix}",
                "agency_id": AGENCY_A,
                "booking_record_id": BOOKING_A,
                "trip_id": TRIP_A,
                "passenger_id": passenger_id,
                "ticket_record_id": f"portal-completion-ticket-{suffix}",
                "emd_number": f"125900000000{suffix}",
                "issue_status": "issued",
                "service_code": "WCHR" if suffix == "1" else "PETC",
                "service_name": "Assistance" if suffix == "1" else "Pet in cabin",
            },
        )

    for document_id, passenger_id, document_status, customer_visible, internal in (
        (
            "portal-completion-document-a",
            PASSENGER_A,
            "requested",
            True,
            False,
        ),
        (
            "portal-completion-document-a2",
            PASSENGER_A2,
            "verified",
            True,
            False,
        ),
        (
            "portal-completion-document-internal",
            PASSENGER_A,
            "under_review",
            False,
            True,
        ),
    ):
        await insert(
            db,
            "document_workspaces",
            {
                "id": document_id,
                "agency_id": AGENCY_A,
                "passenger_id": passenger_id,
                "trip_workspace_id": TRIP_A,
                "booking_workspace_id": BOOKING_A,
                "document_reference": document_id.upper(),
                "document_title": "Travel document",
                "document_type": "travel_document",
                "document_category": "travel",
                "document_status": document_status,
                "received_status": "requested"
                if document_status == "requested"
                else "received",
                "customer_visible": customer_visible,
                "internal_only": internal,
            },
        )

    await insert(
        db,
        "invoices",
        {
            "id": "portal-completion-invoice",
            "agency_id": AGENCY_A,
            "client_id": CLIENT_A,
            "invoice_number": "INV-PORTAL-001",
            "status": "issued",
            "currency": "EUR",
            "total_amount": 500,
            "due_amount": 300,
            "supplier_cost": 100,
            "internal_notes": "Never project",
        },
    )
    await insert(
        db,
        "invoice_line_items",
        {
            "id": "portal-completion-line",
            "agency_id": AGENCY_A,
            "invoice_id": "portal-completion-invoice",
            "description": "Travel services",
            "quantity": 1,
            "unit_price": 500,
            "line_total": 500,
            "supplier_cost": 100,
        },
    )
    await insert(
        db,
        "payment_records",
        {
            "id": "portal-completion-payment",
            "agency_id": AGENCY_A,
            "client_id": CLIENT_A,
            "invoice_id": "portal-completion-invoice",
            "payment_reference": "PAY-PORTAL-001",
            "status": "received",
            "currency": "EUR",
            "amount": 200,
        },
    )
    await insert(
        db,
        "credit_notes",
        {
            "id": "portal-completion-credit",
            "agency_id": AGENCY_A,
            "client_id": CLIENT_A,
            "credit_note_number": "CR-PORTAL-001",
            "status": "issued",
            "currency": "EUR",
            "total_amount": 25,
        },
    )

    actor = {
        "id": "portal-completion-agent",
        "identity_id": "portal-completion-agent-identity",
        "actor_type": "agency",
        "display_name": "Portal Completion Agent",
    }
    collaboration = OperationalCollaborationService(db)
    await collaboration.ensure_entity_thread(
        agency_id=AGENCY_A,
        entity_type="trip",
        entity_id=TRIP_A,
        subject="London journey",
        actor=actor,
        visibility=["client", "passenger"],
        context_key="portal-completion-trip",
    )
    client_event = await collaboration.record_business_event(
        agency_id=AGENCY_A,
        entity_type="trip",
        entity_id=TRIP_A,
        event_type="approval_requested",
        summary="Please review the journey.",
        actor=actor,
        visibility="client",
        idempotency_key="portal-completion-client-event",
    )
    passenger_event = await collaboration.record_business_event(
        agency_id=AGENCY_A,
        entity_type="ticket",
        entity_id="portal-completion-ticket-1",
        event_type="deadline",
        summary="Travel document due.",
        actor=actor,
        visibility="passenger",
        idempotency_key="portal-completion-passenger-event",
    )
    await insert(
        db,
        "operational_notification_projections",
        {
            "id": "portal-completion-client-notification",
            "agency_id": AGENCY_A,
            "timeline_entry_id": client_event["id"],
            "notification_type": "approval_required",
            "visibility": "client",
            "status": "open",
            "title": "Review journey",
            "summary": "A journey decision needs attention.",
        },
    )
    await insert(
        db,
        "operational_notification_projections",
        {
            "id": "portal-completion-passenger-notification",
            "agency_id": AGENCY_A,
            "timeline_entry_id": passenger_event["id"],
            "notification_type": "deadline",
            "visibility": "passenger",
            "status": "open",
            "title": "Document due",
            "summary": "Your requested travel document is due.",
        },
    )
    return {"request": request}


async def run_service_checks(checks: Checks) -> None:
    db = Database()
    fixture = await seed(db)
    client_service = PortalProjectionService(db)
    passenger_service = PortalProjectionService(db)
    client_ctx = client_context()
    passenger_ctx = passenger_context()

    client_dashboard = await client_service.dashboard(client_ctx)
    checks.check(
        "client_dashboard_sections",
        {
            "upcoming_trips",
            "pending_offers",
            "action_required",
            "outstanding_payments",
            "recent_communications",
            "recent_documents",
            "recent_timeline",
            "travel_credits",
            "service_requests",
            "notifications",
        }.issubset(client_dashboard),
        "Client dashboard is missing canonical operational sections.",
    )
    checks.check(
        "client_dashboard_scope",
        [item["id"] for item in client_dashboard["upcoming_trips"]] == [TRIP_A]
        and client_dashboard["outstanding_payments"]["outstanding_balance"] == 300,
        "Client dashboard did not use the scoped Trip and ledger projections.",
    )
    checks.check(
        "client_finance_redaction",
        "supplier_cost" not in str(client_dashboard)
        and "internal_notes" not in str(client_dashboard),
        "Client dashboard exposed private commercial fields.",
    )

    passenger_dashboard = await passenger_service.dashboard(passenger_ctx)
    checks.check(
        "passenger_dashboard_sections",
        passenger_dashboard["subject_type"] == "passenger"
        and passenger_dashboard["travel_profile"]["id"] == PASSENGER_A
        and passenger_dashboard["outstanding_payments"]["outstanding_balance"] == 0,
        "Passenger dashboard did not use the exact Passenger projection.",
    )
    checks.check(
        "passenger_ticket_scope",
        [item["id"] for item in await passenger_service.list_tickets(passenger_ctx)]
        == ["portal-completion-ticket-1"],
        "Passenger could see another traveler's Ticket.",
    )
    checks.check(
        "passenger_emd_scope",
        [item["id"] for item in await passenger_service.list_emds(passenger_ctx)]
        == ["portal-completion-emd-1"],
        "Passenger could see another traveler's EMD.",
    )
    passenger_documents = await passenger_service.list_documents(passenger_ctx)
    checks.check(
        "passenger_document_scope",
        [item["id"] for item in passenger_documents]
        == ["portal-completion-document-a"],
        "Passenger document scope included another Passenger or internal data.",
    )
    trip_detail = await passenger_service.trip_detail(passenger_ctx, TRIP_A)
    checks.check(
        "shared_trip_subject_filter",
        [item["id"] for item in trip_detail["passengers"]]
        == [f"trip-passenger-{PASSENGER_A}"]
        and [item["id"] for item in trip_detail["services"]]
        == [f"service-{PASSENGER_A}"]
        and "notes" not in trip_detail["services"][0],
        "Shared Trip detail exposed another Passenger's records.",
    )
    booking_detail = await passenger_service.booking_detail(passenger_ctx, BOOKING_A)
    checks.check(
        "booking_embedded_subject_filter",
        len(booking_detail["booking"]["passengers"]) == 1
        and len(booking_detail["booking"]["services"]) == 1,
        "Booking projection did not filter embedded Passenger content.",
    )
    checks.check(
        "booking_internal_fields_redacted",
        "provider_status" not in booking_detail["booking"]
        and "reconciliation_status" not in booking_detail["booking"]
        and booking_detail["booking"]["warnings"][0]["summary"]
        == "Agency review is required.",
        "Booking projection exposed internal provider, reconciliation, or warning data.",
    )
    await expect_portal_error(
        lambda: passenger_service.finance(passenger_ctx),
        "CLIENT_FINANCE_SCOPE_REQUIRED",
    )
    checks.items.append("passenger_finance_denied")
    await expect_portal_error(
        lambda: client_service.trip_detail(client_ctx, TRIP_B),
        "TRIP_NOT_FOUND",
    )
    checks.items.append("cross_agency_trip_denied")

    first_upload = await passenger_service.upload_document(
        passenger_ctx,
        "portal-completion-document-a",
        {
            "file_name": "travel-document.pdf",
            "content_type": "application/pdf",
            "content_base64": base64.b64encode(b"%PDF-1.4 portal version one").decode(
                "ascii"
            ),
        },
    )
    first_version_id = first_upload["versions"][0]["id"]
    await db.collection("document_workspaces").update_one(
        {
            "agency_id": AGENCY_A,
            "id": "portal-completion-document-a",
        },
        {
            "document_status": "requested",
            "received_status": "requested",
        },
    )
    second_upload = await passenger_service.upload_document(
        passenger_ctx,
        "portal-completion-document-a",
        {
            "file_name": "travel-document-v2.pdf",
            "content_type": "application/pdf",
            "content_base64": base64.b64encode(b"%PDF-1.4 portal version two").decode(
                "ascii"
            ),
        },
    )
    checks.check(
        "document_immutable_versions",
        len(second_upload["versions"]) == 2
        and first_version_id in {item["id"] for item in second_upload["versions"]}
        and all(item["immutable"] for item in second_upload["versions"]),
        "Requested document upload did not preserve immutable versions.",
    )
    downloaded = await passenger_service.document_download(
        passenger_ctx,
        "portal-completion-document-a",
        second_upload["versions"][0]["id"],
    )
    checks.check(
        "document_checksum_download",
        downloaded["content"] == b"%PDF-1.4 portal version two",
        "Document download did not return the checksum-verified selected version.",
    )
    await expect_portal_error(
        lambda: passenger_service.upload_document(
            passenger_ctx,
            "portal-completion-document-a2",
            {
                "file_name": "not-requested.pdf",
                "content_type": "application/pdf",
                "content_base64": base64.b64encode(b"blocked").decode("ascii"),
            },
        ),
        "DOCUMENT_NOT_FOUND",
    )
    checks.items.append("other_passenger_upload_denied")
    await db.collection("document_workspaces").update_one(
        {
            "agency_id": AGENCY_A,
            "id": "portal-completion-document-a",
        },
        {
            "document_status": "requested",
            "received_status": "requested",
        },
    )
    await expect_portal_error(
        lambda: passenger_service.upload_document(
            passenger_ctx,
            "portal-completion-document-a",
            {
                "file_name": "mismatched-image.png",
                "content_type": "application/pdf",
                "content_base64": base64.b64encode(b"%PDF-1.4 blocked").decode(
                    "ascii"
                ),
            },
        ),
        "DOCUMENT_TYPE_MISMATCH",
    )
    checks.items.append("document_extension_mime_mismatch_denied")
    await expect_portal_error(
        lambda: passenger_service.upload_document(
            passenger_ctx,
            "portal-completion-document-a",
            {
                "file_name": "disguised-document.pdf",
                "content_type": "application/pdf",
                "content_base64": base64.b64encode(
                    b"<html>not a PDF document</html>"
                ).decode("ascii"),
            },
        ),
        "DOCUMENT_CONTENT_MISMATCH",
    )
    checks.items.append("document_content_signature_mismatch_denied")

    profile = await passenger_service.update_profile(
        passenger_ctx,
        {
            "known_assistance_needs": "Wheelchair support at the airport.",
            "seating_preferences": "Aisle seat",
            "emergency_contact": {
                "name": "Morgan Passenger",
                "relationship": "Family",
                "phone": "+359000000",
            },
        },
    )
    other_profile = await db.collection("passenger_profiles").find_one(
        {"agency_id": AGENCY_A, "id": PASSENGER_A2}
    )
    checks.check(
        "governed_passenger_profile_update",
        profile["seating_preferences"] == "Aisle seat"
        and not other_profile.get("seating_preferences"),
        "Passenger profile update did not remain on the mapped canonical profile.",
    )

    updated_request = await client_service.update_request_draft(
        client_ctx,
        fixture["request"]["id"],
        {
            "title": "Updated portal draft",
            "client_notes": "Please keep the morning departure.",
        },
    )
    checks.check(
        "request_v4_draft_update",
        updated_request["title"] == "Updated portal draft"
        and updated_request["status"] == "draft",
        "Client draft update did not use Request V4.",
    )
    cancelled = await client_service.cancel_request(
        client_ctx,
        fixture["request"]["id"],
        "Travel plans changed.",
    )
    checks.check(
        "request_v4_cancellation",
        cancelled["status"] == "cancelled",
        "Client Request cancellation did not complete canonically.",
    )
    await expect_portal_error(
        lambda: client_service.update_request_draft(
            client_ctx,
            fixture["request"]["id"],
            {"title": "Invalid later edit"},
        ),
        "REQUEST_NOT_EDITABLE",
    )
    checks.items.append("request_invalid_jump_denied")

    timeline = await passenger_service.timeline(passenger_ctx)
    notifications = await passenger_service.notifications(passenger_ctx)
    checks.check(
        "timeline_notification_scope",
        all(item.get("entity_id") != TRIP_A for item in timeline)
        and [item["id"] for item in notifications]
        == ["portal-completion-passenger-notification"],
        "Passenger timeline or notification projection crossed visibility.",
    )
    checks.check(
        "canonical_collaboration_projection",
        len(await passenger_service._threads(passenger_ctx)) == 1
        and len(await client_service._threads(client_ctx)) == 1,
        "Portal did not consume canonical Operational Collaboration.",
    )

    before = {
        name: await db.collection(name).count()
        for name in (
            "portal_access_mappings",
            "auth_identities",
            "portal_action_events",
            "document_acknowledgements",
            "journey_offer_client_decisions",
            "journey_offer_client_interactions",
        )
    }
    analysis = await PortalProjectionService(db).migration_analysis(AGENCY_A)
    after = {
        name: await db.collection(name).count()
        for name in before
    }
    checks.check(
        "portal_migration_dry_run",
        analysis["dry_run"]
        and analysis["writes_performed"] == 0
        and analysis["write_mode_available"] is False
        and analysis["legacy_mapping_ids"] == ["portal-completion-legacy-mapping"]
        and before == after,
        "Portal migration analysis wrote data or lost legacy mapping evidence.",
    )


def run_source_checks(checks: Checks) -> None:
    route_paths = {
        getattr(route, "path", "")
        for route in app.routes
    }
    required_api_routes = {
        "/api/portal/workspace/dashboard",
        "/api/portal/trips",
        "/api/portal/trips/{trip_id}",
        "/api/portal/booking-records",
        "/api/portal/tickets",
        "/api/portal/emds",
        "/api/portal/document-center",
        "/api/portal/timeline",
        "/api/portal/notifications",
        "/api/portal/finance",
        "/api/portal/approvals",
        "/api/portal/profile",
    }
    checks.check(
        "portal_router_registration",
        required_api_routes.issubset(route_paths),
        f"Missing canonical Portal routes: {sorted(required_api_routes - route_paths)}",
    )
    app_text = (ROOT / "frontend/src/routes/RoutedApplication.jsx").read_text()
    layout_text = (ROOT / "frontend/src/layouts/ClientPortalLayout.jsx").read_text()
    required_ui_routes = {
        "/portal/travel-options",
        "/portal/trips",
        "/portal/bookings",
        "/portal/tickets",
        "/portal/emds",
        "/portal/documents",
        "/portal/communications",
        "/portal/timeline",
        "/portal/finance",
        "/portal/actions",
        "/portal/assistance",
    }
    checks.check(
        "portal_frontend_registration",
        all(value in app_text or value in layout_text for value in required_ui_routes),
        "Client or Passenger Portal route registration is incomplete.",
    )
    checks.check(
        "separate_portal_navigation",
        'subjectType === "passenger"' in layout_text
        and "clientLinks" in layout_text
        and "passengerLinks" in layout_text,
        "Client and Passenger navigation are not separated.",
    )
    legacy_source = inspect.getsource(submit_offer_decision)
    checks.check(
        "legacy_offer_mutation_disabled",
        "update_one" not in legacy_source
        and "legacy Offer is read-only" in legacy_source
        and "canonical OfferWorkspace" in legacy_source,
        "Legacy Portal Offer mutation remains a second acceptance path.",
    )
    projection_source = (
        ROOT / "backend/services/portal_projection_service.py"
    ).read_text()
    checks.check(
        "execution_boundaries_disabled",
        '"payment_execution_enabled": False' in projection_source
        and "provider_execution" not in projection_source
        and "payment_gateway" not in projection_source,
        "Portal projection implies payment or provider execution.",
    )
    migration_source = (
        ROOT / "backend/scripts/analyze_portal_completion_migration.py"
    ).read_text()
    checks.check(
        "migration_write_mode_absent",
        "permanently dry-run only" in migration_source
        and "insert_one(" not in migration_source
        and "update_one(" not in migration_source,
        "Portal migration tooling exposes a write path.",
    )
    docs = [
        "docs/architecture/client-portal-contract.md",
        "docs/architecture/passenger-portal-contract.md",
        "docs/architecture/portal-visibility-matrix.md",
        "docs/architecture/portal-dashboard-contract.md",
        "docs/architecture/portal-operational-workspace.md",
        "docs/architecture/portal-approval-contract.md",
    ]
    checks.check(
        "portal_documentation",
        all((ROOT / item).is_file() for item in docs),
        "Portal completion architecture documentation is incomplete.",
    )


async def main() -> int:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="build_phase.CURRENT_BUILD_PHASE",
    )
    checks = Checks()
    try:
        await run_service_checks(checks)
        run_source_checks(checks)
    finally:
        shutil.rmtree(STORAGE_ROOT, ignore_errors=True)
    print(f"Client and Passenger Portal completion smoke passed: {len(checks.items)} checks.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as exc:
        print(f"Client and Passenger Portal completion smoke failed: {exc}", file=sys.stderr)
        raise
