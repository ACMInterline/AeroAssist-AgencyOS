from __future__ import annotations

from typing import Any


PHASE_LABEL = "phase_37_5_offer_decision_export_foundation"


ADOPTION_ITEMS: list[dict[str, Any]] = [
    {
        "category": "RBAC",
        "concept": "Authentication & RBAC",
        "supplementary_concept": "users, roles, user_roles, permissions, role_permissions",
        "current_equivalent": "platform_users, auth_identities, auth_sessions, agency_staff_memberships, invitation records, platform/agency role helpers",
        "status": "built differently",
        "action": "Do not duplicate RBAC; current platform and agency role model remains canonical.",
    },
    {
        "category": "Airline Intelligence",
        "concept": "Airlines and operating intelligence",
        "supplementary_concept": "airlines, airline_contacts, airline_fleet, aircraft, routes, fare families, RBD matrix, fare rules, ancillaries, interline, distribution, PSS/GDS parameters, exception rules",
        "current_equivalent": "airline_profiles, airline_intelligence_profiles, airline_contacts, airline_fleet_types, aircraft_tail_numbers, aircraft_configurations, aircraft_seatmaps, airline_routes, airline_fare_families, airline_rbd_matrix_rows, airline_fare_rules, airline_ancillaries, airline_interline_agreements, airline_distribution_profiles, airline_pss_parameters, airline_gds_parameters, unified_exception_rules",
        "status": "partially built",
        "action": "Use existing Phase 36 airline intelligence and Rules & Services structures; add only AirlineBrandAsset foundation now.",
    },
    {
        "category": "GDS/Supplier",
        "concept": "Supplier and parser layer",
        "supplementary_concept": "supplier_endpoints, supplier_credentials, supplier_health, supplier_failover_log, gds_ai_normalizer_traces",
        "current_equivalent": "gds_parser_profiles, gds_parser_versions, gds_parser_runs, gds_parsed_entities, gds_parse_corrections, gds_parse_training_samples, gds_parser_evaluation_runs, plus provider target placeholders on booking records/workspaces; no live supplier execution",
        "status": "built",
        "action": "Use Phase 36.6 governed parser foundations; defer credentials, health, failover, and execution.",
    },
    {
        "category": "Requests/Trips/Offers/Bookings",
        "concept": "Operational workflow",
        "supplementary_concept": "trip_requests, trip_segments, offers, offer_items, bookings, pnr_snapshots",
        "current_equivalent": "request_intakes, travel_requests, request_segments, trip_dossiers, trip_segments, offer_workspaces, offer_options, offer_builder_segments, fare bundles, pricing lines, booking_workspaces, booking_records.internal_pnr_mirror_json",
        "status": "built",
        "action": "Map supplementary workflow to existing AgencyOS request/trip/offer/booking lifecycle.",
    },
    {
        "category": "Tickets/EMDs",
        "concept": "Ticket and EMD mirrors",
        "supplementary_concept": "tickets, ticket coupons, EMDs, EMD coupons",
        "current_equivalent": "ticket_records, ticket_coupons, emd_records, emd_coupons, ticket_emd_timeline_events",
        "status": "built",
        "action": "Recognize Phase 36.4 Tickets + EMD Foundation; do not create duplicate ticket or EMD models.",
    },
    {
        "category": "Documents",
        "concept": "Documents, templates, shares, designer",
        "supplementary_concept": "documents, document_versions, document_shares, document_templates, document designer",
        "current_equivalent": "document_templates, document_render_jobs, document_packages, document_share_records, rendered_documents, document_exports, document_deliveries, document_storage_records",
        "status": "built",
        "action": "Recognize Phase 36.5 document foundation; defer visual designer, version governance, public links, and automatic delivery.",
    },
    {
        "category": "AI systems",
        "concept": "Unified AI trace and ADM risk",
        "supplementary_concept": "ai_parsing_logs, ai_offerbuilder_logs, ai_pnrfix_logs, ai_debug_console_logs, ai_model_config, airline_ai_trace, adm_risk_events",
        "current_equivalent": "new AiTraceEvent and AdmRiskEvent foundations",
        "status": "add foundation now",
        "action": "Use one unified AiTraceEvent collection instead of fragmented ai_* logs; add AdmRiskEvent without implementing live AI engines.",
    },
    {
        "category": "Audit/Telemetry",
        "concept": "Audit and operational telemetry",
        "supplementary_concept": "audit_logs, error_logs, system_events, api_usage_logs",
        "current_equivalent": "audit_events plus workflow timeline events across request, booking, ticket/EMD, refund/exchange, and documents",
        "status": "built differently",
        "action": "Do not duplicate audit logs; defer formal error/api usage telemetry.",
    },
    {
        "category": "Special Services",
        "concept": "Unified special services",
        "supplementary_concept": "PassengerServiceRequest, MedicalServiceRequest, CargoLikeItem, VipServiceRequest, ExceptionRule, SSR/OSI generator, rules engine",
        "current_equivalent": "PassengerServiceRequest, request_pets, request_special_items, trip_service_items, unified_exception_rules, special_services_service, exception_engine_service, ssr_osi_generator_service, rules_and_services_registry, service catalogue mappings, canonical service taxonomy domains/families/variants/aliases, service mechanics metadata, and ancillary pricing/exception metadata",
        "status": "built differently",
        "action": "Use the lightweight special-services facade, Phase 36.8 canonical taxonomy, and Phase 36.9 service mechanics mapping; do not rebuild parallel medical/cargo/VIP modules.",
    },
    {
        "category": "Service Taxonomy",
        "concept": "Canonical special and ancillary service taxonomy",
        "supplementary_concept": "normalized service families, SSR/GDS labels, ancillary terms, policy applicability and outcomes",
        "current_equivalent": "canonical_service_domains, canonical_service_families, canonical_service_variants, airline_service_aliases, service_applicability_dimensions, service_policy_outcome_types, service_taxonomy_mapping_rules, policy_candidate_taxonomy_links, service_taxonomy_review_corrections",
        "status": "built",
        "action": "Recognize Phase 36.8 taxonomy as canonical meaning foundation; keep mechanics and execution in separate layers.",
    },
    {
        "category": "Service Mechanics",
        "concept": "SSR/OSI and EMD/RFIC/RFISC service mechanics",
        "supplementary_concept": "SSR/OSI request mechanics, recognition patterns, EMD issuance metadata, RFIC/RFISC maps, interline, lifecycle",
        "current_equivalent": "airline_service_communication_rules, ssr_osi_templates, ssr_osi_requirements, ssr_status_recognition_rules, airline_rejection_patterns, airline_service_payment_rules, airline_emd_issuance_rules, airline_rfic_rfisc_mappings, airline_emd_interline_rules, airline_emd_lifecycle_rules, policy_candidate_mechanics_links",
        "status": "foundation adopted",
        "action": "Map communication mechanics separately from payment/EMD mechanics without live SSR/OSI transmission, ticket/EMD issuance, provider execution, or agency auto-promotion.",
    },
    {
        "category": "Ancillary Pricing",
        "concept": "Ancillary pricing schema and service exception expansion",
        "supplementary_concept": "pricing rules, price components, applicability dimensions, pricing matrices, exception conditions, quote scenarios, policy candidate pricing links",
        "current_equivalent": "airline_ancillary_pricing_rules, airline_ancillary_price_components, airline_ancillary_pricing_applicability, airline_ancillary_pricing_matrices, airline_ancillary_pricing_matrix_rows, airline_service_exception_rules, airline_service_price_quote_scenarios, airline_service_price_quote_results, policy_candidate_pricing_links",
        "status": "foundation adopted",
        "action": "Use deterministic non-binding quote estimates and advisory exception metadata without invoices, payments, settlement, EMD/ticket issuance, provider execution, external AI, or agency auto-promotion.",
    },
    {
        "category": "Policy Comparison",
        "concept": "Airline policy comparison and service advisor",
        "supplementary_concept": "airline comparison matrix, service advisor, operational guidance rows, saved comparison views",
        "current_equivalent": "airline_policy_comparison_profiles, airline_policy_comparison_snapshots, airline_policy_comparison_rows, airline_service_advisor_scenarios, airline_service_advisor_results, airline_policy_comparison_saved_views",
        "status": "foundation adopted",
        "action": "Use metadata-only comparison/advisor views with deterministic complexity scoring; do not recommend airlines automatically or execute providers, EMDs, payments, invoices, accounting, or settlement.",
    },
    {
        "category": "Offer Policy Advisor",
        "concept": "Offer builder policy advisor integration",
        "supplementary_concept": "offer-linked service advisor context, offer comparison guidance, manual decision notes",
        "current_equivalent": "offer_policy_advisor_contexts, offer_policy_advisor_airline_rows, offer_policy_advisor_warnings, offer_policy_advisor_decision_notes, offer_policy_advisor_saved_snapshots",
        "status": "foundation adopted",
        "action": "Attach policy comparison, service advisor, ancillary quote, service mechanics, and taxonomy metadata to offer workspaces without automatic airline selection, offer price mutation, provider execution, EMD issuance, payment, invoice, accounting, or settlement.",
    },
    {
        "category": "Offer Decision Pack",
        "concept": "Offer builder advisor consumption and decision pack",
        "supplementary_concept": "offer decision pack, advisor evidence bundle, option review evidence, manual review notes",
        "current_equivalent": "offer_decision_packs, offer_decision_pack_options, offer_decision_pack_evidence, offer_decision_pack_warnings, offer_decision_pack_review_notes, offer_decision_pack_snapshots",
        "status": "foundation adopted",
        "action": "Consume saved advisor evidence into human-reviewed offer decision packs without automatic ranking, offer price mutation, booking, ticketing, EMD issuance, payment, invoice, accounting, settlement, or provider execution.",
    },
    {
        "category": "Offer Decision Explanation",
        "concept": "Offer explanation and decision timeline",
        "supplementary_concept": "decision explanation, evidence references, decision reasons, acknowledgements, timeline, audit snapshots",
        "current_equivalent": "offer_decision_explanations, offer_decision_timeline_events, offer_decision_evidence_references, offer_decision_reasons, offer_decision_acknowledgements, offer_decision_audit_snapshots",
        "status": "foundation adopted",
        "action": "Record human explanation and immutable audit timelines for offer decision packs without automatic recommendation, price mutation, provider execution, booking, ticketing, EMD issuance, payment, invoice, accounting, or settlement.",
    },
    {
        "category": "Offer Decision Export",
        "concept": "Offer decision pack PDF/shareable review export",
        "supplementary_concept": "review PDF export, export sections, artifacts, recipient drafts, export audit",
        "current_equivalent": "offer_decision_exports, offer_decision_export_sections, offer_decision_export_artifacts, offer_decision_export_recipient_drafts, offer_decision_export_audit_events",
        "status": "foundation adopted",
        "action": "Create metadata-only review export records for decision packs and explanations without automatic sending, public links, recommendations, offer price mutation, provider execution, booking, ticketing, EMD issuance, payment, invoice, accounting, or settlement.",
    },
    {
        "category": "Routes",
        "concept": "Route roots",
        "supplementary_concept": "/agent/* and /admin/* route shells",
        "current_equivalent": "/agency/* and /platform/*",
        "status": "intentionally rejected",
        "action": "Keep /agency and /platform canonical; do not introduce /agent or /admin roots.",
    },
    {
        "category": "Booking UX",
        "concept": "Booking workspace creation entry point",
        "supplementary_concept": "booking workflow create/open action",
        "current_equivalent": "/agency/booking-workspaces with readiness, manual booking, and import entry points",
        "status": "built",
        "action": "Recognize accepted-offer readiness, standalone manual, import, and existing-trip change booking paths.",
    },
    {
        "category": "Standalone/Import/Change",
        "concept": "Non-linear agency booking workflows",
        "supplementary_concept": "manual bookings, imported confirmations, existing trip changes, exchanges, reissues",
        "current_equivalent": "BookingImportDraft, TripChangeOperation, TicketExchangeOperation, EmdExchangeOperation, source-context fields",
        "status": "built",
        "action": "Adopt as internal mirror foundations without provider execution, live exchange, refund, void, or payment actions.",
    },
]


ROUTE_POLICY: dict[str, Any] = {
    "canonical_routes": [
        {"root": "/platform/*", "purpose": "Platform owner and global governance/configuration UI."},
        {"root": "/agency/*", "purpose": "Agency operational workspace UI."},
        {"root": "/api/platform/*", "purpose": "Platform owner governance APIs."},
        {"root": "/api/agencies/{agency_id}/*", "purpose": "Agency operational APIs."},
        {"root": "/api/reference/*", "purpose": "Shared consume APIs."},
    ],
    "rejected_routes": [
        {"root": "/agent/*", "reason": "Duplicates the existing agency workspace route root."},
        {"root": "/admin/*", "reason": "Duplicates the existing platform owner route root."},
    ],
    "route_mappings": [
        {"supplementary": "/agent/clients", "agencyos": "/agency/clients"},
        {"supplementary": "/agent/trip-requests", "agencyos": "/agency/requests and /agency/trips"},
        {"supplementary": "/agent/parser", "agencyos": "/agency/gds-parser"},
        {"supplementary": "/agent/parser/imports", "agencyos": "/agency/booking-imports and /agency/gds-parser"},
        {"supplementary": "/admin/exception-rules", "agencyos": "/platform/rules-services"},
        {"supplementary": "/admin/special-services", "agencyos": "/platform/rules-services"},
        {"supplementary": "/admin/ancillary-pricing", "agencyos": "/platform/ancillary-pricing"},
        {"supplementary": "/agent/ancillary-pricing", "agencyos": "/agency/ancillary-pricing"},
        {"supplementary": "/admin/policy-comparison", "agencyos": "/platform/policy-comparison"},
        {"supplementary": "/agent/policy-comparison", "agencyos": "/agency/policy-comparison"},
        {"supplementary": "/agent/service-advisor", "agencyos": "/agency/airline-service-advisor"},
        {"supplementary": "/admin/offer-advisor", "agencyos": "/platform/offer-policy-advisor"},
        {"supplementary": "/agent/offer-advisor", "agencyos": "/agency/offer-policy-advisor"},
        {"supplementary": "/admin/offer-decision-packs", "agencyos": "/platform/offer-decision-packs"},
        {"supplementary": "/agent/offer-decision-packs", "agencyos": "/agency/offer-decision-packs"},
        {"supplementary": "/admin/offer-decision-explanations", "agencyos": "/platform/offer-decision-explanations"},
        {"supplementary": "/agent/offer-decision-explanations", "agencyos": "/agency/offer-decision-explanations"},
        {"supplementary": "/admin/offer-decision-exports", "agencyos": "/platform/offer-decision-exports"},
        {"supplementary": "/agent/offer-decision-exports", "agencyos": "/agency/offer-decision-exports"},
        {"supplementary": "/documents", "agencyos": "/agency/documents and /platform/document-templates"},
        {"supplementary": "/admin/parser", "agencyos": "/platform/gds-parser"},
        {"supplementary": "/tickets", "agencyos": "/agency/tickets-emds"},
        {"supplementary": "/bookings", "agencyos": "/agency/booking-workspaces"},
        {"supplementary": "/changes or /exchanges", "agencyos": "/agency/trips/{trip_id} and /agency/tickets-emds"},
    ],
    "aliases_added": False,
}


NEXT_PHASE_RECOMMENDATIONS: list[dict[str, str]] = [
    {
        "phase": "Phase 37",
        "title": "Provider Import And Issuance Provenance",
        "reason": "Document and governed parser foundations are now in place; the next gap is provider import provenance and reconciliation around booking, ticket, and EMD mirrors.",
    },
    {
        "phase": "Phase 37.6",
        "title": "Airline Intelligence Data Expansion",
        "reason": "Existing airline intelligence tables can receive curated data packs and brand assets.",
    },
    {
        "phase": "Phase 37.7",
        "title": "Special Services UX Unification",
        "reason": "The facade keeps current services canonical while future UI can unify medical, cargo, VIP, and PRM flows.",
    },
    {
        "phase": "Phase 37.8",
        "title": "AI Trace / ADM Risk Console",
        "reason": "AiTraceEvent and AdmRiskEvent foundations need an operator review console before any automation.",
    },
    {
        "phase": "Phase 38",
        "title": "Live Provider/Supplier Execution Planning",
        "reason": "Provider execution must remain disabled by default until explicit integration governance is designed.",
    },
]


def get_blueprint_adoption_map() -> dict[str, Any]:
    return {
        "phase": PHASE_LABEL,
        "items": ADOPTION_ITEMS,
        "statuses": ["built", "built differently", "partially built", "add foundation now", "planned later", "intentionally rejected"],
        "tickets_emd_foundation": "built in Phase 36.4",
        "booking_workspace_creation_entrypoint": "fixed after Phase 36.4",
    }


def get_blueprint_route_policy() -> dict[str, Any]:
    return {"phase": PHASE_LABEL, **ROUTE_POLICY}


def get_blueprint_gap_summary() -> dict[str, Any]:
    return {
        "phase": PHASE_LABEL,
        "foundations_added_now": [
            "AiTraceEvent",
            "AdmRiskEvent",
            "GdsParseSample",
            "AirlineBrandAsset",
            "Blueprint adoption governance API/UI",
            "SpecialServicesUnifiedFacade",
            "BookingImportDraft",
            "TripChangeOperation",
            "TicketExchangeOperation",
            "EmdExchangeOperation",
            "DocumentRenderJob",
            "DocumentPackage",
            "DocumentShareRecord",
            "DocumentContextService and DocumentRenderService",
            "GdsParserProfile",
            "GdsParserVersion",
            "GdsParserRun",
            "GdsParsedEntity",
            "GdsParseCorrection",
            "GdsParseTrainingSample",
            "GdsParserEvaluationRun",
            "CanonicalServiceDomain",
            "CanonicalServiceFamily",
            "CanonicalServiceVariant",
            "AirlineServiceAlias",
            "ServiceApplicabilityDimension",
            "ServicePolicyOutcomeType",
            "ServiceTaxonomyMappingRule",
            "PolicyCandidateTaxonomyLink",
            "ServiceTaxonomyReviewCorrection",
        ],
        "already_built": [
            "Rules & Services foundation",
            "Rule-aware offer builder",
            "Offer acceptance and booking readiness",
            "Booking workspace and BookingRecord/PNR mirror foundation",
            "Tickets + EMD Foundation built in Phase 36.4",
            "Booking workspace creation entry point fixed after Phase 36.4",
            "Standalone booking, import draft, and existing-trip change/exchange foundations built in Phase 36.4.6",
            "Document foundation built in Phase 36.5",
            "GDS parser foundation and training samples built in Phase 36.6",
            "Airline policy ingestion source, extraction, review, and approved knowledge foundation built in Phase 36.7",
            "Canonical special and ancillary service taxonomy foundation built in Phase 36.8",
            "SSR/OSI and EMD/RFIC/RFISC service mechanics mapping foundation built in Phase 36.9",
            "Ancillary pricing schema and exception engine expansion foundation built in Phase 37.0",
            "Policy comparison and service advisor foundation built in Phase 37.1",
            "Offer builder policy advisor integration foundation built in Phase 37.2",
            "Offer builder advisor consumption and decision pack foundation built in Phase 37.3",
            "Offer explanation and decision timeline foundation built in Phase 37.4",
            "Offer decision export foundation built in Phase 37.5",
        ],
        "deferred": [
            "Full visual document designer, document version governance, public sharing links, automatic delivery, and e-signature",
            "Full GDS grammar coverage, provider reconciliation, and live supplier execution",
            "Live SSR/OSI transmission, live ticket/EMD issuance, automatic airline recommendation, and provider-priced reconciliation",
            "Visual airline dashboards",
            "Live AI engines and model configuration console",
            "Supplier credentials, health, failover, and execution",
            "Payment, invoice/accounting expansion, and settlement",
        ],
        "intentionally_rejected": [
            "/agent/* route root",
            "/admin/* route root",
            "Parallel RBAC model",
            "Parallel trip/request/offer/booking/ticket/EMD models",
            "Supabase, Next.js, or Horizons-specific architecture migration",
        ],
        "next_immediate_phase": "Phase 37 - Provider Import And Issuance Provenance",
        "gap_count": 6,
        "rejected_route_count": len(ROUTE_POLICY["rejected_routes"]),
    }


def get_next_phase_recommendations() -> dict[str, Any]:
    return {"phase": PHASE_LABEL, "items": NEXT_PHASE_RECOMMENDATIONS}
