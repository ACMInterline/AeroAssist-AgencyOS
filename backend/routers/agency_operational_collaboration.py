from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from auth import get_current_user
from database import Database, get_database
from models import (
    CommunicationAttachmentCreate,
    CommunicationMessageCreate,
    CommunicationMessageEdit,
    CommunicationThreadCreate,
)
from services.authorization_service import agency_permissions
from services.operational_collaboration_service import (
    OperationalCollaborationError,
    OperationalCollaborationService,
)
from services.tenant_service import assert_agency_access, get_membership


router = APIRouter(
    prefix="/api/agencies/{agency_id}/operational-collaboration",
    tags=["agency-operational-collaboration"],
)


class ThreadCloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str


async def authorize(
    db: Database,
    agency_id: str,
    user: dict[str, Any],
    permission: str,
) -> dict[str, Any]:
    await assert_agency_access(db, agency_id, user)
    membership = await get_membership(db, agency_id, user["id"])
    if permission not in agency_permissions(membership.get("agency_role")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission {permission} is required.",
        )
    return membership


def actor(user: dict[str, Any], membership: dict[str, Any]) -> dict[str, Any]:
    return {
        **user,
        "actor_type": "agency",
        "agency_role": membership.get("agency_role"),
        "identity_id": user.get("identity_id") or user.get("id"),
        "display_name": user.get("full_name") or user.get("email") or "Agency user",
    }


def translate(exc: OperationalCollaborationError) -> HTTPException:
    not_found = {
        "THREAD_NOT_FOUND",
        "MESSAGE_NOT_FOUND",
        "TIMELINE_NOT_FOUND",
        "ENTITY_REFERENCE_NOT_FOUND",
    }
    conflict = {
        "IDEMPOTENCY_CONFLICT",
        "THREAD_CLOSED",
        "THREAD_ARCHIVED",
    }
    code = (
        status.HTTP_404_NOT_FOUND
        if exc.code in not_found
        else status.HTTP_409_CONFLICT
        if exc.code in conflict
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(
        status_code=code, detail={"code": exc.code, "message": str(exc)}
    )


@router.get("/threads")
async def list_threads(
    agency_id: str,
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    thread_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await authorize(db, agency_id, user, "view_tasks")
    service = OperationalCollaborationService(db)
    items = await service.list_threads(
        agency_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status=thread_status,
        visibility={"internal", "agency", "client", "passenger", "supplier", "system"},
        limit=limit,
    )
    return {"items": items, "count": len(items), **service.safety_flags()}


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_thread(
    agency_id: str,
    payload: CommunicationThreadCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    membership = await authorize(db, agency_id, user, "edit_tasks")
    service = OperationalCollaborationService(db)
    try:
        detail = await service.create_thread(
            agency_id, payload, actor(user, membership)
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {**detail, **service.safety_flags()}


@router.get("/threads/{thread_id}")
async def get_thread(
    agency_id: str,
    thread_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await authorize(db, agency_id, user, "view_tasks")
    service = OperationalCollaborationService(db)
    try:
        detail = await service.thread_detail(
            agency_id,
            thread_id,
            visibility={"internal", "agency", "client", "passenger", "supplier", "system"},
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {**detail, **service.safety_flags()}


@router.post("/threads/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
async def post_message(
    agency_id: str,
    thread_id: str,
    payload: CommunicationMessageCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    membership = await authorize(db, agency_id, user, "edit_tasks")
    service = OperationalCollaborationService(db)
    try:
        message = await service.post_message(
            agency_id, thread_id, payload, actor(user, membership)
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {"message": message, **service.safety_flags()}


@router.patch("/messages/{message_id}")
async def edit_message(
    agency_id: str,
    message_id: str,
    payload: CommunicationMessageEdit,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    membership = await authorize(db, agency_id, user, "edit_tasks")
    service = OperationalCollaborationService(db)
    try:
        message = await service.edit_message(
            agency_id, message_id, payload, actor(user, membership)
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {"message": message, **service.safety_flags()}


@router.post("/threads/{thread_id}/attachments", status_code=status.HTTP_201_CREATED)
async def register_attachment(
    agency_id: str,
    thread_id: str,
    payload: CommunicationAttachmentCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    membership = await authorize(db, agency_id, user, "edit_tasks")
    service = OperationalCollaborationService(db)
    try:
        attachment = await service.register_attachment(
            agency_id, thread_id, payload, actor(user, membership)
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {"attachment": attachment, **service.safety_flags()}


@router.post("/threads/{thread_id}/close")
async def close_thread(
    agency_id: str,
    thread_id: str,
    payload: ThreadCloseRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    membership = await authorize(db, agency_id, user, "edit_tasks")
    service = OperationalCollaborationService(db)
    try:
        thread = await service.close_thread(
            agency_id, thread_id, actor(user, membership), payload.reason
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {"thread": thread, **service.safety_flags()}


@router.get("/entities/{entity_type}/{entity_id}/activity")
async def entity_activity(
    agency_id: str,
    entity_type: str,
    entity_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await authorize(db, agency_id, user, "view_tasks")
    service = OperationalCollaborationService(db)
    try:
        return await service.entity_activity(
            agency_id,
            entity_type,
            entity_id,
            visibility={"internal", "agency", "client", "passenger", "supplier", "system"},
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc


@router.get("/search")
async def search_activity(
    agency_id: str,
    q: str = Query(min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await authorize(db, agency_id, user, "view_tasks")
    service = OperationalCollaborationService(db)
    return await service.search(
        agency_id,
        q,
        visibility={"internal", "agency", "client", "passenger", "supplier", "system"},
        limit=limit,
    )


@router.get("/notifications")
async def list_notifications(
    agency_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    await authorize(db, agency_id, user, "view_tasks")
    service = OperationalCollaborationService(db)
    items = await service.list_notifications(
        agency_id,
        visibility={"internal", "agency", "client", "passenger", "supplier", "system"},
        limit=limit,
    )
    return {
        "items": items,
        "count": len(items),
        "projection_only": True,
        **service.safety_flags(),
    }
