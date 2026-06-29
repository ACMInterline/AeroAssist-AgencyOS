from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import assert_startup_safe, configure_logging, get_settings, validate_config
from database import database
from routers import platform
from routers import agencies, agency_booking_workspaces, agency_offer_acceptance, agency_offer_builder, agency_special_services, airline_intelligence, auth, bookings, clients, documents, finance, form_profiles, offers, passengers, platform_airline_intelligence, platform_reference, platform_rules_services, platform_service_catalogue, portal, refunds_exchanges, reference, request_intakes, requests, trips, websites
from services.pdf_rendering_service import pdf_capabilities
from services.reference_data_service import REFERENCE_DOMAINS, country_enrichment_complete
from services.reference_domain_usage_service import list_domain_usage, reference_action_required
from services.reference_import_template_service import list_import_templates
from services.secret_service import check_secret
from services.seed_service import seed_core_data

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title="AeroAssist AgencyOS API",
    version="0.1.0",
    description="AeroAssist AgencyOS API foundation through Phase 36.3 booking and PNR foundation.",
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
        "phase": "phase_36_3_booking_pnr_foundation",
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
    country_reference_records = [item for item in reference_records if item.get("domain") == "countries"]
    airport_reference_records = [item for item in reference_records if item.get("domain") == "airports"]
    airline_reference_records = [item for item in reference_records if item.get("domain") == "airlines"]
    currency_reference_records = [item for item in reference_records if item.get("domain") == "currencies"]
    language_reference_records = [item for item in reference_records if item.get("domain") == "languages"]
    country_codes = {item.get("code") or item.get("key") for item in country_reference_records}
    country_record_count = len(country_reference_records)
    enriched_country_record_count = len([item for item in country_reference_records if country_enrichment_complete(item.get("metadata_json") or item.get("metadata") or {})])
    countries_missing_iso3_count = len([item for item in country_reference_records if not (item.get("metadata_json") or item.get("metadata") or {}).get("iso3_code")])
    countries_missing_capital_iata_count = len([item for item in country_reference_records if not (item.get("metadata_json") or item.get("metadata") or {}).get("capital_iata_code")])
    enriched_airport_record_count = len([item for item in airport_reference_records if (item.get("metadata_json") or item.get("metadata") or {}).get("iata_code")])
    enriched_airline_record_count = len([item for item in airline_reference_records if (item.get("metadata_json") or item.get("metadata") or {}).get("iata_code") or (item.get("metadata_json") or item.get("metadata") or {}).get("icao_code")])
    enriched_currency_record_count = len([item for item in currency_reference_records if (item.get("metadata_json") or item.get("metadata") or {}).get("currency_iso_code")])
    enriched_language_record_count = len([item for item in language_reference_records if (item.get("metadata_json") or item.get("metadata") or {}).get("iso639_1") or (item.get("metadata_json") or item.get("metadata") or {}).get("iso639_2")])
    countries_with_major_airports_count = len([item for item in country_reference_records if (item.get("metadata_json") or item.get("metadata") or {}).get("major_airports")])
    countries_with_national_carrier_count = len([item for item in country_reference_records if (item.get("metadata_json") or item.get("metadata") or {}).get("national_carrier")])
    airports_missing_country_link_count = len([item for item in airport_reference_records if ((item.get("metadata_json") or item.get("metadata") or {}).get("country_code") or (item.get("metadata_json") or item.get("metadata") or {}).get("country_iso2")) not in country_codes])
    airlines_missing_country_link_count = len([item for item in airline_reference_records if ((item.get("metadata_json") or item.get("metadata") or {}).get("country_code") or (item.get("metadata_json") or item.get("metadata") or {}).get("country_iso2")) not in country_codes])
    service_catalogue_records = await database.collection("service_catalogue").find_many()
    service_catalogue_record_count = len(service_catalogue_records)
    service_catalogue_active_count = len(
        [
            item
            for item in service_catalogue_records
            if item.get("is_active", item.get("active", True)) and item.get("status") != "archived"
        ]
    )
    reference_domain_usage_count = len(list_domain_usage())
    import_template_count = len(list_import_templates())
    enrichment_pack_count = 6 + await database.collection("reference_enrichment_packs").count()
    reference_action_required_count = len(await reference_action_required(database))
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
    trip_dossier_count = await database.collection("trip_dossiers").count()
    linked_trip_request_count = len([item for item in await database.collection("travel_requests").find_many() if item.get("trip_id")])
    trip_passenger_count = await database.collection("trip_passengers").count()
    trip_segment_count = await database.collection("trip_segments").count()
    trip_service_item_count = await database.collection("trip_service_items").count()
    airline_rules_core_count = await database.collection("airline_rules_core").count()
    exception_rule_count = await database.collection("unified_exception_rules").count()
    passenger_service_request_count = await database.collection("passenger_service_requests").count()
    offer_workspace_count = await database.collection("offer_workspaces").count()
    offer_option_count = await database.collection("offer_options").count()
    offer_builder_segment_count = await database.collection("offer_builder_segments").count()
    offer_fare_bundle_count = await database.collection("offer_fare_bundles").count()
    offer_pricing_line_count = await database.collection("offer_pricing_lines").count()
    offer_comparison_snapshot_count = await database.collection("offer_comparison_snapshots").count()
    offer_acceptance_count = await database.collection("offer_acceptances").count()
    trip_accepted_offer_snapshot_count = await database.collection("trip_accepted_offer_snapshots").count()
    booking_readiness_package_count = await database.collection("booking_readiness_packages").count()
    booking_workspace_count = await database.collection("booking_workspaces").count()
    booking_record_count = await database.collection("booking_records").count()
    booking_timeline_events = await database.collection("booking_timeline_events").find_many()
    booking_timeline_event_count = len(
        [item for item in booking_timeline_events if item.get("booking_workspace_id")]
    )
    booking_workspace_ready_count = await database.collection("booking_workspaces").count({"status": "ready_to_book"})
    booking_workspace_blocked_count = await database.collection("booking_workspaces").count({"status": "blocked"})
    booking_workspace_cancelled_count = await database.collection("booking_workspaces").count({"status": "cancelled"})
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
        "phase": "phase_36_3_booking_pnr_foundation",
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
            "reference_governance_permissions_enforced": True,
            "agency_reference_mutation_blocked": True,
            "agency_reference_consume_suggest_only": True,
            "reference_suggestion_queue_enabled": True,
            "reference_bulk_import_enabled": True,
            "reference_domain_usage_map_enabled": True,
            "reference_health_action_required_enabled": True,
            "domain_aware_import_templates_enabled": True,
            "enrichment_packs_defined_enabled": True,
            "service_catalogue_editable_enabled": True,
            "service_catalogue_operational_mapping_enabled": True,
            "service_catalogue_request_integration_enabled": True,
            "service_catalogue_rules_services_integration_enabled": True,
            "service_catalogue_offer_builder_integration_enabled": True,
            "service_catalogue_acceptance_booking_readiness_integration_enabled": True,
            "agency_service_catalogue_consume_enabled": True,
            "reference_domain_count": len(REFERENCE_DOMAINS),
            "reference_domain_usage_count": reference_domain_usage_count,
            "import_template_count": import_template_count,
            "enrichment_pack_count": enrichment_pack_count,
            "active_reference_record_count": active_reference_record_count,
            "service_catalogue_record_count": service_catalogue_record_count,
            "service_catalogue_active_count": service_catalogue_active_count,
            "reference_action_required_count": reference_action_required_count,
            "pending_reference_suggestion_count": pending_reference_suggestion_count,
            "approved_reference_suggestion_count": approved_reference_suggestion_count,
            "reference_import_batch_count": reference_import_batch_count,
            "reference_bootstrap_available": True,
            "readiness_required": False,
            "diagnostic": "Reference data is globally governed; suggestions and imports are manual, reviewed, and informational for readiness.",
        },
        "platform_reference_console": {
            "platform_reference_console_enabled": True,
            "platform_reference_management_enabled": True,
            "enriched_country_schema_enabled": True,
            "platform_reference_import_enabled": True,
            "platform_reference_export_enabled": True,
            "platform_reference_suggestion_review_enabled": True,
            "country_record_count": country_record_count,
            "enriched_country_record_count": enriched_country_record_count,
            "countries_missing_iso3_count": countries_missing_iso3_count,
            "countries_missing_capital_iata_count": countries_missing_capital_iata_count,
            "reference_record_card_enabled": True,
            "reference_enrichment_import_enabled": True,
            "reference_enrichment_templates_enabled": True,
            "enriched_airport_record_count": enriched_airport_record_count,
            "enriched_airline_record_count": enriched_airline_record_count,
            "enriched_currency_record_count": enriched_currency_record_count,
            "enriched_language_record_count": enriched_language_record_count,
            "countries_with_major_airports_count": countries_with_major_airports_count,
            "countries_with_national_carrier_count": countries_with_national_carrier_count,
            "airports_missing_country_link_count": airports_missing_country_link_count,
            "airlines_missing_country_link_count": airlines_missing_country_link_count,
            "readiness_required": False,
            "diagnostic": "Platform reference management and enrichment imports are owner-controlled; quality and link gaps are informational.",
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
        "trip_dossiers": {
            "trip_dossier_foundation_enabled": True,
            "request_to_trip_conversion_enabled": True,
            "trip_linking_enabled": True,
            "trip_passenger_copy_enabled": True,
            "trip_segment_copy_enabled": True,
            "trip_service_scope_copy_enabled": True,
            "trip_dossier_count": trip_dossier_count,
            "linked_trip_request_count": linked_trip_request_count,
            "trip_passenger_count": trip_passenger_count,
            "trip_segment_count": trip_segment_count,
            "trip_service_item_count": trip_service_item_count,
            "readiness_required": False,
            "diagnostic": "Trip dossiers are operational shells created manually or from requests; counts are informational.",
        },
        "rules_and_services": {
            "rules_services_registry_enabled": True,
            "airline_rules_core_enabled": True,
            "exception_engine_enabled": True,
            "ssr_osi_generator_enabled": True,
            "passenger_service_requests_enabled": True,
            "platform_rules_services_console_enabled": True,
            "agency_special_services_workspace_enabled": True,
            "airline_rules_core_count": airline_rules_core_count,
            "exception_rule_count": exception_rule_count,
            "passenger_service_request_count": passenger_service_request_count,
            "readiness_required": False,
            "diagnostic": "Rules and Services foundation is additive; empty rules and exception collections require manual verification but do not affect deployment readiness.",
        },
        "offer_builder": {
            "offer_workspace_foundation_enabled": True,
            "rule_aware_offer_options_enabled": True,
            "internal_comparison_matrix_enabled": True,
            "workspace_request_entrypoint_enabled": True,
            "workspace_trip_entrypoint_enabled": True,
            "rule_evaluation_in_offer_builder_enabled": True,
            "pricing_recalculation_enabled": True,
            "recommendation_flagging_enabled": True,
            "offer_acceptance_enabled": True,
            "accepted_offer_snapshot_enabled": True,
            "booking_readiness_package_enabled": True,
            "offer_to_trip_acceptance_enabled": True,
            "rules_aware_acceptance_enabled": True,
            "ssr_osi_booking_preview_enabled": True,
            "agency_acceptance_ui_enabled": True,
            "offer_workspace_count": offer_workspace_count,
            "offer_option_count": offer_option_count,
            "offer_segment_count": offer_builder_segment_count,
            "offer_fare_bundle_count": offer_fare_bundle_count,
            "offer_pricing_line_count": offer_pricing_line_count,
            "offer_comparison_snapshot_count": offer_comparison_snapshot_count,
            "offer_acceptance_count": offer_acceptance_count,
            "trip_accepted_offer_snapshot_count": trip_accepted_offer_snapshot_count,
            "booking_readiness_package_count": booking_readiness_package_count,
            "readiness_required": False,
            "diagnostic": "Offer builder acceptance snapshots and booking readiness packages are additive; no real booking, ticketing, or supplier execution is performed.",
        },
        "booking_foundation": {
            "booking_workspace_foundation_enabled": True,
            "booking_from_readiness_enabled": True,
            "booking_record_mirror_enabled": True,
            "booking_timeline_enabled": True,
            "manual_pnr_mirror_enabled": True,
            "provider_execution_disabled": True,
            "service_catalogue_booking_snapshot_enabled": True,
            "trip_booking_workspace_link_enabled": True,
            "agency_booking_workspace_ui_enabled": True,
            "booking_workspace_count": booking_workspace_count,
            "booking_record_count": booking_record_count,
            "booking_timeline_event_count": booking_timeline_event_count,
            "booking_workspace_ready_count": booking_workspace_ready_count,
            "booking_workspace_blocked_count": booking_workspace_blocked_count,
            "booking_workspace_cancelled_count": booking_workspace_cancelled_count,
            "readiness_required": False,
            "diagnostic": "Booking workspaces and PNR mirrors are manual foundations created from readiness packages; provider execution remains disabled.",
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
app.include_router(platform_airline_intelligence.router)
app.include_router(platform_rules_services.router)
app.include_router(platform_service_catalogue.router)
app.include_router(agencies.router)
app.include_router(clients.router)
app.include_router(passengers.router)
app.include_router(request_intakes.public_router)
app.include_router(request_intakes.staff_router)
app.include_router(requests.router)
app.include_router(trips.router)
app.include_router(agency_special_services.router)
app.include_router(agency_offer_builder.router)
app.include_router(agency_offer_acceptance.router)
app.include_router(agency_booking_workspaces.router)
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
app.include_router(platform_reference.router)
app.include_router(form_profiles.router)
app.include_router(form_profiles.agency_router)
app.include_router(form_profiles.public_router)
