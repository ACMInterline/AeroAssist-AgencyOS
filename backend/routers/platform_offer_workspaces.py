from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OfferWorkspaceV2Create, OfferWorkspaceV2Update
from services.offer_workspace_service import PHASE_LABEL, OfferWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-workspaces", tags=["platform-offer-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_offer_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    validity: date | None = Query(default=None),
    client_id: str | None = Query(default=None),
    destination: str | None = Query(default=None),
    min_price: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
    assigned_agent: str | None = Query(default=None),
    trip_workspace_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OfferWorkspaceService(db).platform_response(
        agency_id=agency_id,
        status=status_filter,
        validity=validity,
        client_id=client_id,
        destination=destination,
        min_price=min_price,
        max_price=max_price,
        assigned_agent=assigned_agent,
        trip_workspace_id=trip_workspace_id,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_offer_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OfferWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_offer_workspace(
    payload: OfferWorkspaceV2Create,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OfferWorkspaceService(db).create_offer(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{offer_workspace_id}")
async def get_platform_offer_workspace(
    offer_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OfferWorkspaceService(db)
    try:
        offer_workspace = await service.get_platform_offer(offer_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "offer_workspace": offer_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{offer_workspace_id}")
async def update_platform_offer_workspace(
    offer_workspace_id: str,
    payload: OfferWorkspaceV2Update,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OfferWorkspaceService(db).update_offer(offer_workspace_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{offer_workspace_id}")
async def delete_platform_offer_workspace(
    offer_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OfferWorkspaceService(db).delete_offer(offer_workspace_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
