from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_to_booking_handoff_service import PHASE_LABEL, OfferToBookingHandoffService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/booking-handoffs", tags=["platform-offer-booking-handoffs"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def list_platform_booking_handoffs(
    agency_id: str | None = None,
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
    await require_platform_read(user)
    return await OfferToBookingHandoffService(db).platform_dashboard(
        agency_id=agency_id,
        status=status_filter,
        acceptance_id=acceptance_id,
        booking_readiness_package_id=booking_readiness_package_id,
        trip_id=trip_id,
        offer_workspace_id=offer_workspace_id,
        booking_workspace_id=booking_workspace_id,
        booking_mode=booking_mode,
    )


@router.get("/summary")
async def summarize_platform_booking_handoffs(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OfferToBookingHandoffService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id=agency_id), "platform_read_only_diagnostics": True, "metadata_only": True, **service.safety_flags()}


@router.get("/checks")
async def list_platform_booking_handoff_checks(
    agency_id: str | None = None,
    handoff_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OfferToBookingHandoffService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_checks(agency_id=agency_id, handoff_id=handoff_id, status=status_filter, category=category), "platform_read_only_diagnostics": True, "metadata_only": True, **service.safety_flags()}


@router.get("/mappings")
async def list_platform_booking_handoff_mappings(
    agency_id: str | None = None,
    handoff_id: str | None = None,
    mapping_type: str | None = None,
    booking_workspace_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OfferToBookingHandoffService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_mappings(agency_id=agency_id, handoff_id=handoff_id, mapping_type=mapping_type, booking_workspace_id=booking_workspace_id), "platform_read_only_diagnostics": True, "metadata_only": True, **service.safety_flags()}


@router.get("/instructions")
async def list_platform_booking_handoff_instructions(
    agency_id: str | None = None,
    handoff_id: str | None = None,
    instruction_status: str | None = None,
    booking_mode: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OfferToBookingHandoffService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_instructions(agency_id=agency_id, handoff_id=handoff_id, instruction_status=instruction_status, booking_mode=booking_mode), "platform_read_only_diagnostics": True, "metadata_only": True, **service.safety_flags()}


@router.get("/{handoff_id}")
async def get_platform_booking_handoff(
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"phase": PHASE_LABEL, "handoff": await OfferToBookingHandoffService(db).get_handoff(handoff_id), "platform_read_only_diagnostics": True, "metadata_only": True}
