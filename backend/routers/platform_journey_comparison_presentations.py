from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.journey_comparison_client_presentation_service import (
    JourneyComparisonClientPresentationService,
    JourneyComparisonPresentationError,
    PHASE_LABEL,
)


router = APIRouter(prefix="/api/platform/journey-comparison-presentations", tags=["platform-journey-comparison-presentations"])
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


def require_platform(user: dict) -> None:
    if user.get("global_role") not in PLATFORM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform access is required.")


@router.get("")
async def dashboard(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    return await JourneyComparisonClientPresentationService(db).dashboard()


@router.get("/summary")
async def summary(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyComparisonClientPresentationService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_readiness(), "read_only": True, **service.safety_flags()}


@router.get("/filters")
async def filters(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyComparisonClientPresentationService(db)
    return {"phase": PHASE_LABEL, "filters": service.filters(), "read_only": True, **service.safety_flags()}


@router.get("/comparison-dimensions")
async def comparison_dimensions(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyComparisonClientPresentationService(db)
    return {"phase": PHASE_LABEL, "items": service.filters()["comparison_dimensions"], "read_only": True, **service.safety_flags()}


@router.get("/validation-codes")
async def validation_codes(user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyComparisonClientPresentationService(db)
    return {"phase": PHASE_LABEL, "items": service.filters()["validation_codes"], "read_only": True, **service.safety_flags()}


@router.get("/presentations")
async def presentations(
    agency_id: str | None = Query(default=None),
    presentation_status: str | None = Query(default=None, alias="status"),
    audience_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    require_platform(user)
    service = JourneyComparisonClientPresentationService(db)
    items = await service.list_presentations(agency_id, status=presentation_status, audience_type=audience_type, include_archived=True)
    safe_items = [service._platform_summary(item) for item in items]
    return {"phase": PHASE_LABEL, "items": safe_items, "count": len(safe_items), "read_only": True, **service.safety_flags()}


@router.get("/presentations/{presentation_id}")
async def presentation_detail(presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    try:
        return await JourneyComparisonClientPresentationService(db).platform_detail(presentation_id)
    except JourneyComparisonPresentationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/presentations/{presentation_id}/snapshots")
async def presentation_snapshots(presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    require_platform(user)
    service = JourneyComparisonClientPresentationService(db)
    presentation = await db.collection("journey_comparison_presentations").find_one({"id": presentation_id})
    if not presentation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey comparison presentation was not found.")
    items = [service._snapshot_summary(item) for item in await service.list_snapshots(str(presentation["agency_id"]), presentation_id)]
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), "read_only": True, **service.safety_flags()}
