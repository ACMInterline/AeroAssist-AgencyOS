from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import VisualPolicyEditorCardCreate, VisualPolicyEditorCardUpdate
from services.tenant_service import require_any_platform_role
from services.visual_policy_editor_service import (
    PHASE_LABEL,
    VisualPolicyEditorError,
    VisualPolicyEditorService,
)


router = APIRouter(tags=["platform-visual-policy-editor"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/visual-policy-editor")
async def list_platform_visual_policy_editor_cards(
    agency_id: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    policy_family: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    support_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await VisualPolicyEditorService(db).platform_response(
        agency_id=agency_id,
        airline=airline,
        policy_family=policy_family,
        service_family=service_family,
        service_code=service_code,
        status=status_filter,
        support_status=support_status,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/visual-policy-editor/summary")
async def summarize_platform_visual_policy_editor_cards(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await VisualPolicyEditorService(db).platform_summary(agency_id)


@router.post("/api/platform/visual-policy-editor", status_code=status.HTTP_201_CREATED)
async def create_platform_visual_policy_editor_card(
    payload: VisualPolicyEditorCardCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await VisualPolicyEditorService(db).create_card(payload, user)
    except VisualPolicyEditorError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/visual-policy-editor/{card_id}")
async def get_platform_visual_policy_editor_card(
    card_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = VisualPolicyEditorService(db)
    try:
        card = await service.get_card(card_id)
    except VisualPolicyEditorError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "visual_policy_editor_card": card, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/visual-policy-editor/{card_id}")
async def update_platform_visual_policy_editor_card(
    card_id: str,
    payload: VisualPolicyEditorCardUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await VisualPolicyEditorService(db).update_card(card_id, payload, user)
    except VisualPolicyEditorError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/visual-policy-editor/{card_id}")
async def archive_platform_visual_policy_editor_card(
    card_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await VisualPolicyEditorService(db).archive_card(card_id, user)
    except VisualPolicyEditorError as exc:
        raise bad_request(str(exc)) from exc
