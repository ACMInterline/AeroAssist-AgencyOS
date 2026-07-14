from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_knowledge_versioning_service import (
    PHASE_LABEL,
    AirlineKnowledgeVersioningError,
    AirlineKnowledgeVersioningService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/knowledge-versions", tags=["platform-airline-knowledge-versioning"])

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: AirlineKnowledgeVersioningError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def list_platform_knowledge_versions(
    agency_id: str | None = Query(default=None),
    airline_id: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    category: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    revalidation_required: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlineKnowledgeVersioningService(db).platform_response(
        agency_id=agency_id,
        airline_id=airline_id,
        lifecycle_status=lifecycle_status,
        service_family=service_family,
        category=category,
        review_status=review_status,
        revalidation_required=revalidation_required,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_knowledge_version(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineKnowledgeVersioningService(db).create_version(payload, user)
    except AirlineKnowledgeVersioningError as exc:
        raise bad_request(exc) from exc


@router.post("/compare", status_code=status.HTTP_201_CREATED)
async def compare_platform_knowledge_versions(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return {
            "phase": PHASE_LABEL,
            **await AirlineKnowledgeVersioningService(db).compare_versions(
                str(payload.get("base_version_id") or ""),
                str(payload.get("target_version_id") or ""),
                user,
            ),
        }
    except AirlineKnowledgeVersioningError as exc:
        raise bad_request(exc) from exc


@router.get("/change-sets")
async def list_platform_knowledge_change_sets(
    agency_id: str | None = Query(default=None),
    airline_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    revalidation_required: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineKnowledgeVersioningService(db)
    items = await service.list_change_sets(
        agency_id=agency_id,
        airline_id=airline_id,
        category=category,
        review_status=review_status,
        revalidation_required=revalidation_required,
    )
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.get("/change-sets/{change_set_id}")
async def get_platform_knowledge_change_set(
    change_set_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return {"phase": PHASE_LABEL, **await AirlineKnowledgeVersioningService(db).get_change_set(change_set_id)}
    except AirlineKnowledgeVersioningError as exc:
        raise bad_request(exc) from exc


@router.put("/change-sets/{change_set_id}/review")
async def review_platform_knowledge_change_set(
    change_set_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return {"phase": PHASE_LABEL, **await AirlineKnowledgeVersioningService(db).review_change_set(change_set_id, payload, user)}
    except AirlineKnowledgeVersioningError as exc:
        raise bad_request(exc) from exc


@router.put("/revalidation-requests/{request_id}")
async def update_platform_knowledge_revalidation_request(
    request_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return {"phase": PHASE_LABEL, **await AirlineKnowledgeVersioningService(db).update_revalidation(request_id, payload, user)}
    except AirlineKnowledgeVersioningError as exc:
        raise bad_request(exc) from exc


@router.get("/versions/{version_id}")
async def get_platform_knowledge_version(
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return {"phase": PHASE_LABEL, **await AirlineKnowledgeVersioningService(db).get_version(version_id)}
    except AirlineKnowledgeVersioningError as exc:
        raise bad_request(exc) from exc
