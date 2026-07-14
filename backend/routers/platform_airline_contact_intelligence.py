from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_contact_communication_intelligence_service import (
    PHASE_LABEL,
    AirlineContactCommunicationIntelligenceError,
    AirlineContactCommunicationIntelligenceService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(
    prefix="/api/platform/airline-contact-intelligence",
    tags=["platform-airline-contact-intelligence"],
)

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_platform_airline_contact_intelligence(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    desk_type: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    freshness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlineContactCommunicationIntelligenceService(db).platform_dashboard(
        agency_id=agency_id,
        airline_code=airline_code,
        desk_type=desk_type,
        publication_status=publication_status,
        freshness_status=freshness_status,
    )


@router.get("/summary")
async def summarize_platform_airline_contact_intelligence(
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineContactCommunicationIntelligenceService(db)
    response = await service.platform_dashboard(airline_code=airline_code)
    return {
        "phase": PHASE_LABEL,
        "summary": response["summary"],
        "stale_contacts": response["stale_contacts"],
        **service.safety_flags(),
    }


@router.get("/filters")
async def get_platform_airline_contact_filters(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineContactCommunicationIntelligenceService(db)
    return {"phase": PHASE_LABEL, "filters": service.filter_metadata(), **service.safety_flags()}


@router.post("/find-desk")
async def find_platform_airline_desk(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).find_desk(
            payload,
            agency_id=payload.get("agency_id"),
            agency_safe=False,
        )
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/compose")
async def compose_platform_airline_message(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).compose_message(
            payload,
            agency_id=payload.get("agency_id"),
            agency_safe=False,
        )
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}")
async def list_platform_airline_contact_records(
    entity_type: str,
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    desk_type: str | None = Query(default=None),
    contact_directory_entry_id: str | None = Query(default=None),
    template_type: str | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineContactCommunicationIntelligenceService(db)
    try:
        items = await service.list_records(
            entity_type,
            agency_id=agency_id,
            airline_code=airline_code,
            desk_type=desk_type,
            contact_directory_entry_id=contact_directory_entry_id,
            template_type=template_type,
            verification_status=verification_status,
            publication_status=publication_status,
        )
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "entity_type": entity_type, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/{entity_type}", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_contact_record(
    entity_type: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).create_record(entity_type, payload, user)
    except (AirlineContactCommunicationIntelligenceError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}/{record_id}")
async def get_platform_airline_contact_record(
    entity_type: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).get_record(entity_type, record_id)
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.put("/{entity_type}/{record_id}")
async def update_platform_airline_contact_record(
    entity_type: str,
    record_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).update_record(entity_type, record_id, payload, user)
    except (AirlineContactCommunicationIntelligenceError, ValueError) as exc:
        raise bad_request(exc) from exc
