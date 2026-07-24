from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.operational_collaboration_service import (
    OperationalCollaborationError,
    OperationalCollaborationService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(
    prefix="/api/platform/operational-collaboration",
    tags=["platform-operational-collaboration"],
)

PLATFORM_GOVERNANCE_ROLES = ["platform_owner", "platform_admin"]


async def require_governance(user: dict[str, Any]) -> None:
    await require_any_platform_role(user, PLATFORM_GOVERNANCE_ROLES)


def translate(exc: OperationalCollaborationError) -> HTTPException:
    return HTTPException(
        status_code=(
            status.HTTP_404_NOT_FOUND
            if exc.code in {"THREAD_NOT_FOUND", "ENTITY_REFERENCE_NOT_FOUND"}
            else status.HTTP_400_BAD_REQUEST
        ),
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get("")
async def overview(
    agency_id: str = Query(min_length=1),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await require_governance(user)
    service = OperationalCollaborationService(db)
    threads = await service.list_threads(agency_id, limit=200)
    timeline = await service.list_timeline(agency_id=agency_id, limit=200)
    notifications = await service.list_notifications(agency_id, limit=200)
    return {
        "agency_id": agency_id,
        "summary": {
            "thread_count": len(threads),
            "timeline_entry_count": len(timeline),
            "notification_projection_count": len(notifications),
        },
        "threads": threads,
        "recent_timeline": timeline[-50:],
        "read_only_governance": True,
        **service.safety_flags(),
    }


@router.get("/threads/{thread_id}")
async def thread_detail(
    thread_id: str,
    agency_id: str = Query(min_length=1),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await require_governance(user)
    service = OperationalCollaborationService(db)
    try:
        detail = await service.thread_detail(agency_id, thread_id)
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {**detail, "read_only_governance": True, **service.safety_flags()}


@router.get("/search")
async def search(
    agency_id: str = Query(min_length=1),
    q: str = Query(min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await require_governance(user)
    return await OperationalCollaborationService(db).search(
        agency_id, q, limit=limit
    )


@router.get("/migration-analysis")
async def migration_analysis(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await require_governance(user)
    return await OperationalCollaborationService(db).migration_analysis()
