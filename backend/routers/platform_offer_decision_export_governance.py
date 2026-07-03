from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_governance_service import OfferDecisionExportGovernanceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-export-governance", tags=["platform-offer-decision-export-governance"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_governance_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportGovernanceService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/diagnostics")
async def get_platform_offer_decision_export_governance_diagnostics(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportGovernanceService(db).summary(),
        "read_only": True,
    }


@router.get("/governance-records")
async def list_platform_offer_decision_export_governance_records(
    export_id: str | None = Query(default=None),
    audit_review_id: str | None = Query(default=None),
    governance_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportGovernanceService(db).list_records(export_id=export_id, audit_review_id=audit_review_id, governance_status=governance_status),
        "read_only": True,
    }


@router.get("/governance-records/{record_id}")
async def get_platform_offer_decision_export_governance_record(
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionExportGovernanceService(db).get_record_detail(record_id)
    return {
        **(detail or {"governance_record": None, "rules": [], "retention_policies": [], "legal_bases": [], "archive_statuses": [], "governance_exceptions": [], "snapshots": []}),
        "read_only": True,
    }


@router.get("/rules")
async def list_platform_offer_decision_export_governance_rules(
    governance_record_id: str | None = Query(default=None),
    rule_status: str | None = Query(default=None, alias="status"),
    rule_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportGovernanceService(db).list_rules(governance_record_id=governance_record_id, rule_status=rule_status, rule_type=rule_type),
        "read_only": True,
    }


@router.get("/retention-policies")
async def list_platform_offer_decision_export_retention_policies(
    governance_record_id: str | None = Query(default=None),
    retention_action: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportGovernanceService(db).list_retention_policies(governance_record_id=governance_record_id, retention_action=retention_action),
        "read_only": True,
    }


@router.get("/legal-bases")
async def list_platform_offer_decision_export_legal_bases(
    governance_record_id: str | None = Query(default=None),
    basis_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportGovernanceService(db).list_legal_bases(governance_record_id=governance_record_id, basis_type=basis_type),
        "read_only": True,
    }


@router.get("/archive-statuses")
async def list_platform_offer_decision_export_archive_statuses(
    governance_record_id: str | None = Query(default=None),
    archive_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportGovernanceService(db).list_archive_statuses(governance_record_id=governance_record_id, archive_status=archive_status),
        "read_only": True,
    }


@router.get("/governance-exceptions")
async def list_platform_offer_decision_export_governance_exceptions(
    governance_record_id: str | None = Query(default=None),
    exception_status: str | None = Query(default=None, alias="status"),
    exception_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportGovernanceService(db).list_exceptions(governance_record_id=governance_record_id, exception_status=exception_status, exception_type=exception_type),
        "read_only": True,
    }


@router.get("/snapshots")
async def list_platform_offer_decision_export_governance_snapshots(
    governance_record_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportGovernanceService(db).list_snapshots(governance_record_id=governance_record_id, snapshot_type=snapshot_type),
        "read_only": True,
    }
