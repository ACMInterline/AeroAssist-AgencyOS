from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineIntelligenceKnowledgeReleaseAssignmentCreateRequest,
    AirlineIntelligenceKnowledgeReleaseAssignmentUpdateRequest,
    AirlineIntelligenceKnowledgeReleaseChannelCreateRequest,
    AirlineIntelligenceKnowledgeReleaseChannelUpdateRequest,
    AirlineIntelligenceKnowledgeRollbackPlanCreateRequest,
    AirlineIntelligenceKnowledgeRollbackPlanUpdateRequest,
    AirlineIntelligenceKnowledgeVersionComparisonCreateRequest,
    AirlineIntelligenceKnowledgeVersionCreateRequest,
    AirlineIntelligenceKnowledgeVersionItemCreateRequest,
    AirlineIntelligenceKnowledgeVersionItemUpdateRequest,
    AirlineIntelligenceKnowledgeVersionSnapshotCreateRequest,
    AirlineIntelligenceKnowledgeVersionUpdateRequest,
)
from services.airline_intelligence_knowledge_version_service import AirlineIntelligenceKnowledgeVersionService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-intelligence-knowledge-versions", tags=["platform-airline-intelligence-knowledge-versions"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("/summary")
async def get_platform_airline_intelligence_knowledge_version_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineIntelligenceKnowledgeVersionService(db).summary()


@router.get("/versions")
async def list_platform_airline_intelligence_knowledge_versions(
    version_status: str | None = Query(default=None, alias="status"),
    agency_visibility_mode: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).list_versions(status=version_status, agency_visibility_mode=agency_visibility_mode),
        "metadata_only": True,
    }


@router.post("/versions", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_knowledge_version(
    payload: AirlineIntelligenceKnowledgeVersionCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).create_version(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/versions/{version_id}")
async def get_platform_airline_intelligence_knowledge_version(
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await AirlineIntelligenceKnowledgeVersionService(db).get_version(version_id)
    if not detail:
        raise not_found("Airline intelligence knowledge version not found.")
    return detail


@router.patch("/versions/{version_id}")
async def update_platform_airline_intelligence_knowledge_version(
    version_id: str,
    payload: AirlineIntelligenceKnowledgeVersionUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).update_version(version_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/versions/{version_id}/items")
async def list_platform_airline_intelligence_knowledge_version_items(
    version_id: str,
    inclusion_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).list_version_items(version_id=version_id, inclusion_status=inclusion_status),
        "metadata_only": True,
    }


@router.post("/versions/{version_id}/items", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_knowledge_version_item(
    version_id: str,
    payload: AirlineIntelligenceKnowledgeVersionItemCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).add_version_item(version_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/version-items/{version_item_id}")
async def update_platform_airline_intelligence_knowledge_version_item(
    version_item_id: str,
    payload: AirlineIntelligenceKnowledgeVersionItemUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).update_version_item(version_item_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/version-items/{version_item_id}")
async def remove_platform_airline_intelligence_knowledge_version_item(
    version_item_id: str,
    reason: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).remove_version_item(version_item_id, reason)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/versions/{version_id}/freeze")
async def freeze_platform_airline_intelligence_knowledge_version(
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).freeze_version(version_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/versions/{version_id}/approve")
async def approve_platform_airline_intelligence_knowledge_version(
    version_id: str,
    payload: AirlineIntelligenceKnowledgeVersionUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).approve_version(version_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/versions/{version_id}/mark-published-metadata")
async def mark_platform_airline_intelligence_knowledge_version_published_metadata(
    version_id: str,
    payload: AirlineIntelligenceKnowledgeVersionUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).mark_published_metadata(version_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/release-channels")
async def list_platform_airline_intelligence_release_channels(
    audience: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).list_release_channels(audience=audience, is_active=is_active),
        "metadata_only": True,
    }


@router.post("/release-channels", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_release_channel(
    payload: AirlineIntelligenceKnowledgeReleaseChannelCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).create_release_channel(payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/release-channels/{channel_id}")
async def update_platform_airline_intelligence_release_channel(
    channel_id: str,
    payload: AirlineIntelligenceKnowledgeReleaseChannelUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).update_release_channel(channel_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/release-assignments")
async def list_platform_airline_intelligence_release_assignments(
    version_id: str | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    agency_id: str | None = Query(default=None),
    assignment_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).list_release_assignments(
            version_id=version_id,
            channel_id=channel_id,
            agency_id=agency_id,
            status=assignment_status,
        ),
        "metadata_only": True,
    }


@router.post("/release-assignments", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_release_assignment(
    payload: AirlineIntelligenceKnowledgeReleaseAssignmentCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).create_release_assignment(payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/release-assignments/{assignment_id}")
async def update_platform_airline_intelligence_release_assignment(
    assignment_id: str,
    payload: AirlineIntelligenceKnowledgeReleaseAssignmentUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).update_release_assignment(assignment_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/comparisons")
async def list_platform_airline_intelligence_knowledge_version_comparisons(
    base_version_id: str | None = Query(default=None),
    compare_version_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).list_comparisons(base_version_id=base_version_id, compare_version_id=compare_version_id),
        "metadata_only": True,
    }


@router.post("/comparisons", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_knowledge_version_comparison(
    payload: AirlineIntelligenceKnowledgeVersionComparisonCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).compare_versions(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/rollback-plans")
async def list_platform_airline_intelligence_rollback_plans(
    from_version_id: str | None = Query(default=None),
    to_version_id: str | None = Query(default=None),
    rollback_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).list_rollback_plans(from_version_id=from_version_id, to_version_id=to_version_id, status=rollback_status),
        "metadata_only": True,
    }


@router.post("/rollback-plans", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_rollback_plan(
    payload: AirlineIntelligenceKnowledgeRollbackPlanCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).create_rollback_plan(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/rollback-plans/{rollback_plan_id}")
async def update_platform_airline_intelligence_rollback_plan(
    rollback_plan_id: str,
    payload: AirlineIntelligenceKnowledgeRollbackPlanUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).update_rollback_plan(rollback_plan_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/versions/{version_id}/snapshots")
async def list_platform_airline_intelligence_knowledge_version_snapshots(
    version_id: str,
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AirlineIntelligenceKnowledgeVersionService(db).list_snapshots(version_id=version_id, snapshot_type=snapshot_type),
        "metadata_only": True,
    }


@router.post("/versions/{version_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_knowledge_version_snapshot(
    version_id: str,
    payload: AirlineIntelligenceKnowledgeVersionSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineIntelligenceKnowledgeVersionService(db).create_snapshot(version_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
