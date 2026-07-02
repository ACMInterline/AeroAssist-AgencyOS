from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from auth import get_current_user
from database import Database, get_database
from models import PolicyCandidateMechanicsLinkCreate, ServiceMechanicsLookupRequest
from services.service_mechanics_service import ServiceMechanicsService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/service-mechanics", tags=["agency-service-mechanics"])

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


async def list_resource(
    resource: str,
    agency_id: str,
    db: Database,
    *,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = False,
) -> dict:
    return {
        "items": await ServiceMechanicsService(db).list_records(
            resource,
            agency_id=agency_id,
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            include_archived=include_archived,
        ),
        "read_only": resource != "candidate_mechanics_links",
        "agency_global_mutation_disabled": True,
    }


@router.get("/summary")
async def get_agency_service_mechanics_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    summary = await ServiceMechanicsService(db).summary(agency_id=agency_id)
    return {
        **summary,
        "platform_mechanics_read_only": True,
        "agency_global_mutation_disabled": True,
    }


@router.post("/lookup")
async def lookup_agency_service_mechanics(
    agency_id: str,
    payload: ServiceMechanicsLookupRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ServiceMechanicsService(db).lookup(**payload.model_dump(mode="json"), agency_id=agency_id)


@router.get("/communication-rules")
async def list_agency_communication_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("communication_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/ssr-osi-templates")
async def list_agency_ssr_osi_templates(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("ssr_osi_templates", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/requirements")
async def list_agency_requirements(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("requirements", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/status-recognition-rules")
async def list_agency_status_recognition_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("status_recognition_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/rejection-patterns")
async def list_agency_rejection_patterns(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("rejection_patterns", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/payment-rules")
async def list_agency_payment_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("payment_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/emd-issuance-rules")
async def list_agency_emd_issuance_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("emd_issuance_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/rfic-rfisc-mappings")
async def list_agency_rfic_rfisc_mappings(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("rfic_rfisc_mappings", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/emd-interline-rules")
async def list_agency_emd_interline_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("emd_interline_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/emd-lifecycle-rules")
async def list_agency_emd_lifecycle_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("emd_lifecycle_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/candidate-mechanics-links")
async def list_agency_candidate_mechanics_links(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("candidate_mechanics_links", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/candidate-mechanics-links", status_code=status.HTTP_201_CREATED)
async def create_agency_candidate_mechanics_link(
    agency_id: str,
    payload: PolicyCandidateMechanicsLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    link = await ServiceMechanicsService(db).create_record("candidate_mechanics_links", payload, user, agency_id=agency_id)
    return {
        "link": link,
        "agency_auto_promotion_disabled": True,
        "agency_global_mutation_disabled": True,
    }
