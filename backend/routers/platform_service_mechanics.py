from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineEmdInterlineRuleCreate,
    AirlineEmdInterlineRuleUpdate,
    AirlineEmdIssuanceRuleCreate,
    AirlineEmdIssuanceRuleUpdate,
    AirlineEmdLifecycleRuleCreate,
    AirlineEmdLifecycleRuleUpdate,
    AirlineRejectionPatternCreate,
    AirlineRejectionPatternUpdate,
    AirlineRficRfiscMappingCreate,
    AirlineRficRfiscMappingUpdate,
    AirlineServiceCommunicationRuleCreate,
    AirlineServiceCommunicationRuleUpdate,
    AirlineServicePaymentRuleCreate,
    AirlineServicePaymentRuleUpdate,
    PolicyCandidateMechanicsLinkCreate,
    PolicyCandidateMechanicsLinkUpdate,
    ServiceMechanicsLookupRequest,
    SsrOsiRequirementCreate,
    SsrOsiRequirementUpdate,
    SsrOsiTemplateCreate,
    SsrOsiTemplateUpdate,
    SsrStatusRecognitionRuleCreate,
    SsrStatusRecognitionRuleUpdate,
)
from services.service_mechanics_service import RESOURCE_SPECS, ServiceMechanicsService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/service-mechanics", tags=["platform-service-mechanics"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def response_key(resource: str) -> str:
    return RESOURCE_SPECS[resource]["singular"]


async def list_resource(
    resource: str,
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
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            include_archived=include_archived,
        )
    }


async def create_resource(resource: str, payload: Any, user: dict, db: Database) -> dict:
    record = await ServiceMechanicsService(db).create_record(resource, payload, user)
    return {response_key(resource): record}


async def update_resource(resource: str, record_id: str, payload: Any, db: Database) -> dict:
    record = await ServiceMechanicsService(db).update_record(resource, record_id, payload)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service mechanics record not found.")
    return {response_key(resource): record}


@router.get("/summary")
async def get_platform_service_mechanics_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ServiceMechanicsService(db).summary()


@router.post("/lookup")
async def lookup_platform_service_mechanics(
    payload: ServiceMechanicsLookupRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ServiceMechanicsService(db).lookup(**payload.model_dump(mode="json"))


@router.get("/communication-rules")
async def list_platform_communication_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("communication_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/communication-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_communication_rule(
    payload: AirlineServiceCommunicationRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("communication_rules", payload, user, db)


@router.patch("/communication-rules/{record_id}")
async def update_platform_communication_rule(
    record_id: str,
    payload: AirlineServiceCommunicationRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("communication_rules", record_id, payload, db)


@router.get("/ssr-osi-templates")
async def list_platform_ssr_osi_templates(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("ssr_osi_templates", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/ssr-osi-templates", status_code=status.HTTP_201_CREATED)
async def create_platform_ssr_osi_template(
    payload: SsrOsiTemplateCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("ssr_osi_templates", payload, user, db)


@router.patch("/ssr-osi-templates/{record_id}")
async def update_platform_ssr_osi_template(
    record_id: str,
    payload: SsrOsiTemplateUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("ssr_osi_templates", record_id, payload, db)


@router.get("/requirements")
async def list_platform_requirements(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("requirements", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/requirements", status_code=status.HTTP_201_CREATED)
async def create_platform_requirement(
    payload: SsrOsiRequirementCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("requirements", payload, user, db)


@router.patch("/requirements/{record_id}")
async def update_platform_requirement(
    record_id: str,
    payload: SsrOsiRequirementUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("requirements", record_id, payload, db)


@router.get("/status-recognition-rules")
async def list_platform_status_recognition_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("status_recognition_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/status-recognition-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_status_recognition_rule(
    payload: SsrStatusRecognitionRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("status_recognition_rules", payload, user, db)


@router.patch("/status-recognition-rules/{record_id}")
async def update_platform_status_recognition_rule(
    record_id: str,
    payload: SsrStatusRecognitionRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("status_recognition_rules", record_id, payload, db)


@router.get("/rejection-patterns")
async def list_platform_rejection_patterns(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("rejection_patterns", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/rejection-patterns", status_code=status.HTTP_201_CREATED)
async def create_platform_rejection_pattern(
    payload: AirlineRejectionPatternCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("rejection_patterns", payload, user, db)


@router.patch("/rejection-patterns/{record_id}")
async def update_platform_rejection_pattern(
    record_id: str,
    payload: AirlineRejectionPatternUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("rejection_patterns", record_id, payload, db)


@router.get("/payment-rules")
async def list_platform_payment_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("payment_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/payment-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_payment_rule(
    payload: AirlineServicePaymentRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("payment_rules", payload, user, db)


@router.patch("/payment-rules/{record_id}")
async def update_platform_payment_rule(
    record_id: str,
    payload: AirlineServicePaymentRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("payment_rules", record_id, payload, db)


@router.get("/emd-issuance-rules")
async def list_platform_emd_issuance_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("emd_issuance_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/emd-issuance-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_emd_issuance_rule(
    payload: AirlineEmdIssuanceRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("emd_issuance_rules", payload, user, db)


@router.patch("/emd-issuance-rules/{record_id}")
async def update_platform_emd_issuance_rule(
    record_id: str,
    payload: AirlineEmdIssuanceRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("emd_issuance_rules", record_id, payload, db)


@router.get("/rfic-rfisc-mappings")
async def list_platform_rfic_rfisc_mappings(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("rfic_rfisc_mappings", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/rfic-rfisc-mappings", status_code=status.HTTP_201_CREATED)
async def create_platform_rfic_rfisc_mapping(
    payload: AirlineRficRfiscMappingCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("rfic_rfisc_mappings", payload, user, db)


@router.patch("/rfic-rfisc-mappings/{record_id}")
async def update_platform_rfic_rfisc_mapping(
    record_id: str,
    payload: AirlineRficRfiscMappingUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("rfic_rfisc_mappings", record_id, payload, db)


@router.get("/emd-interline-rules")
async def list_platform_emd_interline_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("emd_interline_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/emd-interline-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_emd_interline_rule(
    payload: AirlineEmdInterlineRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("emd_interline_rules", payload, user, db)


@router.patch("/emd-interline-rules/{record_id}")
async def update_platform_emd_interline_rule(
    record_id: str,
    payload: AirlineEmdInterlineRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("emd_interline_rules", record_id, payload, db)


@router.get("/emd-lifecycle-rules")
async def list_platform_emd_lifecycle_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("emd_lifecycle_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/emd-lifecycle-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_emd_lifecycle_rule(
    payload: AirlineEmdLifecycleRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("emd_lifecycle_rules", payload, user, db)


@router.patch("/emd-lifecycle-rules/{record_id}")
async def update_platform_emd_lifecycle_rule(
    record_id: str,
    payload: AirlineEmdLifecycleRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("emd_lifecycle_rules", record_id, payload, db)


@router.get("/candidate-mechanics-links")
async def list_platform_candidate_mechanics_links(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("candidate_mechanics_links", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/candidate-mechanics-links", status_code=status.HTTP_201_CREATED)
async def create_platform_candidate_mechanics_link(
    payload: PolicyCandidateMechanicsLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("candidate_mechanics_links", payload, user, db)


@router.patch("/candidate-mechanics-links/{record_id}")
async def update_platform_candidate_mechanics_link(
    record_id: str,
    payload: PolicyCandidateMechanicsLinkUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("candidate_mechanics_links", record_id, payload, db)
