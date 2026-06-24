import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AgencyWebsitePage,
    AgencyWebsitePageCreate,
    AgencyWebsitePageUpdate,
    AgencyWebsiteSettings,
    AgencyWebsiteSettingsUpdate,
    AuditEvent,
    WebsitePageStatus,
    WebsiteStatus,
    now_utc,
)
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}/website", tags=["agency-websites"])
public_router = APIRouter(prefix="/api/public/websites", tags=["public-websites"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin"]
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
DANGEROUS_TEXT = re.compile(r"(<\s*/?\s*(script|style|iframe|object|embed|link|meta)\b|javascript:|data:text/html)", re.IGNORECASE)


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:64]


def validate_slug(value: str) -> str:
    slug = normalize_slug(value)
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug must be 3-64 lowercase letters, numbers, or hyphens.")
    return slug


def validate_safe_text(value: Any) -> None:
    if isinstance(value, str):
        if DANGEROUS_TEXT.search(value):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Website content cannot include scripts, styles, iframes, or javascript URLs.")
    elif isinstance(value, list):
        for item in value:
            validate_safe_text(item)
    elif isinstance(value, dict):
        for item in value.values():
            validate_safe_text(item)


async def write_audit(db: Database, agency_id: str, user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def default_settings(db: Database, agency_id: str) -> dict:
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id})
    branding = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    slug = validate_slug(agency.get("slug") or agency.get("name") or agency_id)
    model = AgencyWebsiteSettings(
        agency_id=agency_id,
        workspace_id=workspace.get("id") if workspace else None,
        site_name=(branding or {}).get("brand_name") or (workspace or {}).get("brand_name") or agency.get("name"),
        slug=slug,
        tagline="Travel support, planning, and assistance from your agency team.",
        status=WebsiteStatus.NOT_CONFIGURED,
        seo_title=(branding or {}).get("brand_name") or agency.get("name"),
        seo_description="Agency travel assistance website managed in AeroAssist AgencyOS.",
    )
    return model.model_dump(mode="json")


async def ensure_slug_available(db: Database, agency_id: str, slug: str) -> None:
    existing = await db.collection("agency_website_settings").find_one({"slug": slug})
    if existing and existing.get("agency_id") != agency_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Website slug is already in use.")


def safe_settings(settings: dict) -> dict:
    return {key: value for key, value in settings.items() if key not in {"audit_metadata"}}


def safe_page(page: dict) -> dict:
    return {key: value for key, value in page.items() if key not in {"audit_metadata"}}


@router.get("")
async def get_website_settings(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    settings = await db.collection("agency_website_settings").find_one({"agency_id": agency_id}) or await default_settings(db, agency_id)
    pages = await db.collection("agency_website_pages").find_many({"agency_id": agency_id})
    return {"settings": safe_settings(settings), "page_count": len(pages), "published_page_count": len([page for page in pages if page.get("status") == "published"])}


@router.put("")
async def update_website_settings(agency_id: str, payload: AgencyWebsiteSettingsUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updates = clean_updates(payload)
    validate_safe_text(updates)
    if "slug" in updates and updates["slug"]:
        updates["slug"] = validate_slug(updates["slug"])
        await ensure_slug_available(db, agency_id, updates["slug"])
    if "site_name" in updates and updates["site_name"] is not None and not str(updates["site_name"]).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site name cannot be blank.")
    if updates.get("workspace_id"):
        workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id, "id": updates["workspace_id"]})
        if not workspace:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace must belong to the agency.")
    if updates.get("status") == "active" and not await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "status": "published"}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Publish at least one page before activating the website.")

    existing = await db.collection("agency_website_settings").find_one({"agency_id": agency_id})
    audit_metadata = {"fields": sorted(updates.keys()), "controlled_builder": True, "custom_code_allowed": False}
    updates.update({"updated_by_user_id": user["id"], "updated_by_email": user.get("email"), "audit_metadata": audit_metadata})
    if updates.get("status") == "active":
        updates["published_at"] = now_utc()
    if existing:
        settings = await db.collection("agency_website_settings").update_one({"id": existing["id"]}, updates)
    else:
        defaults = await default_settings(db, agency_id)
        defaults.update(updates)
        settings = await db.collection("agency_website_settings").insert_one(AgencyWebsiteSettings(**defaults).model_dump(mode="json"))
    await db.collection("agency_workspaces").update_one({"agency_id": agency_id}, {"website_status": settings["status"]})
    await write_audit(db, agency_id, user["id"], "agency_website_settings_updated", "agency_website_settings", settings["id"], "Updated agency website settings.", audit_metadata)
    return {"settings": safe_settings(settings)}


@router.get("/pages")
async def list_pages(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    pages = await db.collection("agency_website_pages").find_many({"agency_id": agency_id})
    pages.sort(key=lambda page: (page.get("page_type") != "home", page.get("title", "")))
    return {"items": [safe_page(page) for page in pages]}


@router.post("/pages", status_code=status.HTTP_201_CREATED)
async def create_page(agency_id: str, payload: AgencyWebsitePageCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    data = payload.model_dump(mode="json")
    validate_safe_text(data)
    data["slug"] = validate_slug(data["slug"])
    existing = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "slug": data["slug"]})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A website page with this slug already exists.")
    if data.get("page_type") == "home" and await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "page_type": "home"}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only one home page is allowed.")
    page = AgencyWebsitePage(agency_id=agency_id, updated_by_user_id=user["id"], updated_by_email=user.get("email"), audit_metadata={"created_from_builder": True}, **data)
    created = await db.collection("agency_website_pages").insert_one(page.model_dump(mode="json"))
    await write_audit(db, agency_id, user["id"], "agency_website_page_created", "agency_website_page", created["id"], f"Created website page {created['title']}.")
    return {"page": safe_page(created)}


@router.put("/pages/{page_id}")
async def update_page(agency_id: str, page_id: str, payload: AgencyWebsitePageUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    current = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "id": page_id})
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website page not found.")
    updates = clean_updates(payload)
    validate_safe_text(updates)
    if "slug" in updates and updates["slug"]:
        updates["slug"] = validate_slug(updates["slug"])
        existing = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "slug": updates["slug"]})
        if existing and existing["id"] != page_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A website page with this slug already exists.")
    if updates.get("page_type") == "home":
        existing_home = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "page_type": "home"})
        if existing_home and existing_home["id"] != page_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only one home page is allowed.")
    updates.update({"updated_by_user_id": user["id"], "updated_by_email": user.get("email"), "audit_metadata": {"fields": sorted(updates.keys()), "custom_code_allowed": False}})
    page = await db.collection("agency_website_pages").update_one({"agency_id": agency_id, "id": page_id}, updates)
    await write_audit(db, agency_id, user["id"], "agency_website_page_updated", "agency_website_page", page_id, "Updated agency website page.", {"fields": sorted(updates.keys())})
    return {"page": safe_page(page)}


@router.post("/pages/{page_id}/publish")
async def publish_page(agency_id: str, page_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    current = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "id": page_id})
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website page not found.")
    if not current.get("sections"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add at least one section before publishing.")
    page = await db.collection("agency_website_pages").update_one({"agency_id": agency_id, "id": page_id}, {"status": WebsitePageStatus.PUBLISHED, "published_at": now_utc(), "updated_by_user_id": user["id"], "updated_by_email": user.get("email")})
    await write_audit(db, agency_id, user["id"], "agency_website_page_published", "agency_website_page", page_id, f"Published website page {page['title']}.")
    return {"page": safe_page(page)}


@router.post("/pages/{page_id}/archive")
async def archive_page(agency_id: str, page_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    page = await db.collection("agency_website_pages").update_one({"agency_id": agency_id, "id": page_id}, {"status": WebsitePageStatus.ARCHIVED, "updated_by_user_id": user["id"], "updated_by_email": user.get("email")})
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website page not found.")
    await write_audit(db, agency_id, user["id"], "agency_website_page_archived", "agency_website_page", page_id, f"Archived website page {page['title']}.")
    return {"page": safe_page(page)}


@public_router.get("/{slug}")
async def public_website(slug: str, db: Database = Depends(get_database)) -> dict:
    settings = await db.collection("agency_website_settings").find_one({"slug": validate_slug(slug), "status": "active"})
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not published.")
    agency_id = settings["agency_id"]
    pages = await db.collection("agency_website_pages").find_many({"agency_id": agency_id, "status": "published"})
    pages.sort(key=lambda page: (page.get("page_type") != "home", page.get("title", "")))
    branding = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    return {
        "settings": safe_settings(settings),
        "branding": {
            "brand_name": (branding or {}).get("brand_name") or settings.get("site_name"),
            "logo_url": (branding or {}).get("logo_url"),
            "theme_mode": (branding or {}).get("theme_mode", "light"),
            "color_palette_key": (branding or {}).get("color_palette_key", "aero_blue"),
        },
        "pages": [safe_page(page) for page in pages],
    }
