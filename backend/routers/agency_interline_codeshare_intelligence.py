from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.interline_codeshare_intelligence_service import (
    PHASE_LABEL,
    InterlineCodeshareIntelligenceError,
    InterlineCodeshareIntelligenceService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/interline-codeshare-advisor",
    tags=["agency-interline-codeshare-advisor"],
)

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def bad_request(exc: InterlineCodeshareIntelligenceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_agency_interline_codeshare_advisor(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await InterlineCodeshareIntelligenceService(db).agency_dashboard(
        agency_id,
        airline_code=airline_code,
        relationship_type=relationship_type,
        service_family=service_family,
    )


@router.get("/summary")
async def summarize_agency_interline_codeshare_advisor(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = InterlineCodeshareIntelligenceService(db)
    response = await service.agency_dashboard(agency_id, airline_code=airline_code)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": response["summary"], "warnings": response["warnings"], "read_only": True, **service.safety_flags()}


@router.post("/evaluate")
async def evaluate_agency_interline_itinerary(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await InterlineCodeshareIntelligenceService(db).evaluate_itinerary(payload, agency_id=agency_id, agency_safe=True)
    except InterlineCodeshareIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}")
async def list_agency_interline_codeshare_records(
    agency_id: str,
    entity_type: str,
    airline_code: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = InterlineCodeshareIntelligenceService(db)
    try:
        response = await service.agency_dashboard(agency_id, airline_code=airline_code, relationship_type=relationship_type, service_family=service_family)
        mapping = {"relationships": response["relationships"], **response["rules"]}
        normalized = entity_type.strip().lower().replace("_", "-")
        if normalized not in mapping:
            raise InterlineCodeshareIntelligenceError("Agency interline intelligence view is not available for this entity type.")
        items = mapping[normalized]
    except InterlineCodeshareIntelligenceError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "entity_type": entity_type, "items": items, "count": len(items), "read_only": True, **service.safety_flags()}
