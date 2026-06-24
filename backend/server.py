from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import assert_startup_safe, configure_logging, get_settings, validate_config
from database import database
from routers import platform
from routers import agencies, airline_intelligence, auth, bookings, clients, documents, finance, form_profiles, offers, passengers, portal, refunds_exchanges, reference, request_intakes, requests, websites
from services.pdf_rendering_service import pdf_capabilities
from services.reference_data_service import REFERENCE_DOMAINS
from services.secret_service import check_secret
from services.seed_service import seed_core_data

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title="AeroAssist AgencyOS API",
    version="0.1.0",
    description="AeroAssist AgencyOS API foundation through Phase 34.1 global field library and agency form profiles.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    assert_startup_safe(get_settings())
    await database.connect()
    if get_settings().seed_on_startup:
        await seed_core_data(database)


@app.get("/api/health")
async def root_health() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "service": "AeroAssist AgencyOS API",
        "app_env": settings.app_env,
        "phase": "phase_34_1_global_field_library_agency_form_profiles",
    }


def storage_status() -> dict:
    settings = get_settings()
    root: Path = settings.document_export_storage_dir
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".aeroassist-readiness-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {"ok": True, "configured": True, "writable": True, "diagnostic": "Document export storage is writable."}
    except OSError:
        return {"ok": False, "configured": True, "writable": False, "diagnostic": "Document export storage is not writable."}


def delivery_config_status() -> dict:
    settings = get_settings()
    refs = []
    for secret_ref in settings.smtp_secret_refs:
        result = check_secret(secret_ref)
        refs.append(
            {
                "ok": result.ok,
                "configured": result.configured,
                "resolved": result.resolved,
                "diagnostic": result.diagnostic,
                "secret_ref_masked": result.secret_ref_masked,
            }
        )
    return {
        "smtp_secret_refs_configured": len(refs),
        "smtp_secret_refs_resolved": sum(1 for ref in refs if ref["resolved"]),
        "smtp_secret_refs": refs,
        "automatic_sending_enabled": False,
    }


@app.get("/api/readiness")
async def readiness() -> dict:
    settings = get_settings()
    config = validate_config(settings, include_storage=False)
    storage = storage_status()
    database_status = await database.readiness()
    pdf = pdf_capabilities()
    delivery = delivery_config_status()
    intake_count = await database.collection("request_intakes").count()
    new_intake_count = await database.collection("request_intakes").count({"status": "new"})
    converted_intake_count = await database.collection("request_intakes").count({"status": "converted"})
    open_request_count = len(
        [
            item
            for item in await database.collection("travel_requests").find_many()
            if item.get("status") not in {"closed", "cancelled", "archived"}
        ]
    )
    branding_settings_count = await database.collection("agency_branding_settings").count()
    branding_logo_asset_count = await database.collection("agency_branding_assets").count()
    website_settings_count = await database.collection("agency_website_settings").count()
    published_website_count = await database.collection("agency_website_settings").count({"status": "active"})
    website_page_count = await database.collection("agency_website_pages").count()
    media_asset_count = await database.collection("agency_website_media_assets").count()
    public_media_asset_count = await database.collection("agency_website_media_assets").count({"status": "active", "public_usage_allowed": True, "is_public_safe": True})
    website_origin_intake_count = await database.collection("request_intakes").count({"source": "agency_website"})
    reference_records = await database.collection("global_reference_records").find_many()
    active_reference_record_count = len([item for item in reference_records if item.get("is_active", True)])
    service_catalogue_record_count = await database.collection("service_catalogue").count()
    pending_reference_suggestion_count = await database.collection("reference_data_suggestions").count({"status": "pending_review"})
    approved_reference_suggestion_count = await database.collection("reference_data_suggestions").count({"status": "approved"})
    reference_import_batch_count = await database.collection("reference_import_batches").count()
    global_field_definition_count = await database.collection("global_field_definitions").count()
    agency_form_profile_count = await database.collection("agency_form_profiles").count()
    agency_form_field_setting_count = await database.collection("agency_form_field_settings").count()
    normalized_request_segment_count = await database.collection("request_segments").count()
    normalized_request_passenger_count = await database.collection("request_passengers").count()
    normalized_passenger_segment_service_count = await database.collection("request_passenger_segment_services").count()
    normalized_request_pet_count = await database.collection("request_pets").count()
    normalized_request_special_item_count = await database.collection("request_special_items").count()
    branded_logo_count = len(
        [
            item
            for item in await database.collection("agency_branding_settings").find_many()
            if item.get("logo_storage_record_id")
        ]
    )
    ok = config["ok"] and storage["ok"] and database_status["ok"]
    return {
        "ok": ok,
        "service": "AeroAssist AgencyOS API",
        "app_env": settings.app_env,
        "phase": "phase_34_1_global_field_library_agency_form_profiles",
        "config": config,
        "database": database_status,
        "storage": storage,
        "document_delivery_providers": {
            "automatic_delivery_enabled": False,
            "manual_provider_enabled": True,
            "public_links_enabled": False,
            "object_storage_enabled": False,
            "diagnostic": "Automatic delivery providers are disabled or not configured in Phase 25.",
        },
        "request_intake": {
            "total_intakes": intake_count,
            "new_intakes": new_intake_count,
            "converted_intakes": converted_intake_count,
            "open_operational_requests": open_request_count,
            "diagnostic": "Request intake counts are informational and do not affect readiness.",
        },
        "agency_branding": {
            "branding_enabled": True,
            "logo_assets_enabled": True,
            "logo_variant_generation_enabled": True,
            "public_safe_logo_serving_enabled": True,
            "configured_agency_branding_count": branding_settings_count,
            "configured_logo_count": branded_logo_count,
            "logo_asset_count": branding_logo_asset_count,
            "readiness_required": False,
            "diagnostic": "Agency branding settings are optional and do not affect service readiness.",
        },
        "agency_websites": {
            "cms_enabled": True,
            "public_site_renderer_enabled": True,
            "public_website_intake_enabled": True,
            "cms_media_library_enabled": True,
            "public_safe_media_enabled": True,
            "image_variant_generation_enabled": True,
            "configured_websites": website_settings_count,
            "active_websites": published_website_count,
            "website_pages": website_page_count,
            "media_asset_count": media_asset_count,
            "public_media_asset_count": public_media_asset_count,
            "website_origin_intakes": website_origin_intake_count,
            "readiness_required": False,
            "diagnostic": "Agency website builder content is optional and does not affect service readiness.",
        },
        "blueprint_alignment": {
            "blueprint_alignment_documented": True,
            "canonical_operations_model_documented": True,
            "current_model_inventory_documented": True,
            "trip_dossier_foundation_ready": True,
            "reference_data_phase_ready": True,
            "readiness_required": False,
            "diagnostic": "Blueprint alignment is documented and additive foundations are informational only.",
        },
        "reference_data": {
            "reference_data_enabled": True,
            "service_catalogue_enabled": True,
            "global_reference_governance_enabled": True,
            "reference_suggestion_queue_enabled": True,
            "reference_bulk_import_enabled": True,
            "reference_domain_count": len(REFERENCE_DOMAINS),
            "active_reference_record_count": active_reference_record_count,
            "service_catalogue_record_count": service_catalogue_record_count,
            "pending_reference_suggestion_count": pending_reference_suggestion_count,
            "approved_reference_suggestion_count": approved_reference_suggestion_count,
            "reference_import_batch_count": reference_import_batch_count,
            "reference_bootstrap_available": True,
            "readiness_required": False,
            "diagnostic": "Reference data is globally governed; suggestions and imports are manual, reviewed, and informational for readiness.",
        },
        "segment_scoped_requests": {
            "segment_scoped_services_enabled": True,
            "request_service_normalization_enabled": True,
            "normalized_request_segment_count": normalized_request_segment_count,
            "normalized_request_passenger_count": normalized_request_passenger_count,
            "normalized_passenger_segment_service_count": normalized_passenger_segment_service_count,
            "normalized_request_pet_count": normalized_request_pet_count,
            "normalized_request_special_item_count": normalized_request_special_item_count,
            "readiness_required": False,
            "diagnostic": "Segment-scoped services, pets, and special items are informational and may be zero before request normalization.",
        },
        "form_profiles": {
            "global_field_library_enabled": True,
            "agency_form_profiles_enabled": True,
            "agency_field_menu_enabled": True,
            "global_field_definition_count": global_field_definition_count,
            "agency_form_profile_count": agency_form_profile_count,
            "agency_form_field_setting_count": agency_form_field_setting_count,
            "readiness_required": False,
            "diagnostic": "Field library and agency form profiles are controlled configuration foundations and do not affect core readiness.",
        },
        "pdf": {
            "available": pdf.get("available"),
            "engine": pdf.get("engine"),
            "engine_version": pdf.get("engine_version"),
            "diagnostic": pdf.get("diagnostic"),
        },
        "delivery": delivery,
    }


@app.get("/api/audit-events")
async def audit_events() -> dict:
    return {"items": await database.collection("audit_events").find_many()}


app.include_router(auth.router)
app.include_router(platform.router)
app.include_router(agencies.router)
app.include_router(clients.router)
app.include_router(passengers.router)
app.include_router(request_intakes.public_router)
app.include_router(request_intakes.staff_router)
app.include_router(requests.router)
app.include_router(offers.router)
app.include_router(bookings.router)
app.include_router(finance.router)
app.include_router(airline_intelligence.router)
app.include_router(documents.router)
app.include_router(documents.storage_router)
app.include_router(documents.portal_router)
app.include_router(refunds_exchanges.router)
app.include_router(refunds_exchanges.portal_router)
app.include_router(websites.router)
app.include_router(websites.public_router)
app.include_router(portal.router)
app.include_router(reference.router)
app.include_router(form_profiles.router)
app.include_router(form_profiles.agency_router)
app.include_router(form_profiles.public_router)
