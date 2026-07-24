from __future__ import annotations

from typing import Any

from database import Database
from persistence_query import MAXIMUM_QUERY_LIMIT


HIGH_RISK_DOMAINS = {
    "airlines",
    "airports",
    "service_catalogue",
    "currencies",
    "ssr_osi_codes",
    "document_types",
}


def _usage(
    domain_key: str,
    label: str,
    description: str,
    primary_consumers: list[str],
    used_in_workflows: list[str],
    required_metadata_fields: list[str],
    optional_metadata_fields: list[str],
    import_template_type: str,
    missing_data_risk_level: str,
    secondary_consumers: list[str] | None = None,
    used_in_routes: list[str] | None = None,
    used_in_models: list[str] | None = None,
    enrichment_supported: bool = True,
    bulk_import_supported: bool = True,
    health_checks: list[str] | None = None,
    operational_impact: str | None = None,
    fields_using_reference: list[str] | None = None,
    frontend_selectors: list[str] | None = None,
    migration_reconciliation_status: str = "not_assessed",
) -> dict[str, Any]:
    return {
        "domain_key": domain_key,
        "label": label,
        "description": description,
        "owner_scope": "platform_owner",
        "agency_behavior": ["consume_only", "suggest_changes"],
        "primary_consumers": primary_consumers,
        "secondary_consumers": secondary_consumers or [],
        "used_in_routes": used_in_routes or [],
        "used_in_models": used_in_models or [],
        "fields_using_reference": fields_using_reference or [],
        "frontend_selectors": frontend_selectors or [],
        "used_in_workflows": used_in_workflows,
        "required_metadata_fields": required_metadata_fields,
        "optional_metadata_fields": optional_metadata_fields,
        "bulk_import_supported": bulk_import_supported,
        "import_template_type": import_template_type,
        "enrichment_supported": enrichment_supported,
        "health_checks": health_checks
        or [
            "required_metadata_present",
            "active_workflow_references_explained",
            "review_status_clear",
        ],
        "operational_impact": operational_impact
        or f"{label} records feed {', '.join(used_in_workflows[:3])}. Missing data can reduce automation quality.",
        "missing_data_risk_level": missing_data_risk_level,
        "deactivation_risk": missing_data_risk_level,
        "migration_reconciliation_status": migration_reconciliation_status,
        "usage_counts_available": True,
        "usage_queries_bounded": True,
    }


DOMAIN_USAGE: dict[str, dict[str, Any]] = {
    "passenger_types": _usage(
        "passenger_types",
        "Passenger Type Codes",
        "Canonical passenger classification metadata with historical code and label snapshots.",
        ["passenger_profiles", "request_passengers"],
        ["passenger_profiles", "request_v4", "request_passenger_identity"],
        ["iata_ptc_code", "passenger_category"],
        [
            "age_min_years",
            "age_max_years",
            "requires_date_of_birth",
            "requires_guardian",
            "manual_review_required",
        ],
        "passenger_types",
        "high",
        used_in_routes=[
            "/api/reference/passenger_types/options",
            "/api/agencies/{agency_id}/passengers",
            "/api/agencies/{agency_id}/requests",
        ],
        used_in_models=[
            "GlobalReferenceRecord",
            "PassengerProfile",
            "RequestV4Passenger",
            "RequestPassenger",
        ],
        fields_using_reference=[
            "passenger_type_code_id",
            "passenger_type_code",
            "passenger_type_label",
        ],
        frontend_selectors=["PtcSelect", "PassengerForm", "RequestCreatePage"],
        migration_reconciliation_status="dry_run_analysis_available",
    ),
    "countries": _usage(
        "countries",
        "Countries",
        "Country records used for nationality, residence, addresses, documents, and compliance context.",
        ["passengers", "documents", "visa_compliance", "addresses"],
        ["client_passenger_profiles", "request_intake", "documents", "future_compliance"],
        ["iso2_code", "iso3_code", "currency_iso_code"],
        ["continent", "capital_iata_code", "major_airports", "official_languages", "national_carrier"],
        "countries",
        "medium",
        used_in_routes=["/api/reference/countries", "/api/platform/reference/records"],
        used_in_models=["GlobalReferenceRecord", "Passenger", "Client"],
    ),
    "cities": _usage(
        "cities",
        "Cities",
        "Canonical city references for airport grouping, request display, trip display, and offer route context.",
        ["airports", "requests", "trips", "offer_routes"],
        ["request_builder", "trip_dossier", "offer_builder", "route_display"],
        ["iata_city_code", "city_name", "country_code"],
        ["legacy_codes", "record_type"],
        "cities",
        "medium",
        used_in_models=["GlobalReferenceRecord", "RequestSegment", "TripSegment"],
    ),
    "airports": _usage(
        "airports",
        "Airports",
        "Airport records used by request segments, trip segments, offer routes, and booking readiness segments.",
        ["request_segments", "trip_segments", "offer_routes", "booking_readiness"],
        ["request_builder", "trip_dossier", "offer_builder", "offer_acceptance", "booking_readiness"],
        ["iata_code", "city_code", "country_code"],
        ["icao_code", "timezone", "latitude", "longitude", "airport_type", "is_major_airport"],
        "airports",
        "high",
        used_in_models=["GlobalReferenceRecord", "RequestSegment", "TripSegment", "OfferBuilderSegment"],
    ),
    "airlines": _usage(
        "airlines",
        "Airlines",
        "Airline records connect airline intelligence, rules/services, offers, booking readiness, and future ticketing.",
        ["airline_intelligence", "rules_services", "offer_options", "booking_readiness"],
        ["airline_rules", "special_services", "offer_builder", "offer_acceptance", "booking_readiness"],
        ["iata_code"],
        ["icao_code", "country_code", "distribution_profile", "alliance_code"],
        "airlines",
        "high",
        used_in_models=["GlobalReferenceRecord", "AirlineRulesCore", "OfferOption", "OfferBuilderSegment"],
    ),
    "currencies": _usage(
        "currencies",
        "Currencies",
        "Currency records power offer pricing, accepted pricing snapshots, and future invoices/payments.",
        ["offer_pricing", "accepted_offer_snapshots", "future_finance"],
        ["offer_builder", "offer_acceptance", "booking_readiness", "future_invoices"],
        ["currency_iso_code"],
        ["numeric_code", "minor_unit", "symbol"],
        "currencies",
        "high",
        used_in_models=["GlobalReferenceRecord", "OfferWorkspace", "OfferPricingLine", "BookingReadinessPackage"],
    ),
    "languages": _usage(
        "languages",
        "Languages",
        "Language records support passenger assistance, UMNR/cognitive support, and client documents.",
        ["passenger_support", "documents", "special_services"],
        ["request_builder", "passenger_profiles", "documents", "future_client_localization"],
        ["iso639_1"],
        ["iso639_2", "native_name"],
        "languages",
        "medium",
        used_in_models=["GlobalReferenceRecord", "Passenger"],
    ),
    "service_catalogue": _usage(
        "service_catalogue",
        "Service Catalogue",
        "Canonical service foundation for requests, rules/services, SSR/OSI, offers, acceptance, booking readiness, EMD readiness, and documents.",
        ["request_services", "PassengerServiceRequest", "rules_services", "offer_feasibility", "booking_readiness"],
        ["request_builder", "special_services", "rules_services", "offer_builder", "offer_acceptance", "booking_readiness", "future_emd_readiness", "documents"],
        ["service_key", "label", "category", "status"],
        ["ssr_code", "osi_template", "required_documents_json", "emd_applicability", "segment_scope_default"],
        "service_catalogue",
        "critical",
        used_in_routes=["/api/platform/service-catalogue", "/api/reference/service-catalogue"],
        used_in_models=["ServiceCatalogueRecord", "RequestedService", "PassengerServiceRequest", "BookingReadinessPackage"],
    ),
    "service_categories": _usage(
        "service_categories",
        "Service Categories",
        "Service category records group catalogue services for request, rules, and offer workflows.",
        ["service_catalogue", "request_services", "rules_services"],
        ["request_builder", "special_services", "offer_builder"],
        ["category_key"],
        ["default_rules_category", "sort_order"],
        "service_categories",
        "medium",
        enrichment_supported=False,
    ),
    "ssr_osi_codes": _usage(
        "ssr_osi_codes",
        "SSR/OSI Codes",
        "SSR and OSI code records support deterministic booking previews without live booking execution.",
        ["special_services", "rules_services", "booking_readiness"],
        ["special_services", "offer_acceptance", "booking_readiness"],
        ["code", "message_type"],
        ["description", "airline_scope", "template"],
        "ssr_osi_codes",
        "high",
        used_in_models=["PassengerServiceRequest", "BookingReadinessPackage"],
    ),
    "document_types": _usage(
        "document_types",
        "Document Types",
        "Document type records describe compliance documents required by services, requests, and readiness packages.",
        ["request_compliance", "booking_readiness", "documents"],
        ["request_builder", "special_services", "booking_readiness", "future_documents"],
        ["document_type"],
        ["validity_rules", "service_keys", "country_scope"],
        "document_types",
        "high",
        used_in_models=["GlobalReferenceRecord", "BookingReadinessPackage"],
    ),
    "pet_species": _usage(
        "pet_species",
        "Pet Species",
        "Pet species records support pet/service animal requests, offer feasibility, and booking readiness.",
        ["request_pets", "service_animals", "booking_readiness"],
        ["request_builder", "offer_builder", "booking_readiness", "future_emd_readiness"],
        ["species_key"],
        ["iata_live_animal_category", "default_documents"],
        "pet_species",
        "medium",
    ),
    "pet_breeds": _usage(
        "pet_breeds",
        "Pet Breeds",
        "Pet breed records refine pet and service animal handling decisions.",
        ["request_pets", "service_animals", "booking_readiness"],
        ["request_builder", "offer_builder", "booking_readiness"],
        ["species_code"],
        ["breed_group", "snub_nosed", "size_category"],
        "pet_breeds",
        "medium",
    ),
    "special_item_categories": _usage(
        "special_item_categories",
        "Special Item Categories",
        "Special item categories support requested items, offer fees, booking readiness, and future EMD readiness.",
        ["request_special_items", "offer_pricing", "booking_readiness"],
        ["request_builder", "offer_builder", "offer_acceptance", "booking_readiness", "future_emd_readiness"],
        ["category_key"],
        ["handling_notes", "fee_expected", "ssr_code"],
        "special_item_categories",
        "medium",
    ),
    "aircraft_types": _usage(
        "aircraft_types",
        "Aircraft Types",
        "Aircraft type records support airline intelligence, rules exceptions, and future seat/cabin constraints.",
        ["airline_intelligence", "rules_services", "future_booking"],
        ["airline_rules", "special_services", "future_seatmap"],
        ["iata_aircraft_code"],
        ["icao_aircraft_code", "manufacturer", "family"],
        "aircraft_types",
        "medium",
    ),
    "airline_alliances": _usage(
        "airline_alliances",
        "Airline Alliances",
        "Alliance records support airline grouping, partner logic, and future interline/commercial context.",
        ["airline_intelligence", "future_interline"],
        ["airline_intelligence", "future_booking"],
        ["alliance_key"],
        ["member_airlines", "commercial_notes"],
        "airline_alliances",
        "low",
    ),
    "payment_methods": _usage(
        "payment_methods",
        "Payment Methods",
        "Payment method records support future payment and accounting classification.",
        ["future_payments", "future_accounting"],
        ["future_invoices", "future_payments"],
        ["payment_method_key"],
        ["settlement_type", "requires_reference"],
        "payment_methods",
        "low",
        enrichment_supported=False,
    ),
    "tax_types": _usage(
        "tax_types",
        "Tax Types",
        "Tax type records support future pricing, invoices, and accounting classifications.",
        ["offer_pricing", "future_invoices", "future_accounting"],
        ["offer_builder", "future_finance"],
        ["tax_type_key"],
        ["jurisdiction", "rate_hint"],
        "tax_types",
        "medium",
        enrichment_supported=False,
    ),
}


def _register_unwired_reference_domains() -> None:
    from services.reference_data_service import REFERENCE_DOMAINS

    for domain_key, label in REFERENCE_DOMAINS.items():
        if domain_key in DOMAIN_USAGE:
            continue
        DOMAIN_USAGE[domain_key] = _usage(
            domain_key,
            label,
            f"{label} are governed by GlobalReferenceRecord; consumer wiring remains explicitly inventoried.",
            [],
            [],
            [],
            [],
            domain_key,
            "low",
            enrichment_supported=False,
            fields_using_reference=[],
            frontend_selectors=[],
            migration_reconciliation_status="consumer_wiring_pending",
            operational_impact="No canonical operational consumer is registered yet; deactivation still requires platform governance.",
        )


_register_unwired_reference_domains()


def list_domain_usage() -> list[dict[str, Any]]:
    return [DOMAIN_USAGE[key] for key in sorted(DOMAIN_USAGE)]


def get_domain_usage(domain_key: str) -> dict[str, Any] | None:
    return DOMAIN_USAGE.get(domain_key)


def missing_required_metadata(record: dict[str, Any], usage: dict[str, Any]) -> list[str]:
    metadata = record.get("metadata_json") or record.get("metadata") or {}
    missing = []
    for field in usage.get("required_metadata_fields") or []:
        aliases = {
            "code": [record.get("code"), record.get("key")],
            "document_type": [record.get("code"), record.get("key"), metadata.get("document_type")],
            "category_key": [record.get("code"), record.get("key"), metadata.get("category_key")],
            "species_key": [record.get("code"), record.get("key"), metadata.get("species_key")],
            "payment_method_key": [record.get("code"), record.get("key"), metadata.get("payment_method_key")],
            "tax_type_key": [record.get("code"), record.get("key"), metadata.get("tax_type_key")],
            "alliance_key": [record.get("code"), record.get("key"), metadata.get("alliance_key")],
        }.get(field, [metadata.get(field)])
        if not any(value not in (None, "", [], {}) for value in aliases):
            missing.append(field)
    return missing


def service_missing_required_metadata(record: dict[str, Any], usage: dict[str, Any]) -> list[str]:
    missing = []
    for field in usage.get("required_metadata_fields") or []:
        aliases = {
            "service_key": [record.get("service_key"), record.get("service_code")],
            "label": [record.get("label"), record.get("service_label")],
            "category": [record.get("category"), record.get("service_family_code")],
            "status": [record.get("status"), "active" if record.get("is_active", True) else "archived"],
        }.get(field, [record.get(field)])
        if not any(value not in (None, "", [], {}) for value in aliases):
            missing.append(field)
    return missing


def severity_for_risk(risk: str) -> str:
    return {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "info",
    }.get(risk, "medium")


def action_item(
    domain: str,
    record: dict[str, Any],
    reason: str,
    severity: str,
    consumer_impact: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "domain": domain,
        "record_id": record.get("id"),
        "code": record.get("code") or record.get("key") or record.get("service_key") or record.get("service_code"),
        "label": record.get("label") or record.get("service_label"),
        "reason": reason,
        "severity": severity,
        "consumer_impact": consumer_impact,
        "recommended_action": recommended_action,
    }


def service_code(record: dict[str, Any]) -> str:
    return str(record.get("service_key") or record.get("service_code") or "").upper()


async def workflow_reference_counts(db: Database) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {domain: {} for domain in DOMAIN_USAGE}

    for passenger in await db.collection("passenger_profiles").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        key = str(
            passenger.get("passenger_type_code")
            or passenger.get("passenger_type")
            or ""
        ).upper()
        if key:
            counts["passenger_types"][key] = (
                counts["passenger_types"].get(key, 0) + 1
            )

    for passenger in await db.collection("request_passengers").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        key = str(
            passenger.get("passenger_type_code")
            or passenger.get("snapshot_passenger_type")
            or ""
        ).upper()
        if key:
            counts["passenger_types"][key] = (
                counts["passenger_types"].get(key, 0) + 1
            )

    for segment in await db.collection("request_segments").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        for domain, keys in {
            "airports": [segment.get("origin_airport_code"), segment.get("destination_airport_code")],
            "airlines": [segment.get("marketing_airline"), segment.get("operating_airline"), segment.get("preferred_airline_code")],
        }.items():
            for key in keys:
                if key:
                    counts[domain][str(key).upper()] = counts[domain].get(str(key).upper(), 0) + 1

    for segment in await db.collection("trip_segments").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        for key in [segment.get("origin_airport_code"), segment.get("destination_airport_code")]:
            if key:
                counts["airports"][str(key).upper()] = counts["airports"].get(str(key).upper(), 0) + 1
        for key in [segment.get("marketing_airline_code"), segment.get("operating_airline_code")]:
            if key:
                counts["airlines"][str(key).upper()] = counts["airlines"].get(str(key).upper(), 0) + 1

    for segment in await db.collection("offer_builder_segments").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        for key in [segment.get("origin_airport"), segment.get("destination_airport")]:
            if key:
                counts["airports"][str(key).upper()] = counts["airports"].get(str(key).upper(), 0) + 1
        for key in [segment.get("marketing_airline_code"), segment.get("operating_airline_code")]:
            if key:
                counts["airlines"][str(key).upper()] = counts["airlines"].get(str(key).upper(), 0) + 1

    for option in await db.collection("offer_options").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        if option.get("main_airline_code"):
            key = str(option["main_airline_code"]).upper()
            counts["airlines"][key] = counts["airlines"].get(key, 0) + 1

    for workspace in await db.collection("offer_workspaces").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        if workspace.get("currency"):
            key = str(workspace["currency"]).upper()
            counts["currencies"][key] = counts["currencies"].get(key, 0) + 1

    for line in await db.collection("offer_pricing_lines").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        if line.get("currency"):
            key = str(line["currency"]).upper()
            counts["currencies"][key] = counts["currencies"].get(key, 0) + 1

    for service in await db.collection("requested_services").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        key = str(service.get("service_key") or service.get("service_code") or "").upper()
        if key:
            counts["service_catalogue"][key] = counts["service_catalogue"].get(key, 0) + 1

    for service in await db.collection("passenger_service_requests").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        key = str(service.get("service_key") or service.get("service_type") or service.get("ssr_code") or "").upper()
        if key:
            counts["service_catalogue"][key] = counts["service_catalogue"].get(key, 0) + 1
            counts["ssr_osi_codes"][key] = counts["ssr_osi_codes"].get(key, 0) + 1

    for package in await db.collection("booking_readiness_packages").find_many(
        sort=[("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    ):
        pricing = package.get("pricing_snapshot_json") or {}
        summary = pricing.get("summary") or {}
        if summary.get("currency"):
            key = str(summary["currency"]).upper()
            counts["currencies"][key] = counts["currencies"].get(key, 0) + 1
        for doc in package.get("required_documents_json") or []:
            key = str(doc.get("code") or doc.get("document_type") or doc.get("label") or "").lower()
            if key:
                counts["document_types"][key] = counts["document_types"].get(key, 0) + 1

    return counts


async def reference_action_required(db: Database) -> list[dict[str, Any]]:
    records = await db.collection("global_reference_records").find_many(
        sort=[("domain", 1), ("key", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    )
    services = await db.collection("service_catalogue").find_many(
        sort=[("service_family_code", 1), ("service_code", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT
    )
    suggestions = await db.collection("reference_data_suggestions").find_many(
        {"status": "pending_review"},
        sort=[("created_at", 1), ("id", 1)],
        limit=MAXIMUM_QUERY_LIMIT,
    )
    usage_counts = await workflow_reference_counts(db)
    items: list[dict[str, Any]] = []

    for record in records:
        domain = record.get("domain")
        usage = DOMAIN_USAGE.get(domain)
        if not usage:
            continue
        missing = missing_required_metadata(record, usage)
        if missing:
            items.append(
                action_item(
                    domain,
                    record,
                    f"Missing required metadata: {', '.join(missing)}.",
                    severity_for_risk(usage["missing_data_risk_level"]),
                    usage["operational_impact"],
                    "Open the reference record and complete the required metadata fields.",
                )
            )
        metadata = record.get("metadata_json") or {}
        if metadata.get("data_quality_status") in {"draft", "needs_review"}:
            items.append(
                action_item(
                    domain,
                    record,
                    f"Record quality status is {metadata.get('data_quality_status')}.",
                    "medium",
                    "Draft or review records may still be visible to operators but need platform validation.",
                    "Review the record metadata and mark it verified or archive it.",
                )
            )
        key = str(record.get("code") or record.get("key") or "").upper()
        if usage_counts.get(domain, {}).get(key):
            items.append(
                action_item(
                    domain,
                    record,
                    f"Used by active workflows {usage_counts[domain][key]} time(s).",
                    "info",
                    "This record is referenced by active request, trip, offer, service, or readiness data.",
                    "Prioritize careful review before editing, merging, or archiving.",
                )
            )
        if domain in HIGH_RISK_DOMAINS and not record.get("is_active", True):
            items.append(
                action_item(
                    domain,
                    record,
                    "High-risk operational domain record is inactive.",
                    "medium",
                    usage["operational_impact"],
                    "Confirm the inactive record is intentionally retired and not referenced by active workflows.",
                )
            )

    service_usage = DOMAIN_USAGE["service_catalogue"]
    for service in services:
        missing = service_missing_required_metadata(service, service_usage)
        if missing:
            items.append(
                action_item(
                    "service_catalogue",
                    service,
                    f"Missing required operational service fields: {', '.join(missing)}.",
                    "critical",
                    service_usage["operational_impact"],
                    "Edit the service catalogue record and complete its operational mapping.",
                )
            )
        key = service_code(service)
        if usage_counts.get("service_catalogue", {}).get(key):
            items.append(
                action_item(
                    "service_catalogue",
                    service,
                    f"Used by active service workflows {usage_counts['service_catalogue'][key]} time(s).",
                    "info",
                    "This service is already referenced by request or special-service records.",
                    "Review compatibility before changing keys, SSR mappings, or archive status.",
                )
            )
        if service.get("status") in {"draft", "deprecated"}:
            items.append(
                action_item(
                    "service_catalogue",
                    service,
                    f"Service catalogue status is {service.get('status')}.",
                    "medium",
                    "Draft or deprecated services may affect request choices and booking readiness mapping.",
                    "Review and activate, deprecate intentionally, or archive the service.",
                )
            )

    for suggestion in suggestions:
        items.append(
            {
                "domain": suggestion.get("domain"),
                "record_id": suggestion.get("target_reference_record_id") or suggestion.get("id"),
                "code": suggestion.get("suggested_code"),
                "label": suggestion.get("suggested_label"),
                "reason": "Agency suggestion is pending platform review.",
                "severity": "medium",
                "consumer_impact": "Agency-submitted corrections are not active until reviewed.",
                "recommended_action": "Review, approve, request information, reject, or archive the suggestion.",
            }
        )

    return sorted(items, key=lambda item: (item["severity"] != "critical", item["severity"] != "high", item["domain"], item.get("label") or ""))


async def reference_health(db: Database) -> dict[str, Any]:
    records = await db.collection("global_reference_records").find_many()
    services = await db.collection("service_catalogue").find_many()
    action_items = await reference_action_required(db)
    usage_counts = await workflow_reference_counts(db)

    recently_updated = sorted(
        records,
        key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
        reverse=True,
    )[:12]
    pinned = [
        record
        for record in records
        if (record.get("metadata_json") or {}).get("pinned") is True
    ]
    high_risk_records = [
        record
        for record in records
        if record.get("domain") in HIGH_RISK_DOMAINS
    ]

    return {
        "label": "Reference Health & Action Required",
        "important_records_replaced": True,
        "action_required_count": len(action_items),
        "sections": [
            {
                "key": "missing_required_metadata",
                "label": "Missing Required Metadata",
                "items": [item for item in action_items if item["reason"].startswith("Missing required")],
            },
            {
                "key": "used_by_active_workflows",
                "label": "Used by Active Workflows",
                "items": [item for item in action_items if item["reason"].startswith("Used by active")],
                "usage_counts": usage_counts,
            },
            {
                "key": "recently_imported_or_updated",
                "label": "Recently Imported / Recently Updated",
                "items": [
                    action_item(
                        record.get("domain"),
                        record,
                        "Recently imported or updated by platform owner.",
                        "info",
                        "Recent platform changes may affect consuming workflows.",
                        "Review if the change affects active operational workflows.",
                    )
                    for record in recently_updated
                ],
            },
            {
                "key": "needs_review",
                "label": "Needs Review",
                "items": [
                    item
                    for item in action_items
                    if "quality status" in item["reason"] or "pending platform review" in item["reason"] or "status is" in item["reason"]
                ],
            },
            {
                "key": "pinned_records",
                "label": "Pinned Records",
                "items": [
                    action_item(
                        record.get("domain"),
                        record,
                        "Pinned by platform owner.",
                        "info",
                        "Pinned records are intentionally highlighted for operations.",
                        "Keep pinned only while the record needs operator attention.",
                    )
                    for record in pinned
                ],
            },
            {
                "key": "high_risk_operational_domains",
                "label": "High-Risk Operational Domains",
                "items": [
                    action_item(
                        record.get("domain"),
                        record,
                        "Record belongs to a high-risk operational domain.",
                        "info",
                        DOMAIN_USAGE[record.get("domain")]["operational_impact"],
                        "Prioritize metadata completeness and cautious edits.",
                    )
                    for record in high_risk_records[:30]
                ]
                + [
                    action_item(
                        "service_catalogue",
                        service,
                        "Record belongs to a high-risk operational domain.",
                        "info",
                        DOMAIN_USAGE["service_catalogue"]["operational_impact"],
                        "Prioritize operational mapping completeness and cautious edits.",
                    )
                    for service in services[:30]
                ],
            },
        ],
    }
