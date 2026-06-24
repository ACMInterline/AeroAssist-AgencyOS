from models import now_utc
from services.secret_service import check_secret, mask_secret_ref


PROVIDER_TYPES = ["manual", "email_smtp", "email_api", "portal", "object_storage", "webhook"]


async def delivery_provider_statuses(db, agency_id: str | None = None) -> list[dict]:
    settings = None
    if agency_id:
        settings = await db.collection("agency_email_settings").find_one({"agency_id": agency_id, "status": "active"})
    smtp_ref = (settings or {}).get("smtp_password_secret_ref")
    smtp_secret = check_secret(smtp_ref) if smtp_ref else None
    smtp_configured = bool(
        settings
        and settings.get("mode") == "smtp"
        and settings.get("smtp_host")
        and settings.get("smtp_port")
        and settings.get("smtp_username")
        and smtp_secret
        and smtp_secret.ok
    )
    statuses = [
        {
            "provider_type": "manual",
            "enabled": True,
            "configured": True,
            "mode": "manual",
            "last_checked_at": now_utc(),
            "warnings": ["Manual download/delivery tracking is the only active provider in Phase 25."],
        },
        {
            "provider_type": "email_smtp",
            "enabled": False,
            "configured": smtp_configured,
            "mode": "disabled",
            "last_checked_at": now_utc(),
            "warnings": [
                "Automatic SMTP sending is disabled in Phase 25.",
                "SMTP secret reference is masked." if smtp_ref else "SMTP secret reference is not configured.",
            ],
            "smtp_secret_ref_masked": mask_secret_ref(smtp_ref),
        },
    ]
    for provider_type in ["email_api", "portal", "object_storage", "webhook"]:
        statuses.append(
            {
                "provider_type": provider_type,
                "enabled": False,
                "configured": False,
                "mode": "not_configured",
                "last_checked_at": now_utc(),
                "warnings": [f"{provider_type.replace('_', ' ')} provider is not configured in Phase 25."],
            }
        )
    return statuses


async def delivery_provider_readiness(db, agency_id: str | None = None) -> dict:
    providers = await delivery_provider_statuses(db, agency_id)
    return {
        "automatic_delivery_enabled": False,
        "public_links_enabled": False,
        "object_storage_enabled": False,
        "providers": providers,
    }
