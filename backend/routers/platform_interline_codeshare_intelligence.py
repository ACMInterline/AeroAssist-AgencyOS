from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.interline_codeshare_intelligence_service import (
    PHASE_LABEL,
    InterlineCodeshareIntelligenceError,
    InterlineCodeshareIntelligenceService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(
    prefix="/api/platform/interline-codeshare-intelligence",
    tags=["platform-interline-codeshare-intelligence"],
)

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: InterlineCodeshareIntelligenceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_platform_interline_codeshare_intelligence(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    relationship_status: str | None = Query(default=None),
    rule_status: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await InterlineCodeshareIntelligenceService(db).platform_dashboard(
        agency_id=agency_id,
        airline_code=airline_code,
        relationship_type=relationship_type,
        relationship_status=relationship_status,
        rule_status=rule_status,
        service_family=service_family,
        publication_status=publication_status,
    )


@router.get("/summary")
async def summarize_platform_interline_codeshare_intelligence(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = InterlineCodeshareIntelligenceService(db)
    response = await service.platform_dashboard(agency_id=agency_id, airline_code=airline_code)
    return {"phase": PHASE_LABEL, "summary": response["summary"], "legacy_context": response["legacy_context"], **service.safety_flags()}


@router.get("/filters")
async def get_platform_interline_codeshare_filters(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = InterlineCodeshareIntelligenceService(db)
    return {"phase": PHASE_LABEL, "filters": service.filter_metadata(), **service.safety_flags()}


@router.post("/evaluate")
async def evaluate_platform_interline_itinerary(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await InterlineCodeshareIntelligenceService(db).evaluate_itinerary(payload, agency_id=payload.get("agency_id"))
    except InterlineCodeshareIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}")
async def list_platform_interline_codeshare_records(
    entity_type: str,
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    relationship_status: str | None = Query(default=None),
    rule_status: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = InterlineCodeshareIntelligenceService(db)
    try:
        items = await service.list_records(
            entity_type,
            agency_id=agency_id,
            airline_code=airline_code,
            relationship_type=relationship_type,
            relationship_status=relationship_status,
            rule_status=rule_status,
            service_family=service_family,
            service_code=service_code,
            publication_status=publication_status,
        )
    except InterlineCodeshareIntelligenceError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "entity_type": entity_type, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/{entity_type}", status_code=status.HTTP_201_CREATED)
async def create_platform_interline_codeshare_record(
    entity_type: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await InterlineCodeshareIntelligenceService(db).create_record(entity_type, payload, user)
    except (InterlineCodeshareIntelligenceError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{entity_type}/{record_id}")
async def get_platform_interline_codeshare_record(
    entity_type: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await InterlineCodeshareIntelligenceService(db).get_record(entity_type, record_id)
    except InterlineCodeshareIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.put("/{entity_type}/{record_id}")
async def update_platform_interline_codeshare_record(
    entity_type: str,
    record_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await InterlineCodeshareIntelligenceService(db).update_record(entity_type, record_id, payload, user)
    except (InterlineCodeshareIntelligenceError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
