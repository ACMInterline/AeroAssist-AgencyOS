from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_contact_communication_intelligence_service import (
    PHASE_LABEL,
    AirlineContactCommunicationIntelligenceError,
    AirlineContactCommunicationIntelligenceService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/airline-contact-directory",
    tags=["agency-airline-contact-directory"],
)

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
INTERACTION_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_interaction_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, INTERACTION_ROLES)


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_agency_airline_contact_directory(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    desk_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineContactCommunicationIntelligenceService(db).agency_dashboard(
        agency_id,
        airline_code=airline_code,
        desk_type=desk_type,
    )


@router.get("/summary")
async def summarize_agency_airline_contact_directory(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineContactCommunicationIntelligenceService(db)
    response = await service.agency_dashboard(agency_id)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": response["summary"], "stale_contacts": response["stale_contacts"], "read_only_directory": True, **service.safety_flags()}


@router.get("/filters")
async def get_agency_airline_contact_filters(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineContactCommunicationIntelligenceService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "filters": service.filter_metadata(), "read_only_directory": True, **service.safety_flags()}


@router.post("/find-desk")
async def find_agency_airline_desk(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).find_desk(
            payload,
            agency_id=agency_id,
            agency_safe=True,
        )
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/compose")
async def compose_agency_airline_message(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).compose_message(
            payload,
            agency_id=agency_id,
            agency_safe=True,
        )
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.get("/interactions")
async def list_agency_airline_supplier_interactions(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    desk_type: str | None = Query(default=None),
    after_sales_case_id: str | None = Query(default=None),
    workflow_instance_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineContactCommunicationIntelligenceService(db)
    items = await service.list_agency_records(
        "interactions",
        agency_id,
        airline_code=airline_code,
        desk_type=desk_type,
        after_sales_case_id=after_sales_case_id,
        workflow_instance_id=workflow_instance_id,
    )
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/interactions", status_code=status.HTTP_201_CREATED)
async def log_agency_airline_supplier_interaction(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_interaction_write(db, agency_id, user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).log_interaction(payload, user, agency_id=agency_id)
    except (AirlineContactCommunicationIntelligenceError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/interactions/{record_id}")
async def get_agency_airline_supplier_interaction(
    agency_id: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).get_agency_record("interactions", agency_id, record_id)
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}")
async def list_agency_airline_contact_records(
    agency_id: str,
    entity_type: str,
    airline_code: str | None = Query(default=None),
    desk_type: str | None = Query(default=None),
    contact_directory_entry_id: str | None = Query(default=None),
    template_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineContactCommunicationIntelligenceService(db)
    try:
        items = await service.list_agency_records(
            entity_type,
            agency_id,
            airline_code=airline_code,
            desk_type=desk_type,
            contact_directory_entry_id=contact_directory_entry_id,
            template_type=template_type,
        )
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "entity_type": entity_type, "items": items, "count": len(items), "read_only": entity_type != "interactions", **service.safety_flags()}


@router.get("/{entity_type}/{record_id}")
async def get_agency_airline_contact_record(
    agency_id: str,
    entity_type: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await AirlineContactCommunicationIntelligenceService(db).get_agency_record(entity_type, agency_id, record_id)
    except AirlineContactCommunicationIntelligenceError as exc:
        raise bad_request(exc) from exc
