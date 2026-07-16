from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from build_phase import CURRENT_BUILD_PHASE
from config import assert_startup_safe, configure_logging, get_settings, validate_config
from database import database
from http_security import (
    SecurityHttpMiddleware,
    http_exception_handler,
    internal_readiness_authorized,
    security_readiness_metadata,
    unexpected_exception_handler,
    validation_exception_handler,
)
from smoke_inventory import SMOKE_INVENTORY_SUMMARY
from routers import platform
from routers import agency_airline_capability_matrix, agency_airline_knowledge_acquisition, agency_airline_knowledge_governance, agency_airline_knowledge_normalisation, agency_airline_operational_intelligence, agency_airline_recommendations, agency_operational_constraints, agency_operational_evaluations, agency_passenger_service_feasibility, platform_airline_capability_matrix, platform_airline_knowledge_acquisition, platform_airline_knowledge_governance, platform_airline_knowledge_normalisation, platform_airline_operational_intelligence, platform_airline_recommendations, platform_operational_constraints, platform_operational_evaluations, platform_passenger_service_feasibility
from routers import agency_airline_intelligence_agency_consumption, agency_airline_intelligence_data_pack_reviews, agency_airline_intelligence_data_packs, agency_airline_intelligence_knowledge_versions, agency_ancillary_pricing, agency_capabilities, agency_feature_bundle_assignments, agency_feature_flag_bundles, agency_feature_flag_readiness, agency_feature_flags, agency_offer_decision_export_audit_reviews, agency_offer_decision_export_compliance, agency_offer_decision_export_deliveries, agency_offer_decision_export_delivery_outcomes, agency_offer_decision_export_governance, agency_offer_decision_export_previews, agency_offer_decision_export_releases, agency_offer_decision_exports, agency_offer_decision_explanations, agency_offer_decision_packs, agency_offer_policy_advisor, agency_policy_comparison, agency_saas_subscriptions, platform_airline_intelligence_agency_consumption, platform_airline_intelligence_data_pack_reviews, platform_airline_intelligence_data_packs, platform_airline_intelligence_knowledge_versions, platform_ancillary_pricing, platform_capabilities, platform_feature_bundle_assignments, platform_feature_flag_audits, platform_feature_flag_bundles, platform_feature_flags, platform_offer_decision_export_audit_reviews, platform_offer_decision_export_compliance, platform_offer_decision_export_deliveries, platform_offer_decision_export_delivery_outcomes, platform_offer_decision_export_governance, platform_offer_decision_export_previews, platform_offer_decision_export_releases, platform_offer_decision_exports, platform_offer_decision_explanations, platform_offer_decision_packs, platform_offer_policy_advisor, platform_policy_comparison, platform_saas_subscriptions
from routers import agency_feature_bundle_dependencies, agency_feature_bundle_rollout_approvals, agency_feature_bundle_rollout_change_requests, agency_feature_bundle_rollout_decisions, agency_feature_bundle_rollout_issues, agency_feature_bundle_rollout_plans, agency_feature_bundle_rollout_readiness, agency_feature_bundle_rollout_risks, agency_feature_bundle_rollout_rollback_plans, agency_feature_bundle_rollout_schedule, agency_feature_bundle_rollout_summary_packs, agency_feature_bundle_rollout_timeline, agency_rollout_dashboard, platform_feature_bundle_dependencies, platform_feature_bundle_rollout_approvals, platform_feature_bundle_rollout_change_requests, platform_feature_bundle_rollout_decisions, platform_feature_bundle_rollout_issues, platform_feature_bundle_rollout_plans, platform_feature_bundle_rollout_readiness, platform_feature_bundle_rollout_risks, platform_feature_bundle_rollout_rollback_plans, platform_feature_bundle_rollout_schedule, platform_feature_bundle_rollout_summary_packs, platform_feature_bundle_rollout_timeline, platform_rollout_dashboard
from routers import agency_agent_work_queues, agency_document_workspaces, agency_emd_workspaces, agency_flight_workspaces, agency_journey_authoring, agency_journey_comparison_presentations, agency_offer_deliveries, agency_journey_option_composition, agency_journeys, agency_offer_booking_handoffs, agency_offer_workspaces, agency_operational_sla_deadlines, agency_operational_timelines, agency_operational_travel_workspaces, agency_operational_workflows, agency_passenger_service_workflows, agency_passenger_workspaces, agency_request_trip_conversion, agency_ssr_osi_workspaces, agency_task_automation, agency_ticket_workspaces, agency_travel_request_workspaces, agency_trip_workspaces, platform_agent_work_queues, platform_booking_workspaces, platform_document_workspaces, platform_emd_workspaces, platform_flight_workspaces, platform_journey_authoring, platform_journey_comparison_presentations, platform_journey_engine, platform_offer_delivery_diagnostics, platform_journey_option_composition, platform_offer_booking_handoffs, platform_offer_workspaces, platform_operational_sla_deadlines, platform_operational_timelines, platform_operational_travel_workspaces, platform_operational_workflows, platform_passenger_service_workflows, platform_passenger_workspaces, platform_request_trip_conversion, platform_ssr_osi_workspaces, platform_task_automation, platform_ticket_workspaces, platform_travel_request_workspaces, platform_trip_workspaces, portal_offer_deliveries
from routers import agency_after_sales_workflows, platform_after_sales_workflows
from routers import agency_operational_workflow_maturity, agency_operations_command_center, platform_operational_workflow_maturity, platform_operations_governance
from routers import agency_airline_master_profiles, platform_airline_master_profiles
from routers import agency_airline_contact_directory, agency_airline_distribution_capabilities, agency_airline_fare_brand_intelligence, agency_airline_intelligence_readiness, agency_airline_knowledge_versioning, agency_airline_policy_evidence_governance, agency_airline_service_coverage, agency_interline_codeshare_intelligence, platform_airline_contact_intelligence, platform_airline_distribution_capabilities, platform_airline_fare_brand_intelligence, platform_airline_intelligence_readiness, platform_airline_knowledge_versioning, platform_airline_policy_evidence_governance, platform_airline_service_coverage, platform_interline_codeshare_intelligence
from routers import agency_service_mechanics, platform_service_mechanics
from routers import agency_airline_knowledge_publishing, agency_client_passenger_master, agency_intelligent_offer_builder, agency_knowledge_import_templates, agency_knowledge_population_toolkit, agency_knowledge_quality_assurance, agency_operational_intelligence_cases, agency_operational_rule_composer, agency_operational_scenario_testing, agency_pilot_readiness, agency_pricing_formula_builder, agency_reference_data_engine, agency_request_segment_services, agency_service_parameter_taxonomies, agency_visual_policy_editor, platform_airline_knowledge_publishing, platform_client_passenger_master, platform_intelligent_offer_builder, platform_knowledge_import_templates, platform_knowledge_population_toolkit, platform_knowledge_quality_assurance, platform_operational_intelligence_cases, platform_operational_rule_composer, platform_operational_scenario_testing, platform_pilot_readiness, platform_pricing_formula_builder, platform_reference_data_engine, platform_request_segment_services, platform_service_parameter_taxonomies, platform_visual_policy_editor
from routers import agencies, agency_airline_policy_library, agency_booking_imports, agency_booking_workspaces, agency_documents, agency_gds_parser, agency_offer_acceptance, agency_offer_builder, agency_service_taxonomy, agency_special_services, agency_ticket_emd, agency_trip_changes, airline_intelligence, auth, bookings, clients, documents, finance, form_profiles, offers, passengers, platform_airline_intelligence, platform_airline_policy_ingestion, platform_blueprint, platform_documents, platform_gds_parser, platform_reference, platform_rules_services, platform_service_catalogue, platform_service_taxonomy, portal, refunds_exchanges, reference, request_intakes, requests, trips, websites
from services.blueprint_adoption_service import get_blueprint_adoption_map, get_blueprint_gap_summary, get_blueprint_route_policy
from services.pdf_rendering_service import pdf_capabilities
from services.reference_data_service import REFERENCE_DOMAINS, country_enrichment_complete
from services.reference_domain_usage_service import list_domain_usage, reference_action_required
from services.reference_import_template_service import list_import_templates
from services.agency_feature_flag_bundle_service import DEFAULT_FEATURE_FLAG_BUNDLES
from services.capability_catalog_service import DEFAULT_CAPABILITY_CATALOG
from services.feature_bundle_rollout_approval_service import APPROVAL_STATUSES
from services.feature_bundle_dependency_service import DEPENDENCY_TYPES
from services.feature_bundle_rollout_change_request_service import CHANGE_REQUEST_IMPACT_LEVELS, CHANGE_REQUEST_PRIORITIES, CHANGE_REQUEST_STATUSES, CHANGE_REQUEST_TYPES
from services.feature_bundle_rollout_decision_service import DECISION_CATEGORIES, DECISION_STATUSES
from services.feature_bundle_rollout_issue_service import ISSUE_SEVERITIES, ISSUE_STATUSES
from services.feature_bundle_rollout_plan_service import PLAN_STAGES
from services.feature_bundle_rollout_readiness_service import READINESS_STATUSES
from services.feature_bundle_rollout_risk_service import RISK_IMPACTS, RISK_LIKELIHOODS, RISK_STATUSES
from services.feature_bundle_rollout_rollback_plan_service import ROLLBACK_PRIORITIES, ROLLBACK_SCOPES, ROLLBACK_STATUSES, ROLLBACK_TRIGGERS
from services.feature_bundle_rollout_schedule_service import SCHEDULE_STATUSES
from services.feature_bundle_rollout_summary_pack_service import PACK_AUDIENCES, PACK_STATUSES
from services.feature_bundle_rollout_timeline_service import (
    TIMELINE_EVENT_TYPES as FEATURE_BUNDLE_ROLLOUT_TIMELINE_EVENT_TYPES,
)
from services.operational_travel_workspace_service import WORKSPACE_PRIORITIES, WORKSPACE_STATUSES, WORKSPACE_TYPES
from services.passenger_workspace_service import PASSENGER_STATUSES
from services.flight_workspace_service import FLIGHT_STATUSES
from services.trip_workspace_service import TRIP_STATUSES
from services.offer_workspace_service import OFFER_STATUSES
from services.booking_workspace_service import BOOKING_WORKSPACE_STATUSES
from services.emd_workspace_service import EMD_DOCUMENT_STATUSES, EMD_WORKSPACE_STATUSES
from services.document_workspace_service import DOCUMENT_WORKSPACE_STATUSES, DOCUMENT_WORKSPACE_TYPES
from services.timeline_workspace_service import (
    COMMUNICATION_TYPES,
    TIMELINE_EVENT_TYPES as OPERATIONAL_TIMELINE_EVENT_TYPES,
)
from services.passenger_service_workflow_service import READINESS_STATES, WORKFLOW_STAGES
from services.airline_operational_intelligence_service import AirlineOperationalIntelligenceService
from services.airline_knowledge_acquisition_service import ACQUISITION_STATUSES, APPROVAL_STATUSES as ACQUISITION_APPROVAL_STATUSES, KNOWLEDGE_GRAPH_PILLARS, REVIEW_STATUSES as ACQUISITION_REVIEW_STATUSES, SOURCE_TYPES as ACQUISITION_SOURCE_TYPES
from services.operational_constraint_engine_service import APPROVAL_STATUSES as OPERATIONAL_CONSTRAINT_APPROVAL_STATUSES, CONDITION_OPERATORS, CONSTRAINT_STATUSES as OPERATIONAL_CONSTRAINT_STATUSES, OUTCOME_TYPES as OPERATIONAL_CONSTRAINT_OUTCOME_TYPES, REVIEW_STATUSES as OPERATIONAL_CONSTRAINT_REVIEW_STATUSES
from services.airline_capability_matrix_service import CAPABILITY_OUTCOMES as MATRIX_CAPABILITY_OUTCOMES, CAPABILITY_REVIEW_STATUSES as MATRIX_REVIEW_STATUSES, CAPABILITY_STATUSES as MATRIX_CAPABILITY_STATUSES, CAPABILITY_STATUS_VALUES as MATRIX_CAPABILITY_STATUS_VALUES, CONFIDENCE_LEVELS as MATRIX_CONFIDENCE_LEVELS, OPERATIONAL_RISK_LEVELS as MATRIX_RISK_LEVELS, OPERATIONAL_VALIDITY_STATUSES as MATRIX_VALIDITY_STATUSES
from services.operational_knowledge_evaluation_service import EVALUATION_CONFIDENCE_LEVELS, EVALUATION_RESULT_VALUES, EVALUATION_STATUSES, EVALUATION_TYPES, OPERATIONAL_RESULTS as EVALUATION_OPERATIONAL_RESULTS, OPERATIONAL_RISK_LEVELS as EVALUATION_RISK_LEVELS
from services.passenger_service_feasibility_service import FEASIBILITY_CONFIDENCE_LEVELS, FEASIBILITY_OUTCOMES, FEASIBILITY_STATUSES, FEASIBILITY_TYPES, OPERATIONAL_RISK_LEVELS as FEASIBILITY_RISK_LEVELS
from services.airline_recommendation_engine_service import AIRLINE_RECOMMENDATION_LEVELS, AIRLINE_RECOMMENDATION_STATUSES, RECOMMENDATION_STATUS_VALUES
from services.intelligent_offer_builder_service import INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES, INTELLIGENT_OFFER_PACKAGE_STATUSES, INTELLIGENT_OFFER_READINESS_STATUSES
from services.operational_intelligence_case_service import OPERATIONAL_INTELLIGENCE_CASE_STATUSES, OPERATIONAL_INTELLIGENCE_OVERALL_STATUSES, PIPELINE_LINK_FIELDS, PIPELINE_READY_FIELDS
from services.service_parameter_taxonomy_service import AMOUNT_TYPES, APPROVAL_STATUS_OPTIONS, EVALUATION_STATUS_OPTIONS, KNOWLEDGE_GRAPH_LINK_FIELDS as TAXONOMY_KNOWLEDGE_GRAPH_LINK_FIELDS, PASSENGER_ASSISTANCE_PARAMETER_FIELDS, PETS_ANIMALS_PARAMETER_FIELDS, PRICING_CATEGORIES, PRICING_FARE_BUNDLES, PRICING_FLIGHT_TYPES, PRICING_PARAMETER_FIELDS, PRICING_ROUTE_TYPES, PRICING_UNITS, PRICING_WAY_VALUES, RESTRICTION_STATUS_OPTIONS, ROUTE_AIRCRAFT_CABIN_PARAMETER_FIELDS, SERVICE_PARAMETER_TAXONOMY_STATUSES, SPECIAL_ITEM_PARAMETER_FIELDS, SUPPORT_STATUS_OPTIONS, TAXONOMY_APPROVAL_STATUSES, TAXONOMY_REVIEW_STATUSES
from services.request_segment_service_precision_service import KNOWLEDGE_LINK_FIELDS as REQUEST_SEGMENT_SERVICE_KNOWLEDGE_LINK_FIELDS, OPERATIONAL_FLAG_FIELDS as REQUEST_SEGMENT_SERVICE_OPERATIONAL_FLAG_FIELDS, REQUEST_SEGMENT_SERVICE_READINESS_STATUSES, REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES, REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES
from services.client_passenger_master_service import CLIENT_MASTER_STATUSES, CLIENT_PASSENGER_LINK_STATUSES, CLIENT_PORTAL_ACCESS_STATUSES, MASTER_COLLECTIONS as CLIENT_PASSENGER_MASTER_COLLECTIONS, PASSENGER_DOCUMENT_STATUSES, PASSENGER_HISTORY_STATUSES, PASSENGER_MASTER_STATUSES, PASSENGER_PREFERENCE_STATUSES
from services.reference_data_engine_service import GOVERNANCE_STATUSES as REFERENCE_DATA_ENGINE_GOVERNANCE_STATUSES, REFERENCE_DATA_DOMAINS_COLLECTION, REVIEW_STATUSES as REFERENCE_DATA_ENGINE_REVIEW_STATUSES, SUPPORTED_REFERENCE_DOMAIN_CODES
from services.knowledge_import_template_service import FOUNDATION_PHASE_LABEL as KNOWLEDGE_IMPORT_TEMPLATE_FOUNDATION_PHASE_LABEL, IMPORT_SCOPES as KNOWLEDGE_IMPORT_TEMPLATE_IMPORT_SCOPES, KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION, TEMPLATE_TYPES as KNOWLEDGE_IMPORT_TEMPLATE_TYPES
from services.airline_knowledge_publishing_service import AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION, PUBLICATION_STATUSES as AIRLINE_KNOWLEDGE_PUBLICATION_STATUSES, RELEASE_CHANNELS as AIRLINE_KNOWLEDGE_RELEASE_CHANNELS, VISIBILITY_STATUSES as AIRLINE_KNOWLEDGE_VISIBILITY_STATUSES
from services.operational_scenario_testing_service import EXPECTED_RECOMMENDATION_LEVELS as OPERATIONAL_SCENARIO_EXPECTED_RECOMMENDATION_LEVELS, OPERATIONAL_SCENARIO_TESTS_COLLECTION, SCENARIO_FAMILIES as OPERATIONAL_SCENARIO_FAMILIES, SCENARIO_TEST_STATUSES as OPERATIONAL_SCENARIO_TEST_STATUSES
from services.knowledge_population_toolkit_service import KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION, POPULATION_STATUSES as KNOWLEDGE_POPULATION_STATUSES, TOOLKIT_READINESS_STATUSES as KNOWLEDGE_POPULATION_READINESS_STATUSES
from services.operational_workflow_orchestration_service import BOOKING_READINESS_STATES as OPERATIONAL_WORKFLOW_BOOKING_READINESS_STATES, DEFAULT_WORKFLOW_DEFINITIONS as OPERATIONAL_WORKFLOW_DEFAULT_DEFINITIONS, GUARD_RESULTS as OPERATIONAL_WORKFLOW_GUARD_RESULTS, GUARD_TYPES as OPERATIONAL_WORKFLOW_GUARD_TYPES, OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION, OPERATIONAL_WORKFLOW_EVENTS_COLLECTION, OPERATIONAL_WORKFLOW_GUARDS_COLLECTION, OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION, OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION, REQUEST_LIFECYCLE_STATES as OPERATIONAL_WORKFLOW_REQUEST_STATES, SERVICE_FULFILLMENT_STATES as OPERATIONAL_WORKFLOW_SERVICE_STATES, TRANSITION_STATUSES as OPERATIONAL_WORKFLOW_TRANSITION_STATUSES, TRIP_LIFECYCLE_STATES as OPERATIONAL_WORKFLOW_TRIP_STATES, WORKFLOW_STATUSES as OPERATIONAL_WORKFLOW_STATUSES
from services.agent_work_queue_service import ASSIGNMENT_EVENT_TYPES as OPERATIONAL_ASSIGNMENT_EVENT_TYPES, BLOCKER_STATUSES as OPERATIONAL_QUEUE_BLOCKER_STATUSES, CANONICAL_QUEUE_CODES as OPERATIONAL_QUEUE_CODES, DEFAULT_QUEUE_DEFINITIONS as OPERATIONAL_DEFAULT_QUEUE_DEFINITIONS, OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION, OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION, OPERATIONAL_QUEUE_VIEWS_COLLECTION, OPERATIONAL_WORK_ITEMS_COLLECTION, PHASE_LABEL as AGENT_WORK_QUEUE_PHASE_LABEL, SLA_STATUSES as OPERATIONAL_QUEUE_SLA_STATUSES, WORK_ITEM_PRIORITIES as OPERATIONAL_WORK_ITEM_PRIORITIES, WORK_ITEM_SEVERITIES as OPERATIONAL_WORK_ITEM_SEVERITIES, WORK_ITEM_STATUSES as OPERATIONAL_WORK_ITEM_STATUSES, WORK_ITEM_TYPES as OPERATIONAL_WORK_ITEM_TYPES
from services.operational_sla_deadline_service import BREACH_STATES as OPERATIONAL_DEADLINE_BREACH_STATES, BUSINESS_HOURS_BEHAVIORS as OPERATIONAL_BUSINESS_HOURS_BEHAVIORS, DEADLINE_STATUSES as OPERATIONAL_DEADLINE_STATUSES, DEADLINE_TYPES as OPERATIONAL_DEADLINE_TYPES, DEFAULT_SLA_POLICIES as OPERATIONAL_DEFAULT_SLA_POLICIES, OPERATIONAL_BUSINESS_CALENDARS_COLLECTION, OPERATIONAL_DEADLINES_COLLECTION, OPERATIONAL_SLA_EVENTS_COLLECTION, OPERATIONAL_SLA_POLICIES_COLLECTION, PHASE_LABEL as SLA_OPERATIONAL_DEADLINE_PHASE_LABEL, SLA_DURATION_UNITS as OPERATIONAL_SLA_DURATION_UNITS, SLA_EVENT_TYPES as OPERATIONAL_SLA_EVENT_TYPES, SLA_POLICY_SCOPES as OPERATIONAL_SLA_POLICY_SCOPES, SLA_POLICY_STATUSES as OPERATIONAL_SLA_POLICY_STATUSES
from services.task_automation_dependency_service import DEFAULT_AUTOMATION_RULES as OPERATIONAL_DEFAULT_TASK_AUTOMATION_RULES, OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION, OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION, OPERATIONAL_TASK_DEPENDENCIES_COLLECTION, OPERATIONAL_TASK_TEMPLATES_COLLECTION, PHASE_LABEL as TASK_AUTOMATION_PHASE_LABEL, SAFE_TASK_TEMPLATES as OPERATIONAL_SAFE_TASK_TEMPLATES, TASK_AUTOMATION_RULE_STATUSES, TASK_AUTOMATION_RUN_STATUSES, TASK_AUTOMATION_TRIGGER_EVENTS, TASK_DEPENDENCY_STATUSES, TASK_DEPENDENCY_TYPES, TASK_TEMPLATE_STATUSES
from services.request_to_trip_conversion_service import CONVERSION_ISSUE_TYPES, CONVERSION_MAPPING_TYPES, CONVERSION_MODES, CONVERSION_PLAN_STATUSES, CONVERSION_RUN_STATUSES, REQUEST_TRIP_CONVERSION_ISSUES_COLLECTION, REQUEST_TRIP_CONVERSION_PLANS_COLLECTION, REQUEST_TRIP_CONVERSION_RUNS_COLLECTION, REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION
from services.offer_to_booking_handoff_service import BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION, BOOKING_MODES as OFFER_BOOKING_MODES, HANDOFF_CHECK_STATUSES, HANDOFF_MAPPING_TYPES, HANDOFF_STATUSES, INSTRUCTION_TYPES as BOOKING_INSTRUCTION_TYPES, OFFER_BOOKING_HANDOFF_CHECKS_COLLECTION, OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION, OFFER_BOOKING_HANDOFFS_COLLECTION
from services.after_sales_workflow_service import AFTER_SALES_CASES_COLLECTION, AFTER_SALES_CASE_ITEMS_COLLECTION, AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION, AFTER_SALES_DECISIONS_COLLECTION, AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION, AFTER_SALES_RESOLUTIONS_COLLECTION, CASE_STATUSES as AFTER_SALES_CASE_STATUSES, CASE_TYPES as AFTER_SALES_CASE_TYPES, COMMUNICATION_TYPES as AFTER_SALES_COMMUNICATION_TYPES, DECISION_STATUSES as AFTER_SALES_DECISION_STATUSES, FINANCIAL_IMPACT_TYPES as AFTER_SALES_FINANCIAL_IMPACT_TYPES, RESOLUTION_STATUSES as AFTER_SALES_RESOLUTION_STATUSES
from services.operations_command_center_service import VIEW_TYPES as OPERATIONS_COMMAND_CENTER_VIEW_TYPES, OperationsCommandCenterService
from services.operational_workflow_maturity_service import GOLDEN_PATH_STAGES as OPERATIONAL_MATURITY_GOLDEN_PATH_STAGES, MATURITY_DIMENSIONS as OPERATIONAL_MATURITY_DIMENSIONS, TEST_CASE_TEMPLATES as OPERATIONAL_MATURITY_TEST_CASE_TEMPLATES, OperationalWorkflowMaturityService
from services.airline_master_profile_intelligence_service import CAPABILITY_PHASE as AIRLINE_MASTER_PROFILE_CAPABILITY_PHASE, AirlineMasterProfileIntelligenceService
from services.airline_policy_evidence_governance_service import CAPABILITY_PHASE as AIRLINE_EVIDENCE_CAPABILITY_PHASE, AirlinePolicyEvidenceGovernanceService
from services.airline_knowledge_versioning_service import CAPABILITY_PHASE as AIRLINE_KNOWLEDGE_VERSIONING_CAPABILITY_PHASE, AirlineKnowledgeVersioningService
from services.airline_service_coverage_gap_service import CAPABILITY_PHASE as AIRLINE_SERVICE_COVERAGE_CAPABILITY_PHASE, AirlineServiceCoverageGapService
from services.airline_distribution_capability_service import CAPABILITY_PHASE as AIRLINE_DISTRIBUTION_CAPABILITY_PHASE, AirlineDistributionCapabilityService
from services.interline_codeshare_intelligence_service import CAPABILITY_PHASE as INTERLINE_CODESHARE_CAPABILITY_PHASE, InterlineCodeshareIntelligenceService
from services.airline_fare_family_brand_intelligence_service import CAPABILITY_PHASE as AIRLINE_FARE_BRAND_CAPABILITY_PHASE, AirlineFareFamilyBrandIntelligenceService
from services.airline_contact_communication_intelligence_service import CAPABILITY_PHASE as AIRLINE_CONTACT_CAPABILITY_PHASE, AirlineContactCommunicationIntelligenceService
from services.airline_intelligence_scale_readiness_service import CAPABILITY_PHASE as AIRLINE_INTELLIGENCE_READINESS_CAPABILITY_PHASE, AirlineIntelligenceScaleReadinessService
from services.canonical_journey_itinerary_service import CAPABILITY_PHASE as CANONICAL_JOURNEY_CAPABILITY_PHASE, CanonicalJourneyItineraryService
from services.journey_segment_authoring_service import CAPABILITY_PHASE as JOURNEY_AUTHORING_CAPABILITY_PHASE, JourneySegmentAuthoringService
from services.journey_option_fare_brand_composition_service import CAPABILITY_PHASE as JOURNEY_COMPOSITION_CAPABILITY_PHASE, JourneyOptionFareBrandCompositionService
from services.journey_comparison_client_presentation_service import CAPABILITY_PHASE as JOURNEY_PRESENTATION_CAPABILITY_PHASE, JourneyComparisonClientPresentationService
from services.offer_delivery_client_interaction_service import CAPABILITY_PHASE as OFFER_DELIVERY_CAPABILITY_PHASE, OfferDeliveryClientInteractionService
from services.pilot_readiness_service import CHECK_FAMILIES as PILOT_READINESS_CHECK_FAMILIES, CHECK_STATUSES as PILOT_READINESS_CHECK_STATUSES, GOLDEN_PATH_CASE_TEMPLATES as PILOT_GOLDEN_PATH_CASE_TEMPLATES, GOLDEN_PATH_STAGE_CODES as PILOT_GOLDEN_PATH_STAGE_CODES, GOLDEN_PATH_STATUSES as PILOT_GOLDEN_PATH_STATUSES, ISSUE_STATUSES as PILOT_READINESS_ISSUE_STATUSES, PILOT_GOLDEN_PATH_CASES_COLLECTION, PILOT_GOLDEN_PATH_RUNS_COLLECTION, PILOT_READINESS_ASSESSMENTS_COLLECTION, PILOT_READINESS_CHECKS_COLLECTION, PILOT_READINESS_ISSUES_COLLECTION, PILOT_READINESS_PROFILES_COLLECTION, READINESS_STATUSES as PILOT_READINESS_STATUSES, REMEDIATION_LINKS as PILOT_READINESS_REMEDIATION_LINKS
from services.knowledge_quality_assurance_service import APPROVAL_RECOMMENDATIONS as KNOWLEDGE_QA_APPROVAL_RECOMMENDATIONS, KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION, QA_CHECKS as KNOWLEDGE_QA_CHECKS, QA_STATUSES as KNOWLEDGE_QA_STATUSES, SEVERITY_LEVELS as KNOWLEDGE_QA_SEVERITY_LEVELS, TARGET_TYPES as KNOWLEDGE_QA_TARGET_TYPES
from services.operational_rule_composer_service import LIFECYCLE_STATUSES as OPERATIONAL_RULE_LIFECYCLE_STATUSES, OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION, RULE_FAMILIES as OPERATIONAL_RULE_FAMILIES, SEVERITY_LEVELS as OPERATIONAL_RULE_SEVERITY_LEVELS, SUPPORTED_OPERATORS as OPERATIONAL_RULE_SUPPORTED_OPERATORS
from services.pricing_formula_builder_service import CLIENT_VISIBILITY_OPTIONS as PRICING_FORMULA_CLIENT_VISIBILITY_OPTIONS, FORMULA_STATUSES as PRICING_FORMULA_STATUSES, PRICING_FORMULA_BUILDERS_COLLECTION
from services.visual_policy_editor_service import POLICY_CARD_STATUSES, POLICY_FAMILIES, SUPPORT_STATUSES as VISUAL_POLICY_SUPPORT_STATUSES, VISUAL_POLICY_EDITOR_CARDS_COLLECTION
from services.airline_knowledge_governance_service import APPROVAL_STATUSES as GOVERNANCE_APPROVAL_STATUSES, CHANGE_TYPES as GOVERNANCE_CHANGE_TYPES, KNOWLEDGE_LIFECYCLE_STATUSES, KNOWLEDGE_SCOPES, RELEASE_STATUSES as GOVERNANCE_RELEASE_STATUSES, REVIEW_STATUSES as GOVERNANCE_REVIEW_STATUSES
from services.airline_knowledge_normalisation_service import APPROVAL_STATUSES as NORMALISATION_APPROVAL_STATUSES, NORMALISATION_STATUSES, NORMALISATION_TYPES, REVIEW_STATUSES as NORMALISATION_REVIEW_STATUSES
from services.ssr_osi_workspace_service import SSR_OSI_APPROVAL_STATUSES, SSR_OSI_NEED_CATEGORIES, SSR_OSI_OPERATIONAL_STATUSES, SSR_OSI_READINESS_STATUSES
from services.ticket_workspace_service import TICKET_DOCUMENT_STATUSES, TICKET_WORKSPACE_STATUSES
from services.travel_request_workspace_service import REQUEST_PRIORITIES, REQUEST_STATUSES, REQUEST_TYPES
from services.rollout_dashboard_service import DASHBOARD_SECTIONS
from services.saas_subscription_service import AGENCY_MODULE_VISIBILITY_CATALOG
from services.secret_service import check_secret
from services.seed_service import seed_core_data
from services.authentication_security_service import validate_auth_token

settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title="AeroAssist AgencyOS API",
    version="0.1.0",
    description="AeroAssist AgencyOS API foundation through Phase 56.5.4 authentication, security, and HTTP hardening.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)
app.add_middleware(SecurityHttpMiddleware, settings=settings)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)


@app.on_event("startup")
async def startup() -> None:
    assert_startup_safe(get_settings())
    await database.connect()
    if get_settings().seed_on_startup:
        await seed_core_data(database)


@app.get("/api/health")
async def root_health() -> dict:
    settings = get_settings()
    payload = {
        "ok": True,
        "service": "AeroAssist AgencyOS API",
        "phase": CURRENT_BUILD_PHASE,
    }
    if not settings.is_production:
        payload["app_env"] = settings.app_env
    return payload


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


async def internal_readiness_payload() -> dict:
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
    offer_builder_workspace_count = await database.collection("offer_workspaces").count()
    offer_option_count = await database.collection("offer_options").count()
    offer_builder_segment_count = await database.collection("offer_builder_segments").count()
    offer_fare_bundle_count = await database.collection("offer_fare_bundles").count()
    offer_pricing_line_count = await database.collection("offer_pricing_lines").count()
    offer_comparison_snapshot_count = await database.collection("offer_comparison_snapshots").count()
    offer_acceptance_count = await database.collection("offer_acceptances").count()
    trip_accepted_offer_snapshot_count = await database.collection("trip_accepted_offer_snapshots").count()
    booking_readiness_package_count = await database.collection("booking_readiness_packages").count()
    booking_workspace_records = await database.collection("booking_workspaces").find_many()
    booking_workspace_count = len(booking_workspace_records)
    booking_record_count = await database.collection("booking_records").count()
    booking_timeline_events = await database.collection("booking_timeline_events").find_many()
    booking_timeline_event_count = len(
        [item for item in booking_timeline_events if item.get("booking_workspace_id")]
    )
    booking_workspace_ready_count = len([item for item in booking_workspace_records if (item.get("booking_status") or item.get("status")) == "ready_to_book"])
    booking_workspace_blocked_count = len([item for item in booking_workspace_records if (item.get("booking_status") or item.get("status")) == "blocked"])
    booking_workspace_cancelled_count = len([item for item in booking_workspace_records if (item.get("booking_status") or item.get("status")) == "cancelled"])
    booking_workspace_status_counts = {
        booking_status: len(
            [
                item
                for item in booking_workspace_records
                if (item.get("booking_status") or item.get("status") or "draft") == booking_status
            ]
        )
        for booking_status in BOOKING_WORKSPACE_STATUSES
    }
    booking_workspace_owner_count = len({item.get("booking_owner") for item in booking_workspace_records if item.get("booking_owner")})
    booking_workspace_supplier_count = len({item.get("supplier_reference") for item in booking_workspace_records if item.get("supplier_reference")})
    booking_workspace_airline_count = len({item.get("airline_pnr") for item in booking_workspace_records if item.get("airline_pnr")})
    booking_workspace_operational_workspace_count = len({item.get("operational_workspace_id") for item in booking_workspace_records if item.get("operational_workspace_id")})
    booking_workspace_trip_workspace_count = len({item.get("trip_workspace_id") or item.get("trip_id") for item in booking_workspace_records if item.get("trip_workspace_id") or item.get("trip_id")})
    booking_workspace_offer_workspace_count = len({item.get("offer_workspace_id") for item in booking_workspace_records if item.get("offer_workspace_id")})
    ticket_workspace_records = await database.collection("ticket_workspaces").find_many()
    ticket_workspace_count = len(ticket_workspace_records)
    ticket_workspace_status_counts = {
        ticket_status: len(
            [
                item
                for item in ticket_workspace_records
                if (item.get("ticket_status") or "draft") == ticket_status
            ]
        )
        for ticket_status in TICKET_WORKSPACE_STATUSES
    }
    ticket_document_status_counts = {
        ticket_status: len(
            [
                item
                for item in ticket_workspace_records
                if (item.get("ticket_document_status") or "draft_metadata") == ticket_status
            ]
        )
        for ticket_status in TICKET_DOCUMENT_STATUSES
    }
    ticket_workspace_validating_carrier_count = len({item.get("validating_carrier") for item in ticket_workspace_records if item.get("validating_carrier")})
    ticket_workspace_currency_count = len({item.get("currency") for item in ticket_workspace_records if item.get("currency")})
    ticket_workspace_passenger_count = len({item.get("passenger_id") for item in ticket_workspace_records if item.get("passenger_id")})
    ticket_workspace_booking_reference_count = len({item.get("booking_reference") for item in ticket_workspace_records if item.get("booking_reference")})
    ticket_workspace_operational_workspace_count = len({item.get("operational_workspace_id") for item in ticket_workspace_records if item.get("operational_workspace_id")})
    ticket_workspace_trip_workspace_count = len({item.get("trip_workspace_id") for item in ticket_workspace_records if item.get("trip_workspace_id")})
    ticket_workspace_offer_workspace_count = len({item.get("offer_workspace_id") for item in ticket_workspace_records if item.get("offer_workspace_id")})
    ticket_workspace_booking_workspace_count = len({item.get("booking_workspace_id") for item in ticket_workspace_records if item.get("booking_workspace_id")})
    ticket_workspace_coupon_detail_count = sum(len(item.get("coupon_details") or []) for item in ticket_workspace_records)
    ticket_workspace_pricing_unit_count = sum(len(item.get("pricing_units") or []) for item in ticket_workspace_records)
    ticket_workspace_fare_component_count = sum(len(item.get("fare_components") or []) for item in ticket_workspace_records)
    ticket_workspace_tax_breakdown_count = sum(len(item.get("tax_breakdown") or []) for item in ticket_workspace_records)
    ticket_workspace_exchange_reference_count = sum(len(item.get("exchange_reference_ids") or []) for item in ticket_workspace_records)
    ticket_workspace_refund_reference_count = sum(len(item.get("refund_reference_ids") or []) for item in ticket_workspace_records)
    ticket_workspace_void_reference_count = sum(len(item.get("void_reference_ids") or []) for item in ticket_workspace_records)
    emd_workspace_records = await database.collection("emd_workspaces").find_many()
    emd_workspace_count = len(emd_workspace_records)
    emd_workspace_status_counts = {
        emd_status: len(
            [
                item
                for item in emd_workspace_records
                if (item.get("emd_status") or "draft") == emd_status
            ]
        )
        for emd_status in EMD_WORKSPACE_STATUSES
    }
    emd_document_status_counts = {
        emd_status: len(
            [
                item
                for item in emd_workspace_records
                if (item.get("emd_document_status") or "draft_metadata") == emd_status
            ]
        )
        for emd_status in EMD_DOCUMENT_STATUSES
    }
    emd_workspace_validating_carrier_count = len({item.get("validating_carrier") for item in emd_workspace_records if item.get("validating_carrier")})
    emd_workspace_currency_count = len({item.get("currency") for item in emd_workspace_records if item.get("currency")})
    emd_workspace_passenger_count = len({item.get("passenger_id") for item in emd_workspace_records if item.get("passenger_id")})
    emd_workspace_rfic_count = len({item.get("rfic") for item in emd_workspace_records if item.get("rfic")})
    emd_workspace_rfisc_count = len({item.get("rfisc") for item in emd_workspace_records if item.get("rfisc")})
    emd_workspace_service_category_count = len({item.get("service_category") for item in emd_workspace_records if item.get("service_category")})
    emd_workspace_booking_reference_count = len({item.get("booking_reference") for item in emd_workspace_records if item.get("booking_reference")})
    emd_workspace_operational_workspace_count = len({item.get("operational_workspace_id") for item in emd_workspace_records if item.get("operational_workspace_id")})
    emd_workspace_trip_workspace_count = len({item.get("trip_workspace_id") for item in emd_workspace_records if item.get("trip_workspace_id")})
    emd_workspace_offer_workspace_count = len({item.get("offer_workspace_id") for item in emd_workspace_records if item.get("offer_workspace_id")})
    emd_workspace_booking_workspace_count = len({item.get("booking_workspace_id") for item in emd_workspace_records if item.get("booking_workspace_id")})
    emd_workspace_ticket_workspace_count = len({item.get("ticket_workspace_id") for item in emd_workspace_records if item.get("ticket_workspace_id")})
    emd_workspace_coupon_detail_count = sum(len(item.get("emd_coupon_details") or []) for item in emd_workspace_records)
    emd_workspace_tax_breakdown_count = sum(len(item.get("tax_breakdown") or []) for item in emd_workspace_records)
    emd_workspace_associated_ticket_coupon_count = sum(len(item.get("associated_ticket_coupon_numbers") or []) for item in emd_workspace_records)
    emd_workspace_associated_flight_workspace_count = sum(len(item.get("associated_flight_workspace_ids") or []) for item in emd_workspace_records)
    emd_workspace_ssr_count = sum(len(item.get("ssr_ids") or []) for item in emd_workspace_records)
    emd_workspace_osi_count = sum(len(item.get("osi_ids") or []) for item in emd_workspace_records)
    emd_workspace_ancillary_service_count = sum(len(item.get("ancillary_service_ids") or []) for item in emd_workspace_records)
    emd_workspace_exchange_reference_count = sum(len(item.get("exchange_reference_ids") or []) for item in emd_workspace_records)
    emd_workspace_refund_reference_count = sum(len(item.get("refund_reference_ids") or []) for item in emd_workspace_records)
    emd_workspace_void_reference_count = sum(len(item.get("void_reference_ids") or []) for item in emd_workspace_records)
    emd_workspace_linked_document_count = sum(len(item.get("linked_document_ids") or []) for item in emd_workspace_records)
    ssr_osi_workspace_records = await database.collection("ssr_osi_workspaces").find_many()
    ssr_osi_workspace_count = len(ssr_osi_workspace_records)
    ssr_osi_operational_status_counts = {
        status: len([item for item in ssr_osi_workspace_records if item.get("operational_status") == status])
        for status in SSR_OSI_OPERATIONAL_STATUSES
    }
    ssr_osi_readiness_status_counts = {
        status: len([item for item in ssr_osi_workspace_records if item.get("readiness_status") == status])
        for status in SSR_OSI_READINESS_STATUSES
    }
    ssr_osi_approval_status_counts = {
        status: len([item for item in ssr_osi_workspace_records if item.get("approval_status") == status])
        for status in SSR_OSI_APPROVAL_STATUSES
    }
    ssr_osi_need_category_counts = {
        category: len([item for item in ssr_osi_workspace_records if item.get("need_category") == category])
        for category in SSR_OSI_NEED_CATEGORIES
    }
    ssr_osi_airline_count = len(
        {
            item.get("airline_code") or item.get("validating_carrier") or item.get("operating_carrier")
            for item in ssr_osi_workspace_records
            if item.get("airline_code") or item.get("validating_carrier") or item.get("operating_carrier")
        }
    )
    ssr_osi_passenger_count = len({item.get("passenger_workspace_id") for item in ssr_osi_workspace_records if item.get("passenger_workspace_id")})
    ssr_osi_rfic_count = len({item.get("rfic") for item in ssr_osi_workspace_records if item.get("rfic")})
    ssr_osi_rfisc_count = len({item.get("rfisc") for item in ssr_osi_workspace_records if item.get("rfisc")})
    ssr_osi_emd_required_count = len([item for item in ssr_osi_workspace_records if item.get("emd_required")])
    ssr_osi_medif_required_count = len([item for item in ssr_osi_workspace_records if item.get("medif_required")])
    ssr_osi_approval_required_count = len([item for item in ssr_osi_workspace_records if item.get("approval_required")])
    ssr_osi_missing_requirement_count = sum(len(item.get("missing_requirements") or []) for item in ssr_osi_workspace_records)
    ssr_osi_unresolved_item_count = sum(len(item.get("unresolved_items") or []) for item in ssr_osi_workspace_records)
    ssr_osi_document_requirement_count = sum(len(item.get("document_requirements") or []) for item in ssr_osi_workspace_records)
    ssr_osi_task_count = sum(len(item.get("task_ids") or []) for item in ssr_osi_workspace_records)
    ssr_osi_timeline_count = sum(len(item.get("timeline_ids") or []) for item in ssr_osi_workspace_records)
    ssr_osi_communication_count = sum(len(item.get("communication_ids") or []) for item in ssr_osi_workspace_records)
    ssr_osi_flight_workspace_count = sum(len(item.get("flight_workspace_ids") or []) for item in ssr_osi_workspace_records)
    ssr_osi_linked_document_count = sum(len(item.get("linked_document_ids") or []) for item in ssr_osi_workspace_records)
    document_workspace_records = await database.collection("document_workspaces").find_many()
    document_workspace_count = len(document_workspace_records)
    document_workspace_status_counts = {
        status: len([item for item in document_workspace_records if item.get("document_status") == status])
        for status in DOCUMENT_WORKSPACE_STATUSES
    }
    document_workspace_type_counts = {
        document_type: len([item for item in document_workspace_records if item.get("document_type") == document_type])
        for document_type in DOCUMENT_WORKSPACE_TYPES
    }
    document_workspace_verification_status_count = len({item.get("verification_status") for item in document_workspace_records if item.get("verification_status")})
    document_workspace_required_for_travel_count = len([item for item in document_workspace_records if item.get("required_for_travel")])
    document_workspace_required_by_airline_count = len([item for item in document_workspace_records if item.get("required_by_airline")])
    document_workspace_required_by_airport_count = len([item for item in document_workspace_records if item.get("required_by_airport")])
    document_workspace_required_by_authority_count = len([item for item in document_workspace_records if item.get("required_by_authority")])
    document_workspace_customer_visible_count = len([item for item in document_workspace_records if item.get("customer_visible")])
    document_workspace_airline_visible_count = len([item for item in document_workspace_records if item.get("airline_visible")])
    document_workspace_internal_only_count = len([item for item in document_workspace_records if item.get("internal_only")])
    document_workspace_passenger_workspace_count = len({item.get("passenger_workspace_id") for item in document_workspace_records if item.get("passenger_workspace_id")})
    document_workspace_travel_request_workspace_count = len({item.get("travel_request_workspace_id") for item in document_workspace_records if item.get("travel_request_workspace_id")})
    document_workspace_trip_workspace_count = len({item.get("trip_workspace_id") for item in document_workspace_records if item.get("trip_workspace_id")})
    document_workspace_booking_workspace_count = len({item.get("booking_workspace_id") for item in document_workspace_records if item.get("booking_workspace_id")})
    document_workspace_ticket_workspace_count = len({item.get("ticket_workspace_id") for item in document_workspace_records if item.get("ticket_workspace_id")})
    document_workspace_emd_workspace_count = len({item.get("emd_workspace_id") for item in document_workspace_records if item.get("emd_workspace_id")})
    document_workspace_ssr_osi_workspace_count = len({item.get("ssr_osi_workspace_id") for item in document_workspace_records if item.get("ssr_osi_workspace_id")})
    document_workspace_operational_intelligence_record_count = sum(len(item.get("operational_intelligence_record_ids") or []) for item in document_workspace_records)
    document_workspace_package_count = sum(len(item.get("document_package_ids") or []) for item in document_workspace_records)
    document_workspace_render_job_count = sum(len(item.get("render_job_ids") or []) for item in document_workspace_records)
    document_workspace_share_record_count = sum(len(item.get("share_record_ids") or []) for item in document_workspace_records)
    document_workspace_storage_reference_count = len({item.get("storage_reference") for item in document_workspace_records if item.get("storage_reference")})
    operational_timeline_records = await database.collection("operational_timelines").find_many()
    operational_timeline_count = len(operational_timeline_records)
    operational_timeline_event_type_counts = {
        event_type: len([item for item in operational_timeline_records if item.get("event_type") == event_type])
        for event_type in OPERATIONAL_TIMELINE_EVENT_TYPES
    }
    operational_timeline_communication_type_counts = {
        communication_type: len([item for item in operational_timeline_records if item.get("communication_type") == communication_type])
        for communication_type in COMMUNICATION_TYPES
    }
    operational_timeline_status_count = len({item.get("event_status") for item in operational_timeline_records if item.get("event_status")})
    operational_timeline_priority_count = len({item.get("event_priority") for item in operational_timeline_records if item.get("event_priority")})
    operational_timeline_category_count = len({item.get("event_category") for item in operational_timeline_records if item.get("event_category")})
    operational_timeline_passenger_workspace_count = len({item.get("passenger_workspace_id") for item in operational_timeline_records if item.get("passenger_workspace_id")})
    operational_timeline_travel_request_workspace_count = len({item.get("travel_request_workspace_id") for item in operational_timeline_records if item.get("travel_request_workspace_id")})
    operational_timeline_trip_workspace_count = len({item.get("trip_workspace_id") for item in operational_timeline_records if item.get("trip_workspace_id")})
    operational_timeline_booking_workspace_count = len({item.get("booking_workspace_id") for item in operational_timeline_records if item.get("booking_workspace_id")})
    operational_timeline_ticket_workspace_count = len({item.get("ticket_workspace_id") for item in operational_timeline_records if item.get("ticket_workspace_id")})
    operational_timeline_emd_workspace_count = len({item.get("emd_workspace_id") for item in operational_timeline_records if item.get("emd_workspace_id")})
    operational_timeline_ssr_osi_workspace_count = len({item.get("ssr_osi_workspace_id") for item in operational_timeline_records if item.get("ssr_osi_workspace_id")})
    operational_timeline_document_workspace_count = len({item.get("document_workspace_id") for item in operational_timeline_records if item.get("document_workspace_id")})
    operational_timeline_attachment_count = sum(len(item.get("attachment_ids") or []) for item in operational_timeline_records)
    operational_timeline_approval_reference_count = len({item.get("approval_reference") for item in operational_timeline_records if item.get("approval_reference")})
    operational_timeline_reminder_required_count = len([item for item in operational_timeline_records if item.get("reminder_required")])
    operational_timeline_internal_only_count = len([item for item in operational_timeline_records if item.get("internal_only")])
    operational_timeline_passenger_visible_count = len([item for item in operational_timeline_records if item.get("passenger_visible")])
    operational_timeline_airline_visible_count = len([item for item in operational_timeline_records if item.get("airline_visible")])
    passenger_service_workflow_records = await database.collection("passenger_service_workflows").find_many()
    passenger_service_workflow_count = len(passenger_service_workflow_records)
    passenger_service_workflow_stage_counts = {
        stage: len([item for item in passenger_service_workflow_records if item.get("current_stage") == stage])
        for stage in WORKFLOW_STAGES
    }
    passenger_service_workflow_readiness_counts = {
        readiness: len([item for item in passenger_service_workflow_records if item.get("readiness_status") == readiness])
        for readiness in READINESS_STATES
    }
    passenger_service_workflow_status_count = len({item.get("workflow_status") for item in passenger_service_workflow_records if item.get("workflow_status")})
    passenger_service_workflow_type_count = len({item.get("workflow_type") for item in passenger_service_workflow_records if item.get("workflow_type")})
    passenger_service_workflow_priority_count = len({item.get("workflow_priority") for item in passenger_service_workflow_records if item.get("workflow_priority")})
    passenger_service_workflow_airline_count = len({item.get("related_airline") for item in passenger_service_workflow_records if item.get("related_airline")})
    passenger_service_workflow_assigned_agent_count = len({item.get("responsible_agent") for item in passenger_service_workflow_records if item.get("responsible_agent")})
    passenger_service_workflow_passenger_workspace_count = len({item.get("passenger_workspace_id") for item in passenger_service_workflow_records if item.get("passenger_workspace_id")})
    passenger_service_workflow_travel_request_workspace_count = len({item.get("travel_request_workspace_id") for item in passenger_service_workflow_records if item.get("travel_request_workspace_id")})
    passenger_service_workflow_trip_workspace_count = len({item.get("trip_workspace_id") for item in passenger_service_workflow_records if item.get("trip_workspace_id")})
    passenger_service_workflow_booking_workspace_count = len({item.get("booking_workspace_id") for item in passenger_service_workflow_records if item.get("booking_workspace_id")})
    passenger_service_workflow_ticket_workspace_count = len({item.get("ticket_workspace_id") for item in passenger_service_workflow_records if item.get("ticket_workspace_id")})
    passenger_service_workflow_emd_workspace_count = len({item.get("emd_workspace_id") for item in passenger_service_workflow_records if item.get("emd_workspace_id")})
    passenger_service_workflow_ssr_osi_workspace_count = len({item.get("ssr_osi_workspace_id") for item in passenger_service_workflow_records if item.get("ssr_osi_workspace_id")})
    passenger_service_workflow_document_workspace_count = len({item.get("document_workspace_id") for item in passenger_service_workflow_records if item.get("document_workspace_id")})
    passenger_service_workflow_timeline_workspace_count = len({item.get("timeline_workspace_id") for item in passenger_service_workflow_records if item.get("timeline_workspace_id")})
    passenger_service_workflow_blocking_requirement_count = sum(len(item.get("blocking_requirements") or []) for item in passenger_service_workflow_records)
    passenger_service_workflow_completed_requirement_count = sum(len(item.get("completed_requirements") or []) for item in passenger_service_workflow_records)
    passenger_service_workflow_recommendation_pack_count = len({item.get("recommendation_pack_reference") for item in passenger_service_workflow_records if item.get("recommendation_pack_reference")})
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
    airline_operational_intelligence_service = AirlineOperationalIntelligenceService(database)
    airline_operational_intelligence_architecture_record = await airline_operational_intelligence_service.ensure_architecture_record()
    airline_operational_intelligence_architecture_count = await database.collection("airline_operational_intelligence_architecture").count()
    airline_knowledge_acquisition_records = await database.collection("airline_knowledge_acquisitions").find_many()
    airline_knowledge_acquisition_count = len(airline_knowledge_acquisition_records)
    airline_knowledge_acquisition_status_counts = {
        status: len([item for item in airline_knowledge_acquisition_records if item.get("acquisition_status") == status])
        for status in ACQUISITION_STATUSES
    }
    airline_knowledge_acquisition_source_type_counts = {
        source_type: len([item for item in airline_knowledge_acquisition_records if item.get("source_type") == source_type])
        for source_type in ACQUISITION_SOURCE_TYPES
    }
    airline_knowledge_acquisition_review_status_counts = {
        status: len([item for item in airline_knowledge_acquisition_records if item.get("review_status") == status])
        for status in ACQUISITION_REVIEW_STATUSES
    }
    airline_knowledge_acquisition_approval_status_counts = {
        status: len([item for item in airline_knowledge_acquisition_records if item.get("approval_status") == status])
        for status in ACQUISITION_APPROVAL_STATUSES
    }
    airline_knowledge_acquisition_official_source_count = len([item for item in airline_knowledge_acquisition_records if item.get("official_source_flag")])
    airline_knowledge_acquisition_raw_source_text_count = len([item for item in airline_knowledge_acquisition_records if item.get("raw_source_text")])
    airline_knowledge_acquisition_service_domain_count = len({item.get("service_domain") for item in airline_knowledge_acquisition_records if item.get("service_domain")})
    airline_knowledge_acquisition_service_family_count = len({item.get("service_family") for item in airline_knowledge_acquisition_records if item.get("service_family")})
    airline_knowledge_acquisition_ssr_code_count = len({item.get("ssr_code") for item in airline_knowledge_acquisition_records if item.get("ssr_code")})
    airline_knowledge_acquisition_rfic_rfisc_count = len({(item.get("rfic"), item.get("rfisc")) for item in airline_knowledge_acquisition_records if item.get("rfic") or item.get("rfisc")})
    airline_knowledge_acquisition_version_link_count = (
        len([item for item in airline_knowledge_acquisition_records if item.get("previous_acquisition_id")])
        + sum(len(item.get("supersedes_acquisition_ids") or []) for item in airline_knowledge_acquisition_records)
    )
    airline_knowledge_acquisition_future_aoie_link_count = sum(
        len(item.get("parser_run_ids") or [])
        + len(item.get("normalized_rule_ids") or [])
        + len(item.get("knowledge_version_ids") or [])
        + len(item.get("capability_matrix_ids") or [])
        for item in airline_knowledge_acquisition_records
    )
    airline_knowledge_acquisition_operational_link_count = sum(
        len(item.get("ssr_osi_workspace_ids") or [])
        + len(item.get("emd_workspace_ids") or [])
        + len(item.get("ticket_workspace_ids") or [])
        + len(item.get("document_workspace_ids") or [])
        for item in airline_knowledge_acquisition_records
    )
    airline_knowledge_acquisition_policy_count = len([item for item in airline_knowledge_acquisition_records if item.get("policy")])
    airline_knowledge_acquisition_pricing_count = len([item for item in airline_knowledge_acquisition_records if item.get("pricing")])
    airline_knowledge_acquisition_capability_count = sum(len(item.get("capabilities") or []) for item in airline_knowledge_acquisition_records)
    airline_knowledge_acquisition_operational_constraint_count = sum(
        len(item.get("operational_constraints") or [])
        + len((item.get("animal_transport") or {}).get("constraints") or [])
        + sum(len(extra_seat.get("operational_constraints") or []) for extra_seat in (item.get("extra_seat") or []) if isinstance(extra_seat, dict))
        + sum(len(cabin.get("constraints") or []) for cabin in (item.get("cabin_capabilities") or []) if isinstance(cabin, dict))
        for item in airline_knowledge_acquisition_records
    )
    airline_knowledge_acquisition_animal_transport_count = len([item for item in airline_knowledge_acquisition_records if item.get("animal_transport")])
    airline_knowledge_acquisition_extra_seat_count = sum(len(item.get("extra_seat") or []) for item in airline_knowledge_acquisition_records)
    airline_knowledge_acquisition_cabin_capability_count = sum(len(item.get("cabin_capabilities") or []) for item in airline_knowledge_acquisition_records)
    airline_knowledge_acquisition_operational_procedure_count = sum(len(item.get("operational_procedures") or []) for item in airline_knowledge_acquisition_records)
    operational_constraint_records = await database.collection("operational_constraints").find_many()
    operational_constraint_count = len(operational_constraint_records)
    operational_constraint_status_counts = {
        status: len([item for item in operational_constraint_records if item.get("constraint_status") == status])
        for status in OPERATIONAL_CONSTRAINT_STATUSES
    }
    operational_constraint_outcome_type_counts = {
        outcome_type: len([item for item in operational_constraint_records if item.get("outcome_type") == outcome_type])
        for outcome_type in OPERATIONAL_CONSTRAINT_OUTCOME_TYPES
    }
    operational_constraint_review_status_counts = {
        status: len([item for item in operational_constraint_records if item.get("review_status") == status])
        for status in OPERATIONAL_CONSTRAINT_REVIEW_STATUSES
    }
    operational_constraint_approval_status_counts = {
        status: len([item for item in operational_constraint_records if item.get("approval_status") == status])
        for status in OPERATIONAL_CONSTRAINT_APPROVAL_STATUSES
    }
    operational_constraint_condition_count = sum(
        len(item.get("conditions") or [])
        + sum(len(group.get("conditions") or []) for group in (item.get("condition_groups") or []) if isinstance(group, dict))
        for item in operational_constraint_records
    )
    operational_constraint_condition_group_count = sum(len(item.get("condition_groups") or []) for item in operational_constraint_records)
    operational_constraint_evidence_link_count = sum(len(item.get("evidence_reference_ids") or []) for item in operational_constraint_records)
    operational_constraint_operational_link_count = sum(
        len(item.get("ssr_osi_workspace_ids") or [])
        + len(item.get("emd_workspace_ids") or [])
        + len(item.get("document_workspace_ids") or [])
        + len(item.get("workflow_ids") or [])
        + len(item.get("timeline_ids") or [])
        for item in operational_constraint_records
    )
    operational_constraint_evaluation_ready_count = len([item for item in operational_constraint_records if item.get("evaluation_ready")])
    airline_knowledge_normalisation_records = await database.collection("airline_knowledge_normalisations").find_many()
    airline_knowledge_normalisation_count = len(airline_knowledge_normalisation_records)
    airline_knowledge_normalisation_status_counts = {
        status: len([item for item in airline_knowledge_normalisation_records if item.get("normalisation_status") == status])
        for status in NORMALISATION_STATUSES
    }
    airline_knowledge_normalisation_type_counts = {
        normalisation_type: len([item for item in airline_knowledge_normalisation_records if item.get("normalisation_type") == normalisation_type])
        for normalisation_type in NORMALISATION_TYPES
    }
    airline_knowledge_normalisation_review_status_counts = {
        status: len([item for item in airline_knowledge_normalisation_records if item.get("review_status") == status])
        for status in NORMALISATION_REVIEW_STATUSES
    }
    airline_knowledge_normalisation_approval_status_counts = {
        status: len([item for item in airline_knowledge_normalisation_records if item.get("approval_status") == status])
        for status in NORMALISATION_APPROVAL_STATUSES
    }
    airline_knowledge_normalisation_hierarchy_count = len(
        [
            item
            for item in airline_knowledge_normalisation_records
            if item.get("hierarchy_path") or item.get("parent_canonical_id")
        ]
    )
    airline_knowledge_normalisation_alias_count = sum(
        len(item.get("aliases") or [])
        + len(item.get("abbreviations") or [])
        + len(item.get("airline_specific_terms") or [])
        + len(item.get("gds_terms") or [])
        + len(item.get("commercial_terms") or [])
        + len(item.get("operational_terms") or [])
        for item in airline_knowledge_normalisation_records
    )
    airline_knowledge_normalisation_applicability_count = sum(
        len(item.get("airline_codes") or [])
        + len(item.get("country_codes") or [])
        + len(item.get("airport_codes") or [])
        + len(item.get("aircraft_types") or [])
        + len(item.get("cabin_codes") or [])
        + len(item.get("service_codes") or [])
        + len(item.get("ssr_codes") or [])
        + len(item.get("rfic_codes") or [])
        + len(item.get("rfisc_codes") or [])
        for item in airline_knowledge_normalisation_records
    )
    airline_knowledge_normalisation_animal_taxonomy_count = len(
        [
            item
            for item in airline_knowledge_normalisation_records
            if item.get("species") or item.get("breed") or item.get("animal_notes")
        ]
    )
    airline_knowledge_normalisation_aircraft_cabin_taxonomy_count = len(
        [
            item
            for item in airline_knowledge_normalisation_records
            if item.get("aircraft_family") or item.get("cabin_family") or item.get("cabin_name")
        ]
    )
    airline_knowledge_normalisation_service_taxonomy_count = len(
        [
            item
            for item in airline_knowledge_normalisation_records
            if item.get("service_domain") or item.get("service_family") or item.get("related_ssr_code")
        ]
    )
    airline_knowledge_normalisation_unit_count = len(
        [
            item
            for item in airline_knowledge_normalisation_records
            if item.get("unit_type") or item.get("canonical_unit")
        ]
    )
    airline_knowledge_normalisation_knowledge_link_count = sum(
        len(item.get("acquisition_ids") or [])
        + len(item.get("constraint_ids") or [])
        + len(item.get("evidence_reference_ids") or [])
        + len(item.get("policy_reference_ids") or [])
        + len(item.get("pricing_reference_ids") or [])
        + len(item.get("capability_reference_ids") or [])
        for item in airline_knowledge_normalisation_records
    )
    airline_knowledge_version_records = await database.collection("airline_knowledge_versions").find_many()
    airline_knowledge_release_records = await database.collection("airline_knowledge_releases").find_many()
    airline_knowledge_version_count = len(airline_knowledge_version_records)
    airline_knowledge_release_count = len(airline_knowledge_release_records)
    airline_knowledge_version_lifecycle_counts = {
        status: len([item for item in airline_knowledge_version_records if item.get("lifecycle_status") == status])
        for status in KNOWLEDGE_LIFECYCLE_STATUSES
    }
    airline_knowledge_version_review_counts = {
        status: len([item for item in airline_knowledge_version_records if item.get("review_status") == status])
        for status in GOVERNANCE_REVIEW_STATUSES
    }
    airline_knowledge_version_approval_counts = {
        status: len([item for item in airline_knowledge_version_records if item.get("approval_status") == status])
        for status in GOVERNANCE_APPROVAL_STATUSES
    }
    airline_knowledge_release_status_counts = {
        status: len([item for item in airline_knowledge_release_records if item.get("release_status") == status])
        for status in GOVERNANCE_RELEASE_STATUSES
    }
    airline_knowledge_version_scope_counts = {
        scope: len([item for item in airline_knowledge_version_records if scope in (item.get("knowledge_scope") or [])])
        for scope in KNOWLEDGE_SCOPES
    }
    airline_knowledge_version_change_type_counts = {
        change_type: len([item for item in airline_knowledge_version_records if item.get("change_type") == change_type])
        for change_type in GOVERNANCE_CHANGE_TYPES
    }
    airline_knowledge_review_queue_count = len(
        [
            item
            for item in airline_knowledge_version_records
            if item.get("lifecycle_status") == "under_review" or item.get("review_status") == "under_review"
        ]
    )
    airline_knowledge_approval_queue_count = len(
        [item for item in airline_knowledge_version_records if item.get("approval_status") == "pending"]
    )
    airline_knowledge_publication_queue_count = len(
        [item for item in airline_knowledge_version_records if item.get("lifecycle_status") == "approved"]
    )
    airline_knowledge_historical_version_count = len(
        [
            item
            for item in airline_knowledge_version_records
            if item.get("lifecycle_status") == "historical_audit" or item.get("historical_lookup_tags")
        ]
    )
    airline_knowledge_superseded_version_count = len(
        [
            item
            for item in airline_knowledge_version_records
            if item.get("lifecycle_status") == "superseded" or item.get("supersedes_version_ids")
        ]
    )
    airline_knowledge_archived_version_count = len(
        [item for item in airline_knowledge_version_records if item.get("lifecycle_status") == "archived"]
    )
    airline_knowledge_comparison_metadata_count = len(
        [
            item
            for item in airline_knowledge_version_records
            if item.get("comparison_base_version_id")
            or item.get("comparison_target_version_id")
            or item.get("added_objects")
            or item.get("modified_objects")
            or item.get("removed_objects")
            or item.get("changed_effective_dates")
            or item.get("changed_pricing")
            or item.get("changed_capability")
            or item.get("changed_operational_constraints")
            or item.get("changed_procedures")
        ]
    )
    airline_knowledge_rollback_metadata_count = len(
        [
            item
            for item in airline_knowledge_version_records
            if item.get("rollback_from_version_id") or item.get("rollback_to_version_id")
        ]
    )
    airline_knowledge_release_evaluation_ready_count = len(
        [item for item in airline_knowledge_release_records if item.get("evaluation_ready")]
    )
    airline_knowledge_release_recommendation_ready_count = len(
        [item for item in airline_knowledge_release_records if item.get("recommendation_ready")]
    )
    airline_capability_matrix_records = await database.collection("airline_capability_matrix").find_many()
    airline_capability_matrix_count = len(airline_capability_matrix_records)
    airline_capability_matrix_status_counts = {
        status: len([item for item in airline_capability_matrix_records if item.get("capability_status") == status])
        for status in MATRIX_CAPABILITY_STATUSES
    }
    airline_capability_matrix_status_value_counts = {
        status: len([item for item in airline_capability_matrix_records if item.get("capability_status_value") == status])
        for status in MATRIX_CAPABILITY_STATUS_VALUES
    }
    airline_capability_matrix_outcome_counts = {
        outcome: len([item for item in airline_capability_matrix_records if item.get("capability_outcome") == outcome])
        for outcome in MATRIX_CAPABILITY_OUTCOMES
    }
    airline_capability_matrix_review_status_counts = {
        status: len([item for item in airline_capability_matrix_records if item.get("capability_review_status") == status])
        for status in MATRIX_REVIEW_STATUSES
    }
    airline_capability_matrix_validity_status_counts = {
        status: len([item for item in airline_capability_matrix_records if item.get("operational_validity_status") == status])
        for status in MATRIX_VALIDITY_STATUSES
    }
    airline_capability_matrix_risk_counts = {
        risk: len([item for item in airline_capability_matrix_records if item.get("operational_risk_level") == risk])
        for risk in MATRIX_RISK_LEVELS
    }
    airline_capability_matrix_confidence_counts = {
        confidence: len([item for item in airline_capability_matrix_records if item.get("capability_confidence") == confidence])
        for confidence in MATRIX_CONFIDENCE_LEVELS
    }
    airline_capability_matrix_airline_count = len(
        {item.get("airline_code") for item in airline_capability_matrix_records if item.get("airline_code")}
    )
    airline_capability_matrix_service_domain_count = len(
        {item.get("service_domain") for item in airline_capability_matrix_records if item.get("service_domain")}
    )
    airline_capability_matrix_governance_link_count = sum(
        len(item.get("knowledge_version_ids") or [])
        + len(item.get("knowledge_release_ids") or [])
        + len(item.get("acquisition_ids") or [])
        + len(item.get("normalisation_ids") or [])
        + len(item.get("constraint_ids") or [])
        + len(item.get("evidence_reference_ids") or [])
        for item in airline_capability_matrix_records
    )
    airline_capability_matrix_aircraft_cabin_count = len(
        [
            item
            for item in airline_capability_matrix_records
            if item.get("aircraft_family") or item.get("aircraft_subtype") or item.get("cabin_family") or item.get("cabin_name")
        ]
    )
    airline_capability_matrix_airport_station_count = len(
        [
            item
            for item in airline_capability_matrix_records
            if item.get("airport_applicability") or item.get("station_applicability")
        ]
    )
    airline_capability_matrix_route_country_season_count = len(
        [
            item
            for item in airline_capability_matrix_records
            if item.get("route_applicability")
            or item.get("origin_country_applicability")
            or item.get("destination_country_applicability")
            or item.get("seasonal_applicability")
        ]
    )
    airline_capability_matrix_animal_transport_count = len(
        [
            item
            for item in airline_capability_matrix_records
            if item.get("animal_transport_applicable") or item.get("petc_capability") or item.get("avih_capability")
        ]
    )
    airline_capability_matrix_extra_seat_count = len(
        [
            item
            for item in airline_capability_matrix_records
            if item.get("extra_seat_applicable") or item.get("extra_seat_available")
        ]
    )
    airline_capability_matrix_medical_accessibility_count = len(
        [
            item
            for item in airline_capability_matrix_records
            if item.get("wheelchair_capability") or item.get("medif_capability") or item.get("oxygen_capability")
        ]
    )
    airline_capability_matrix_manual_review_required_count = len(
        [item for item in airline_capability_matrix_records if item.get("manual_review_required")]
    )
    operational_knowledge_evaluation_records = await database.collection("operational_knowledge_evaluations").find_many()
    operational_knowledge_evaluation_count = len(operational_knowledge_evaluation_records)
    operational_knowledge_evaluation_status_counts = {
        status: len([item for item in operational_knowledge_evaluation_records if item.get("evaluation_status") == status])
        for status in EVALUATION_STATUSES
    }
    operational_knowledge_evaluation_type_counts = {
        evaluation_type: len([item for item in operational_knowledge_evaluation_records if item.get("evaluation_type") == evaluation_type])
        for evaluation_type in EVALUATION_TYPES
    }
    operational_knowledge_evaluation_confidence_counts = {
        confidence: len([item for item in operational_knowledge_evaluation_records if item.get("evaluation_confidence") == confidence])
        for confidence in EVALUATION_CONFIDENCE_LEVELS
    }
    operational_knowledge_evaluation_capability_result_counts = {
        result: len([item for item in operational_knowledge_evaluation_records if item.get("capability_result") == result])
        for result in EVALUATION_RESULT_VALUES
    }
    operational_knowledge_evaluation_policy_result_counts = {
        result: len([item for item in operational_knowledge_evaluation_records if item.get("policy_result") == result])
        for result in EVALUATION_RESULT_VALUES
    }
    operational_knowledge_evaluation_pricing_result_counts = {
        result: len([item for item in operational_knowledge_evaluation_records if item.get("pricing_result") == result])
        for result in EVALUATION_RESULT_VALUES
    }
    operational_knowledge_evaluation_constraint_result_counts = {
        result: len([item for item in operational_knowledge_evaluation_records if item.get("constraint_result") == result])
        for result in EVALUATION_RESULT_VALUES
    }
    operational_knowledge_evaluation_procedure_result_counts = {
        result: len([item for item in operational_knowledge_evaluation_records if item.get("operational_procedure_result") == result])
        for result in EVALUATION_RESULT_VALUES
    }
    operational_knowledge_evaluation_operational_result_counts = {
        result: len([item for item in operational_knowledge_evaluation_records if item.get("operational_result") == result])
        for result in EVALUATION_OPERATIONAL_RESULTS
    }
    operational_knowledge_evaluation_risk_counts = {
        risk: len([item for item in operational_knowledge_evaluation_records if item.get("operational_risk") == risk])
        for risk in EVALUATION_RISK_LEVELS
    }
    operational_knowledge_evaluation_completed_count = len(
        [item for item in operational_knowledge_evaluation_records if item.get("evaluation_completed")]
    )
    operational_knowledge_evaluation_source_reference_count = sum(
        len(item.get("knowledge_version_ids") or [])
        + len(item.get("capability_matrix_ids") or [])
        + len(item.get("operational_constraint_ids") or [])
        + len(item.get("acquisition_ids") or [])
        + len(item.get("evidence_reference_ids") or [])
        for item in operational_knowledge_evaluation_records
    )
    operational_knowledge_evaluation_evidence_trace_count = sum(
        len(item.get("evidence_trace") or []) for item in operational_knowledge_evaluation_records
    )
    operational_knowledge_evaluation_required_action_count = sum(
        len(item.get("required_ssrs") or [])
        + len(item.get("required_osis") or [])
        + len(item.get("required_emds") or [])
        + len(item.get("required_documents") or [])
        + int(bool(item.get("required_medif")))
        + int(bool(item.get("required_manual_review")))
        + int(bool(item.get("required_airline_approval")))
        + int(bool(item.get("required_station_notification")))
        + int(bool(item.get("required_crew_notification")))
        for item in operational_knowledge_evaluation_records
    )
    operational_knowledge_evaluation_feasibility_ready_count = len(
        [item for item in operational_knowledge_evaluation_records if item.get("feasibility_ready")]
    )
    operational_knowledge_evaluation_recommendation_ready_count = len(
        [item for item in operational_knowledge_evaluation_records if item.get("recommendation_ready")]
    )
    passenger_service_feasibility_records = await database.collection("passenger_service_feasibilities").find_many()
    passenger_service_feasibility_count = len(passenger_service_feasibility_records)
    passenger_service_feasibility_status_counts = {
        status: len([item for item in passenger_service_feasibility_records if item.get("feasibility_status") == status])
        for status in FEASIBILITY_STATUSES
    }
    passenger_service_feasibility_type_counts = {
        feasibility_type: len([item for item in passenger_service_feasibility_records if item.get("feasibility_type") == feasibility_type])
        for feasibility_type in FEASIBILITY_TYPES
    }
    passenger_service_feasibility_outcome_counts = {
        outcome: len([item for item in passenger_service_feasibility_records if item.get("feasibility_outcome") == outcome])
        for outcome in FEASIBILITY_OUTCOMES
    }
    passenger_service_feasibility_confidence_counts = {
        confidence: len([item for item in passenger_service_feasibility_records if item.get("feasibility_confidence") == confidence])
        for confidence in FEASIBILITY_CONFIDENCE_LEVELS
    }
    passenger_service_feasibility_risk_counts = {
        risk: len([item for item in passenger_service_feasibility_records if item.get("operational_risk_level") == risk])
        for risk in FEASIBILITY_RISK_LEVELS
    }
    passenger_service_feasibility_operational_evaluation_reference_count = sum(
        len(item.get("operational_evaluation_ids") or []) for item in passenger_service_feasibility_records
    )
    passenger_service_feasibility_evidence_trace_count = sum(
        len(item.get("evidence_trace") or []) for item in passenger_service_feasibility_records
    )
    passenger_service_feasibility_evaluation_trace_count = sum(
        len(item.get("evaluation_trace") or []) for item in passenger_service_feasibility_records
    )
    passenger_service_feasibility_decision_trace_count = sum(
        len(item.get("decision_trace") or []) for item in passenger_service_feasibility_records
    )
    passenger_service_feasibility_required_action_count = sum(
        len(item.get("required_ssrs") or [])
        + len(item.get("required_osis") or [])
        + len(item.get("required_emds") or [])
        + len(item.get("required_documents") or [])
        + len(item.get("required_follow_up_tasks") or [])
        + int(bool(item.get("required_medif")))
        + int(bool(item.get("required_manual_review")))
        + int(bool(item.get("required_airline_approval")))
        + int(bool(item.get("required_station_notification")))
        + int(bool(item.get("required_crew_notification")))
        for item in passenger_service_feasibility_records
    )
    passenger_service_feasibility_recommendation_ready_count = len(
        [item for item in passenger_service_feasibility_records if item.get("recommendation_ready")]
    )
    airline_recommendation_records = await database.collection("airline_recommendations").find_many()
    airline_recommendation_count = len(airline_recommendation_records)
    airline_recommendation_status_counts = {
        status: len([item for item in airline_recommendation_records if item.get("recommendation_status") == status])
        for status in AIRLINE_RECOMMENDATION_STATUSES
    }
    airline_recommendation_level_counts = {
        level: len([item for item in airline_recommendation_records if item.get("recommendation_level") == level])
        for level in AIRLINE_RECOMMENDATION_LEVELS
    }
    airline_recommendation_status_value_counts = {
        value: len([item for item in airline_recommendation_records if item.get("recommendation_status_value") == value])
        for value in RECOMMENDATION_STATUS_VALUES
    }
    airline_recommendation_ready_count = len(
        [item for item in airline_recommendation_records if item.get("recommendation_ready")]
    )
    airline_recommendation_feasibility_reference_count = sum(
        len(item.get("feasibility_ids") or []) for item in airline_recommendation_records
    )
    airline_recommendation_comparison_matrix_count = sum(
        len(item.get("comparison_matrix") or []) for item in airline_recommendation_records
    )
    airline_recommendation_evidence_count = sum(
        len(item.get("recommendation_evidence") or []) for item in airline_recommendation_records
    )
    airline_recommendation_trace_count = sum(
        len(item.get("recommendation_trace") or []) for item in airline_recommendation_records
    )
    airline_recommendation_required_action_count = sum(
        len(item.get("required_ssrs") or [])
        + len(item.get("required_osis") or [])
        + len(item.get("required_emds") or [])
        + len(item.get("required_documents") or [])
        + int(bool(item.get("required_medif")))
        + int(bool(item.get("required_manual_review")))
        + int(bool(item.get("required_station_notification")))
        + int(bool(item.get("required_crew_notification")))
        for item in airline_recommendation_records
    )
    intelligent_offer_builder_package_records = await database.collection("intelligent_offer_builder_packages").find_many()
    intelligent_offer_builder_package_count = len(intelligent_offer_builder_package_records)
    intelligent_offer_builder_package_status_counts = {
        status: len([item for item in intelligent_offer_builder_package_records if item.get("package_status") == status])
        for status in INTELLIGENT_OFFER_PACKAGE_STATUSES
    }
    intelligent_offer_builder_readiness_status_counts = {
        status: len([item for item in intelligent_offer_builder_package_records if item.get("readiness_status") == status])
        for status in INTELLIGENT_OFFER_READINESS_STATUSES
    }
    intelligent_offer_builder_client_visibility_status_counts = {
        status: len([item for item in intelligent_offer_builder_package_records if item.get("client_visibility_status") == status])
        for status in INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES
    }
    intelligent_offer_builder_recommendation_reference_count = sum(
        len(item.get("recommendation_ids") or []) for item in intelligent_offer_builder_package_records
    )
    intelligent_offer_builder_feasibility_reference_count = sum(
        len(item.get("feasibility_ids") or []) for item in intelligent_offer_builder_package_records
    )
    intelligent_offer_builder_evaluation_reference_count = sum(
        len(item.get("operational_evaluation_ids") or []) for item in intelligent_offer_builder_package_records
    )
    intelligent_offer_builder_capability_matrix_reference_count = sum(
        len(item.get("capability_matrix_ids") or []) for item in intelligent_offer_builder_package_records
    )
    intelligent_offer_builder_evidence_reference_count = sum(
        len(item.get("evidence_reference_ids") or []) for item in intelligent_offer_builder_package_records
    )
    intelligent_offer_builder_required_action_count = sum(
        len(item.get("required_ssrs") or [])
        + len(item.get("required_osis") or [])
        + len(item.get("required_emds") or [])
        + len(item.get("required_documents") or [])
        + len(item.get("required_follow_up_tasks") or [])
        + int(bool(item.get("required_medif")))
        + int(bool(item.get("required_manual_review")))
        + int(bool(item.get("required_airline_approval")))
        + int(bool(item.get("required_station_notification")))
        + int(bool(item.get("required_crew_notification")))
        for item in intelligent_offer_builder_package_records
    )
    intelligent_offer_builder_client_explanation_count = len(
        [
            item
            for item in intelligent_offer_builder_package_records
            if item.get("client_explanation_summary")
            or item.get("client_visible_reasons")
            or item.get("client_visible_limitations")
            or item.get("client_visible_conditions")
        ]
    )
    intelligent_offer_builder_internal_trace_count = sum(
        len(item.get("internal_evidence_trace") or []) + len(item.get("internal_decision_trace") or [])
        for item in intelligent_offer_builder_package_records
    )
    intelligent_offer_builder_decision_pack_ready_count = len(
        [item for item in intelligent_offer_builder_package_records if item.get("decision_pack_ready")]
    )
    intelligent_offer_builder_approved_for_client_presentation_count = len(
        [item for item in intelligent_offer_builder_package_records if item.get("approved_for_client_presentation")]
    )
    operational_intelligence_case_records = await database.collection("operational_intelligence_cases").find_many()
    operational_intelligence_case_count = len(operational_intelligence_case_records)
    operational_intelligence_case_status_counts = {
        status: len([item for item in operational_intelligence_case_records if item.get("case_status") == status])
        for status in OPERATIONAL_INTELLIGENCE_CASE_STATUSES
    }
    operational_intelligence_overall_status_counts = {
        status: len([item for item in operational_intelligence_case_records if item.get("overall_case_status") == status])
        for status in OPERATIONAL_INTELLIGENCE_OVERALL_STATUSES
    }
    operational_intelligence_pipeline_ready_counts = {
        field: len([item for item in operational_intelligence_case_records if item.get(field)])
        for field in PIPELINE_READY_FIELDS
    }
    operational_intelligence_pipeline_link_counts = {
        field: sum(len(item.get(field) or []) for item in operational_intelligence_case_records)
        for field in PIPELINE_LINK_FIELDS
    }
    operational_intelligence_ready_for_agent_review_count = len(
        [item for item in operational_intelligence_case_records if item.get("ready_for_agent_review")]
    )
    operational_intelligence_ready_for_offer_builder_count = len(
        [item for item in operational_intelligence_case_records if item.get("ready_for_offer_builder")]
    )
    operational_intelligence_ready_for_client_presentation_count = len(
        [item for item in operational_intelligence_case_records if item.get("ready_for_client_presentation")]
    )
    operational_intelligence_missing_pipeline_item_count = sum(
        len(item.get("missing_pipeline_items") or []) for item in operational_intelligence_case_records
    )
    operational_intelligence_blocking_pipeline_item_count = sum(
        len(item.get("blocking_pipeline_items") or []) for item in operational_intelligence_case_records
    )
    operational_intelligence_trace_entry_count = sum(
        len(item.get("evidence_trace") or [])
        + len(item.get("decision_trace") or [])
        + len(item.get("knowledge_trace") or [])
        + len(item.get("operational_trace") or [])
        for item in operational_intelligence_case_records
    )
    reference_data_domain_records = await database.collection(REFERENCE_DATA_DOMAINS_COLLECTION).find_many()
    reference_data_domain_count = len(reference_data_domain_records)
    reference_data_domain_active_count = len(
        [item for item in reference_data_domain_records if item.get("active", True) and not item.get("archived")]
    )
    reference_data_domain_governance_status_counts = {
        status: len([item for item in reference_data_domain_records if item.get("governance_status") == status])
        for status in REFERENCE_DATA_ENGINE_GOVERNANCE_STATUSES
    }
    reference_data_domain_review_status_counts = {
        status: len([item for item in reference_data_domain_records if item.get("review_status") == status])
        for status in REFERENCE_DATA_ENGINE_REVIEW_STATUSES
    }
    reference_data_engine_record_count = sum(len(item.get("records") or []) for item in reference_data_domain_records)
    reference_data_engine_alias_count = sum(len(item.get("aliases") or []) for item in reference_data_domain_records)
    reference_data_engine_normalization_rule_count = sum(
        len(item.get("normalization_rules") or []) for item in reference_data_domain_records
    )
    reference_data_engine_validation_rule_count = sum(
        len(item.get("validation_rules") or []) for item in reference_data_domain_records
    )
    reference_data_supported_domain_coverage_count = len(
        {
            item.get("domain_code")
            for item in reference_data_domain_records
            if item.get("domain_code") in SUPPORTED_REFERENCE_DOMAIN_CODES
        }
    )
    knowledge_import_template_records = await database.collection(KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION).find_many()
    knowledge_import_template_count = len(knowledge_import_template_records)
    knowledge_import_template_active_count = len([item for item in knowledge_import_template_records if not item.get("archived")])
    knowledge_import_template_type_counts = {
        template_type: len([item for item in knowledge_import_template_records if item.get("template_type") == template_type])
        for template_type in KNOWLEDGE_IMPORT_TEMPLATE_TYPES
    }
    knowledge_import_template_import_scope_counts = {
        import_scope: len([item for item in knowledge_import_template_records if item.get("import_scope") == import_scope])
        for import_scope in KNOWLEDGE_IMPORT_TEMPLATE_IMPORT_SCOPES
    }
    knowledge_import_template_required_column_count = sum(
        len(item.get("required_columns") or []) for item in knowledge_import_template_records
    )
    knowledge_import_template_optional_column_count = sum(
        len(item.get("optional_columns") or []) for item in knowledge_import_template_records
    )
    knowledge_import_template_validation_rule_count = sum(
        len(item.get("validation_rules") or []) for item in knowledge_import_template_records
    )
    knowledge_import_template_mapping_rule_count = sum(
        len(item.get("mapping_rules") or []) for item in knowledge_import_template_records
    )
    knowledge_import_template_sample_row_count = sum(len(item.get("sample_rows") or []) for item in knowledge_import_template_records)
    knowledge_import_template_governance_link_count = sum(
        len(item.get("governance_links") or []) for item in knowledge_import_template_records
    )
    knowledge_import_template_review_required_count = len(
        [item for item in knowledge_import_template_records if item.get("review_required") is True]
    )
    knowledge_import_template_type_coverage_count = len(
        {
            item.get("template_type")
            for item in knowledge_import_template_records
            if item.get("template_type") in KNOWLEDGE_IMPORT_TEMPLATE_TYPES
        }
    )
    visual_policy_editor_card_records = await database.collection(VISUAL_POLICY_EDITOR_CARDS_COLLECTION).find_many()
    visual_policy_editor_card_count = len(visual_policy_editor_card_records)
    visual_policy_editor_active_card_count = len(
        [item for item in visual_policy_editor_card_records if not item.get("archived") and item.get("status") != "archived"]
    )
    visual_policy_editor_status_counts = {
        status: len([item for item in visual_policy_editor_card_records if item.get("status") == status])
        for status in POLICY_CARD_STATUSES
    }
    visual_policy_editor_support_status_counts = {
        status: len([item for item in visual_policy_editor_card_records if item.get("support_status") == status])
        for status in VISUAL_POLICY_SUPPORT_STATUSES
    }
    visual_policy_editor_service_code_count = sum(len(item.get("service_codes") or []) for item in visual_policy_editor_card_records)
    visual_policy_editor_evidence_link_count = sum(len(item.get("evidence_links") or []) for item in visual_policy_editor_card_records)
    visual_policy_editor_governance_link_count = sum(
        len(item.get("knowledge_governance_links") or []) for item in visual_policy_editor_card_records
    )
    visual_policy_editor_taxonomy_link_count = sum(
        len(item.get("service_parameter_taxonomy_links") or []) for item in visual_policy_editor_card_records
    )
    visual_policy_editor_family_coverage_count = len(
        {
            item.get("policy_family")
            for item in visual_policy_editor_card_records
            if item.get("policy_family") in POLICY_FAMILIES
        }
    )
    pricing_formula_builder_records = await database.collection(PRICING_FORMULA_BUILDERS_COLLECTION).find_many()
    pricing_formula_builder_count = len(pricing_formula_builder_records)
    pricing_formula_builder_active_count = len(
        [item for item in pricing_formula_builder_records if not item.get("archived") and item.get("formula_status") != "archived"]
    )
    pricing_formula_builder_status_counts = {
        status: len([item for item in pricing_formula_builder_records if item.get("formula_status") == status])
        for status in PRICING_FORMULA_STATUSES
    }
    pricing_formula_builder_amount_type_counts = {
        amount_type: len([item for item in pricing_formula_builder_records if item.get("amount_type") == amount_type])
        for amount_type in AMOUNT_TYPES
    }
    pricing_formula_builder_category_counts = {
        category: len([item for item in pricing_formula_builder_records if item.get("pricing_category") == category])
        for category in PRICING_CATEGORIES
    }
    pricing_formula_builder_client_visibility_counts = {
        visibility: len([item for item in pricing_formula_builder_records if item.get("client_visibility") == visibility])
        for visibility in PRICING_FORMULA_CLIENT_VISIBILITY_OPTIONS
    }
    pricing_formula_builder_service_code_count = sum(len(item.get("service_codes") or []) for item in pricing_formula_builder_records)
    pricing_formula_builder_component_count = sum(len(item.get("formula_components") or []) for item in pricing_formula_builder_records)
    pricing_formula_builder_multiplier_count = sum(len(item.get("multipliers") or []) for item in pricing_formula_builder_records)
    pricing_formula_builder_refund_exchange_reference_count = sum(
        len(item.get("refund_exchange_condition_references") or []) for item in pricing_formula_builder_records
    )
    pricing_formula_builder_evidence_link_count = sum(len(item.get("evidence_links") or []) for item in pricing_formula_builder_records)
    pricing_formula_builder_governance_link_count = sum(len(item.get("governance_links") or []) for item in pricing_formula_builder_records)
    pricing_formula_builder_taxonomy_link_count = sum(
        len(item.get("service_parameter_taxonomy_links") or []) for item in pricing_formula_builder_records
    )
    pricing_formula_builder_visual_policy_link_count = sum(
        len(item.get("visual_policy_editor_links") or []) for item in pricing_formula_builder_records
    )
    pricing_formula_builder_manual_confirmation_required_count = len(
        [item for item in pricing_formula_builder_records if item.get("manual_confirmation_required") is True]
    )
    pricing_formula_builder_category_coverage_count = len(
        {
            item.get("pricing_category")
            for item in pricing_formula_builder_records
            if item.get("pricing_category") in PRICING_CATEGORIES
        }
    )
    operational_rule_composer_records = await database.collection(OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION).find_many()
    operational_rule_composer_rule_count = len(operational_rule_composer_records)
    operational_rule_composer_active_rule_count = len(
        [item for item in operational_rule_composer_records if not item.get("archived") and item.get("lifecycle_status") != "archived"]
    )
    operational_rule_composer_family_counts = {
        family: len([item for item in operational_rule_composer_records if item.get("rule_family") == family])
        for family in OPERATIONAL_RULE_FAMILIES
    }
    operational_rule_composer_lifecycle_counts = {
        status: len([item for item in operational_rule_composer_records if item.get("lifecycle_status") == status])
        for status in OPERATIONAL_RULE_LIFECYCLE_STATUSES
    }
    operational_rule_composer_severity_counts = {
        severity: len([item for item in operational_rule_composer_records if item.get("severity") == severity])
        for severity in OPERATIONAL_RULE_SEVERITY_LEVELS
    }
    operational_rule_composer_service_code_count = sum(
        len(item.get("service_codes") or []) for item in operational_rule_composer_records
    )
    operational_rule_composer_condition_count = sum(len(item.get("conditions") or []) for item in operational_rule_composer_records)
    operational_rule_composer_any_condition_count = sum(
        len(item.get("any_conditions") or []) for item in operational_rule_composer_records
    )
    operational_rule_composer_evidence_link_count = sum(
        len(item.get("evidence_links") or []) for item in operational_rule_composer_records
    )
    operational_rule_composer_governance_link_count = sum(
        len(item.get("governance_links") or []) for item in operational_rule_composer_records
    )
    operational_rule_composer_parameter_taxonomy_link_count = sum(
        len(item.get("parameter_taxonomy_links") or []) for item in operational_rule_composer_records
    )
    operational_rule_composer_client_message_count = len(
        [item for item in operational_rule_composer_records if item.get("client_message")]
    )
    operational_rule_composer_internal_message_count = len(
        [item for item in operational_rule_composer_records if item.get("internal_message")]
    )
    operational_rule_composer_family_coverage_count = len(
        {
            item.get("rule_family")
            for item in operational_rule_composer_records
            if item.get("rule_family") in OPERATIONAL_RULE_FAMILIES
        }
    )
    knowledge_quality_assurance_records = await database.collection(KNOWLEDGE_QUALITY_ASSURANCE_REVIEWS_COLLECTION).find_many()
    knowledge_quality_assurance_review_count = len(knowledge_quality_assurance_records)
    knowledge_quality_assurance_active_review_count = len(
        [
            item
            for item in knowledge_quality_assurance_records
            if not item.get("archived") and item.get("qa_status") != "archived"
        ]
    )
    knowledge_quality_assurance_status_counts = {
        status: len([item for item in knowledge_quality_assurance_records if item.get("qa_status") == status])
        for status in KNOWLEDGE_QA_STATUSES
    }
    knowledge_quality_assurance_severity_counts = {
        severity: len([item for item in knowledge_quality_assurance_records if item.get("severity") == severity])
        for severity in KNOWLEDGE_QA_SEVERITY_LEVELS
    }
    knowledge_quality_assurance_target_type_counts = {
        target_type: len([item for item in knowledge_quality_assurance_records if item.get("target_type") == target_type])
        for target_type in KNOWLEDGE_QA_TARGET_TYPES
    }
    knowledge_quality_assurance_approval_recommendation_counts = {
        recommendation: len(
            [
                item
                for item in knowledge_quality_assurance_records
                if item.get("approval_recommendation") == recommendation
            ]
        )
        for recommendation in KNOWLEDGE_QA_APPROVAL_RECOMMENDATIONS
    }
    knowledge_quality_assurance_issue_check_counts = {
        check: len(
            [
                item
                for item in knowledge_quality_assurance_records
                if check in [issue.get("check") for issue in (item.get("issues") or []) if isinstance(issue, dict)]
            ]
        )
        for check in KNOWLEDGE_QA_CHECKS
    }
    knowledge_quality_assurance_issue_count = sum(len(item.get("issues") or []) for item in knowledge_quality_assurance_records)
    knowledge_quality_assurance_requested_change_count = sum(
        len(item.get("requested_changes") or []) for item in knowledge_quality_assurance_records
    )
    knowledge_quality_assurance_governance_link_count = sum(
        len(item.get("governance_links") or []) for item in knowledge_quality_assurance_records
    )
    airline_knowledge_publication_records = await database.collection(AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION).find_many()
    airline_knowledge_publication_count = len(airline_knowledge_publication_records)
    airline_knowledge_active_publication_count = len(
        [
            item
            for item in airline_knowledge_publication_records
            if not item.get("archived") and item.get("publication_status") != "archived"
        ]
    )
    airline_knowledge_publication_status_counts = {
        status: len([item for item in airline_knowledge_publication_records if item.get("publication_status") == status])
        for status in AIRLINE_KNOWLEDGE_PUBLICATION_STATUSES
    }
    airline_knowledge_release_channel_counts = {
        channel: len([item for item in airline_knowledge_publication_records if item.get("release_channel") == channel])
        for channel in AIRLINE_KNOWLEDGE_RELEASE_CHANNELS
    }
    airline_knowledge_visibility_counts = {
        status: len(
            [
                item
                for item in airline_knowledge_publication_records
                if isinstance(item.get("agency_visibility"), dict)
                and item.get("agency_visibility", {}).get("visibility_status") == status
            ]
        )
        for status in AIRLINE_KNOWLEDGE_VISIBILITY_STATUSES
    }
    airline_knowledge_publication_aoie_ready_count = len(
        [item for item in airline_knowledge_publication_records if item.get("AOIE_ready") is True]
    )
    airline_knowledge_publication_knowledge_version_count = sum(
        len(item.get("included_knowledge_version_ids") or []) for item in airline_knowledge_publication_records
    )
    airline_knowledge_publication_policy_card_count = sum(
        len(item.get("included_policy_cards") or []) for item in airline_knowledge_publication_records
    )
    airline_knowledge_publication_pricing_formula_count = sum(
        len(item.get("included_pricing_formulas") or []) for item in airline_knowledge_publication_records
    )
    airline_knowledge_publication_rule_count = sum(
        len(item.get("included_rules") or []) for item in airline_knowledge_publication_records
    )
    airline_knowledge_publication_qa_review_count = sum(
        len(item.get("qa_review_ids") or []) for item in airline_knowledge_publication_records
    )
    airline_knowledge_publication_supersession_count = sum(
        len(item.get("supersedes_publication_ids") or []) for item in airline_knowledge_publication_records
    )
    operational_scenario_test_records = await database.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).find_many()
    operational_scenario_test_count = len(operational_scenario_test_records)
    operational_scenario_active_test_count = len(
        [
            item
            for item in operational_scenario_test_records
            if not item.get("archived") and item.get("test_status") != "archived"
        ]
    )
    operational_scenario_family_counts = {
        family: len([item for item in operational_scenario_test_records if item.get("scenario_family") == family])
        for family in OPERATIONAL_SCENARIO_FAMILIES
    }
    operational_scenario_test_status_counts = {
        status: len([item for item in operational_scenario_test_records if item.get("test_status") == status])
        for status in OPERATIONAL_SCENARIO_TEST_STATUSES
    }
    operational_scenario_expected_recommendation_counts = {
        level: len(
            [
                item
                for item in operational_scenario_test_records
                if item.get("expected_recommendation_level") == level
            ]
        )
        for level in OPERATIONAL_SCENARIO_EXPECTED_RECOMMENDATION_LEVELS
    }
    operational_scenario_service_requirement_count = sum(
        len(item.get("service_requirements") or []) for item in operational_scenario_test_records
    )
    operational_scenario_document_count = sum(len(item.get("documents") or []) for item in operational_scenario_test_records)
    operational_scenario_expected_required_action_count = sum(
        len(item.get("expected_required_actions") or []) for item in operational_scenario_test_records
    )
    operational_scenario_evidence_link_count = sum(
        len(item.get("evidence_links") or []) for item in operational_scenario_test_records
    )
    operational_scenario_pet_case_count = len([item for item in operational_scenario_test_records if item.get("pets")])
    operational_scenario_special_item_case_count = len(
        [item for item in operational_scenario_test_records if item.get("special_items")]
    )
    knowledge_population_toolkit_records = await database.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).find_many()
    knowledge_population_toolkit_count = len(knowledge_population_toolkit_records)
    knowledge_population_active_toolkit_count = len(
        [
            item
            for item in knowledge_population_toolkit_records
            if not item.get("archived") and item.get("population_status") != "archived"
        ]
    )
    knowledge_population_status_counts = {
        status: len([item for item in knowledge_population_toolkit_records if item.get("population_status") == status])
        for status in KNOWLEDGE_POPULATION_STATUSES
    }
    knowledge_population_qa_status_counts = {
        status: len([item for item in knowledge_population_toolkit_records if item.get("QA_status") == status])
        for status in KNOWLEDGE_POPULATION_READINESS_STATUSES
    }
    knowledge_population_publishing_status_counts = {
        status: len([item for item in knowledge_population_toolkit_records if item.get("publishing_status") == status])
        for status in KNOWLEDGE_POPULATION_READINESS_STATUSES
    }
    knowledge_population_scenario_status_counts = {
        status: len([item for item in knowledge_population_toolkit_records if item.get("scenario_test_status") == status])
        for status in KNOWLEDGE_POPULATION_READINESS_STATUSES
    }
    knowledge_population_service_family_coverage_count = sum(
        len(item.get("service_family_coverage") or []) for item in knowledge_population_toolkit_records
    )
    knowledge_population_missing_domain_count = sum(
        len(item.get("missing_domains") or []) for item in knowledge_population_toolkit_records
    )
    knowledge_population_blocker_count = sum(len(item.get("blockers") or []) for item in knowledge_population_toolkit_records)
    knowledge_population_warning_count = sum(len(item.get("warnings") or []) for item in knowledge_population_toolkit_records)
    knowledge_population_next_action_count = sum(
        len(item.get("next_actions") or []) for item in knowledge_population_toolkit_records
    )
    pilot_readiness_profile_records = await database.collection(PILOT_READINESS_PROFILES_COLLECTION).find_many()
    pilot_readiness_assessment_records = await database.collection(PILOT_READINESS_ASSESSMENTS_COLLECTION).find_many()
    pilot_readiness_check_records = await database.collection(PILOT_READINESS_CHECKS_COLLECTION).find_many()
    pilot_golden_path_case_records = await database.collection(PILOT_GOLDEN_PATH_CASES_COLLECTION).find_many()
    pilot_golden_path_run_records = await database.collection(PILOT_GOLDEN_PATH_RUNS_COLLECTION).find_many()
    pilot_readiness_issue_records = await database.collection(PILOT_READINESS_ISSUES_COLLECTION).find_many()
    pilot_readiness_assessment_status_counts = {
        status: len([item for item in pilot_readiness_assessment_records if item.get("assessment_status") == status])
        for status in PILOT_READINESS_STATUSES
    }
    pilot_readiness_check_status_counts = {
        status: len([item for item in pilot_readiness_check_records if item.get("status") == status])
        for status in PILOT_READINESS_CHECK_STATUSES
    }
    pilot_readiness_check_family_counts = {
        family: len([item for item in pilot_readiness_check_records if item.get("check_family") == family])
        for family in PILOT_READINESS_CHECK_FAMILIES
    }
    pilot_golden_path_run_status_counts = {
        status: len([item for item in pilot_golden_path_run_records if item.get("run_status") == status])
        for status in PILOT_GOLDEN_PATH_STATUSES
    }
    pilot_readiness_issue_status_counts = {
        status: len([item for item in pilot_readiness_issue_records if item.get("issue_status") == status])
        for status in PILOT_READINESS_ISSUE_STATUSES
    }
    pilot_readiness_open_issue_count = len(
        [item for item in pilot_readiness_issue_records if item.get("issue_status") in {"open", "in_review", "reopened"}]
    )
    pilot_readiness_critical_blocker_count = len(
        [
            item
            for item in pilot_readiness_issue_records
            if item.get("severity") == "critical" and item.get("issue_status") in {"open", "in_review", "reopened"}
        ]
    )
    operational_workflow_definition_records = await database.collection(OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION).find_many()
    operational_workflow_instance_records = await database.collection(OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION).find_many()
    operational_workflow_transition_records = await database.collection(OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION).find_many()
    operational_workflow_guard_records = await database.collection(OPERATIONAL_WORKFLOW_GUARDS_COLLECTION).find_many()
    operational_workflow_event_records = await database.collection(OPERATIONAL_WORKFLOW_EVENTS_COLLECTION).find_many()
    operational_workflow_definition_status_counts = {
        status: len([item for item in operational_workflow_definition_records if item.get("status") == status])
        for status in ["draft", "active", "deprecated", "archived"]
    }
    operational_workflow_instance_status_counts = {
        status: len([item for item in operational_workflow_instance_records if item.get("workflow_status") == status])
        for status in OPERATIONAL_WORKFLOW_STATUSES
    }
    operational_workflow_transition_status_counts = {
        status: len([item for item in operational_workflow_transition_records if item.get("transition_status") == status])
        for status in OPERATIONAL_WORKFLOW_TRANSITION_STATUSES
    }
    operational_workflow_entity_type_counts: dict[str, int] = {}
    operational_workflow_current_state_counts: dict[str, int] = {}
    for item in operational_workflow_instance_records:
        entity_type = item.get("entity_type") or "unset"
        current_state = item.get("current_state") or "unset"
        operational_workflow_entity_type_counts[entity_type] = operational_workflow_entity_type_counts.get(entity_type, 0) + 1
        operational_workflow_current_state_counts[current_state] = operational_workflow_current_state_counts.get(current_state, 0) + 1
    operational_workflow_guard_type_counts = {
        guard_type: len([item for item in operational_workflow_guard_records if item.get("guard_type") == guard_type])
        for guard_type in OPERATIONAL_WORKFLOW_GUARD_TYPES
    }
    operational_workflow_active_blocker_count = sum(
        len(item.get("active_blockers_json") or []) for item in operational_workflow_instance_records
    )
    operational_workflow_active_warning_count = sum(
        len(item.get("active_warnings_json") or []) for item in operational_workflow_instance_records
    )
    operational_work_item_records = await database.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).find_many()
    operational_queue_definition_records = await database.collection(OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION).find_many()
    operational_assignment_event_records = await database.collection(OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION).find_many()
    operational_queue_view_records = await database.collection(OPERATIONAL_QUEUE_VIEWS_COLLECTION).find_many()
    operational_sla_policy_records = await database.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).find_many()
    operational_deadline_records = await database.collection(OPERATIONAL_DEADLINES_COLLECTION).find_many()
    operational_sla_event_records = await database.collection(OPERATIONAL_SLA_EVENTS_COLLECTION).find_many()
    operational_business_calendar_records = await database.collection(OPERATIONAL_BUSINESS_CALENDARS_COLLECTION).find_many()
    operational_task_template_records = await database.collection(OPERATIONAL_TASK_TEMPLATES_COLLECTION).find_many()
    operational_task_dependency_records = await database.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).find_many()
    operational_task_automation_rule_records = await database.collection(OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION).find_many()
    operational_task_automation_run_records = await database.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).find_many()
    request_trip_conversion_plan_records = await database.collection(REQUEST_TRIP_CONVERSION_PLANS_COLLECTION).find_many()
    request_trip_conversion_run_records = await database.collection(REQUEST_TRIP_CONVERSION_RUNS_COLLECTION).find_many()
    request_trip_entity_mapping_records = await database.collection(REQUEST_TRIP_ENTITY_MAPPINGS_COLLECTION).find_many()
    request_trip_conversion_issue_records = await database.collection(REQUEST_TRIP_CONVERSION_ISSUES_COLLECTION).find_many()
    offer_booking_handoff_records = await database.collection(OFFER_BOOKING_HANDOFFS_COLLECTION).find_many()
    offer_booking_handoff_check_records = await database.collection(OFFER_BOOKING_HANDOFF_CHECKS_COLLECTION).find_many()
    offer_booking_handoff_mapping_records = await database.collection(OFFER_BOOKING_HANDOFF_MAPPINGS_COLLECTION).find_many()
    booking_execution_instruction_records = await database.collection(BOOKING_EXECUTION_INSTRUCTIONS_COLLECTION).find_many()
    after_sales_case_records = await database.collection(AFTER_SALES_CASES_COLLECTION).find_many()
    after_sales_case_item_records = await database.collection(AFTER_SALES_CASE_ITEMS_COLLECTION).find_many()
    after_sales_decision_records = await database.collection(AFTER_SALES_DECISIONS_COLLECTION).find_many()
    after_sales_financial_impact_records = await database.collection(AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION).find_many()
    after_sales_resolution_records = await database.collection(AFTER_SALES_RESOLUTIONS_COLLECTION).find_many()
    after_sales_communication_record_records = await database.collection(AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION).find_many()
    operational_work_item_status_counts = {
        status: len([item for item in operational_work_item_records if item.get("status") == status])
        for status in OPERATIONAL_WORK_ITEM_STATUSES
    }
    operational_work_item_priority_counts = {
        priority: len([item for item in operational_work_item_records if item.get("priority") == priority])
        for priority in OPERATIONAL_WORK_ITEM_PRIORITIES
    }
    operational_work_item_severity_counts = {
        severity: len([item for item in operational_work_item_records if item.get("severity") == severity])
        for severity in OPERATIONAL_WORK_ITEM_SEVERITIES
    }
    operational_work_item_type_counts = {
        work_item_type: len([item for item in operational_work_item_records if item.get("work_item_type") == work_item_type])
        for work_item_type in OPERATIONAL_WORK_ITEM_TYPES
    }
    operational_work_item_queue_counts = {
        queue_code: len([item for item in operational_work_item_records if item.get("queue_code") == queue_code])
        for queue_code in OPERATIONAL_QUEUE_CODES
    }
    operational_work_item_sla_counts = {
        sla_status: len([item for item in operational_work_item_records if item.get("sla_status") == sla_status])
        for sla_status in OPERATIONAL_QUEUE_SLA_STATUSES
    }
    operational_work_item_blocker_counts = {
        blocker_status: len([item for item in operational_work_item_records if item.get("blocker_status") == blocker_status])
        for blocker_status in OPERATIONAL_QUEUE_BLOCKER_STATUSES
    }
    operational_assignment_event_type_counts = {
        event_type: len([item for item in operational_assignment_event_records if item.get("event_type") == event_type])
        for event_type in OPERATIONAL_ASSIGNMENT_EVENT_TYPES
    }
    operational_work_item_unassigned_count = len([item for item in operational_work_item_records if not item.get("assigned_user_id")])
    operational_work_item_due_soon_count = len([item for item in operational_work_item_records if item.get("sla_status") == "due_soon"])
    operational_work_item_overdue_count = len([item for item in operational_work_item_records if item.get("sla_status") in {"overdue", "breached"}])
    operational_deadline_status_counts = {
        status: len([item for item in operational_deadline_records if item.get("status") == status])
        for status in OPERATIONAL_DEADLINE_STATUSES
    }
    operational_deadline_breach_counts = {
        breach_state: len([item for item in operational_deadline_records if item.get("breach_state") == breach_state])
        for breach_state in OPERATIONAL_DEADLINE_BREACH_STATES
    }
    operational_deadline_type_counts = {
        deadline_type: len([item for item in operational_deadline_records if item.get("deadline_type") == deadline_type])
        for deadline_type in OPERATIONAL_DEADLINE_TYPES
    }
    operational_sla_policy_status_counts = {
        status: len([item for item in operational_sla_policy_records if item.get("status") == status])
        for status in OPERATIONAL_SLA_POLICY_STATUSES
    }
    operational_sla_event_type_counts = {
        event_type: len([item for item in operational_sla_event_records if item.get("event_type") == event_type])
        for event_type in OPERATIONAL_SLA_EVENT_TYPES
    }
    operational_task_template_status_counts = {
        status: len([item for item in operational_task_template_records if item.get("status") == status])
        for status in TASK_TEMPLATE_STATUSES
    }
    operational_task_dependency_status_counts = {
        status: len([item for item in operational_task_dependency_records if item.get("status") == status])
        for status in TASK_DEPENDENCY_STATUSES
    }
    operational_task_automation_rule_status_counts = {
        status: len([item for item in operational_task_automation_rule_records if item.get("status") == status])
        for status in TASK_AUTOMATION_RULE_STATUSES
    }
    operational_task_automation_run_status_counts = {
        status: len([item for item in operational_task_automation_run_records if item.get("status") == status])
        for status in TASK_AUTOMATION_RUN_STATUSES
    }
    operational_task_automation_trigger_counts = {
        trigger_event: len([item for item in operational_task_automation_run_records if item.get("trigger_event") == trigger_event])
        for trigger_event in TASK_AUTOMATION_TRIGGER_EVENTS
    }
    operational_task_dependency_blocked_count = len([item for item in operational_task_dependency_records if item.get("status") in {"pending", "blocked"}])
    operational_task_dependency_satisfied_count = len([item for item in operational_task_dependency_records if item.get("status") == "satisfied"])
    operational_task_automation_created_task_count = sum(len(item.get("tasks_created") or []) for item in operational_task_automation_run_records)
    operational_task_automation_skipped_task_count = sum(len(item.get("tasks_skipped") or []) for item in operational_task_automation_run_records)
    request_trip_conversion_plan_status_counts = {
        status: len([item for item in request_trip_conversion_plan_records if item.get("plan_status") == status])
        for status in CONVERSION_PLAN_STATUSES
    }
    request_trip_conversion_run_status_counts = {
        status: len([item for item in request_trip_conversion_run_records if item.get("run_status") == status])
        for status in CONVERSION_RUN_STATUSES
    }
    request_trip_conversion_mapping_type_counts = {
        mapping_type: len([item for item in request_trip_entity_mapping_records if item.get("mapping_type") == mapping_type])
        for mapping_type in CONVERSION_MAPPING_TYPES
    }
    request_trip_conversion_issue_type_counts = {
        issue_type: len([item for item in request_trip_conversion_issue_records if item.get("issue_type") == issue_type])
        for issue_type in CONVERSION_ISSUE_TYPES
    }
    request_trip_conversion_warning_count = len([item for item in request_trip_conversion_issue_records if item.get("severity") == "warning"])
    request_trip_conversion_critical_issue_count = len([item for item in request_trip_conversion_issue_records if item.get("severity") == "critical"])
    offer_booking_handoff_status_counts = {
        status: len([item for item in offer_booking_handoff_records if item.get("handoff_status") == status])
        for status in HANDOFF_STATUSES
    }
    offer_booking_handoff_check_status_counts = {
        status: len([item for item in offer_booking_handoff_check_records if item.get("status") == status])
        for status in HANDOFF_CHECK_STATUSES
    }
    offer_booking_handoff_mapping_type_counts = {
        mapping_type: len([item for item in offer_booking_handoff_mapping_records if item.get("mapping_type") == mapping_type])
        for mapping_type in HANDOFF_MAPPING_TYPES
    }
    offer_booking_handoff_booking_mode_counts = {
        booking_mode: len([item for item in offer_booking_handoff_records if item.get("booking_mode") == booking_mode])
        for booking_mode in OFFER_BOOKING_MODES
    }
    booking_execution_instruction_type_counts = {
        instruction_type: len([item for item in booking_execution_instruction_records if item.get("instruction_type") == instruction_type])
        for instruction_type in BOOKING_INSTRUCTION_TYPES
    }
    after_sales_case_status_counts = {
        status: len([item for item in after_sales_case_records if item.get("case_status") == status])
        for status in AFTER_SALES_CASE_STATUSES
    }
    after_sales_case_type_counts = {
        case_type: len([item for item in after_sales_case_records if item.get("case_type") == case_type])
        for case_type in AFTER_SALES_CASE_TYPES
    }
    after_sales_decision_status_counts = {
        status: len([item for item in after_sales_decision_records if item.get("decision_status") == status])
        for status in AFTER_SALES_DECISION_STATUSES
    }
    after_sales_financial_impact_type_counts = {
        impact_type: len([item for item in after_sales_financial_impact_records if item.get("impact_type") == impact_type])
        for impact_type in AFTER_SALES_FINANCIAL_IMPACT_TYPES
    }
    after_sales_resolution_status_counts = {
        status: len([item for item in after_sales_resolution_records if item.get("resolution_status") == status])
        for status in AFTER_SALES_RESOLUTION_STATUSES
    }
    after_sales_communication_type_counts = {
        communication_type: len([item for item in after_sales_communication_record_records if item.get("communication_type") == communication_type])
        for communication_type in AFTER_SALES_COMMUNICATION_TYPES
    }
    operations_command_center_snapshot = await OperationsCommandCenterService(database).platform_dashboard()
    operational_workflow_maturity_snapshot = await OperationalWorkflowMaturityService(database).platform_dashboard()
    airline_master_profile_coverage = await AirlineMasterProfileIntelligenceService(database).coverage()
    airline_evidence_coverage = await AirlinePolicyEvidenceGovernanceService(database).coverage()
    airline_knowledge_versioning_coverage = await AirlineKnowledgeVersioningService(database).coverage()
    airline_service_coverage_gap_coverage = await AirlineServiceCoverageGapService(database).coverage()
    airline_distribution_capability_coverage = await AirlineDistributionCapabilityService(database).coverage()
    interline_codeshare_intelligence_coverage = await InterlineCodeshareIntelligenceService(database).coverage()
    airline_fare_brand_intelligence_coverage = await AirlineFareFamilyBrandIntelligenceService(database).coverage()
    airline_contact_communication_intelligence_coverage = await AirlineContactCommunicationIntelligenceService(database).coverage()
    airline_intelligence_scale_readiness_coverage = await AirlineIntelligenceScaleReadinessService(database).coverage()
    canonical_journey_itinerary_coverage = await CanonicalJourneyItineraryService(database).coverage()
    journey_segment_authoring_coverage = await JourneySegmentAuthoringService(database).summarize_authoring_readiness()
    journey_option_composition_coverage = await JourneyOptionFareBrandCompositionService(database).summarize_readiness()
    journey_comparison_presentation_coverage = await JourneyComparisonClientPresentationService(database).summarize_readiness()
    offer_delivery_coverage = await OfferDeliveryClientInteractionService(database).summarize_readiness()
    operational_deadline_due_soon_count = len([item for item in operational_deadline_records if item.get("status") == "due_soon" or item.get("breach_state") == "due_soon"])
    operational_deadline_overdue_count = len([item for item in operational_deadline_records if item.get("status") == "overdue" or item.get("breach_state") == "breached"])
    operational_deadline_paused_count = len([item for item in operational_deadline_records if item.get("status") == "paused"])
    operational_deadline_completed_count = len([item for item in operational_deadline_records if item.get("status") == "completed"])
    service_parameter_taxonomy_records = await database.collection("service_parameter_taxonomies").find_many()
    service_parameter_taxonomy_count = len(service_parameter_taxonomy_records)
    service_parameter_taxonomy_status_counts = {
        status: len([item for item in service_parameter_taxonomy_records if item.get("taxonomy_status") == status])
        for status in SERVICE_PARAMETER_TAXONOMY_STATUSES
    }
    service_parameter_taxonomy_review_status_counts = {
        status: len([item for item in service_parameter_taxonomy_records if item.get("review_status") == status])
        for status in TAXONOMY_REVIEW_STATUSES
    }
    service_parameter_taxonomy_approval_status_counts = {
        status: len([item for item in service_parameter_taxonomy_records if item.get("approval_status") == status])
        for status in TAXONOMY_APPROVAL_STATUSES
    }
    service_parameter_taxonomy_service_code_count = sum(
        len(item.get("service_codes") or []) for item in service_parameter_taxonomy_records
    )
    service_parameter_taxonomy_passenger_assistance_parameter_count = sum(
        sum(len(item.get(field) or []) for field in PASSENGER_ASSISTANCE_PARAMETER_FIELDS)
        for item in service_parameter_taxonomy_records
    )
    service_parameter_taxonomy_pets_animals_parameter_count = sum(
        sum(len(item.get(field) or []) for field in PETS_ANIMALS_PARAMETER_FIELDS)
        for item in service_parameter_taxonomy_records
    )
    service_parameter_taxonomy_special_item_parameter_count = sum(
        sum(len(item.get(field) or []) for field in SPECIAL_ITEM_PARAMETER_FIELDS)
        for item in service_parameter_taxonomy_records
    )
    service_parameter_taxonomy_route_aircraft_cabin_parameter_count = sum(
        sum(len(item.get(field) or []) for field in ROUTE_AIRCRAFT_CABIN_PARAMETER_FIELDS)
        for item in service_parameter_taxonomy_records
    )
    service_parameter_taxonomy_pricing_parameter_count = sum(
        sum(len(item.get(field) or []) for field in PRICING_PARAMETER_FIELDS)
        for item in service_parameter_taxonomy_records
    )
    service_parameter_taxonomy_reference_requirement_count = sum(
        len(item.get("required_reference_collections") or []) + len(item.get("required_reference_values") or [])
        for item in service_parameter_taxonomy_records
    )
    service_parameter_taxonomy_knowledge_graph_link_count = sum(
        sum(len(item.get(field) or []) for field in TAXONOMY_KNOWLEDGE_GRAPH_LINK_FIELDS)
        for item in service_parameter_taxonomy_records
    )
    request_segment_service_scope_records = await database.collection("request_segment_service_scopes").find_many()
    request_segment_service_scope_count = len(request_segment_service_scope_records)
    request_segment_service_scope_status_counts = {
        status: len([item for item in request_segment_service_scope_records if item.get("scope_status") == status])
        for status in REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES
    }
    request_segment_service_readiness_status_counts = {
        status: len([item for item in request_segment_service_scope_records if item.get("readiness_status") == status])
        for status in REQUEST_SEGMENT_SERVICE_READINESS_STATUSES
    }
    request_segment_service_requested_status_counts = {
        status: len([item for item in request_segment_service_scope_records if item.get("requested_status") == status])
        for status in REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES
    }
    request_segment_service_operational_flag_counts = {
        field: len([item for item in request_segment_service_scope_records if item.get(field)])
        for field in REQUEST_SEGMENT_SERVICE_OPERATIONAL_FLAG_FIELDS
    }
    request_segment_service_knowledge_link_counts = {
        field: sum(len(item.get(field) or []) for item in request_segment_service_scope_records)
        for field in REQUEST_SEGMENT_SERVICE_KNOWLEDGE_LINK_FIELDS
    }
    request_segment_service_pet_scope_count = len(
        [item for item in request_segment_service_scope_records if item.get("pet_reference") or item.get("pet_id")]
    )
    request_segment_service_special_item_scope_count = len(
        [item for item in request_segment_service_scope_records if item.get("special_item_reference") or item.get("special_item_id")]
    )
    request_segment_service_converted_to_trip_count = len(
        [item for item in request_segment_service_scope_records if item.get("converted_to_trip")]
    )
    request_segment_service_missing_field_count = sum(
        len(item.get("missing_fields") or []) for item in request_segment_service_scope_records
    )
    request_segment_service_missing_document_count = sum(
        len(item.get("missing_documents") or []) for item in request_segment_service_scope_records
    )
    request_segment_service_readiness_warning_count = sum(
        len(item.get("readiness_warnings") or []) for item in request_segment_service_scope_records
    )
    request_segment_service_readiness_blocker_count = sum(
        len(item.get("readiness_blockers") or []) for item in request_segment_service_scope_records
    )
    request_segment_service_decision_trace_count = sum(
        len(item.get("decision_trace") or []) for item in request_segment_service_scope_records
    )
    client_master_records = await database.collection("client_master_records").find_many()
    passenger_master_records = await database.collection("passenger_master_records").find_many()
    client_passenger_link_records = await database.collection("client_passenger_links").find_many()
    passenger_service_history_records = await database.collection("passenger_service_history").find_many()
    passenger_operational_preference_records = await database.collection("passenger_operational_preferences").find_many()
    passenger_known_document_records = await database.collection("passenger_known_documents").find_many()
    client_portal_access_profile_records = await database.collection("client_portal_access_profiles").find_many()
    client_master_record_count = len(client_master_records)
    passenger_master_record_count = len(passenger_master_records)
    client_passenger_link_count = len(client_passenger_link_records)
    passenger_service_history_count = len(passenger_service_history_records)
    passenger_operational_preference_count = len(passenger_operational_preference_records)
    passenger_known_document_count = len(passenger_known_document_records)
    client_portal_access_profile_count = len(client_portal_access_profile_records)
    client_master_status_counts = {
        status: len([item for item in client_master_records if item.get("client_status") == status])
        for status in CLIENT_MASTER_STATUSES
    }
    passenger_master_status_counts = {
        status: len([item for item in passenger_master_records if item.get("passenger_status") == status])
        for status in PASSENGER_MASTER_STATUSES
    }
    client_passenger_link_status_counts = {
        status: len([item for item in client_passenger_link_records if item.get("link_status") == status])
        for status in CLIENT_PASSENGER_LINK_STATUSES
    }
    passenger_history_status_counts = {
        status: len([item for item in passenger_service_history_records if item.get("history_status") == status])
        for status in PASSENGER_HISTORY_STATUSES
    }
    passenger_preference_status_counts = {
        status: len([item for item in passenger_operational_preference_records if item.get("preference_status") == status])
        for status in PASSENGER_PREFERENCE_STATUSES
    }
    passenger_document_status_counts = {
        status: len([item for item in passenger_known_document_records if item.get("document_status") == status])
        for status in PASSENGER_DOCUMENT_STATUSES
    }
    client_portal_access_status_counts = {
        status: len([item for item in client_portal_access_profile_records if item.get("portal_status") == status])
        for status in CLIENT_PORTAL_ACCESS_STATUSES
    }
    client_master_linked_passenger_count = sum(len(item.get("linked_passenger_ids") or []) for item in client_master_records)
    passenger_master_reusable_history_count = (
        sum(
            len(item.get("service_history_ids") or [])
            + len(item.get("trip_ids") or [])
            + len(item.get("booking_ids") or [])
            + len(item.get("ticket_ids") or [])
            + len(item.get("emd_ids") or [])
            + len(item.get("operational_evaluation_ids") or [])
            + len(item.get("feasibility_ids") or [])
            + len(item.get("recommendation_ids") or [])
            for item in passenger_master_records
        )
        + passenger_service_history_count
    )
    passenger_master_known_document_count = sum(len(item.get("document_ids") or []) for item in passenger_master_records) + passenger_known_document_count
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
    feature_bundle_rollout_approval_records = await database.collection("feature_bundle_rollout_approvals").find_many()
    feature_bundle_rollout_approval_count = len(feature_bundle_rollout_approval_records)
    feature_bundle_rollout_approval_status_counts = {
        status: len([item for item in feature_bundle_rollout_approval_records if item.get("status") == status])
        for status in APPROVAL_STATUSES
    }
    feature_bundle_rollout_approval_note_count = await database.collection("feature_bundle_rollout_approval_notes").count()
    feature_bundle_rollout_schedule_records = await database.collection("feature_bundle_rollout_schedules").find_many()
    feature_bundle_rollout_schedule_count = len(feature_bundle_rollout_schedule_records)
    feature_bundle_rollout_schedule_status_counts = {
        status: len([item for item in feature_bundle_rollout_schedule_records if item.get("schedule_status") == status])
        for status in SCHEDULE_STATUSES
    }
    feature_bundle_rollout_timeline_records = await database.collection("feature_bundle_rollout_timeline_entries").find_many()
    feature_bundle_rollout_timeline_count = len(feature_bundle_rollout_timeline_records)
    feature_bundle_rollout_timeline_event_type_counts = {
        event_type: len([item for item in feature_bundle_rollout_timeline_records if item.get("event_type") == event_type])
        for event_type in FEATURE_BUNDLE_ROLLOUT_TIMELINE_EVENT_TYPES
    }
    feature_bundle_dependency_records = await database.collection("feature_bundle_dependencies").find_many()
    feature_bundle_dependency_count = len(feature_bundle_dependency_records)
    feature_bundle_dependency_type_counts = {
        dependency_type: len([item for item in feature_bundle_dependency_records if item.get("dependency_type") == dependency_type])
        for dependency_type in DEPENDENCY_TYPES
    }
    feature_bundle_rollout_risk_records = await database.collection("feature_bundle_rollout_risks").find_many()
    feature_bundle_rollout_risk_count = len(feature_bundle_rollout_risk_records)
    feature_bundle_rollout_risk_status_counts = {
        risk_status: len([item for item in feature_bundle_rollout_risk_records if item.get("status") == risk_status])
        for risk_status in RISK_STATUSES
    }
    feature_bundle_rollout_risk_impact_counts = {
        impact: len([item for item in feature_bundle_rollout_risk_records if item.get("impact") == impact])
        for impact in RISK_IMPACTS
    }
    feature_bundle_rollout_risk_likelihood_counts = {
        likelihood: len([item for item in feature_bundle_rollout_risk_records if item.get("likelihood") == likelihood])
        for likelihood in RISK_LIKELIHOODS
    }
    feature_bundle_rollout_issue_records = await database.collection("feature_bundle_rollout_issues").find_many()
    feature_bundle_rollout_issue_count = len(feature_bundle_rollout_issue_records)
    feature_bundle_rollout_issue_status_counts = {
        issue_status: len([item for item in feature_bundle_rollout_issue_records if item.get("status") == issue_status])
        for issue_status in ISSUE_STATUSES
    }
    feature_bundle_rollout_issue_severity_counts = {
        severity: len([item for item in feature_bundle_rollout_issue_records if item.get("severity") == severity])
        for severity in ISSUE_SEVERITIES
    }
    feature_bundle_rollout_decision_records = await database.collection("feature_bundle_rollout_decisions").find_many()
    feature_bundle_rollout_decision_count = len(feature_bundle_rollout_decision_records)
    feature_bundle_rollout_decision_status_counts = {
        decision_status: len([item for item in feature_bundle_rollout_decision_records if item.get("decision_status") == decision_status])
        for decision_status in DECISION_STATUSES
    }
    feature_bundle_rollout_decision_category_counts = {
        category: len([item for item in feature_bundle_rollout_decision_records if item.get("decision_category") == category])
        for category in DECISION_CATEGORIES
    }
    feature_bundle_rollout_change_request_records = await database.collection("feature_bundle_rollout_change_requests").find_many()
    feature_bundle_rollout_change_request_count = len(feature_bundle_rollout_change_request_records)
    feature_bundle_rollout_change_request_status_counts = {
        change_status: len([item for item in feature_bundle_rollout_change_request_records if item.get("change_status") == change_status])
        for change_status in CHANGE_REQUEST_STATUSES
    }
    feature_bundle_rollout_change_request_priority_counts = {
        priority: len([item for item in feature_bundle_rollout_change_request_records if item.get("priority") == priority])
        for priority in CHANGE_REQUEST_PRIORITIES
    }
    feature_bundle_rollout_change_request_impact_counts = {
        impact_level: len([item for item in feature_bundle_rollout_change_request_records if item.get("impact_level") == impact_level])
        for impact_level in CHANGE_REQUEST_IMPACT_LEVELS
    }
    feature_bundle_rollout_change_request_type_counts = {
        change_type: len([item for item in feature_bundle_rollout_change_request_records if item.get("change_type") == change_type])
        for change_type in CHANGE_REQUEST_TYPES
    }
    feature_bundle_rollout_rollback_plan_records = await database.collection("feature_bundle_rollout_rollback_plans").find_many()
    feature_bundle_rollout_rollback_plan_count = len(feature_bundle_rollout_rollback_plan_records)
    feature_bundle_rollout_rollback_plan_status_counts = {
        rollback_status: len([item for item in feature_bundle_rollout_rollback_plan_records if item.get("rollback_status") == rollback_status])
        for rollback_status in ROLLBACK_STATUSES
    }
    feature_bundle_rollout_rollback_plan_priority_counts = {
        priority: len([item for item in feature_bundle_rollout_rollback_plan_records if item.get("rollback_priority") == priority])
        for priority in ROLLBACK_PRIORITIES
    }
    feature_bundle_rollout_rollback_plan_scope_counts = {
        scope: len([item for item in feature_bundle_rollout_rollback_plan_records if item.get("rollback_scope") == scope])
        for scope in ROLLBACK_SCOPES
    }
    feature_bundle_rollout_rollback_plan_trigger_counts = {
        trigger: len([item for item in feature_bundle_rollout_rollback_plan_records if item.get("rollback_trigger") == trigger])
        for trigger in ROLLBACK_TRIGGERS
    }
    feature_bundle_rollout_summary_pack_records = await database.collection("feature_bundle_rollout_summary_packs").find_many()
    feature_bundle_rollout_summary_pack_count = len(feature_bundle_rollout_summary_pack_records)
    feature_bundle_rollout_summary_pack_status_counts = {
        pack_status: len([item for item in feature_bundle_rollout_summary_pack_records if item.get("pack_status") == pack_status])
        for pack_status in PACK_STATUSES
    }
    feature_bundle_rollout_summary_pack_audience_counts = {
        audience: len([item for item in feature_bundle_rollout_summary_pack_records if item.get("generated_for_audience") == audience])
        for audience in PACK_AUDIENCES
    }
    operational_travel_workspace_records = await database.collection("operational_travel_workspaces").find_many()
    operational_travel_workspace_count = len(operational_travel_workspace_records)
    operational_travel_workspace_status_counts = {
        workspace_status: len([item for item in operational_travel_workspace_records if item.get("workspace_status") == workspace_status])
        for workspace_status in WORKSPACE_STATUSES
    }
    operational_travel_workspace_type_counts = {
        workspace_type: len([item for item in operational_travel_workspace_records if item.get("workspace_type") == workspace_type])
        for workspace_type in WORKSPACE_TYPES
    }
    operational_travel_workspace_priority_counts = {
        priority: len([item for item in operational_travel_workspace_records if item.get("priority") == priority])
        for priority in WORKSPACE_PRIORITIES
    }
    travel_request_workspace_records = await database.collection("travel_request_workspaces").find_many()
    travel_request_workspace_count = len(travel_request_workspace_records)
    travel_request_workspace_status_counts = {
        request_status: len([item for item in travel_request_workspace_records if item.get("request_status") == request_status])
        for request_status in REQUEST_STATUSES
    }
    travel_request_workspace_type_counts = {
        request_type: len([item for item in travel_request_workspace_records if item.get("request_type") == request_type])
        for request_type in REQUEST_TYPES
    }
    travel_request_workspace_priority_counts = {
        priority: len([item for item in travel_request_workspace_records if item.get("request_priority") == priority])
        for priority in REQUEST_PRIORITIES
    }
    passenger_workspace_records = await database.collection("passenger_workspaces").find_many()
    passenger_workspace_count = len(passenger_workspace_records)
    passenger_workspace_status_counts = {
        passenger_status: len([item for item in passenger_workspace_records if item.get("passenger_status") == passenger_status])
        for passenger_status in PASSENGER_STATUSES
    }
    passenger_workspace_nationality_count = len({item.get("nationality") for item in passenger_workspace_records if item.get("nationality")})
    passenger_workspace_citizenship_count = len({item.get("citizenship") for item in passenger_workspace_records if item.get("citizenship")})
    flight_workspace_records = await database.collection("flight_workspaces").find_many()
    flight_workspace_count = len(flight_workspace_records)
    flight_workspace_status_counts = {
        flight_status: len([item for item in flight_workspace_records if item.get("flight_status") == flight_status])
        for flight_status in FLIGHT_STATUSES
    }
    flight_workspace_airline_count = len({item.get("airline_code") for item in flight_workspace_records if item.get("airline_code")})
    flight_workspace_departure_airport_count = len({item.get("departure_airport") for item in flight_workspace_records if item.get("departure_airport")})
    flight_workspace_arrival_airport_count = len({item.get("arrival_airport") for item in flight_workspace_records if item.get("arrival_airport")})
    flight_workspace_cabin_count = len({item.get("cabin_class") for item in flight_workspace_records if item.get("cabin_class")})
    trip_workspace_records = await database.collection("trip_workspaces").find_many()
    trip_workspace_count = len(trip_workspace_records)
    trip_workspace_status_counts = {
        trip_status: len([item for item in trip_workspace_records if item.get("trip_status") == trip_status])
        for trip_status in TRIP_STATUSES
    }
    trip_workspace_departure_country_count = len({item.get("departure_country") for item in trip_workspace_records if item.get("departure_country")})
    trip_workspace_destination_country_count = len({item.get("destination_country") for item in trip_workspace_records if item.get("destination_country")})
    trip_workspace_priority_count = len({item.get("operational_priority") for item in trip_workspace_records if item.get("operational_priority")})
    offer_workspace_records = await database.collection("offer_workspaces_v2").find_many()
    offer_workspace_v2_count = len(offer_workspace_records)
    offer_workspace_status_counts = {
        offer_status: len([item for item in offer_workspace_records if item.get("offer_status") == offer_status])
        for offer_status in OFFER_STATUSES
    }
    offer_workspace_type_count = len({item.get("offer_type") for item in offer_workspace_records if item.get("offer_type")})
    offer_workspace_currency_count = len({item.get("currency") for item in offer_workspace_records if item.get("currency")})
    offer_workspace_destination_count = len({item.get("destination_summary") for item in offer_workspace_records if item.get("destination_summary")})
    offer_workspace_assigned_agent_count = len({item.get("assigned_agent") for item in offer_workspace_records if item.get("assigned_agent")})
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
        "phase": CURRENT_BUILD_PHASE,
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
            "offer_workspace_count": offer_builder_workspace_count,
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
        "airline_operational_intelligence_engine_architecture_foundation": {
            "airline_operational_intelligence_engine_enabled": True,
            "aoie_architecture_foundation_enabled": True,
            "passenger_service_operations_principle_enabled": True,
            "architecture_record_seeded": bool(airline_operational_intelligence_architecture_record),
            "architecture_collection_registered": True,
            "platform_airline_operational_intelligence_ui_enabled": True,
            "agency_operational_intelligence_ui_enabled": True,
            "platform_airline_operational_intelligence_api_enabled": True,
            "agency_airline_operational_intelligence_api_enabled": True,
            "metadata_only": True,
            "architecture_only": True,
            "read_only_visualization_enabled": True,
            "coordinates_existing_foundations": True,
            "duplicates_existing_foundations": False,
            "chapter_50_intelligence_track_enabled": True,
            "chapter_41_operational_workspaces_preserved": True,
            "feeds_chapter_41_42_operational_workspaces": True,
            "next_intelligence_phase": "Phase 50.4 - Airline Knowledge Version Review Foundation",
            "next_operational_phase": "Phase 42.2 - Passenger Service Workflow Engine Foundation",
            "ai_generation_disabled": True,
            "ai_execution_disabled": True,
            "airline_scraping_disabled": True,
            "automatic_web_crawling_disabled": True,
            "live_airline_apis_disabled": True,
            "provider_integrations_disabled": True,
            "pricing_engine_execution_disabled": True,
            "itinerary_search_disabled": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "emd_issuance_disabled": True,
            "recommendation_automation_disabled": True,
            "background_workers_disabled": True,
            "automation_disabled": True,
            "external_api_calls_disabled": True,
            "architecture_record_count": airline_operational_intelligence_architecture_count,
            "linked_existing_foundation_count": len(airline_operational_intelligence_architecture_record.get("linked_existing_foundations") or []),
            "future_aoie_phase_count": len(airline_operational_intelligence_architecture_record.get("linked_future_phases") or []),
            "excluded_scope_count": len(airline_operational_intelligence_architecture_record.get("excluded_scope") or []),
            "readiness_required": False,
            "diagnostic": "Phase 50.0 defines AOIE as an architecture and governance layer only. It coordinates existing airline policy, data pack, knowledge version, agency consumption, taxonomy, service mechanics, pricing, comparison, offer advisor, passenger, booking, offer, ticket, EMD, and future SSR/OSI workspace foundations without AI generation, scraping, crawling, live airline APIs, provider integrations, pricing engine execution, itinerary search, booking execution, ticket issuance, EMD issuance, recommendation automation, background workers, or external API calls.",
        },
        "airline_knowledge_acquisition_workspace_foundation": {
            "airline_knowledge_acquisition_enabled": True,
            "airline_knowledge_acquisition_workspace_enabled": True,
            "manual_source_evidence_intake_enabled": True,
            "source_evidence_metadata_enabled": True,
            "airline_operational_knowledge_graph_foundation_enabled": True,
            "operational_knowledge_graph_pillars_enabled": True,
            "policy_metadata_pillar_enabled": True,
            "pricing_metadata_pillar_enabled": True,
            "capability_metadata_pillar_enabled": True,
            "operational_constraints_metadata_pillar_enabled": True,
            "animal_transport_knowledge_metadata_enabled": True,
            "extra_seat_knowledge_metadata_enabled": True,
            "cabin_capability_knowledge_metadata_enabled": True,
            "policy_pricing_capability_constraints_separated": True,
            "platform_airline_knowledge_acquisition_metadata_crud_enabled": True,
            "agency_airline_knowledge_acquisition_read_only_enabled": True,
            "platform_airline_knowledge_acquisition_ui_enabled": True,
            "agency_knowledge_acquisition_ui_enabled": True,
            "filter_by_airline_enabled": True,
            "filter_by_service_domain_enabled": True,
            "filter_by_service_family_enabled": True,
            "filter_by_ssr_code_enabled": True,
            "filter_by_rfic_enabled": True,
            "filter_by_rfisc_enabled": True,
            "filter_by_source_type_enabled": True,
            "filter_by_review_status_enabled": True,
            "filter_by_approval_status_enabled": True,
            "filter_by_effective_date_enabled": True,
            "filter_by_official_source_flag_enabled": True,
            "review_metadata_enabled": True,
            "approval_metadata_enabled": True,
            "versioning_metadata_enabled": True,
            "future_aoie_link_metadata_enabled": True,
            "operational_link_metadata_enabled": True,
            "feeds_policy_text_parser_metadata": True,
            "feeds_service_rule_normalisation_metadata": True,
            "feeds_knowledge_version_review_metadata": True,
            "feeds_capability_matrix_metadata": True,
            "feeds_passenger_service_feasibility_metadata": True,
            "feeds_airline_itinerary_recommendation_metadata": True,
            "feeds_total_journey_cost_comparison_metadata": True,
            "metadata_only": True,
            "evidence_intake_only": True,
            "ai_parsing_disabled": True,
            "automatic_extraction_disabled": True,
            "web_scraping_disabled": True,
            "web_crawling_disabled": True,
            "airline_website_automation_disabled": True,
            "provider_integrations_disabled": True,
            "live_airline_apis_disabled": True,
            "recommendation_engine_disabled": True,
            "feasibility_engine_disabled": True,
            "pricing_calculation_engine_disabled": True,
            "background_workers_disabled": True,
            "parser_execution_disabled": True,
            "automation_disabled": True,
            "airline_knowledge_acquisition_count": airline_knowledge_acquisition_count,
            "airline_knowledge_acquisition_status_counts": airline_knowledge_acquisition_status_counts,
            "airline_knowledge_acquisition_source_type_counts": airline_knowledge_acquisition_source_type_counts,
            "airline_knowledge_acquisition_review_status_counts": airline_knowledge_acquisition_review_status_counts,
            "airline_knowledge_acquisition_approval_status_counts": airline_knowledge_acquisition_approval_status_counts,
            "airline_knowledge_acquisition_official_source_count": airline_knowledge_acquisition_official_source_count,
            "airline_knowledge_acquisition_raw_source_text_count": airline_knowledge_acquisition_raw_source_text_count,
            "airline_knowledge_acquisition_service_domain_count": airline_knowledge_acquisition_service_domain_count,
            "airline_knowledge_acquisition_service_family_count": airline_knowledge_acquisition_service_family_count,
            "airline_knowledge_acquisition_ssr_code_count": airline_knowledge_acquisition_ssr_code_count,
            "airline_knowledge_acquisition_rfic_rfisc_count": airline_knowledge_acquisition_rfic_rfisc_count,
            "airline_knowledge_acquisition_version_link_count": airline_knowledge_acquisition_version_link_count,
            "airline_knowledge_acquisition_future_aoie_link_count": airline_knowledge_acquisition_future_aoie_link_count,
            "airline_knowledge_acquisition_operational_link_count": airline_knowledge_acquisition_operational_link_count,
            "airline_knowledge_graph_pillars": KNOWLEDGE_GRAPH_PILLARS,
            "airline_knowledge_acquisition_policy_count": airline_knowledge_acquisition_policy_count,
            "airline_knowledge_acquisition_pricing_count": airline_knowledge_acquisition_pricing_count,
            "airline_knowledge_acquisition_capability_count": airline_knowledge_acquisition_capability_count,
            "airline_knowledge_acquisition_operational_constraint_count": airline_knowledge_acquisition_operational_constraint_count,
            "airline_knowledge_acquisition_animal_transport_count": airline_knowledge_acquisition_animal_transport_count,
            "airline_knowledge_acquisition_extra_seat_count": airline_knowledge_acquisition_extra_seat_count,
            "airline_knowledge_acquisition_cabin_capability_count": airline_knowledge_acquisition_cabin_capability_count,
            "airline_knowledge_acquisition_operational_procedure_count": airline_knowledge_acquisition_operational_procedure_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.1 stores Airline Operational Knowledge Graph metadata across evidence, policy, pricing, capability, and operational constraints/procedures. It does not parse with AI, automatically extract, scrape, crawl, automate airline websites, call providers or live airline APIs, recommend, decide feasibility, calculate pricing, or run background workers.",
        },
        "operational_constraint_engine_foundation": {
            "operational_constraint_engine_enabled": True,
            "operational_constraints_collection_enabled": True,
            "constraint_language_foundation_enabled": True,
            "condition_groups_metadata_enabled": True,
            "conditions_metadata_enabled": True,
            "supported_condition_operators": CONDITION_OPERATORS,
            "outcome_metadata_enabled": True,
            "applicability_metadata_enabled": True,
            "priority_precedence_metadata_enabled": True,
            "governance_metadata_enabled": True,
            "future_evaluation_metadata_enabled": True,
            "operational_links_metadata_enabled": True,
            "platform_operational_constraints_metadata_crud_enabled": True,
            "agency_operational_constraints_read_only_enabled": True,
            "platform_operational_constraints_ui_enabled": True,
            "agency_operational_constraints_ui_enabled": True,
            "filter_by_agency_enabled": True,
            "filter_by_acquisition_enabled": True,
            "filter_by_airline_enabled": True,
            "filter_by_service_domain_enabled": True,
            "filter_by_service_family_enabled": True,
            "filter_by_ssr_code_enabled": True,
            "filter_by_rfic_enabled": True,
            "filter_by_rfisc_enabled": True,
            "filter_by_constraint_status_enabled": True,
            "filter_by_outcome_type_enabled": True,
            "filter_by_review_status_enabled": True,
            "filter_by_approval_status_enabled": True,
            "filter_by_evaluation_ready_enabled": True,
            "metadata_only": True,
            "live_rule_execution_disabled": True,
            "ai_reasoning_disabled": True,
            "recommendation_engine_disabled": True,
            "feasibility_scoring_disabled": True,
            "pricing_calculation_disabled": True,
            "parser_execution_disabled": True,
            "scraping_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "evaluation_endpoint_disabled": True,
            "operational_constraint_count": operational_constraint_count,
            "operational_constraint_status_counts": operational_constraint_status_counts,
            "operational_constraint_outcome_type_counts": operational_constraint_outcome_type_counts,
            "operational_constraint_review_status_counts": operational_constraint_review_status_counts,
            "operational_constraint_approval_status_counts": operational_constraint_approval_status_counts,
            "operational_constraint_condition_count": operational_constraint_condition_count,
            "operational_constraint_condition_group_count": operational_constraint_condition_group_count,
            "operational_constraint_evidence_link_count": operational_constraint_evidence_link_count,
            "operational_constraint_operational_link_count": operational_constraint_operational_link_count,
            "operational_constraint_evaluation_ready_count": operational_constraint_evaluation_ready_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.2 defines the formal AOIE operational constraint language as metadata only. It stores condition groups, supported operators, outcomes, applicability, priority, governance, future evaluation notes, and operational links without live rule execution, AI reasoning, recommendations, feasibility scoring, pricing calculation, parser execution, scraping, background workers, provider integrations, or evaluation endpoints.",
        },
        "airline_knowledge_normalisation_foundation": {
            "airline_knowledge_normalisation_enabled": True,
            "airline_knowledge_normalisations_collection_enabled": True,
            "canonical_operational_vocabulary_enabled": True,
            "taxonomy_hierarchy_metadata_enabled": True,
            "aliases_terms_metadata_enabled": True,
            "applicability_metadata_enabled": True,
            "animal_taxonomy_metadata_enabled": True,
            "aircraft_cabin_taxonomy_metadata_enabled": True,
            "service_taxonomy_metadata_enabled": True,
            "unit_normalisation_metadata_enabled": True,
            "knowledge_links_metadata_enabled": True,
            "governance_metadata_enabled": True,
            "platform_airline_knowledge_normalisation_metadata_crud_enabled": True,
            "agency_airline_knowledge_normalisation_read_only_enabled": True,
            "platform_airline_knowledge_normalisation_ui_enabled": True,
            "agency_knowledge_normalisation_ui_enabled": True,
            "filter_by_agency_enabled": True,
            "filter_by_normalisation_status_enabled": True,
            "filter_by_normalisation_type_enabled": True,
            "filter_by_canonical_code_enabled": True,
            "filter_by_taxonomy_enabled": True,
            "filter_by_airline_enabled": True,
            "filter_by_ssr_code_enabled": True,
            "filter_by_rfic_enabled": True,
            "filter_by_rfisc_enabled": True,
            "filter_by_review_status_enabled": True,
            "filter_by_approval_status_enabled": True,
            "normalisation_statuses": NORMALISATION_STATUSES,
            "normalisation_types": NORMALISATION_TYPES,
            "metadata_only": True,
            "live_evaluation_disabled": True,
            "ai_parsing_disabled": True,
            "recommendation_engine_disabled": True,
            "feasibility_scoring_disabled": True,
            "pricing_calculation_disabled": True,
            "scraping_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "airline_knowledge_normalisation_count": airline_knowledge_normalisation_count,
            "airline_knowledge_normalisation_status_counts": airline_knowledge_normalisation_status_counts,
            "airline_knowledge_normalisation_type_counts": airline_knowledge_normalisation_type_counts,
            "airline_knowledge_normalisation_review_status_counts": airline_knowledge_normalisation_review_status_counts,
            "airline_knowledge_normalisation_approval_status_counts": airline_knowledge_normalisation_approval_status_counts,
            "airline_knowledge_normalisation_hierarchy_count": airline_knowledge_normalisation_hierarchy_count,
            "airline_knowledge_normalisation_alias_count": airline_knowledge_normalisation_alias_count,
            "airline_knowledge_normalisation_applicability_count": airline_knowledge_normalisation_applicability_count,
            "airline_knowledge_normalisation_animal_taxonomy_count": airline_knowledge_normalisation_animal_taxonomy_count,
            "airline_knowledge_normalisation_aircraft_cabin_taxonomy_count": airline_knowledge_normalisation_aircraft_cabin_taxonomy_count,
            "airline_knowledge_normalisation_service_taxonomy_count": airline_knowledge_normalisation_service_taxonomy_count,
            "airline_knowledge_normalisation_unit_count": airline_knowledge_normalisation_unit_count,
            "airline_knowledge_normalisation_knowledge_link_count": airline_knowledge_normalisation_knowledge_link_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.3 creates the metadata-only normalisation layer for the Airline Operational Knowledge Graph. It maps messy operational terms into canonical vocabulary and taxonomy metadata so future AOIE phases can compare airlines consistently without live evaluation, AI parsing, recommendations, feasibility scoring, pricing calculation, scraping, background workers, or provider integrations.",
        },
        "airline_operational_knowledge_governance_foundation": {
            "airline_operational_knowledge_governance_enabled": True,
            "airline_knowledge_versions_collection_enabled": True,
            "airline_knowledge_releases_collection_enabled": True,
            "knowledge_lifecycle_metadata_enabled": True,
            "independent_knowledge_versioning_enabled": True,
            "evidence_versioning_enabled": True,
            "policy_versioning_enabled": True,
            "pricing_versioning_enabled": True,
            "capability_versioning_enabled": True,
            "operational_constraint_versioning_enabled": True,
            "operational_procedure_versioning_enabled": True,
            "knowledge_release_metadata_enabled": True,
            "version_comparison_metadata_enabled": True,
            "rollback_metadata_enabled": True,
            "superseded_metadata_enabled": True,
            "historical_lookup_metadata_enabled": True,
            "review_queue_metadata_enabled": True,
            "approval_queue_metadata_enabled": True,
            "publication_queue_metadata_enabled": True,
            "platform_airline_knowledge_governance_metadata_crud_enabled": True,
            "agency_airline_knowledge_governance_read_only_enabled": True,
            "platform_airline_knowledge_governance_ui_enabled": True,
            "agency_knowledge_governance_ui_enabled": True,
            "knowledge_lifecycle_statuses": KNOWLEDGE_LIFECYCLE_STATUSES,
            "knowledge_release_statuses": GOVERNANCE_RELEASE_STATUSES,
            "knowledge_review_statuses": GOVERNANCE_REVIEW_STATUSES,
            "knowledge_approval_statuses": GOVERNANCE_APPROVAL_STATUSES,
            "knowledge_scopes": KNOWLEDGE_SCOPES,
            "knowledge_change_types": GOVERNANCE_CHANGE_TYPES,
            "metadata_only": True,
            "live_rule_evaluation_disabled": True,
            "ai_reasoning_disabled": True,
            "parser_execution_disabled": True,
            "recommendation_engine_disabled": True,
            "pricing_calculation_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "automatic_publication_disabled": True,
            "airline_knowledge_version_count": airline_knowledge_version_count,
            "airline_knowledge_release_count": airline_knowledge_release_count,
            "airline_knowledge_version_lifecycle_counts": airline_knowledge_version_lifecycle_counts,
            "airline_knowledge_version_review_counts": airline_knowledge_version_review_counts,
            "airline_knowledge_version_approval_counts": airline_knowledge_version_approval_counts,
            "airline_knowledge_release_status_counts": airline_knowledge_release_status_counts,
            "airline_knowledge_version_scope_counts": airline_knowledge_version_scope_counts,
            "airline_knowledge_version_change_type_counts": airline_knowledge_version_change_type_counts,
            "airline_knowledge_review_queue_count": airline_knowledge_review_queue_count,
            "airline_knowledge_approval_queue_count": airline_knowledge_approval_queue_count,
            "airline_knowledge_publication_queue_count": airline_knowledge_publication_queue_count,
            "airline_knowledge_historical_version_count": airline_knowledge_historical_version_count,
            "airline_knowledge_superseded_version_count": airline_knowledge_superseded_version_count,
            "airline_knowledge_archived_version_count": airline_knowledge_archived_version_count,
            "airline_knowledge_comparison_metadata_count": airline_knowledge_comparison_metadata_count,
            "airline_knowledge_rollback_metadata_count": airline_knowledge_rollback_metadata_count,
            "airline_knowledge_release_evaluation_ready_count": airline_knowledge_release_evaluation_ready_count,
            "airline_knowledge_release_recommendation_ready_count": airline_knowledge_release_recommendation_ready_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.4 creates metadata-only governance and version-control records for Airline Operational Knowledge. It governs independent Evidence, Policy, Pricing, Capability, Operational Constraint, and Operational Procedure versions plus grouped releases, comparison metadata, rollback metadata, superseded records, and historical lookup metadata without live rule evaluation, AI reasoning, parser execution, recommendations, pricing calculation, provider integrations, background workers, or automatic publication.",
        },
        "airline_operational_capability_matrix_foundation": {
            "airline_operational_capability_matrix_enabled": True,
            "airline_capability_matrix_collection_enabled": True,
            "platform_airline_capability_matrix_metadata_crud_enabled": True,
            "agency_airline_capability_matrix_read_only_enabled": True,
            "platform_airline_capability_matrix_ui_enabled": True,
            "agency_capability_matrix_ui_enabled": True,
            "capability_is_distinct_from_policy": True,
            "knowledge_governance_links_enabled": True,
            "airline_service_capability_metadata_enabled": True,
            "aircraft_cabin_capability_metadata_enabled": True,
            "airport_station_capability_metadata_enabled": True,
            "route_country_season_capability_metadata_enabled": True,
            "interline_codeshare_capability_metadata_enabled": True,
            "animal_transport_capability_metadata_enabled": True,
            "extra_seat_capability_metadata_enabled": True,
            "medical_accessibility_capability_metadata_enabled": True,
            "operational_requirements_metadata_enabled": True,
            "risk_confidence_metadata_enabled": True,
            "lifecycle_metadata_enabled": True,
            "future_50_6_rule_evaluation_consumer_only": True,
            "future_50_7_feasibility_consumer_only": True,
            "capability_statuses": MATRIX_CAPABILITY_STATUSES,
            "capability_status_values": MATRIX_CAPABILITY_STATUS_VALUES,
            "capability_outcomes": MATRIX_CAPABILITY_OUTCOMES,
            "capability_review_statuses": MATRIX_REVIEW_STATUSES,
            "operational_validity_statuses": MATRIX_VALIDITY_STATUSES,
            "confidence_levels": MATRIX_CONFIDENCE_LEVELS,
            "operational_risk_levels": MATRIX_RISK_LEVELS,
            "metadata_only": True,
            "live_rule_evaluation_disabled": True,
            "passenger_feasibility_scoring_disabled": True,
            "airline_recommendation_ranking_disabled": True,
            "ai_reasoning_disabled": True,
            "parser_execution_disabled": True,
            "pricing_calculation_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "automatic_publication_disabled": True,
            "scraping_disabled": True,
            "airline_capability_matrix_count": airline_capability_matrix_count,
            "airline_capability_matrix_status_counts": airline_capability_matrix_status_counts,
            "airline_capability_matrix_status_value_counts": airline_capability_matrix_status_value_counts,
            "airline_capability_matrix_outcome_counts": airline_capability_matrix_outcome_counts,
            "airline_capability_matrix_review_status_counts": airline_capability_matrix_review_status_counts,
            "airline_capability_matrix_validity_status_counts": airline_capability_matrix_validity_status_counts,
            "airline_capability_matrix_risk_counts": airline_capability_matrix_risk_counts,
            "airline_capability_matrix_confidence_counts": airline_capability_matrix_confidence_counts,
            "airline_capability_matrix_airline_count": airline_capability_matrix_airline_count,
            "airline_capability_matrix_service_domain_count": airline_capability_matrix_service_domain_count,
            "airline_capability_matrix_governance_link_count": airline_capability_matrix_governance_link_count,
            "airline_capability_matrix_aircraft_cabin_count": airline_capability_matrix_aircraft_cabin_count,
            "airline_capability_matrix_airport_station_count": airline_capability_matrix_airport_station_count,
            "airline_capability_matrix_route_country_season_count": airline_capability_matrix_route_country_season_count,
            "airline_capability_matrix_animal_transport_count": airline_capability_matrix_animal_transport_count,
            "airline_capability_matrix_extra_seat_count": airline_capability_matrix_extra_seat_count,
            "airline_capability_matrix_medical_accessibility_count": airline_capability_matrix_medical_accessibility_count,
            "airline_capability_matrix_manual_review_required_count": airline_capability_matrix_manual_review_required_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.5 creates the metadata-only Airline Operational Capability Matrix. It records what airlines can operationally deliver by airline, service, aircraft, cabin, airport, route, country, season, interline/codeshare context, operational restriction, confidence, evidence, and governance references. It does not evaluate passenger cases, score feasibility, rank or recommend airlines, reason with AI, execute parsers, calculate pricing, call providers, run workers, scrape, or automatically publish. Phase 50.6 consumes the matrix for operational knowledge evaluation metadata, and future Phase 50.7 consumes evaluation outputs for passenger service feasibility.",
        },
        "operational_knowledge_evaluation_engine_foundation": {
            "operational_knowledge_evaluation_engine_enabled": True,
            "operational_knowledge_evaluations_collection_enabled": True,
            "platform_operational_evaluations_metadata_crud_enabled": True,
            "agency_operational_evaluations_read_only_enabled": True,
            "platform_operational_evaluations_ui_enabled": True,
            "agency_operational_evaluations_ui_enabled": True,
            "evaluation_is_deterministic": True,
            "evaluation_is_explainable": True,
            "evaluation_always_references_evidence": True,
            "evaluation_is_not_recommendation": True,
            "evaluation_does_not_determine_passenger_feasibility": True,
            "knowledge_acquisition_consumer": True,
            "knowledge_normalisation_consumer": True,
            "operational_constraints_consumer": True,
            "knowledge_governance_consumer": True,
            "capability_matrix_consumer": True,
            "structured_explanation_metadata_enabled": True,
            "capability_evaluation_metadata_enabled": True,
            "policy_evaluation_metadata_enabled": True,
            "pricing_evaluation_metadata_enabled": True,
            "constraint_evaluation_metadata_enabled": True,
            "procedure_evaluation_metadata_enabled": True,
            "operational_action_metadata_enabled": True,
            "evidence_trace_metadata_enabled": True,
            "future_50_7_feasibility_consumer_only": True,
            "future_50_8_recommendation_consumer_only": True,
            "future_50_9_offer_builder_consumer_only": True,
            "evaluation_statuses": EVALUATION_STATUSES,
            "evaluation_types": EVALUATION_TYPES,
            "evaluation_result_values": EVALUATION_RESULT_VALUES,
            "operational_results": EVALUATION_OPERATIONAL_RESULTS,
            "evaluation_confidence_levels": EVALUATION_CONFIDENCE_LEVELS,
            "operational_risk_levels": EVALUATION_RISK_LEVELS,
            "metadata_only": True,
            "deterministic_evaluation": True,
            "explainable_evaluation": True,
            "evidence_required": True,
            "no_ai_reasoning": True,
            "no_llm_prompts": True,
            "flight_search_disabled": True,
            "itinerary_recommendation_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "pricing_optimisation_disabled": True,
            "background_workers_disabled": True,
            "feasibility_determination_disabled": True,
            "recommendation_engine_disabled": True,
            "operational_knowledge_evaluation_count": operational_knowledge_evaluation_count,
            "operational_knowledge_evaluation_status_counts": operational_knowledge_evaluation_status_counts,
            "operational_knowledge_evaluation_type_counts": operational_knowledge_evaluation_type_counts,
            "operational_knowledge_evaluation_confidence_counts": operational_knowledge_evaluation_confidence_counts,
            "operational_knowledge_evaluation_capability_result_counts": operational_knowledge_evaluation_capability_result_counts,
            "operational_knowledge_evaluation_policy_result_counts": operational_knowledge_evaluation_policy_result_counts,
            "operational_knowledge_evaluation_pricing_result_counts": operational_knowledge_evaluation_pricing_result_counts,
            "operational_knowledge_evaluation_constraint_result_counts": operational_knowledge_evaluation_constraint_result_counts,
            "operational_knowledge_evaluation_procedure_result_counts": operational_knowledge_evaluation_procedure_result_counts,
            "operational_knowledge_evaluation_operational_result_counts": operational_knowledge_evaluation_operational_result_counts,
            "operational_knowledge_evaluation_risk_counts": operational_knowledge_evaluation_risk_counts,
            "operational_knowledge_evaluation_completed_count": operational_knowledge_evaluation_completed_count,
            "operational_knowledge_evaluation_source_reference_count": operational_knowledge_evaluation_source_reference_count,
            "operational_knowledge_evaluation_evidence_trace_count": operational_knowledge_evaluation_evidence_trace_count,
            "operational_knowledge_evaluation_required_action_count": operational_knowledge_evaluation_required_action_count,
            "operational_knowledge_evaluation_feasibility_ready_count": operational_knowledge_evaluation_feasibility_ready_count,
            "operational_knowledge_evaluation_recommendation_ready_count": operational_knowledge_evaluation_recommendation_ready_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.6 creates metadata-only Operational Knowledge Evaluation records. Evaluation determines what operationally applies from evidence-backed knowledge acquisition, normalisation, constraints, governance, and capability matrix metadata. It does not determine passenger feasibility, rank or recommend airlines, use AI or LLM prompts, search flights, book, ticket, execute parsers, optimise pricing, call providers, or run background workers.",
        },
        "passenger_service_feasibility_engine_foundation": {
            "passenger_service_feasibility_engine_enabled": True,
            "passenger_service_feasibilities_collection_enabled": True,
            "platform_passenger_service_feasibility_metadata_crud_enabled": True,
            "agency_passenger_service_feasibility_read_only_enabled": True,
            "platform_passenger_service_feasibility_ui_enabled": True,
            "agency_service_feasibility_ui_enabled": True,
            "consumes_operational_evaluation_results": True,
            "feasibility_is_not_boolean": True,
            "feasibility_is_explainable": True,
            "feasibility_is_evidence_linked": True,
            "feasibility_is_advisory": True,
            "human_authority_final": True,
            "feasibility_is_not_recommendation": True,
            "recommendation_engine_consumer_phase_50_8_enabled": True,
            "operational_evaluation_link_metadata_enabled": True,
            "passenger_context_metadata_enabled": True,
            "trip_itinerary_context_metadata_enabled": True,
            "airline_context_metadata_enabled": True,
            "feasibility_result_metadata_enabled": True,
            "requirement_outcome_metadata_enabled": True,
            "required_action_metadata_enabled": True,
            "operational_risk_metadata_enabled": True,
            "evidence_trace_metadata_enabled": True,
            "evaluation_trace_metadata_enabled": True,
            "decision_trace_metadata_enabled": True,
            "confidence_metadata_enabled": True,
            "future_50_9_offer_builder_consumer_only": True,
            "feasibility_statuses": FEASIBILITY_STATUSES,
            "feasibility_types": FEASIBILITY_TYPES,
            "feasibility_outcomes": FEASIBILITY_OUTCOMES,
            "feasibility_confidence_levels": FEASIBILITY_CONFIDENCE_LEVELS,
            "operational_risk_levels": FEASIBILITY_RISK_LEVELS,
            "metadata_only": True,
            "advisory_only": True,
            "no_ai_reasoning": True,
            "no_llm_prompts": True,
            "flight_search_disabled": True,
            "airline_recommendation_ranking_disabled": True,
            "recommendation_engine_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "pricing_optimisation_disabled": True,
            "background_workers_disabled": True,
            "automatic_operational_decisions_disabled": True,
            "passenger_service_feasibility_count": passenger_service_feasibility_count,
            "passenger_service_feasibility_status_counts": passenger_service_feasibility_status_counts,
            "passenger_service_feasibility_type_counts": passenger_service_feasibility_type_counts,
            "passenger_service_feasibility_outcome_counts": passenger_service_feasibility_outcome_counts,
            "passenger_service_feasibility_confidence_counts": passenger_service_feasibility_confidence_counts,
            "passenger_service_feasibility_risk_counts": passenger_service_feasibility_risk_counts,
            "passenger_service_feasibility_operational_evaluation_reference_count": passenger_service_feasibility_operational_evaluation_reference_count,
            "passenger_service_feasibility_evidence_trace_count": passenger_service_feasibility_evidence_trace_count,
            "passenger_service_feasibility_evaluation_trace_count": passenger_service_feasibility_evaluation_trace_count,
            "passenger_service_feasibility_decision_trace_count": passenger_service_feasibility_decision_trace_count,
            "passenger_service_feasibility_required_action_count": passenger_service_feasibility_required_action_count,
            "passenger_service_feasibility_recommendation_ready_count": passenger_service_feasibility_recommendation_ready_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.7 creates metadata-only Passenger Service Feasibility records. Feasibility consumes Operational Evaluation Results from Phase 50.6 and answers whether passenger operational service requirements can be fulfilled under evaluated conditions. Feasibility is not Boolean, is advisory, and does not book, ticket, search flights, use AI or LLM prompts, execute parsers, optimise pricing, call providers, run workers, or automate decisions. Phase 50.8 consumes feasibility metadata for advisory recommendation records.",
        },
        "airline_recommendation_engine_foundation": {
            "airline_recommendation_engine_enabled": True,
            "airline_recommendations_collection_enabled": True,
            "platform_airline_recommendation_metadata_crud_enabled": True,
            "agency_airline_recommendation_read_only_enabled": True,
            "platform_airline_recommendations_ui_enabled": True,
            "agency_recommendations_ui_enabled": True,
            "consumes_passenger_service_feasibility": True,
            "recommendation_is_not_feasibility": True,
            "recommendation_compares_feasible_airlines": True,
            "recommendation_is_advisory": True,
            "human_authority_final": True,
            "recommendation_dashboard_metadata_enabled": True,
            "comparison_matrix_metadata_enabled": True,
            "recommendation_card_metadata_enabled": True,
            "operational_scores_metadata_enabled": True,
            "commercial_scores_metadata_enabled": True,
            "required_action_metadata_enabled": True,
            "recommendation_explanation_metadata_enabled": True,
            "recommendation_evidence_metadata_enabled": True,
            "future_50_9_offer_builder_consumer_only": True,
            "recommendation_statuses": AIRLINE_RECOMMENDATION_STATUSES,
            "recommendation_status_values": RECOMMENDATION_STATUS_VALUES,
            "recommendation_levels": AIRLINE_RECOMMENDATION_LEVELS,
            "metadata_only": True,
            "advisory_only": True,
            "no_live_gds_search": True,
            "no_ndc_search": True,
            "flight_search_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "airline_recommendation_count": airline_recommendation_count,
            "airline_recommendation_status_counts": airline_recommendation_status_counts,
            "airline_recommendation_level_counts": airline_recommendation_level_counts,
            "airline_recommendation_status_value_counts": airline_recommendation_status_value_counts,
            "airline_recommendation_ready_count": airline_recommendation_ready_count,
            "airline_recommendation_feasibility_reference_count": airline_recommendation_feasibility_reference_count,
            "airline_recommendation_comparison_matrix_count": airline_recommendation_comparison_matrix_count,
            "airline_recommendation_evidence_count": airline_recommendation_evidence_count,
            "airline_recommendation_trace_count": airline_recommendation_trace_count,
            "airline_recommendation_required_action_count": airline_recommendation_required_action_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.8 creates metadata-only Airline & Itinerary Recommendation records. Recommendations consume Phase 50.7 Passenger Service Feasibility, compare feasible airlines and itinerary metadata, and remain advisory. This phase does not run live GDS or NDC search, book, issue tickets or EMDs, call providers, execute parsers, generate AI or LLM text, create prices, or run background workers.",
        },
        "intelligent_offer_builder_integration_foundation": {
            "intelligent_offer_builder_integration_enabled": True,
            "intelligent_offer_builder_packages_collection_enabled": True,
            "platform_intelligent_offer_builder_metadata_crud_enabled": True,
            "agency_offer_intelligence_metadata_crud_enabled": True,
            "platform_intelligent_offer_builder_ui_enabled": True,
            "agency_offer_intelligence_ui_enabled": True,
            "offer_builder_should_not_invent_intelligence": True,
            "consumes_passenger_service_feasibility": True,
            "consumes_airline_recommendations": True,
            "consumes_operational_evaluations": True,
            "consumes_capability_matrix": True,
            "consumes_knowledge_governance_evidence": True,
            "package_overview_metadata_enabled": True,
            "passenger_context_metadata_enabled": True,
            "trip_request_context_metadata_enabled": True,
            "offer_context_metadata_enabled": True,
            "intelligence_input_metadata_enabled": True,
            "recommended_options_metadata_enabled": True,
            "operational_readiness_metadata_enabled": True,
            "required_action_metadata_enabled": True,
            "pricing_cost_reference_metadata_enabled": True,
            "client_explanation_metadata_enabled": True,
            "internal_explanation_metadata_enabled": True,
            "decision_pack_metadata_enabled": True,
            "lifecycle_metadata_enabled": True,
            "notes_metadata_enabled": True,
            "package_statuses": INTELLIGENT_OFFER_PACKAGE_STATUSES,
            "readiness_statuses": INTELLIGENT_OFFER_READINESS_STATUSES,
            "client_visibility_statuses": INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES,
            "metadata_only": True,
            "advisory_only": True,
            "human_authority_final": True,
            "no_live_gds_search": True,
            "no_ndc_search": True,
            "flight_search_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "automatic_sending_disabled": True,
            "intelligent_offer_builder_package_count": intelligent_offer_builder_package_count,
            "intelligent_offer_builder_package_status_counts": intelligent_offer_builder_package_status_counts,
            "intelligent_offer_builder_readiness_status_counts": intelligent_offer_builder_readiness_status_counts,
            "intelligent_offer_builder_client_visibility_status_counts": intelligent_offer_builder_client_visibility_status_counts,
            "intelligent_offer_builder_recommendation_reference_count": intelligent_offer_builder_recommendation_reference_count,
            "intelligent_offer_builder_feasibility_reference_count": intelligent_offer_builder_feasibility_reference_count,
            "intelligent_offer_builder_evaluation_reference_count": intelligent_offer_builder_evaluation_reference_count,
            "intelligent_offer_builder_capability_matrix_reference_count": intelligent_offer_builder_capability_matrix_reference_count,
            "intelligent_offer_builder_evidence_reference_count": intelligent_offer_builder_evidence_reference_count,
            "intelligent_offer_builder_required_action_count": intelligent_offer_builder_required_action_count,
            "intelligent_offer_builder_client_explanation_count": intelligent_offer_builder_client_explanation_count,
            "intelligent_offer_builder_internal_trace_count": intelligent_offer_builder_internal_trace_count,
            "intelligent_offer_builder_decision_pack_ready_count": intelligent_offer_builder_decision_pack_ready_count,
            "intelligent_offer_builder_approved_for_client_presentation_count": intelligent_offer_builder_approved_for_client_presentation_count,
            "readiness_required": False,
            "diagnostic": "Phase 50.9 creates metadata-only Intelligent Offer Builder package records. Packages consume approved recommendations, feasibility, evaluations, capability matrix records, knowledge versions, and evidence for explainable offer presentation support. They do not search, book, ticket, issue EMDs, call providers, run parsers, generate AI or LLM output, run workers, or send offers automatically.",
        },
        "operational_intelligence_pipeline_consolidation_foundation": {
            "operational_intelligence_pipeline_consolidation_enabled": True,
            "operational_intelligence_cases_collection_enabled": True,
            "platform_operational_intelligence_cases_metadata_crud_enabled": True,
            "agency_intelligence_cases_metadata_crud_enabled": True,
            "platform_operational_intelligence_cases_ui_enabled": True,
            "agency_intelligence_cases_ui_enabled": True,
            "chapter_50_pipeline_consolidated": True,
            "no_new_intelligence_added": True,
            "scenario_testing_preparation": True,
            "real_airline_data_population_preparation": True,
            "human_authority_final": True,
            "passenger_requirement_to_offer_intelligence_case_view_enabled": True,
            "knowledge_acquisition_links_enabled": True,
            "normalisation_links_enabled": True,
            "operational_constraint_links_enabled": True,
            "knowledge_governance_links_enabled": True,
            "capability_matrix_links_enabled": True,
            "operational_evaluation_links_enabled": True,
            "passenger_service_feasibility_links_enabled": True,
            "airline_recommendation_links_enabled": True,
            "intelligent_offer_package_links_enabled": True,
            "pipeline_status_metadata_enabled": True,
            "decision_summary_metadata_enabled": True,
            "trace_metadata_enabled": True,
            "readiness_metadata_enabled": True,
            "notes_metadata_enabled": True,
            "case_statuses": OPERATIONAL_INTELLIGENCE_CASE_STATUSES,
            "overall_case_statuses": OPERATIONAL_INTELLIGENCE_OVERALL_STATUSES,
            "metadata_only": True,
            "advisory_only": True,
            "no_live_gds_search": True,
            "no_ndc_search": True,
            "flight_search_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "automatic_sending_disabled": True,
            "operational_intelligence_case_count": operational_intelligence_case_count,
            "operational_intelligence_case_status_counts": operational_intelligence_case_status_counts,
            "operational_intelligence_overall_status_counts": operational_intelligence_overall_status_counts,
            "operational_intelligence_pipeline_ready_counts": operational_intelligence_pipeline_ready_counts,
            "operational_intelligence_pipeline_link_counts": operational_intelligence_pipeline_link_counts,
            "operational_intelligence_ready_for_agent_review_count": operational_intelligence_ready_for_agent_review_count,
            "operational_intelligence_ready_for_offer_builder_count": operational_intelligence_ready_for_offer_builder_count,
            "operational_intelligence_ready_for_client_presentation_count": operational_intelligence_ready_for_client_presentation_count,
            "operational_intelligence_missing_pipeline_item_count": operational_intelligence_missing_pipeline_item_count,
            "operational_intelligence_blocking_pipeline_item_count": operational_intelligence_blocking_pipeline_item_count,
            "operational_intelligence_trace_entry_count": operational_intelligence_trace_entry_count,
            "readiness_required": False,
            "diagnostic": "Phase 51.0 creates metadata-only Operational Intelligence Case records. Cases consolidate the completed Chapter 50 pipeline from passenger requirement through offer-intelligence package, prepare scenario testing and real airline data population, and add no new intelligence or execution. Human authority remains final.",
        },
        "reference_data_engine_foundation": {
            "reference_data_engine_enabled": True,
            "reference_data_domains_collection_enabled": True,
            "platform_reference_data_engine_metadata_crud_enabled": True,
            "agency_reference_data_metadata_crud_enabled": True,
            "platform_reference_data_engine_ui_enabled": True,
            "agency_reference_data_ui_enabled": True,
            "airline_operational_knowledge_production_ready": True,
            "supported_reference_domains_enabled": True,
            "domain_records_metadata_enabled": True,
            "alias_metadata_enabled": True,
            "normalization_rules_metadata_enabled": True,
            "validation_rules_metadata_enabled": True,
            "import_template_reference_metadata_enabled": True,
            "governance_metadata_enabled": True,
            "review_metadata_enabled": True,
            "human_authority_final": True,
            "supported_domain_codes": SUPPORTED_REFERENCE_DOMAIN_CODES,
            "governance_statuses": REFERENCE_DATA_ENGINE_GOVERNANCE_STATUSES,
            "review_statuses": REFERENCE_DATA_ENGINE_REVIEW_STATUSES,
            "metadata_only": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "live_evaluation_disabled": True,
            "pricing_calculation_disabled": True,
            "background_workers_disabled": True,
            "old_admin_routes_disabled": True,
            "reference_data_domain_count": reference_data_domain_count,
            "reference_data_domain_active_count": reference_data_domain_active_count,
            "reference_data_domain_governance_status_counts": reference_data_domain_governance_status_counts,
            "reference_data_domain_review_status_counts": reference_data_domain_review_status_counts,
            "reference_data_engine_record_count": reference_data_engine_record_count,
            "reference_data_engine_alias_count": reference_data_engine_alias_count,
            "reference_data_engine_normalization_rule_count": reference_data_engine_normalization_rule_count,
            "reference_data_engine_validation_rule_count": reference_data_engine_validation_rule_count,
            "reference_data_engine_supported_domain_count": len(SUPPORTED_REFERENCE_DOMAIN_CODES),
            "reference_data_supported_domain_coverage_count": reference_data_supported_domain_coverage_count,
            "readiness_required": False,
            "diagnostic": "Phase 52.1 creates a metadata-only Reference Data Engine for airline operational knowledge production. It stores supported domain records, aliases, normalization rules, validation rules, import-template references, governance status, and review status. It does not add provider integrations, AI, live evaluation, pricing calculation, background workers, or old /admin routes. Human authority remains final.",
        },
        "knowledge_import_templates_foundation": {
            "foundation_phase": KNOWLEDGE_IMPORT_TEMPLATE_FOUNDATION_PHASE_LABEL,
            "knowledge_import_templates_enabled": True,
            "knowledge_import_templates_collection_enabled": True,
            "platform_knowledge_import_templates_metadata_crud_enabled": True,
            "agency_import_templates_metadata_crud_enabled": True,
            "platform_knowledge_import_templates_ui_enabled": True,
            "agency_import_templates_ui_enabled": True,
            "template_types": KNOWLEDGE_IMPORT_TEMPLATE_TYPES,
            "import_scopes": KNOWLEDGE_IMPORT_TEMPLATE_IMPORT_SCOPES,
            "required_columns_metadata_enabled": True,
            "optional_columns_metadata_enabled": True,
            "validation_rules_metadata_enabled": True,
            "mapping_rules_metadata_enabled": True,
            "sample_rows_metadata_enabled": True,
            "accepted_file_types_metadata_enabled": True,
            "governance_links_metadata_enabled": True,
            "review_required_metadata_enabled": True,
            "metadata_only": True,
            "parsing_execution_disabled": True,
            "scraping_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "human_authority_final": True,
            "knowledge_import_template_count": knowledge_import_template_count,
            "knowledge_import_template_active_count": knowledge_import_template_active_count,
            "knowledge_import_template_type_counts": knowledge_import_template_type_counts,
            "knowledge_import_template_import_scope_counts": knowledge_import_template_import_scope_counts,
            "knowledge_import_template_required_column_count": knowledge_import_template_required_column_count,
            "knowledge_import_template_optional_column_count": knowledge_import_template_optional_column_count,
            "knowledge_import_template_validation_rule_count": knowledge_import_template_validation_rule_count,
            "knowledge_import_template_mapping_rule_count": knowledge_import_template_mapping_rule_count,
            "knowledge_import_template_sample_row_count": knowledge_import_template_sample_row_count,
            "knowledge_import_template_governance_link_count": knowledge_import_template_governance_link_count,
            "knowledge_import_template_review_required_count": knowledge_import_template_review_required_count,
            "knowledge_import_template_supported_type_count": len(KNOWLEDGE_IMPORT_TEMPLATE_TYPES),
            "knowledge_import_template_type_coverage_count": knowledge_import_template_type_coverage_count,
            "readiness_required": False,
            "diagnostic": "Phase 52.2 creates metadata-only Knowledge Import Templates for future airline knowledge population. It stores reusable column, validation, mapping, sample-row, accepted-file-type, scope, review, and governance metadata without parsing execution, scraping, AI, background workers, or provider integrations. Human authority remains final.",
        },
        "visual_policy_editor_foundation": {
            "visual_policy_editor_enabled": True,
            "visual_policy_editor_cards_collection_enabled": True,
            "platform_visual_policy_editor_metadata_crud_enabled": True,
            "agency_policy_editor_metadata_crud_enabled": True,
            "platform_visual_policy_editor_ui_enabled": True,
            "agency_policy_editor_ui_enabled": True,
            "no_code_policy_sections_enabled": True,
            "overview_section_enabled": True,
            "support_status_section_enabled": True,
            "limits_section_enabled": True,
            "restrictions_section_enabled": True,
            "documents_section_enabled": True,
            "approvals_section_enabled": True,
            "warnings_section_enabled": True,
            "evidence_section_enabled": True,
            "governance_section_enabled": True,
            "service_parameter_taxonomy_link_section_enabled": True,
            "policy_families": POLICY_FAMILIES,
            "policy_card_statuses": POLICY_CARD_STATUSES,
            "support_statuses": VISUAL_POLICY_SUPPORT_STATUSES,
            "metadata_only": True,
            "policy_execution_disabled": True,
            "rule_evaluation_disabled": True,
            "pricing_calculation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "old_admin_routes_disabled": True,
            "human_authority_final": True,
            "visual_policy_editor_card_count": visual_policy_editor_card_count,
            "visual_policy_editor_active_card_count": visual_policy_editor_active_card_count,
            "visual_policy_editor_status_counts": visual_policy_editor_status_counts,
            "visual_policy_editor_support_status_counts": visual_policy_editor_support_status_counts,
            "visual_policy_editor_service_code_count": visual_policy_editor_service_code_count,
            "visual_policy_editor_evidence_link_count": visual_policy_editor_evidence_link_count,
            "visual_policy_editor_governance_link_count": visual_policy_editor_governance_link_count,
            "visual_policy_editor_taxonomy_link_count": visual_policy_editor_taxonomy_link_count,
            "visual_policy_editor_supported_family_count": len(POLICY_FAMILIES),
            "visual_policy_editor_family_coverage_count": visual_policy_editor_family_coverage_count,
            "readiness_required": False,
            "diagnostic": "Phase 52.3 creates a metadata-only Visual Policy Editor for airline service policy cards. It stores no-code sections for support status, limits, restrictions, documents, approvals, warnings, evidence, governance, and taxonomy links without policy execution, rule evaluation, pricing calculation, provider integrations, AI, workers, or legacy admin routes. Human authority remains final.",
        },
        "pricing_formula_builder_foundation": {
            "pricing_formula_builder_enabled": True,
            "pricing_formula_builders_collection_enabled": True,
            "platform_pricing_formula_builder_metadata_crud_enabled": True,
            "agency_pricing_formula_builder_metadata_crud_enabled": True,
            "platform_pricing_formula_builder_ui_enabled": True,
            "agency_pricing_formula_builder_ui_enabled": True,
            "pricing_units_metadata_enabled": True,
            "way_metadata_enabled": True,
            "route_type_metadata_enabled": True,
            "flight_type_metadata_enabled": True,
            "fare_bundle_metadata_enabled": True,
            "pricing_category_metadata_enabled": True,
            "amount_type_metadata_enabled": True,
            "currency_metadata_enabled": True,
            "base_amount_metadata_enabled": True,
            "formula_components_metadata_enabled": True,
            "multipliers_metadata_enabled": True,
            "applicability_metadata_enabled": True,
            "manual_confirmation_metadata_enabled": True,
            "client_visibility_metadata_enabled": True,
            "refund_exchange_condition_reference_metadata_enabled": True,
            "pricing_units": PRICING_UNITS,
            "way_values": PRICING_WAY_VALUES,
            "route_types": PRICING_ROUTE_TYPES,
            "flight_types": PRICING_FLIGHT_TYPES,
            "fare_bundles": PRICING_FARE_BUNDLES,
            "pricing_categories": PRICING_CATEGORIES,
            "amount_types": AMOUNT_TYPES,
            "formula_statuses": PRICING_FORMULA_STATUSES,
            "client_visibility_options": PRICING_FORMULA_CLIENT_VISIBILITY_OPTIONS,
            "metadata_only": True,
            "live_price_calculation_disabled": True,
            "payment_integrations_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_client_sending_disabled": True,
            "human_authority_final": True,
            "pricing_formula_builder_count": pricing_formula_builder_count,
            "pricing_formula_builder_active_count": pricing_formula_builder_active_count,
            "pricing_formula_builder_status_counts": pricing_formula_builder_status_counts,
            "pricing_formula_builder_amount_type_counts": pricing_formula_builder_amount_type_counts,
            "pricing_formula_builder_category_counts": pricing_formula_builder_category_counts,
            "pricing_formula_builder_client_visibility_counts": pricing_formula_builder_client_visibility_counts,
            "pricing_formula_builder_service_code_count": pricing_formula_builder_service_code_count,
            "pricing_formula_builder_component_count": pricing_formula_builder_component_count,
            "pricing_formula_builder_multiplier_count": pricing_formula_builder_multiplier_count,
            "pricing_formula_builder_refund_exchange_reference_count": pricing_formula_builder_refund_exchange_reference_count,
            "pricing_formula_builder_evidence_link_count": pricing_formula_builder_evidence_link_count,
            "pricing_formula_builder_governance_link_count": pricing_formula_builder_governance_link_count,
            "pricing_formula_builder_taxonomy_link_count": pricing_formula_builder_taxonomy_link_count,
            "pricing_formula_builder_visual_policy_link_count": pricing_formula_builder_visual_policy_link_count,
            "pricing_formula_builder_manual_confirmation_required_count": pricing_formula_builder_manual_confirmation_required_count,
            "pricing_formula_builder_supported_category_count": len(PRICING_CATEGORIES),
            "pricing_formula_builder_category_coverage_count": pricing_formula_builder_category_coverage_count,
            "readiness_required": False,
            "diagnostic": "Phase 52.4 creates metadata-only Pricing Formula Builder records for airline ancillary and service pricing. It stores pricing unit, way, route type, flight type, fare bundle, category, amount type, currency, base amount, formula components, multipliers, applicability, manual confirmation, client visibility, and refund/exchange condition references without live price calculation, payment integrations, provider integrations, AI, workers, or automatic client sending. Human authority remains final.",
        },
        "operational_rule_composer_foundation": {
            "operational_rule_composer_enabled": True,
            "operational_rule_composer_rules_collection_enabled": True,
            "platform_operational_rule_composer_metadata_crud_enabled": True,
            "agency_rule_composer_metadata_crud_enabled": True,
            "platform_operational_rule_composer_ui_enabled": True,
            "agency_rule_composer_ui_enabled": True,
            "no_code_compound_rules_enabled": True,
            "applies_to_metadata_enabled": True,
            "all_conditions_metadata_enabled": True,
            "any_conditions_metadata_enabled": True,
            "result_metadata_enabled": True,
            "severity_metadata_enabled": True,
            "client_message_metadata_enabled": True,
            "internal_message_metadata_enabled": True,
            "evidence_links_metadata_enabled": True,
            "governance_links_metadata_enabled": True,
            "parameter_taxonomy_links_metadata_enabled": True,
            "effective_dates_metadata_enabled": True,
            "lifecycle_status_metadata_enabled": True,
            "supported_operators": OPERATIONAL_RULE_SUPPORTED_OPERATORS,
            "rule_families": OPERATIONAL_RULE_FAMILIES,
            "severity_levels": OPERATIONAL_RULE_SEVERITY_LEVELS,
            "lifecycle_statuses": OPERATIONAL_RULE_LIFECYCLE_STATUSES,
            "metadata_only": True,
            "rule_execution_disabled": True,
            "live_rule_evaluation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_decisioning_disabled": True,
            "human_authority_final": True,
            "operational_rule_composer_rule_count": operational_rule_composer_rule_count,
            "operational_rule_composer_active_rule_count": operational_rule_composer_active_rule_count,
            "operational_rule_composer_family_counts": operational_rule_composer_family_counts,
            "operational_rule_composer_lifecycle_counts": operational_rule_composer_lifecycle_counts,
            "operational_rule_composer_severity_counts": operational_rule_composer_severity_counts,
            "operational_rule_composer_service_code_count": operational_rule_composer_service_code_count,
            "operational_rule_composer_condition_count": operational_rule_composer_condition_count,
            "operational_rule_composer_any_condition_count": operational_rule_composer_any_condition_count,
            "operational_rule_composer_total_condition_count": operational_rule_composer_condition_count + operational_rule_composer_any_condition_count,
            "operational_rule_composer_evidence_link_count": operational_rule_composer_evidence_link_count,
            "operational_rule_composer_governance_link_count": operational_rule_composer_governance_link_count,
            "operational_rule_composer_parameter_taxonomy_link_count": operational_rule_composer_parameter_taxonomy_link_count,
            "operational_rule_composer_client_message_count": operational_rule_composer_client_message_count,
            "operational_rule_composer_internal_message_count": operational_rule_composer_internal_message_count,
            "operational_rule_composer_supported_operator_count": len(OPERATIONAL_RULE_SUPPORTED_OPERATORS),
            "operational_rule_composer_supported_family_count": len(OPERATIONAL_RULE_FAMILIES),
            "operational_rule_composer_family_coverage_count": operational_rule_composer_family_coverage_count,
            "readiness_required": False,
            "diagnostic": "Phase 52.5 creates metadata-only Operational Rule Composer records for no-code compound airline passenger service restrictions and outcomes. It stores applies-to metadata, all/any condition groups, supported operators, result metadata, severity, messages, evidence, governance, parameter taxonomy links, effective dates, and lifecycle status without rule execution, live evaluation, provider integrations, AI, workers, or automatic decisions. Human authority remains final.",
        },
        "knowledge_quality_assurance_foundation": {
            "knowledge_quality_assurance_enabled": True,
            "knowledge_quality_assurance_reviews_collection_enabled": True,
            "platform_knowledge_quality_assurance_metadata_crud_enabled": True,
            "agency_knowledge_quality_assurance_metadata_crud_enabled": True,
            "platform_knowledge_qa_ui_enabled": True,
            "agency_knowledge_qa_ui_enabled": True,
            "qa_review_layer_enabled": True,
            "qa_checks_metadata_enabled": True,
            "issues_metadata_enabled": True,
            "reviewer_metadata_enabled": True,
            "requested_changes_metadata_enabled": True,
            "approval_recommendation_metadata_enabled": True,
            "governance_links_metadata_enabled": True,
            "target_metadata_enabled": True,
            "airline_service_metadata_enabled": True,
            "qa_status_metadata_enabled": True,
            "severity_metadata_enabled": True,
            "qa_checks": KNOWLEDGE_QA_CHECKS,
            "target_types": KNOWLEDGE_QA_TARGET_TYPES,
            "qa_statuses": KNOWLEDGE_QA_STATUSES,
            "severity_levels": KNOWLEDGE_QA_SEVERITY_LEVELS,
            "approval_recommendations": KNOWLEDGE_QA_APPROVAL_RECOMMENDATIONS,
            "metadata_only": True,
            "auto_approval_disabled": True,
            "publishing_disabled": True,
            "rule_execution_disabled": True,
            "ai_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
            "knowledge_quality_assurance_review_count": knowledge_quality_assurance_review_count,
            "knowledge_quality_assurance_active_review_count": knowledge_quality_assurance_active_review_count,
            "knowledge_quality_assurance_status_counts": knowledge_quality_assurance_status_counts,
            "knowledge_quality_assurance_severity_counts": knowledge_quality_assurance_severity_counts,
            "knowledge_quality_assurance_target_type_counts": knowledge_quality_assurance_target_type_counts,
            "knowledge_quality_assurance_approval_recommendation_counts": knowledge_quality_assurance_approval_recommendation_counts,
            "knowledge_quality_assurance_issue_check_counts": knowledge_quality_assurance_issue_check_counts,
            "knowledge_quality_assurance_issue_count": knowledge_quality_assurance_issue_count,
            "knowledge_quality_assurance_requested_change_count": knowledge_quality_assurance_requested_change_count,
            "knowledge_quality_assurance_governance_link_count": knowledge_quality_assurance_governance_link_count,
            "knowledge_quality_assurance_supported_check_count": len(KNOWLEDGE_QA_CHECKS),
            "knowledge_quality_assurance_supported_target_type_count": len(KNOWLEDGE_QA_TARGET_TYPES),
            "readiness_required": False,
            "diagnostic": "Phase 52.6 creates metadata-only Knowledge Quality Assurance reviews for airline knowledge production. It stores QA checks, issues, severities, reviewers, requested changes, approval recommendations, and governance links without auto-approval, publishing, rule execution, AI, providers, workers, or operational automation. Human authority remains final.",
        },
        "airline_knowledge_publishing_foundation": {
            "airline_knowledge_publishing_enabled": True,
            "airline_knowledge_publications_collection_enabled": True,
            "platform_airline_knowledge_publishing_metadata_crud_enabled": True,
            "agency_published_knowledge_metadata_crud_enabled": True,
            "platform_knowledge_publishing_ui_enabled": True,
            "agency_published_knowledge_ui_enabled": True,
            "controlled_publication_workflow_metadata_enabled": True,
            "included_knowledge_version_metadata_enabled": True,
            "included_policy_card_metadata_enabled": True,
            "included_pricing_formula_metadata_enabled": True,
            "included_rule_metadata_enabled": True,
            "qa_review_metadata_enabled": True,
            "release_channel_metadata_enabled": True,
            "effective_date_metadata_enabled": True,
            "supersession_metadata_enabled": True,
            "rollback_plan_metadata_enabled": True,
            "consumer_readiness_metadata_enabled": True,
            "AOIE_ready_metadata_enabled": True,
            "agency_visibility_metadata_enabled": True,
            "publication_statuses": AIRLINE_KNOWLEDGE_PUBLICATION_STATUSES,
            "release_channels": AIRLINE_KNOWLEDGE_RELEASE_CHANNELS,
            "visibility_statuses": AIRLINE_KNOWLEDGE_VISIBILITY_STATUSES,
            "metadata_only": True,
            "automatic_publication_disabled": True,
            "recommendation_execution_disabled": True,
            "auto_approval_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
            "airline_knowledge_publication_count": airline_knowledge_publication_count,
            "airline_knowledge_active_publication_count": airline_knowledge_active_publication_count,
            "airline_knowledge_publication_status_counts": airline_knowledge_publication_status_counts,
            "airline_knowledge_release_channel_counts": airline_knowledge_release_channel_counts,
            "airline_knowledge_visibility_counts": airline_knowledge_visibility_counts,
            "airline_knowledge_publication_aoie_ready_count": airline_knowledge_publication_aoie_ready_count,
            "airline_knowledge_publication_knowledge_version_count": airline_knowledge_publication_knowledge_version_count,
            "airline_knowledge_publication_policy_card_count": airline_knowledge_publication_policy_card_count,
            "airline_knowledge_publication_pricing_formula_count": airline_knowledge_publication_pricing_formula_count,
            "airline_knowledge_publication_rule_count": airline_knowledge_publication_rule_count,
            "airline_knowledge_publication_qa_review_count": airline_knowledge_publication_qa_review_count,
            "airline_knowledge_publication_supersession_count": airline_knowledge_publication_supersession_count,
            "airline_knowledge_publication_supported_status_count": len(AIRLINE_KNOWLEDGE_PUBLICATION_STATUSES),
            "airline_knowledge_publication_supported_release_channel_count": len(AIRLINE_KNOWLEDGE_RELEASE_CHANNELS),
            "readiness_required": False,
            "diagnostic": "Phase 52.7 creates metadata-only Airline Knowledge Publishing records for controlled publication workflow tracking. It stores included knowledge artifacts, QA review links, status, release channel, effective dates, supersession, rollback plan, consumer readiness, AOIE readiness, and agency visibility without automatic publication, recommendation execution, providers, AI, workers, or operational automation. Human authority remains final.",
        },
        "operational_scenario_testing_foundation": {
            "operational_scenario_testing_enabled": True,
            "operational_scenario_tests_collection_enabled": True,
            "platform_operational_scenario_testing_metadata_crud_enabled": True,
            "agency_operational_scenario_testing_read_only_enabled": True,
            "platform_scenario_testing_ui_enabled": True,
            "agency_scenario_testing_ui_enabled": True,
            "passenger_context_metadata_enabled": True,
            "itinerary_context_metadata_enabled": True,
            "airline_context_metadata_enabled": True,
            "service_requirement_metadata_enabled": True,
            "pet_scenario_metadata_enabled": True,
            "special_item_scenario_metadata_enabled": True,
            "document_scenario_metadata_enabled": True,
            "expected_policy_outcome_metadata_enabled": True,
            "expected_pricing_behavior_metadata_enabled": True,
            "expected_feasibility_metadata_enabled": True,
            "expected_recommendation_level_metadata_enabled": True,
            "expected_required_action_metadata_enabled": True,
            "evidence_link_metadata_enabled": True,
            "review_notes_metadata_enabled": True,
            "scenario_families": OPERATIONAL_SCENARIO_FAMILIES,
            "test_statuses": OPERATIONAL_SCENARIO_TEST_STATUSES,
            "expected_recommendation_levels": OPERATIONAL_SCENARIO_EXPECTED_RECOMMENDATION_LEVELS,
            "metadata_only": True,
            "scenario_execution_disabled": True,
            "live_provider_execution_disabled": True,
            "ai_disabled": True,
            "automated_test_execution_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
            "operational_scenario_test_count": operational_scenario_test_count,
            "operational_scenario_active_test_count": operational_scenario_active_test_count,
            "operational_scenario_family_counts": operational_scenario_family_counts,
            "operational_scenario_test_status_counts": operational_scenario_test_status_counts,
            "operational_scenario_expected_recommendation_counts": operational_scenario_expected_recommendation_counts,
            "operational_scenario_service_requirement_count": operational_scenario_service_requirement_count,
            "operational_scenario_document_count": operational_scenario_document_count,
            "operational_scenario_expected_required_action_count": operational_scenario_expected_required_action_count,
            "operational_scenario_evidence_link_count": operational_scenario_evidence_link_count,
            "operational_scenario_pet_case_count": operational_scenario_pet_case_count,
            "operational_scenario_special_item_case_count": operational_scenario_special_item_case_count,
            "operational_scenario_supported_family_count": len(OPERATIONAL_SCENARIO_FAMILIES),
            "readiness_required": False,
            "diagnostic": "Phase 52.8 creates metadata-only Operational Scenario Testing records for validating airline knowledge production against passenger service examples. It stores passenger, itinerary, airline, service, pet, special-item, document, expected outcome, evidence, and review metadata without running live providers, AI, parser execution, automated tests, workers, or operational automation. Human authority remains final.",
        },
        "knowledge_population_toolkit_foundation": {
            "knowledge_population_toolkit_enabled": True,
            "knowledge_population_toolkits_collection_enabled": True,
            "platform_knowledge_population_toolkit_metadata_crud_enabled": True,
            "agency_knowledge_population_toolkit_read_only_enabled": True,
            "platform_knowledge_population_toolkit_ui_enabled": True,
            "agency_knowledge_population_toolkit_ui_enabled": True,
            "airline_onboarding_checklist_metadata_enabled": True,
            "reference_readiness_metadata_enabled": True,
            "import_template_readiness_metadata_enabled": True,
            "policy_editor_readiness_metadata_enabled": True,
            "pricing_builder_readiness_metadata_enabled": True,
            "rule_composer_readiness_metadata_enabled": True,
            "qa_readiness_metadata_enabled": True,
            "publishing_readiness_metadata_enabled": True,
            "scenario_test_readiness_metadata_enabled": True,
            "evidence_coverage_metadata_enabled": True,
            "population_progress_metadata_enabled": True,
            "missing_domains_metadata_enabled": True,
            "next_actions_metadata_enabled": True,
            "population_statuses": KNOWLEDGE_POPULATION_STATUSES,
            "readiness_statuses": KNOWLEDGE_POPULATION_READINESS_STATUSES,
            "metadata_only": True,
            "scraping_disabled": True,
            "auto_import_disabled": True,
            "ai_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "population_execution_disabled": True,
            "human_authority_final": True,
            "knowledge_population_toolkit_count": knowledge_population_toolkit_count,
            "knowledge_population_active_toolkit_count": knowledge_population_active_toolkit_count,
            "knowledge_population_status_counts": knowledge_population_status_counts,
            "knowledge_population_qa_status_counts": knowledge_population_qa_status_counts,
            "knowledge_population_publishing_status_counts": knowledge_population_publishing_status_counts,
            "knowledge_population_scenario_status_counts": knowledge_population_scenario_status_counts,
            "knowledge_population_service_family_coverage_count": knowledge_population_service_family_coverage_count,
            "knowledge_population_missing_domain_count": knowledge_population_missing_domain_count,
            "knowledge_population_blocker_count": knowledge_population_blocker_count,
            "knowledge_population_warning_count": knowledge_population_warning_count,
            "knowledge_population_next_action_count": knowledge_population_next_action_count,
            "knowledge_population_supported_status_count": len(KNOWLEDGE_POPULATION_STATUSES),
            "knowledge_population_supported_readiness_status_count": len(KNOWLEDGE_POPULATION_READINESS_STATUSES),
            "readiness_required": False,
            "diagnostic": "Phase 52.9 creates metadata-only Knowledge Population Toolkit records for airline knowledge population readiness, coverage, progress, gaps, blockers, warnings, and next actions. It does not scrape, auto-import, call providers, use AI, run workers, execute population jobs, or override human authority.",
        },
        "end_to_end_stabilization_pilot_readiness_foundation": {
            "pilot_readiness_enabled": True,
            "pilot_readiness_profiles_collection_enabled": True,
            "pilot_readiness_assessments_collection_enabled": True,
            "pilot_readiness_checks_collection_enabled": True,
            "pilot_golden_path_cases_collection_enabled": True,
            "pilot_golden_path_runs_collection_enabled": True,
            "pilot_readiness_issues_collection_enabled": True,
            "platform_pilot_readiness_metadata_crud_enabled": True,
            "agency_pilot_readiness_diagnostic_metadata_enabled": True,
            "platform_pilot_readiness_ui_enabled": True,
            "agency_pilot_readiness_ui_enabled": True,
            "deterministic_readiness_scoring_enabled": True,
            "critical_blockers_prevent_pilot_ready": True,
            "golden_path_templates_exposed_without_auto_seed": True,
            "golden_path_stage_results_persisted": True,
            "remediation_links_use_canonical_routes": True,
            "client_internal_message_separation_enabled": True,
            "check_families": PILOT_READINESS_CHECK_FAMILIES,
            "readiness_statuses": PILOT_READINESS_STATUSES,
            "check_statuses": PILOT_READINESS_CHECK_STATUSES,
            "golden_path_statuses": PILOT_GOLDEN_PATH_STATUSES,
            "golden_path_stage_codes": PILOT_GOLDEN_PATH_STAGE_CODES,
            "golden_path_sample_template_count": len(PILOT_GOLDEN_PATH_CASE_TEMPLATES),
            "remediation_link_count": len(PILOT_READINESS_REMEDIATION_LINKS),
            "metadata_only": True,
            "production_seed_disabled": True,
            "production_record_mutation_disabled": True,
            "automation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "destructive_reset_disabled": True,
            "human_authority_final": True,
            "pilot_readiness_profile_count": len(pilot_readiness_profile_records),
            "pilot_readiness_assessment_count": len(pilot_readiness_assessment_records),
            "pilot_readiness_check_count": len(pilot_readiness_check_records),
            "pilot_golden_path_case_count": len(pilot_golden_path_case_records),
            "pilot_golden_path_run_count": len(pilot_golden_path_run_records),
            "pilot_readiness_issue_count": len(pilot_readiness_issue_records),
            "pilot_readiness_open_issue_count": pilot_readiness_open_issue_count,
            "pilot_readiness_critical_blocker_count": pilot_readiness_critical_blocker_count,
            "pilot_readiness_assessment_status_counts": pilot_readiness_assessment_status_counts,
            "pilot_readiness_check_status_counts": pilot_readiness_check_status_counts,
            "pilot_readiness_check_family_counts": pilot_readiness_check_family_counts,
            "pilot_golden_path_run_status_counts": pilot_golden_path_run_status_counts,
            "pilot_readiness_issue_status_counts": pilot_readiness_issue_status_counts,
            "readiness_required": False,
            "diagnostic": "Phase 53.0 adds metadata-only end-to-end stabilization and pilot readiness diagnostics. It records assessment, check, golden-path run, and issue metadata only; it does not seed production records, reset data, execute providers, use AI, run workers, mutate operational records, or override human authority.",
        },
        "operational_workflow_orchestration_foundation": {
            "operational_workflow_orchestration_enabled": True,
            "workflow_definition_collection_enabled": True,
            "workflow_instance_collection_enabled": True,
            "workflow_transition_collection_enabled": True,
            "workflow_guard_collection_enabled": True,
            "workflow_event_collection_enabled": True,
            "platform_operational_workflow_definition_metadata_crud_enabled": True,
            "platform_operational_workflow_guard_metadata_crud_enabled": True,
            "agency_operational_workflow_instance_metadata_enabled": True,
            "agency_operational_workflow_transition_metadata_enabled": True,
            "shared_workflow_state_layer_enabled": True,
            "guarded_transition_metadata_enabled": True,
            "warning_acknowledgement_metadata_enabled": True,
            "blocked_transition_rejection_enabled": True,
            "unknown_guard_handling_enabled": True,
            "immutable_transition_history_enabled": True,
            "workflow_events_metadata_enabled": True,
            "explicit_entity_adapters_enabled": True,
            "request_lifecycle_states": OPERATIONAL_WORKFLOW_REQUEST_STATES,
            "trip_lifecycle_states": OPERATIONAL_WORKFLOW_TRIP_STATES,
            "booking_readiness_states": OPERATIONAL_WORKFLOW_BOOKING_READINESS_STATES,
            "service_fulfillment_states": OPERATIONAL_WORKFLOW_SERVICE_STATES,
            "guard_types": OPERATIONAL_WORKFLOW_GUARD_TYPES,
            "guard_results": OPERATIONAL_WORKFLOW_GUARD_RESULTS,
            "transition_statuses": OPERATIONAL_WORKFLOW_TRANSITION_STATUSES,
            "workflow_statuses": OPERATIONAL_WORKFLOW_STATUSES,
            "default_workflow_definition_count": len(OPERATIONAL_WORKFLOW_DEFAULT_DEFINITIONS),
            "metadata_only": True,
            "entity_status_sync_disabled_by_default": True,
            "unrestricted_dynamic_mutation_disabled": True,
            "existing_workspace_services_preserved": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "automatic_execution_disabled": True,
            "automation_disabled": True,
            "destructive_reset_disabled": True,
            "human_authority_final": True,
            "operational_workflow_definition_count": len(operational_workflow_definition_records),
            "operational_workflow_instance_count": len(operational_workflow_instance_records),
            "operational_workflow_transition_count": len(operational_workflow_transition_records),
            "operational_workflow_guard_count": len(operational_workflow_guard_records),
            "operational_workflow_event_count": len(operational_workflow_event_records),
            "operational_workflow_definition_status_counts": operational_workflow_definition_status_counts,
            "operational_workflow_instance_status_counts": operational_workflow_instance_status_counts,
            "operational_workflow_transition_status_counts": operational_workflow_transition_status_counts,
            "operational_workflow_entity_type_counts": operational_workflow_entity_type_counts,
            "operational_workflow_current_state_counts": operational_workflow_current_state_counts,
            "operational_workflow_guard_type_counts": operational_workflow_guard_type_counts,
            "operational_workflow_active_blocker_count": operational_workflow_active_blocker_count,
            "operational_workflow_active_warning_count": operational_workflow_active_warning_count,
            "readiness_required": False,
            "diagnostic": "Phase 54.1 adds the canonical operational workflow orchestration metadata layer around existing request, trip, offer, booking, ticket, EMD, document, timeline, and passenger-service workflow foundations. It stores definitions, instances, guards, immutable transition history, and events without replacing workspace services, executing providers, running automation, or mutating entity statuses unless a future explicit adapter enables it.",
        },
        "agent_work_queue_assignment_foundation": {
            "agent_work_queue_assignment_enabled": True,
            "operational_work_items_collection_enabled": True,
            "operational_queue_definitions_collection_enabled": True,
            "operational_assignment_events_collection_enabled": True,
            "operational_queue_views_collection_enabled": True,
            "canonical_operational_queue": True,
            "platform_queue_governance_enabled": True,
            "agency_work_queue_enabled": True,
            "assignment_actions_enabled": True,
            "bulk_safe_assignment_enabled": True,
            "idempotent_work_item_generation_enabled": True,
            "workflow_event_integration_enabled": True,
            "request_task_compatibility_mapping_enabled": True,
            "timeline_history_integration_enabled": True,
            "existing_task_system_preserved": True,
            "client_facing_context_hidden": True,
            "platform_governance_does_not_silently_act_as_agency_staff": True,
            "deterministic_queue_ordering_enabled": True,
            "agency_isolation_enforced": True,
            "work_item_statuses": OPERATIONAL_WORK_ITEM_STATUSES,
            "work_item_priorities": OPERATIONAL_WORK_ITEM_PRIORITIES,
            "work_item_severities": OPERATIONAL_WORK_ITEM_SEVERITIES,
            "work_item_types": OPERATIONAL_WORK_ITEM_TYPES,
            "canonical_queue_codes": OPERATIONAL_QUEUE_CODES,
            "blocker_statuses": OPERATIONAL_QUEUE_BLOCKER_STATUSES,
            "sla_statuses": OPERATIONAL_QUEUE_SLA_STATUSES,
            "assignment_event_types": OPERATIONAL_ASSIGNMENT_EVENT_TYPES,
            "default_queue_definition_count": len(OPERATIONAL_DEFAULT_QUEUE_DEFINITIONS),
            "metadata_only": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_execution_disabled": True,
            "automation_disabled": True,
            "destructive_reset_disabled": True,
            "human_authority_final": True,
            "operational_work_item_count": len(operational_work_item_records),
            "operational_queue_definition_count": len(operational_queue_definition_records),
            "operational_assignment_event_count": len(operational_assignment_event_records),
            "operational_queue_view_count": len(operational_queue_view_records),
            "operational_work_item_unassigned_count": operational_work_item_unassigned_count,
            "operational_work_item_due_soon_count": operational_work_item_due_soon_count,
            "operational_work_item_overdue_count": operational_work_item_overdue_count,
            "operational_work_item_status_counts": operational_work_item_status_counts,
            "operational_work_item_priority_counts": operational_work_item_priority_counts,
            "operational_work_item_severity_counts": operational_work_item_severity_counts,
            "operational_work_item_type_counts": operational_work_item_type_counts,
            "operational_work_item_queue_counts": operational_work_item_queue_counts,
            "operational_work_item_sla_counts": operational_work_item_sla_counts,
            "operational_work_item_blocker_counts": operational_work_item_blocker_counts,
            "operational_assignment_event_type_counts": operational_assignment_event_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 54.2 adds the canonical agent work queue and assignment metadata layer. It consolidates work from existing requests, trips, offers, bookings, ticketing, EMDs, passenger services, documents, approvals, policy gaps, knowledge issues, disruptions, service cases, workflow blockers, timelines, request tasks, and pilot-readiness issues without creating a second task system, executing providers, running automation, exposing internal context to client routes, or bypassing agency isolation.",
        },
        "sla_operational_deadline_engine_foundation": {
            "sla_operational_deadline_engine_enabled": True,
            "operational_sla_policies_collection_enabled": True,
            "operational_deadlines_collection_enabled": True,
            "operational_sla_events_collection_enabled": True,
            "operational_business_calendars_collection_enabled": True,
            "platform_sla_policy_governance_enabled": True,
            "agency_deadline_workspace_enabled": True,
            "deadline_calculation_enabled": True,
            "business_calendar_calculation_enabled": True,
            "pause_resume_metadata_enabled": True,
            "extension_audit_enabled": True,
            "manual_extensions_preserved": True,
            "due_soon_detection_enabled": True,
            "breach_detection_enabled": True,
            "escalation_suggestion_metadata_enabled": True,
            "work_queue_integration_enabled": True,
            "workflow_event_integration_enabled": True,
            "timeline_history_integration_enabled": True,
            "request_offer_booking_ticketing_deadline_types_supported": True,
            "passenger_service_notice_deadline_types_supported": True,
            "disruption_claim_refund_change_deadline_types_supported": True,
            "agency_isolation_enforced": True,
            "metadata_only": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "automatic_execution_disabled": True,
            "automation_disabled": True,
            "enforcement_disabled": True,
            "destructive_reset_disabled": True,
            "human_authority_final": True,
            "sla_policy_scopes": OPERATIONAL_SLA_POLICY_SCOPES,
            "sla_policy_statuses": OPERATIONAL_SLA_POLICY_STATUSES,
            "duration_units": OPERATIONAL_SLA_DURATION_UNITS,
            "business_hours_behaviors": OPERATIONAL_BUSINESS_HOURS_BEHAVIORS,
            "deadline_statuses": OPERATIONAL_DEADLINE_STATUSES,
            "breach_states": OPERATIONAL_DEADLINE_BREACH_STATES,
            "sla_event_types": OPERATIONAL_SLA_EVENT_TYPES,
            "deadline_types": OPERATIONAL_DEADLINE_TYPES,
            "default_sla_policy_count": len(OPERATIONAL_DEFAULT_SLA_POLICIES),
            "operational_sla_policy_count": len(operational_sla_policy_records),
            "operational_deadline_count": len(operational_deadline_records),
            "operational_sla_event_count": len(operational_sla_event_records),
            "operational_business_calendar_count": len(operational_business_calendar_records),
            "operational_deadline_due_soon_count": operational_deadline_due_soon_count,
            "operational_deadline_overdue_count": operational_deadline_overdue_count,
            "operational_deadline_paused_count": operational_deadline_paused_count,
            "operational_deadline_completed_count": operational_deadline_completed_count,
            "operational_deadline_status_counts": operational_deadline_status_counts,
            "operational_deadline_breach_counts": operational_deadline_breach_counts,
            "operational_deadline_type_counts": operational_deadline_type_counts,
            "operational_sla_policy_status_counts": operational_sla_policy_status_counts,
            "operational_sla_event_type_counts": operational_sla_event_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 54.3 adds the metadata-only SLA and operational deadline engine. It stores SLA policies, business calendars, calculated deadlines, and SLA events; explains calculations; preserves manual extensions; detects due-soon and breach states; and emits work-queue/workflow/timeline metadata without enforcing access, blocking routes, scheduling workers, contacting providers, sending messages, or automating operational action.",
        },
        "task_automation_dependency_orchestration_foundation": {
            "task_automation_dependency_orchestration_enabled": True,
            "operational_task_templates_collection_enabled": True,
            "operational_task_dependencies_collection_enabled": True,
            "operational_task_automation_rules_collection_enabled": True,
            "operational_task_automation_runs_collection_enabled": True,
            "platform_task_automation_governance_enabled": True,
            "agency_task_automation_workspace_enabled": True,
            "existing_task_system_preserved": True,
            "request_tasks_reused": True,
            "safe_automatic_task_creation_enabled": True,
            "idempotent_task_generation_enabled": True,
            "dependency_blocking_enabled": True,
            "dependency_unblocking_enabled": True,
            "work_queue_integration_enabled": True,
            "workflow_event_integration_enabled": True,
            "sla_due_date_integration_enabled": True,
            "audit_run_records_enabled": True,
            "manual_retry_enabled": True,
            "arbitrary_code_execution_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "unbounded_automation_disabled": True,
            "agency_isolation_enforced": True,
            "metadata_only": True,
            "human_authority_final": True,
            "task_template_statuses": TASK_TEMPLATE_STATUSES,
            "task_dependency_types": TASK_DEPENDENCY_TYPES,
            "task_dependency_statuses": TASK_DEPENDENCY_STATUSES,
            "task_automation_rule_statuses": TASK_AUTOMATION_RULE_STATUSES,
            "task_automation_run_statuses": TASK_AUTOMATION_RUN_STATUSES,
            "task_automation_trigger_events": TASK_AUTOMATION_TRIGGER_EVENTS,
            "safe_task_template_count": len(OPERATIONAL_SAFE_TASK_TEMPLATES),
            "default_task_automation_rule_count": len(OPERATIONAL_DEFAULT_TASK_AUTOMATION_RULES),
            "operational_task_template_count": len(operational_task_template_records),
            "operational_task_dependency_count": len(operational_task_dependency_records),
            "operational_task_automation_rule_count": len(operational_task_automation_rule_records),
            "operational_task_automation_run_count": len(operational_task_automation_run_records),
            "operational_task_dependency_blocked_count": operational_task_dependency_blocked_count,
            "operational_task_dependency_satisfied_count": operational_task_dependency_satisfied_count,
            "operational_task_automation_created_task_count": operational_task_automation_created_task_count,
            "operational_task_automation_skipped_task_count": operational_task_automation_skipped_task_count,
            "operational_task_template_status_counts": operational_task_template_status_counts,
            "operational_task_dependency_status_counts": operational_task_dependency_status_counts,
            "operational_task_automation_rule_status_counts": operational_task_automation_rule_status_counts,
            "operational_task_automation_run_status_counts": operational_task_automation_run_status_counts,
            "operational_task_automation_trigger_counts": operational_task_automation_trigger_counts,
            "readiness_required": False,
            "diagnostic": "Phase 54.4 adds metadata-only task automation and dependency orchestration. It reuses request tasks, records safe task templates/rules/runs, links predecessor and successor task dependencies, refreshes the canonical work queue, and records workflow metadata without arbitrary code execution, background workers, provider integrations, AI, messaging, or operational execution.",
        },
        "request_to_trip_operational_conversion_foundation": {
            "request_to_trip_operational_conversion_enabled": True,
            "request_trip_conversion_plans_collection_enabled": True,
            "request_trip_conversion_runs_collection_enabled": True,
            "request_trip_entity_mappings_collection_enabled": True,
            "request_trip_conversion_issues_collection_enabled": True,
            "agency_request_trip_conversion_workspace_enabled": True,
            "platform_request_trip_conversion_diagnostics_enabled": True,
            "conversion_preview_enabled": True,
            "critical_validation_enabled": True,
            "missing_data_warning_enabled": True,
            "safe_warning_conversion_enabled": True,
            "new_trip_creation_enabled": True,
            "explicit_existing_trip_attachment_enabled": True,
            "idempotency_enabled": True,
            "safe_retry_enabled": True,
            "source_request_snapshot_preservation_enabled": True,
            "request_remains_immutable_intake_origin": True,
            "trip_becomes_downstream_operational_shell": True,
            "request_id_as_trip_id_forbidden": True,
            "segment_mapping_enabled": True,
            "passenger_mapping_enabled": True,
            "service_requirement_carry_forward_enabled": True,
            "pet_segment_scope_carry_forward_enabled": True,
            "special_item_segment_scope_carry_forward_enabled": True,
            "linked_offer_carry_forward_enabled": True,
            "workflow_start_metadata_enabled": True,
            "task_generation_integration_enabled": True,
            "deadline_generation_integration_enabled": True,
            "timeline_event_integration_enabled": True,
            "agency_isolation_enforced": True,
            "metadata_only": True,
            "booking_execution_disabled": True,
            "ticketing_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "automatic_production_seeding_disabled": True,
            "human_authority_final": True,
            "conversion_modes": CONVERSION_MODES,
            "conversion_plan_statuses": CONVERSION_PLAN_STATUSES,
            "conversion_run_statuses": CONVERSION_RUN_STATUSES,
            "conversion_mapping_types": CONVERSION_MAPPING_TYPES,
            "conversion_issue_types": CONVERSION_ISSUE_TYPES,
            "request_trip_conversion_plan_count": len(request_trip_conversion_plan_records),
            "request_trip_conversion_run_count": len(request_trip_conversion_run_records),
            "request_trip_entity_mapping_count": len(request_trip_entity_mapping_records),
            "request_trip_conversion_issue_count": len(request_trip_conversion_issue_records),
            "request_trip_conversion_warning_count": request_trip_conversion_warning_count,
            "request_trip_conversion_critical_issue_count": request_trip_conversion_critical_issue_count,
            "request_trip_conversion_plan_status_counts": request_trip_conversion_plan_status_counts,
            "request_trip_conversion_run_status_counts": request_trip_conversion_run_status_counts,
            "request_trip_conversion_mapping_type_counts": request_trip_conversion_mapping_type_counts,
            "request_trip_conversion_issue_type_counts": request_trip_conversion_issue_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 54.5 adds the metadata-only request-to-trip operational conversion foundation. It previews, validates, safely executes, maps, and audits request intake conversion into a downstream trip shell while preserving the request as immutable intake origin, never using request id as trip id, and recording workflow, task, deadline, and timeline metadata without booking, ticketing, provider calls, AI, workers, seeding, or external execution.",
        },
        "offer_to_booking_handoff_readiness_foundation": {
            "offer_to_booking_handoff_enabled": True,
            "offer_booking_handoffs_collection_enabled": True,
            "offer_booking_handoff_checks_collection_enabled": True,
            "offer_booking_handoff_mappings_collection_enabled": True,
            "booking_execution_instructions_collection_enabled": True,
            "agency_booking_handoff_workspace_enabled": True,
            "platform_booking_handoff_diagnostics_enabled": True,
            "accepted_offer_snapshot_usage_enabled": True,
            "mutable_offer_reconstruction_disabled": True,
            "booking_readiness_package_reuse_enabled": True,
            "readiness_checklist_enabled": True,
            "blocker_warning_readiness_states_enabled": True,
            "passenger_mapping_enabled": True,
            "segment_mapping_enabled": True,
            "service_mapping_enabled": True,
            "document_approval_mapping_enabled": True,
            "pricing_trace_preservation_enabled": True,
            "policy_trace_preservation_enabled": True,
            "internal_client_trace_separation_enabled": True,
            "booking_instruction_metadata_enabled": True,
            "manual_booking_path_supported": True,
            "imported_booking_path_supported": True,
            "duplicate_handoff_prevention_enabled": True,
            "booking_workspace_link_creation_enabled": True,
            "workflow_integration_enabled": True,
            "work_queue_integration_enabled": True,
            "task_automation_integration_enabled": True,
            "deadline_integration_enabled": True,
            "timeline_integration_enabled": True,
            "agency_isolation_enforced": True,
            "metadata_only": True,
            "booking_execution_disabled": True,
            "provider_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "payment_processing_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "human_authority_final": True,
            "handoff_statuses": HANDOFF_STATUSES,
            "handoff_check_statuses": HANDOFF_CHECK_STATUSES,
            "handoff_mapping_types": HANDOFF_MAPPING_TYPES,
            "booking_modes": OFFER_BOOKING_MODES,
            "booking_instruction_types": BOOKING_INSTRUCTION_TYPES,
            "offer_booking_handoff_count": len(offer_booking_handoff_records),
            "offer_booking_handoff_check_count": len(offer_booking_handoff_check_records),
            "offer_booking_handoff_mapping_count": len(offer_booking_handoff_mapping_records),
            "booking_execution_instruction_count": len(booking_execution_instruction_records),
            "offer_booking_handoff_status_counts": offer_booking_handoff_status_counts,
            "offer_booking_handoff_check_status_counts": offer_booking_handoff_check_status_counts,
            "offer_booking_handoff_mapping_type_counts": offer_booking_handoff_mapping_type_counts,
            "offer_booking_handoff_booking_mode_counts": offer_booking_handoff_booking_mode_counts,
            "booking_execution_instruction_type_counts": booking_execution_instruction_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 54.6 adds a metadata-only offer-to-booking handoff readiness foundation. It consumes frozen accepted-offer snapshots and existing booking readiness packages, records checks, blockers, warnings, mappings, and booking instructions, and can safely create/link a booking workspace through the existing readiness path without reconstructing mutable offer data, booking execution, provider calls, ticketing, payments, AI, workers, or external automation.",
        },
        "servicing_after_sales_workflow_foundation": {
            "servicing_after_sales_workflow_enabled": True,
            "after_sales_cases_collection_enabled": True,
            "after_sales_case_items_collection_enabled": True,
            "after_sales_decisions_collection_enabled": True,
            "after_sales_financial_impacts_collection_enabled": True,
            "after_sales_resolutions_collection_enabled": True,
            "after_sales_communication_records_collection_enabled": True,
            "agency_after_sales_workspace_enabled": True,
            "platform_after_sales_governance_diagnostics_enabled": True,
            "unified_case_types_supported": True,
            "impact_scope_across_trip_booking_ticket_emd_passenger_segment_enabled": True,
            "coupon_status_awareness_enabled": True,
            "financial_placeholders_enabled": True,
            "residual_value_metadata_enabled": True,
            "penalty_metadata_enabled": True,
            "fare_difference_metadata_enabled": True,
            "service_fee_metadata_enabled": True,
            "refundability_metadata_enabled": True,
            "document_requirement_metadata_enabled": True,
            "supplier_communication_metadata_enabled": True,
            "client_approval_guard_enabled": True,
            "generated_advice_metadata_enabled": True,
            "internal_client_message_separation_enabled": True,
            "workflow_integration_enabled": True,
            "work_queue_integration_enabled": True,
            "task_automation_integration_enabled": True,
            "deadline_integration_enabled": True,
            "timeline_integration_enabled": True,
            "agency_isolation_enforced": True,
            "metadata_only": True,
            "ticket_mutation_disabled": True,
            "emd_mutation_disabled": True,
            "financial_commitment_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "human_authority_final": True,
            "case_statuses": AFTER_SALES_CASE_STATUSES,
            "case_types": AFTER_SALES_CASE_TYPES,
            "decision_statuses": AFTER_SALES_DECISION_STATUSES,
            "financial_impact_types": AFTER_SALES_FINANCIAL_IMPACT_TYPES,
            "resolution_statuses": AFTER_SALES_RESOLUTION_STATUSES,
            "communication_types": AFTER_SALES_COMMUNICATION_TYPES,
            "after_sales_case_count": len(after_sales_case_records),
            "after_sales_case_item_count": len(after_sales_case_item_records),
            "after_sales_decision_count": len(after_sales_decision_records),
            "after_sales_financial_impact_count": len(after_sales_financial_impact_records),
            "after_sales_resolution_count": len(after_sales_resolution_records),
            "after_sales_communication_record_count": len(after_sales_communication_record_records),
            "after_sales_case_status_counts": after_sales_case_status_counts,
            "after_sales_case_type_counts": after_sales_case_type_counts,
            "after_sales_decision_status_counts": after_sales_decision_status_counts,
            "after_sales_financial_impact_type_counts": after_sales_financial_impact_type_counts,
            "after_sales_resolution_status_counts": after_sales_resolution_status_counts,
            "after_sales_communication_type_counts": after_sales_communication_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 54.7 adds the metadata-only servicing and after-sales workflow foundation. It records unified after-sales cases, affected item links, decisions, financial impact placeholders, resolutions, and communication metadata for changes, cancellations, refunds, exchanges, claims, amendments, and disruptions while reusing existing ticket, EMD, document, timeline, task, SLA, queue, workflow, and change/exchange foundations. It does not mutate tickets or EMDs, commit money, execute providers, call external APIs, send messages, run AI, or automate operational execution.",
        },
        "operations_command_center_foundation": {
            "operations_command_center_enabled": True,
            "agency_operations_command_center_enabled": True,
            "platform_operations_governance_enabled": True,
            "aggregation_only": True,
            "duplicate_operational_data_disabled": True,
            "current_operational_workload_enabled": True,
            "unassigned_work_enabled": True,
            "overdue_due_soon_enabled": True,
            "critical_blockers_enabled": True,
            "requests_awaiting_triage_enabled": True,
            "offers_awaiting_action_enabled": True,
            "accepted_offers_awaiting_booking_enabled": True,
            "bookings_awaiting_ticketing_enabled": True,
            "service_approvals_documents_enabled": True,
            "departure_horizon_enabled": True,
            "disrupted_trips_enabled": True,
            "after_sales_cases_enabled": True,
            "knowledge_manual_review_enabled": True,
            "payment_invoice_blockers_enabled": True,
            "pilot_readiness_issues_enabled": True,
            "team_workload_enabled": True,
            "dashboard_view_enabled": True,
            "queue_view_enabled": True,
            "kanban_view_enabled": True,
            "calendar_view_enabled": True,
            "timeline_view_enabled": True,
            "exception_list_enabled": True,
            "exception_list_view_enabled": True,
            "agent_team_workload_view_enabled": True,
            "workload_view_enabled": True,
            "urgency_ranked_feed_enabled": True,
            "calendar_generation_enabled": True,
            "kanban_lanes_from_workflow_state_enabled": True,
            "kanban_moves_require_workflow_transitions": True,
            "kanban_guard_enforcement_enabled": True,
            "uncontrolled_drag_and_drop_disabled": True,
            "safe_action_links_enabled": True,
            "queue_integration_enabled": True,
            "sla_integration_enabled": True,
            "workflow_integration_enabled": True,
            "after_sales_integration_enabled": True,
            "agency_isolation_enforced": True,
            "metadata_only": True,
            "read_only_dashboard": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "status_mutation_disabled": True,
            "human_authority_final": True,
            "view_types": OPERATIONS_COMMAND_CENTER_VIEW_TYPES,
            "kpis": operations_command_center_snapshot.get("kpis") or {},
            "feed_count": len(operations_command_center_snapshot.get("queue") or []),
            "operational_feed_count": len(operations_command_center_snapshot.get("queue") or []),
            "calendar_event_count": len((operations_command_center_snapshot.get("calendar") or {}).get("events") or []),
            "kanban_lane_count": len((operations_command_center_snapshot.get("kanban") or {}).get("lanes") or []),
            "workload_bucket_count": len(operations_command_center_snapshot.get("workload") or []),
            "workload_summary_count": len(operations_command_center_snapshot.get("workload") or []),
            "exception_count": len(operations_command_center_snapshot.get("exceptions") or []),
            "readiness_required": False,
            "diagnostic": "Phase 54.8 adds the metadata-only Operations Command Center foundation. It aggregates existing work queue, SLA, workflow, request, offer, booking, ticketing, service approval, document, departure, disruption, after-sales, knowledge/manual-review, payment/invoice, pilot-readiness, and team workload metadata into dashboard, queue, kanban, calendar, timeline, exception, and workload views without duplicating operational records, uncontrolled drag-and-drop, provider execution, AI, background workers, status mutation, or automatic operational execution.",
        },
        "end_to_end_operational_workflow_maturity_foundation": {
            "end_to_end_operational_workflow_maturity_enabled": True,
            "platform_workflow_maturity_enabled": True,
            "agency_workflow_maturity_enabled": True,
            "epic_54_consolidation_enabled": True,
            "phase_53_readiness_patterns_reused": True,
            "new_parallel_subsystem_disabled": True,
            "new_maturity_collection_disabled": True,
            "workflow_linkage_assessment_enabled": True,
            "assignment_readiness_assessment_enabled": True,
            "sla_readiness_assessment_enabled": True,
            "task_dependency_readiness_assessment_enabled": True,
            "request_to_trip_conversion_readiness_assessment_enabled": True,
            "offer_to_booking_readiness_assessment_enabled": True,
            "servicing_readiness_assessment_enabled": True,
            "command_center_visibility_assessment_enabled": True,
            "audit_completeness_assessment_enabled": True,
            "client_internal_message_separation_assessment_enabled": True,
            "agency_isolation_assessment_enabled": True,
            "production_safety_assessment_enabled": True,
            "deterministic_scoring_enabled": True,
            "critical_blocker_behavior_enabled": True,
            "golden_path_stage_results_enabled": True,
            "blocked_and_resumed_flow_enabled": True,
            "isolated_test_templates_enabled": True,
            "isolated_test_runs_enabled": True,
            "test_runs_persisted": False,
            "test_records_become_production_records": False,
            "automatic_production_seeding_disabled": True,
            "destructive_reset_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_booking_disabled": True,
            "automatic_ticketing_disabled": True,
            "automatic_emd_issuance_disabled": True,
            "automatic_financial_commitment_disabled": True,
            "human_authority_final": True,
            "maturity_dimensions": OPERATIONAL_MATURITY_DIMENSIONS,
            "golden_path_stages": OPERATIONAL_MATURITY_GOLDEN_PATH_STAGES,
            "test_template_count": len(OPERATIONAL_MATURITY_TEST_CASE_TEMPLATES),
            "maturity_score": operational_workflow_maturity_snapshot.get("maturity_score"),
            "maturity_status": operational_workflow_maturity_snapshot.get("maturity_status"),
            "module_scores": operational_workflow_maturity_snapshot.get("module_scores") or [],
            "failing_stage_count": len(operational_workflow_maturity_snapshot.get("failing_stages") or []),
            "blocker_count": len(operational_workflow_maturity_snapshot.get("blocker_register") or []),
            "recent_workflow_error_count": len(operational_workflow_maturity_snapshot.get("recent_workflow_errors") or []),
            "operational_coverage": operational_workflow_maturity_snapshot.get("operational_coverage") or {},
            "readiness_required": False,
            "metadata_only": True,
            "diagnostic": "Phase 54.9 completes Epic 54 with a deterministic aggregate maturity assessment and isolated golden-path diagnostics over the existing workflow, queue, SLA, task dependency, request-to-trip conversion, offer-to-booking handoff, after-sales, command-center, timeline, and Phase 53 pilot-readiness foundations. It creates no parallel subsystem or production operational records.",
        },
        "airline_master_profile_intelligence_foundation": {
            "capability_phase": AIRLINE_MASTER_PROFILE_CAPABILITY_PHASE,
            "airline_master_profile_intelligence_enabled": True,
            "canonical_airline_identity_reused": True,
            "duplicate_airline_catalogue_disabled": True,
            "platform_profile_governance_enabled": True,
            "agency_approved_published_read_only_enabled": True,
            "alias_resolution_enabled": True,
            "duplicate_candidate_review_enabled": True,
            "airline_relationships_enabled": True,
            "hub_assignments_enabled": True,
            "operational_classification_enabled": True,
            "distribution_summary_enabled": True,
            "service_desk_summary_enabled": True,
            "profile_completeness_scoring_enabled": True,
            "profile_confidence_scoring_enabled": True,
            "missing_intelligence_detection_enabled": True,
            "effective_dating_enabled": True,
            "revision_history_enabled": True,
            "source_evidence_links_enabled": True,
            "conflicting_evidence_preserved": True,
            "operational_summary_enabled": True,
            "agency_safe_projection_enabled": True,
            "client_safe_minimal_identity_enabled": True,
            "internal_notes_restricted": True,
            "automatic_production_seeding_disabled": True,
            "external_api_calls_disabled": True,
            "provider_execution_disabled": True,
            "ai_disabled": True,
            "metadata_only": True,
            **airline_master_profile_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.1 enriches the existing canonical airline_profiles identity with governed aliases, relationships, hubs, operational classification, distribution, service desks, evidence, confidence, effective dates, and revisions. Agency consumption is read-only and limited to approved or published metadata; internal notes and restricted evidence references are excluded.",
        },
        "airline_policy_evidence_source_governance_foundation": {
            "capability_phase": AIRLINE_EVIDENCE_CAPABILITY_PHASE,
            "airline_policy_evidence_source_governance_enabled": True,
            "canonical_evidence_governance_enabled": True,
            "raw_source_truth_preserved": True,
            "normalized_assertions_separate": True,
            "source_registry_enabled": True,
            "artifact_registration_enabled": True,
            "assertion_registration_enabled": True,
            "knowledge_object_linking_enabled": True,
            "conflict_detection_enabled": True,
            "conflicting_sources_preserved": True,
            "conflict_review_resolution_enabled": True,
            "supersede_without_destroying_enabled": True,
            "source_authority_assessment_enabled": True,
            "confidence_calculation_enabled": True,
            "freshness_assessment_enabled": True,
            "unsupported_knowledge_detection_enabled": True,
            "evidence_trace_enabled": True,
            "agency_safe_evidence_summary_enabled": True,
            "restricted_evidence_protected": True,
            "platform_evidence_governance_enabled": True,
            "agency_evidence_read_only_enabled": True,
            "physical_evidence_deletion_disabled": True,
            "automatic_production_seeding_disabled": True,
            "automatic_extraction_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "provider_execution_disabled": True,
            "ai_disabled": True,
            "metadata_only": True,
            **airline_evidence_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.2 governs airline evidence sources, artifacts, assertions, links, reviews, conflicts, freshness, and access classifications around existing raw acquisition and policy source records. Conflicts and superseded evidence remain retained. Agencies receive only approved, agency-visible summaries without restricted URLs, attachments, internal notes, or raw source locations.",
        },
        "airline_knowledge_versioning_change_detection_foundation": {
            "capability_phase": AIRLINE_KNOWLEDGE_VERSIONING_CAPABILITY_PHASE,
            "airline_knowledge_versioning_change_detection_enabled": True,
            "canonical_airline_knowledge_version_reused": True,
            "immutable_version_items_enabled": True,
            "structured_scalar_diff_enabled": True,
            "structured_nested_diff_enabled": True,
            "structured_list_diff_enabled": True,
            "formula_change_detection_enabled": True,
            "effective_date_change_detection_enabled": True,
            "operational_severity_categorization_enabled": True,
            "evidence_source_causation_enabled": True,
            "published_release_trace_enabled": True,
            "impact_assessment_enabled": True,
            "re_qa_request_enabled": True,
            "republish_request_enabled": True,
            "historical_snapshot_immutability_enabled": True,
            "historical_snapshot_mutation_disabled": True,
            "agency_published_updates_read_only": True,
            "unpublished_draft_agency_visibility_disabled": True,
            "automatic_operational_mutation_disabled": True,
            "automatic_republication_disabled": True,
            "metadata_only": True,
            **airline_knowledge_versioning_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.3 reuses the canonical airline_knowledge_versions governance envelope and adds immutable object snapshots, deterministic field-level changes, impact assessments, reviews, and explicit re-QA or republish requests. Historical offers, recommendations, bookings, trips, and published snapshots are identified for review but never mutated automatically. Agencies see only published or effective update summaries.",
        },
        "airline_service_coverage_gap_management_foundation": {
            "capability_phase": AIRLINE_SERVICE_COVERAGE_CAPABILITY_PHASE,
            "airline_service_coverage_gap_management_enabled": True,
            "airline_service_coverage_profiles_collection_enabled": True,
            "airline_service_coverage_cells_collection_enabled": True,
            "airline_knowledge_gaps_collection_enabled": True,
            "airline_coverage_targets_collection_enabled": True,
            "airline_coverage_assessments_collection_enabled": True,
            "airline_coverage_remediation_plans_collection_enabled": True,
            "airline_service_matrix_enabled": True,
            "coverage_dimension_filtering_enabled": True,
            "deterministic_completeness_scoring_enabled": True,
            "deterministic_confidence_scoring_enabled": True,
            "deterministic_freshness_scoring_enabled": True,
            "deterministic_test_coverage_scoring_enabled": True,
            "deterministic_publication_readiness_scoring_enabled": True,
            "deterministic_operational_usability_scoring_enabled": True,
            "critical_gap_operational_ready_guard_enabled": True,
            "stale_evidence_gap_detection_enabled": True,
            "unresolved_conflict_gap_detection_enabled": True,
            "knowledge_population_toolkit_integration_enabled": True,
            "pilot_readiness_integration_enabled": True,
            "knowledge_qa_integration_enabled": True,
            "publishing_integration_enabled": True,
            "scenario_testing_integration_enabled": True,
            "capability_matrix_integration_enabled": True,
            "recommendation_hint_integration_enabled": True,
            "agency_published_coverage_read_only": True,
            "unpublished_draft_agency_visibility_disabled": True,
            "restricted_evidence_protected": True,
            "automatic_publication_disabled": True,
            "automatic_recommendation_disabled": True,
            "offer_intelligence_mutation_disabled": True,
            "metadata_only": True,
            **airline_service_coverage_gap_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.4 projects existing policy, pricing, rule, evidence, QA, publication, scenario, capability, toolkit, pilot-readiness, and recommendation metadata into deterministic airline-by-service coverage cells. Critical gaps prevent operational-ready status. Agency views contain only published coverage and sanitized missing-or-unknown warnings; assessments never publish knowledge or mutate offers and recommendations.",
        },
        "airline_distribution_pss_gds_ndc_capability_intelligence_foundation": {
            "capability_phase": AIRLINE_DISTRIBUTION_CAPABILITY_PHASE,
            "airline_distribution_pss_gds_ndc_capability_intelligence_enabled": True,
            "airline_distribution_channels_collection_enabled": True,
            "airline_distribution_capabilities_collection_enabled": True,
            "airline_pss_profiles_collection_enabled": True,
            "airline_gds_participations_collection_enabled": True,
            "airline_ndc_capabilities_collection_enabled": True,
            "airline_fulfillment_capabilities_collection_enabled": True,
            "airline_servicing_capabilities_collection_enabled": True,
            "airline_distribution_restrictions_collection_enabled": True,
            "airline_distribution_evidence_links_collection_enabled": True,
            "distribution_channel_matrix_enabled": True,
            "pss_host_context_enabled": True,
            "gds_participation_intelligence_enabled": True,
            "ndc_capability_intelligence_enabled": True,
            "shopping_capability_intelligence_enabled": True,
            "booking_capability_intelligence_enabled": True,
            "fulfillment_capability_intelligence_enabled": True,
            "servicing_capability_intelligence_enabled": True,
            "provider_channel_distinction_enabled": True,
            "documented_configured_sandbox_production_distinction_enabled": True,
            "unknown_capability_handling_enabled": True,
            "restriction_and_fallback_metadata_enabled": True,
            "evidence_governance_integration_enabled": True,
            "knowledge_versioning_integration_enabled": True,
            "service_coverage_integration_enabled": True,
            "booking_handoff_planning_integration_enabled": True,
            "canonical_legacy_distribution_context_reused": True,
            "agency_published_read_only": True,
            "unpublished_draft_agency_visibility_disabled": True,
            "credential_storage_disabled": True,
            "planning_record_does_not_imply_live_capability": True,
            "live_provider_connectivity_disabled": True,
            "provider_execution_disabled": True,
            "metadata_only": True,
            **airline_distribution_capability_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.5 adds governed distribution-channel, PSS, GDS, NDC, fulfillment, servicing, restriction, and evidence-link intelligence around existing broad distribution records. Provider stage is recorded separately from capability status, credentials are prohibited, and every agency view is published and read-only. Booking handoff consumes advisory planning snapshots only; no provider connectivity or execution is introduced.",
        },
        "interline_codeshare_operating_carrier_intelligence_foundation": {
            "capability_phase": INTERLINE_CODESHARE_CAPABILITY_PHASE,
            "interline_codeshare_operating_carrier_intelligence_enabled": True,
            "airline_carrier_relationships_collection_enabled": True,
            "airline_interline_agreement_profiles_collection_enabled": True,
            "airline_codeshare_rules_collection_enabled": True,
            "airline_operating_carrier_policy_rules_collection_enabled": True,
            "airline_validating_carrier_rules_collection_enabled": True,
            "airline_through_check_rules_collection_enabled": True,
            "airline_baggage_responsibility_rules_collection_enabled": True,
            "airline_service_responsibility_rules_collection_enabled": True,
            "airline_interline_emd_rules_collection_enabled": True,
            "carrier_role_mapping_enabled": True,
            "policy_ownership_intelligence_enabled": True,
            "ssr_responsibility_intelligence_enabled": True,
            "emd_responsibility_intelligence_enabled": True,
            "baggage_responsibility_intelligence_enabled": True,
            "through_check_and_service_continuity_enabled": True,
            "multi_segment_advisory_evaluation_enabled": True,
            "unknown_state_preserved": True,
            "unsupported_certainty_disabled": True,
            "manual_review_requirements_enabled": True,
            "legacy_interline_truth_preserved": True,
            "operational_constraint_integration_enabled": True,
            "feasibility_integration_enabled": True,
            "recommendation_integration_enabled": True,
            "offer_intelligence_integration_enabled": True,
            "agency_published_read_only": True,
            "provider_connectivity_disabled": True,
            "booking_ticket_emd_execution_disabled": True,
            "metadata_only": True,
            **interline_codeshare_intelligence_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.6 adds governed carrier relationships and responsibility rules for interline, codeshare, operating, validating, ticketing, plating, handling, baggage, through-check, special-service, and EMD contexts. It produces advisory itinerary responsibility traces with explicit unknown, unsupported, and manual-review states; it preserves legacy source truth and does not connect to or execute provider systems.",
        },
        "airline_fare_family_rbd_baggage_brand_intelligence_foundation": {
            "capability_phase": AIRLINE_FARE_BRAND_CAPABILITY_PHASE,
            "airline_fare_family_rbd_baggage_brand_intelligence_enabled": True,
            "canonical_airline_fare_families_collection_reused": True,
            "airline_fare_brand_attributes_collection_enabled": True,
            "airline_booking_class_mappings_collection_enabled": True,
            "airline_baggage_allowance_rules_collection_enabled": True,
            "airline_baggage_exceptions_collection_enabled": True,
            "airline_commercial_bundles_collection_enabled": True,
            "airline_fare_family_evidence_links_collection_enabled": True,
            "airline_brand_comparison_profiles_collection_enabled": True,
            "fare_family_hierarchy_enabled": True,
            "rbd_mapping_with_unknown_states_enabled": True,
            "baggage_context_resolution_enabled": True,
            "interline_baggage_uncertainty_enabled": True,
            "commercial_attribute_comparison_enabled": True,
            "client_safe_labels_enabled": True,
            "internal_evidence_separation_enabled": True,
            "evidence_governance_integration_enabled": True,
            "knowledge_versioning_integration_enabled": True,
            "offer_builder_integration_enabled": True,
            "agency_published_read_only": True,
            "live_availability_disabled": True,
            "fare_pricing_engine_disabled": True,
            "provider_connectivity_disabled": True,
            "booking_ticketing_execution_disabled": True,
            "metadata_only": True,
            **airline_fare_brand_intelligence_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.7 adds governed fare-family hierarchy, RBD mapping, commercial attributes, baggage allowances and exceptions, comparison profiles, and offer-builder projections. Unknown and interline contexts remain explicit manual-review states. It neither calculates live fares nor invents availability, and it does not connect to or execute providers.",
        },
        "airline_contact_communication_intelligence_foundation": {
            "capability_phase": AIRLINE_CONTACT_CAPABILITY_PHASE,
            "airline_contact_communication_intelligence_enabled": True,
            "canonical_airline_contacts_collection_reused": True,
            "airline_contact_channels_collection_enabled": True,
            "airline_contact_scopes_collection_enabled": True,
            "airline_contact_availabilities_collection_enabled": True,
            "airline_contact_escalation_paths_collection_enabled": True,
            "airline_communication_templates_collection_enabled": True,
            "airline_communication_requirements_collection_enabled": True,
            "airline_contact_verifications_collection_enabled": True,
            "airline_supplier_interactions_collection_enabled": True,
            "desk_and_scope_matching_enabled": True,
            "timezone_operating_hours_enabled": True,
            "governed_template_separation_enabled": True,
            "required_information_checklists_enabled": True,
            "verification_and_freshness_enabled": True,
            "evidence_reference_linkage_enabled": True,
            "manual_interaction_logging_enabled": True,
            "operational_timeline_integration_enabled": True,
            "workflow_after_sales_task_sla_linkage_enabled": True,
            "agency_published_directory_enabled": True,
            "restricted_contact_protection_enabled": True,
            "private_credentials_disabled": True,
            "secret_storage_disabled": True,
            "external_messaging_disabled": True,
            "automatic_escalation_disabled": True,
            "provider_connectivity_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "metadata_only": True,
            **airline_contact_communication_intelligence_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.8 adds governed airline and supplier desk, channel, scope, operating-hours, escalation, message-template, requirement, verification, and interaction-history intelligence. Internal instructions, supplier messages, and client status text remain separate; no credentials are stored and no message, escalation, provider action, or background process is executed.",
        },
        "airline_intelligence_scale_release_readiness_foundation": {
            "capability_phase": AIRLINE_INTELLIGENCE_READINESS_CAPABILITY_PHASE,
            "airline_intelligence_scale_release_readiness_enabled": True,
            "epic_55_canonical_sources_reused": True,
            "readiness_profiles_collection_enabled": True,
            "readiness_assessments_collection_enabled": True,
            "readiness_checks_collection_enabled": True,
            "release_candidates_collection_enabled": True,
            "release_gates_collection_enabled": True,
            "release_decisions_collection_enabled": True,
            "population_waves_collection_enabled": True,
            "scale_issues_collection_enabled": True,
            "eighteen_readiness_dimensions_enabled": True,
            "eleven_deterministic_release_gates_enabled": True,
            "critical_blocker_guard_enabled": True,
            "decision_audit_enabled": True,
            "population_wave_tracking_enabled": True,
            "agency_release_assignment_enabled": True,
            "rollback_reference_gate_enabled": True,
            "client_internal_message_separation_enabled": True,
            "agency_released_read_only_projection_enabled": True,
            "draft_governance_agency_visibility_disabled": True,
            "automatic_publication_disabled": True,
            "automatic_production_seeding_disabled": True,
            "provider_connectivity_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "metadata_only": True,
            **airline_intelligence_scale_readiness_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 55.9 consolidates Epic 55 knowledge, evidence, coverage, capability, QA, publication, and agency-consumption metadata into deterministic scale-readiness assessments and human-controlled release gates. It does not seed production, publish automatically, call providers, or mutate historical knowledge snapshots.",
        },
        "canonical_journey_itinerary_representation_foundation": {
            "capability_phase": CANONICAL_JOURNEY_CAPABILITY_PHASE,
            "canonical_journey_itinerary_representation_enabled": True,
            "canonical_operational_entities_reused": True,
            "duplicate_operational_entities_disabled": True,
            "journey_representation_collection_enabled": True,
            "itinerary_option_representation_enabled": True,
            "journey_leg_representation_enabled": True,
            "journey_segment_projection_enabled": True,
            "journey_connection_representation_enabled": True,
            "journey_fare_brand_presentation_enabled": True,
            "journey_service_presentation_enabled": True,
            "journey_presentation_configuration_enabled": True,
            "immutable_journey_snapshots_enabled": True,
            "finalized_snapshot_mutation_disabled": True,
            "source_provenance_enabled": True,
            "trip_projection_enabled": True,
            "offer_projection_enabled": True,
            "booking_projection_enabled": True,
            "ticket_reference_enabled": True,
            "agency_isolation_enabled": True,
            "client_safe_projection_enabled": True,
            "live_availability_disabled": True,
            "live_pricing_disabled": True,
            "provider_connectivity_disabled": True,
            "external_api_calls_disabled": True,
            "automatic_publication_disabled": True,
            "metadata_only": True,
            **canonical_journey_itinerary_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 56.0 establishes the canonical journey and itinerary presentation layer while preserving Request, Trip, Offer, Booking, Ticket, EMD, Passenger, and canonical segment records as source truth. Projections retain provenance, finalized snapshots are immutable, and no live availability, pricing, provider connectivity, external calls, AI, background workers, or automatic publication is introduced.",
        },
        "journey_segment_authoring_intelligent_import_workspace_foundation": {
            "capability_phase": JOURNEY_AUTHORING_CAPABILITY_PHASE,
            **JourneySegmentAuthoringService(database).safety_flags(),
            **journey_segment_authoring_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 56.1 preserves immutable raw inputs, normalizes editable segment drafts with field provenance, performs deterministic timezone-aware calculations, and applies only through canonical Phase 56.0 Journey records. It performs no live schedule or pricing lookup, provider call, scraping, AI inference, background work, or automatic publication.",
        },
        "journey_option_fare_brand_composition_workspace_foundation": {
            "capability_phase": JOURNEY_COMPOSITION_CAPABILITY_PHASE,
            **JourneyOptionFareBrandCompositionService(database).safety_flags(),
            **journey_option_composition_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 56.2 composes canonical Journey segment projections, governed fare-brand intelligence, explicit agency commercial values, and advisory service assessments into offer-ready itinerary alternatives. It retrieves no live fares or availability, contacts no provider, publishes nothing automatically, and performs no booking, ticketing, or EMD execution.",
        },
        "journey_comparison_client_presentation_foundation": {
            "capability_phase": JOURNEY_PRESENTATION_CAPABILITY_PHASE,
            **JourneyComparisonClientPresentationService(database).safety_flags(),
            **journey_comparison_presentation_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 56.3 converts existing canonical Journey and composition data into deterministic, client-safe itinerary and fare-brand comparisons with explicit operational suitability, unknown states, agent-controlled preference, immutable snapshots, and reviewable handoffs. It does not retrieve live fares or availability, publish offers, create public share links, send messages, or execute provider operations.",
        },
        "offer_delivery_client_interaction_foundation": {
            "capability_phase": OFFER_DELIVERY_CAPABILITY_PHASE,
            **OfferDeliveryClientInteractionService(database).safety_flags(),
            **offer_delivery_coverage,
            "readiness_required": False,
            "diagnostic": "Phase 56.4 enables controlled authenticated delivery and recipient-bound client decisions against immutable released presentation snapshots. It does not retrieve live fares or availability, connect to providers, publish anonymous links, process payments, create bookings, issue tickets or EMDs, send uncontrolled external messages, use AI, scrape, or run background workers.",
        },
        "phase_marker_regression_integrity_foundation": {
            "current_build_phase_centralized": True,
            "numeric_phase_comparison_enabled": True,
            "exact_phase_comparison_enabled": True,
            "invalid_phase_detection_enabled": True,
            "historical_minimum_phase_assertions_enabled": True,
            "capability_provenance_separated": True,
            "historical_provenance_preserved": True,
            "immutable_snapshot_phase_mutation_disabled": True,
            "readiness_required": False,
            "diagnostic": "Phase 56.5.1 centralizes current build metadata and gives historical smoke tests numeric minimum-phase semantics while preserving capability and immutable snapshot provenance.",
        },
        "legacy_regression_suite_migration": {
            **SMOKE_INVENTORY_SUMMARY,
            "legacy_runtime_exact_assertions_migrated": True,
            "exact_current_assertions_allowlisted": True,
            "historical_provenance_preserved": True,
            "product_behavior_changed": False,
            "readiness_required": False,
            "diagnostic": "Phase 56.5.2 inventories the complete smoke suite and migrates historical runtime phase checks to evidence-backed minimum semantics. Exact current-build ownership advances through one documented allowlisted release-registration smoke.",
        },
        "github_actions_continuous_integration_foundation": {
            **SMOKE_INVENTORY_SUMMARY,
            "fast_ci_workflow_enabled": True,
            "docker_ci_workflow_enabled": True,
            "focused_smoke_ci_workflow_enabled": True,
            "full_regression_workflow_enabled": True,
            "inventory_driven_ci_enabled": True,
            "production_import_validation_enabled": True,
            "frontend_build_validation_enabled": True,
            "backend_compile_validation_enabled": True,
            "current_phase_validation_enabled": True,
            "production_deployment_disabled": True,
            "production_secrets_required": False,
            "workflow_count": 4,
            "readiness_required": False,
            "diagnostic": "Phase 56.5.3 defines least-privilege GitHub Actions validation for static checks, production Docker imports, focused inventory smokes, and scheduled or manual full regression. CI never deploys or requires production credentials.",
        },
        "authentication_security_http_hardening_foundation": security_readiness_metadata(settings),
        "service_parameter_taxonomy_integration_foundation": {
            "service_parameter_taxonomy_integration_enabled": True,
            "service_parameter_taxonomies_collection_enabled": True,
            "platform_service_parameter_taxonomies_metadata_crud_enabled": True,
            "agency_service_parameter_taxonomies_metadata_crud_enabled": True,
            "platform_service_parameter_taxonomies_ui_enabled": True,
            "agency_service_parameter_taxonomies_ui_enabled": True,
            "measurable_service_parameters_enabled": True,
            "chapter_50_51_pipeline_integrated": True,
            "parameter_taxonomies_reusable": True,
            "supports_structured_knowledge_entry": True,
            "supports_future_evaluation_inputs": True,
            "policy_pricing_capability_constraints_procedures_separate": True,
            "capability_remains_separate_from_policy": True,
            "pricing_remains_separate_from_capability_and_policy": True,
            "passenger_assistance_parameters_enabled": True,
            "pets_animals_parameters_enabled": True,
            "special_items_baggage_parameters_enabled": True,
            "route_aircraft_cabin_parameters_enabled": True,
            "pricing_parameters_enabled": True,
            "reference_requirements_enabled": True,
            "knowledge_graph_links_enabled": True,
            "governance_metadata_enabled": True,
            "taxonomy_statuses": SERVICE_PARAMETER_TAXONOMY_STATUSES,
            "review_statuses": TAXONOMY_REVIEW_STATUSES,
            "approval_statuses": TAXONOMY_APPROVAL_STATUSES,
            "support_status_options": SUPPORT_STATUS_OPTIONS,
            "evaluation_status_options": EVALUATION_STATUS_OPTIONS,
            "restriction_status_options": RESTRICTION_STATUS_OPTIONS,
            "approval_status_options": APPROVAL_STATUS_OPTIONS,
            "pricing_units": PRICING_UNITS,
            "pricing_way_values": PRICING_WAY_VALUES,
            "pricing_route_types": PRICING_ROUTE_TYPES,
            "pricing_flight_types": PRICING_FLIGHT_TYPES,
            "pricing_fare_bundles": PRICING_FARE_BUNDLES,
            "pricing_categories": PRICING_CATEGORIES,
            "amount_types": AMOUNT_TYPES,
            "metadata_only": True,
            "standalone_policy_engine_disabled": True,
            "legacy_pricing_engine_disabled": True,
            "pocketbase_logic_disabled": True,
            "duplicate_operational_models_disabled": True,
            "live_rule_evaluation_disabled": True,
            "live_pricing_calculation_disabled": True,
            "recommendation_execution_disabled": True,
            "provider_integrations_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "human_authority_final": True,
            "service_parameter_taxonomy_count": service_parameter_taxonomy_count,
            "service_parameter_taxonomy_status_counts": service_parameter_taxonomy_status_counts,
            "service_parameter_taxonomy_review_status_counts": service_parameter_taxonomy_review_status_counts,
            "service_parameter_taxonomy_approval_status_counts": service_parameter_taxonomy_approval_status_counts,
            "service_parameter_taxonomy_service_code_count": service_parameter_taxonomy_service_code_count,
            "service_parameter_taxonomy_passenger_assistance_parameter_count": service_parameter_taxonomy_passenger_assistance_parameter_count,
            "service_parameter_taxonomy_pets_animals_parameter_count": service_parameter_taxonomy_pets_animals_parameter_count,
            "service_parameter_taxonomy_special_item_parameter_count": service_parameter_taxonomy_special_item_parameter_count,
            "service_parameter_taxonomy_route_aircraft_cabin_parameter_count": service_parameter_taxonomy_route_aircraft_cabin_parameter_count,
            "service_parameter_taxonomy_pricing_parameter_count": service_parameter_taxonomy_pricing_parameter_count,
            "service_parameter_taxonomy_reference_requirement_count": service_parameter_taxonomy_reference_requirement_count,
            "service_parameter_taxonomy_knowledge_graph_link_count": service_parameter_taxonomy_knowledge_graph_link_count,
            "readiness_required": False,
            "diagnostic": "Phase 51.1 integrates metadata-only Service Parameter Taxonomies for measurable fields reused across acquisition, constraints, capability, evaluation, feasibility, recommendation, offer intelligence, and operational intelligence cases. It does not copy legacy policy-card execution, evaluate rules, calculate prices, call providers, generate AI/LLM output, run workers, or automate recommendations. Human authority remains final.",
        },
        "request_segment_service_precision_foundation": {
            "request_segment_service_precision_enabled": True,
            "request_segment_service_scopes_collection_enabled": True,
            "platform_request_segment_services_metadata_crud_enabled": True,
            "agency_request_segment_services_metadata_crud_enabled": True,
            "platform_request_segment_services_ui_enabled": True,
            "agency_request_segment_services_ui_enabled": True,
            "segment_first_intake_enabled": True,
            "service_scope_requires_passenger_segment_service_context": True,
            "passenger_segment_service_scope_enabled": True,
            "pets_segment_scoped": True,
            "special_items_segment_scoped": True,
            "request_remains_intake": True,
            "trip_remains_operational_dossier": True,
            "never_use_travel_request_id_as_trip_id": True,
            "trip_conversion_metadata_only": True,
            "service_parameter_taxonomy_links_enabled": True,
            "operational_constraint_links_enabled": True,
            "capability_matrix_links_enabled": True,
            "operational_evaluation_links_enabled": True,
            "feasibility_links_enabled": True,
            "recommendation_links_enabled": True,
            "operational_flags_metadata_enabled": True,
            "readiness_metadata_enabled": True,
            "conversion_metadata_enabled": True,
            "request_snapshot_metadata_enabled": True,
            "decision_trace_metadata_enabled": True,
            "scope_statuses": REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES,
            "readiness_statuses": REQUEST_SEGMENT_SERVICE_READINESS_STATUSES,
            "requested_statuses": REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES,
            "metadata_only": True,
            "policy_evaluation_disabled": True,
            "pricing_calculation_disabled": True,
            "live_policy_review_disabled": True,
            "live_pricing_review_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "automatic_trip_conversion_disabled": True,
            "automatic_client_sending_disabled": True,
            "human_authority_final": True,
            "request_segment_service_scope_count": request_segment_service_scope_count,
            "request_segment_service_scope_status_counts": request_segment_service_scope_status_counts,
            "request_segment_service_readiness_status_counts": request_segment_service_readiness_status_counts,
            "request_segment_service_requested_status_counts": request_segment_service_requested_status_counts,
            "request_segment_service_operational_flag_counts": request_segment_service_operational_flag_counts,
            "request_segment_service_knowledge_link_counts": request_segment_service_knowledge_link_counts,
            "request_segment_service_pet_scope_count": request_segment_service_pet_scope_count,
            "request_segment_service_special_item_scope_count": request_segment_service_special_item_scope_count,
            "request_segment_service_converted_to_trip_count": request_segment_service_converted_to_trip_count,
            "request_segment_service_missing_field_count": request_segment_service_missing_field_count,
            "request_segment_service_missing_document_count": request_segment_service_missing_document_count,
            "request_segment_service_readiness_warning_count": request_segment_service_readiness_warning_count,
            "request_segment_service_readiness_blocker_count": request_segment_service_readiness_blocker_count,
            "request_segment_service_decision_trace_count": request_segment_service_decision_trace_count,
            "readiness_required": False,
            "diagnostic": "Phase 51.2 creates metadata-only Request Segment Service Scope records. It makes request intake segment-first by preserving passenger + segment + service precision, keeps pets and special items segment-scoped, leaves the request as intake and the trip as the operational dossier, and performs no policy evaluation, pricing calculation, booking, ticketing, provider integration, AI/LLM generation, background work, or automatic client sending. Human authority remains final.",
        },
        "client_passenger_master_workspace_foundation": {
            "client_passenger_master_workspace_enabled": True,
            "client_master_records_collection_enabled": True,
            "passenger_master_records_collection_enabled": True,
            "client_passenger_links_collection_enabled": True,
            "passenger_service_history_collection_enabled": True,
            "passenger_operational_preferences_collection_enabled": True,
            "passenger_known_documents_collection_enabled": True,
            "client_portal_access_profiles_collection_enabled": True,
            "registered_collections": CLIENT_PASSENGER_MASTER_COLLECTIONS,
            "platform_client_master_metadata_crud_enabled": True,
            "platform_passenger_master_metadata_crud_enabled": True,
            "agency_client_master_metadata_crud_enabled": True,
            "agency_passenger_master_metadata_crud_enabled": True,
            "platform_client_master_ui_enabled": True,
            "platform_passenger_master_ui_enabled": True,
            "agency_clients_ui_enabled": True,
            "agency_passengers_ui_enabled": True,
            "relationship_graph_metadata_enabled": True,
            "client_overview_enabled": True,
            "passenger_overview_enabled": True,
            "service_history_enabled": True,
            "known_operational_profile_enabled": True,
            "known_preferences_enabled": True,
            "portal_access_enabled": True,
            "client_is_commercial_owner": True,
            "passenger_is_operational_identity": True,
            "many_to_many_relationships_supported": True,
            "passenger_history_reusable": True,
            "metadata_only": True,
            "crm_sales_pipeline_disabled": True,
            "marketing_automation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_llm_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "payment_gateway_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
            "client_master_record_count": client_master_record_count,
            "passenger_master_record_count": passenger_master_record_count,
            "client_passenger_link_count": client_passenger_link_count,
            "passenger_service_history_count": passenger_service_history_count,
            "passenger_operational_preference_count": passenger_operational_preference_count,
            "passenger_known_document_count": passenger_known_document_count,
            "client_portal_access_profile_count": client_portal_access_profile_count,
            "client_master_status_counts": client_master_status_counts,
            "passenger_master_status_counts": passenger_master_status_counts,
            "client_passenger_link_status_counts": client_passenger_link_status_counts,
            "passenger_history_status_counts": passenger_history_status_counts,
            "passenger_preference_status_counts": passenger_preference_status_counts,
            "passenger_document_status_counts": passenger_document_status_counts,
            "client_portal_access_status_counts": client_portal_access_status_counts,
            "client_master_linked_passenger_count": client_master_linked_passenger_count,
            "passenger_master_reusable_history_count": passenger_master_reusable_history_count,
            "passenger_master_known_document_count": passenger_master_known_document_count,
            "readiness_required": False,
            "diagnostic": "Phase 51.3 creates metadata-only Client and Passenger master workspace records. Client is the commercial owner, Passenger is the reusable operational identity, many-to-many relationships are metadata only, and passenger history can be reused across requests, trips, booking mirrors, ticket mirrors, EMD mirrors, documents, operational evaluations, feasibility, and recommendations. It adds no CRM sales pipeline, marketing automation, provider integration, AI/LLM generation, booking, ticketing, payment gateway, or background worker execution. Human authority remains final.",
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
        "feature_bundle_rollout_approval_foundation": {
            "feature_bundle_rollout_approvals_enabled": True,
            "feature_bundle_rollout_approval_notes_enabled": True,
            "platform_rollout_approval_metadata_crud_enabled": True,
            "platform_rollout_approval_notes_metadata_enabled": True,
            "agency_rollout_approval_read_only_enabled": True,
            "approval_status_metadata_enabled": True,
            "approval_summary_enabled": True,
            "approval_timeline_enabled": True,
            "approval_note_visibility_enabled": True,
            "metadata_only": True,
            "read_only_visibility_only": True,
            "actual_feature_enablement_disabled": True,
            "feature_enablement_disabled": True,
            "feature_activation_disabled": True,
            "route_blocking_disabled": True,
            "permission_enforcement_disabled": True,
            "runtime_gating_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "stripe_disabled": True,
            "payment_provider_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "authentication_changes_disabled": True,
            "deployment_automation_disabled": True,
            "rollout_execution_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
            "webhook_execution_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "notifications_disabled": True,
            "ai_execution_disabled": True,
            "openai_disabled": True,
            "scraping_disabled": True,
            "publishing_disabled": True,
            "approval_count": feature_bundle_rollout_approval_count,
            "approval_note_count": feature_bundle_rollout_approval_note_count,
            "approval_status_counts": feature_bundle_rollout_approval_status_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.4 records metadata-only rollout approval, note, and timeline records for reviewed rollout plans. It does not enable features, enforce permissions, gate runtime access, bill, use Stripe or payment providers, change authentication, deploy, schedule jobs, run webhooks or background workers, send email/SMS/notifications, use AI/OpenAI, scrape, publish, or execute rollouts.",
        },
        "feature_bundle_rollout_schedule_foundation": {
            "feature_bundle_rollout_schedules_enabled": True,
            "platform_rollout_schedule_metadata_crud_enabled": True,
            "agency_rollout_schedule_read_only_enabled": True,
            "schedule_status_metadata_enabled": True,
            "planned_window_metadata_enabled": True,
            "maintenance_window_metadata_enabled": True,
            "estimated_duration_metadata_enabled": True,
            "dependency_summary_metadata_enabled": True,
            "checklist_summary_metadata_enabled": True,
            "approval_summary_metadata_enabled": True,
            "metadata_only": True,
            "read_only_planning": True,
            "actual_rollout_execution_disabled": True,
            "rollout_execution_disabled": True,
            "feature_activation_disabled": True,
            "entitlement_behavior_disabled": True,
            "permission_changes_disabled": True,
            "cron_jobs_disabled": True,
            "schedulers_disabled": True,
            "workers_disabled": True,
            "queues_disabled": True,
            "timers_disabled": True,
            "background_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "billing_disabled": True,
            "publishing_disabled": True,
            "automation_disabled": True,
            "schedule_count": feature_bundle_rollout_schedule_count,
            "schedule_status_counts": feature_bundle_rollout_schedule_status_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.5 records intended rollout schedule metadata only. It does not execute rollouts, activate features, change entitlements, modify permissions, start cron jobs, schedulers, workers, queues, timers, or background execution, call external APIs, use AI, bill, or publish anything automatically.",
        },
        "feature_bundle_rollout_timeline_foundation": {
            "feature_bundle_rollout_timeline_entries_enabled": True,
            "feature_bundle_rollout_actor_metadata_enabled": True,
            "feature_bundle_rollout_event_type_metadata_enabled": True,
            "platform_rollout_timeline_metadata_create_enabled": True,
            "platform_rollout_timeline_read_enabled": True,
            "agency_rollout_timeline_read_only_enabled": True,
            "timeline_filter_by_plan_enabled": True,
            "timeline_filter_by_agency_enabled": True,
            "timeline_filter_by_bundle_enabled": True,
            "timeline_filter_by_event_type_enabled": True,
            "timeline_filter_by_date_enabled": True,
            "newest_first_enabled": True,
            "metadata_only": True,
            "historical_timeline_only": True,
            "feature_bundles_enablement_disabled": True,
            "feature_bundle_enablement_disabled": True,
            "agency_permission_changes_disabled": True,
            "rollout_plan_execution_disabled": True,
            "rollout_execution_disabled": True,
            "background_jobs_disabled": True,
            "background_workers_disabled": True,
            "scheduled_jobs_disabled": True,
            "cron_jobs_disabled": True,
            "automation_disabled": True,
            "publishing_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "email_sending_disabled": True,
            "notifications_disabled": True,
            "notification_sending_disabled": True,
            "rollout_state_enforcement_disabled": True,
            "subscription_modification_disabled": True,
            "timeline_entry_count": feature_bundle_rollout_timeline_count,
            "timeline_event_type_counts": feature_bundle_rollout_timeline_event_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.6 records metadata-only rollout timeline history. It does not enable feature bundles, change agency permissions, execute rollout plans, schedule background jobs, publish, call providers, send emails or notifications, enforce rollout state, modify subscriptions, or introduce automation.",
        },
        "feature_bundle_dependency_foundation": {
            "feature_bundle_dependencies_enabled": True,
            "feature_bundle_dependency_reference_metadata_enabled": True,
            "feature_bundle_dependency_type_metadata_enabled": True,
            "platform_dependency_metadata_crud_enabled": True,
            "agency_dependency_read_only_enabled": True,
            "bundle_dependency_filter_enabled": True,
            "plan_dependency_filter_enabled": True,
            "agency_dependency_filter_enabled": True,
            "dependency_type_filter_enabled": True,
            "metadata_only": True,
            "dependency_metadata_only": True,
            "dependency_informational_only": True,
            "rollout_execution_disabled": True,
            "background_jobs_disabled": True,
            "scheduled_jobs_disabled": True,
            "dependency_enforcement_disabled": True,
            "rollout_blocking_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundles_enablement_disabled": True,
            "permission_modification_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "publishing_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "automation_disabled": True,
            "dependency_count": feature_bundle_dependency_count,
            "dependency_type_counts": feature_bundle_dependency_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.7 stores feature bundle dependency metadata only. It does not execute rollout plans, schedule background jobs, enforce dependencies, block rollouts, activate feature bundles, modify permissions, send notifications, publish, call providers, or introduce automation.",
        },
        "feature_bundle_rollout_risk_register_foundation": {
            "feature_bundle_rollout_risks_enabled": True,
            "feature_bundle_rollout_risk_impact_metadata_enabled": True,
            "feature_bundle_rollout_risk_likelihood_metadata_enabled": True,
            "feature_bundle_rollout_risk_status_metadata_enabled": True,
            "platform_risk_metadata_crud_enabled": True,
            "agency_risk_read_only_enabled": True,
            "risk_filter_by_agency_enabled": True,
            "risk_filter_by_bundle_enabled": True,
            "risk_filter_by_rollout_plan_enabled": True,
            "risk_filter_by_status_enabled": True,
            "risk_filter_by_impact_enabled": True,
            "risk_filter_by_likelihood_enabled": True,
            "metadata_only": True,
            "risk_register_metadata_only": True,
            "risk_decisions_informational_only": True,
            "rollout_execution_disabled": True,
            "risk_decision_enforcement_disabled": True,
            "risk_enforcement_disabled": True,
            "risk_blocking_disabled": True,
            "rollout_blocking_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundles_enablement_disabled": True,
            "automation_disabled": True,
            "background_jobs_disabled": True,
            "external_provider_calls_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "risk_count": feature_bundle_rollout_risk_count,
            "risk_status_counts": feature_bundle_rollout_risk_status_counts,
            "risk_impact_counts": feature_bundle_rollout_risk_impact_counts,
            "risk_likelihood_counts": feature_bundle_rollout_risk_likelihood_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.8 stores feature bundle rollout risk metadata only. It does not execute rollouts, enforce risk decisions, block anything, send notifications, activate bundles, add automation, or call external providers.",
        },
        "feature_bundle_rollout_issue_log_foundation": {
            "feature_bundle_rollout_issues_enabled": True,
            "feature_bundle_rollout_issue_severity_metadata_enabled": True,
            "feature_bundle_rollout_issue_status_metadata_enabled": True,
            "platform_issue_metadata_crud_enabled": True,
            "agency_issue_read_only_enabled": True,
            "issue_filter_by_agency_enabled": True,
            "issue_filter_by_bundle_enabled": True,
            "issue_filter_by_rollout_plan_enabled": True,
            "issue_filter_by_risk_enabled": True,
            "issue_filter_by_dependency_enabled": True,
            "issue_filter_by_approval_enabled": True,
            "issue_filter_by_severity_enabled": True,
            "issue_filter_by_status_enabled": True,
            "metadata_only": True,
            "issue_log_metadata_only": True,
            "issue_records_informational_only": True,
            "rollout_execution_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundles_enablement_disabled": True,
            "rollout_blocking_disabled": True,
            "blocking_enforcement_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "external_provider_calls_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "ai_provider_execution_disabled": True,
            "ai_execution_disabled": True,
            "automation_disabled": True,
            "background_jobs_disabled": True,
            "issue_count": feature_bundle_rollout_issue_count,
            "issue_status_counts": feature_bundle_rollout_issue_status_counts,
            "issue_severity_counts": feature_bundle_rollout_issue_severity_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.9 stores feature bundle rollout issue metadata only. It does not execute rollouts, activate bundles, enforce blocking, send notifications, call external providers, or add AI/provider execution.",
        },
        "feature_bundle_rollout_decision_register_foundation": {
            "feature_bundle_rollout_decisions_enabled": True,
            "feature_bundle_rollout_decision_category_metadata_enabled": True,
            "feature_bundle_rollout_decision_status_metadata_enabled": True,
            "platform_decision_metadata_crud_enabled": True,
            "agency_decision_read_only_enabled": True,
            "decision_filter_by_rollout_enabled": True,
            "decision_filter_by_category_enabled": True,
            "decision_filter_by_owner_enabled": True,
            "decision_filter_by_status_enabled": True,
            "decision_related_bundle_references_enabled": True,
            "decision_related_dependency_references_enabled": True,
            "decision_related_risk_references_enabled": True,
            "decision_related_issue_references_enabled": True,
            "decision_timeline_references_enabled": True,
            "metadata_only": True,
            "decision_register_metadata_only": True,
            "decision_records_informational_only": True,
            "read_only_ui_enabled": True,
            "rollout_execution_disabled": True,
            "deployment_automation_disabled": True,
            "feature_activation_disabled": True,
            "feature_bundle_activation_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
            "provider_integrations_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "webhook_execution_disabled": True,
            "publishing_disabled": True,
            "runtime_switching_disabled": True,
            "automation_disabled": True,
            "decision_count": feature_bundle_rollout_decision_count,
            "decision_status_counts": feature_bundle_rollout_decision_status_counts,
            "decision_category_counts": feature_bundle_rollout_decision_category_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.10 stores feature bundle rollout decision register metadata only. It does not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, or switch runtime behavior.",
        },
        "feature_bundle_rollout_change_request_foundation": {
            "feature_bundle_rollout_change_requests_enabled": True,
            "feature_bundle_rollout_change_request_type_metadata_enabled": True,
            "feature_bundle_rollout_change_request_priority_metadata_enabled": True,
            "feature_bundle_rollout_change_request_impact_metadata_enabled": True,
            "feature_bundle_rollout_change_request_status_metadata_enabled": True,
            "platform_change_request_metadata_crud_enabled": True,
            "agency_change_request_read_only_enabled": True,
            "change_request_filter_by_rollout_enabled": True,
            "change_request_filter_by_status_enabled": True,
            "change_request_filter_by_priority_enabled": True,
            "change_request_filter_by_impact_level_enabled": True,
            "change_request_filter_by_change_type_enabled": True,
            "change_request_affected_bundle_references_enabled": True,
            "change_request_affected_feature_flag_references_enabled": True,
            "change_request_related_decision_references_enabled": True,
            "change_request_related_issue_references_enabled": True,
            "change_request_related_risk_references_enabled": True,
            "change_request_related_dependency_references_enabled": True,
            "metadata_only": True,
            "change_request_metadata_only": True,
            "change_request_records_informational_only": True,
            "read_only_ui_enabled": True,
            "rollout_execution_disabled": True,
            "deployment_automation_disabled": True,
            "feature_activation_disabled": True,
            "feature_bundle_activation_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
            "provider_integrations_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "webhook_execution_disabled": True,
            "publishing_disabled": True,
            "runtime_switching_disabled": True,
            "automation_disabled": True,
            "change_request_count": feature_bundle_rollout_change_request_count,
            "change_request_status_counts": feature_bundle_rollout_change_request_status_counts,
            "change_request_priority_counts": feature_bundle_rollout_change_request_priority_counts,
            "change_request_impact_counts": feature_bundle_rollout_change_request_impact_counts,
            "change_request_type_counts": feature_bundle_rollout_change_request_type_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.11 stores feature bundle rollout change request metadata only. It does not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, or switch runtime behavior.",
        },
        "feature_bundle_rollout_rollback_plan_foundation": {
            "feature_bundle_rollout_rollback_plans_enabled": True,
            "feature_bundle_rollout_rollback_trigger_metadata_enabled": True,
            "feature_bundle_rollout_rollback_scope_metadata_enabled": True,
            "feature_bundle_rollout_rollback_priority_metadata_enabled": True,
            "feature_bundle_rollout_rollback_status_metadata_enabled": True,
            "platform_rollback_plan_metadata_crud_enabled": True,
            "agency_rollback_plan_read_only_enabled": True,
            "rollback_plan_filter_by_rollout_enabled": True,
            "rollback_plan_filter_by_status_enabled": True,
            "rollback_plan_filter_by_priority_enabled": True,
            "rollback_plan_filter_by_scope_enabled": True,
            "rollback_plan_filter_by_owner_enabled": True,
            "rollback_plan_affected_bundle_references_enabled": True,
            "rollback_plan_affected_feature_flag_references_enabled": True,
            "rollback_plan_related_change_request_references_enabled": True,
            "rollback_plan_related_decision_references_enabled": True,
            "rollback_plan_related_issue_references_enabled": True,
            "rollback_plan_related_risk_references_enabled": True,
            "rollback_plan_related_dependency_references_enabled": True,
            "rollback_steps_metadata_enabled": True,
            "validation_notes_metadata_enabled": True,
            "metadata_only": True,
            "rollback_plan_metadata_only": True,
            "rollback_plan_records_informational_only": True,
            "read_only_ui_enabled": True,
            "rollout_execution_disabled": True,
            "rollback_execution_disabled": True,
            "deployment_automation_disabled": True,
            "feature_activation_disabled": True,
            "feature_deactivation_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundle_deactivation_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
            "provider_integrations_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "webhook_execution_disabled": True,
            "publishing_disabled": True,
            "runtime_switching_disabled": True,
            "automation_disabled": True,
            "rollback_plan_count": feature_bundle_rollout_rollback_plan_count,
            "rollback_plan_status_counts": feature_bundle_rollout_rollback_plan_status_counts,
            "rollback_plan_priority_counts": feature_bundle_rollout_rollback_plan_priority_counts,
            "rollback_plan_scope_counts": feature_bundle_rollout_rollback_plan_scope_counts,
            "rollback_plan_trigger_counts": feature_bundle_rollout_rollback_plan_trigger_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.12 stores feature bundle rollout rollback plan metadata only. It does not execute rollbacks, automate deployments, activate or deactivate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, or switch runtime behavior.",
        },
        "feature_bundle_rollout_summary_pack_foundation": {
            "feature_bundle_rollout_summary_packs_enabled": True,
            "feature_bundle_rollout_summary_pack_status_metadata_enabled": True,
            "feature_bundle_rollout_summary_pack_audience_metadata_enabled": True,
            "platform_summary_pack_metadata_crud_enabled": True,
            "agency_summary_pack_read_only_enabled": True,
            "summary_pack_filter_by_rollout_enabled": True,
            "summary_pack_filter_by_status_enabled": True,
            "summary_pack_filter_by_audience_enabled": True,
            "summary_pack_filter_by_bundle_enabled": True,
            "summary_pack_covered_bundle_references_enabled": True,
            "summary_pack_readiness_references_enabled": True,
            "summary_pack_approval_references_enabled": True,
            "summary_pack_schedule_references_enabled": True,
            "summary_pack_timeline_references_enabled": True,
            "summary_pack_dependency_references_enabled": True,
            "summary_pack_risk_references_enabled": True,
            "summary_pack_issue_references_enabled": True,
            "summary_pack_decision_references_enabled": True,
            "summary_pack_change_request_references_enabled": True,
            "summary_pack_rollback_plan_references_enabled": True,
            "evidence_notes_metadata_enabled": True,
            "compliance_notes_metadata_enabled": True,
            "metadata_only": True,
            "summary_pack_metadata_only": True,
            "summary_pack_records_informational_only": True,
            "read_only_ui_enabled": True,
            "rollout_execution_disabled": True,
            "deployment_automation_disabled": True,
            "feature_activation_disabled": True,
            "feature_deactivation_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundle_deactivation_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
            "provider_integrations_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "webhook_execution_disabled": True,
            "publishing_disabled": True,
            "runtime_switching_disabled": True,
            "pdf_generation_disabled": True,
            "file_export_disabled": True,
            "automation_disabled": True,
            "summary_pack_count": feature_bundle_rollout_summary_pack_count,
            "summary_pack_status_counts": feature_bundle_rollout_summary_pack_status_counts,
            "summary_pack_audience_counts": feature_bundle_rollout_summary_pack_audience_counts,
            "readiness_required": False,
            "diagnostic": "Phase 40.13 stores feature bundle rollout summary evidence-pack metadata only. It does not execute rollouts, automate deployments, activate or deactivate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, switch runtime behavior, generate PDFs, export files, or automate actions.",
        },
        "operational_travel_workspace_foundation": {
            "operational_travel_workspaces_enabled": True,
            "operational_travel_workspace_metadata_enabled": True,
            "platform_operational_travel_workspace_metadata_crud_enabled": True,
            "agency_operational_travel_workspace_read_only_enabled": True,
            "workspace_filter_by_agency_enabled": True,
            "workspace_filter_by_status_enabled": True,
            "workspace_filter_by_type_enabled": True,
            "workspace_filter_by_priority_enabled": True,
            "workspace_filter_by_assigned_agent_enabled": True,
            "workspace_filter_by_travel_date_enabled": True,
            "primary_client_metadata_enabled": True,
            "primary_passenger_metadata_enabled": True,
            "linked_request_metadata_enabled": True,
            "linked_trip_metadata_enabled": True,
            "linked_offer_metadata_enabled": True,
            "linked_booking_metadata_enabled": True,
            "linked_ticket_metadata_enabled": True,
            "linked_document_metadata_enabled": True,
            "origin_summary_metadata_enabled": True,
            "destination_summary_metadata_enabled": True,
            "service_summary_metadata_enabled": True,
            "operational_notes_metadata_enabled": True,
            "assigned_team_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "operational_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_live_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "payment_processing_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "ai_automation_disabled": True,
            "external_api_calls_disabled": True,
            "supplier_integrations_disabled": True,
            "live_airline_calls_disabled": True,
            "background_workers_disabled": True,
            "automation_disabled": True,
            "workspace_count": operational_travel_workspace_count,
            "workspace_status_counts": operational_travel_workspace_status_counts,
            "workspace_type_counts": operational_travel_workspace_type_counts,
            "workspace_priority_counts": operational_travel_workspace_priority_counts,
            "readiness_required": False,
            "diagnostic": "Phase 41.0 stores operational travel workspace metadata only. It does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, or automate travel operations.",
        },
        "travel_request_workspace_foundation": {
            "travel_request_workspaces_enabled": True,
            "travel_request_workspace_metadata_enabled": True,
            "platform_travel_request_workspace_metadata_crud_enabled": True,
            "agency_travel_request_workspace_read_only_enabled": True,
            "request_workspace_filter_by_agency_enabled": True,
            "request_workspace_filter_by_status_enabled": True,
            "request_workspace_filter_by_type_enabled": True,
            "request_workspace_filter_by_priority_enabled": True,
            "request_workspace_filter_by_assigned_agent_enabled": True,
            "request_workspace_filter_by_departure_date_enabled": True,
            "request_workspace_filter_by_operational_workspace_enabled": True,
            "operational_workspace_link_metadata_enabled": True,
            "requester_metadata_enabled": True,
            "client_passenger_metadata_enabled": True,
            "requested_route_metadata_enabled": True,
            "requested_dates_metadata_enabled": True,
            "passenger_summary_metadata_enabled": True,
            "requested_services_metadata_enabled": True,
            "special_service_notes_metadata_enabled": True,
            "budget_notes_metadata_enabled": True,
            "deadline_metadata_enabled": True,
            "linked_trip_metadata_enabled": True,
            "linked_offer_metadata_enabled": True,
            "linked_document_metadata_enabled": True,
            "internal_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "travel_request_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_live_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "payment_processing_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "ai_automation_disabled": True,
            "external_api_calls_disabled": True,
            "supplier_integrations_disabled": True,
            "live_airline_calls_disabled": True,
            "background_workers_disabled": True,
            "automatic_trip_creation_disabled": True,
            "automatic_offer_creation_disabled": True,
            "automation_disabled": True,
            "request_workspace_count": travel_request_workspace_count,
            "request_workspace_status_counts": travel_request_workspace_status_counts,
            "request_workspace_type_counts": travel_request_workspace_type_counts,
            "request_workspace_priority_counts": travel_request_workspace_priority_counts,
            "readiness_required": False,
            "diagnostic": "Phase 41.1 stores travel request workspace metadata inside operational workspaces. It does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, automatically convert requests to trips, automatically create offers, or automate travel operations.",
        },
        "passenger_workspace_foundation": {
            "passenger_workspaces_enabled": True,
            "passenger_workspace_metadata_enabled": True,
            "platform_passenger_workspace_metadata_crud_enabled": True,
            "agency_passenger_workspace_read_only_enabled": True,
            "passenger_workspace_filter_by_status_enabled": True,
            "passenger_workspace_filter_by_nationality_enabled": True,
            "passenger_workspace_filter_by_citizenship_enabled": True,
            "passenger_workspace_filter_by_assistance_profile_enabled": True,
            "passenger_workspace_filter_by_travel_date_enabled": True,
            "passenger_workspace_filter_by_operational_workspace_enabled": True,
            "personal_information_metadata_enabled": True,
            "travel_document_metadata_enabled": True,
            "loyalty_membership_metadata_enabled": True,
            "known_traveler_metadata_enabled": True,
            "emergency_contact_metadata_enabled": True,
            "mobility_profile_metadata_enabled": True,
            "medical_profile_metadata_enabled": True,
            "dietary_profile_metadata_enabled": True,
            "assistance_profile_metadata_enabled": True,
            "baggage_profile_metadata_enabled": True,
            "seating_preference_metadata_enabled": True,
            "language_preference_metadata_enabled": True,
            "linked_request_metadata_enabled": True,
            "linked_trip_metadata_enabled": True,
            "linked_offer_metadata_enabled": True,
            "linked_booking_metadata_enabled": True,
            "linked_ticket_metadata_enabled": True,
            "linked_document_metadata_enabled": True,
            "internal_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "passenger_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_connectivity_disabled": True,
            "gds_live_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "payment_processing_disabled": True,
            "supplier_integrations_disabled": True,
            "ai_disabled": True,
            "ai_automation_disabled": True,
            "email_disabled": True,
            "email_sending_disabled": True,
            "sms_disabled": True,
            "sms_sending_disabled": True,
            "background_workers_disabled": True,
            "external_api_calls_disabled": True,
            "automatic_profile_matching_disabled": True,
            "automatic_document_validation_disabled": True,
            "document_validation_disabled": True,
            "airline_communication_disabled": True,
            "automation_disabled": True,
            "passenger_workspace_count": passenger_workspace_count,
            "passenger_workspace_status_counts": passenger_workspace_status_counts,
            "passenger_workspace_nationality_count": passenger_workspace_nationality_count,
            "passenger_workspace_citizenship_count": passenger_workspace_citizenship_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.2 stores passenger workspace metadata only. It does not execute bookings, issue tickets, connect to GDS or NDC, process payments, integrate suppliers, use AI, send email or SMS, run background workers, call external APIs, automatically match profiles, automatically validate documents, communicate with airlines, or automate passenger operations.",
        },
        "flight_workspace_foundation": {
            "flight_workspaces_enabled": True,
            "flight_workspace_metadata_enabled": True,
            "platform_flight_workspace_metadata_crud_enabled": True,
            "agency_flight_workspace_read_only_enabled": True,
            "flight_workspace_filter_by_status_enabled": True,
            "flight_workspace_filter_by_airline_enabled": True,
            "flight_workspace_filter_by_departure_airport_enabled": True,
            "flight_workspace_filter_by_arrival_airport_enabled": True,
            "flight_workspace_filter_by_departure_date_enabled": True,
            "flight_workspace_filter_by_cabin_enabled": True,
            "flight_workspace_filter_by_booking_class_enabled": True,
            "flight_workspace_filter_by_operational_workspace_enabled": True,
            "flight_reference_metadata_enabled": True,
            "flight_type_metadata_enabled": True,
            "travel_direction_metadata_enabled": True,
            "airline_metadata_enabled": True,
            "marketing_carrier_metadata_enabled": True,
            "operating_carrier_metadata_enabled": True,
            "flight_number_metadata_enabled": True,
            "departure_airport_metadata_enabled": True,
            "arrival_airport_metadata_enabled": True,
            "terminal_metadata_enabled": True,
            "schedule_metadata_enabled": True,
            "aircraft_metadata_enabled": True,
            "cabin_class_metadata_enabled": True,
            "booking_class_metadata_enabled": True,
            "fare_family_metadata_enabled": True,
            "baggage_summary_metadata_enabled": True,
            "connection_summary_metadata_enabled": True,
            "stopover_summary_metadata_enabled": True,
            "elapsed_travel_time_metadata_enabled": True,
            "operating_days_metadata_enabled": True,
            "passenger_link_metadata_enabled": True,
            "linked_request_metadata_enabled": True,
            "linked_trip_metadata_enabled": True,
            "linked_offer_metadata_enabled": True,
            "linked_booking_metadata_enabled": True,
            "linked_ticket_metadata_enabled": True,
            "linked_document_metadata_enabled": True,
            "operational_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "flight_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "live_flight_search_disabled": True,
            "flight_search_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_disabled": True,
            "payment_processing_disabled": True,
            "ticket_issuance_disabled": True,
            "schedule_synchronization_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_route_generation_disabled": True,
            "flight_validation_disabled": True,
            "airline_lookups_disabled": True,
            "live_schedule_updates_disabled": True,
            "automation_disabled": True,
            "flight_workspace_count": flight_workspace_count,
            "flight_workspace_status_counts": flight_workspace_status_counts,
            "flight_workspace_airline_count": flight_workspace_airline_count,
            "flight_workspace_departure_airport_count": flight_workspace_departure_airport_count,
            "flight_workspace_arrival_airport_count": flight_workspace_arrival_airport_count,
            "flight_workspace_cabin_count": flight_workspace_cabin_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.3 stores flight workspace metadata only. It does not execute bookings, search live flights, connect to GDS or NDC, call airline APIs, process payments, issue tickets, synchronize schedules, call external APIs, use AI, run background workers, automatically generate routes, validate flights, look up airlines, update live schedules, or automate flight operations.",
        },
        "trip_workspace_foundation": {
            "trip_workspaces_enabled": True,
            "trip_workspace_metadata_enabled": True,
            "platform_trip_workspace_metadata_crud_enabled": True,
            "agency_trip_workspace_read_only_enabled": True,
            "trip_workspace_filter_by_status_enabled": True,
            "trip_workspace_filter_by_departure_country_enabled": True,
            "trip_workspace_filter_by_destination_country_enabled": True,
            "trip_workspace_filter_by_departure_date_enabled": True,
            "trip_workspace_filter_by_assigned_agent_enabled": True,
            "trip_workspace_filter_by_priority_enabled": True,
            "trip_workspace_filter_by_operational_workspace_enabled": True,
            "trip_reference_metadata_enabled": True,
            "journey_type_metadata_enabled": True,
            "service_type_metadata_enabled": True,
            "client_metadata_enabled": True,
            "passenger_summary_metadata_enabled": True,
            "flight_summary_metadata_enabled": True,
            "linked_request_metadata_enabled": True,
            "linked_offer_metadata_enabled": True,
            "linked_booking_metadata_enabled": True,
            "linked_ticket_metadata_enabled": True,
            "linked_emd_metadata_enabled": True,
            "linked_document_metadata_enabled": True,
            "route_metadata_enabled": True,
            "travel_date_metadata_enabled": True,
            "itinerary_summary_metadata_enabled": True,
            "baggage_summary_metadata_enabled": True,
            "service_summary_metadata_enabled": True,
            "assigned_team_metadata_enabled": True,
            "operational_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "trip_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_processing_disabled": True,
            "invoicing_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_trip_generation_disabled": True,
            "automatic_itinerary_generation_disabled": True,
            "itinerary_generation_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
            "trip_workspace_count": trip_workspace_count,
            "trip_workspace_status_counts": trip_workspace_status_counts,
            "trip_workspace_departure_country_count": trip_workspace_departure_country_count,
            "trip_workspace_destination_country_count": trip_workspace_destination_country_count,
            "trip_workspace_priority_count": trip_workspace_priority_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.4 stores trip workspace metadata only. It does not execute bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, invoice, use AI, run background workers, automatically generate trips, automatically generate itineraries, call external integrations, or automate journey operations.",
        },
        "offer_workspace_foundation": {
            "offer_workspaces_enabled": True,
            "offer_workspace_metadata_enabled": True,
            "platform_offer_workspace_metadata_crud_enabled": True,
            "agency_offer_workspace_read_only_enabled": True,
            "offer_workspace_filter_by_status_enabled": True,
            "offer_workspace_filter_by_validity_enabled": True,
            "offer_workspace_filter_by_client_enabled": True,
            "offer_workspace_filter_by_destination_enabled": True,
            "offer_workspace_filter_by_price_range_enabled": True,
            "offer_workspace_filter_by_assigned_agent_enabled": True,
            "offer_workspace_filter_by_trip_workspace_enabled": True,
            "offer_reference_metadata_enabled": True,
            "offer_status_metadata_enabled": True,
            "offer_type_metadata_enabled": True,
            "client_metadata_enabled": True,
            "passenger_summary_metadata_enabled": True,
            "flight_summary_metadata_enabled": True,
            "trip_summary_metadata_enabled": True,
            "pricing_summary_metadata_enabled": True,
            "taxes_metadata_enabled": True,
            "fees_metadata_enabled": True,
            "ancillary_metadata_enabled": True,
            "baggage_metadata_enabled": True,
            "seat_metadata_enabled": True,
            "meal_metadata_enabled": True,
            "hotel_metadata_enabled": True,
            "transfer_metadata_enabled": True,
            "insurance_metadata_enabled": True,
            "validity_metadata_enabled": True,
            "linked_booking_metadata_enabled": True,
            "linked_ticket_metadata_enabled": True,
            "linked_document_metadata_enabled": True,
            "agent_notes_metadata_enabled": True,
            "customer_notes_metadata_enabled": True,
            "internal_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "offer_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "payment_processing_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "fare_calculation_engines_disabled": True,
            "fare_calculation_disabled": True,
            "live_pricing_disabled": True,
            "ai_itinerary_generation_disabled": True,
            "supplier_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automatic_booking_conversion_disabled": True,
            "background_workers_disabled": True,
            "automation_disabled": True,
            "offer_workspace_count": offer_workspace_v2_count,
            "offer_workspace_status_counts": offer_workspace_status_counts,
            "offer_workspace_type_count": offer_workspace_type_count,
            "offer_workspace_currency_count": offer_workspace_currency_count,
            "offer_workspace_destination_count": offer_workspace_destination_count,
            "offer_workspace_assigned_agent_count": offer_workspace_assigned_agent_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.5 stores offer workspace metadata only. It does not execute bookings, issue tickets, process payments, connect to GDS or NDC, call airline APIs, calculate fares, generate AI itineraries, integrate suppliers, call external APIs, convert bookings automatically, run background workers, or automate proposals.",
        },
        "booking_workspace_foundation": {
            "booking_workspaces_enabled": True,
            "booking_workspace_metadata_enabled": True,
            "platform_booking_workspace_metadata_crud_enabled": True,
            "agency_booking_workspace_read_only_enabled": True,
            "booking_workspace_filter_by_status_enabled": True,
            "booking_workspace_filter_by_owner_enabled": True,
            "booking_workspace_filter_by_airline_enabled": True,
            "booking_workspace_filter_by_supplier_enabled": True,
            "booking_workspace_filter_by_booking_date_enabled": True,
            "booking_reference_metadata_enabled": True,
            "booking_status_metadata_enabled": True,
            "booking_type_metadata_enabled": True,
            "booking_source_metadata_enabled": True,
            "booking_owner_metadata_enabled": True,
            "airline_pnr_metadata_enabled": True,
            "gds_record_locator_metadata_enabled": True,
            "supplier_reference_metadata_enabled": True,
            "passenger_summary_metadata_enabled": True,
            "flight_summary_metadata_enabled": True,
            "trip_summary_metadata_enabled": True,
            "offer_summary_metadata_enabled": True,
            "ticket_link_metadata_enabled": True,
            "emd_link_metadata_enabled": True,
            "ssr_link_metadata_enabled": True,
            "osi_link_metadata_enabled": True,
            "document_link_metadata_enabled": True,
            "timeline_link_metadata_enabled": True,
            "communication_link_metadata_enabled": True,
            "payment_summary_metadata_enabled": True,
            "booking_summary_metadata_enabled": True,
            "operational_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "booking_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "live_booking_creation_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_processing_disabled": True,
            "fare_calculation_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_booking_confirmation_disabled": True,
            "automatic_ticket_generation_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
            "booking_workspace_count": booking_workspace_count,
            "booking_workspace_status_counts": booking_workspace_status_counts,
            "booking_workspace_owner_count": booking_workspace_owner_count,
            "booking_workspace_supplier_count": booking_workspace_supplier_count,
            "booking_workspace_airline_count": booking_workspace_airline_count,
            "booking_workspace_operational_workspace_count": booking_workspace_operational_workspace_count,
            "booking_workspace_trip_workspace_count": booking_workspace_trip_workspace_count,
            "booking_workspace_offer_workspace_count": booking_workspace_offer_workspace_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.6 stores booking workspace metadata only. It does not create live bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, calculate fares, use AI, run background workers, confirm bookings automatically, generate tickets automatically, call external integrations, or automate booking operations.",
        },
        "ticket_workspace_foundation": {
            "ticket_workspaces_enabled": True,
            "ticket_workspace_metadata_enabled": True,
            "platform_ticket_workspace_metadata_crud_enabled": True,
            "agency_ticket_workspace_read_only_enabled": True,
            "ticket_workspace_filter_by_status_enabled": True,
            "ticket_workspace_filter_by_document_status_enabled": True,
            "ticket_workspace_filter_by_validating_carrier_enabled": True,
            "ticket_workspace_filter_by_issue_date_enabled": True,
            "ticket_workspace_filter_by_passenger_enabled": True,
            "ticket_workspace_filter_by_booking_reference_enabled": True,
            "ticket_workspace_filter_by_currency_enabled": True,
            "ticket_reference_metadata_enabled": True,
            "ticket_status_metadata_enabled": True,
            "ticket_document_status_metadata_enabled": True,
            "ticket_type_metadata_enabled": True,
            "ticket_number_metadata_enabled": True,
            "validating_carrier_metadata_enabled": True,
            "issuing_agent_metadata_enabled": True,
            "issuing_office_metadata_enabled": True,
            "issue_date_metadata_enabled": True,
            "passenger_metadata_enabled": True,
            "flight_summary_metadata_enabled": True,
            "booking_reference_metadata_enabled": True,
            "airline_pnr_metadata_enabled": True,
            "gds_record_locator_metadata_enabled": True,
            "fare_basis_metadata_enabled": True,
            "fare_amount_metadata_enabled": True,
            "taxes_amount_metadata_enabled": True,
            "total_amount_metadata_enabled": True,
            "fare_calculation_line_metadata_enabled": True,
            "fare_calculation_currency_metadata_enabled": True,
            "fare_calculation_nuc_total_metadata_enabled": True,
            "fare_calculation_roe_metadata_enabled": True,
            "equivalent_fare_metadata_enabled": True,
            "form_of_payment_metadata_enabled": True,
            "payment_reference_metadata_enabled": True,
            "payment_restrictions_metadata_enabled": True,
            "commission_summary_metadata_enabled": True,
            "tax_breakdown_metadata_enabled": True,
            "fare_construction_notes_metadata_enabled": True,
            "pricing_units_metadata_enabled": True,
            "fare_components_metadata_enabled": True,
            "coupon_summary_metadata_enabled": True,
            "coupon_status_summary_metadata_enabled": True,
            "coupon_details_metadata_enabled": True,
            "baggage_summary_metadata_enabled": True,
            "endorsement_summary_metadata_enabled": True,
            "restrictions_summary_metadata_enabled": True,
            "exchange_reference_metadata_enabled": True,
            "refund_reference_metadata_enabled": True,
            "void_reference_metadata_enabled": True,
            "emd_link_metadata_enabled": True,
            "document_link_metadata_enabled": True,
            "lifecycle_notes_metadata_enabled": True,
            "operational_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "ticket_workspace_metadata_only": True,
            "ticket_issuance_disabled": True,
            "ticket_reissue_disabled": True,
            "voiding_disabled": True,
            "void_workflow_disabled": True,
            "refunds_disabled": True,
            "refund_workflow_disabled": True,
            "exchanges_disabled": True,
            "exchange_workflow_disabled": True,
            "payment_processing_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "fare_calculation_disabled": True,
            "fare_recalculation_disabled": True,
            "automated_ticket_validation_disabled": True,
            "coupon_validation_disabled": True,
            "background_workers_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
            "ticket_workspace_count": ticket_workspace_count,
            "ticket_workspace_status_counts": ticket_workspace_status_counts,
            "ticket_document_status_counts": ticket_document_status_counts,
            "ticket_workspace_validating_carrier_count": ticket_workspace_validating_carrier_count,
            "ticket_workspace_currency_count": ticket_workspace_currency_count,
            "ticket_workspace_passenger_count": ticket_workspace_passenger_count,
            "ticket_workspace_booking_reference_count": ticket_workspace_booking_reference_count,
            "ticket_workspace_operational_workspace_count": ticket_workspace_operational_workspace_count,
            "ticket_workspace_trip_workspace_count": ticket_workspace_trip_workspace_count,
            "ticket_workspace_offer_workspace_count": ticket_workspace_offer_workspace_count,
            "ticket_workspace_booking_workspace_count": ticket_workspace_booking_workspace_count,
            "ticket_workspace_coupon_detail_count": ticket_workspace_coupon_detail_count,
            "ticket_workspace_pricing_unit_count": ticket_workspace_pricing_unit_count,
            "ticket_workspace_fare_component_count": ticket_workspace_fare_component_count,
            "ticket_workspace_tax_breakdown_count": ticket_workspace_tax_breakdown_count,
            "ticket_workspace_exchange_reference_count": ticket_workspace_exchange_reference_count,
            "ticket_workspace_refund_reference_count": ticket_workspace_refund_reference_count,
            "ticket_workspace_void_reference_count": ticket_workspace_void_reference_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.7 stores ticket workspace metadata only. It does not issue, reissue, void, refund, exchange, process payments, connect to GDS or NDC, call airline APIs, calculate fares, validate coupons, run background workers, call external integrations, or automate ticket operations.",
        },
        "emd_workspace_foundation": {
            "emd_workspaces_enabled": True,
            "emd_workspace_metadata_enabled": True,
            "platform_emd_workspace_metadata_crud_enabled": True,
            "agency_emd_workspace_read_only_enabled": True,
            "emd_workspace_filter_by_status_enabled": True,
            "emd_workspace_filter_by_type_enabled": True,
            "emd_workspace_filter_by_a_or_s_enabled": True,
            "emd_workspace_filter_by_validating_carrier_enabled": True,
            "emd_workspace_filter_by_passenger_enabled": True,
            "emd_workspace_filter_by_rfic_enabled": True,
            "emd_workspace_filter_by_rfisc_enabled": True,
            "emd_workspace_filter_by_service_category_enabled": True,
            "emd_workspace_filter_by_issue_date_enabled": True,
            "emd_reference_metadata_enabled": True,
            "emd_status_metadata_enabled": True,
            "emd_document_status_metadata_enabled": True,
            "emd_type_metadata_enabled": True,
            "emd_number_metadata_enabled": True,
            "emd_form_type_metadata_enabled": True,
            "emd_a_or_s_metadata_enabled": True,
            "validating_carrier_metadata_enabled": True,
            "issuing_metadata_enabled": True,
            "passenger_metadata_enabled": True,
            "booking_reference_metadata_enabled": True,
            "airline_pnr_metadata_enabled": True,
            "gds_record_locator_metadata_enabled": True,
            "associated_ticket_metadata_enabled": True,
            "associated_ticket_coupon_metadata_enabled": True,
            "associated_flight_metadata_enabled": True,
            "ssr_link_metadata_enabled": True,
            "osi_link_metadata_enabled": True,
            "ancillary_service_link_metadata_enabled": True,
            "rfic_metadata_enabled": True,
            "rfisc_metadata_enabled": True,
            "service_metadata_enabled": True,
            "emd_coupon_status_summary_metadata_enabled": True,
            "emd_coupon_details_metadata_enabled": True,
            "amount_metadata_enabled": True,
            "tax_breakdown_metadata_enabled": True,
            "payment_metadata_enabled": True,
            "exchange_reference_metadata_enabled": True,
            "refund_reference_metadata_enabled": True,
            "void_reference_metadata_enabled": True,
            "document_link_metadata_enabled": True,
            "lifecycle_notes_metadata_enabled": True,
            "operational_notes_metadata_enabled": True,
            "read_only_ui_enabled": True,
            "metadata_only": True,
            "emd_workspace_metadata_only": True,
            "emd_issuance_disabled": True,
            "emd_exchange_disabled": True,
            "emd_refund_disabled": True,
            "emd_voiding_disabled": True,
            "live_gds_ndc_connectivity_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_processing_disabled": True,
            "rfic_rfisc_validation_engine_disabled": True,
            "ssr_osi_transmission_disabled": True,
            "background_workers_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "parallel_duplicate_emd_architecture_disabled": True,
            "automation_disabled": True,
            "emd_workspace_count": emd_workspace_count,
            "emd_workspace_status_counts": emd_workspace_status_counts,
            "emd_document_status_counts": emd_document_status_counts,
            "emd_workspace_validating_carrier_count": emd_workspace_validating_carrier_count,
            "emd_workspace_currency_count": emd_workspace_currency_count,
            "emd_workspace_passenger_count": emd_workspace_passenger_count,
            "emd_workspace_rfic_count": emd_workspace_rfic_count,
            "emd_workspace_rfisc_count": emd_workspace_rfisc_count,
            "emd_workspace_service_category_count": emd_workspace_service_category_count,
            "emd_workspace_booking_reference_count": emd_workspace_booking_reference_count,
            "emd_workspace_operational_workspace_count": emd_workspace_operational_workspace_count,
            "emd_workspace_trip_workspace_count": emd_workspace_trip_workspace_count,
            "emd_workspace_offer_workspace_count": emd_workspace_offer_workspace_count,
            "emd_workspace_booking_workspace_count": emd_workspace_booking_workspace_count,
            "emd_workspace_ticket_workspace_count": emd_workspace_ticket_workspace_count,
            "emd_workspace_coupon_detail_count": emd_workspace_coupon_detail_count,
            "emd_workspace_tax_breakdown_count": emd_workspace_tax_breakdown_count,
            "emd_workspace_associated_ticket_coupon_count": emd_workspace_associated_ticket_coupon_count,
            "emd_workspace_associated_flight_workspace_count": emd_workspace_associated_flight_workspace_count,
            "emd_workspace_ssr_count": emd_workspace_ssr_count,
            "emd_workspace_osi_count": emd_workspace_osi_count,
            "emd_workspace_ancillary_service_count": emd_workspace_ancillary_service_count,
            "emd_workspace_exchange_reference_count": emd_workspace_exchange_reference_count,
            "emd_workspace_refund_reference_count": emd_workspace_refund_reference_count,
            "emd_workspace_void_reference_count": emd_workspace_void_reference_count,
            "emd_workspace_linked_document_count": emd_workspace_linked_document_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.8 stores EMD workspace metadata only and links operational EMD records to the earlier ticket/EMD mirror, service mechanics, and ancillary pricing foundations. It does not issue, exchange, refund, void, validate RFIC/RFISC, transmit SSR/OSI, process payments, connect to GDS or NDC, call airline APIs, run background workers, create duplicate EMD architecture, call external integrations, or automate EMD operations.",
        },
        "ssr_osi_operational_workspace_foundation": {
            "ssr_osi_workspaces_enabled": True,
            "ssr_osi_workspace_metadata_enabled": True,
            "platform_ssr_osi_workspace_metadata_crud_enabled": True,
            "agency_ssr_osi_workspace_read_only_enabled": True,
            "passenger_services_ui_enabled": True,
            "ssr_osi_operations_ui_enabled": True,
            "filter_by_need_category_enabled": True,
            "filter_by_airline_enabled": True,
            "filter_by_approval_status_enabled": True,
            "filter_by_readiness_enabled": True,
            "filter_by_passenger_enabled": True,
            "filter_by_priority_enabled": True,
            "filter_by_rfic_enabled": True,
            "filter_by_rfisc_enabled": True,
            "passenger_need_metadata_enabled": True,
            "service_classification_metadata_enabled": True,
            "ssr_metadata_enabled": True,
            "osi_metadata_enabled": True,
            "airline_handling_metadata_enabled": True,
            "airport_handling_metadata_enabled": True,
            "emd_reference_metadata_enabled": True,
            "document_requirement_metadata_enabled": True,
            "medif_metadata_enabled": True,
            "operational_fulfilment_metadata_enabled": True,
            "readiness_metadata_enabled": True,
            "relationship_metadata_enabled": True,
            "aoie_operational_input_enabled": True,
            "aoie_input_path": "Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder",
            "metadata_only": True,
            "ssr_osi_workspace_metadata_only": True,
            "live_ssr_transmission_disabled": True,
            "live_osi_transmission_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "ai_recommendation_disabled": True,
            "automatic_airline_approval_disabled": True,
            "automatic_emd_issuance_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
            "ssr_osi_workspace_count": ssr_osi_workspace_count,
            "ssr_osi_operational_status_counts": ssr_osi_operational_status_counts,
            "ssr_osi_readiness_status_counts": ssr_osi_readiness_status_counts,
            "ssr_osi_approval_status_counts": ssr_osi_approval_status_counts,
            "ssr_osi_need_category_counts": ssr_osi_need_category_counts,
            "ssr_osi_airline_count": ssr_osi_airline_count,
            "ssr_osi_passenger_count": ssr_osi_passenger_count,
            "ssr_osi_rfic_count": ssr_osi_rfic_count,
            "ssr_osi_rfisc_count": ssr_osi_rfisc_count,
            "ssr_osi_emd_required_count": ssr_osi_emd_required_count,
            "ssr_osi_medif_required_count": ssr_osi_medif_required_count,
            "ssr_osi_approval_required_count": ssr_osi_approval_required_count,
            "ssr_osi_missing_requirement_count": ssr_osi_missing_requirement_count,
            "ssr_osi_unresolved_item_count": ssr_osi_unresolved_item_count,
            "ssr_osi_document_requirement_count": ssr_osi_document_requirement_count,
            "ssr_osi_task_count": ssr_osi_task_count,
            "ssr_osi_timeline_count": ssr_osi_timeline_count,
            "ssr_osi_communication_count": ssr_osi_communication_count,
            "ssr_osi_flight_workspace_count": ssr_osi_flight_workspace_count,
            "ssr_osi_linked_document_count": ssr_osi_linked_document_count,
            "readiness_required": False,
            "diagnostic": "Phase 41.9 stores SSR / OSI operational workspace metadata only. It turns passenger needs into operational service requirement records for future AOIE consumption without live SSR/OSI transmission, GDS/NDC connectivity, airline APIs, AI recommendations, automatic airline approval, automatic EMD issuance, background workers, provider integrations, external API calls, or automation.",
        },
        "document_workspace_foundation": {
            "document_workspaces_enabled": True,
            "document_workspace_metadata_enabled": True,
            "platform_document_workspace_metadata_crud_enabled": True,
            "agency_document_workspace_read_only_enabled": True,
            "platform_document_workspaces_ui_enabled": True,
            "agency_documents_workspace_ui_enabled": True,
            "filter_by_document_type_enabled": True,
            "filter_by_document_status_enabled": True,
            "filter_by_passenger_enabled": True,
            "filter_by_booking_reference_enabled": True,
            "filter_by_related_service_enabled": True,
            "filter_by_required_for_travel_enabled": True,
            "filter_by_verification_status_enabled": True,
            "filter_by_deadline_enabled": True,
            "operational_document_workspace_layer_enabled": True,
            "passenger_workspace_link_enabled": True,
            "travel_request_workspace_link_enabled": True,
            "trip_workspace_link_enabled": True,
            "booking_workspace_link_enabled": True,
            "ticket_workspace_link_enabled": True,
            "emd_workspace_link_enabled": True,
            "ssr_osi_workspace_link_enabled": True,
            "operational_intelligence_record_link_enabled": True,
            "phase_36_5_document_foundation_not_duplicated": True,
            "document_requirement_metadata_enabled": True,
            "document_verification_metadata_enabled": True,
            "document_validity_metadata_enabled": True,
            "document_storage_reference_metadata_enabled": True,
            "document_package_reference_metadata_enabled": True,
            "document_visibility_metadata_enabled": True,
            "metadata_only": True,
            "document_workspace_metadata_only": True,
            "live_document_delivery_disabled": True,
            "e_signature_disabled": True,
            "public_share_links_disabled": True,
            "automatic_pdf_generation_disabled": True,
            "payment_invoice_generation_disabled": True,
            "external_storage_integrations_disabled": True,
            "background_workers_disabled": True,
            "ai_document_generation_disabled": True,
            "automation_disabled": True,
            "document_workspace_count": document_workspace_count,
            "document_workspace_status_counts": document_workspace_status_counts,
            "document_workspace_type_counts": document_workspace_type_counts,
            "document_workspace_verification_status_count": document_workspace_verification_status_count,
            "document_workspace_required_for_travel_count": document_workspace_required_for_travel_count,
            "document_workspace_required_by_airline_count": document_workspace_required_by_airline_count,
            "document_workspace_required_by_airport_count": document_workspace_required_by_airport_count,
            "document_workspace_required_by_authority_count": document_workspace_required_by_authority_count,
            "document_workspace_customer_visible_count": document_workspace_customer_visible_count,
            "document_workspace_airline_visible_count": document_workspace_airline_visible_count,
            "document_workspace_internal_only_count": document_workspace_internal_only_count,
            "document_workspace_passenger_workspace_count": document_workspace_passenger_workspace_count,
            "document_workspace_travel_request_workspace_count": document_workspace_travel_request_workspace_count,
            "document_workspace_trip_workspace_count": document_workspace_trip_workspace_count,
            "document_workspace_booking_workspace_count": document_workspace_booking_workspace_count,
            "document_workspace_ticket_workspace_count": document_workspace_ticket_workspace_count,
            "document_workspace_emd_workspace_count": document_workspace_emd_workspace_count,
            "document_workspace_ssr_osi_workspace_count": document_workspace_ssr_osi_workspace_count,
            "document_workspace_operational_intelligence_record_count": document_workspace_operational_intelligence_record_count,
            "document_workspace_package_count": document_workspace_package_count,
            "document_workspace_render_job_count": document_workspace_render_job_count,
            "document_workspace_share_record_count": document_workspace_share_record_count,
            "document_workspace_storage_reference_count": document_workspace_storage_reference_count,
            "readiness_required": False,
            "diagnostic": "Phase 42.0 stores operational document workspace metadata only. It links documents to passenger, request, trip, booking, ticket, EMD, SSR / OSI, and operational intelligence records without live delivery, e-signature, public share links, automatic PDF generation, payment or invoice generation, external storage integrations, background workers, AI document generation, or duplication of the Phase 36.5 render/package/share foundation.",
        },
        "operational_timeline_workspace_foundation": {
            "operational_timelines_enabled": True,
            "operational_timeline_metadata_enabled": True,
            "platform_operational_timeline_metadata_crud_enabled": True,
            "agency_operational_timeline_read_only_enabled": True,
            "platform_operational_timelines_ui_enabled": True,
            "agency_timeline_ui_enabled": True,
            "chronological_timeline_enabled": True,
            "filter_by_passenger_enabled": True,
            "filter_by_booking_enabled": True,
            "filter_by_ticket_enabled": True,
            "filter_by_emd_enabled": True,
            "filter_by_ssr_enabled": True,
            "filter_by_airline_enabled": True,
            "filter_by_communication_type_enabled": True,
            "filter_by_event_type_enabled": True,
            "filter_by_priority_enabled": True,
            "filter_by_status_enabled": True,
            "filter_by_date_enabled": True,
            "passenger_workspace_link_enabled": True,
            "travel_request_workspace_link_enabled": True,
            "trip_workspace_link_enabled": True,
            "booking_workspace_link_enabled": True,
            "ticket_workspace_link_enabled": True,
            "emd_workspace_link_enabled": True,
            "ssr_osi_workspace_link_enabled": True,
            "document_workspace_link_enabled": True,
            "communication_metadata_enabled": True,
            "approval_metadata_enabled": True,
            "attachment_metadata_enabled": True,
            "visibility_metadata_enabled": True,
            "metadata_only": True,
            "timeline_workspace_metadata_only": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "whatsapp_disabled": True,
            "teams_disabled": True,
            "slack_disabled": True,
            "live_airline_messaging_disabled": True,
            "live_customer_messaging_disabled": True,
            "ai_summarization_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "automation_disabled": True,
            "operational_timeline_count": operational_timeline_count,
            "operational_timeline_event_type_counts": operational_timeline_event_type_counts,
            "operational_timeline_communication_type_counts": operational_timeline_communication_type_counts,
            "operational_timeline_status_count": operational_timeline_status_count,
            "operational_timeline_priority_count": operational_timeline_priority_count,
            "operational_timeline_category_count": operational_timeline_category_count,
            "operational_timeline_passenger_workspace_count": operational_timeline_passenger_workspace_count,
            "operational_timeline_travel_request_workspace_count": operational_timeline_travel_request_workspace_count,
            "operational_timeline_trip_workspace_count": operational_timeline_trip_workspace_count,
            "operational_timeline_booking_workspace_count": operational_timeline_booking_workspace_count,
            "operational_timeline_ticket_workspace_count": operational_timeline_ticket_workspace_count,
            "operational_timeline_emd_workspace_count": operational_timeline_emd_workspace_count,
            "operational_timeline_ssr_osi_workspace_count": operational_timeline_ssr_osi_workspace_count,
            "operational_timeline_document_workspace_count": operational_timeline_document_workspace_count,
            "operational_timeline_attachment_count": operational_timeline_attachment_count,
            "operational_timeline_approval_reference_count": operational_timeline_approval_reference_count,
            "operational_timeline_reminder_required_count": operational_timeline_reminder_required_count,
            "operational_timeline_internal_only_count": operational_timeline_internal_only_count,
            "operational_timeline_passenger_visible_count": operational_timeline_passenger_visible_count,
            "operational_timeline_airline_visible_count": operational_timeline_airline_visible_count,
            "readiness_required": False,
            "diagnostic": "Phase 42.1 stores operational timeline and communication metadata only. It links timeline entries to passenger, request, trip, booking, ticket, EMD, SSR / OSI, and document workspaces without email, SMS, WhatsApp, Teams, Slack, live airline messaging, live customer messaging, AI summarization, background workers, provider integrations, or automation.",
        },
        "passenger_service_workflow_engine_foundation": {
            "passenger_service_workflows_enabled": True,
            "workflow_engine_metadata_enabled": True,
            "platform_passenger_service_workflow_metadata_crud_enabled": True,
            "agency_passenger_service_workflow_read_only_enabled": True,
            "platform_passenger_service_workflows_ui_enabled": True,
            "agency_workflow_engine_ui_enabled": True,
            "workflow_stage_definitions_enabled": True,
            "workflow_readiness_state_definitions_enabled": True,
            "filter_by_workflow_stage_enabled": True,
            "filter_by_readiness_enabled": True,
            "filter_by_passenger_enabled": True,
            "filter_by_airline_enabled": True,
            "filter_by_priority_enabled": True,
            "filter_by_assigned_agent_enabled": True,
            "passenger_workspace_link_enabled": True,
            "travel_request_workspace_link_enabled": True,
            "trip_workspace_link_enabled": True,
            "booking_workspace_link_enabled": True,
            "ticket_workspace_link_enabled": True,
            "emd_workspace_link_enabled": True,
            "ssr_osi_workspace_link_enabled": True,
            "document_workspace_link_enabled": True,
            "timeline_workspace_link_enabled": True,
            "future_aoie_reference_metadata_enabled": True,
            "blocking_requirements_metadata_enabled": True,
            "completed_requirements_metadata_enabled": True,
            "responsible_team_metadata_enabled": True,
            "responsible_agent_metadata_enabled": True,
            "metadata_only": True,
            "workflow_engine_metadata_only": True,
            "automatic_workflow_execution_disabled": True,
            "ai_decision_making_disabled": True,
            "background_workers_disabled": True,
            "airline_apis_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "automatic_approvals_disabled": True,
            "automatic_ticketing_disabled": True,
            "automatic_emd_issuance_disabled": True,
            "automatic_messaging_disabled": True,
            "provider_integrations_disabled": True,
            "automation_disabled": True,
            "passenger_service_workflow_count": passenger_service_workflow_count,
            "passenger_service_workflow_stage_counts": passenger_service_workflow_stage_counts,
            "passenger_service_workflow_readiness_counts": passenger_service_workflow_readiness_counts,
            "passenger_service_workflow_status_count": passenger_service_workflow_status_count,
            "passenger_service_workflow_type_count": passenger_service_workflow_type_count,
            "passenger_service_workflow_priority_count": passenger_service_workflow_priority_count,
            "passenger_service_workflow_airline_count": passenger_service_workflow_airline_count,
            "passenger_service_workflow_assigned_agent_count": passenger_service_workflow_assigned_agent_count,
            "passenger_service_workflow_passenger_workspace_count": passenger_service_workflow_passenger_workspace_count,
            "passenger_service_workflow_travel_request_workspace_count": passenger_service_workflow_travel_request_workspace_count,
            "passenger_service_workflow_trip_workspace_count": passenger_service_workflow_trip_workspace_count,
            "passenger_service_workflow_booking_workspace_count": passenger_service_workflow_booking_workspace_count,
            "passenger_service_workflow_ticket_workspace_count": passenger_service_workflow_ticket_workspace_count,
            "passenger_service_workflow_emd_workspace_count": passenger_service_workflow_emd_workspace_count,
            "passenger_service_workflow_ssr_osi_workspace_count": passenger_service_workflow_ssr_osi_workspace_count,
            "passenger_service_workflow_document_workspace_count": passenger_service_workflow_document_workspace_count,
            "passenger_service_workflow_timeline_workspace_count": passenger_service_workflow_timeline_workspace_count,
            "passenger_service_workflow_blocking_requirement_count": passenger_service_workflow_blocking_requirement_count,
            "passenger_service_workflow_completed_requirement_count": passenger_service_workflow_completed_requirement_count,
            "passenger_service_workflow_recommendation_pack_count": passenger_service_workflow_recommendation_pack_count,
            "readiness_required": False,
            "diagnostic": "Phase 42.2 stores Passenger Service Workflow Engine metadata only. It coordinates passenger, request, trip, booking, ticket, EMD, SSR / OSI, document, timeline, and future AOIE references without automatic workflow execution, AI decision making, background workers, airline APIs, GDS/NDC connectivity, automatic approvals, ticketing, EMD issuance, messaging, provider integrations, or automation.",
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


async def public_readiness_payload() -> dict:
    settings = get_settings()
    config = validate_config(settings, include_storage=False)
    database_status = await database.readiness()
    inventory = {
        key: value
        for key, value in SMOKE_INVENTORY_SUMMARY.items()
        if key
        in {
            "total_smoke_scripts",
            "inventoried_smoke_scripts",
            "unresolved_scripts",
            "inventory_validation_ready",
        }
    }
    return {
        "ok": bool(config.get("ok") and database_status.get("ok")),
        "service": "AeroAssist AgencyOS API",
        "phase": CURRENT_BUILD_PHASE,
        "readiness_mode": "public_summary",
        "diagnostics": {
            "configuration": "ready" if config.get("ok") else "attention_required",
            "database": "ready" if database_status.get("ok") else "unavailable",
        },
        "inventory": inventory,
        "authentication_security_http_hardening_foundation": security_readiness_metadata(settings),
    }


@app.get("/api/readiness")
async def readiness(authorization: str | None = Header(default=None)) -> dict:
    settings = get_settings()
    if settings.readiness_public_mode == "detailed":
        return await internal_readiness_payload()
    if settings.readiness_authenticated_detail_enabled and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        result = await validate_auth_token(database, token, update_last_seen=False)
        if result.valid and result.identity:
            user = await database.collection("platform_users").find_one({"email": result.identity.get("email")})
            if user and user.get("status") == "active" and user.get("global_role"):
                return await internal_readiness_payload()
    return await public_readiness_payload()


@app.get("/api/system/readiness")
async def system_readiness(x_internal_readiness_key: str | None = Header(default=None)) -> dict:
    if not internal_readiness_authorized(x_internal_readiness_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return await internal_readiness_payload()


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
app.include_router(platform_airline_operational_intelligence.router)
app.include_router(platform_airline_knowledge_acquisition.router)
app.include_router(platform_operational_constraints.router)
app.include_router(platform_airline_knowledge_normalisation.router)
app.include_router(platform_airline_knowledge_governance.router)
app.include_router(platform_airline_capability_matrix.router)
app.include_router(platform_operational_evaluations.router)
app.include_router(platform_passenger_service_feasibility.router)
app.include_router(platform_airline_recommendations.router)
app.include_router(platform_intelligent_offer_builder.router)
app.include_router(platform_operational_intelligence_cases.router)
app.include_router(platform_reference_data_engine.router)
app.include_router(platform_knowledge_import_templates.router)
app.include_router(platform_visual_policy_editor.router)
app.include_router(platform_pricing_formula_builder.router)
app.include_router(platform_operational_rule_composer.router)
app.include_router(platform_knowledge_quality_assurance.router)
app.include_router(platform_airline_knowledge_publishing.router)
app.include_router(platform_operational_scenario_testing.router)
app.include_router(platform_knowledge_population_toolkit.router)
app.include_router(platform_pilot_readiness.router)
app.include_router(platform_service_parameter_taxonomies.router)
app.include_router(platform_request_segment_services.router)
app.include_router(platform_client_passenger_master.router)
app.include_router(platform_saas_subscriptions.router)
app.include_router(platform_feature_flags.router)
app.include_router(platform_feature_flag_audits.router)
app.include_router(platform_feature_flag_bundles.router)
app.include_router(platform_feature_bundle_assignments.router)
app.include_router(platform_feature_bundle_rollout_readiness.router)
app.include_router(platform_feature_bundle_rollout_plans.router)
app.include_router(platform_feature_bundle_rollout_approvals.router)
app.include_router(platform_feature_bundle_rollout_schedule.router)
app.include_router(platform_feature_bundle_rollout_timeline.router)
app.include_router(platform_feature_bundle_dependencies.router)
app.include_router(platform_feature_bundle_rollout_risks.router)
app.include_router(platform_feature_bundle_rollout_issues.router)
app.include_router(platform_feature_bundle_rollout_decisions.router)
app.include_router(platform_feature_bundle_rollout_change_requests.router)
app.include_router(platform_feature_bundle_rollout_rollback_plans.router)
app.include_router(platform_feature_bundle_rollout_summary_packs.router)
app.include_router(platform_operational_travel_workspaces.router)
app.include_router(platform_travel_request_workspaces.router)
app.include_router(platform_passenger_workspaces.router)
app.include_router(platform_flight_workspaces.router)
app.include_router(platform_trip_workspaces.router)
app.include_router(platform_offer_workspaces.router)
app.include_router(platform_booking_workspaces.router)
app.include_router(platform_ticket_workspaces.router)
app.include_router(platform_emd_workspaces.router)
app.include_router(platform_ssr_osi_workspaces.router)
app.include_router(platform_document_workspaces.router)
app.include_router(platform_operational_timelines.router)
app.include_router(platform_operational_workflows.router)
app.include_router(platform_agent_work_queues.router)
app.include_router(platform_operational_sla_deadlines.router)
app.include_router(platform_task_automation.router)
app.include_router(platform_request_trip_conversion.router)
app.include_router(platform_offer_booking_handoffs.router)
app.include_router(platform_after_sales_workflows.router)
app.include_router(platform_operations_governance.router)
app.include_router(platform_operational_workflow_maturity.router)
app.include_router(platform_airline_master_profiles.router)
app.include_router(platform_airline_policy_evidence_governance.router)
app.include_router(platform_airline_knowledge_versioning.router)
app.include_router(platform_airline_service_coverage.router)
app.include_router(platform_airline_distribution_capabilities.router)
app.include_router(platform_interline_codeshare_intelligence.router)
app.include_router(platform_airline_fare_brand_intelligence.router)
app.include_router(platform_airline_contact_intelligence.router)
app.include_router(platform_airline_intelligence_readiness.router)
app.include_router(platform_journey_engine.router)
app.include_router(platform_journey_authoring.router)
app.include_router(platform_journey_option_composition.router)
app.include_router(platform_journey_comparison_presentations.router)
app.include_router(platform_offer_delivery_diagnostics.router)
app.include_router(platform_passenger_service_workflows.router)
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
app.include_router(agency_airline_operational_intelligence.router)
app.include_router(agency_airline_knowledge_acquisition.router)
app.include_router(agency_operational_constraints.router)
app.include_router(agency_airline_knowledge_normalisation.router)
app.include_router(agency_airline_knowledge_governance.router)
app.include_router(agency_airline_capability_matrix.router)
app.include_router(agency_operational_evaluations.router)
app.include_router(agency_passenger_service_feasibility.router)
app.include_router(agency_airline_recommendations.router)
app.include_router(agency_intelligent_offer_builder.router)
app.include_router(agency_operational_intelligence_cases.router)
app.include_router(agency_reference_data_engine.router)
app.include_router(agency_knowledge_import_templates.router)
app.include_router(agency_visual_policy_editor.router)
app.include_router(agency_pricing_formula_builder.router)
app.include_router(agency_operational_rule_composer.router)
app.include_router(agency_knowledge_quality_assurance.router)
app.include_router(agency_airline_knowledge_publishing.router)
app.include_router(agency_operational_scenario_testing.router)
app.include_router(agency_knowledge_population_toolkit.router)
app.include_router(agency_pilot_readiness.router)
app.include_router(agency_airline_intelligence_readiness.router)
app.include_router(agency_journeys.router)
app.include_router(agency_journey_authoring.router)
app.include_router(agency_journey_option_composition.router)
app.include_router(agency_journey_comparison_presentations.router)
app.include_router(agency_offer_deliveries.router)
app.include_router(agency_service_parameter_taxonomies.router)
app.include_router(agency_request_segment_services.router)
app.include_router(agency_client_passenger_master.router)
app.include_router(agency_saas_subscriptions.router)
app.include_router(agency_feature_flags.router)
app.include_router(agency_feature_flag_readiness.router)
app.include_router(agency_feature_flag_bundles.router)
app.include_router(agency_feature_bundle_assignments.router)
app.include_router(agency_feature_bundle_rollout_readiness.router)
app.include_router(agency_feature_bundle_rollout_plans.router)
app.include_router(agency_feature_bundle_rollout_approvals.router)
app.include_router(agency_feature_bundle_rollout_schedule.router)
app.include_router(agency_feature_bundle_rollout_timeline.router)
app.include_router(agency_feature_bundle_dependencies.router)
app.include_router(agency_feature_bundle_rollout_risks.router)
app.include_router(agency_feature_bundle_rollout_issues.router)
app.include_router(agency_feature_bundle_rollout_decisions.router)
app.include_router(agency_feature_bundle_rollout_change_requests.router)
app.include_router(agency_feature_bundle_rollout_rollback_plans.router)
app.include_router(agency_feature_bundle_rollout_summary_packs.router)
app.include_router(agency_operational_travel_workspaces.router)
app.include_router(agency_travel_request_workspaces.router)
app.include_router(agency_passenger_workspaces.router)
app.include_router(agency_flight_workspaces.router)
app.include_router(agency_trip_workspaces.router)
app.include_router(agency_offer_workspaces.router)
app.include_router(agency_ticket_workspaces.router)
app.include_router(agency_emd_workspaces.router)
app.include_router(agency_ssr_osi_workspaces.router)
app.include_router(agency_document_workspaces.router)
app.include_router(agency_operational_timelines.router)
app.include_router(agency_operational_workflows.router)
app.include_router(agency_agent_work_queues.router)
app.include_router(agency_operational_sla_deadlines.router)
app.include_router(agency_task_automation.router)
app.include_router(agency_request_trip_conversion.router)
app.include_router(agency_offer_booking_handoffs.router)
app.include_router(agency_after_sales_workflows.router)
app.include_router(agency_operations_command_center.router)
app.include_router(agency_operational_workflow_maturity.router)
app.include_router(agency_airline_master_profiles.router)
app.include_router(agency_airline_policy_evidence_governance.router)
app.include_router(agency_airline_knowledge_versioning.router)
app.include_router(agency_airline_service_coverage.router)
app.include_router(agency_airline_distribution_capabilities.router)
app.include_router(agency_interline_codeshare_intelligence.router)
app.include_router(agency_airline_fare_brand_intelligence.router)
app.include_router(agency_airline_contact_directory.router)
app.include_router(agency_passenger_service_workflows.router)
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
app.include_router(portal_offer_deliveries.router)
app.include_router(reference.router)
app.include_router(platform_reference.router)
app.include_router(form_profiles.router)
app.include_router(form_profiles.agency_router)
app.include_router(form_profiles.public_router)
