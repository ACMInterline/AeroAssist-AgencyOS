import base64
import hashlib
import re
from io import BytesIO
from pathlib import PurePath
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AgencyWebsitePage,
    AgencyWebsitePageCreate,
    AgencyWebsitePageUpdate,
    AgencyWebsiteMediaAsset,
    AgencyWebsiteMediaUpdate,
    AgencyWebsiteMediaUpload,
    AgencyWebsiteSettings,
    AgencyWebsiteSettingsUpdate,
    AuditEvent,
    PublicRequestIntakeCreate,
    RequestIntakeContactSnapshot,
    RequestIntakeServiceSummary,
    RequestIntakeTravelSummary,
    WebsitePageStatus,
    WebsiteStatus,
    now_utc,
)
from services.request_intake_conversion_service import create_intake
from services.tenant_service import assert_agency_access, require_any_agency_role
from routers.agencies import computed_branding_theme, load_logo_assets, public_safe_branding

router = APIRouter(prefix="/api/agencies/{agency_id}/website", tags=["agency-websites"])
public_router = APIRouter(prefix="/api/public/websites", tags=["public-websites"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin"]
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
DANGEROUS_TEXT = re.compile(r"(<\s*/?\s*(script|style|iframe|object|embed|link|meta)\b|javascript:|data:text/html)", re.IGNORECASE)
MAX_MEDIA_BYTES = 5 * 1024 * 1024
SAFE_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
SAFE_IMAGE_EXTENSIONS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
MEDIA_VARIANT_WIDTHS = {"thumbnail": 320, "card": 640, "hero": 1600, "original_safe": None}
ALLOWED_SECTION_FIELDS = {
    "hero": {"section_type", "eyebrow", "heading", "headline", "subheadline", "body", "cta_label", "cta_href", "primary_cta_label", "primary_cta_target", "secondary_cta_label", "secondary_cta_target", "image_asset_id", "alignment", "items", "cards", "sort_order"},
    "text": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
    "services": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
    "cta": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "primary_cta_label", "primary_cta_target", "items", "cards", "sort_order"},
    "contact": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
    "intake_link": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "primary_cta_label", "primary_cta_target", "items", "cards", "sort_order"},
    "service_cards": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "image_asset_id", "sort_order"},
    "feature_grid": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
    "process_steps": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
    "faq": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
    "contact_cta": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "primary_cta_label", "primary_cta_target", "items", "cards", "image_asset_id", "sort_order"},
    "request_form_cta": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "primary_cta_label", "primary_cta_target", "items", "cards", "sort_order"},
    "testimonials": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "image_asset_id", "sort_order"},
    "trust_badges": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "image_asset_id", "sort_order"},
    "image_text": {"section_type", "eyebrow", "heading", "headline", "body", "cta_label", "cta_href", "items", "cards", "image_asset_id", "image_position", "sort_order"},
    "contact_details": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
    "legal_text": {"section_type", "eyebrow", "heading", "body", "cta_label", "cta_href", "items", "cards", "sort_order"},
}


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


def safe_filename(value: str) -> str:
    name = PurePath(value or "media").name.strip() or "media"
    return "".join(char for char in name if char.isalnum() or char in {"-", "_", "."})[:120] or "media"


def detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_media_upload(payload: AgencyWebsiteMediaUpload, media_bytes: bytes) -> None:
    if payload.content_type not in SAFE_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Website media must be PNG, JPEG, or WEBP. SVG is not accepted.")
    extension = PurePath(payload.filename or "").suffix.lower()
    if extension not in SAFE_IMAGE_EXTENSIONS or SAFE_IMAGE_EXTENSIONS[extension] != payload.content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Website media extension and MIME type must match PNG, JPEG, or WEBP.")
    if detect_image_type(media_bytes) != payload.content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Website media bytes do not match the declared image type.")
    if payload.asset_type not in {"image", "background", "illustration", "icon"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image-like media assets are renderable in this phase.")
    if not payload.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Media title is required.")
    if not payload.alt_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alt text is required for public website images.")


def prepare_media_variants(media_bytes: bytes) -> tuple[int, int, list[dict]]:
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Website media image preparation requires Pillow on the server.") from exc
    try:
        image = Image.open(BytesIO(media_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Website media image could not be decoded.") from exc
    has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
    normalized = ImageOps.exif_transpose(image).convert("RGBA" if has_alpha else "RGB")
    variants = []
    for variant_key, target_width in MEDIA_VARIANT_WIDTHS.items():
        working = normalized.copy()
        if target_width and working.width > target_width:
            ratio = target_width / working.width
            working = working.resize((target_width, max(1, int(working.height * ratio))), Image.Resampling.LANCZOS)
        output = BytesIO()
        working.save(output, format="PNG", optimize=True)
        data = output.getvalue()
        variants.append(
            {
                "variant_key": variant_key,
                "mime_type": "image/png",
                "width_px": working.width,
                "height_px": working.height,
                "file_size_bytes": len(data),
                "checksum_sha256": hashlib.sha256(data).hexdigest(),
                "data_base64": base64.b64encode(data).decode("ascii"),
                "is_public_safe": True,
            }
        )
    return normalized.width, normalized.height, variants


def variant_url(variant: dict | None) -> str | None:
    if not variant:
        return None
    return f"data:{variant.get('mime_type')};base64,{variant.get('data_base64')}" if variant.get("data_base64") and variant.get("mime_type") else None


def safe_media_asset(asset: dict, include_private_preview: bool = True) -> dict:
    variants = {
        variant.get("variant_key"): {
            "variant_key": variant.get("variant_key"),
            "mime_type": variant.get("mime_type"),
            "width_px": variant.get("width_px"),
            "height_px": variant.get("height_px"),
            "file_size_bytes": variant.get("file_size_bytes"),
            "checksum_sha256": variant.get("checksum_sha256"),
            "url": variant_url(variant) if include_private_preview and variant.get("is_public_safe") else None,
        }
        for variant in asset.get("variants", [])
        if variant.get("variant_key")
    }
    return {
        "id": asset.get("id"),
        "agency_id": asset.get("agency_id"),
        "website_profile_id": asset.get("website_profile_id"),
        "storage_record_id": asset.get("storage_record_id"),
        "asset_type": asset.get("asset_type"),
        "title": asset.get("title"),
        "alt_text": asset.get("alt_text"),
        "caption": asset.get("caption"),
        "usage_context": asset.get("usage_context"),
        "mime_type": asset.get("mime_type"),
        "width_px": asset.get("width_px"),
        "height_px": asset.get("height_px"),
        "file_size_bytes": asset.get("file_size_bytes"),
        "checksum_sha256": asset.get("checksum_sha256"),
        "original_filename": asset.get("original_filename"),
        "public_usage_allowed": asset.get("public_usage_allowed", False),
        "is_public_safe": asset.get("is_public_safe", False),
        "status": asset.get("status", "active"),
        "created_at": asset.get("created_at"),
        "updated_at": asset.get("updated_at"),
        "created_by_user_id": asset.get("created_by_user_id"),
        "updated_by_user_id": asset.get("updated_by_user_id"),
        "variants": variants,
        "thumbnail_url": variants.get("thumbnail", {}).get("url"),
        "card_url": variants.get("card", {}).get("url"),
        "hero_url": variants.get("hero", {}).get("url"),
    }


def public_media_asset(asset: dict) -> dict | None:
    if asset.get("status") != "active" or not asset.get("is_public_safe") or not asset.get("public_usage_allowed"):
        return None
    variants = {
        variant.get("variant_key"): {
            "variant_key": variant.get("variant_key"),
            "mime_type": variant.get("mime_type"),
            "width_px": variant.get("width_px"),
            "height_px": variant.get("height_px"),
            "file_size_bytes": variant.get("file_size_bytes"),
            "url": variant_url(variant),
        }
        for variant in asset.get("variants", [])
        if variant.get("variant_key") and variant.get("is_public_safe")
    }
    return {
        "id": asset.get("id"),
        "asset_type": asset.get("asset_type"),
        "title": asset.get("title"),
        "alt_text": asset.get("alt_text"),
        "caption": asset.get("caption"),
        "usage_context": asset.get("usage_context"),
        "width_px": asset.get("width_px"),
        "height_px": asset.get("height_px"),
        "variants": variants,
        "thumbnail_url": variants.get("thumbnail", {}).get("url"),
        "card_url": variants.get("card", {}).get("url"),
        "hero_url": variants.get("hero", {}).get("url"),
    }


def collect_section_media_ids(pages: list[dict]) -> set[str]:
    asset_ids = set()
    for page in pages:
        for section in page.get("sections", []):
            if section.get("image_asset_id"):
                asset_ids.add(section["image_asset_id"])
            for card in section.get("cards", []):
                if isinstance(card, dict) and card.get("image_asset_id"):
                    asset_ids.add(card["image_asset_id"])
    return asset_ids


async def validate_section_media_refs(db: Database, agency_id: str, sections: list[dict]) -> None:
    asset_ids = collect_section_media_ids([{"sections": sections}])
    for asset_id in asset_ids:
        asset = await db.collection("agency_website_media_assets").find_one({"agency_id": agency_id, "id": asset_id, "status": "active"})
        if not asset or not asset.get("is_public_safe") or not asset.get("public_usage_allowed"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Website section image must reference an active public-safe media asset.")


def clean_section(section: dict) -> dict:
    section = {
        key: value
        for key, value in section.items()
        if value is not None and value != "" and value != []
    }
    section_type = section.get("section_type") or "text"
    allowed = ALLOWED_SECTION_FIELDS.get(section_type)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported website section type: {section_type}.")
    unknown = sorted(set(section).difference(allowed))
    if unknown:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported fields for {section_type}: {', '.join(unknown)}.")
    if section.get("alignment") and section["alignment"] not in {"left", "center"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hero alignment must be left or center.")
    if section.get("image_position") and section["image_position"] not in {"left", "right"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image position must be left or right.")
    cleaned = {key: value for key, value in section.items() if key in allowed}
    for card in cleaned.get("cards", []):
        if not isinstance(card, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section cards must be objects.")
        validate_safe_text(card)
    return cleaned


def clean_sections(sections: list[dict]) -> list[dict]:
    cleaned = []
    for index, section in enumerate(sections):
        item = clean_section(section)
        item["sort_order"] = index
        cleaned.append(item)
    return cleaned


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


def section_change_events(before: list[dict], after: list[dict]) -> set[str]:
    events = set()
    if len(after) > len(before):
        events.add("website_section_created")
    if len(after) < len(before):
        events.add("website_section_deleted")
    if [item.get("sort_order") for item in before] != [item.get("sort_order") for item in after] or [item.get("heading") for item in before] != [item.get("heading") for item in after]:
        events.add("website_sections_reordered")
    if before != after:
        events.add("website_section_updated")
    return events


async def load_active_site(db: Database, slug: str) -> dict:
    settings = await db.collection("agency_website_settings").find_one({"slug": validate_slug(slug), "status": "active"})
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not published.")
    return settings


def safe_public_intake(intake: dict) -> dict:
    return {"id": intake["id"], "reference_code": intake["reference_code"], "status": "received"}


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


@router.get("/media")
async def list_media_assets(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    assets = await db.collection("agency_website_media_assets").find_many({"agency_id": agency_id})
    assets.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    pages = await db.collection("agency_website_pages").find_many({"agency_id": agency_id})
    used_ids = collect_section_media_ids(pages)
    items = []
    for asset in assets:
        safe = safe_media_asset(asset)
        safe["used_in_published_content"] = asset["id"] in used_ids
        items.append(safe)
    return {"items": items}


@router.post("/media", status_code=status.HTTP_201_CREATED)
async def upload_media_asset(agency_id: str, payload: AgencyWebsiteMediaUpload, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        media_bytes = base64.b64decode(payload.data_base64, validate=True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Media data must be valid base64.") from exc
    if not media_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Media file is empty.")
    if len(media_bytes) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Website media file must be 5MB or smaller.")
    validate_media_upload(payload, media_bytes)
    width, height, variants = prepare_media_variants(media_bytes)
    settings = await db.collection("agency_website_settings").find_one({"agency_id": agency_id})
    asset = AgencyWebsiteMediaAsset(
        agency_id=agency_id,
        website_profile_id=(settings or {}).get("id"),
        storage_record_id=f"website_media_{now_utc().strftime('%Y%m%d%H%M%S%f')}",
        asset_type=payload.asset_type,
        title=payload.title.strip(),
        alt_text=payload.alt_text.strip(),
        caption=payload.caption,
        usage_context=payload.usage_context,
        mime_type="image/png",
        width_px=width,
        height_px=height,
        file_size_bytes=len(media_bytes),
        checksum_sha256=hashlib.sha256(media_bytes).hexdigest(),
        original_filename=safe_filename(payload.filename),
        public_usage_allowed=payload.public_usage_allowed,
        is_public_safe=True,
        variants=variants,
        created_by_user_id=user["id"],
        created_by_email=user.get("email"),
        updated_by_user_id=user["id"],
        updated_by_email=user.get("email"),
        audit_metadata={"variants_generated": [variant["variant_key"] for variant in variants], "svg_allowed": False},
    )
    created = await db.collection("agency_website_media_assets").insert_one(asset.model_dump(mode="json"))
    await write_audit(db, agency_id, user["id"], "website_media_uploaded", "agency_website_media_asset", created["id"], "Uploaded website media asset.", {"mime_type": created["mime_type"], "size_bytes": len(media_bytes), "variants_generated": len(variants)})
    return {"asset": safe_media_asset(created)}


@router.put("/media/{asset_id}")
async def update_media_asset(agency_id: str, asset_id: str, payload: AgencyWebsiteMediaUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updates = clean_updates(payload)
    validate_safe_text(updates)
    if "title" in updates and updates["title"] is not None and not str(updates["title"]).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Media title cannot be blank.")
    if "alt_text" in updates and updates["alt_text"] is not None and not str(updates["alt_text"]).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alt text is required for public website images.")
    updates.update({"updated_by_user_id": user["id"], "updated_by_email": user.get("email")})
    asset = await db.collection("agency_website_media_assets").update_one({"agency_id": agency_id, "id": asset_id}, updates)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")
    await write_audit(db, agency_id, user["id"], "website_media_updated", "agency_website_media_asset", asset_id, "Updated website media asset.", {"fields": sorted(updates.keys())})
    return {"asset": safe_media_asset(asset)}


@router.delete("/media/{asset_id}")
async def archive_media_asset(agency_id: str, asset_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    asset = await db.collection("agency_website_media_assets").update_one(
        {"agency_id": agency_id, "id": asset_id},
        {"status": "archived", "public_usage_allowed": False, "updated_by_user_id": user["id"], "updated_by_email": user.get("email")},
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")
    await write_audit(db, agency_id, user["id"], "website_media_archived", "agency_website_media_asset", asset_id, "Archived website media asset.")
    return {"asset": safe_media_asset(asset)}


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
    data["sections"] = clean_sections(data.get("sections") or [])
    await validate_section_media_refs(db, agency_id, data["sections"])
    data["slug"] = validate_slug(data["slug"])
    existing = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "slug": data["slug"]})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A website page with this slug already exists.")
    if data.get("page_type") == "home" and await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "page_type": "home"}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only one home page is allowed.")
    page = AgencyWebsitePage(agency_id=agency_id, updated_by_user_id=user["id"], updated_by_email=user.get("email"), audit_metadata={"created_from_builder": True}, **data)
    created = await db.collection("agency_website_pages").insert_one(page.model_dump(mode="json"))
    await write_audit(db, agency_id, user["id"], "agency_website_page_created", "agency_website_page", created["id"], f"Created website page {created['title']}.")
    if created.get("sections"):
        await write_audit(db, agency_id, user["id"], "website_section_created", "agency_website_page", created["id"], "Created website page sections.", {"section_count": len(created["sections"])})
    return {"page": safe_page(created)}


@router.put("/pages/{page_id}")
async def update_page(agency_id: str, page_id: str, payload: AgencyWebsitePageUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    current = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "id": page_id})
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website page not found.")
    updates = clean_updates(payload)
    validate_safe_text(updates)
    if "sections" in updates:
        updates["sections"] = clean_sections(updates.get("sections") or [])
        await validate_section_media_refs(db, agency_id, updates["sections"])
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
    if "sections" in updates:
        for event_type in section_change_events(current.get("sections") or [], updates["sections"]):
            await write_audit(db, agency_id, user["id"], event_type, "agency_website_page", page_id, "Updated website page sections.", {"section_count": len(updates["sections"])})
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
    await write_audit(db, agency_id, user["id"], "website_page_published", "agency_website_page", page_id, f"Published website page {page['title']}.")
    return {"page": safe_page(page)}


@router.post("/publish")
async def publish_site(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    settings = await db.collection("agency_website_settings").find_one({"agency_id": agency_id})
    if not settings:
        defaults = await default_settings(db, agency_id)
        settings = await db.collection("agency_website_settings").insert_one(AgencyWebsiteSettings(**defaults).model_dump(mode="json"))
    home_page = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "page_type": "home", "status": "published"})
    if not home_page:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Publish a home page before publishing the site.")
    updated = await db.collection("agency_website_settings").update_one({"id": settings["id"]}, {"status": WebsiteStatus.ACTIVE, "published_at": now_utc(), "updated_by_user_id": user["id"], "updated_by_email": user.get("email")})
    await db.collection("agency_workspaces").update_one({"agency_id": agency_id}, {"website_status": "active"})
    await write_audit(db, agency_id, user["id"], "website_site_published", "agency_website_settings", updated["id"], "Published agency website.", {"slug": updated.get("slug")})
    return {"settings": safe_settings(updated)}


@router.post("/unpublish")
async def unpublish_site(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    settings = await db.collection("agency_website_settings").find_one({"agency_id": agency_id})
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website settings not found.")
    updated = await db.collection("agency_website_settings").update_one({"id": settings["id"]}, {"status": WebsiteStatus.DRAFT, "updated_by_user_id": user["id"], "updated_by_email": user.get("email")})
    await db.collection("agency_workspaces").update_one({"agency_id": agency_id}, {"website_status": "draft"})
    await write_audit(db, agency_id, user["id"], "website_site_unpublished", "agency_website_settings", updated["id"], "Unpublished agency website.", {"slug": updated.get("slug")})
    return {"settings": safe_settings(updated)}


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
    settings = await load_active_site(db, slug)
    agency_id = settings["agency_id"]
    pages = await db.collection("agency_website_pages").find_many({"agency_id": agency_id, "status": "published"})
    pages.sort(key=lambda page: (page.get("page_type") != "home", page.get("title", "")))
    branding = await db.collection("agency_branding_settings").find_one({"agency_id": agency_id})
    logo_assets = await load_logo_assets(db, agency_id, branding or {}) if branding else []
    media_ids = collect_section_media_ids(pages)
    media_assets = {}
    for media_id in media_ids:
        asset = await db.collection("agency_website_media_assets").find_one({"agency_id": agency_id, "id": media_id})
        safe_asset = public_media_asset(asset or {})
        if safe_asset:
            media_assets[media_id] = safe_asset
    return {
        "settings": safe_settings(settings),
        "branding": public_safe_branding(branding or {}, logo_assets, settings.get("site_name")),
        "computed_theme": computed_branding_theme(branding or {}),
        "media_assets": media_assets,
        "navigation": [{"title": page["title"], "slug": page["slug"], "page_type": page.get("page_type")} for page in pages],
        "pages": [safe_page(page) for page in pages],
    }


@public_router.get("/{slug}/pages/{page_slug}")
async def public_website_page(slug: str, page_slug: str, db: Database = Depends(get_database)) -> dict:
    site = await public_website(slug, db)
    page_slug = validate_slug(page_slug)
    page = next((item for item in site["pages"] if item.get("slug") == page_slug), None)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published page not found.")
    return {**site, "page": page, "pages": [page]}


@public_router.post("/{slug}/request", status_code=status.HTTP_201_CREATED)
async def submit_website_request(slug: str, payload: PublicRequestIntakeCreate, page_slug: str | None = None, db: Database = Depends(get_database)) -> dict:
    settings = await load_active_site(db, slug)
    agency_id = settings["agency_id"]
    page = None
    if page_slug:
        page = await db.collection("agency_website_pages").find_one({"agency_id": agency_id, "slug": validate_slug(page_slug), "status": "published"})
        if not page:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published page not found.")
    contact = payload.contact.model_dump(mode="json")
    travel = payload.travel.model_dump(mode="json")
    services = payload.services.model_dump(mode="json")
    if not contact.get("name") or not (contact.get("email") or contact.get("phone")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name and email or phone are required.")
    if not contact.get("privacy_policy_accepted") or not contact.get("data_processing_consent"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consent is required.")
    metadata = {
        "source_site_slug": settings["slug"],
        "source_page_slug": page.get("slug") if page else page_slug,
        "source_website_profile_id": settings["id"],
        "source_website_page_id": page.get("id") if page else None,
    }
    intake = await create_intake(
        db,
        source="agency_website",
        agency_id=agency_id,
        workspace_id=settings.get("workspace_id"),
        contact=contact,
        travel=travel,
        services=services,
        request_details=payload.request_details,
        agency_custom_fields=payload.agency_custom_fields,
        raw_payload={**payload.model_dump(mode="json"), **metadata},
        source_metadata=metadata,
    )
    await write_audit(db, agency_id, None, "website_public_request_submitted", "request_intake", intake["id"], "Public website request submitted.", {"reference_code": intake["reference_code"], "site_slug": settings["slug"], "page_slug": metadata.get("source_page_slug")})
    return {"intake": safe_public_intake(intake), "message": "We received your request. Our team will review it."}
