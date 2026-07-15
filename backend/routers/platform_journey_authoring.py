from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.journey_segment_authoring_service import PHASE_LABEL, JourneyAuthoringError, JourneySegmentAuthoringService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/journey-authoring", tags=["platform-journey-authoring"])

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


@router.get("")
async def dashboard(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await JourneySegmentAuthoringService(db).dashboard(agency_id)


@router.get("/summary")
async def summary(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = JourneySegmentAuthoringService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_authoring_readiness(agency_id), **service.safety_flags()}


@router.get("/filters")
async def filters(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(user)
    service = JourneySegmentAuthoringService(db)
    return {"phase": PHASE_LABEL, "filters": service.filters(), **service.safety_flags()}


@router.get("/sessions")
async def sessions(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    source_type: str | None = Query(default=None),
    include_archived: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = JourneySegmentAuthoringService(db)
    items = await service.list_authoring_sessions(agency_id, status=status_filter, source_type=source_type, include_archived=include_archived)
    safe_items = [{key: value for key, value in item.items() if key not in {"metadata"}} for item in items]
    return {"phase": PHASE_LABEL, "items": safe_items, "count": len(safe_items), "platform_diagnostics_read_only": True, **service.safety_flags()}


@router.get("/sessions/{session_id}")
async def session_detail(
    session_id: str,
    agency_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        detail = await JourneySegmentAuthoringService(db).get_authoring_session(agency_id, session_id)
        detail["sources"] = [
            {key: value for key, value in source.items() if key not in {"raw_text", "raw_payload", "restricted_metadata"}}
            for source in detail.get("sources") or []
        ]
        detail["platform_diagnostics_read_only"] = True
        return detail
    except JourneyAuthoringError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/validation-codes")
async def validation_codes(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(user)
    service = JourneySegmentAuthoringService(db)
    return {"phase": PHASE_LABEL, "items": service.filters()["validation_codes"], "platform_diagnostics_read_only": True, **service.safety_flags()}
