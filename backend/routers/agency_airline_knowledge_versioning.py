from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_knowledge_versioning_service import (
    PHASE_LABEL,
    AirlineKnowledgeVersioningError,
    AirlineKnowledgeVersioningService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/knowledge-updates", tags=["agency-airline-knowledge-updates"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


@router.get("")
async def list_agency_knowledge_updates(
    agency_id: str,
    airline_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgeVersioningService(db).agency_response(
        agency_id,
        airline_id=airline_id,
        category=category,
        review_status=review_status,
    )


@router.get("/{change_set_id}")
async def get_agency_knowledge_update(
    agency_id: str,
    change_set_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await AirlineKnowledgeVersioningService(db).agency_change_set(agency_id, change_set_id)
    except AirlineKnowledgeVersioningError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
