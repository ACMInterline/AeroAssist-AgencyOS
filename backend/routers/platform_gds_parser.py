from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import GdsParserEvaluationCreate, GdsParserVersionCreate, GdsParseTrainingSampleReview
from services.gds_parser_service import GdsParserService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/gds-parser", tags=["platform-gds-parser"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def filters_from(**kwargs: object) -> dict:
    return {key: value for key, value in kwargs.items() if value not in {None, ""}}


@router.get("/profiles")
async def list_platform_parser_profiles(
    provider_family: str | None = None,
    input_format: str | None = None,
    active: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await GdsParserService(db).list_parser_profiles(filters_from(provider_family=provider_family, input_format=input_format, active=active))


@router.post("/profiles/seed-defaults", status_code=status.HTTP_201_CREATED)
async def seed_parser_profiles(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await GdsParserService(db).seed_default_parser_profiles()


@router.get("/profiles/{profile_id}/versions")
async def list_platform_parser_versions(
    profile_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    profile = await GdsParserService(db).get_parser_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parser profile not found.")
    return await GdsParserService(db).list_parser_versions(profile_id)


@router.post("/profiles/{profile_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_platform_parser_version(
    profile_id: str,
    payload: GdsParserVersionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    result = await GdsParserService(db).create_parser_version(profile_id, payload, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parser profile not found.")
    return result


@router.post("/profiles/{profile_id}/versions/{version_id}/activate")
async def activate_platform_parser_version(
    profile_id: str,
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    result = await GdsParserService(db).activate_parser_version(profile_id, version_id, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parser profile or version not found.")
    return result


@router.get("/training-samples")
async def list_training_samples(
    scope: str | None = None,
    agency_id: str | None = None,
    provider_family: str | None = None,
    input_format: str | None = None,
    sample_status: str | None = None,
    difficulty: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await GdsParserService(db).list_training_samples(
        filters_from(
            scope=scope,
            agency_id=agency_id,
            provider_family=provider_family,
            input_format=input_format,
            sample_status=sample_status,
            difficulty=difficulty,
        )
    )


@router.post("/training-samples/{sample_id}/review")
async def review_training_sample(
    sample_id: str,
    payload: GdsParseTrainingSampleReview,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    result = await GdsParserService(db).review_training_sample(sample_id, payload, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training sample not found.")
    return result


@router.post("/evaluations", status_code=status.HTTP_201_CREATED)
async def create_parser_evaluation(
    payload: GdsParserEvaluationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await GdsParserService(db).evaluate_parser_version(payload, user)


@router.get("/evaluations")
async def list_parser_evaluations(
    parser_profile_id: str | None = None,
    parser_version_id: str | None = None,
    evaluation_status: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await GdsParserService(db).list_evaluation_runs(
        filters_from(parser_profile_id=parser_profile_id, parser_version_id=parser_version_id, evaluation_status=evaluation_status)
    )
