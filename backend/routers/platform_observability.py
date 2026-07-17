from fastapi import APIRouter, Depends

from auth import require_platform_role
from observability import operational_diagnostics_snapshot


router = APIRouter(
    prefix="/api/platform/diagnostics/observability",
    tags=["platform-observability"],
)


@router.get("")
async def get_observability_diagnostics(
    _user: dict = Depends(
        require_platform_role(["platform_owner", "platform_admin", "platform_support"])
    ),
) -> dict:
    return {
        "diagnostics": operational_diagnostics_snapshot(),
        "bounded_aggregates_only": True,
        "raw_logs_exposed": False,
        "environment_values_exposed": False,
        "sensitive_values_exposed": False,
    }

