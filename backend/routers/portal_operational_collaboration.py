from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from database import Database, get_database
from routers.portal import portal_context
from services.operational_collaboration_service import (
    OperationalCollaborationError,
    OperationalCollaborationService,
)


router = APIRouter(
    prefix="/api/portal/communications", tags=["portal-operational-collaboration"]
)


class PortalCommunicationReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plain_text: str
    rich_text: str | None = None
    attachment_ids: list[str] = Field(default_factory=list)
    idempotency_key: str | None = None


def translate(exc: OperationalCollaborationError) -> HTTPException:
    return HTTPException(
        status_code=(
            status.HTTP_404_NOT_FOUND
            if exc.code in {"THREAD_NOT_FOUND", "ENTITY_REFERENCE_NOT_FOUND"}
            else status.HTTP_403_FORBIDDEN
            if exc.code
            in {
                "PORTAL_VISIBILITY_MISMATCH",
                "SENDER_PARTICIPANT_MISMATCH",
                "THREAD_PARTICIPATION_REQUIRED",
                "MESSAGE_VISIBILITY_FORBIDDEN",
            }
            else status.HTTP_400_BAD_REQUEST
        ),
        detail={"code": exc.code, "message": str(exc)},
    )


@router.get("")
async def list_threads(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    service = OperationalCollaborationService(db)
    items = await service.portal_threads(
        ctx, entity_type=entity_type, entity_id=entity_id
    )
    return {
        "items": items,
        "count": len(items),
        "subject_type": ctx.get("subject_type"),
        **service.safety_flags(),
    }


@router.get("/{thread_id}")
async def thread_detail(
    thread_id: str,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    service = OperationalCollaborationService(db)
    try:
        detail = await service.portal_thread_detail(ctx, thread_id)
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {**detail, **service.safety_flags()}


@router.post("/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
async def post_reply(
    thread_id: str,
    payload: PortalCommunicationReply,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict[str, Any]:
    service = OperationalCollaborationService(db)
    try:
        message = await service.portal_post_message(
            ctx,
            thread_id,
            {
                **payload.model_dump(mode="json"),
                "message_type": "message",
            },
        )
    except OperationalCollaborationError as exc:
        raise translate(exc) from exc
    return {"message": message, **service.safety_flags()}
