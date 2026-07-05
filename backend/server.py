from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import assert_startup_safe, configure_logging, get_settings, validate_config
from database import database
from routers import platform
from routers import agency_airline_intelligence_agency_consumption, agency_airline_intelligence_data_pack_reviews, agency_airline_intelligence_data_packs, agency_airline_intelligence_knowledge_versions, agency_ancillary_pricing, agency_capabilities, agency_feature_bundle_assignments, agency_feature_flag_bundles, agency_feature_flag_readiness, agency_feature_flags, agency_offer_decision_export_audit_reviews, agency_offer_decision_export_compliance, agency_offer_decision_export_deliveries, agency_offer_decision_export_delivery_outcomes, agency_offer_decision_export_governance, agency_offer_decision_export_previews, agency_offer_decision_export_releases, agency_offer_decision_exports, agency_offer_decision_explanations, agency_offer_decision_packs, agency_offer_policy_advisor, agency_policy_comparison, agency_saas_subscriptions, platform_airline_intelligence_agency_consumption, platform_airline_intelligence_data_pack_reviews, platform_airline_intelligence_data_packs, platform_airline_intelligence_knowledge_versions, platform_ancillary_pricing, platform_capabilities, platform_feature_bundle_assignments, platform_feature_flag_audits, platform_feature_flag_bundles, platform_feature_flags, platform_offer_decision_export_audit_reviews, platform_offer_decision_export_compliance, platform_offer_decision_export_deliveries, platform_offer_decision_export_delivery_outcomes, platform_offer_decision_export_governance, platform_offer_decision_export_previews, platform_offer_decision_export_releases, platform_offer_decision_exports, platform_offer_decision_explanations, platform_offer_decision_packs, platform_offer_policy_advisor, platform_policy_comparison, platform_saas_subscriptions
from routers import agency_feature_bundle_rollout_plans, agency_feature_bundle_rollout_readiness, agency_rollout_dashboard, platform_feature_bundle_rollout_plans, platform_feature_bundle_rollout_readiness, platform_rollout_dashboard
from routers import agency_service_mechanics, platform_service_mechanics
from routers import agencies, agency_airline_policy_library, agency_booking_imports, agency_booking_workspaces, agency_documents, agency_gds_parser, agency_offer_acceptance, agency_offer_builder, agency_service_taxonomy, agency_special_services, agency_ticket_emd, agency_trip_changes, airline_intelligence, auth, bookings, clients, documents, finance, form_profiles, offers, passengers, platform_airline_intelligence, platform_airline_policy_ingestion, platform_blueprint, platform_documents, platform_gds_parser, platform_reference, platform_rules_services, platform_service_catalogue, platform_service_taxonomy, portal, refunds_exchanges, reference, request_intakes, requests, trips, websites
from services.blueprint_adoption_service import get_blueprint_adoption_map, get_blueprint_gap_summary, get_blueprint_route_policy
from services.pdf_rendering_service import pdf_capabilities
from services.reference_data_service import REFERENCE_DOMAINS, country_enrichment_complete
from services.reference_domain_usage_service import list_domain_usage, reference_action_required
from services.reference_import_template_service import list_import_templates
from services.agency_feature_flag_bundle_service import DEFAULT_FEATURE_FLAG_BUNDLES
from services.capability_catalog_service import DEFAULT_CAPABILITY_CATALOG
from services.feature_bundle_rollout_plan_service import PLAN_STAGES
from services.feature_bundle_rollout_readiness_service import READINESS_STATUSES
from services.rollout_dashboard_service import DASHBOARD_SECTIONS
from services.saas_subscription_service import AGENCY_MODULE_VISIBILITY_CATALOG, PHASE_LABEL
from services.secret_service import check_secret
from services.seed_service import seed_core_data

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title="AeroAssist AgencyOS API",
    version="0.1.0",
    description="AeroAssist AgencyOS API foundation through Phase 40.3 rollout dashboard foundation.",
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
        "phase": PHASE_LABEL,
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
    booking_import_draft_count = await database.collection("booking_import_drafts").count()
    trip_change_operation_count = await database.collection("trip_change_operations").count()
    ticket_record_count = await database.collection("ticket_records").count()
    ticket_coupon_count = await database.collection("ticket_coupons").count()
    emd_record_count = await database.collection("emd_records").count()
    emd_coupon_count = await database.collection("emd_coupons").count()
    ticket_draft_count = await database.collection("ticket_records").count({"issue_status": "draft"})
    ticket_issued_count = await database.collection("ticket_records").count({"issue_status": "issued"})
    emd_draft_count = await database.collection("emd_records").count({"issue_status": "draft"})
    emd_issued_count = await database.collection("emd_records").count({"issue_status": "issued"})
    ticket_exchange_operation_count = await database.collection("ticket_exchange_operations").count()
    emd_exchange_operation_count = await database.collection("emd_exchange_operations").count()
    ai_trace_event_count = await database.collection("ai_trace_events").count()
    adm_risk_event_count = await database.collection("adm_risk_events").count()
    gds_parse_sample_count = await database.collection("gds_parse_samples").count()
    parser_profile_count = await database.collection("gds_parser_profiles").count()
    parser_version_count = await database.collection("gds_parser_versions").count()
    parser_run_count = await database.collection("gds_parser_runs").count()
    parsed_entity_count = await database.collection("gds_parsed_entities").count()
    parse_correction_count = await database.collection("gds_parse_corrections").count()
    training_sample_count = await database.collection("gds_parse_training_samples").count()
    parser_evaluation_run_count = await database.collection("gds_parser_evaluation_runs").count()
    low_confidence_parser_run_count = await database.collection("gds_parser_runs").count({"parse_status": "manual_review_required"})
    approved_training_sample_count = await database.collection("gds_parse_training_samples").count({"sample_status": "approved"})
    airline_brand_asset_count = await database.collection("airline_brand_assets").count()
    policy_sources = await database.collection("airline_policy_sources").find_many()
    policy_source_count = len(policy_sources)
    policy_section_count = await database.collection("airline_policy_sections").count()
    policy_extraction_run_count = await database.collection("airline_policy_extraction_runs").count()
    extracted_rule_candidate_count = await database.collection("airline_policy_extracted_rules").count()
    extracted_price_candidate_count = await database.collection("airline_policy_extracted_prices").count()
    extracted_communication_candidate_count = await database.collection("airline_policy_extracted_communication_rules").count()
    extracted_emd_rule_candidate_count = await database.collection("airline_policy_extracted_emd_rules").count()
    extracted_exception_candidate_count = await database.collection("airline_policy_extracted_exceptions").count()
    policy_review_correction_count = await database.collection("airline_policy_review_corrections").count()
    approved_knowledge_record_count = await database.collection("airline_policy_approved_knowledge_records").count()
    pending_policy_source_count = len([item for item in policy_sources if item.get("ingestion_status") in {"draft", "extracted", "reviewed"}])
    approved_policy_source_count = len([item for item in policy_sources if item.get("ingestion_status") == "approved"])
    rejected_policy_source_count = len([item for item in policy_sources if item.get("ingestion_status") == "rejected"])
    taxonomy_domain_count = await database.collection("canonical_service_domains").count()
    taxonomy_family_count = await database.collection("canonical_service_families").count()
    taxonomy_variant_count = await database.collection("canonical_service_variants").count()
    taxonomy_alias_count = await database.collection("airline_service_aliases").count()
    taxonomy_applicability_dimension_count = await database.collection("service_applicability_dimensions").count()
    taxonomy_outcome_type_count = await database.collection("service_policy_outcome_types").count()
    taxonomy_mapping_rule_count = await database.collection("service_taxonomy_mapping_rules").count()
    taxonomy_candidate_link_count = await database.collection("policy_candidate_taxonomy_links").count()
    taxonomy_review_correction_count = await database.collection("service_taxonomy_review_corrections").count()
    mechanics_communication_rule_count = await database.collection("airline_service_communication_rules").count()
    mechanics_ssr_osi_template_count = await database.collection("ssr_osi_templates").count()
    mechanics_ssr_osi_requirement_count = await database.collection("ssr_osi_requirements").count()
    mechanics_status_recognition_rule_count = await database.collection("ssr_status_recognition_rules").count()
    mechanics_rejection_pattern_count = await database.collection("airline_rejection_patterns").count()
    mechanics_payment_rule_count = await database.collection("airline_service_payment_rules").count()
    mechanics_emd_issuance_rule_count = await database.collection("airline_emd_issuance_rules").count()
    mechanics_rfic_rfisc_mapping_count = await database.collection("airline_rfic_rfisc_mappings").count()
    mechanics_emd_interline_rule_count = await database.collection("airline_emd_interline_rules").count()
    mechanics_emd_lifecycle_rule_count = await database.collection("airline_emd_lifecycle_rules").count()
    mechanics_candidate_link_count = await database.collection("policy_candidate_mechanics_links").count()
    ancillary_pricing_rule_count = await database.collection("airline_ancillary_pricing_rules").count()
    ancillary_price_component_count = await database.collection("airline_ancillary_price_components").count()
    ancillary_pricing_applicability_count = await database.collection("airline_ancillary_pricing_applicability").count()
    ancillary_pricing_matrix_count = await database.collection("airline_ancillary_pricing_matrices").count()
    ancillary_pricing_matrix_row_count = await database.collection("airline_ancillary_pricing_matrix_rows").count()
    airline_service_exception_rule_count = await database.collection("airline_service_exception_rules").count()
    price_quote_scenario_count = await database.collection("airline_service_price_quote_scenarios").count()
    price_quote_result_count = await database.collection("airline_service_price_quote_results").count()
    candidate_pricing_link_count = await database.collection("policy_candidate_pricing_links").count()
    policy_comparison_profile_count = await database.collection("airline_policy_comparison_profiles").count()
    policy_comparison_snapshot_count = await database.collection("airline_policy_comparison_snapshots").count()
    policy_comparison_row_count = await database.collection("airline_policy_comparison_rows").count()
    service_advisor_scenario_count = await database.collection("airline_service_advisor_scenarios").count()
    service_advisor_result_count = await database.collection("airline_service_advisor_results").count()
    policy_comparison_saved_view_count = await database.collection("airline_policy_comparison_saved_views").count()
    offer_policy_advisor_context_count = await database.collection("offer_policy_advisor_contexts").count()
    offer_policy_advisor_airline_row_count = await database.collection("offer_policy_advisor_airline_rows").count()
    offer_policy_advisor_warning_count = await database.collection("offer_policy_advisor_warnings").count()
    offer_policy_advisor_decision_note_count = await database.collection("offer_policy_advisor_decision_notes").count()
    offer_policy_advisor_saved_snapshot_count = await database.collection("offer_policy_advisor_saved_snapshots").count()
    offer_decision_pack_count = await database.collection("offer_decision_packs").count()
    offer_decision_pack_option_count = await database.collection("offer_decision_pack_options").count()
    offer_decision_pack_evidence_count = await database.collection("offer_decision_pack_evidence").count()
    offer_decision_pack_warning_count = await database.collection("offer_decision_pack_warnings").count()
    offer_decision_pack_review_note_count = await database.collection("offer_decision_pack_review_notes").count()
    offer_decision_pack_snapshot_count = await database.collection("offer_decision_pack_snapshots").count()
    offer_decision_explanation_count = await database.collection("offer_decision_explanations").count()
    offer_decision_timeline_event_count = await database.collection("offer_decision_timeline_events").count()
    offer_decision_evidence_reference_count = await database.collection("offer_decision_evidence_references").count()
    offer_decision_reason_count = await database.collection("offer_decision_reasons").count()
    offer_decision_acknowledgement_count = await database.collection("offer_decision_acknowledgements").count()
    offer_decision_audit_snapshot_count = await database.collection("offer_decision_audit_snapshots").count()
    offer_decision_export_count = await database.collection("offer_decision_exports").count()
    offer_decision_export_section_count = await database.collection("offer_decision_export_sections").count()
    offer_decision_export_artifact_count = await database.collection("offer_decision_export_artifacts").count()
    offer_decision_export_recipient_draft_count = await database.collection("offer_decision_export_recipient_drafts").count()
    offer_decision_export_audit_event_count = await database.collection("offer_decision_export_audit_events").count()
    offer_decision_export_preview_count = await database.collection("offer_decision_export_previews").count()
    offer_decision_export_preview_section_count = await database.collection("offer_decision_export_preview_sections").count()
    offer_decision_export_preview_block_count = await database.collection("offer_decision_export_preview_blocks").count()
    offer_decision_export_preview_validation_count = await database.collection("offer_decision_export_preview_validations").count()
    offer_decision_export_preview_snapshot_count = await database.collection("offer_decision_export_preview_snapshots").count()
    offer_decision_export_approval_count = await database.collection("offer_decision_export_approvals").count()
    offer_decision_export_approval_checkpoint_count = await database.collection("offer_decision_export_approval_checkpoints").count()
    offer_decision_export_release_readiness_count = await database.collection("offer_decision_export_release_readiness").count()
    offer_decision_export_release_hold_count = await database.collection("offer_decision_export_release_holds").count()
    offer_decision_export_release_snapshot_count = await database.collection("offer_decision_export_release_snapshots").count()
    offer_decision_export_delivery_handoff_count = await database.collection("offer_decision_export_delivery_handoffs").count()
    offer_decision_export_delivery_recipient_count = await database.collection("offer_decision_export_delivery_recipients").count()
    offer_decision_export_delivery_attachment_count = await database.collection("offer_decision_export_delivery_attachments").count()
    offer_decision_export_delivery_instruction_count = await database.collection("offer_decision_export_delivery_instructions").count()
    offer_decision_export_delivery_snapshot_count = await database.collection("offer_decision_export_delivery_snapshots").count()
    offer_decision_export_delivery_outcome_count = await database.collection("offer_decision_export_delivery_outcomes").count()
    offer_decision_export_delivery_outcome_event_count = await database.collection("offer_decision_export_delivery_outcome_events").count()
    offer_decision_export_delivery_receipt_count = await database.collection("offer_decision_export_delivery_receipts").count()
    offer_decision_export_delivery_issue_count = await database.collection("offer_decision_export_delivery_issues").count()
    offer_decision_export_delivery_outcome_snapshot_count = await database.collection("offer_decision_export_delivery_outcome_snapshots").count()
    offer_decision_export_audit_review_count = await database.collection("offer_decision_export_audit_reviews").count()
    offer_decision_export_audit_review_finding_count = await database.collection("offer_decision_export_audit_review_findings").count()
    offer_decision_export_audit_review_checklist_item_count = await database.collection("offer_decision_export_audit_review_checklist_items").count()
    offer_decision_export_audit_review_snapshot_count = await database.collection("offer_decision_export_audit_review_snapshots").count()
    offer_decision_export_governance_record_count = await database.collection("offer_decision_export_governance_records").count()
    offer_decision_export_governance_rule_count = await database.collection("offer_decision_export_governance_rules").count()
    offer_decision_export_retention_policy_count = await database.collection("offer_decision_export_retention_policies").count()
    offer_decision_export_legal_basis_count = await database.collection("offer_decision_export_legal_bases").count()
    offer_decision_export_archive_status_count = await database.collection("offer_decision_export_archive_statuses").count()
    offer_decision_export_governance_exception_count = await database.collection("offer_decision_export_governance_exceptions").count()
    offer_decision_export_governance_snapshot_count = await database.collection("offer_decision_export_governance_snapshots").count()
    offer_decision_export_compliance_evidence_count = await database.collection("offer_decision_export_compliance_evidence").count()
    offer_decision_export_compliance_requirement_count = await database.collection("offer_decision_export_compliance_requirements").count()
    offer_decision_export_compliance_check_count = await database.collection("offer_decision_export_compliance_checks").count()
    offer_decision_export_compliance_result_count = await database.collection("offer_decision_export_compliance_results").count()
    offer_decision_export_compliance_exception_count = await database.collection("offer_decision_export_compliance_exceptions").count()
    offer_decision_export_compliance_snapshot_count = await database.collection("offer_decision_export_compliance_snapshots").count()
    airline_intelligence_data_pack_count = await database.collection("airline_intelligence_data_packs").count()
    airline_intelligence_data_pack_item_count = await database.collection("airline_intelligence_data_pack_items").count()
    airline_intelligence_data_pack_validation_issue_count = await database.collection("airline_intelligence_data_pack_validation_issues").count()
    airline_intelligence_data_pack_import_run_count = await database.collection("airline_intelligence_data_pack_import_runs").count()
    airline_intelligence_data_pack_review_note_count = await database.collection("airline_intelligence_data_pack_review_notes").count()
    airline_intelligence_coverage_snapshot_count = await database.collection("airline_intelligence_coverage_snapshots").count()
    airline_intelligence_data_pack_review_count = await database.collection("airline_intelligence_data_pack_reviews").count()
    airline_intelligence_data_pack_review_checklist_item_count = await database.collection("airline_intelligence_data_pack_review_checklist_items").count()
    airline_intelligence_data_pack_field_mapping_count = await database.collection("airline_intelligence_data_pack_field_mappings").count()
    airline_intelligence_data_pack_conflict_count = await database.collection("airline_intelligence_data_pack_conflicts").count()
    airline_intelligence_data_pack_open_conflict_count = await database.collection("airline_intelligence_data_pack_conflicts").count({"status": "open"})
    airline_intelligence_data_pack_promotion_readiness_count = await database.collection("airline_intelligence_data_pack_promotion_readiness").count()
    airline_intelligence_data_pack_review_snapshot_count = await database.collection("airline_intelligence_data_pack_review_snapshots").count()
    airline_intelligence_data_pack_promotion_ready_records = await database.collection("airline_intelligence_data_pack_promotion_readiness").find_many({"ready_for_promotion": True})
    airline_intelligence_knowledge_version_count = await database.collection("airline_intelligence_knowledge_versions").count()
    airline_intelligence_knowledge_version_item_count = await database.collection("airline_intelligence_knowledge_version_items").count()
    airline_intelligence_knowledge_release_channel_count = await database.collection("airline_intelligence_knowledge_release_channels").count()
    airline_intelligence_knowledge_release_assignment_count = await database.collection("airline_intelligence_knowledge_release_assignments").count()
    airline_intelligence_knowledge_version_comparison_count = await database.collection("airline_intelligence_knowledge_version_comparisons").count()
    airline_intelligence_knowledge_rollback_plan_count = await database.collection("airline_intelligence_knowledge_rollback_plans").count()
    airline_intelligence_knowledge_version_snapshot_count = await database.collection("airline_intelligence_knowledge_version_snapshots").count()
    airline_intelligence_knowledge_frozen_version_count = await database.collection("airline_intelligence_knowledge_versions").count({"status": "frozen"})
    airline_intelligence_knowledge_approved_version_count = await database.collection("airline_intelligence_knowledge_versions").count({"status": "approved"})
    airline_intelligence_knowledge_published_metadata_version_count = await database.collection("airline_intelligence_knowledge_versions").count({"status": "published"})
    airline_intelligence_knowledge_agency_visible_version_count = await database.collection("airline_intelligence_knowledge_versions").count({"agency_visibility_mode": "visible"})
    airline_intelligence_agency_consumption_profile_count = await database.collection("airline_intelligence_agency_consumption_profiles").count()
    airline_intelligence_agency_assignment_view_count = await database.collection("airline_intelligence_agency_knowledge_assignment_views").count()
    airline_intelligence_agency_usage_readiness_count = await database.collection("airline_intelligence_agency_usage_readiness").count()
    airline_intelligence_agency_consumption_note_count = await database.collection("airline_intelligence_agency_consumption_notes").count()
    airline_intelligence_agency_consumption_snapshot_count = await database.collection("airline_intelligence_agency_consumption_snapshots").count()
    airline_intelligence_agency_visible_profile_count = await database.collection("airline_intelligence_agency_consumption_profiles").count({"status": "visible", "visible_to_agency": True})
    saas_subscription_plan_count = await database.collection("saas_subscription_plans").count()
    saas_plan_entitlement_count = await database.collection("saas_plan_entitlements").count()
    agency_subscription_assignment_count = await database.collection("agency_subscription_assignments").count()
    agency_entitlement_readiness_count = await database.collection("agency_entitlement_readiness").count()
    agency_subscription_review_note_count = await database.collection("agency_subscription_review_notes").count()
    agency_subscription_snapshot_count = await database.collection("agency_subscription_snapshots").count()
    agency_feature_flag_count = await database.collection("agency_feature_flags").count()
    agency_feature_flag_review_count = await database.collection("agency_feature_flag_reviews").count()
    agency_feature_flag_snapshot_count = await database.collection("agency_feature_flag_snapshots").count()
    agency_feature_flag_audit_count = await database.collection("agency_feature_flag_audits").count()
    agency_feature_flag_readiness_count = await database.collection("agency_feature_flag_readiness").count()
    agency_feature_flag_bundle_count = await database.collection("agency_feature_flag_bundles").count()
    agency_feature_flag_bundle_review_count = await database.collection("agency_feature_flag_bundle_reviews").count()
    agency_feature_bundle_assignment_count = await database.collection("agency_feature_bundle_assignments").count()
    agency_feature_bundle_assignment_history_count = await database.collection("agency_feature_bundle_assignment_history").count()
    agency_feature_bundle_rollout_readiness_records = await database.collection("agency_feature_bundle_rollout_readiness").find_many()
    agency_feature_bundle_rollout_readiness_count = len(agency_feature_bundle_rollout_readiness_records)
    agency_feature_bundle_rollout_readiness_status_counts = {
        status: len([item for item in agency_feature_bundle_rollout_readiness_records if item.get("readiness_status") == status])
        for status in READINESS_STATUSES
    }
    agency_feature_bundle_rollout_plan_records = await database.collection("agency_feature_bundle_rollout_plans").find_many()
    agency_feature_bundle_rollout_plan_count = len(agency_feature_bundle_rollout_plan_records)
    agency_feature_bundle_rollout_plan_stage_counts = {
        stage: len([item for item in agency_feature_bundle_rollout_plan_records if item.get("rollout_stage") == stage])
        for stage in PLAN_STAGES
    }
    rollout_dashboard_view_count = await database.collection("rollout_dashboard_views").count()
    rollout_dashboard_snapshot_count = await database.collection("rollout_dashboard_snapshots").count()
    capability_catalog_count = await database.collection("capability_catalog").count()
    airline_intelligence_data_packs = await database.collection("airline_intelligence_data_packs").find_many()
    airline_data_packs_needing_review_count = len([item for item in airline_intelligence_data_packs if item.get("verification_status") in {"draft", "needs_review"}])
    airline_data_pack_approved_count = len([item for item in airline_intelligence_data_packs if item.get("verification_status") == "approved"])
    airline_data_pack_demo_count = len([item for item in airline_intelligence_data_packs if item.get("is_demo_data")])
    airline_data_pack_agency_display_safe_count = len([item for item in airline_intelligence_data_packs if item.get("safe_for_agency_display")])
    airline_data_pack_cms_display_safe_count = len([item for item in airline_intelligence_data_packs if item.get("safe_for_cms_display")])
    airline_data_pack_client_portal_safe_count = len([item for item in airline_intelligence_data_packs if item.get("safe_for_client_portal_later")])
    airline_data_pack_offer_builder_safe_count = len([item for item in airline_intelligence_data_packs if item.get("safe_for_offer_builder")])
    document_template_count = await database.collection("document_templates").count()
    document_render_job_count = await database.collection("document_render_jobs").count()
    document_package_count = await database.collection("document_packages").count()
    document_share_record_count = await database.collection("document_share_records").count()
    rendered_document_count = await database.collection("rendered_documents").count()
    document_export_count = await database.collection("document_exports").count()
    blueprint_adoption = get_blueprint_adoption_map()
    blueprint_gaps = get_blueprint_gap_summary()
    blueprint_route_policy = get_blueprint_route_policy()
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
        "phase": PHASE_LABEL,
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
            "manual_booking_workspace_enabled": True,
            "structured_manual_booking_form_enabled": True,
            "structured_import_preview_enabled": True,
            "raw_json_advanced_fallback_enabled": True,
            "standalone_booking_record_enabled": True,
            "booking_import_draft_enabled": True,
            "booking_import_parser_stub_enabled": True,
            "existing_trip_change_booking_enabled": True,
            "provider_execution_disabled": True,
            "service_catalogue_booking_snapshot_enabled": True,
            "trip_booking_workspace_link_enabled": True,
            "agency_booking_workspace_ui_enabled": True,
            "booking_workspace_count": booking_workspace_count,
            "booking_record_count": booking_record_count,
            "booking_import_draft_count": booking_import_draft_count,
            "booking_timeline_event_count": booking_timeline_event_count,
            "booking_workspace_ready_count": booking_workspace_ready_count,
            "booking_workspace_blocked_count": booking_workspace_blocked_count,
            "booking_workspace_cancelled_count": booking_workspace_cancelled_count,
            "readiness_required": False,
            "diagnostic": "Booking workspaces and PNR mirrors can be created from readiness packages, manual entry, imports, or existing-trip change operations; provider execution remains disabled.",
        },
        "ticket_emd_foundation": {
            "ticket_record_foundation_enabled": True,
            "ticket_coupon_foundation_enabled": True,
            "emd_record_foundation_enabled": True,
            "emd_coupon_foundation_enabled": True,
            "ticket_from_booking_enabled": True,
            "emd_from_booking_service_enabled": True,
            "ticket_emd_readiness_enabled": True,
            "manual_ticket_mirror_enabled": True,
            "manual_emd_mirror_enabled": True,
            "manual_ticket_creation_enabled": True,
            "structured_manual_ticket_form_enabled": True,
            "standalone_ticket_creation_enabled": True,
            "manual_emd_creation_enabled": True,
            "structured_manual_emd_form_enabled": True,
            "raw_json_advanced_fallback_enabled": True,
            "standalone_emd_creation_enabled": True,
            "ticket_emd_import_association_ready": True,
            "ticket_exchange_operation_foundation_enabled": True,
            "emd_exchange_operation_foundation_enabled": True,
            "exchange_reissue_mirror_enabled": True,
            "service_catalogue_emd_mapping_enabled": True,
            "provider_ticketing_disabled": True,
            "provider_emd_issuance_disabled": True,
            "agency_ticket_emd_ui_enabled": True,
            "ticket_record_count": ticket_record_count,
            "ticket_coupon_count": ticket_coupon_count,
            "emd_record_count": emd_record_count,
            "emd_coupon_count": emd_coupon_count,
            "ticket_draft_count": ticket_draft_count,
            "ticket_issued_count": ticket_issued_count,
            "emd_draft_count": emd_draft_count,
            "emd_issued_count": emd_issued_count,
            "ticket_exchange_operation_count": ticket_exchange_operation_count,
            "emd_exchange_operation_count": emd_exchange_operation_count,
            "readiness_required": False,
            "diagnostic": "Ticket and EMD records are internal mirrors only; provider ticketing and EMD issuance are disabled.",
        },
        "change_exchange_foundation": {
            "trip_change_operation_foundation_enabled": True,
            "ticket_exchange_operation_foundation_enabled": True,
            "emd_exchange_operation_foundation_enabled": True,
            "existing_trip_change_booking_enabled": True,
            "request_offer_change_linkage_ready": True,
            "provider_exchange_execution_disabled": True,
            "provider_refund_execution_disabled": True,
            "provider_void_execution_disabled": True,
            "booking_import_draft_count": booking_import_draft_count,
            "trip_change_operation_count": trip_change_operation_count,
            "ticket_exchange_operation_count": ticket_exchange_operation_count,
            "emd_exchange_operation_count": emd_exchange_operation_count,
            "readiness_required": False,
            "diagnostic": "Change, exchange, refund, and void workflows are internal planning/mirror records only; no provider execution is enabled.",
        },
        "document_foundation": {
            "document_template_foundation_enabled": True,
            "default_document_templates_enabled": True,
            "document_context_builder_enabled": True,
            "document_render_job_enabled": True,
            "document_package_enabled": True,
            "document_share_record_foundation_enabled": True,
            "agency_documents_ui_enabled": True,
            "trip_documents_entrypoint_enabled": True,
            "booking_documents_entrypoint_enabled": True,
            "ticket_emd_documents_entrypoint_enabled": True,
            "offer_documents_entrypoint_enabled": True,
            "import_review_document_entrypoint_enabled": True,
            "html_document_preview_enabled": True,
            "pdf_export_required": False,
            "live_delivery_disabled": True,
            "e_signature_disabled": True,
            "payment_invoice_accounting_disabled": True,
            "document_template_count": document_template_count,
            "document_render_job_count": document_render_job_count,
            "document_package_count": document_package_count,
            "document_share_record_count": document_share_record_count,
            "rendered_document_count": rendered_document_count,
            "document_export_count": document_export_count,
            "readiness_required": False,
            "diagnostic": "Document templates, context previews, render jobs, packages, and internal/manual share records are enabled; live delivery, e-signature, provider execution, payments, invoices/accounting, and settlement remain disabled.",
        },
        "gds_parser_foundation": {
            "parser_profile_foundation_enabled": True,
            "parser_version_foundation_enabled": True,
            "parser_run_foundation_enabled": True,
            "parsed_entity_foundation_enabled": True,
            "parse_correction_foundation_enabled": True,
            "training_sample_foundation_enabled": True,
            "parser_evaluation_foundation_enabled": True,
            "agency_gds_parser_ui_enabled": True,
            "platform_gds_parser_governance_ui_enabled": True,
            "booking_import_parser_integration_enabled": True,
            "parser_document_context_enabled": True,
            "conservative_parser_rules_enabled": True,
            "manual_review_required_for_low_confidence": True,
            "explicit_import_required": True,
            "live_gds_connection_disabled": True,
            "live_provider_execution_disabled": True,
            "external_ai_parser_disabled": True,
            "parser_profile_count": parser_profile_count,
            "parser_version_count": parser_version_count,
            "parser_run_count": parser_run_count,
            "parsed_entity_count": parsed_entity_count,
            "parse_correction_count": parse_correction_count,
            "training_sample_count": training_sample_count,
            "parser_evaluation_run_count": parser_evaluation_run_count,
            "low_confidence_parser_run_count": low_confidence_parser_run_count,
            "approved_training_sample_count": approved_training_sample_count,
            "readiness_required": False,
            "diagnostic": "Governed GDS parser profiles, versions, runs, entities, corrections, training samples, and evaluations are enabled. Parsing is deterministic and conservative; import remains explicit and no live GDS/provider/AI parser connection is enabled.",
        },
        "airline_policy_ingestion_foundation": {
            "policy_source_foundation_enabled": True,
            "policy_section_detection_enabled": True,
            "policy_extraction_run_enabled": True,
            "extracted_rule_candidates_enabled": True,
            "extracted_price_candidates_enabled": True,
            "extracted_communication_candidates_enabled": True,
            "extracted_emd_rule_candidates_enabled": True,
            "extracted_exception_candidates_enabled": True,
            "review_correction_foundation_enabled": True,
            "approved_knowledge_foundation_enabled": True,
            "platform_policy_ingestion_ui_enabled": True,
            "agency_policy_library_ui_enabled": True,
            "document_policy_summary_context_enabled": True,
            "deterministic_extraction_enabled": True,
            "external_ai_policy_extraction_disabled": True,
            "auto_promotion_disabled": True,
            "platform_review_required_for_global_knowledge": True,
            "policy_source_count": policy_source_count,
            "policy_section_count": policy_section_count,
            "policy_extraction_run_count": policy_extraction_run_count,
            "extracted_rule_candidate_count": extracted_rule_candidate_count,
            "extracted_price_candidate_count": extracted_price_candidate_count,
            "extracted_communication_candidate_count": extracted_communication_candidate_count,
            "extracted_emd_rule_candidate_count": extracted_emd_rule_candidate_count,
            "extracted_exception_candidate_count": extracted_exception_candidate_count,
            "policy_review_correction_count": policy_review_correction_count,
            "approved_knowledge_record_count": approved_knowledge_record_count,
            "pending_policy_source_count": pending_policy_source_count,
            "approved_policy_source_count": approved_policy_source_count,
            "rejected_policy_source_count": rejected_policy_source_count,
            "readiness_required": False,
            "diagnostic": "Airline policy ingestion stores raw sources, detected sections, deterministic extraction candidates, human review corrections, and approved knowledge records. External AI extraction and automatic global promotion remain disabled.",
        },
        "service_taxonomy_foundation": {
            "taxonomy_domains_enabled": True,
            "taxonomy_families_enabled": True,
            "taxonomy_variants_enabled": True,
            "airline_service_aliases_enabled": True,
            "applicability_dimensions_enabled": True,
            "outcome_types_enabled": True,
            "mapping_rules_enabled": True,
            "policy_candidate_taxonomy_links_enabled": True,
            "taxonomy_review_corrections_enabled": True,
            "platform_service_taxonomy_ui_enabled": True,
            "agency_service_taxonomy_ui_enabled": True,
            "deterministic_taxonomy_mapping_enabled": True,
            "external_ai_taxonomy_mapping_disabled": True,
            "agency_auto_promotion_disabled": True,
            "taxonomy_seeding_enabled": True,
            "domain_count": taxonomy_domain_count,
            "family_count": taxonomy_family_count,
            "variant_count": taxonomy_variant_count,
            "alias_count": taxonomy_alias_count,
            "applicability_dimension_count": taxonomy_applicability_dimension_count,
            "outcome_type_count": taxonomy_outcome_type_count,
            "mapping_rule_count": taxonomy_mapping_rule_count,
            "candidate_link_count": taxonomy_candidate_link_count,
            "review_correction_count": taxonomy_review_correction_count,
            "readiness_required": False,
            "diagnostic": "Canonical service taxonomy maps airline policy terms, commercial labels, SSR/GDS codes, and extracted policy candidates into normalized domains, families, and variants only; it does not perform SSR/OSI communication mapping, EMD/RFIC/RFISC payment mechanics, pricing matrices, provider execution, or live GDS/NDC connectivity.",
        },
        "service_mechanics_mapping_foundation": {
            "communication_rules_enabled": True,
            "ssr_osi_templates_enabled": True,
            "ssr_osi_requirements_enabled": True,
            "ssr_status_recognition_enabled": True,
            "airline_rejection_patterns_enabled": True,
            "payment_rules_enabled": True,
            "emd_issuance_rules_enabled": True,
            "rfic_rfisc_mappings_enabled": True,
            "emd_interline_rules_enabled": True,
            "emd_lifecycle_rules_enabled": True,
            "candidate_mechanics_links_enabled": True,
            "platform_service_mechanics_ui_enabled": True,
            "agency_service_mechanics_ui_enabled": True,
            "deterministic_mechanics_lookup_enabled": True,
            "communication_payment_separation_enforced": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "agency_auto_promotion_disabled": True,
            "communication_rule_count": mechanics_communication_rule_count,
            "ssr_osi_template_count": mechanics_ssr_osi_template_count,
            "ssr_osi_requirement_count": mechanics_ssr_osi_requirement_count,
            "status_recognition_rule_count": mechanics_status_recognition_rule_count,
            "rejection_pattern_count": mechanics_rejection_pattern_count,
            "payment_rule_count": mechanics_payment_rule_count,
            "emd_issuance_rule_count": mechanics_emd_issuance_rule_count,
            "rfic_rfisc_mapping_count": mechanics_rfic_rfisc_mapping_count,
            "emd_interline_rule_count": mechanics_emd_interline_rule_count,
            "emd_lifecycle_rule_count": mechanics_emd_lifecycle_rule_count,
            "candidate_mechanics_link_count": mechanics_candidate_link_count,
            "readiness_required": False,
            "diagnostic": "Phase 36.9 maps canonical services to SSR/OSI communication and EMD/RFIC/RFISC payment mechanics separately. It is metadata-only and does not execute provider actions, issue tickets/EMDs, process payments, or perform settlement.",
        },
        "ancillary_pricing_exception_foundation": {
            "pricing_rules_enabled": True,
            "price_components_enabled": True,
            "pricing_applicability_enabled": True,
            "pricing_matrices_enabled": True,
            "pricing_matrix_rows_enabled": True,
            "service_exception_rules_enabled": True,
            "quote_scenarios_enabled": True,
            "quote_results_enabled": True,
            "candidate_pricing_links_enabled": True,
            "platform_ancillary_pricing_ui_enabled": True,
            "agency_ancillary_pricing_ui_enabled": True,
            "deterministic_quote_evaluation_enabled": True,
            "exception_engine_expansion_enabled": True,
            "pricing_mechanics_reference_enabled": True,
            "invoice_payment_settlement_disabled": True,
            "emd_issuance_disabled": True,
            "provider_execution_disabled": True,
            "agency_auto_promotion_disabled": True,
            "pricing_rule_count": ancillary_pricing_rule_count,
            "price_component_count": ancillary_price_component_count,
            "pricing_applicability_count": ancillary_pricing_applicability_count,
            "pricing_matrix_count": ancillary_pricing_matrix_count,
            "pricing_matrix_row_count": ancillary_pricing_matrix_row_count,
            "service_exception_rule_count": airline_service_exception_rule_count,
            "quote_scenario_count": price_quote_scenario_count,
            "quote_result_count": price_quote_result_count,
            "candidate_pricing_link_count": candidate_pricing_link_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.0 adds policy-based ancillary pricing estimates and expanded exception metadata. It does not create invoices, process payments, perform settlement, issue EMDs/tickets, or execute providers.",
        },
        "policy_comparison_service_advisor_foundation": {
            "comparison_profiles_enabled": True,
            "comparison_snapshots_enabled": True,
            "comparison_rows_enabled": True,
            "advisor_scenarios_enabled": True,
            "advisor_results_enabled": True,
            "saved_views_enabled": True,
            "platform_policy_comparison_ui_enabled": True,
            "agency_policy_comparison_ui_enabled": True,
            "agency_airline_service_advisor_ui_enabled": True,
            "deterministic_service_advisor_enabled": True,
            "operational_complexity_scoring_enabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "agency_global_mutation_blocked": True,
            "comparison_profile_count": policy_comparison_profile_count,
            "comparison_snapshot_count": policy_comparison_snapshot_count,
            "comparison_row_count": policy_comparison_row_count,
            "advisor_scenario_count": service_advisor_scenario_count,
            "advisor_result_count": service_advisor_result_count,
            "saved_view_count": policy_comparison_saved_view_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.1 adds metadata-only airline policy comparison and service advisor records. Complexity scores are operational indicators, not automatic airline recommendations; provider execution, EMD issuance, payments, invoices, and settlement remain disabled.",
        },
        "offer_policy_advisor_integration_foundation": {
            "offer_advisor_contexts_enabled": True,
            "offer_advisor_airline_rows_enabled": True,
            "offer_advisor_warnings_enabled": True,
            "offer_advisor_decision_notes_enabled": True,
            "offer_advisor_saved_snapshots_enabled": True,
            "platform_offer_policy_advisor_ui_enabled": True,
            "agency_offer_policy_advisor_ui_enabled": True,
            "deterministic_offer_advisor_integration_enabled": True,
            "auto_recommendation_disabled": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "agency_global_mutation_blocked": True,
            "context_count": offer_policy_advisor_context_count,
            "airline_row_count": offer_policy_advisor_airline_row_count,
            "warning_count": offer_policy_advisor_warning_count,
            "decision_note_count": offer_policy_advisor_decision_note_count,
            "saved_snapshot_count": offer_policy_advisor_saved_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.2 links offer workspaces/options to metadata-only policy comparison and service advisor context. It does not auto-select airlines, alter offer pricing, book, issue, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_builder_advisor_consumption_decision_pack_foundation": {
            "decision_packs_enabled": True,
            "option_evidence_enabled": True,
            "decision_pack_warnings_enabled": True,
            "review_notes_enabled": True,
            "immutable_snapshots_enabled": True,
            "advisor_snapshot_consumption_enabled": True,
            "offer_builder_consumption_enabled": True,
            "agency_decision_pack_ui_enabled": True,
            "platform_decision_pack_ui_enabled": True,
            "human_review_required_enabled": True,
            "auto_recommendation_disabled": True,
            "offer_price_mutation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "decision_pack_count": offer_decision_pack_count,
            "option_count": offer_decision_pack_option_count,
            "option_evidence_count": offer_decision_pack_evidence_count,
            "warning_count": offer_decision_pack_warning_count,
            "review_note_count": offer_decision_pack_review_note_count,
            "saved_snapshot_count": offer_decision_pack_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.3 consumes saved advisor evidence inside offer workflows and creates metadata-only decision packs for human review. It does not rank winners, mutate prices, book, issue tickets or EMDs, charge, invoice, settle, or execute providers.",
        },
        "offer_decision_explanation_foundation": {
            "decision_explanations_enabled": True,
            "decision_timeline_enabled": True,
            "decision_reasons_enabled": True,
            "evidence_reference_enabled": True,
            "acknowledgements_enabled": True,
            "immutable_snapshots_enabled": True,
            "agency_ui_enabled": True,
            "platform_ui_enabled": True,
            "human_review_only_enabled": True,
            "provider_execution_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_disabled": True,
            "payment_disabled": True,
            "invoice_disabled": True,
            "settlement_disabled": True,
            "automatic_recommendation_disabled": True,
            "explanations": offer_decision_explanation_count,
            "timeline_events": offer_decision_timeline_event_count,
            "reasons": offer_decision_reason_count,
            "evidence_references": offer_decision_evidence_reference_count,
            "acknowledgements": offer_decision_acknowledgement_count,
            "snapshots": offer_decision_audit_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.4 records human explanation, reason, evidence reference, acknowledgement, timeline, and immutable audit snapshot metadata for offer decision packs. It does not rank winners, mutate prices, book, issue tickets or EMDs, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_decision_export_foundation": {
            "decision_exports_enabled": True,
            "export_sections_enabled": True,
            "export_artifacts_enabled": True,
            "recipient_drafts_enabled": True,
            "export_audit_events_enabled": True,
            "pdf_export_metadata_enabled": True,
            "automatic_sending_disabled": True,
            "public_links_disabled": True,
            "offer_price_mutation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "export_count": offer_decision_export_count,
            "section_count": offer_decision_export_section_count,
            "artifact_count": offer_decision_export_artifact_count,
            "recipient_draft_count": offer_decision_export_recipient_draft_count,
            "audit_event_count": offer_decision_export_audit_event_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.5 creates metadata-only offer decision review export records and PDF metadata artifacts. It does not send email, create public links, mutate offers or prices, recommend airlines, book, issue tickets or EMDs, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_decision_export_preview_foundation": {
            "export_previews_enabled": True,
            "preview_sections_enabled": True,
            "preview_blocks_enabled": True,
            "preview_validations_enabled": True,
            "immutable_preview_snapshots_enabled": True,
            "agency_export_preview_ui_enabled": True,
            "platform_export_preview_ui_enabled": True,
            "metadata_only_rendering_enabled": True,
            "automatic_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_price_mutation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "preview_count": offer_decision_export_preview_count,
            "section_count": offer_decision_export_preview_section_count,
            "block_count": offer_decision_export_preview_block_count,
            "validation_count": offer_decision_export_preview_validation_count,
            "snapshot_count": offer_decision_export_preview_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.6 creates metadata-only render preview records for offer decision exports. It does not deliver PDFs, send email, create public links, mutate offers or prices, recommend airlines, book, issue tickets or EMDs, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_decision_export_release_readiness_foundation": {
            "export_approvals_enabled": True,
            "approval_checkpoints_enabled": True,
            "release_readiness_enabled": True,
            "release_holds_enabled": True,
            "immutable_release_snapshots_enabled": True,
            "agency_export_release_ui_enabled": True,
            "platform_export_release_ui_enabled": True,
            "human_approval_required_enabled": True,
            "automatic_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_price_mutation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "approval_count": offer_decision_export_approval_count,
            "checkpoint_count": offer_decision_export_approval_checkpoint_count,
            "readiness_count": offer_decision_export_release_readiness_count,
            "hold_count": offer_decision_export_release_hold_count,
            "snapshot_count": offer_decision_export_release_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.7 creates metadata-only human approval, checkpoint, manual release readiness, hold, and immutable release snapshot records for offer decision export previews. It does not send email, create public links, deliver real PDFs, mutate offers or prices, recommend airlines, book, issue tickets or EMDs, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_decision_export_manual_delivery_handoff_foundation": {
            "delivery_handoffs_enabled": True,
            "delivery_recipients_enabled": True,
            "delivery_attachment_metadata_enabled": True,
            "delivery_instructions_enabled": True,
            "immutable_delivery_snapshots_enabled": True,
            "agency_delivery_handoff_ui_enabled": True,
            "platform_delivery_handoff_ui_enabled": True,
            "manual_delivery_only_enabled": True,
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "handoff_count": offer_decision_export_delivery_handoff_count,
            "recipient_count": offer_decision_export_delivery_recipient_count,
            "attachment_count": offer_decision_export_delivery_attachment_count,
            "instruction_count": offer_decision_export_delivery_instruction_count,
            "snapshot_count": offer_decision_export_delivery_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.8 creates metadata-only manual delivery handoff records for approved offer decision exports. It records human handoff intent, recipient metadata, attachment metadata, instructions, and immutable snapshots; it does not send email or SMS, create public links, deliver real PDFs, mutate offers or prices, recommend airlines, book, create or alter PNRs, issue tickets or EMDs, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_decision_export_manual_delivery_outcome_foundation": {
            "delivery_outcomes_enabled": True,
            "delivery_outcome_events_enabled": True,
            "delivery_receipts_enabled": True,
            "delivery_issues_enabled": True,
            "immutable_outcome_snapshots_enabled": True,
            "agency_delivery_outcome_ui_enabled": True,
            "platform_delivery_outcome_ui_enabled": True,
            "manual_tracking_only_enabled": True,
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "outcome_count": offer_decision_export_delivery_outcome_count,
            "event_count": offer_decision_export_delivery_outcome_event_count,
            "receipt_count": offer_decision_export_delivery_receipt_count,
            "issue_count": offer_decision_export_delivery_issue_count,
            "snapshot_count": offer_decision_export_delivery_outcome_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 37.9 creates metadata-only manual delivery outcome tracking records after a human performs delivery outside AgencyOS. It records outcome status, human-entered events, receipt metadata, issue metadata, and immutable snapshots; it does not send email or SMS, create public links, deliver real PDFs, mutate offers or prices, recommend airlines, book, create or alter PNRs, issue tickets or EMDs, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_decision_export_audit_review_foundation": {
            "audit_reviews_enabled": True,
            "audit_review_findings_enabled": True,
            "audit_review_checklists_enabled": True,
            "immutable_audit_review_snapshots_enabled": True,
            "agency_audit_review_ui_enabled": True,
            "platform_audit_review_ui_enabled": True,
            "metadata_only_review_enabled": True,
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_price_mutation_disabled": True,
            "automatic_recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "review_count": offer_decision_export_audit_review_count,
            "finding_count": offer_decision_export_audit_review_finding_count,
            "checklist_item_count": offer_decision_export_audit_review_checklist_item_count,
            "snapshot_count": offer_decision_export_audit_review_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 38.0 creates metadata-only audit reviews over decision pack, explanation, export, preview, release readiness, manual handoff, and manual outcome records. It reviews completeness, approval trail, handoff trail, outcome trail, unresolved issues, and immutable snapshot coverage without email/SMS sending, public links, real PDF delivery, offer price mutation, automatic recommendation, provider execution, booking, PNR mutation, ticketing, EMD issuance, payment, invoice, settlement, scraping, or external AI.",
        },
        "offer_decision_export_governance_foundation": {
            "governance_records_enabled": True,
            "governance_rules_enabled": True,
            "retention_policies_enabled": True,
            "legal_bases_enabled": True,
            "archive_status_metadata_enabled": True,
            "governance_exceptions_enabled": True,
            "immutable_governance_snapshots_enabled": True,
            "agency_governance_ui_enabled": True,
            "platform_governance_ui_enabled": True,
            "metadata_only_governance_enabled": True,
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_mutation_disabled": True,
            "price_mutation_disabled": True,
            "recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_disabled": True,
            "invoice_disabled": True,
            "settlement_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
            "governance_record_count": offer_decision_export_governance_record_count,
            "rule_count": offer_decision_export_governance_rule_count,
            "retention_policy_count": offer_decision_export_retention_policy_count,
            "legal_basis_count": offer_decision_export_legal_basis_count,
            "archive_status_count": offer_decision_export_archive_status_count,
            "exception_count": offer_decision_export_governance_exception_count,
            "snapshot_count": offer_decision_export_governance_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 38.1 creates metadata-only governance records for offer decision exports, audit reviews, retention policies, legal bases, archive statuses, exceptions, and immutable governance snapshots. It does not send, deliver, mutate offers or prices, recommend, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external AI, or execute providers.",
        },
        "offer_decision_export_compliance_foundation": {
            "compliance_evidence_enabled": True,
            "compliance_requirements_enabled": True,
            "compliance_checks_enabled": True,
            "compliance_results_enabled": True,
            "compliance_exceptions_enabled": True,
            "immutable_compliance_snapshots_enabled": True,
            "agency_compliance_ui_enabled": True,
            "platform_compliance_ui_enabled": True,
            "metadata_only_enabled": True,
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_mutation_disabled": True,
            "price_mutation_disabled": True,
            "recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_disabled": True,
            "invoice_disabled": True,
            "settlement_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
            "evidence_count": offer_decision_export_compliance_evidence_count,
            "requirement_count": offer_decision_export_compliance_requirement_count,
            "check_count": offer_decision_export_compliance_check_count,
            "result_count": offer_decision_export_compliance_result_count,
            "exception_count": offer_decision_export_compliance_exception_count,
            "snapshot_count": offer_decision_export_compliance_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 38.2 creates metadata-only compliance evidence for offer decision exports and governance records. It records requirements, checks, pass/fail results, exceptions, and immutable compliance snapshots without sending, delivery, offer or price mutation, recommendation, booking, PNR mutation, ticketing, EMD issuance, payment, invoice, settlement, scraping, external AI, GDS execution, or provider execution.",
        },
        "airline_intelligence_data_pack_foundation": {
            "data_packs_enabled": True,
            "data_pack_items_enabled": True,
            "data_pack_validation_enabled": True,
            "data_pack_dry_runs_enabled": True,
            "data_pack_review_notes_enabled": True,
            "coverage_snapshots_enabled": True,
            "platform_data_pack_ui_enabled": True,
            "agency_coverage_ui_enabled": True,
            "agency_read_only_consumption_enabled": True,
            "crm_alignment_metadata_enabled": True,
            "cms_alignment_metadata_enabled": True,
            "client_portal_alignment_metadata_enabled": True,
            "offer_builder_alignment_metadata_enabled": True,
            "metadata_only_staging_enabled": True,
            "automatic_promotion_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
            "external_api_calls_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "public_client_portal_disabled": True,
            "public_cms_publishing_disabled": True,
            "automatic_sending_disabled": True,
            "data_pack_count": airline_intelligence_data_pack_count,
            "data_pack_item_count": airline_intelligence_data_pack_item_count,
            "validation_issue_count": airline_intelligence_data_pack_validation_issue_count,
            "import_run_count": airline_intelligence_data_pack_import_run_count,
            "review_note_count": airline_intelligence_data_pack_review_note_count,
            "coverage_snapshot_count": airline_intelligence_coverage_snapshot_count,
            "packs_needing_review_count": airline_data_packs_needing_review_count,
            "approved_pack_count": airline_data_pack_approved_count,
            "demo_pack_count": airline_data_pack_demo_count,
            "agency_display_safe_pack_count": airline_data_pack_agency_display_safe_count,
            "cms_display_safe_pack_count": airline_data_pack_cms_display_safe_count,
            "client_portal_safe_pack_count": airline_data_pack_client_portal_safe_count,
            "offer_builder_safe_pack_count": airline_data_pack_offer_builder_safe_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.0 creates metadata-only airline intelligence data pack staging, validation, review, and coverage records. It does not scrape, call external APIs, use external AI, auto-promote records into operational airline tables, publish CMS/client portal content, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, send messages, or execute providers.",
        },
        "airline_intelligence_data_pack_review_foundation": {
            "review_checklists_enabled": True,
            "field_mappings_enabled": True,
            "duplicate_conflict_detection_enabled": True,
            "promotion_readiness_metadata_enabled": True,
            "safe_consumption_flags_enabled": True,
            "agency_plain_language_coverage_enabled": True,
            "platform_review_ui_enabled": True,
            "agency_review_coverage_ui_enabled": True,
            "metadata_only_review_enabled": True,
            "automatic_promotion_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "review_count": airline_intelligence_data_pack_review_count,
            "review_checklist_item_count": airline_intelligence_data_pack_review_checklist_item_count,
            "field_mapping_count": airline_intelligence_data_pack_field_mapping_count,
            "conflict_count": airline_intelligence_data_pack_conflict_count,
            "open_conflict_count": airline_intelligence_data_pack_open_conflict_count,
            "promotion_readiness_count": airline_intelligence_data_pack_promotion_readiness_count,
            "promotion_ready_count": len(airline_intelligence_data_pack_promotion_ready_records),
            "review_snapshot_count": airline_intelligence_data_pack_review_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.1 records metadata-only review checklists, field mappings, duplicate/conflict metadata, promotion-readiness status, safe-consumption flags, and agency-readable coverage summaries. It does not promote staged data into operational airline tables, scrape, call external APIs or external AI, publish CMS/client portal content, recommend airlines, execute providers, book, mutate PNRs, ticket, issue EMDs, charge, invoice, or settle.",
        },
        "airline_intelligence_knowledge_versioning_foundation": {
            "metadata_only_versioning_enabled": True,
            "release_channel_metadata_enabled": True,
            "version_comparison_metadata_enabled": True,
            "rollback_plan_metadata_enabled": True,
            "immutable_version_snapshots_enabled": True,
            "platform_versioning_ui_enabled": True,
            "agency_version_visibility_ui_enabled": True,
            "operational_promotion_disabled": True,
            "automatic_promotion_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
            "external_api_calls_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "automatic_sending_disabled": True,
            "knowledge_version_count": airline_intelligence_knowledge_version_count,
            "version_item_count": airline_intelligence_knowledge_version_item_count,
            "release_channel_count": airline_intelligence_knowledge_release_channel_count,
            "release_assignment_count": airline_intelligence_knowledge_release_assignment_count,
            "comparison_count": airline_intelligence_knowledge_version_comparison_count,
            "rollback_plan_count": airline_intelligence_knowledge_rollback_plan_count,
            "snapshot_count": airline_intelligence_knowledge_version_snapshot_count,
            "frozen_version_count": airline_intelligence_knowledge_frozen_version_count,
            "approved_version_count": airline_intelligence_knowledge_approved_version_count,
            "published_metadata_version_count": airline_intelligence_knowledge_published_metadata_version_count,
            "agency_visible_version_count": airline_intelligence_knowledge_agency_visible_version_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.2 records governed airline intelligence knowledge versions, version items, release channels, release assignments, comparisons, rollback plans, and immutable snapshots as metadata only. It does not promote staged data into operational airline tables, scrape, call external APIs or external AI, publish CMS/client portal content, execute providers, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, or send automatically.",
        },
        "airline_intelligence_agency_consumption_bridge": {
            "consumption_profiles_enabled": True,
            "agency_assignment_visibility_enabled": True,
            "crm_readiness_metadata_enabled": True,
            "cms_readiness_metadata_enabled": True,
            "client_portal_readiness_metadata_enabled": True,
            "offer_builder_readiness_metadata_enabled": True,
            "agency_plain_language_ui_enabled": True,
            "platform_governance_ui_enabled": True,
            "metadata_only_consumption_enabled": True,
            "automatic_publishing_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendations_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "external_ai_disabled": True,
            "external_api_calls_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
            "profile_count": airline_intelligence_agency_consumption_profile_count,
            "assignment_view_count": airline_intelligence_agency_assignment_view_count,
            "usage_readiness_count": airline_intelligence_agency_usage_readiness_count,
            "note_count": airline_intelligence_agency_consumption_note_count,
            "snapshot_count": airline_intelligence_agency_consumption_snapshot_count,
            "agency_visible_profile_count": airline_intelligence_agency_visible_profile_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.3 exposes platform-governed airline intelligence knowledge versions to agencies through metadata-only consumption profiles, assignment views, usage readiness, notes, and snapshots. It does not publish CMS/client portal content, recommend airlines, execute providers, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external APIs, call external AI, or send automatically.",
        },
        "platform_agency_ux_consolidation": {
            "platform_console_labels_enabled": True,
            "agency_workspace_labels_enabled": True,
            "owner_agency_separation_enabled": True,
            "plain_language_navigation_enabled": True,
            "canonical_routes_preserved": True,
            "admin_agent_routes_rejected": True,
            "metadata_only_ui_enabled": True,
            "operational_execution_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendation_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "provider_execution_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "automatic_sending_disabled": True,
            "readiness_required": False,
            "diagnostic": "Phase 39.4 clarifies Platform Console and Agency Workspace navigation with plain-language metadata-only UI. It does not publish CMS or client portal content, recommend airlines, execute providers, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external APIs, call external AI, or send automatically.",
        },
        "saas_subscription_entitlement_foundation": {
            "plans_enabled": True,
            "plan_entitlements_enabled": True,
            "agency_subscription_assignments_enabled": True,
            "entitlement_readiness_enabled": True,
            "subscription_review_notes_enabled": True,
            "immutable_subscription_snapshots_enabled": True,
            "platform_subscription_ui_enabled": True,
            "agency_subscription_visibility_ui_enabled": True,
            "metadata_only_subscription_enabled": True,
            "billing_disabled": True,
            "payment_disabled": True,
            "invoice_disabled": True,
            "settlement_disabled": True,
            "automatic_access_enforcement_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "automatic_sending_disabled": True,
            "plan_count": saas_subscription_plan_count,
            "entitlement_count": saas_plan_entitlement_count,
            "assignment_count": agency_subscription_assignment_count,
            "readiness_count": agency_entitlement_readiness_count,
            "note_count": agency_subscription_review_note_count,
            "snapshot_count": agency_subscription_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.5 records SaaS subscription plans, entitlements, agency assignments, entitlement readiness, review notes, and immutable snapshots as metadata only. It does not bill, charge, invoice, settle, enforce access automatically, publish CMS/client portal content, recommend airlines, execute providers, book, mutate PNRs, ticket, issue EMDs, scrape, call external APIs, call external AI, or send automatically.",
        },
        "subscription_entitlement_ui_guardrails": {
            "entitlement_visibility_enabled": True,
            "agency_navigation_badges_enabled": True,
            "platform_entitlement_review_enabled": True,
            "read_only_guardrail_ui_enabled": True,
            "automatic_enforcement_disabled": True,
            "billing_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
            "visibility_statuses": ["included", "limited", "not_included", "review_required", "unknown"],
            "agency_module_visibility_catalog_count": len(AGENCY_MODULE_VISIBILITY_CATALOG),
            "plan_count": saas_subscription_plan_count,
            "entitlement_count": saas_plan_entitlement_count,
            "assignment_count": agency_subscription_assignment_count,
            "readiness_count": agency_entitlement_readiness_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.6 adds read-only subscription entitlement visibility metadata for Platform Console review and Agency Workspace navigation badges. It remains informational only and does not bill, charge, invoice, settle, enforce access automatically, execute providers, book, mutate PNRs, ticket, issue EMDs, scrape, call external APIs, call external AI, or send automatically.",
        },
        "agency_feature_flags_foundation": {
            "feature_flags_enabled": True,
            "review_notes_enabled": True,
            "snapshots_enabled": True,
            "platform_review_enabled": True,
            "agency_read_only_visibility_enabled": True,
            "automatic_enforcement_disabled": True,
            "automatic_enforcement_enabled": False,
            "billing_disabled": True,
            "billing_enabled": False,
            "payments_disabled": True,
            "payments_enabled": False,
            "provider_execution_disabled": True,
            "provider_execution_enabled": False,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
            "feature_blocking_disabled": True,
            "flag_count": agency_feature_flag_count,
            "review_count": agency_feature_flag_review_count,
            "snapshot_count": agency_feature_flag_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.7 records agency-specific feature flag visibility metadata for Platform Console review and Agency Workspace read-only visibility. It does not enforce permissions, block features, bill, charge, execute providers, book, mutate PNRs, ticket, issue EMDs, publish CMS/client portal content, scrape, call external APIs, call external AI, or send automatically.",
        },
        "feature_flag_audit_foundation": {
            "feature_flag_audits_enabled": True,
            "feature_flag_readiness_enabled": True,
            "audit_history_enabled": True,
            "readiness_checklist_enabled": True,
            "platform_read_only_audit_enabled": True,
            "agency_read_only_readiness_enabled": True,
            "metadata_only": True,
            "automatic_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "permission_changes_disabled": True,
            "subscription_changes_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
            "feature_blocking_disabled": True,
            "operational_enforcement_enabled": False,
            "audit_count": agency_feature_flag_audit_count,
            "readiness_count": agency_feature_flag_readiness_count,
            "readiness_required": False,
            "diagnostic": "Phase 39.8 records feature flag audit history and readiness checklist metadata. It does not enforce features, block routes, change permissions, affect subscriptions, bill, execute providers, book, mutate PNRs, ticket, issue EMDs, publish CMS/client portal content, call external APIs, call external AI, scrape, or send automatically.",
        },
        "feature_flag_bundle_foundation": {
            "feature_flag_bundles_enabled": True,
            "feature_flag_bundle_reviews_enabled": True,
            "feature_flag_bundle_members_enabled": True,
            "bundle_readiness_enabled": True,
            "platform_bundle_read_only_enabled": True,
            "agency_bundle_read_only_enabled": True,
            "metadata_only": True,
            "runtime_feature_enforcement_disabled": True,
            "entitlement_checks_disabled": True,
            "billing_disabled": True,
            "execution_logic_disabled": True,
            "module_hiding_disabled": True,
            "permission_decisions_disabled": True,
            "publishing_disabled": True,
            "rollout_disabled": True,
            "percentage_deployments_disabled": True,
            "provider_integrations_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "background_workers_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "api_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "bundle_count": agency_feature_flag_bundle_count,
            "bundle_review_count": agency_feature_flag_bundle_review_count,
            "default_bundle_count": len(DEFAULT_FEATURE_FLAG_BUNDLES),
            "readiness_required": False,
            "diagnostic": "Phase 39.9 defines reusable feature flag bundle metadata for platform review and agency read-only visibility. Bundles do not enable features, enforce access, hide modules, decide permissions, bill, execute providers, publish, roll out changes, call external APIs, call external AI, scrape, send notifications, or start background workers.",
        },
        "feature_bundle_assignment_foundation": {
            "feature_bundle_assignments_enabled": True,
            "feature_bundle_assignment_history_enabled": True,
            "platform_assignment_metadata_crud_enabled": True,
            "agency_read_only_assignment_visibility_enabled": True,
            "delete_marks_inactive_enabled": True,
            "history_preserved_enabled": True,
            "metadata_only": True,
            "no_activation_logic_enabled": True,
            "feature_activation_disabled": True,
            "runtime_execution_disabled": True,
            "feature_flag_execution_disabled": True,
            "entitlement_enforcement_disabled": True,
            "entitlement_evaluation_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "stripe_disabled": True,
            "licensing_disabled": True,
            "permission_changes_disabled": True,
            "provider_calls_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
            "assignment_count": agency_feature_bundle_assignment_count,
            "assignment_history_count": agency_feature_bundle_assignment_history_count,
            "readiness_required": False,
            "diagnostic": "Phase 40.0 records agency feature bundle assignment metadata for platform review and agency read-only visibility. Assignments do not activate features, enforce entitlements, change permissions, bill, license, execute feature flags, call providers, call external AI, start background workers, run cron jobs, or deploy anything.",
        },
        "feature_bundle_rollout_readiness_foundation": {
            "feature_bundle_rollout_readiness_enabled": True,
            "feature_bundle_rollout_checklist_enabled": True,
            "default_readiness_views_enabled": True,
            "platform_rollout_readiness_review_enabled": True,
            "agency_rollout_readiness_read_only_enabled": True,
            "readiness_status_summary_enabled": True,
            "metadata_only": True,
            "activation_logic_disabled": True,
            "feature_activation_disabled": True,
            "feature_deactivation_disabled": True,
            "feature_access_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "permission_changes_disabled": True,
            "entitlement_enforcement_disabled": True,
            "entitlement_evaluation_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "notifications_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "scraping_disabled": True,
            "publishing_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
            "rollout_readiness_count": agency_feature_bundle_rollout_readiness_count,
            "readiness_status_counts": agency_feature_bundle_rollout_readiness_status_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.1 records metadata-only feature bundle rollout readiness and checklist views for assigned bundles. It does not activate or deactivate features, enforce access, block routes, change permissions, bill, send email or SMS, call providers, call external APIs, scrape, publish, or run background logic.",
        },
        "feature_bundle_rollout_plan_foundation": {
            "feature_bundle_rollout_plans_enabled": True,
            "platform_rollout_plan_metadata_crud_enabled": True,
            "agency_rollout_plan_read_only_enabled": True,
            "rollout_stage_metadata_enabled": True,
            "target_window_metadata_enabled": True,
            "readiness_snapshot_reference_enabled": True,
            "assigned_bundle_reference_enabled": True,
            "checklist_summary_metadata_enabled": True,
            "metadata_only": True,
            "rollout_execution_disabled": True,
            "feature_activation_disabled": True,
            "feature_deactivation_disabled": True,
            "feature_access_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "permission_changes_disabled": True,
            "entitlement_enforcement_disabled": True,
            "entitlement_evaluation_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "notifications_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "external_services_disabled": True,
            "ai_execution_disabled": True,
            "scraping_disabled": True,
            "publishing_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
            "rollout_plan_count": agency_feature_bundle_rollout_plan_count,
            "rollout_stage_counts": agency_feature_bundle_rollout_plan_stage_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.2 records metadata-only feature bundle rollout plan records after readiness review. It does not activate features, enforce access, block routes, publish, send email or SMS, bill, call providers, call external APIs, use AI, scrape, or execute rollout logic.",
        },
        "rollout_dashboard_foundation": {
            "rollout_dashboard_enabled": True,
            "platform_rollout_dashboard_enabled": True,
            "agency_rollout_dashboard_enabled": True,
            "rollout_dashboard_summary_enabled": True,
            "rollout_dashboard_filters_enabled": True,
            "rollout_dashboard_snapshots_read_only_enabled": True,
            "capability_catalog_section_enabled": True,
            "feature_flags_section_enabled": True,
            "feature_bundles_section_enabled": True,
            "assigned_bundles_section_enabled": True,
            "rollout_readiness_section_enabled": True,
            "rollout_plans_section_enabled": True,
            "metadata_only": True,
            "read_only": True,
            "automation_disabled": True,
            "rollout_automation_disabled": True,
            "rollout_execution_disabled": True,
            "execution_engines_disabled": True,
            "feature_activation_disabled": True,
            "permission_enforcement_disabled": True,
            "feature_access_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "scraping_disabled": True,
            "publishing_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "cron_disabled": True,
            "webhook_execution_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "dashboard_section_count": len(DASHBOARD_SECTIONS),
            "rollout_dashboard_view_count": rollout_dashboard_view_count,
            "rollout_dashboard_snapshot_count": rollout_dashboard_snapshot_count,
            "readiness_required": False,
            "diagnostic": "Phase 40.3 exposes a read-only rollout dashboard that aggregates existing capability, feature flag, bundle, assignment, readiness, and rollout plan metadata. It does not enforce entitlements, bill, execute providers, use AI, publish, automate rollouts, schedule jobs, send messages, activate features, block routes, call external APIs, run webhooks, or scrape.",
        },
        "capability_catalog_foundation": {
            "capability_catalog_enabled": True,
            "platform_capability_catalog_enabled": True,
            "agency_capability_visibility_enabled": True,
            "category_listing_enabled": True,
            "module_listing_enabled": True,
            "search_filter_metadata_enabled": True,
            "flag_references_enabled": True,
            "bundle_references_enabled": True,
            "dependency_view_enabled": True,
            "documentation_links_enabled": True,
            "availability_informational_only": True,
            "metadata_only": True,
            "read_only": True,
            "no_execution_logic": True,
            "runtime_feature_enforcement_disabled": True,
            "entitlement_checks_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "subscription_charging_disabled": True,
            "route_blocking_disabled": True,
            "permission_changes_disabled": True,
            "provider_execution_disabled": True,
            "publishing_disabled": True,
            "external_services_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
            "capability_count": capability_catalog_count,
            "default_capability_count": len(DEFAULT_CAPABILITY_CATALOG),
            "readiness_required": False,
            "diagnostic": "Phase 40.1 creates a metadata-only Capability Catalog that relates subscriptions, bundles, feature flags, and capabilities for read-only visibility. It does not enforce features, evaluate entitlements, block routes, change permissions, bill, execute providers, publish, call external services, call external APIs, call external AI, start background workers, or run cron jobs.",
        },
        "blueprint_sync": {
            "supplementary_blueprint_adoption_map_enabled": True,
            "canonical_route_policy_enabled": True,
            "ai_trace_foundation_enabled": True,
            "adm_risk_event_foundation_enabled": True,
            "gds_parse_sample_foundation_enabled": True,
            "airline_brand_asset_foundation_enabled": True,
            "special_services_unified_facade_enabled": True,
            "platform_blueprint_ui_enabled": True,
            "supplementary_agent_admin_routes_rejected": True,
            "tickets_emd_phase_36_4_recognized": True,
            "booking_workspace_creation_entrypoint_recognized": True,
            "standalone_booking_ticket_emd_workflow_recognized": True,
            "gds_confirmation_import_foundation_enabled": True,
            "existing_trip_change_exchange_workflow_recognized": True,
            "phase_36_5_documents_ready": True,
            "phase_36_6_gds_parser_ready": True,
            "ai_trace_event_count": ai_trace_event_count,
            "adm_risk_event_count": adm_risk_event_count,
            "gds_parse_sample_count": gds_parse_sample_count,
            "airline_brand_asset_count": airline_brand_asset_count,
            "blueprint_adoption_item_count": len(blueprint_adoption.get("items") or []),
            "blueprint_gap_count": blueprint_gaps.get("gap_count", 0),
            "blueprint_rejected_route_count": len(blueprint_route_policy.get("rejected_routes") or []),
            "readiness_required": False,
            "diagnostic": "Supplementary blueprint sync is documented and mapped to existing AgencyOS foundations through Phase 40.1; /platform and /agency remain canonical.",
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


@app.get("/api/system/readiness")
async def system_readiness() -> dict:
    return await readiness()


@app.get("/api/audit-events")
async def audit_events() -> dict:
    return {"items": await database.collection("audit_events").find_many()}


app.include_router(auth.router)
app.include_router(platform.router)
app.include_router(platform_blueprint.router)
app.include_router(platform_airline_intelligence.router)
app.include_router(platform_rules_services.router)
app.include_router(platform_ancillary_pricing.router)
app.include_router(platform_policy_comparison.router)
app.include_router(platform_offer_policy_advisor.router)
app.include_router(platform_offer_decision_packs.router)
app.include_router(platform_offer_decision_explanations.router)
app.include_router(platform_offer_decision_exports.router)
app.include_router(platform_offer_decision_export_previews.router)
app.include_router(platform_offer_decision_export_releases.router)
app.include_router(platform_offer_decision_export_deliveries.router)
app.include_router(platform_offer_decision_export_delivery_outcomes.router)
app.include_router(platform_offer_decision_export_audit_reviews.router)
app.include_router(platform_offer_decision_export_governance.router)
app.include_router(platform_offer_decision_export_compliance.router)
app.include_router(platform_airline_intelligence_data_packs.router)
app.include_router(platform_airline_intelligence_data_pack_reviews.router)
app.include_router(platform_airline_intelligence_knowledge_versions.router)
app.include_router(platform_airline_intelligence_agency_consumption.router)
app.include_router(platform_saas_subscriptions.router)
app.include_router(platform_feature_flags.router)
app.include_router(platform_feature_flag_audits.router)
app.include_router(platform_feature_flag_bundles.router)
app.include_router(platform_feature_bundle_assignments.router)
app.include_router(platform_feature_bundle_rollout_readiness.router)
app.include_router(platform_feature_bundle_rollout_plans.router)
app.include_router(platform_rollout_dashboard.router)
app.include_router(platform_capabilities.router)
app.include_router(platform_service_catalogue.router)
app.include_router(platform_service_taxonomy.router)
app.include_router(platform_service_mechanics.router)
app.include_router(platform_documents.router)
app.include_router(platform_gds_parser.router)
app.include_router(platform_airline_policy_ingestion.router)
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
app.include_router(agency_booking_imports.router)
app.include_router(agency_gds_parser.router)
app.include_router(agency_airline_policy_library.router)
app.include_router(agency_ancillary_pricing.router)
app.include_router(agency_policy_comparison.router)
app.include_router(agency_offer_policy_advisor.router)
app.include_router(agency_offer_decision_packs.router)
app.include_router(agency_offer_decision_explanations.router)
app.include_router(agency_offer_decision_exports.router)
app.include_router(agency_offer_decision_export_previews.router)
app.include_router(agency_offer_decision_export_releases.router)
app.include_router(agency_offer_decision_export_deliveries.router)
app.include_router(agency_offer_decision_export_delivery_outcomes.router)
app.include_router(agency_offer_decision_export_audit_reviews.router)
app.include_router(agency_offer_decision_export_governance.router)
app.include_router(agency_offer_decision_export_compliance.router)
app.include_router(agency_airline_intelligence_data_packs.router)
app.include_router(agency_airline_intelligence_data_pack_reviews.router)
app.include_router(agency_airline_intelligence_knowledge_versions.router)
app.include_router(agency_airline_intelligence_agency_consumption.router)
app.include_router(agency_saas_subscriptions.router)
app.include_router(agency_feature_flags.router)
app.include_router(agency_feature_flag_readiness.router)
app.include_router(agency_feature_flag_bundles.router)
app.include_router(agency_feature_bundle_assignments.router)
app.include_router(agency_feature_bundle_rollout_readiness.router)
app.include_router(agency_feature_bundle_rollout_plans.router)
app.include_router(agency_rollout_dashboard.router)
app.include_router(agency_capabilities.router)
app.include_router(agency_service_taxonomy.router)
app.include_router(agency_service_mechanics.router)
app.include_router(agency_ticket_emd.router)
app.include_router(agency_trip_changes.router)
app.include_router(agency_documents.router)
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
