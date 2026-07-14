from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_distribution_capability_service import (
    PHASE_LABEL,
    AirlineDistributionCapabilityError,
    AirlineDistributionCapabilityService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/distribution-capabilities",
    tags=["agency-airline-distribution-capabilities"],
)

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def bad_request(exc: AirlineDistributionCapabilityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_agency_airline_distribution_capabilities(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    capability_area: str | None = Query(default=None),
    capability_status: str | None = Query(default=None),
    provider_stage: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineDistributionCapabilityService(db).agency_dashboard(
        agency_id,
        airline_code=airline_code,
        channel_code=channel_code,
        capability_area=capability_area,
        capability_status=capability_status,
        provider_stage=provider_stage,
    )


@router.get("/summary")
async def summarize_agency_airline_distribution_capabilities(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineDistributionCapabilityService(db)
    response = await service.agency_dashboard(agency_id, airline_code=airline_code)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": response["summary"], "warnings": response["warnings"], "read_only": True, **service.safety_flags()}


@router.get("/booking-handoff")
async def get_agency_booking_handoff_distribution_capabilities(
    agency_id: str,
    airline_code: list[str] | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineDistributionCapabilityService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "booking_handoff": await service.booking_handoff_summary(agency_id, airline_code, channel_code), "read_only": True, **service.safety_flags()}


@router.get("/{entity_type}")
async def list_agency_airline_distribution_records(
    agency_id: str,
    entity_type: str,
    airline_code: str | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    capability_area: str | None = Query(default=None),
    capability_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineDistributionCapabilityService(db)
    try:
        response = await service.agency_dashboard(
            agency_id,
            airline_code=airline_code,
            channel_code=channel_code,
            capability_area=capability_area,
            capability_status=capability_status,
        )
        mapping = {
            "channels": response["operational_channels"],
            "capabilities": response["capabilities"],
            "pss-profiles": response["pss_profiles"],
            "gds-participations": response["gds_participations"],
            "ndc-capabilities": response["ndc_capabilities"],
            "fulfillment-capabilities": response["fulfillment_capabilities"],
            "servicing-capabilities": response["servicing_capabilities"],
            "restrictions": response["restrictions"],
            "evidence-links": response["evidence"],
        }
        normalized = entity_type.strip().lower().replace("_", "-")
        if normalized not in mapping:
            raise AirlineDistributionCapabilityError("Agency distribution record view is not available for this entity type.")
        items = mapping[normalized]
    except AirlineDistributionCapabilityError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "entity_type": entity_type, "items": items, "count": len(items), "read_only": True, **service.safety_flags()}
