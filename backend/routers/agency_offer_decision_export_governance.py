from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionExportArchiveStatusCreateRequest,
    OfferDecisionExportArchiveStatusUpdateRequest,
    OfferDecisionExportGovernanceExceptionCreateRequest,
    OfferDecisionExportGovernanceExceptionUpdateRequest,
    OfferDecisionExportGovernanceRecordCreateRequest,
    OfferDecisionExportGovernanceRecordUpdateRequest,
    OfferDecisionExportGovernanceRuleCreateRequest,
    OfferDecisionExportGovernanceRuleUpdateRequest,
    OfferDecisionExportGovernanceSnapshotCreateRequest,
    OfferDecisionExportLegalBasisCreateRequest,
    OfferDecisionExportLegalBasisUpdateRequest,
    OfferDecisionExportRetentionPolicyCreateRequest,
    OfferDecisionExportRetentionPolicyUpdateRequest,
)
from services.offer_decision_export_governance_service import OfferDecisionExportGovernanceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-export-governance", tags=["agency-offer-decision-export-governance"])

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
async def get_agency_offer_decision_export_governance_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportGovernanceService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.post("/governance-records", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_governance_record(
    agency_id: str,
    payload: OfferDecisionExportGovernanceRecordCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).create_record(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/governance-records")
async def list_agency_offer_decision_export_governance_records(
    agency_id: str,
    export_id: str | None = Query(default=None),
    audit_review_id: str | None = Query(default=None),
    governance_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportGovernanceService(db).list_records(agency_id=agency_id, export_id=export_id, audit_review_id=audit_review_id, governance_status=governance_status)}


@router.get("/governance-records/{record_id}")
async def get_agency_offer_decision_export_governance_record(
    agency_id: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportGovernanceService(db).get_record_detail(record_id, agency_id)
    if not detail:
        raise not_found("Governance record not found.")
    return detail


@router.patch("/governance-records/{record_id}")
async def update_agency_offer_decision_export_governance_record(
    agency_id: str,
    record_id: str,
    payload: OfferDecisionExportGovernanceRecordUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).update_record(agency_id, record_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/governance-records/{record_id}/rules", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_governance_rule(
    agency_id: str,
    record_id: str,
    payload: OfferDecisionExportGovernanceRuleCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).create_rule(agency_id, record_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/rules")
async def list_agency_offer_decision_export_governance_rules(
    agency_id: str,
    governance_record_id: str | None = Query(default=None),
    rule_status: str | None = Query(default=None, alias="status"),
    rule_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportGovernanceService(db).list_rules(agency_id=agency_id, governance_record_id=governance_record_id, rule_status=rule_status, rule_type=rule_type)}


@router.patch("/rules/{rule_id}")
async def update_agency_offer_decision_export_governance_rule(
    agency_id: str,
    rule_id: str,
    payload: OfferDecisionExportGovernanceRuleUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).update_rule(agency_id, rule_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/governance-records/{record_id}/retention-policies", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_retention_policy(
    agency_id: str,
    record_id: str,
    payload: OfferDecisionExportRetentionPolicyCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).create_retention_policy(agency_id, record_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/retention-policies")
async def list_agency_offer_decision_export_retention_policies(
    agency_id: str,
    governance_record_id: str | None = Query(default=None),
    retention_action: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportGovernanceService(db).list_retention_policies(agency_id=agency_id, governance_record_id=governance_record_id, retention_action=retention_action)}


@router.patch("/retention-policies/{policy_id}")
async def update_agency_offer_decision_export_retention_policy(
    agency_id: str,
    policy_id: str,
    payload: OfferDecisionExportRetentionPolicyUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).update_retention_policy(agency_id, policy_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/governance-records/{record_id}/legal-bases", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_legal_basis(
    agency_id: str,
    record_id: str,
    payload: OfferDecisionExportLegalBasisCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).create_legal_basis(agency_id, record_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/legal-bases")
async def list_agency_offer_decision_export_legal_bases(
    agency_id: str,
    governance_record_id: str | None = Query(default=None),
    basis_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportGovernanceService(db).list_legal_bases(agency_id=agency_id, governance_record_id=governance_record_id, basis_type=basis_type)}


@router.patch("/legal-bases/{basis_id}")
async def update_agency_offer_decision_export_legal_basis(
    agency_id: str,
    basis_id: str,
    payload: OfferDecisionExportLegalBasisUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).update_legal_basis(agency_id, basis_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/governance-records/{record_id}/archive-statuses", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_archive_status(
    agency_id: str,
    record_id: str,
    payload: OfferDecisionExportArchiveStatusCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).create_archive_status(agency_id, record_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/archive-statuses")
async def list_agency_offer_decision_export_archive_statuses(
    agency_id: str,
    governance_record_id: str | None = Query(default=None),
    archive_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportGovernanceService(db).list_archive_statuses(agency_id=agency_id, governance_record_id=governance_record_id, archive_status=archive_status)}


@router.patch("/archive-statuses/{status_id}")
async def update_agency_offer_decision_export_archive_status(
    agency_id: str,
    status_id: str,
    payload: OfferDecisionExportArchiveStatusUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).update_archive_status(agency_id, status_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/governance-records/{record_id}/governance-exceptions", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_governance_exception(
    agency_id: str,
    record_id: str,
    payload: OfferDecisionExportGovernanceExceptionCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).create_exception(agency_id, record_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/governance-exceptions")
async def list_agency_offer_decision_export_governance_exceptions(
    agency_id: str,
    governance_record_id: str | None = Query(default=None),
    exception_status: str | None = Query(default=None, alias="status"),
    exception_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportGovernanceService(db).list_exceptions(agency_id=agency_id, governance_record_id=governance_record_id, exception_status=exception_status, exception_type=exception_type)}


@router.patch("/governance-exceptions/{exception_id}")
async def update_agency_offer_decision_export_governance_exception(
    agency_id: str,
    exception_id: str,
    payload: OfferDecisionExportGovernanceExceptionUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).update_exception(agency_id, exception_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/governance-records/{record_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_governance_snapshot(
    agency_id: str,
    record_id: str,
    payload: OfferDecisionExportGovernanceSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportGovernanceService(db).create_snapshot(agency_id, record_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_agency_offer_decision_export_governance_snapshots(
    agency_id: str,
    governance_record_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportGovernanceService(db).list_snapshots(agency_id=agency_id, governance_record_id=governance_record_id, snapshot_type=snapshot_type)}
