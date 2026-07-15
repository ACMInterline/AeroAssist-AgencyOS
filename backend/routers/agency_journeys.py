from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.canonical_journey_itinerary_service import (
    PHASE_LABEL,
    CanonicalJourneyError,
    CanonicalJourneyItineraryService,
    FinalizedJourneySnapshotError,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/journeys", tags=["agency-journeys"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def bad_request(exc: Exception) -> HTTPException:
    code = status.HTTP_409_CONFLICT if isinstance(exc, FinalizedJourneySnapshotError) else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.get("")
async def list_agency_journeys(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    presentation_status: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
    passenger_id: str | None = Query(default=None),
    client_safe: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = CanonicalJourneyItineraryService(db)
    items = await service.list_journeys(
        agency_id=agency_id,
        status=status_filter,
        presentation_status=presentation_status,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        client_id=client_id,
        passenger_id=passenger_id,
        client_safe=client_safe,
    )
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "items": items, "count": len(items), "read_only": False, **service.safety_flags()}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency_journey(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await CanonicalJourneyItineraryService(db).create_journey(payload, user, agency_id=agency_id)
    except (CanonicalJourneyError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/summary")
async def summarize_agency_journeys(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = CanonicalJourneyItineraryService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": await service.summary(agency_id=agency_id), **service.safety_flags()}


@router.get("/{journey_id}")
async def get_agency_journey(
    agency_id: str,
    journey_id: str,
    client_safe: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return {"phase": PHASE_LABEL, **(await CanonicalJourneyItineraryService(db).get_complete_journey(agency_id, journey_id, client_safe=client_safe))}
    except CanonicalJourneyError as exc:
        raise bad_request(exc) from exc


@router.put("/{journey_id}")
async def update_agency_journey(
    agency_id: str,
    journey_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await CanonicalJourneyItineraryService(db).update_journey(agency_id, journey_id, payload, user)
    except (CanonicalJourneyError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.post("/{journey_id}/archive")
async def archive_agency_journey(
    agency_id: str,
    journey_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await CanonicalJourneyItineraryService(db).archive_journey(agency_id, journey_id, user)
    except CanonicalJourneyError as exc:
        raise bad_request(exc) from exc


async def child_create(method: str, agency_id: str, journey_id: str, payload: dict, user: dict, db: Database) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await getattr(CanonicalJourneyItineraryService(db), method)(agency_id, journey_id, payload, user)
    except (CanonicalJourneyError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.post("/{journey_id}/options", status_code=status.HTTP_201_CREATED)
async def create_agency_journey_option(agency_id: str, journey_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("create_option", agency_id, journey_id, payload, user, db)


@router.post("/{journey_id}/legs", status_code=status.HTTP_201_CREATED)
async def create_agency_journey_leg(agency_id: str, journey_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("create_leg", agency_id, journey_id, payload, user, db)


@router.post("/{journey_id}/segments", status_code=status.HTTP_201_CREATED)
async def create_agency_journey_segment(agency_id: str, journey_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("create_segment", agency_id, journey_id, payload, user, db)


@router.post("/{journey_id}/connections", status_code=status.HTTP_201_CREATED)
async def create_agency_journey_connection(agency_id: str, journey_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("create_connection", agency_id, journey_id, payload, user, db)


@router.post("/{journey_id}/fare-brands", status_code=status.HTTP_201_CREATED)
async def create_agency_journey_fare_brand(agency_id: str, journey_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("create_fare_brand", agency_id, journey_id, payload, user, db)


@router.post("/{journey_id}/services", status_code=status.HTTP_201_CREATED)
async def create_agency_journey_service(agency_id: str, journey_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("create_service_presentation", agency_id, journey_id, payload, user, db)


@router.put("/{journey_id}/presentation")
async def configure_agency_journey_presentation(agency_id: str, journey_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("set_presentation", agency_id, journey_id, payload, user, db)


@router.post("/{journey_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_journey_snapshot(agency_id: str, journey_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await child_create("create_snapshot", agency_id, journey_id, payload, user, db)


@router.get("/{journey_id}/snapshots")
async def list_agency_journey_snapshots(agency_id: str, journey_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        service = CanonicalJourneyItineraryService(db)
        items = await service.list_snapshots(agency_id, journey_id)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except CanonicalJourneyError as exc:
        raise bad_request(exc) from exc


@router.put("/{journey_id}/snapshots/{snapshot_id}")
async def update_agency_journey_snapshot(agency_id: str, journey_id: str, snapshot_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await CanonicalJourneyItineraryService(db).update_snapshot(agency_id, journey_id, snapshot_id, payload, user)
    except (CanonicalJourneyError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.post("/{journey_id}/snapshots/{snapshot_id}/finalize")
async def finalize_agency_journey_snapshot(agency_id: str, journey_id: str, snapshot_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await CanonicalJourneyItineraryService(db).finalize_snapshot(agency_id, journey_id, snapshot_id, user)
    except CanonicalJourneyError as exc:
        raise bad_request(exc) from exc


async def project_source(method: str, agency_id: str, source_id: str, user: dict, db: Database) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await getattr(CanonicalJourneyItineraryService(db), method)(agency_id, source_id, user)
    except (CanonicalJourneyError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.post("/from-trip/{trip_id}", status_code=status.HTTP_201_CREATED)
async def project_agency_journey_from_trip(agency_id: str, trip_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await project_source("project_from_trip", agency_id, trip_id, user, db)


@router.post("/from-offer/{offer_id}", status_code=status.HTTP_201_CREATED)
async def project_agency_journey_from_offer(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await project_source("project_from_offer", agency_id, offer_id, user, db)


@router.post("/from-booking/{booking_id}", status_code=status.HTTP_201_CREATED)
async def project_agency_journey_from_booking(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await project_source("project_from_booking", agency_id, booking_id, user, db)


@router.post("/from-ticket/{ticket_id}", status_code=status.HTTP_201_CREATED)
async def project_agency_journey_from_ticket(agency_id: str, ticket_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await project_source("project_from_ticket", agency_id, ticket_id, user, db)


@router.post("/from-emd/{emd_id}", status_code=status.HTTP_201_CREATED)
async def project_agency_journey_from_emd(agency_id: str, emd_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await project_source("project_from_emd", agency_id, emd_id, user, db)
