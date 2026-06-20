from fastapi import APIRouter, Depends

from auth import get_current_user, require_platform_role
from database import Database, get_database

router = APIRouter(prefix="/api/platform", tags=["platform"])


@router.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "service": "AeroAssist AgencyOS API",
        "phase": "phase_1_foundation",
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
            "reference_records": await db.collection("global_reference_records").count(),
            "audit_events": await db.collection("audit_events").count(),
        },
        "implemented_layers": [
            "AeroAssist Global / Platform Owner",
            "Agency Workspace foundation",
        ],
        "not_yet_implemented": [
            "CRM",
            "Requests",
            "Offers",
            "Airline Intelligence UI",
            "Client portal workflows",
            "Documents and payments",
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
