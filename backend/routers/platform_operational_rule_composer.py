from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalRuleComposerRuleCreate, OperationalRuleComposerRuleUpdate
from services.operational_rule_composer_service import (
    PHASE_LABEL,
    OperationalRuleComposerError,
    OperationalRuleComposerService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-operational-rule-composer"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/operational-rule-composer")
async def list_platform_operational_rule_composer_rules(
    agency_id: str | None = Query(default=None),
    rule_family: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    operator: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalRuleComposerService(db).platform_response(
        agency_id=agency_id,
        rule_family=rule_family,
        service_family=service_family,
        service_code=service_code,
        lifecycle_status=lifecycle_status,
        severity=severity,
        operator=operator,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/operational-rule-composer/summary")
async def summarize_platform_operational_rule_composer_rules(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalRuleComposerService(db).platform_summary(agency_id)


@router.post("/api/platform/operational-rule-composer", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_rule_composer_rule(
    payload: OperationalRuleComposerRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalRuleComposerService(db).create_rule(payload, user)
    except OperationalRuleComposerError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/operational-rule-composer/{rule_id}")
async def get_platform_operational_rule_composer_rule(
    rule_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalRuleComposerService(db)
    try:
        rule = await service.get_rule(rule_id)
    except OperationalRuleComposerError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "operational_rule_composer_rule": rule, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/operational-rule-composer/{rule_id}")
async def update_platform_operational_rule_composer_rule(
    rule_id: str,
    payload: OperationalRuleComposerRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalRuleComposerService(db).update_rule(rule_id, payload, user)
    except OperationalRuleComposerError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/operational-rule-composer/{rule_id}")
async def archive_platform_operational_rule_composer_rule(
    rule_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalRuleComposerService(db).archive_rule(rule_id, user)
    except OperationalRuleComposerError as exc:
        raise bad_request(str(exc)) from exc
