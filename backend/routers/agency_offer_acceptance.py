from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import OfferAcceptanceCreate, OfferDeclineCreate
from services.authorization_service import (
    project_authorized_commercial_fields,
    require_permission,
)
from services.canonical_commercial_lifecycle_service import CommercialLifecycleError
from services.offer_acceptance_service import OfferAcceptanceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-offer-acceptance"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, READ_ROLES)
    require_permission(user, "view_offers")


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, WRITE_ROLES)
    require_permission(user, "edit_offers")


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def lifecycle_conflict(exc: CommercialLifecycleError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": exc.code, "message": str(exc)},
    )


@router.post("/offer-workspaces/{workspace_id}/options/{option_id}/accept", status_code=status.HTTP_201_CREATED)
async def accept_offer_option(
    agency_id: str,
    workspace_id: str,
    option_id: str,
    payload: OfferAcceptanceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = OfferAcceptanceService(db)
    try:
        result = await service.accept_offer_option(
            agency_id, workspace_id, option_id, user, payload
        )
    except CommercialLifecycleError as exc:
        raise lifecycle_conflict(exc) from exc
    if result is None:
        raise not_found("Offer workspace or option not found.")
    return project_authorized_commercial_fields(result, user)


@router.post(
    "/offer-workspaces/{workspace_id}/options/{option_id}/decline",
    status_code=status.HTTP_201_CREATED,
)
async def decline_offer_option(
    agency_id: str,
    workspace_id: str,
    option_id: str,
    payload: OfferDeclineCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        result = await OfferAcceptanceService(db).decline_offer_option(
            agency_id, workspace_id, option_id, user, payload
        )
    except CommercialLifecycleError as exc:
        raise lifecycle_conflict(exc) from exc
    if result is None:
        raise not_found("Offer workspace or option not found.")
    return project_authorized_commercial_fields(result, user)


@router.get("/offer-workspaces/{workspace_id}/acceptance")
async def get_workspace_acceptance(
    agency_id: str,
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferAcceptanceService(db)
    workspace = await db.collection("offer_workspaces").find_one(
        {"agency_id": agency_id, "id": workspace_id}
    )
    if workspace is None:
        raise not_found("Offer workspace not found.")
    return project_authorized_commercial_fields(
        await service.get_workspace_acceptance(agency_id, workspace_id), user
    )


@router.get("/trips/{trip_id}/accepted-offer")
async def get_trip_accepted_offer(
    agency_id: str,
    trip_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferAcceptanceService(db)
    trip = await db.collection("trip_dossiers").find_one(
        {"agency_id": agency_id, "id": trip_id}
    )
    if trip is None:
        raise not_found("Trip not found.")
    return project_authorized_commercial_fields(
        await service.get_trip_accepted_offer(agency_id, trip_id), user
    )


@router.get("/trips/{trip_id}/booking-readiness")
async def get_trip_booking_readiness(
    agency_id: str,
    trip_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferAcceptanceService(db)
    trip = await db.collection("trip_dossiers").find_one(
        {"agency_id": agency_id, "id": trip_id}
    )
    if trip is None:
        raise not_found("Trip not found.")
    return project_authorized_commercial_fields(
        await service.get_booking_readiness_for_trip(agency_id, trip_id), user
    )


@router.post("/offer-acceptances/{acceptance_id}/booking-readiness/rebuild")
async def rebuild_booking_readiness(
    agency_id: str,
    acceptance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = OfferAcceptanceService(db)
    readiness = await service.rebuild_booking_readiness(agency_id, acceptance_id, user)
    if readiness is None:
        raise not_found("Offer acceptance not found.")
    return project_authorized_commercial_fields(
        {"booking_readiness": readiness}, user
    )


@router.post("/offer-acceptances/{acceptance_id}/cancel")
async def cancel_acceptance(
    agency_id: str,
    acceptance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = OfferAcceptanceService(db)
    try:
        result = await service.cancel_acceptance(agency_id, acceptance_id, user)
    except CommercialLifecycleError as exc:
        raise lifecycle_conflict(exc) from exc
    if result is None:
        raise not_found("Offer acceptance not found.")
    return project_authorized_commercial_fields(result, user)
