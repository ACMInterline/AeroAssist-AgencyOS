from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.canonical_journey_itinerary_service import PHASE_LABEL, CanonicalJourneyItineraryService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/journey-engine", tags=["platform-journey-engine"])

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


@router.get("")
async def platform_journey_engine_dashboard(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await CanonicalJourneyItineraryService(db).dashboard(agency_id=agency_id)


@router.get("/summary")
async def platform_journey_engine_summary(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = CanonicalJourneyItineraryService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id=agency_id), **service.safety_flags()}


@router.get("/filters")
async def platform_journey_engine_filters(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = CanonicalJourneyItineraryService(db)
    return {"phase": PHASE_LABEL, "filters": service.filter_metadata(), **service.safety_flags()}


@router.get("/journeys")
async def list_platform_journeys(
    agency_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    presentation_status: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
    passenger_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = CanonicalJourneyItineraryService(db)
    items = await service.list_journeys(
        agency_id=agency_id,
        status=status,
        presentation_status=presentation_status,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        client_id=client_id,
        passenger_id=passenger_id,
        include_archived=include_archived,
    )
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.get("/journeys/{journey_id}")
async def get_platform_journey(
    journey_id: str,
    agency_id: str = Query(...),
    client_safe: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return {"phase": PHASE_LABEL, **(await CanonicalJourneyItineraryService(db).get_complete_journey(agency_id, journey_id, client_safe=client_safe))}


@router.get("/journeys/{journey_id}/snapshots")
async def list_platform_journey_snapshots(
    journey_id: str,
    agency_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = CanonicalJourneyItineraryService(db)
    items = await service.list_snapshots(agency_id, journey_id)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
