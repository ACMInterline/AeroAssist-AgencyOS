from fastapi import APIRouter, Depends

from auth import get_current_user, require_platform_role
from config import get_settings
from database import Database, get_database

router = APIRouter(prefix="/api/platform", tags=["platform"])


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "service": "AeroAssist AgencyOS API",
        "app_env": settings.app_env,
        "phase": "phase_36_9_service_mechanics_mapping_foundation",
    }


@router.get("/summary")
async def summary(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin", "platform_support"])),
    db: Database = Depends(get_database),
) -> dict:
    platform_owner_count = await db.collection("platform_users").count({"global_role": "platform_owner", "status": "active"})
    agency_count = await db.collection("agencies").count()
    workspace_count = await db.collection("agency_workspaces").count()
    staff_membership_count = await db.collection("agency_staff_memberships").count()
    staff_invitation_count = await db.collection("invitations").count({"invitation_type": "agency_staff"})
    branding_settings = await db.collection("agency_branding_settings").find_many()
    website_settings = await db.collection("agency_website_settings").find_many()
    request_intakes = await db.collection("request_intakes").find_many()
    open_operational_requests = [
        item
        for item in await db.collection("travel_requests").find_many()
        if item.get("status") not in {"closed", "cancelled", "archived"}
    ]
    return {
        "current_user": user,
        "counts": {
            "agencies": agency_count,
            "workspaces": workspace_count,
            "staff_memberships": staff_membership_count,
            "agency_branding_settings": len(branding_settings),
            "agency_branding_logos": len([item for item in branding_settings if item.get("logo_storage_record_id")]),
            "agency_branding_logo_assets": await db.collection("agency_branding_assets").count(),
            "agency_website_settings": len(website_settings),
            "active_agency_websites": len([item for item in website_settings if item.get("status") == "active"]),
            "agency_website_pages": await db.collection("agency_website_pages").count(),
            "agency_website_media_assets": await db.collection("agency_website_media_assets").count(),
            "public_agency_website_media_assets": await db.collection("agency_website_media_assets").count({"status": "active", "public_usage_allowed": True, "is_public_safe": True}),
            "trip_dossiers": await db.collection("trip_dossiers").count(),
            "request_case_flags": await db.collection("request_case_flags").count(),
            "website_origin_intakes": await db.collection("request_intakes").count({"source": "agency_website"}),
            "clients": await db.collection("client_profiles").count(),
            "passengers": await db.collection("passenger_profiles").count(),
            "relationships": await db.collection("client_passenger_relationships").count(),
            "request_intakes": len(request_intakes),
            "new_request_intakes": len([item for item in request_intakes if item.get("status") == "new"]),
            "converted_request_intakes": len([item for item in request_intakes if item.get("status") == "converted"]),
            "requests": await db.collection("travel_requests").count(),
            "open_operational_requests": len(open_operational_requests),
            "request_tasks": await db.collection("request_tasks").count(),
            "offers": await db.collection("offers").count(),
            "offer_routes": await db.collection("offer_route_alternatives").count(),
            "offer_fare_options": await db.collection("offer_fare_options").count(),
            "offer_workspaces": await db.collection("offer_workspaces").count(),
            "offer_options": await db.collection("offer_options").count(),
            "offer_builder_segments": await db.collection("offer_builder_segments").count(),
            "offer_fare_bundles": await db.collection("offer_fare_bundles").count(),
            "offer_pricing_lines": await db.collection("offer_pricing_lines").count(),
            "offer_comparison_snapshots": await db.collection("offer_comparison_snapshots").count(),
            "offer_acceptances": await db.collection("offer_acceptances").count(),
            "trip_accepted_offer_snapshots": await db.collection("trip_accepted_offer_snapshots").count(),
            "booking_readiness_packages": await db.collection("booking_readiness_packages").count(),
            "booking_workspaces": await db.collection("booking_workspaces").count(),
            "booking_records": await db.collection("booking_records").count(),
            "booking_import_drafts": await db.collection("booking_import_drafts").count(),
            "trip_change_operations": await db.collection("trip_change_operations").count(),
            "bookings": await db.collection("bookings").count(),
            "tickets": await db.collection("ticket_records").count(),
            "ticket_coupons": await db.collection("ticket_coupons").count(),
            "emds": await db.collection("emd_records").count(),
            "emd_coupons": await db.collection("emd_coupons").count(),
            "ticket_exchange_operations": await db.collection("ticket_exchange_operations").count(),
            "emd_exchange_operations": await db.collection("emd_exchange_operations").count(),
            "ticket_emd_timeline_events": await db.collection("ticket_emd_timeline_events").count(),
            "ai_trace_events": await db.collection("ai_trace_events").count(),
            "adm_risk_events": await db.collection("adm_risk_events").count(),
            "gds_parse_samples": await db.collection("gds_parse_samples").count(),
            "gds_parser_profiles": await db.collection("gds_parser_profiles").count(),
            "gds_parser_versions": await db.collection("gds_parser_versions").count(),
            "gds_parser_runs": await db.collection("gds_parser_runs").count(),
            "gds_parsed_entities": await db.collection("gds_parsed_entities").count(),
            "gds_parse_corrections": await db.collection("gds_parse_corrections").count(),
            "gds_parse_training_samples": await db.collection("gds_parse_training_samples").count(),
            "gds_parser_evaluation_runs": await db.collection("gds_parser_evaluation_runs").count(),
            "airline_brand_assets": await db.collection("airline_brand_assets").count(),
            "invoices": await db.collection("invoices").count(),
            "payments": await db.collection("payment_records").count(),
            "portal_mappings": await db.collection("portal_access_mappings").count(),
            "airlines": await db.collection("airline_profiles").count(),
            "airline_knowledge": await db.collection("airline_knowledge_items").count(),
            "airline_procedures": await db.collection("airline_procedures").count(),
            "airline_emd_notes": await db.collection("airline_emd_rule_notes").count(),
            "airline_overrides": await db.collection("agency_airline_overrides").count(),
            "airline_rules_core": await db.collection("airline_rules_core").count(),
            "unified_exception_rules": await db.collection("unified_exception_rules").count(),
            "passenger_service_requests": await db.collection("passenger_service_requests").count(),
            "document_templates": await db.collection("document_templates").count(),
            "document_render_jobs": await db.collection("document_render_jobs").count(),
            "document_packages": await db.collection("document_packages").count(),
            "document_share_records": await db.collection("document_share_records").count(),
            "rendered_documents": await db.collection("rendered_documents").count(),
            "document_exports": await db.collection("document_exports").count(),
            "document_deliveries": await db.collection("document_deliveries").count(),
            "document_delivery_attempts": await db.collection("document_delivery_attempts").count(),
            "reference_records": await db.collection("global_reference_records").count(),
            "country_reference_records": await db.collection("global_reference_records").count({"domain": "countries"}),
            "airport_reference_records": await db.collection("global_reference_records").count({"domain": "airports"}),
            "airline_reference_records": await db.collection("global_reference_records").count({"domain": "airlines"}),
            "currency_reference_records": await db.collection("global_reference_records").count({"domain": "currencies"}),
            "language_reference_records": await db.collection("global_reference_records").count({"domain": "languages"}),
            "reference_domain_metadata": await db.collection("reference_domain_metadata").count(),
            "reference_suggestions": await db.collection("reference_data_suggestions").count(),
            "pending_reference_suggestions": await db.collection("reference_data_suggestions").count({"status": "pending_review"}),
            "reference_import_batches": await db.collection("reference_import_batches").count(),
            "service_catalogue_records": await db.collection("service_catalogue").count(),
            "global_field_definitions": await db.collection("global_field_definitions").count(),
            "agency_form_profiles": await db.collection("agency_form_profiles").count(),
            "agency_form_field_settings": await db.collection("agency_form_field_settings").count(),
            "request_passenger_segment_services": await db.collection("request_passenger_segment_services").count(),
            "request_pets": await db.collection("request_pets").count(),
            "request_pet_segment_transport": await db.collection("request_pet_segment_transport").count(),
            "request_special_items": await db.collection("request_special_items").count(),
            "request_special_item_segments": await db.collection("request_special_item_segments").count(),
            "canonical_service_domains": await db.collection("canonical_service_domains").count(),
            "canonical_service_families": await db.collection("canonical_service_families").count(),
            "canonical_service_variants": await db.collection("canonical_service_variants").count(),
            "airline_service_aliases": await db.collection("airline_service_aliases").count(),
            "service_taxonomy_mapping_rules": await db.collection("service_taxonomy_mapping_rules").count(),
            "policy_candidate_taxonomy_links": await db.collection("policy_candidate_taxonomy_links").count(),
            "airline_service_communication_rules": await db.collection("airline_service_communication_rules").count(),
            "ssr_osi_templates": await db.collection("ssr_osi_templates").count(),
            "ssr_osi_requirements": await db.collection("ssr_osi_requirements").count(),
            "ssr_status_recognition_rules": await db.collection("ssr_status_recognition_rules").count(),
            "airline_rejection_patterns": await db.collection("airline_rejection_patterns").count(),
            "airline_service_payment_rules": await db.collection("airline_service_payment_rules").count(),
            "airline_emd_issuance_rules": await db.collection("airline_emd_issuance_rules").count(),
            "airline_rfic_rfisc_mappings": await db.collection("airline_rfic_rfisc_mappings").count(),
            "airline_emd_interline_rules": await db.collection("airline_emd_interline_rules").count(),
            "airline_emd_lifecycle_rules": await db.collection("airline_emd_lifecycle_rules").count(),
            "policy_candidate_mechanics_links": await db.collection("policy_candidate_mechanics_links").count(),
            "audit_events": await db.collection("audit_events").count(),
        },
        "production_onboarding": {
            "platform_owner_exists": platform_owner_count > 0,
            "agency_exists": agency_count > 0,
            "workspace_exists": workspace_count > 0,
            "staff_membership_or_invitation_exists": staff_membership_count > 0 or staff_invitation_count > 0,
            "staff_invitations": staff_invitation_count,
        },
        "implemented_layers": [
            "AeroAssist Global / Platform Owner",
            "Agency Workspace foundation",
            "CRM client/passenger relationship foundation",
            "Request intake, messages, tasks, and timeline foundation",
            "Manual offer builder foundation",
            "Booking, ticket, EMD, invoice, and payment tracking foundation",
            "Airline Intelligence foundation",
            "Branded HTML document output foundation",
            "Read-only client portal visibility foundation",
            "Persistence and tenant hardening foundation",
            "Authentication and invitation foundation",
            "Controlled client portal actions foundation",
            "Refund and exchange tracking foundation",
            "Printable document export and manual delivery foundation",
            "Document delivery hardening foundation",
            "Production PDF rendering and delivery infrastructure foundation",
            "Production delivery operations and secret resolution foundation",
            "Production configuration hardening foundation",
            "Docker and Hostinger VPS packaging foundation",
            "VPS reverse proxy, TLS, backup, and operations runbook foundation",
            "Hostinger VPS first deployment preparation foundation",
            "Production bootstrap and go-live hardening foundation",
            "Production onboarding and agency setup foundation",
            "Backup automation and lightweight monitoring readiness foundation",
            "Staff invitation acceptance and team access hardening foundation",
            "Document storage lifecycle and delivery provider readiness foundation",
            "Request intake triage and operational request conversion foundation",
            "Operational request builder V1 foundation",
            "Mobility assistance logic and request builder UX correction",
            "Assistance assessment driven SSR recommendation",
            "Agency branding, theme, and UI personalization foundation",
            "AgencyOS app shell, sidebar navigation, and visual polish stabilization",
            "Agency website builder and CMS foundation",
            "Public website publishing, intake forms, and CMS content blocks",
            "Branding, logo asset management, and agency settings stabilization",
            "CMS media library, website image assets, and public website visual polish",
            "Blueprint alignment and canonical operations model foundation",
            "Reference data core and service catalogue foundation",
            "Global reference governance, suggestion queue, and bulk import foundation",
            "Segment-scoped request services, pets, and special items foundation",
            "Global field library and agency form profile foundation",
            "Platform reference data console and enriched country metadata foundation",
            "Reference enrichment import packs and aviation normalization foundation",
            "Offer acceptance, trip accepted-offer snapshots, and booking readiness foundation",
            "Booking workspace and manual PNR mirror foundation",
            "Ticket and EMD mirror foundation",
            "Supplementary blueprint adoption and canonical route sync foundation",
            "Standalone booking, import draft, and existing-trip change/exchange mirror foundation",
            "Document foundation for templates, render jobs, packages, and internal share records",
            "GDS parser profiles, versions, runs, entities, corrections, training samples, and evaluations foundation",
            "Airline policy ingestion source, extraction, review, and approved knowledge foundation",
            "Canonical service taxonomy foundation",
            "SSR/OSI and EMD/RFIC/RFISC service mechanics mapping foundation",
        ],
        "not_yet_implemented": [
            "Document upload workflows",
            "Payment gateway integration",
            "Public document links",
            "Automatic document sending or provider webhooks",
            "Automatic booking, ticketing, or airline execution from portal actions",
            "Live SSR/OSI/GDS/NDC/provider exchange, refund, void, or reissue execution",
            "External AI parser execution",
            "Full GDS host grammar coverage and provider reconciliation",
        ],
    }


@router.get("/audit-events")
async def audit_events(
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin", "platform_support"])),
    db: Database = Depends(get_database),
) -> dict:
    return {"items": await db.collection("audit_events").find_many()}


@router.get("/whoami")
async def whoami(user: dict = Depends(get_current_user)) -> dict:
    return {"user": user}
