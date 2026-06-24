from fastapi import APIRouter, Depends

from auth import get_current_user, require_platform_role
from config import get_settings
from database import Database, get_database

router = APIRouter(prefix="/api/platform", tags=["platform"])


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "service": "AeroAssist AgencyOS API",
        "app_env": settings.app_env,
        "phase": "phase_23_backup_automation_monitoring_readiness",
    }


@router.get("/summary")
async def summary(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin", "platform_support"])),
    db: Database = Depends(get_database),
) -> dict:
    platform_owner_count = await db.collection("platform_users").count({"global_role": "platform_owner", "status": "active"})
    agency_count = await db.collection("agencies").count()
    workspace_count = await db.collection("agency_workspaces").count()
    staff_membership_count = await db.collection("agency_staff_memberships").count()
    staff_invitation_count = await db.collection("invitations").count({"invitation_type": "agency_staff"})
    return {
        "current_user": user,
        "counts": {
            "agencies": agency_count,
            "workspaces": workspace_count,
            "staff_memberships": staff_membership_count,
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
            "document_exports": await db.collection("document_exports").count(),
            "document_deliveries": await db.collection("document_deliveries").count(),
            "document_delivery_attempts": await db.collection("document_delivery_attempts").count(),
            "reference_records": await db.collection("global_reference_records").count(),
            "audit_events": await db.collection("audit_events").count(),
        },
        "production_onboarding": {
            "platform_owner_exists": platform_owner_count > 0,
            "agency_exists": agency_count > 0,
            "workspace_exists": workspace_count > 0,
            "staff_membership_or_invitation_exists": staff_membership_count > 0 or staff_invitation_count > 0,
            "staff_invitations": staff_invitation_count,
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
            "Controlled client portal actions foundation",
            "Refund and exchange tracking foundation",
            "Printable document export and manual delivery foundation",
            "Document delivery hardening foundation",
            "Production PDF rendering and delivery infrastructure foundation",
            "Production delivery operations and secret resolution foundation",
            "Production configuration hardening foundation",
            "Docker and Hostinger VPS packaging foundation",
            "VPS reverse proxy, TLS, backup, and operations runbook foundation",
            "Hostinger VPS first deployment preparation foundation",
            "Production bootstrap and go-live hardening foundation",
            "Production onboarding and agency setup foundation",
            "Backup automation and lightweight monitoring readiness foundation",
        ],
        "not_yet_implemented": [
            "Document upload workflows",
            "Payment gateway integration",
            "Public document links",
            "Automatic document sending or provider webhooks",
            "Automatic booking, ticketing, or airline execution from portal actions",
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
