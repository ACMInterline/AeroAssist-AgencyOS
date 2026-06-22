from fastapi import APIRouter, Depends

from auth import get_current_user, require_platform_role
from database import Database, get_database

router = APIRouter(prefix="/api/platform", tags=["platform"])


@router.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "service": "AeroAssist AgencyOS API",
        "phase": "phase_10_auth_invitations_foundation",
    }


@router.get("/summary")
async def summary(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin", "platform_support"])),
    db: Database = Depends(get_database),
) -> dict:
    return {
        "current_user": user,
        "counts": {
            "agencies": await db.collection("agencies").count(),
            "workspaces": await db.collection("agency_workspaces").count(),
            "staff_memberships": await db.collection("agency_staff_memberships").count(),
            "clients": await db.collection("client_profiles").count(),
            "passengers": await db.collection("passenger_profiles").count(),
            "relationships": await db.collection("client_passenger_relationships").count(),
            "requests": await db.collection("travel_requests").count(),
            "request_tasks": await db.collection("request_tasks").count(),
            "offers": await db.collection("offers").count(),
            "offer_routes": await db.collection("offer_route_alternatives").count(),
            "offer_fare_options": await db.collection("offer_fare_options").count(),
            "bookings": await db.collection("bookings").count(),
            "tickets": await db.collection("ticket_records").count(),
            "emds": await db.collection("emd_records").count(),
            "invoices": await db.collection("invoices").count(),
            "payments": await db.collection("payment_records").count(),
            "portal_mappings": await db.collection("portal_access_mappings").count(),
            "airlines": await db.collection("airline_profiles").count(),
            "airline_knowledge": await db.collection("airline_knowledge_items").count(),
            "airline_procedures": await db.collection("airline_procedures").count(),
            "airline_emd_notes": await db.collection("airline_emd_rule_notes").count(),
            "airline_overrides": await db.collection("agency_airline_overrides").count(),
            "document_templates": await db.collection("document_templates").count(),
            "rendered_documents": await db.collection("rendered_documents").count(),
            "reference_records": await db.collection("global_reference_records").count(),
            "audit_events": await db.collection("audit_events").count(),
        },
        "implemented_layers": [
            "AeroAssist Global / Platform Owner",
            "Agency Workspace foundation",
            "CRM client/passenger relationship foundation",
            "Request intake, messages, tasks, and timeline foundation",
            "Manual offer builder foundation",
            "Booking, ticket, EMD, invoice, and payment tracking foundation",
            "Airline Intelligence foundation",
            "Branded HTML document output foundation",
            "Read-only client portal visibility foundation",
            "Persistence and tenant hardening foundation",
            "Authentication and invitation foundation",
        ],
        "not_yet_implemented": [
            "Client request submission and editable portal workflows",
            "Offer acceptance or rejection workflows",
            "Payment gateway integration",
            "PDF export and public document links",
        ],
    }


@router.get("/audit-events")
async def audit_events(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin", "platform_support"])),
    db: Database = Depends(get_database),
) -> dict:
    return {"items": await db.collection("audit_events").find_many()}


@router.get("/whoami")
async def whoami(user: dict = Depends(get_current_user)) -> dict:
    return {"user": user}
