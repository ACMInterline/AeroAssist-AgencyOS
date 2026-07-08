from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.tenant_service import assert_agency_access, require_any_agency_role
from services.trip_workspace_service import PHASE_LABEL, TripWorkspaceService


router = APIRouter(prefix="/api/agencies/{agency_id}/trip-workspaces", tags=["agency-trip-workspaces"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_trip_workspaces(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    departure_country: str | None = Query(default=None),
    destination_country: str | None = Query(default=None),
    departure_date: date | None = Query(default=None),
    assigned_agent: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    operational_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await TripWorkspaceService(db).agency_response(
        agency_id,
        status=status_filter,
        departure_country=departure_country,
        destination_country=destination_country,
        departure_date=departure_date,
        assigned_agent=assigned_agent,
        priority=priority,
        operational_workspace_id=operational_workspace_id,
    )


@router.get("/summary")
async def summarize_agency_trip_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await TripWorkspaceService(db).agency_summary(agency_id)


@router.get("/{trip_workspace_id}")
async def get_agency_trip_workspace(
    agency_id: str,
    trip_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = TripWorkspaceService(db)
    try:
        trip_workspace = await service.get_agency_trip(agency_id, trip_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "trip_workspace": trip_workspace,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
