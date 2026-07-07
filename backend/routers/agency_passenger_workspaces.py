from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.passenger_workspace_service import PHASE_LABEL, PassengerWorkspaceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/passenger-workspaces", tags=["agency-passenger-workspaces"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_passenger_workspaces(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    nationality: str | None = Query(default=None),
    citizenship: str | None = Query(default=None),
    assistance_profile: str | None = Query(default=None),
    travel_date: date | None = Query(default=None),
    operational_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await PassengerWorkspaceService(db).agency_response(
        agency_id,
        status=status_filter,
        nationality=nationality,
        citizenship=citizenship,
        assistance_profile=assistance_profile,
        travel_date=travel_date,
        operational_workspace_id=operational_workspace_id,
    )


@router.get("/summary")
async def summarize_agency_passenger_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await PassengerWorkspaceService(db).agency_summary(agency_id)


@router.get("/{passenger_workspace_id}")
async def get_agency_passenger_workspace(
    agency_id: str,
    passenger_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = PassengerWorkspaceService(db)
    try:
        passenger_workspace = await service.get_agency_passenger(agency_id, passenger_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "passenger_workspace": passenger_workspace,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
