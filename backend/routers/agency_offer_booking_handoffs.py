from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OfferBookingHandoffBookingCreateRequest, OfferBookingHandoffBuildRequest
from services.offer_to_booking_handoff_service import PHASE_LABEL, OfferToBookingHandoffError, OfferToBookingHandoffService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/booking-handoffs", tags=["agency-offer-booking-handoffs"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def bad_request(exc: OfferToBookingHandoffError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer-to-booking handoff metadata was not found.")


@router.get("")
async def list_agency_booking_handoffs(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    acceptance_id: str | None = None,
    booking_readiness_package_id: str | None = None,
    trip_id: str | None = None,
    offer_workspace_id: str | None = None,
    booking_workspace_id: str | None = None,
    booking_mode: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OfferToBookingHandoffService(db).agency_dashboard(
        agency_id,
        status=status_filter,
        acceptance_id=acceptance_id,
        booking_readiness_package_id=booking_readiness_package_id,
        trip_id=trip_id,
        offer_workspace_id=offer_workspace_id,
        booking_workspace_id=booking_workspace_id,
        booking_mode=booking_mode,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def build_agency_booking_handoff(
    agency_id: str,
    payload: OfferBookingHandoffBuildRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferToBookingHandoffService(db).build_handoff(payload, user, agency_id=agency_id)
    except OfferToBookingHandoffError as exc:
        raise bad_request(exc)


@router.get("/checks")
async def list_agency_booking_handoff_checks(
    agency_id: str,
    handoff_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferToBookingHandoffService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_checks(agency_id=agency_id, handoff_id=handoff_id, status=status_filter, category=category), "metadata_only": True, **service.safety_flags()}


@router.get("/mappings")
async def list_agency_booking_handoff_mappings(
    agency_id: str,
    handoff_id: str | None = None,
    mapping_type: str | None = None,
    booking_workspace_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferToBookingHandoffService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_mappings(agency_id=agency_id, handoff_id=handoff_id, mapping_type=mapping_type, booking_workspace_id=booking_workspace_id), "metadata_only": True, **service.safety_flags()}


@router.get("/instructions")
async def list_agency_booking_handoff_instructions(
    agency_id: str,
    handoff_id: str | None = None,
    instruction_status: str | None = None,
    booking_mode: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OfferToBookingHandoffService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_instructions(agency_id=agency_id, handoff_id=handoff_id, instruction_status=instruction_status, booking_mode=booking_mode), "metadata_only": True, **service.safety_flags()}


@router.get("/{handoff_id}")
async def get_agency_booking_handoff(
    agency_id: str,
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return {"handoff": await OfferToBookingHandoffService(db).get_handoff(handoff_id, agency_id=agency_id)}
    except OfferToBookingHandoffError:
        raise not_found()


@router.post("/{handoff_id}/assess")
async def assess_agency_booking_handoff(
    agency_id: str,
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferToBookingHandoffService(db).assess_handoff(handoff_id, user, agency_id=agency_id)
    except OfferToBookingHandoffError as exc:
        raise bad_request(exc)


@router.post("/{handoff_id}/create-booking-workspace", status_code=status.HTTP_201_CREATED)
async def create_booking_workspace_from_handoff(
    agency_id: str,
    handoff_id: str,
    payload: OfferBookingHandoffBookingCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferToBookingHandoffService(db).create_booking_workspace(handoff_id, payload, user, agency_id=agency_id)
    except OfferToBookingHandoffError as exc:
        raise bad_request(exc)
