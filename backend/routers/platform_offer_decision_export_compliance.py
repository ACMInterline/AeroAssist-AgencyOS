from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_compliance_service import OfferDecisionExportComplianceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-export-compliance", tags=["platform-offer-decision-export-compliance"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_compliance_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportComplianceService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/diagnostics")
async def get_platform_offer_decision_export_compliance_diagnostics(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportComplianceService(db).summary(),
        "read_only": True,
    }


@router.get("/evidence")
async def list_platform_offer_decision_export_compliance_evidence(
    governance_record_id: str | None = Query(default=None),
    audit_review_id: str | None = Query(default=None),
    evidence_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportComplianceService(db).list_evidence(governance_record_id=governance_record_id, audit_review_id=audit_review_id, evidence_status=evidence_status),
        "read_only": True,
    }


@router.get("/evidence/{evidence_id}")
async def get_platform_offer_decision_export_compliance_evidence(
    evidence_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionExportComplianceService(db).get_evidence_detail(evidence_id)
    return {
        **(detail or {"evidence": None, "requirements": [], "checks": [], "results": [], "exceptions": [], "snapshots": []}),
        "read_only": True,
    }


@router.get("/requirements")
async def list_platform_offer_decision_export_compliance_requirements(
    evidence_id: str | None = Query(default=None),
    requirement_status: str | None = Query(default=None, alias="status"),
    requirement_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportComplianceService(db).list_requirements(evidence_id=evidence_id, requirement_status=requirement_status, requirement_type=requirement_type),
        "read_only": True,
    }


@router.get("/checks")
async def list_platform_offer_decision_export_compliance_checks(
    evidence_id: str | None = Query(default=None),
    requirement_id: str | None = Query(default=None),
    check_status: str | None = Query(default=None, alias="status"),
    check_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportComplianceService(db).list_checks(evidence_id=evidence_id, requirement_id=requirement_id, check_status=check_status, check_type=check_type),
        "read_only": True,
    }


@router.get("/results")
async def list_platform_offer_decision_export_compliance_results(
    evidence_id: str | None = Query(default=None),
    requirement_id: str | None = Query(default=None),
    check_id: str | None = Query(default=None),
    result_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportComplianceService(db).list_results(evidence_id=evidence_id, requirement_id=requirement_id, check_id=check_id, result_status=result_status),
        "read_only": True,
    }


@router.get("/exceptions")
async def list_platform_offer_decision_export_compliance_exceptions(
    evidence_id: str | None = Query(default=None),
    exception_status: str | None = Query(default=None, alias="status"),
    exception_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportComplianceService(db).list_exceptions(evidence_id=evidence_id, exception_status=exception_status, exception_type=exception_type),
        "read_only": True,
    }


@router.get("/snapshots")
async def list_platform_offer_decision_export_compliance_snapshots(
    evidence_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportComplianceService(db).list_snapshots(evidence_id=evidence_id, snapshot_type=snapshot_type),
        "read_only": True,
    }
