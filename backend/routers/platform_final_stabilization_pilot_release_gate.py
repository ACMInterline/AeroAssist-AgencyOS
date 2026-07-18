from fastapi import APIRouter, Depends

from auth import require_platform_role
from config import get_settings
from models import PilotReleaseProductionEvidence
from services.final_stabilization_pilot_release_gate_service import (
    FinalStabilizationPilotReleaseGateService,
    foundation_evidence_summary,
    runtime_repository_evidence,
    sign_off_schema,
)


router = APIRouter(
    prefix="/api/platform/diagnostics/pilot-release-gate",
    tags=["platform-pilot-release-gate"],
)


def require_release_operator() -> object:
    return Depends(
        require_platform_role(["platform_owner", "platform_admin", "platform_support"])
    )


@router.get("")
async def get_pilot_release_gate(
    _user: dict = require_release_operator(),
) -> dict:
    assessment = FinalStabilizationPilotReleaseGateService().build_assessment(
        environment_scope="repository",
        machine_evidence=runtime_repository_evidence(),
    )
    return {
        "assessment": assessment.model_dump(mode="json"),
        "foundation_evidence": foundation_evidence_summary(get_settings()),
        "production_access_performed": False,
        "production_evidence_is_attestation": True,
        "bounded_metadata_only": True,
    }


@router.post("/assess")
async def assess_pilot_release_gate(
    evidence: PilotReleaseProductionEvidence,
    _user: dict = require_release_operator(),
) -> dict:
    assessment = FinalStabilizationPilotReleaseGateService().build_assessment(
        environment_scope="production",
        machine_evidence=runtime_repository_evidence(),
        production_evidence=evidence,
        git_commit=evidence.production_git_commit,
    )
    return {
        "assessment": assessment.model_dump(mode="json"),
        "production_evidence_is_attestation": True,
        "production_access_performed": False,
        "assessment_persisted": False,
        "bounded_metadata_only": True,
    }


@router.get("/sign-off-schema")
async def get_pilot_release_sign_off_schema(
    _user: dict = require_release_operator(),
) -> dict:
    return sign_off_schema()
