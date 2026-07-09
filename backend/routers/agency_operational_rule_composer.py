from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalRuleComposerRuleCreate, OperationalRuleComposerRuleUpdate
from services.operational_rule_composer_service import (
    PHASE_LABEL,
    OperationalRuleComposerError,
    OperationalRuleComposerService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-operational-rule-composer"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/agencies/{agency_id}/rule-composer")
async def list_agency_rule_composer_rules(
    agency_id: str,
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
    await require_read(db, agency_id, user)
    return await OperationalRuleComposerService(db).agency_response(
        agency_id,
        rule_family=rule_family,
        service_family=service_family,
        service_code=service_code,
        lifecycle_status=lifecycle_status,
        severity=severity,
        operator=operator,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/agencies/{agency_id}/rule-composer/summary")
async def summarize_agency_rule_composer_rules(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalRuleComposerService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/rule-composer", status_code=status.HTTP_201_CREATED)
async def create_agency_rule_composer_rule(
    agency_id: str,
    payload: OperationalRuleComposerRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalRuleComposerService(db).create_rule(payload, user, agency_id=agency_id)
    except OperationalRuleComposerError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/rule-composer/{rule_id}")
async def get_agency_rule_composer_rule(
    agency_id: str,
    rule_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalRuleComposerService(db)
    try:
        rule = await service.get_rule(rule_id, agency_id=agency_id)
    except OperationalRuleComposerError:
        raise not_found("Operational rule composer metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "operational_rule_composer_rule": rule, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/rule-composer/{rule_id}")
async def update_agency_rule_composer_rule(
    agency_id: str,
    rule_id: str,
    payload: OperationalRuleComposerRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalRuleComposerService(db).update_rule(rule_id, payload, user, agency_id=agency_id)
    except OperationalRuleComposerError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/rule-composer/{rule_id}")
async def archive_agency_rule_composer_rule(
    agency_id: str,
    rule_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalRuleComposerService(db).archive_rule(rule_id, user, agency_id=agency_id)
    except OperationalRuleComposerError as exc:
        raise bad_request(str(exc)) from exc
