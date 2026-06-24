import base64
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_agency_context, get_current_user, require_platform_role
from config import get_settings as get_app_settings
from database import Database, get_database
from models import (
    Agency,
    AgencyBrandingSettings,
    AgencyBrandingSettingsUpdate,
    AgencyCreate,
    AgencyLogoUpload,
    AgencyStaffCreate,
    AgencyStaffMembership,
    AgencyUpdate,
    AgencyWorkspace,
    AgencyWorkspaceCreate,
    AgencyWorkspaceUpdate,
    AuditEvent,
    Invitation,
    PortalActionProcessSubmit,
    PlatformUser,
    StaffInvitationCreate,
    now_utc,
)
from security import hash_token, new_raw_token, normalize_email
from services.tenant_service import require_any_agency_role

router = APIRouter(prefix="/api/agencies", tags=["agencies"])

SAFE_STAFF_INVITE_ROLES = {"agency_admin", "agency_agent", "agency_accountant", "agency_readonly"}
AGENCY_ADMIN_INVITE_ROLES = {"agency_agent", "agency_accountant", "agency_readonly"}
BRANDING_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
BRANDING_WRITE_ROLES = ["agency_owner", "agency_admin"]
MAX_LOGO_BYTES = 2 * 1024 * 1024
SAFE_LOGO_TYPES = {"image/png", "image/jpeg", "image/webp"}

FONT_OPTIONS = {
    "inter": {"label": "Inter", "stack": "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"},
    "quicksand": {"label": "Quicksand", "stack": "Quicksand, Trebuchet MS, ui-sans-serif, system-ui, sans-serif"},
    "manrope": {"label": "Manrope", "stack": "Manrope, ui-sans-serif, system-ui, sans-serif"},
    "nunito_sans": {"label": "Nunito Sans", "stack": "Nunito Sans, ui-sans-serif, system-ui, sans-serif"},
    "lato": {"label": "Lato", "stack": "Lato, ui-sans-serif, system-ui, sans-serif"},
    "source_sans_3": {"label": "Source Sans 3", "stack": "Source Sans 3, Source Sans Pro, ui-sans-serif, system-ui, sans-serif"},
    "ibm_plex_sans": {"label": "IBM Plex Sans", "stack": "IBM Plex Sans, ui-sans-serif, system-ui, sans-serif"},
    "plus_jakarta_sans": {"label": "Plus Jakarta Sans", "stack": "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"},
    "roboto": {"label": "Roboto", "stack": "Roboto, ui-sans-serif, system-ui, sans-serif"},
    "system_ui": {"label": "System UI", "stack": "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"},
}

RADIUS_OPTIONS = {
    "square": "0px",
    "subtle": "6px",
    "rounded": "12px",
    "soft": "18px",
    "pill": "999px",
}

PALETTE_OPTIONS = {
    "aero_blue": {"label": "Aero Blue", "light": {"primary": "#2563eb", "primary_contrast": "#ffffff", "accent": "#38bdf8", "background": "#f8fafc", "surface": "#ffffff", "border": "#dbe3ef", "muted_background": "#eff6ff", "muted_text": "#475569", "success": "#16a34a", "warning": "#d97706", "danger": "#dc2626"}, "dark": {"primary": "#60a5fa", "primary_contrast": "#0f172a", "accent": "#22d3ee", "background": "#020617", "surface": "#0f172a", "border": "#1e293b", "muted_background": "#172554", "muted_text": "#cbd5e1", "success": "#4ade80", "warning": "#fbbf24", "danger": "#f87171"}},
    "midnight_navy": {"label": "Midnight Navy", "light": {"primary": "#1e3a8a", "primary_contrast": "#ffffff", "accent": "#0ea5e9", "background": "#f8fafc", "surface": "#ffffff", "border": "#cbd5e1", "muted_background": "#e0f2fe", "muted_text": "#334155", "success": "#15803d", "warning": "#b45309", "danger": "#b91c1c"}, "dark": {"primary": "#93c5fd", "primary_contrast": "#020617", "accent": "#38bdf8", "background": "#020617", "surface": "#0b1120", "border": "#1e3a8a", "muted_background": "#172554", "muted_text": "#bfdbfe", "success": "#22c55e", "warning": "#f59e0b", "danger": "#ef4444"}},
    "graphite": {"label": "Graphite", "light": {"primary": "#374151", "primary_contrast": "#ffffff", "accent": "#64748b", "background": "#f9fafb", "surface": "#ffffff", "border": "#d1d5db", "muted_background": "#f3f4f6", "muted_text": "#4b5563", "success": "#15803d", "warning": "#b45309", "danger": "#b91c1c"}, "dark": {"primary": "#d1d5db", "primary_contrast": "#111827", "accent": "#94a3b8", "background": "#111827", "surface": "#1f2937", "border": "#374151", "muted_background": "#111827", "muted_text": "#d1d5db", "success": "#4ade80", "warning": "#fbbf24", "danger": "#f87171"}},
    "emerald_aviation": {"label": "Emerald Aviation", "light": {"primary": "#047857", "primary_contrast": "#ffffff", "accent": "#10b981", "background": "#f0fdf4", "surface": "#ffffff", "border": "#bbf7d0", "muted_background": "#dcfce7", "muted_text": "#166534", "success": "#16a34a", "warning": "#ca8a04", "danger": "#dc2626"}, "dark": {"primary": "#6ee7b7", "primary_contrast": "#052e16", "accent": "#34d399", "background": "#022c22", "surface": "#064e3b", "border": "#047857", "muted_background": "#065f46", "muted_text": "#bbf7d0", "success": "#86efac", "warning": "#fde047", "danger": "#fca5a5"}},
    "sky_cyan": {"label": "Sky Cyan", "light": {"primary": "#0891b2", "primary_contrast": "#ffffff", "accent": "#06b6d4", "background": "#ecfeff", "surface": "#ffffff", "border": "#a5f3fc", "muted_background": "#cffafe", "muted_text": "#155e75", "success": "#16a34a", "warning": "#d97706", "danger": "#dc2626"}, "dark": {"primary": "#67e8f9", "primary_contrast": "#083344", "accent": "#22d3ee", "background": "#083344", "surface": "#164e63", "border": "#0e7490", "muted_background": "#155e75", "muted_text": "#cffafe", "success": "#4ade80", "warning": "#facc15", "danger": "#f87171"}},
    "violet_premium": {"label": "Violet Premium", "light": {"primary": "#7c3aed", "primary_contrast": "#ffffff", "accent": "#a855f7", "background": "#faf5ff", "surface": "#ffffff", "border": "#e9d5ff", "muted_background": "#f3e8ff", "muted_text": "#6b21a8", "success": "#16a34a", "warning": "#d97706", "danger": "#dc2626"}, "dark": {"primary": "#c4b5fd", "primary_contrast": "#2e1065", "accent": "#d8b4fe", "background": "#1e1b4b", "surface": "#312e81", "border": "#6d28d9", "muted_background": "#4c1d95", "muted_text": "#ddd6fe", "success": "#4ade80", "warning": "#fbbf24", "danger": "#f87171"}},
    "burgundy_executive": {"label": "Burgundy Executive", "light": {"primary": "#9f1239", "primary_contrast": "#ffffff", "accent": "#e11d48", "background": "#fff1f2", "surface": "#ffffff", "border": "#fecdd3", "muted_background": "#ffe4e6", "muted_text": "#881337", "success": "#15803d", "warning": "#b45309", "danger": "#be123c"}, "dark": {"primary": "#fb7185", "primary_contrast": "#4c0519", "accent": "#f43f5e", "background": "#4c0519", "surface": "#881337", "border": "#be123c", "muted_background": "#9f1239", "muted_text": "#ffe4e6", "success": "#86efac", "warning": "#fde68a", "danger": "#fda4af"}},
    "sandstone": {"label": "Sandstone", "light": {"primary": "#a16207", "primary_contrast": "#ffffff", "accent": "#d97706", "background": "#fffbeb", "surface": "#ffffff", "border": "#fde68a", "muted_background": "#fef3c7", "muted_text": "#92400e", "success": "#15803d", "warning": "#b45309", "danger": "#b91c1c"}, "dark": {"primary": "#fbbf24", "primary_contrast": "#451a03", "accent": "#f59e0b", "background": "#292524", "surface": "#44403c", "border": "#78350f", "muted_background": "#451a03", "muted_text": "#fde68a", "success": "#4ade80", "warning": "#facc15", "danger": "#f87171"}},
    "slate_minimal": {"label": "Slate Minimal", "light": {"primary": "#0f172a", "primary_contrast": "#ffffff", "accent": "#475569", "background": "#f8fafc", "surface": "#ffffff", "border": "#e2e8f0", "muted_background": "#f1f5f9", "muted_text": "#64748b", "success": "#16a34a", "warning": "#d97706", "danger": "#dc2626"}, "dark": {"primary": "#f8fafc", "primary_contrast": "#0f172a", "accent": "#94a3b8", "background": "#020617", "surface": "#0f172a", "border": "#334155", "muted_background": "#1e293b", "muted_text": "#cbd5e1", "success": "#4ade80", "warning": "#fbbf24", "danger": "#f87171"}},
    "black_glass": {"label": "Black Glass", "light": {"primary": "#111827", "primary_contrast": "#ffffff", "accent": "#0ea5e9", "background": "#f8fafc", "surface": "#ffffff", "border": "#cbd5e1", "muted_background": "#f1f5f9", "muted_text": "#475569", "success": "#16a34a", "warning": "#d97706", "danger": "#dc2626"}, "dark": {"primary": "#ffffff", "primary_contrast": "#000000", "accent": "#38bdf8", "background": "#000000", "surface": "#0a0a0a", "border": "#262626", "muted_background": "#171717", "muted_text": "#d4d4d4", "success": "#22c55e", "warning": "#f59e0b", "danger": "#ef4444"}},
}


def clean_updates(payload: AgencyUpdate | AgencyWorkspaceUpdate | AgencyBrandingSettingsUpdate) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


async def write_audit(
    db: Database,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    actor_user_id: str | None = None,
    agency_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


def parse_dt(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return now_utc()


def safe_invitation(invitation: dict) -> dict:
    blocked = {"token_hash"}
    return {key: value for key, value in invitation.items() if key not in blocked}


def branding_design_options() -> dict:
    return {
        "fonts": FONT_OPTIONS,
        "corner_radii": RADIUS_OPTIONS,
        "density": {
            "compact": {"label": "Compact", "spacing": "0.75"},
            "comfortable": {"label": "Comfortable", "spacing": "1"},
            "spacious": {"label": "Spacious", "spacing": "1.2"},
        },
        "theme_modes": ["light", "dark", "system"],
        "palettes": PALETTE_OPTIONS,
        "field_styles": ["outline", "filled", "soft_glass"],
        "button_styles": ["solid", "soft", "outline"],
        "calendar_styles": ["native_polished", "compact", "card"],
        "card_styles": ["flat", "raised", "outline"],
    }


def computed_branding_theme(branding: dict) -> dict:
    font_key = branding.get("font_family_key") or "inter"
    radius_key = branding.get("corner_radius_key") or "rounded"
    palette_key = branding.get("color_palette_key") or "aero_blue"
    palette = PALETTE_OPTIONS.get(palette_key, PALETTE_OPTIONS["aero_blue"])
    return {
        "font_stack": FONT_OPTIONS.get(font_key, FONT_OPTIONS["inter"])["stack"],
        "corner_radius": RADIUS_OPTIONS.get(radius_key, RADIUS_OPTIONS["rounded"]),
        "palette": palette,
        "theme_mode": branding.get("theme_mode") or "light",
        "density_key": branding.get("density_key") or "comfortable",
        "field_style_key": branding.get("field_style_key") or "outline",
        "button_style_key": branding.get("button_style_key") or "solid",
        "calendar_style_key": branding.get("calendar_style_key") or "native_polished",
        "card_style_key": branding.get("card_style_key") or "outline",
    }


def default_branding_settings(agency: dict, workspace: dict | None = None) -> dict:
    defaults = AgencyBrandingSettings(
        agency_id=agency["id"],
        workspace_id=workspace.get("id") if workspace else None,
        brand_name=(workspace or {}).get("brand_name") or agency.get("name"),
    )
    return defaults.model_dump(mode="json")


def branding_response(branding: dict, include_options: bool = True) -> dict:
    payload = {
        "branding": branding,
        "computed_theme": computed_branding_theme(branding),
        "logo_configured": bool(branding.get("logo_storage_record_id") and branding.get("logo_url")),
    }
    if include_options:
        payload["design_options"] = branding_design_options()
    return payload


async def load_branding_or_default(db: Database, agency_id: str) -> dict:
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
    branding = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    if branding:
        return branding
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id})
    return default_branding_settings(agency, workspace)


async def require_branding_read(db: Database, agency_id: str, user: dict) -> dict:
    if user.get("global_role") == "platform_support":
        agency = await db.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
        return {"agency_role": "platform_support", "agency_id": agency_id, "user_id": user["id"]}
    return await require_any_agency_role(db, agency_id, user, BRANDING_READ_ROLES)


async def require_branding_write(db: Database, agency_id: str, user: dict) -> dict:
    return await require_any_agency_role(db, agency_id, user, BRANDING_WRITE_ROLES)


def accept_url(raw_token: str) -> str:
    base_url = str(get_app_settings().public_app_url or "").rstrip("/")
    path = f"/invite/accept?token={raw_token}"
    return f"{base_url}{path}" if base_url else path


async def require_staff_invitation_permission(db: Database, agency_id: str, user: dict, target_role: str) -> dict:
    membership = await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    if target_role not in SAFE_STAFF_INVITE_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role cannot be invited through this flow.")
    if user.get("global_role") in {"platform_owner", "platform_admin"}:
        return membership
    if membership.get("agency_role") == "agency_admin" and target_role not in AGENCY_ADMIN_INVITE_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agency admins cannot invite equal or higher roles.")
    return membership


@router.get("")
async def list_agencies(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    if user.get("global_role") in {"platform_owner", "platform_admin", "platform_support"}:
        agencies = await db.collection("agencies").find_many()
    else:
        memberships = await db.collection("agency_staff_memberships").find_many({"user_id": user["id"], "status": "active"})
        agency_ids = {membership["agency_id"] for membership in memberships}
        agencies = [
            agency
            for agency in await db.collection("agencies").find_many()
            if agency["id"] in agency_ids
        ]
    workspace_counts = {}
    staff_counts = {}
    for workspace in await db.collection("agency_workspaces").find_many():
        workspace_counts[workspace["agency_id"]] = workspace_counts.get(workspace["agency_id"], 0) + 1
    for membership in await db.collection("agency_staff_memberships").find_many():
        staff_counts[membership["agency_id"]] = staff_counts.get(membership["agency_id"], 0) + 1
    return {
        "items": [
            {
                **agency,
                "workspace_count": workspace_counts.get(agency["id"], 0),
                "staff_membership_count": staff_counts.get(agency["id"], 0),
            }
            for agency in agencies
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency(
    payload: AgencyCreate,
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    if not payload.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency name is required.")
    if not payload.legal_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency legal name is required.")
    if not payload.default_currency.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Default currency is required.")
    if not payload.country.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Country is required.")
    if not payload.timezone.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timezone is required.")

    existing = await db.collection("agencies").find_one({"slug": payload.slug})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agency slug already exists.")
    existing_names = await db.collection("agencies").find_many()
    if any(normalize_name(agency.get("name", "")) == normalize_name(payload.name) for agency in existing_names):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agency name already exists.")

    agency = Agency(**payload.model_dump(mode="json"))
    agency_doc = await db.collection("agencies").insert_one(agency.model_dump(mode="json"))
    await write_audit(
        db,
        event_type="agency.created",
        entity_type="agency",
        entity_id=agency.id,
        summary=f"Created agency {agency.name}.",
        actor_user_id=user["id"],
        agency_id=agency.id,
    )
    return {"agency": agency_doc}


@router.get("/{agency_id}")
async def get_agency(context: dict = Depends(get_current_agency_context), db: Database = Depends(get_database)) -> dict:
    workspaces = await db.collection("agency_workspaces").find_many({"agency_id": context["agency"]["id"]})
    memberships = await db.collection("agency_staff_memberships").find_many({"agency_id": context["agency"]["id"]})
    return {
        "agency": {
            **context["agency"],
            "workspace_count": len(workspaces),
            "staff_membership_count": len(memberships),
        },
        "membership": context["membership"],
    }


@router.put("/{agency_id}")
async def update_agency(
    agency_id: str,
    payload: AgencyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])

    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    if "name" in updates and not str(updates["name"]).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency name is required.")
    if "legal_name" in updates and not str(updates["legal_name"]).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency legal name is required.")
    if "slug" in updates:
        existing_slug = await db.collection("agencies").find_one({"slug": updates["slug"]})
        if existing_slug and existing_slug["id"] != agency_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agency slug already exists.")
    if "name" in updates:
        existing_names = await db.collection("agencies").find_many()
        if any(agency["id"] != agency_id and normalize_name(agency.get("name", "")) == normalize_name(updates["name"]) for agency in existing_names):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agency name already exists.")

    agency = await db.collection("agencies").update_one({"id": agency_id}, updates)
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
    await write_audit(
        db,
        event_type="agency.updated",
        entity_type="agency",
        entity_id=agency_id,
        summary="Updated agency profile.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"fields": sorted(updates.keys())},
    )
    return {"agency": agency}


@router.get("/{agency_id}/branding")
async def get_branding_settings(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_branding_read(db, agency_id, user)
    branding = await load_branding_or_default(db, agency_id)
    return branding_response(branding)


@router.put("/{agency_id}/branding")
async def update_branding_settings(
    agency_id: str,
    payload: AgencyBrandingSettingsUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_branding_write(db, agency_id, user)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No branding fields provided.")
    if "brand_name" in updates and updates["brand_name"] is not None and not str(updates["brand_name"]).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brand name cannot be blank.")
    if updates.get("workspace_id"):
        workspace = await db.collection("agency_workspaces").find_one(
            {"agency_id": agency_id, "id": updates["workspace_id"]}
        )
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace must belong to the agency.")

    existing = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    audit_metadata = {
        "fields": sorted(updates.keys()),
        "allowed_configuration_only": True,
        "custom_css_allowed": False,
    }
    updates.update(
        {
            "updated_by_user_id": user["id"],
            "updated_by_email": user.get("email"),
            "audit_metadata": audit_metadata,
        }
    )
    if existing:
        branding = await db.collection("agency_branding_settings").update_one({"id": existing["id"]}, updates)
    else:
        agency = await db.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
        branding_model = AgencyBrandingSettings(agency_id=agency_id, **updates)
        branding = await db.collection("agency_branding_settings").insert_one(branding_model.model_dump(mode="json"))

    await write_audit(
        db,
        event_type="agency_branding_updated",
        entity_type="agency_branding_settings",
        entity_id=branding["id"],
        summary="Updated agency branding settings.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata=audit_metadata,
    )
    return branding_response(branding)


@router.post("/{agency_id}/branding/reset")
async def reset_branding_settings(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_branding_write(db, agency_id, user)
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id})
    existing = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    defaults = default_branding_settings(agency, workspace)
    reset_fields = {
        key: value
        for key, value in defaults.items()
        if key not in {"id", "created_at", "updated_at", "agency_id", "logo_storage_record_id", "logo_url"}
    }
    reset_fields.update(
        {
            "logo_storage_record_id": None,
            "logo_url": None,
            "updated_by_user_id": user["id"],
            "updated_by_email": user.get("email"),
            "audit_metadata": {"reset_to_defaults": True, "logo_removed": bool(existing and existing.get("logo_url"))},
        }
    )
    if existing:
        branding = await db.collection("agency_branding_settings").update_one({"id": existing["id"]}, reset_fields)
    else:
        branding = await db.collection("agency_branding_settings").insert_one(
            AgencyBrandingSettings(agency_id=agency_id, **reset_fields).model_dump(mode="json")
        )
    await write_audit(
        db,
        event_type="agency_theme_reset",
        entity_type="agency_branding_settings",
        entity_id=branding["id"],
        summary="Reset agency branding to controlled defaults.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"reset_to_defaults": True},
    )
    return branding_response(branding)


@router.post("/{agency_id}/branding/logo")
async def upload_branding_logo(
    agency_id: str,
    payload: AgencyLogoUpload,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_branding_write(db, agency_id, user)
    if payload.content_type not in SAFE_LOGO_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo must be PNG, JPEG, or WEBP. SVG is not accepted.")
    try:
        logo_bytes = base64.b64decode(payload.data_base64, validate=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo data must be valid base64.") from exc
    if not logo_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo file is empty.")
    if len(logo_bytes) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo file must be 2MB or smaller.")

    existing = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    if not existing:
        agency = await db.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
        existing = await db.collection("agency_branding_settings").insert_one(
            AgencyBrandingSettings(agency_id=agency_id, brand_name=agency.get("name")).model_dump(mode="json")
        )
    asset = await db.collection("agency_branding_assets").insert_one(
        {
            "id": f"brand_asset_{now_utc().strftime('%Y%m%d%H%M%S%f')}",
            "agency_id": agency_id,
            "branding_settings_id": existing["id"],
            "filename": payload.filename,
            "content_type": payload.content_type,
            "size_bytes": len(logo_bytes),
            "data_base64": payload.data_base64,
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "created_by_user_id": user["id"],
            "created_by_email": user.get("email"),
            "public": False,
        }
    )
    branding = await db.collection("agency_branding_settings").update_one(
        {"id": existing["id"]},
        {
            "logo_storage_record_id": asset["id"],
            "logo_url": f"data:{payload.content_type};base64,{payload.data_base64}",
            "updated_by_user_id": user["id"],
            "updated_by_email": user.get("email"),
            "audit_metadata": {"logo_content_type": payload.content_type, "logo_size_bytes": len(logo_bytes), "public": False},
        },
    )
    await write_audit(
        db,
        event_type="agency_logo_uploaded",
        entity_type="agency_branding_asset",
        entity_id=asset["id"],
        summary="Uploaded agency branding logo.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"content_type": payload.content_type, "size_bytes": len(logo_bytes), "public": False},
    )
    return branding_response(branding)


@router.delete("/{agency_id}/branding/logo")
async def remove_branding_logo(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_branding_write(db, agency_id, user)
    existing = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    if not existing:
        branding = await load_branding_or_default(db, agency_id)
        return branding_response(branding)
    branding = await db.collection("agency_branding_settings").update_one(
        {"id": existing["id"]},
        {
            "logo_storage_record_id": None,
            "logo_url": None,
            "updated_by_user_id": user["id"],
            "updated_by_email": user.get("email"),
            "audit_metadata": {"logo_removed": True},
        },
    )
    await write_audit(
        db,
        event_type="agency_logo_removed",
        entity_type="agency_branding_settings",
        entity_id=branding["id"],
        summary="Removed agency branding logo.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"previous_logo_storage_record_id": existing.get("logo_storage_record_id")},
    )
    return branding_response(branding)


@router.get("/{agency_id}/settings")
async def get_settings(context: dict = Depends(get_current_agency_context), db: Database = Depends(get_database)) -> dict:
    settings = await db.collection("agency_workspaces").find_one({"agency_id": context["agency"]["id"]})
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency settings not found.")
    return {"settings": settings}


@router.get("/{agency_id}/workspaces")
async def list_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(
        db,
        agency_id,
        user,
        ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"],
    )
    return {"items": await db.collection("agency_workspaces").find_many({"agency_id": agency_id})}


@router.post("/{agency_id}/workspaces", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    agency_id: str,
    payload: AgencyWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
    if not payload.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace name is required.")
    if not payload.default_currency.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Default currency is required.")
    if not payload.timezone.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timezone is required.")
    workspaces = await db.collection("agency_workspaces").find_many({"agency_id": agency_id})
    if any(normalize_name(workspace.get("name") or workspace.get("brand_name", "")) == normalize_name(payload.name) for workspace in workspaces):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workspace name already exists for this agency.")

    workspace = AgencyWorkspace(
        agency_id=agency_id,
        name=payload.name,
        brand_name=payload.brand_name or payload.name,
        status=payload.status,
        default_currency=payload.default_currency,
        timezone=payload.timezone,
    )
    workspace_doc = await db.collection("agency_workspaces").insert_one(workspace.model_dump(mode="json"))

    existing_membership = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": user["id"]}
    )
    owner_membership = existing_membership
    if user.get("global_role") in {"platform_owner", "platform_admin"} and existing_membership is None:
        owner_membership = await db.collection("agency_staff_memberships").insert_one(
            AgencyStaffMembership(
                agency_id=agency_id,
                user_id=user["id"],
                agency_role="agency_owner",
                status="active",
                joined_at=now_utc(),
            ).model_dump(mode="json")
        )

    await write_audit(
        db,
        event_type="agency.workspace_created",
        entity_type="agency_workspace",
        entity_id=workspace.id,
        summary=f"Created workspace {workspace.name}.",
        actor_user_id=user["id"],
        agency_id=agency_id,
    )
    return {"workspace": workspace_doc, "owner_membership": owner_membership}


@router.put("/{agency_id}/settings")
async def update_settings(
    agency_id: str,
    payload: AgencyWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")

    settings = await db.collection("agency_workspaces").update_one({"agency_id": agency_id}, updates)
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency settings not found.")
    await write_audit(
        db,
        event_type="agency.settings_updated",
        entity_type="agency_workspace",
        entity_id=settings["id"],
        summary="Updated agency workspace settings.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"fields": sorted(updates.keys())},
    )
    return {"settings": settings}


@router.get("/{agency_id}/staff")
async def list_staff(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(
        db,
        agency_id,
        user,
        ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"],
    )
    memberships = await db.collection("agency_staff_memberships").find_many({"agency_id": agency_id})
    users_by_id = {
        staff_user["id"]: staff_user
        for staff_user in await db.collection("platform_users").find_many()
    }
    return {
        "items": [
            {"membership": membership, "user": users_by_id.get(membership["user_id"])}
            for membership in memberships
        ]
    }


@router.post("/{agency_id}/staff/invitations", status_code=status.HTTP_201_CREATED)
async def create_staff_invitation(
    agency_id: str,
    payload: StaffInvitationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    target_role = str(payload.agency_role)
    await require_staff_invitation_permission(db, agency_id, user, target_role)
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")

    if payload.workspace_id:
        workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id, "id": payload.workspace_id})
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace must belong to the agency.")

    normalized = normalize_email(str(payload.email))
    existing_identity = await db.collection("auth_identities").find_one({"normalized_email": normalized})
    existing_user = await db.collection("platform_users").find_one({"email": normalized})
    if existing_user:
        existing_membership = await db.collection("agency_staff_memberships").find_one(
            {"agency_id": agency_id, "user_id": existing_user["id"]}
        )
        if existing_membership and existing_membership.get("status") == "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active staff membership already exists.")

    pending_invitation = await db.collection("invitations").find_one(
        {
            "agency_id": agency_id,
            "workspace_id": payload.workspace_id,
            "normalized_email": normalized,
            "target_role": target_role,
            "invitation_type": "agency_staff",
            "status": "pending",
        }
    )
    if pending_invitation:
        expires_at = parse_dt(pending_invitation["expires_at"])
        if expires_at > now_utc():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A pending invitation already exists for this email, workspace, and role.")
        await db.collection("invitations").update_one(
            {"id": pending_invitation["id"]},
            {"status": "expired"},
        )

    raw_token = new_raw_token()
    invited_name = payload.invited_name or payload.full_name
    invitation = Invitation(
        agency_id=agency_id,
        workspace_id=payload.workspace_id,
        invited_email=normalized,
        invited_name=invited_name,
        normalized_email=normalized,
        invitation_type="agency_staff",
        target_role=target_role,
        target_user_id=existing_user["id"] if existing_user else None,
        invited_by_user_id=user["id"],
        token_hash=hash_token(raw_token),
        expires_at=now_utc() + timedelta(hours=get_app_settings().invitation_expiry_hours),
    )
    invitation_doc = await db.collection("invitations").insert_one(invitation.model_dump(mode="json"))
    await write_audit(
        db,
        event_type="invitation_created",
        entity_type="invitation",
        entity_id=invitation.id,
        summary=f"Prepared staff invitation for {normalized}.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={
            "agency_role": target_role,
            "workspace_id": payload.workspace_id,
            "existing_identity": bool(existing_identity),
        },
    )
    return {
        "invitation": safe_invitation(invitation_doc),
        "one_time_token": raw_token,
        "accept_url": accept_url(raw_token),
        "delivery": {"automatic_email_sent": False, "manual_delivery_required": True},
    }


@router.get("/{agency_id}/staff/invitations")
async def list_staff_invitations(
    agency_id: str,
    workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    filters = {"agency_id": agency_id, "invitation_type": "agency_staff"}
    if workspace_id:
        workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id, "id": workspace_id})
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace must belong to the agency.")
        filters["workspace_id"] = workspace_id
    invitations = await db.collection("invitations").find_many(filters)
    return {"items": [safe_invitation(invitation) for invitation in invitations]}


@router.post("/{agency_id}/staff/invitations/{invitation_id}/revoke")
async def revoke_staff_invitation(
    agency_id: str,
    invitation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    invitation = await db.collection("invitations").find_one(
        {"agency_id": agency_id, "id": invitation_id, "invitation_type": "agency_staff"}
    )
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")
    if invitation.get("status") == "accepted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Accepted invitations cannot be revoked.")
    if invitation.get("status") != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending invitations can be revoked.")

    updated = await db.collection("invitations").update_one(
        {"id": invitation_id, "status": "pending"},
        {"status": "revoked", "revoked_at": now_utc(), "revoked_by_user_id": user["id"]},
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation is no longer pending.")
    await write_audit(
        db,
        event_type="invitation_revoked",
        entity_type="invitation",
        entity_id=invitation_id,
        summary=f"Revoked staff invitation for {invitation.get('normalized_email')}.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"workspace_id": invitation.get("workspace_id"), "agency_role": invitation.get("target_role")},
    )
    return {"invitation": safe_invitation(updated)}


@router.post("/{agency_id}/staff", status_code=status.HTTP_201_CREATED)
async def create_staff(
    agency_id: str,
    payload: AgencyStaffCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")

    staff_user = await db.collection("platform_users").find_one({"email": payload.email})
    if staff_user is None:
        staff_user_model = PlatformUser(
            email=payload.email,
            full_name=payload.full_name,
            status=payload.status,
        )
        staff_user = await db.collection("platform_users").insert_one(staff_user_model.model_dump(mode="json"))

    existing = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": staff_user["id"]}
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Staff membership already exists.")

    membership = AgencyStaffMembership(
        agency_id=agency_id,
        user_id=staff_user["id"],
        agency_role=payload.agency_role,
        status=payload.status,
        joined_at=staff_user["created_at"] if payload.status == "active" else None,
    )
    membership_doc = await db.collection("agency_staff_memberships").insert_one(membership.model_dump(mode="json"))
    await write_audit(
        db,
        event_type="agency.staff_created",
        entity_type="agency_staff_membership",
        entity_id=membership.id,
        summary=f"Added {payload.full_name} to agency staff.",
        actor_user_id=user["id"],
        agency_id=agency_id,
    )
    return {"membership": membership_doc, "user": staff_user}


@router.get("/{agency_id}/portal-actions")
async def list_portal_actions(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(
        db,
        agency_id,
        user,
        ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"],
    )
    actions = await db.collection("portal_action_events").find_many({"agency_id": agency_id})
    clients_by_id = {
        client["id"]: client
        for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})
    }
    return {
        "items": [
            {
                "action": action,
                "client": clients_by_id.get(action.get("client_id")),
            }
            for action in actions
        ]
    }


@router.post("/{agency_id}/portal-actions/{action_id}/process")
async def process_portal_action(
    agency_id: str,
    action_id: str,
    payload: PortalActionProcessSubmit | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin", "agency_agent"])
    payload = payload or PortalActionProcessSubmit()
    if payload.status not in {"processed", "cancelled", "archived"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Portal action can only be marked processed, cancelled, or archived.")
    action = await db.collection("portal_action_events").update_one(
        {"agency_id": agency_id, "id": action_id},
        {"status": payload.status},
    )
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal action not found.")
    await write_audit(
        db,
        event_type="portal_action.processed",
        entity_type="portal_action_event",
        entity_id=action_id,
        summary=f"Marked portal action {payload.status}.",
        actor_user_id=user["id"],
        agency_id=agency_id,
    )
    return {"action": action}
