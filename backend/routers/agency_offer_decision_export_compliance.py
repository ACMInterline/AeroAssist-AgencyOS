from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionExportComplianceCheckCreateRequest,
    OfferDecisionExportComplianceCheckUpdateRequest,
    OfferDecisionExportComplianceEvidenceCreateRequest,
    OfferDecisionExportComplianceEvidenceUpdateRequest,
    OfferDecisionExportComplianceExceptionCreateRequest,
    OfferDecisionExportComplianceExceptionUpdateRequest,
    OfferDecisionExportComplianceRequirementCreateRequest,
    OfferDecisionExportComplianceRequirementUpdateRequest,
    OfferDecisionExportComplianceResultCreateRequest,
    OfferDecisionExportComplianceResultUpdateRequest,
    OfferDecisionExportComplianceSnapshotCreateRequest,
)
from services.offer_decision_export_compliance_service import OfferDecisionExportComplianceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-export-compliance", tags=["agency-offer-decision-export-compliance"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/summary")
async def get_agency_offer_decision_export_compliance_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportComplianceService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_compliance_evidence(
    agency_id: str,
    payload: OfferDecisionExportComplianceEvidenceCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).create_evidence(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/evidence")
async def list_agency_offer_decision_export_compliance_evidence(
    agency_id: str,
    governance_record_id: str | None = Query(default=None),
    audit_review_id: str | None = Query(default=None),
    evidence_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportComplianceService(db).list_evidence(agency_id=agency_id, governance_record_id=governance_record_id, audit_review_id=audit_review_id, evidence_status=evidence_status)}


@router.get("/evidence/{evidence_id}")
async def get_agency_offer_decision_export_compliance_evidence(
    agency_id: str,
    evidence_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportComplianceService(db).get_evidence_detail(evidence_id, agency_id)
    if not detail:
        raise not_found("Compliance evidence not found.")
    return detail


@router.patch("/evidence/{evidence_id}")
async def update_agency_offer_decision_export_compliance_evidence(
    agency_id: str,
    evidence_id: str,
    payload: OfferDecisionExportComplianceEvidenceUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).update_evidence(agency_id, evidence_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/evidence/{evidence_id}/requirements", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_compliance_requirement(
    agency_id: str,
    evidence_id: str,
    payload: OfferDecisionExportComplianceRequirementCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).create_requirement(agency_id, evidence_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/requirements")
async def list_agency_offer_decision_export_compliance_requirements(
    agency_id: str,
    evidence_id: str | None = Query(default=None),
    requirement_status: str | None = Query(default=None, alias="status"),
    requirement_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportComplianceService(db).list_requirements(agency_id=agency_id, evidence_id=evidence_id, requirement_status=requirement_status, requirement_type=requirement_type)}


@router.patch("/requirements/{requirement_id}")
async def update_agency_offer_decision_export_compliance_requirement(
    agency_id: str,
    requirement_id: str,
    payload: OfferDecisionExportComplianceRequirementUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).update_requirement(agency_id, requirement_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/evidence/{evidence_id}/checks", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_compliance_check(
    agency_id: str,
    evidence_id: str,
    payload: OfferDecisionExportComplianceCheckCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).create_check(agency_id, evidence_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/checks")
async def list_agency_offer_decision_export_compliance_checks(
    agency_id: str,
    evidence_id: str | None = Query(default=None),
    requirement_id: str | None = Query(default=None),
    check_status: str | None = Query(default=None, alias="status"),
    check_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportComplianceService(db).list_checks(agency_id=agency_id, evidence_id=evidence_id, requirement_id=requirement_id, check_status=check_status, check_type=check_type)}


@router.patch("/checks/{check_id}")
async def update_agency_offer_decision_export_compliance_check(
    agency_id: str,
    check_id: str,
    payload: OfferDecisionExportComplianceCheckUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).update_check(agency_id, check_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/evidence/{evidence_id}/results", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_compliance_result(
    agency_id: str,
    evidence_id: str,
    payload: OfferDecisionExportComplianceResultCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).create_result(agency_id, evidence_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/results")
async def list_agency_offer_decision_export_compliance_results(
    agency_id: str,
    evidence_id: str | None = Query(default=None),
    requirement_id: str | None = Query(default=None),
    check_id: str | None = Query(default=None),
    result_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportComplianceService(db).list_results(agency_id=agency_id, evidence_id=evidence_id, requirement_id=requirement_id, check_id=check_id, result_status=result_status)}


@router.patch("/results/{result_id}")
async def update_agency_offer_decision_export_compliance_result(
    agency_id: str,
    result_id: str,
    payload: OfferDecisionExportComplianceResultUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).update_result(agency_id, result_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/evidence/{evidence_id}/exceptions", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_compliance_exception(
    agency_id: str,
    evidence_id: str,
    payload: OfferDecisionExportComplianceExceptionCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).create_exception(agency_id, evidence_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/exceptions")
async def list_agency_offer_decision_export_compliance_exceptions(
    agency_id: str,
    evidence_id: str | None = Query(default=None),
    exception_status: str | None = Query(default=None, alias="status"),
    exception_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportComplianceService(db).list_exceptions(agency_id=agency_id, evidence_id=evidence_id, exception_status=exception_status, exception_type=exception_type)}


@router.patch("/exceptions/{exception_id}")
async def update_agency_offer_decision_export_compliance_exception(
    agency_id: str,
    exception_id: str,
    payload: OfferDecisionExportComplianceExceptionUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).update_exception(agency_id, exception_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/evidence/{evidence_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_compliance_snapshot(
    agency_id: str,
    evidence_id: str,
    payload: OfferDecisionExportComplianceSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportComplianceService(db).create_snapshot(agency_id, evidence_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_agency_offer_decision_export_compliance_snapshots(
    agency_id: str,
    evidence_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportComplianceService(db).list_snapshots(agency_id=agency_id, evidence_id=evidence_id, snapshot_type=snapshot_type)}
