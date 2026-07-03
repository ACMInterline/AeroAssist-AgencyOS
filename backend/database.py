from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import get_settings


IMMUTABLE_UPDATE_FIELDS = {"id", "_id", "agency_id", "created_at"}


def sanitize_updates(updates: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in serialize_document(updates).items()
        if key not in IMMUTABLE_UPDATE_FIELDS
    }


def serialize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    clean = deepcopy(document)
    clean.pop("_id", None)
    return clean


def matches_filter(document: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    if not filters:
        return True
    return all(document.get(key) == value for key, value in filters.items())


class InMemoryCollection:
    def __init__(self) -> None:
        self.documents: Dict[str, Dict[str, Any]] = {}

    async def find_many(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return [
            serialize_document(document)
            for document in self.documents.values()
            if matches_filter(document, filters)
        ]

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for document in self.documents.values():
            if matches_filter(document, filters):
                return serialize_document(document)
        return None

    async def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        clean = serialize_document(document)
        self.documents[clean["id"]] = clean
        return serialize_document(clean)

    async def update_one(self, filters: Dict[str, Any], updates: Dict[str, Any], allow_agency_update: bool = False) -> Optional[Dict[str, Any]]:
        updates = serialize_document(updates) if allow_agency_update else sanitize_updates(updates)
        if allow_agency_update:
            updates = {key: value for key, value in updates.items() if key not in {"id", "_id", "created_at"}}
        for document_id, document in self.documents.items():
            if matches_filter(document, filters):
                updated = serialize_document(document)
                updated.update(updates)
                updated["updated_at"] = datetime.now(timezone.utc)
                self.documents[document_id] = updated
                return serialize_document(updated)
        return None

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(await self.find_many(filters))


class MongoCollection:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def find_many(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        cursor = self.collection.find(filters or {})
        return [serialize_document(document) async for document in cursor]

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        document = await self.collection.find_one(filters)
        return serialize_document(document) if document else None

    async def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        clean = serialize_document(document)
        await self.collection.insert_one(clean)
        return serialize_document(clean)

    async def update_one(self, filters: Dict[str, Any], updates: Dict[str, Any], allow_agency_update: bool = False) -> Optional[Dict[str, Any]]:
        from pymongo import ReturnDocument

        updates = serialize_document(updates) if allow_agency_update else sanitize_updates(updates)
        if allow_agency_update:
            updates = {key: value for key, value in updates.items() if key not in {"id", "_id", "created_at"}}
        updates["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            filters,
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(result) if result else None

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return await self.collection.count_documents(filters or {})


class Database:
    def __init__(self) -> None:
        settings = get_settings()
        self.mode = settings.db_mode
        self.mongodb_url = settings.mongodb_url
        self.mongodb_database = settings.mongodb_database
        self._memory_collections: Dict[str, InMemoryCollection] = {}
        self._mongo_database: Optional[Any] = None
        self._mongo_client: Optional[Any] = None

    async def connect(self) -> None:
        if self.mode != "mongo":
            return

        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(self.mongodb_url)
        self._mongo_client = client
        self._mongo_database = client[self.mongodb_database]
        await ensure_mongo_indexes(self._mongo_database)

    async def readiness(self) -> Dict[str, Any]:
        if self.mode != "mongo":
            return {"ok": True, "mode": self.mode, "diagnostic": "In-memory database is available."}
        if self._mongo_client is None or self._mongo_database is None:
            return {"ok": False, "mode": self.mode, "diagnostic": "MongoDB is not connected."}
        try:
            await self._mongo_client.admin.command("ping")
        except Exception as exc:
            return {"ok": False, "mode": self.mode, "diagnostic": f"MongoDB ping failed: {exc.__class__.__name__}"}
        return {"ok": True, "mode": self.mode, "database": self.mongodb_database, "diagnostic": "MongoDB ping succeeded."}

    def collection(self, name: str) -> InMemoryCollection | MongoCollection:
        if self.mode == "mongo":
            if self._mongo_database is None:
                raise RuntimeError("MongoDB mode is enabled but database is not connected.")
            return MongoCollection(self._mongo_database[name])

        if name not in self._memory_collections:
            self._memory_collections[name] = InMemoryCollection()
        return self._memory_collections[name]


database = Database()


async def get_database() -> Database:
    return database


def normalize_index_spec(index_spec: Any, default_options: Optional[Dict[str, Any]] = None) -> tuple[list[tuple[str, Any]], Dict[str, Any]]:
    options = dict(default_options or {})
    if isinstance(index_spec, dict):
        keys = list(index_spec["keys"])
        options.update({key: value for key, value in index_spec.items() if key != "keys"})
        return keys, options
    return list(index_spec), options


def index_options_compatible(existing: Dict[str, Any], requested_options: Dict[str, Any]) -> bool:
    requested_unique = bool(requested_options.get("unique", False))
    existing_unique = bool(existing.get("unique", False))
    if requested_unique and not existing_unique:
        return False

    if "sparse" in requested_options:
        if bool(existing.get("sparse", False)) != bool(requested_options["sparse"]):
            return False
    elif existing.get("sparse"):
        return False

    requested_partial = requested_options.get("partialFilterExpression")
    existing_partial = existing.get("partialFilterExpression")
    if requested_partial is not None:
        if existing_partial != requested_partial:
            return False
    elif existing_partial is not None:
        return False

    for option_name in ["expireAfterSeconds", "collation"]:
        requested_option = requested_options.get(option_name)
        existing_option = existing.get(option_name)
        if requested_option is not None:
            if existing_option != requested_option:
                return False
        elif existing_option is not None:
            return False

    return True


def describe_index(keys: list[tuple[str, Any]], options: Dict[str, Any]) -> str:
    parts = [f"keys={keys}"]
    if options.get("name"):
        parts.append(f"name={options['name']!r}")
    for key in ["unique", "sparse", "partialFilterExpression"]:
        if key in options:
            parts.append(f"{key}={options[key]!r}")
    return ", ".join(parts)


async def create_compatible_index(collection: Any, collection_name: str, index_spec: Any, **default_options: Any) -> None:
    keys, options = normalize_index_spec(index_spec, default_options)
    requested_name = options.get("name")
    existing_indexes = await collection.index_information()

    if requested_name and requested_name in existing_indexes:
        existing = existing_indexes[requested_name]
        existing_keys = list(existing.get("key") or [])
        if existing_keys == keys and index_options_compatible(existing, options):
            return
        raise RuntimeError(
            f"Mongo index conflict on {collection_name}.{requested_name}: "
            f"existing keys={existing_keys}, requested {describe_index(keys, options)}"
        )

    for existing_name, existing in existing_indexes.items():
        if list(existing.get("key") or []) != keys:
            continue
        if index_options_compatible(existing, options):
            return
        raise RuntimeError(
            f"Mongo index conflict on {collection_name}: existing index {existing_name!r} "
            f"has the same key pattern but incompatible options for requested {describe_index(keys, options)}"
        )

    await collection.create_index(keys, **options)


AGENCY_OWNED_COLLECTIONS = [
    "agency_staff_memberships",
    "agency_workspaces",
    "agency_branding_settings",
    "agency_branding_assets",
    "agency_form_profiles",
    "agency_form_field_settings",
    "agency_website_settings",
    "agency_website_pages",
    "agency_website_media_assets",
    "client_profiles",
    "request_intakes",
    "portal_access_mappings",
    "passenger_profiles",
    "client_passenger_relationships",
    "travel_requests",
    "trip_dossiers",
    "trip_passengers",
    "trip_segments",
    "trip_service_items",
    "trip_timeline_events",
    "request_case_flags",
    "request_passengers",
    "request_segments",
    "requested_services",
    "request_passenger_segment_services",
    "passenger_service_requests",
    "request_pets",
    "request_pet_segment_transport",
    "request_special_items",
    "request_special_item_segments",
    "request_messages",
    "request_tasks",
    "request_timeline_events",
    "offers",
    "offer_passengers",
    "offer_route_alternatives",
    "offer_segments",
    "offer_fare_options",
    "offer_price_lines",
    "offer_service_checks",
    "offer_timeline_events",
    "offer_workspaces",
    "offer_options",
    "offer_routing_options",
    "offer_builder_segments",
    "offer_fare_bundles",
    "offer_pricing_lines",
    "offer_comparison_snapshots",
    "offer_policy_advisor_contexts",
    "offer_policy_advisor_airline_rows",
    "offer_policy_advisor_warnings",
    "offer_policy_advisor_decision_notes",
    "offer_policy_advisor_saved_snapshots",
    "offer_decision_packs",
    "offer_decision_pack_options",
    "offer_decision_pack_evidence",
    "offer_decision_pack_warnings",
    "offer_decision_pack_review_notes",
    "offer_decision_pack_snapshots",
    "offer_decision_explanations",
    "offer_decision_timeline_events",
    "offer_decision_evidence_references",
    "offer_decision_reasons",
    "offer_decision_acknowledgements",
    "offer_decision_audit_snapshots",
    "offer_decision_exports",
    "offer_decision_export_sections",
    "offer_decision_export_artifacts",
    "offer_decision_export_recipient_drafts",
    "offer_decision_export_audit_events",
    "offer_decision_export_previews",
    "offer_decision_export_preview_sections",
    "offer_decision_export_preview_blocks",
    "offer_decision_export_preview_validations",
    "offer_decision_export_preview_snapshots",
    "offer_decision_export_approvals",
    "offer_decision_export_approval_checkpoints",
    "offer_decision_export_release_readiness",
    "offer_decision_export_release_holds",
    "offer_decision_export_release_snapshots",
    "offer_decision_export_delivery_handoffs",
    "offer_decision_export_delivery_recipients",
    "offer_decision_export_delivery_attachments",
    "offer_decision_export_delivery_instructions",
    "offer_decision_export_delivery_snapshots",
    "offer_decision_export_delivery_outcomes",
    "offer_decision_export_delivery_outcome_events",
    "offer_decision_export_delivery_receipts",
    "offer_decision_export_delivery_issues",
    "offer_decision_export_delivery_outcome_snapshots",
    "offer_decision_export_audit_reviews",
    "offer_decision_export_audit_review_findings",
    "offer_decision_export_audit_review_checklist_items",
    "offer_decision_export_audit_review_snapshots",
    "offer_decision_export_governance_records",
    "offer_decision_export_governance_rules",
    "offer_decision_export_retention_policies",
    "offer_decision_export_legal_bases",
    "offer_decision_export_archive_statuses",
    "offer_decision_export_governance_exceptions",
    "offer_decision_export_governance_snapshots",
    "offer_decision_export_compliance_evidence",
    "offer_decision_export_compliance_requirements",
    "offer_decision_export_compliance_checks",
    "offer_decision_export_compliance_results",
    "offer_decision_export_compliance_exceptions",
    "offer_decision_export_compliance_snapshots",
    "airline_intelligence_data_packs",
    "airline_intelligence_data_pack_items",
    "airline_intelligence_data_pack_validation_issues",
    "airline_intelligence_data_pack_import_runs",
    "airline_intelligence_data_pack_review_notes",
    "airline_intelligence_coverage_snapshots",
    "offer_acceptances",
    "trip_accepted_offer_snapshots",
    "booking_readiness_packages",
    "booking_workspaces",
    "booking_records",
    "booking_import_drafts",
    "trip_change_operations",
    "bookings",
    "booking_passengers",
    "booking_segments",
    "ticket_records",
    "ticket_coupons",
    "emd_records",
    "emd_coupons",
    "ticket_exchange_operations",
    "emd_exchange_operations",
    "ticket_emd_timeline_events",
    "ai_trace_events",
    "adm_risk_events",
    "gds_parse_samples",
    "gds_parser_runs",
    "gds_parsed_entities",
    "gds_parse_corrections",
    "gds_parse_training_samples",
    "invoices",
    "invoice_line_items",
    "payment_records",
    "booking_timeline_events",
    "refund_exchange_cases",
    "refund_exchange_items",
    "refund_exchange_financial_lines",
    "refund_exchange_messages",
    "refund_exchange_timeline_events",
    "agency_airline_overrides",
    "document_templates",
    "rendered_documents",
    "document_exports",
    "document_deliveries",
    "document_delivery_attempts",
    "document_storage_records",
    "document_render_jobs",
    "document_packages",
    "document_share_records",
    "agency_email_settings",
    "document_timeline_events",
    "portal_action_events",
    "document_acknowledgements",
    "audit_events",
]


async def ensure_mongo_indexes(mongo_database: Any) -> None:
    from pymongo import ASCENDING

    for collection_name in AGENCY_OWNED_COLLECTIONS:
        collection = mongo_database[collection_name]
        await create_compatible_index(collection, collection_name, [("id", ASCENDING)], unique=True)
        await create_compatible_index(collection, collection_name, [("agency_id", ASCENDING)])

    unique_indexes = {
        "platform_users": [[("email", ASCENDING)]],
        "agencies": [[("slug", ASCENDING)], [("id", ASCENDING)]],
        "global_reference_records": [[("domain", ASCENDING), ("key", ASCENDING)], [("id", ASCENDING)]],
        "reference_domain_metadata": [[("domain", ASCENDING)], [("id", ASCENDING)]],
        "reference_data_suggestions": [[("id", ASCENDING)]],
        "reference_import_batches": [[("id", ASCENDING)]],
        "global_field_definitions": [[("field_key", ASCENDING)], [("id", ASCENDING)]],
        "agency_form_profiles": [[("agency_id", ASCENDING), ("profile_key", ASCENDING)]],
        "agency_form_field_settings": [[("agency_id", ASCENDING), ("form_profile_id", ASCENDING), ("field_key", ASCENDING)]],
        "service_catalogue": [[("service_code", ASCENDING)], [("id", ASCENDING)]],
        "airline_profiles": [[("airline_code", ASCENDING)], [("id", ASCENDING)]],
        "airline_intelligence_profiles": [[("id", ASCENDING)]],
        "airline_contacts": [[("id", ASCENDING)]],
        "airline_fleet_types": [[("id", ASCENDING)]],
        "aircraft_tail_numbers": [[("id", ASCENDING)]],
        "aircraft_configurations": [[("id", ASCENDING)]],
        "aircraft_seatmaps": [[("id", ASCENDING)]],
        "airline_routes": [[("id", ASCENDING)]],
        "airline_fare_families": [[("id", ASCENDING)]],
        "airline_rbd_matrix_rows": [[("id", ASCENDING)]],
        "airline_fare_rules": [[("id", ASCENDING)]],
        "airline_ancillaries": [[("id", ASCENDING)]],
        "airline_interline_agreements": [[("id", ASCENDING)]],
        "airline_distribution_profiles": [[("id", ASCENDING)]],
        "airline_pss_parameters": [[("id", ASCENDING)]],
        "airline_gds_parameters": [[("id", ASCENDING)]],
        "airline_exception_rules": [[("id", ASCENDING)]],
        "airline_brand_assets": [[("id", ASCENDING)]],
        "gds_parser_profiles": [[("profile_key", ASCENDING)], [("id", ASCENDING)]],
        "gds_parser_versions": [[("id", ASCENDING)]],
        "gds_parser_evaluation_runs": [[("id", ASCENDING)]],
        "airline_policy_sources": [[("id", ASCENDING)]],
        "airline_policy_sections": [[("id", ASCENDING)]],
        "airline_policy_extraction_runs": [[("id", ASCENDING)]],
        "airline_policy_extracted_rules": [[("id", ASCENDING)]],
        "airline_policy_extracted_prices": [[("id", ASCENDING)]],
        "airline_policy_extracted_communication_rules": [[("id", ASCENDING)]],
        "airline_policy_extracted_emd_rules": [[("id", ASCENDING)]],
        "airline_policy_extracted_exceptions": [[("id", ASCENDING)]],
        "airline_policy_review_corrections": [[("id", ASCENDING)]],
        "airline_policy_approved_knowledge_records": [[("id", ASCENDING)]],
        "canonical_service_domains": [
            {"keys": [("id", ASCENDING)], "name": "canonical_service_domains_id_unique"},
            {"keys": [("code", ASCENDING)], "name": "canonical_service_domains_code_unique"},
        ],
        "canonical_service_families": [
            {"keys": [("id", ASCENDING)], "name": "canonical_service_families_id_unique"},
            {"keys": [("domain_code", ASCENDING), ("code", ASCENDING)], "name": "canonical_service_families_domain_code_code_unique"},
        ],
        "canonical_service_variants": [
            {"keys": [("id", ASCENDING)], "name": "canonical_service_variants_id_unique"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("code", ASCENDING)], "name": "canonical_service_variants_domain_family_code_unique"},
        ],
        "airline_service_aliases": [[("id", ASCENDING)]],
        "service_applicability_dimensions": [
            {"keys": [("id", ASCENDING)], "name": "service_applicability_dimensions_id_unique"},
            {"keys": [("code", ASCENDING)], "name": "service_applicability_dimensions_code_unique"},
        ],
        "service_policy_outcome_types": [
            {"keys": [("id", ASCENDING)], "name": "service_policy_outcome_types_id_unique"},
            {"keys": [("code", ASCENDING)], "name": "service_policy_outcome_types_code_unique"},
        ],
        "service_taxonomy_mapping_rules": [[("id", ASCENDING)]],
        "policy_candidate_taxonomy_links": [[("id", ASCENDING)]],
        "service_taxonomy_review_corrections": [[("id", ASCENDING)]],
        "airline_service_communication_rules": [
            {"keys": [("id", ASCENDING)], "name": "airline_service_communication_rules_id_unique"},
        ],
        "ssr_osi_templates": [
            {"keys": [("id", ASCENDING)], "name": "ssr_osi_templates_id_unique"},
        ],
        "ssr_osi_requirements": [
            {"keys": [("id", ASCENDING)], "name": "ssr_osi_requirements_id_unique"},
        ],
        "ssr_status_recognition_rules": [
            {"keys": [("id", ASCENDING)], "name": "ssr_status_recognition_rules_id_unique"},
        ],
        "airline_rejection_patterns": [
            {"keys": [("id", ASCENDING)], "name": "airline_rejection_patterns_id_unique"},
        ],
        "airline_service_payment_rules": [
            {"keys": [("id", ASCENDING)], "name": "airline_service_payment_rules_id_unique"},
        ],
        "airline_emd_issuance_rules": [
            {"keys": [("id", ASCENDING)], "name": "airline_emd_issuance_rules_id_unique"},
        ],
        "airline_rfic_rfisc_mappings": [
            {"keys": [("id", ASCENDING)], "name": "airline_rfic_rfisc_mappings_id_unique"},
        ],
        "airline_emd_interline_rules": [
            {"keys": [("id", ASCENDING)], "name": "airline_emd_interline_rules_id_unique"},
        ],
        "airline_emd_lifecycle_rules": [
            {"keys": [("id", ASCENDING)], "name": "airline_emd_lifecycle_rules_id_unique"},
        ],
        "policy_candidate_mechanics_links": [
            {"keys": [("id", ASCENDING)], "name": "policy_candidate_mechanics_links_id_unique"},
        ],
        "airline_rules_core": [[("airline_id", ASCENDING)], [("id", ASCENDING)]],
        "unified_exception_rules": [[("id", ASCENDING)]],
        "agency_staff_memberships": [[("agency_id", ASCENDING), ("user_id", ASCENDING)]],
        "portal_access_mappings": [[("agency_id", ASCENDING), ("user_email", ASCENDING)]],
        "auth_identities": [[("normalized_email", ASCENDING)], [("id", ASCENDING)]],
        "auth_sessions": [[("token_hash", ASCENDING)], [("id", ASCENDING)]],
        "invitations": [[("token_hash", ASCENDING)], [("id", ASCENDING)]],
    }
    for collection_name, index_specs in unique_indexes.items():
        collection = mongo_database[collection_name]
        for spec in index_specs:
            await create_compatible_index(collection, collection_name, spec, unique=True)

    compound_indexes = {
        "client_profiles": [[("agency_id", ASCENDING), ("primary_email", ASCENDING)]],
        "invitations": [
            [("agency_id", ASCENDING), ("workspace_id", ASCENDING), ("normalized_email", ASCENDING), ("target_role", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
        ],
        "passenger_profiles": [[("agency_id", ASCENDING), ("display_name", ASCENDING)]],
        "client_passenger_relationships": [
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("passenger_id", ASCENDING)],
            [("agency_id", ASCENDING), ("client_id", ASCENDING), ("passenger_id", ASCENDING)],
        ],
        "travel_requests": [
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("existing_trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_change_operation_id", ASCENDING)],
            [("agency_id", ASCENDING), ("request_purpose", ASCENDING)],
        ],
        "trip_dossiers": [[("agency_id", ASCENDING), ("primary_request_id", ASCENDING)], [("agency_id", ASCENDING), ("trip_reference", ASCENDING)]],
        "trip_passengers": [[("agency_id", ASCENDING), ("trip_id", ASCENDING)], [("agency_id", ASCENDING), ("source_request_passenger_id", ASCENDING)]],
        "trip_segments": [[("agency_id", ASCENDING), ("trip_id", ASCENDING)], [("agency_id", ASCENDING), ("source_request_segment_id", ASCENDING)]],
        "trip_service_items": [[("agency_id", ASCENDING), ("trip_id", ASCENDING)], [("agency_id", ASCENDING), ("source_request_service_id", ASCENDING)], [("agency_id", ASCENDING), ("source_passenger_segment_service_id", ASCENDING)]],
        "trip_timeline_events": [[("agency_id", ASCENDING), ("trip_id", ASCENDING)], [("agency_id", ASCENDING), ("event_type", ASCENDING)]],
        "passenger_service_requests": [
            [("agency_id", ASCENDING), ("request_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_id", ASCENDING)],
            [("agency_id", ASCENDING), ("category", ASCENDING)],
        ],
        "offers": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("request_id", ASCENDING)]],
        "offer_workspaces": [
            [("agency_id", ASCENDING), ("request_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("existing_trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_change_operation_id", ASCENDING)],
            [("agency_id", ASCENDING), ("offer_purpose", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
        ],
        "offer_options": [
            [("agency_id", ASCENDING), ("workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_change_operation_id", ASCENDING)],
            [("agency_id", ASCENDING), ("offer_purpose", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("recommendation_rank", ASCENDING)],
        ],
        "offer_routing_options": [[("agency_id", ASCENDING), ("option_id", ASCENDING)]],
        "offer_builder_segments": [
            [("agency_id", ASCENDING), ("option_id", ASCENDING)],
            [("agency_id", ASCENDING), ("routing_id", ASCENDING)],
            [("agency_id", ASCENDING), ("option_id", ASCENDING), ("sequence", ASCENDING)],
        ],
        "offer_fare_bundles": [[("agency_id", ASCENDING), ("option_id", ASCENDING)]],
        "offer_pricing_lines": [
            [("agency_id", ASCENDING), ("option_id", ASCENDING)],
            [("agency_id", ASCENDING), ("line_type", ASCENDING)],
        ],
        "offer_comparison_snapshots": [
            [("agency_id", ASCENDING), ("workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("generated_at", ASCENDING)],
        ],
        "offer_acceptances": [
            [("agency_id", ASCENDING), ("workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("option_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
        ],
        "trip_accepted_offer_snapshots": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("acceptance_id", ASCENDING)],
        ],
        "booking_readiness_packages": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("acceptance_id", ASCENDING)],
        ],
        "booking_workspaces": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_readiness_package_id", ASCENDING)],
            [("agency_id", ASCENDING), ("offer_acceptance_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("workspace_number", ASCENDING)],
            [("agency_id", ASCENDING), ("source_context", ASCENDING)],
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("import_draft_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_change_operation_id", ASCENDING)],
        ],
        "booking_records": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_readiness_package_id", ASCENDING)],
            [("agency_id", ASCENDING), ("pnr_locator", ASCENDING)],
            [("agency_id", ASCENDING), ("provider", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_status", ASCENDING)],
            [("agency_id", ASCENDING), ("source_context", ASCENDING)],
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("import_draft_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_change_operation_id", ASCENDING)],
        ],
        "booking_import_drafts": [
            [("agency_id", ASCENDING), ("source_type", ASCENDING)],
            [("agency_id", ASCENDING), ("parser_status", ASCENDING)],
            [("agency_id", ASCENDING), ("linked_trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("import_context", ASCENDING)],
            [("agency_id", ASCENDING), ("linked_booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("linked_booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("latest_parser_run_id", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "trip_change_operations": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("request_id", ASCENDING)],
            [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("source_booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("new_booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("operation_type", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "booking_timeline_events": [
            [("agency_id", ASCENDING), ("booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "bookings": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("offer_id", ASCENDING)]],
        "ticket_records": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("source_context", ASCENDING)],
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("passenger_id", ASCENDING)],
            [("agency_id", ASCENDING), ("ticket_number", ASCENDING)],
            [("agency_id", ASCENDING), ("issue_status", ASCENDING)],
            [("agency_id", ASCENDING), ("validating_carrier", ASCENDING)],
            [("agency_id", ASCENDING), ("original_ticket_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("exchange_operation_id", ASCENDING)],
            [("agency_id", ASCENDING), ("import_draft_id", ASCENDING)],
        ],
        "ticket_coupons": [
            [("agency_id", ASCENDING), ("ticket_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("passenger_id", ASCENDING)],
            [("agency_id", ASCENDING), ("segment_id", ASCENDING)],
            [("agency_id", ASCENDING), ("coupon_status", ASCENDING)],
        ],
        "emd_records": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("ticket_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("source_context", ASCENDING)],
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("passenger_id", ASCENDING)],
            [("agency_id", ASCENDING), ("emd_number", ASCENDING)],
            [("agency_id", ASCENDING), ("service_key", ASCENDING)],
            [("agency_id", ASCENDING), ("service_catalogue_id", ASCENDING)],
            [("agency_id", ASCENDING), ("issue_status", ASCENDING)],
            [("agency_id", ASCENDING), ("original_emd_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("exchange_operation_id", ASCENDING)],
            [("agency_id", ASCENDING), ("import_draft_id", ASCENDING)],
        ],
        "emd_coupons": [
            [("agency_id", ASCENDING), ("emd_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("passenger_id", ASCENDING)],
            [("agency_id", ASCENDING), ("segment_id", ASCENDING)],
            [("agency_id", ASCENDING), ("ticket_coupon_id", ASCENDING)],
            [("agency_id", ASCENDING), ("service_key", ASCENDING)],
            [("agency_id", ASCENDING), ("coupon_status", ASCENDING)],
        ],
        "ticket_emd_timeline_events": [
            [("agency_id", ASCENDING), ("booking_workspace_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("ticket_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("emd_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "ticket_exchange_operations": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("original_ticket_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("new_ticket_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("operation_type", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "emd_exchange_operations": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("original_emd_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("new_emd_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("operation_type", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "ai_trace_events": [
            [("agency_id", ASCENDING), ("trace_type", ASCENDING)],
            [("agency_id", ASCENDING), ("source_module", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "adm_risk_events": [
            [("agency_id", ASCENDING), ("trip_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("ticket_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("emd_record_id", ASCENDING)],
            [("agency_id", ASCENDING), ("risk_level", ASCENDING)],
            [("agency_id", ASCENDING), ("airline_id", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "gds_parse_samples": [
            [("agency_id", ASCENDING), ("mode", ASCENDING)],
            [("agency_id", ASCENDING), ("source", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "gds_parser_profiles": [
            [("provider_family", ASCENDING)],
            [("input_format", ASCENDING)],
            [("active", ASCENDING)],
            [("default_for_provider_family", ASCENDING)],
        ],
        "gds_parser_versions": [
            [("parser_profile_id", ASCENDING)],
            [("parser_profile_id", ASCENDING), ("version_label", ASCENDING)],
            [("status", ASCENDING)],
            [("activated_at", ASCENDING)],
            [("created_at", ASCENDING)],
        ],
        "gds_parser_runs": [
            [("agency_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_import_draft_id", ASCENDING)],
            [("agency_id", ASCENDING), ("parser_profile_id", ASCENDING)],
            [("agency_id", ASCENDING), ("parser_version_id", ASCENDING)],
            [("agency_id", ASCENDING), ("parse_status", ASCENDING)],
            [("agency_id", ASCENDING), ("provider_family_detected", ASCENDING)],
            [("agency_id", ASCENDING), ("input_format_detected", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "gds_parsed_entities": [
            [("agency_id", ASCENDING)],
            [("agency_id", ASCENDING), ("parser_run_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_import_draft_id", ASCENDING)],
            [("agency_id", ASCENDING), ("entity_type", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("confidence", ASCENDING)],
        ],
        "gds_parse_corrections": [
            [("agency_id", ASCENDING)],
            [("agency_id", ASCENDING), ("parser_run_id", ASCENDING)],
            [("agency_id", ASCENDING), ("parsed_entity_id", ASCENDING)],
            [("agency_id", ASCENDING), ("booking_import_draft_id", ASCENDING)],
            [("agency_id", ASCENDING), ("entity_type", ASCENDING)],
            [("agency_id", ASCENDING), ("correction_type", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "gds_parse_training_samples": [
            [("scope", ASCENDING)],
            [("agency_id", ASCENDING)],
            [("provider_family", ASCENDING)],
            [("input_format", ASCENDING)],
            [("sample_status", ASCENDING)],
            [("difficulty", ASCENDING)],
            [("created_at", ASCENDING)],
        ],
        "gds_parser_evaluation_runs": [
            [("parser_profile_id", ASCENDING)],
            [("parser_version_id", ASCENDING)],
            [("evaluation_status", ASCENDING)],
            [("created_at", ASCENDING)],
        ],
        "airline_brand_assets": [
            [("airline_id", ASCENDING), ("asset_type", ASCENDING)],
            [("airline_id", ASCENDING), ("active", ASCENDING)],
        ],
        "airline_policy_sources": [
            [("scope", ASCENDING)],
            [("agency_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("airline_iata_code", ASCENDING)],
            [("service_domain", ASCENDING)],
            [("service_family", ASCENDING)],
            [("ingestion_status", ASCENDING)],
            [("raw_text_hash", ASCENDING)],
            [("created_at", ASCENDING)],
        ],
        "airline_policy_sections": [
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("detected_category", ASCENDING)],
            [("section_order", ASCENDING)],
        ],
        "airline_policy_extraction_runs": [
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("extraction_status", ASCENDING)],
            [("created_at", ASCENDING)],
        ],
        "airline_policy_extracted_rules": [
            [("extraction_run_id", ASCENDING)],
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("service_domain", ASCENDING)],
            [("service_family", ASCENDING)],
            [("rule_type", ASCENDING)],
            [("status", ASCENDING)],
            [("confidence", ASCENDING)],
        ],
        "airline_policy_extracted_prices": [
            [("extraction_run_id", ASCENDING)],
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("service_domain", ASCENDING)],
            [("service_family", ASCENDING)],
            [("mandatory_optional", ASCENDING)],
            [("currency", ASCENDING)],
            [("route_band", ASCENDING)],
            [("status", ASCENDING)],
            [("confidence", ASCENDING)],
        ],
        "airline_policy_extracted_communication_rules": [
            [("extraction_run_id", ASCENDING)],
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("service_family", ASCENDING)],
            [("communication_type", ASCENDING)],
            [("ssr_code", ASCENDING)],
            [("status", ASCENDING)],
        ],
        "airline_policy_extracted_emd_rules": [
            [("extraction_run_id", ASCENDING)],
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("service_family", ASCENDING)],
            [("emd_type", ASCENDING)],
            [("rfic", ASCENDING)],
            [("rfisc", ASCENDING)],
            [("status", ASCENDING)],
        ],
        "airline_policy_extracted_exceptions": [
            [("extraction_run_id", ASCENDING)],
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("service_family", ASCENDING)],
            [("exception_type", ASCENDING)],
            [("status", ASCENDING)],
        ],
        "airline_policy_review_corrections": [
            [("policy_source_id", ASCENDING)],
            [("extraction_run_id", ASCENDING)],
            [("target_type", ASCENDING)],
            [("target_id", ASCENDING)],
            [("correction_type", ASCENDING)],
            [("created_at", ASCENDING)],
        ],
        "airline_policy_approved_knowledge_records": [
            [("policy_source_id", ASCENDING)],
            [("airline_id", ASCENDING)],
            [("service_domain", ASCENDING)],
            [("service_family", ASCENDING)],
            [("knowledge_type", ASCENDING)],
            [("status", ASCENDING)],
            [("effective_from", ASCENDING)],
            [("approved_at", ASCENDING)],
        ],
        "canonical_service_domains": [
            {"keys": [("status", ASCENDING)], "name": "canonical_service_domains_status_lookup"},
            {"keys": [("governance_status", ASCENDING)], "name": "canonical_service_domains_governance_status_lookup"},
            {"keys": [("sort_order", ASCENDING)], "name": "canonical_service_domains_sort_order_lookup"},
        ],
        "canonical_service_families": [
            {"keys": [("domain_code", ASCENDING), ("status", ASCENDING)], "name": "canonical_service_families_domain_status_lookup"},
            {"keys": [("status", ASCENDING)], "name": "canonical_service_families_status_lookup"},
            {"keys": [("sort_order", ASCENDING)], "name": "canonical_service_families_sort_order_lookup"},
        ],
        "canonical_service_variants": [
            {"keys": [("family_code", ASCENDING), ("code", ASCENDING)], "name": "canonical_service_variants_family_code_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("status", ASCENDING)], "name": "canonical_service_variants_domain_family_status_lookup"},
            {"keys": [("status", ASCENDING)], "name": "canonical_service_variants_status_lookup"},
        ],
        "airline_service_aliases": [
            {"keys": [("airline_code", ASCENDING), ("normalized_alias_text", ASCENDING)], "name": "airline_service_aliases_airline_normalized_lookup"},
            {"keys": [("alias_type", ASCENDING), ("status", ASCENDING)], "name": "airline_service_aliases_alias_type_status_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING)], "name": "airline_service_aliases_domain_family_lookup"},
            {"keys": [("agency_id", ASCENDING), ("status", ASCENDING)], "name": "airline_service_aliases_agency_status_lookup"},
            {"keys": [("is_global", ASCENDING), ("status", ASCENDING)], "name": "airline_service_aliases_global_status_lookup"},
        ],
        "service_applicability_dimensions": [
            {"keys": [("status", ASCENDING)], "name": "service_applicability_dimensions_status_lookup"},
            {"keys": [("sort_order", ASCENDING)], "name": "service_applicability_dimensions_sort_order_lookup"},
        ],
        "service_policy_outcome_types": [
            {"keys": [("severity", ASCENDING)], "name": "service_policy_outcome_types_severity_lookup"},
            {"keys": [("status", ASCENDING)], "name": "service_policy_outcome_types_status_lookup"},
            {"keys": [("sort_order", ASCENDING)], "name": "service_policy_outcome_types_sort_order_lookup"},
        ],
        "service_taxonomy_mapping_rules": [
            {"keys": [("airline_code", ASCENDING), ("status", ASCENDING), ("priority", ASCENDING), ("match_type", ASCENDING)], "name": "service_taxonomy_mapping_rules_airline_status_priority_match_lookup"},
            {"keys": [("normalized_match_value", ASCENDING)], "name": "service_taxonomy_mapping_rules_normalized_match_lookup"},
            {"keys": [("scope", ASCENDING), ("agency_id", ASCENDING), ("status", ASCENDING)], "name": "service_taxonomy_mapping_rules_scope_agency_status_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING)], "name": "service_taxonomy_mapping_rules_domain_family_lookup"},
        ],
        "policy_candidate_taxonomy_links": [
            {"keys": [("candidate_type", ASCENDING), ("candidate_id", ASCENDING)], "name": "policy_candidate_taxonomy_links_candidate_lookup"},
            {"keys": [("policy_source_id", ASCENDING), ("extraction_run_id", ASCENDING)], "name": "policy_candidate_taxonomy_links_source_run_lookup"},
            {"keys": [("agency_id", ASCENDING), ("review_status", ASCENDING)], "name": "policy_candidate_taxonomy_links_agency_review_status_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING)], "name": "policy_candidate_taxonomy_links_domain_family_lookup"},
        ],
        "service_taxonomy_review_corrections": [
            {"keys": [("candidate_type", ASCENDING), ("candidate_id", ASCENDING)], "name": "service_taxonomy_review_corrections_candidate_lookup"},
            {"keys": [("promotion_status", ASCENDING)], "name": "service_taxonomy_review_corrections_promotion_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("promotion_status", ASCENDING)], "name": "service_taxonomy_review_corrections_agency_promotion_status_lookup"},
            {"keys": [("created_at", ASCENDING)], "name": "service_taxonomy_review_corrections_created_at_lookup"},
        ],
        "airline_service_communication_rules": [
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_service_communication_rules_airline_taxonomy_lookup"},
            {"keys": [("communication_channel", ASCENDING), ("request_method", ASCENDING), ("status", ASCENDING)], "name": "airline_service_communication_rules_channel_method_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("is_global", ASCENDING), ("status", ASCENDING)], "name": "airline_service_communication_rules_scope_status_lookup"},
            {"keys": [("source_policy_id", ASCENDING), ("approved_knowledge_record_id", ASCENDING)], "name": "airline_service_communication_rules_policy_knowledge_lookup"},
        ],
        "ssr_osi_templates": [
            {"keys": [("communication_rule_id", ASCENDING)], "name": "ssr_osi_templates_communication_rule_lookup"},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "ssr_osi_templates_airline_taxonomy_lookup"},
            {"keys": [("gds_system", ASCENDING), ("template_type", ASCENDING), ("status", ASCENDING)], "name": "ssr_osi_templates_gds_type_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("is_global", ASCENDING), ("status", ASCENDING)], "name": "ssr_osi_templates_scope_status_lookup"},
        ],
        "ssr_osi_requirements": [
            {"keys": [("communication_rule_id", ASCENDING)], "name": "ssr_osi_requirements_communication_rule_lookup"},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "ssr_osi_requirements_airline_taxonomy_lookup"},
            {"keys": [("requirement_type", ASCENDING), ("status", ASCENDING)], "name": "ssr_osi_requirements_type_status_lookup"},
        ],
        "ssr_status_recognition_rules": [
            {"keys": [("airline_code", ASCENDING), ("gds_system", ASCENDING), ("ssr_code", ASCENDING), ("status", ASCENDING), ("priority", ASCENDING)], "name": "ssr_status_recognition_rules_airline_gds_ssr_status_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "ssr_status_recognition_rules_taxonomy_lookup"},
            {"keys": [("normalized_match_value", ASCENDING)], "name": "ssr_status_recognition_rules_normalized_match_lookup"},
        ],
        "airline_rejection_patterns": [
            {"keys": [("airline_code", ASCENDING), ("gds_system", ASCENDING), ("rejection_code", ASCENDING)], "name": "airline_rejection_patterns_airline_gds_code_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_rejection_patterns_taxonomy_lookup"},
            {"keys": [("reason_category", ASCENDING), ("severity", ASCENDING), ("status", ASCENDING)], "name": "airline_rejection_patterns_reason_severity_status_lookup"},
            {"keys": [("normalized_pattern_text", ASCENDING)], "name": "airline_rejection_patterns_normalized_text_lookup"},
        ],
        "airline_service_payment_rules": [
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_service_payment_rules_airline_taxonomy_lookup"},
            {"keys": [("payment_required", ASCENDING), ("separate_emd_required", ASCENDING), ("payment_timing", ASCENDING)], "name": "airline_service_payment_rules_payment_emd_timing_lookup"},
            {"keys": [("agency_id", ASCENDING), ("is_global", ASCENDING), ("status", ASCENDING)], "name": "airline_service_payment_rules_scope_status_lookup"},
            {"keys": [("source_policy_id", ASCENDING), ("approved_knowledge_record_id", ASCENDING)], "name": "airline_service_payment_rules_policy_knowledge_lookup"},
        ],
        "airline_emd_issuance_rules": [
            {"keys": [("payment_rule_id", ASCENDING)], "name": "airline_emd_issuance_rules_payment_rule_lookup"},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_emd_issuance_rules_airline_taxonomy_lookup"},
            {"keys": [("emd_type", ASCENDING), ("rfic", ASCENDING), ("rfisc", ASCENDING), ("status", ASCENDING)], "name": "airline_emd_issuance_rules_type_rfic_rfisc_status_lookup"},
            {"keys": [("gds_system", ASCENDING), ("status", ASCENDING)], "name": "airline_emd_issuance_rules_gds_status_lookup"},
        ],
        "airline_rfic_rfisc_mappings": [
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_rfic_rfisc_mappings_airline_taxonomy_lookup"},
            {"keys": [("airline_code", ASCENDING), ("rfic", ASCENDING), ("rfisc", ASCENDING), ("status", ASCENDING)], "name": "airline_rfic_rfisc_mappings_airline_rfic_rfisc_status_lookup"},
            {"keys": [("source_policy_id", ASCENDING), ("approved_knowledge_record_id", ASCENDING)], "name": "airline_rfic_rfisc_mappings_policy_knowledge_lookup"},
        ],
        "airline_emd_interline_rules": [
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_emd_interline_rules_airline_taxonomy_lookup"},
            {"keys": [("interline_allowed", ASCENDING), ("status", ASCENDING)], "name": "airline_emd_interline_rules_allowed_status_lookup"},
        ],
        "airline_emd_lifecycle_rules": [
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_emd_lifecycle_rules_airline_taxonomy_lookup"},
            {"keys": [("refundable", ASCENDING), ("exchangeable", ASCENDING), ("voidable", ASCENDING), ("status", ASCENDING)], "name": "airline_emd_lifecycle_rules_lifecycle_status_lookup"},
        ],
        "policy_candidate_mechanics_links": [
            {"keys": [("candidate_type", ASCENDING), ("candidate_id", ASCENDING)], "name": "policy_candidate_mechanics_links_candidate_lookup"},
            {"keys": [("taxonomy_link_id", ASCENDING)], "name": "policy_candidate_mechanics_links_taxonomy_link_lookup"},
            {"keys": [("mechanics_type", ASCENDING), ("mechanics_record_id", ASCENDING)], "name": "policy_candidate_mechanics_links_mechanics_record_lookup"},
            {"keys": [("policy_source_id", ASCENDING), ("extraction_run_id", ASCENDING)], "name": "policy_candidate_mechanics_links_source_run_lookup"},
            {"keys": [("agency_id", ASCENDING), ("review_status", ASCENDING)], "name": "policy_candidate_mechanics_links_agency_review_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "policy_candidate_mechanics_links_taxonomy_lookup"},
        ],
        "airline_ancillary_pricing_rules": [
            {"keys": [("id", ASCENDING)], "name": "airline_ancillary_pricing_rules_id_unique", "unique": True},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_ancillary_pricing_rules_airline_taxonomy_lookup"},
            {"keys": [("pricing_status", ASCENDING), ("review_status", ASCENDING)], "name": "airline_ancillary_pricing_rules_status_review_lookup"},
            {"keys": [("agency_id", ASCENDING), ("is_global", ASCENDING), ("pricing_status", ASCENDING)], "name": "airline_ancillary_pricing_rules_scope_status_lookup"},
            {"keys": [("payment_rule_id", ASCENDING), ("emd_issuance_rule_id", ASCENDING)], "name": "airline_ancillary_pricing_rules_mechanics_reference_lookup"},
            {"keys": [("source_policy_id", ASCENDING), ("approved_knowledge_record_id", ASCENDING)], "name": "airline_ancillary_pricing_rules_policy_knowledge_lookup"},
        ],
        "airline_ancillary_price_components": [
            {"keys": [("id", ASCENDING)], "name": "airline_ancillary_price_components_id_unique", "unique": True},
            {"keys": [("pricing_rule_id", ASCENDING), ("sequence", ASCENDING)], "name": "airline_ancillary_price_components_rule_sequence_lookup"},
            {"keys": [("component_type", ASCENDING), ("amount_type", ASCENDING), ("status", ASCENDING)], "name": "airline_ancillary_price_components_type_amount_status_lookup"},
            {"keys": [("currency", ASCENDING), ("applies_per", ASCENDING)], "name": "airline_ancillary_price_components_currency_applies_lookup"},
        ],
        "airline_ancillary_pricing_applicability": [
            {"keys": [("id", ASCENDING)], "name": "airline_ancillary_pricing_applicability_id_unique", "unique": True},
            {"keys": [("pricing_rule_id", ASCENDING), ("dimension_code", ASCENDING)], "name": "airline_ancillary_pricing_applicability_rule_dimension_lookup"},
            {"keys": [("dimension_code", ASCENDING), ("operator", ASCENDING), ("applies_as", ASCENDING)], "name": "airline_ancillary_pricing_applicability_dimension_operator_lookup"},
            {"keys": [("status", ASCENDING)], "name": "airline_ancillary_pricing_applicability_status_lookup"},
        ],
        "airline_ancillary_pricing_matrices": [
            {"keys": [("id", ASCENDING)], "name": "airline_ancillary_pricing_matrices_id_unique", "unique": True},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_ancillary_pricing_matrices_airline_taxonomy_lookup"},
            {"keys": [("scope", ASCENDING), ("agency_id", ASCENDING), ("status", ASCENDING)], "name": "airline_ancillary_pricing_matrices_scope_status_lookup"},
            {"keys": [("source_policy_id", ASCENDING), ("approved_knowledge_record_id", ASCENDING)], "name": "airline_ancillary_pricing_matrices_policy_knowledge_lookup"},
        ],
        "airline_ancillary_pricing_matrix_rows": [
            {"keys": [("id", ASCENDING)], "name": "airline_ancillary_pricing_matrix_rows_id_unique", "unique": True},
            {"keys": [("matrix_id", ASCENDING), ("sort_order", ASCENDING)], "name": "airline_ancillary_pricing_matrix_rows_matrix_sort_lookup"},
            {"keys": [("pricing_rule_id", ASCENDING)], "name": "airline_ancillary_pricing_matrix_rows_pricing_rule_lookup"},
            {"keys": [("direct_vs_connecting", ASCENDING), ("route_band", ASCENDING), ("passenger_type", ASCENDING), ("cabin", ASCENDING)], "name": "airline_ancillary_pricing_matrix_rows_dimensions_lookup"},
            {"keys": [("status", ASCENDING)], "name": "airline_ancillary_pricing_matrix_rows_status_lookup"},
        ],
        "airline_service_exception_rules": [
            {"keys": [("id", ASCENDING)], "name": "airline_service_exception_rules_id_unique", "unique": True},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_service_exception_rules_airline_taxonomy_lookup"},
            {"keys": [("exception_type", ASCENDING), ("severity", ASCENDING), ("outcome", ASCENDING), ("status", ASCENDING)], "name": "airline_service_exception_rules_type_severity_outcome_lookup"},
            {"keys": [("pricing_rule_id", ASCENDING), ("mechanics_record_id", ASCENDING)], "name": "airline_service_exception_rules_pricing_mechanics_lookup"},
            {"keys": [("agency_id", ASCENDING), ("is_global", ASCENDING), ("status", ASCENDING)], "name": "airline_service_exception_rules_scope_status_lookup"},
            {"keys": [("source_policy_id", ASCENDING), ("approved_knowledge_record_id", ASCENDING)], "name": "airline_service_exception_rules_policy_knowledge_lookup"},
        ],
        "airline_service_price_quote_scenarios": [
            {"keys": [("id", ASCENDING)], "name": "airline_service_price_quote_scenarios_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING)], "name": "airline_service_price_quote_scenarios_agency_lookup"},
            {"keys": [("agency_id", ASCENDING), ("created_at", ASCENDING)], "name": "airline_service_price_quote_scenarios_agency_created_lookup"},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_service_price_quote_scenarios_airline_taxonomy_lookup"},
        ],
        "airline_service_price_quote_results": [
            {"keys": [("id", ASCENDING)], "name": "airline_service_price_quote_results_id_unique", "unique": True},
            {"keys": [("scenario_id", ASCENDING), ("created_at", ASCENDING)], "name": "airline_service_price_quote_results_scenario_created_lookup"},
            {"keys": [("evaluation_status", ASCENDING)], "name": "airline_service_price_quote_results_status_lookup"},
        ],
        "policy_candidate_pricing_links": [
            {"keys": [("id", ASCENDING)], "name": "policy_candidate_pricing_links_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING)], "name": "policy_candidate_pricing_links_agency_lookup"},
            {"keys": [("candidate_type", ASCENDING), ("candidate_id", ASCENDING)], "name": "policy_candidate_pricing_links_candidate_lookup"},
            {"keys": [("taxonomy_link_id", ASCENDING)], "name": "policy_candidate_pricing_links_taxonomy_link_lookup"},
            {"keys": [("mechanics_link_id", ASCENDING)], "name": "policy_candidate_pricing_links_mechanics_link_lookup"},
            {"keys": [("pricing_record_type", ASCENDING), ("pricing_record_id", ASCENDING)], "name": "policy_candidate_pricing_links_pricing_record_lookup"},
            {"keys": [("policy_source_id", ASCENDING), ("extraction_run_id", ASCENDING)], "name": "policy_candidate_pricing_links_source_run_lookup"},
            {"keys": [("agency_id", ASCENDING), ("review_status", ASCENDING)], "name": "policy_candidate_pricing_links_agency_review_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "policy_candidate_pricing_links_taxonomy_lookup"},
        ],
        "airline_policy_comparison_profiles": [
            {"keys": [("id", ASCENDING)], "name": "airline_policy_comparison_profiles_id_unique", "unique": True},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_policy_comparison_profiles_airline_taxonomy_lookup"},
            {"keys": [("agency_id", ASCENDING), ("is_global", ASCENDING), ("status", ASCENDING)], "name": "airline_policy_comparison_profiles_scope_status_lookup"},
            {"keys": [("review_status", ASCENDING), ("status", ASCENDING)], "name": "airline_policy_comparison_profiles_review_status_lookup"},
        ],
        "airline_policy_comparison_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "airline_policy_comparison_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("created_at", ASCENDING)], "name": "airline_policy_comparison_snapshots_agency_created_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_policy_comparison_snapshots_taxonomy_lookup"},
            {"keys": [("generated_from", ASCENDING)], "name": "airline_policy_comparison_snapshots_generated_from_lookup"},
        ],
        "airline_policy_comparison_rows": [
            {"keys": [("id", ASCENDING)], "name": "airline_policy_comparison_rows_id_unique", "unique": True},
            {"keys": [("snapshot_id", ASCENDING), ("airline_code", ASCENDING)], "name": "airline_policy_comparison_rows_snapshot_airline_lookup"},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_policy_comparison_rows_airline_taxonomy_lookup"},
            {"keys": [("warning_level", ASCENDING), ("operational_complexity_score", ASCENDING)], "name": "airline_policy_comparison_rows_warning_complexity_lookup"},
        ],
        "airline_service_advisor_scenarios": [
            {"keys": [("id", ASCENDING)], "name": "airline_service_advisor_scenarios_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("created_at", ASCENDING)], "name": "airline_service_advisor_scenarios_agency_created_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_service_advisor_scenarios_taxonomy_lookup"},
        ],
        "airline_service_advisor_results": [
            {"keys": [("id", ASCENDING)], "name": "airline_service_advisor_results_id_unique", "unique": True},
            {"keys": [("scenario_id", ASCENDING), ("created_at", ASCENDING)], "name": "airline_service_advisor_results_scenario_created_lookup"},
            {"keys": [("result_status", ASCENDING)], "name": "airline_service_advisor_results_status_lookup"},
            {"keys": [("comparison_snapshot_id", ASCENDING)], "name": "airline_service_advisor_results_snapshot_lookup"},
        ],
        "airline_policy_comparison_saved_views": [
            {"keys": [("id", ASCENDING)], "name": "airline_policy_comparison_saved_views_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("is_global", ASCENDING), ("status", ASCENDING)], "name": "airline_policy_comparison_saved_views_scope_status_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "airline_policy_comparison_saved_views_taxonomy_lookup"},
        ],
        "offer_policy_advisor_contexts": [
            {"keys": [("id", ASCENDING)], "name": "offer_policy_advisor_contexts_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_policy_advisor_contexts_workspace_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_option_id", ASCENDING)], "name": "offer_policy_advisor_contexts_option_lookup"},
            {"keys": [("policy_comparison_snapshot_id", ASCENDING), ("advisor_result_id", ASCENDING)], "name": "offer_policy_advisor_contexts_advisor_artifact_lookup"},
            {"keys": [("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "offer_policy_advisor_contexts_taxonomy_lookup"},
        ],
        "offer_policy_advisor_airline_rows": [
            {"keys": [("id", ASCENDING)], "name": "offer_policy_advisor_airline_rows_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("context_id", ASCENDING), ("airline_code", ASCENDING)], "name": "offer_policy_advisor_airline_rows_context_airline_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_policy_advisor_airline_rows_workspace_lookup"},
            {"keys": [("policy_comparison_row_id", ASCENDING), ("quote_result_id", ASCENDING)], "name": "offer_policy_advisor_airline_rows_artifact_lookup"},
            {"keys": [("warning_level", ASCENDING), ("operational_complexity_score", ASCENDING)], "name": "offer_policy_advisor_airline_rows_warning_complexity_lookup"},
        ],
        "offer_policy_advisor_warnings": [
            {"keys": [("id", ASCENDING)], "name": "offer_policy_advisor_warnings_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("context_id", ASCENDING), ("warning_level", ASCENDING)], "name": "offer_policy_advisor_warnings_context_level_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_policy_advisor_warnings_workspace_lookup"},
            {"keys": [("source", ASCENDING), ("source_record_id", ASCENDING)], "name": "offer_policy_advisor_warnings_source_lookup"},
        ],
        "offer_policy_advisor_decision_notes": [
            {"keys": [("id", ASCENDING)], "name": "offer_policy_advisor_decision_notes_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("context_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_policy_advisor_decision_notes_context_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_policy_advisor_decision_notes_workspace_lookup"},
            {"keys": [("advisor_result_id", ASCENDING), ("policy_comparison_snapshot_id", ASCENDING)], "name": "offer_policy_advisor_decision_notes_artifact_lookup"},
        ],
        "offer_policy_advisor_saved_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_policy_advisor_saved_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("context_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_policy_advisor_saved_snapshots_context_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_policy_advisor_saved_snapshots_workspace_lookup"},
            {"keys": [("policy_comparison_snapshot_id", ASCENDING), ("advisor_result_id", ASCENDING)], "name": "offer_policy_advisor_saved_snapshots_artifact_lookup"},
        ],
        "offer_decision_packs": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_packs_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_packs_workspace_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("pack_status", ASCENDING)], "name": "offer_decision_packs_status_lookup"},
            {"keys": [("rebuilt_from_pack_id", ASCENDING)], "name": "offer_decision_packs_rebuild_lookup"},
            {"keys": [("warning_level", ASCENDING), ("operational_complexity_score", ASCENDING)], "name": "offer_decision_packs_warning_complexity_lookup"},
        ],
        "offer_decision_pack_options": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_pack_options_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("offer_option_id", ASCENDING)], "name": "offer_decision_pack_options_pack_option_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_pack_options_workspace_lookup"},
            {"keys": [("airline_code", ASCENDING), ("domain_code", ASCENDING), ("family_code", ASCENDING), ("variant_code", ASCENDING)], "name": "offer_decision_pack_options_airline_taxonomy_lookup"},
            {"keys": [("warning_level", ASCENDING), ("operational_complexity_score", ASCENDING)], "name": "offer_decision_pack_options_warning_complexity_lookup"},
        ],
        "offer_decision_pack_evidence": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_pack_evidence_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("offer_option_id", ASCENDING)], "name": "offer_decision_pack_evidence_pack_option_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_pack_evidence_workspace_lookup"},
            {"keys": [("evidence_type", ASCENDING), ("source_record_id", ASCENDING)], "name": "offer_decision_pack_evidence_source_lookup"},
            {"keys": [("advisor_context_id", ASCENDING), ("advisor_saved_snapshot_id", ASCENDING)], "name": "offer_decision_pack_evidence_advisor_lookup"},
        ],
        "offer_decision_pack_warnings": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_pack_warnings_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("warning_level", ASCENDING)], "name": "offer_decision_pack_warnings_pack_level_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_pack_warnings_workspace_lookup"},
            {"keys": [("source", ASCENDING), ("source_record_id", ASCENDING)], "name": "offer_decision_pack_warnings_source_lookup"},
            {"keys": [("resolved", ASCENDING), ("human_review_required", ASCENDING)], "name": "offer_decision_pack_warnings_resolution_lookup"},
        ],
        "offer_decision_pack_review_notes": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_pack_review_notes_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_pack_review_notes_pack_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_pack_review_notes_workspace_lookup"},
            {"keys": [("offer_option_id", ASCENDING), ("airline_code", ASCENDING)], "name": "offer_decision_pack_review_notes_option_airline_lookup"},
        ],
        "offer_decision_pack_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_pack_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_pack_snapshots_pack_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_pack_snapshots_workspace_lookup"},
            {"keys": [("source_advisor_snapshot_ids", ASCENDING)], "name": "offer_decision_pack_snapshots_advisor_snapshot_lookup"},
        ],
        "offer_decision_explanations": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_explanations_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_explanations_pack_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_explanations_workspace_lookup"},
            {"keys": [("offer_option_id", ASCENDING), ("explanation_type", ASCENDING)], "name": "offer_decision_explanations_option_type_lookup"},
            {"keys": [("finalized", ASCENDING), ("archived", ASCENDING)], "name": "offer_decision_explanations_state_lookup"},
        ],
        "offer_decision_timeline_events": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_timeline_events_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("timestamp", ASCENDING)], "name": "offer_decision_timeline_events_pack_time_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_timeline_events_workspace_lookup"},
            {"keys": [("event_type", ASCENDING), ("actor_type", ASCENDING)], "name": "offer_decision_timeline_events_type_actor_lookup"},
        ],
        "offer_decision_evidence_references": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_evidence_references_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("reference_type", ASCENDING)], "name": "offer_decision_evidence_references_pack_type_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_evidence_references_workspace_lookup"},
            {"keys": [("reference_type", ASCENDING), ("reference_id", ASCENDING)], "name": "offer_decision_evidence_references_reference_lookup"},
            {"keys": [("source_collection", ASCENDING), ("source_record_id", ASCENDING)], "name": "offer_decision_evidence_references_source_lookup"},
        ],
        "offer_decision_reasons": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_reasons_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_reasons_pack_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_reasons_workspace_lookup"},
            {"keys": [("reason_category", ASCENDING), ("importance", ASCENDING)], "name": "offer_decision_reasons_category_importance_lookup"},
            {"keys": [("archived", ASCENDING)], "name": "offer_decision_reasons_archived_lookup"},
        ],
        "offer_decision_acknowledgements": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_acknowledgements_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("acknowledged_at", ASCENDING)], "name": "offer_decision_acknowledgements_pack_time_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_acknowledgements_workspace_lookup"},
            {"keys": [("acknowledgement_type", ASCENDING), ("acknowledged_by", ASCENDING)], "name": "offer_decision_acknowledgements_type_actor_lookup"},
        ],
        "offer_decision_audit_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_audit_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_audit_snapshots_pack_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_audit_snapshots_workspace_lookup"},
            {"keys": [("immutable", ASCENDING)], "name": "offer_decision_audit_snapshots_immutable_lookup"},
        ],
        "offer_decision_exports": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_exports_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_exports_pack_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("offer_workspace_id", ASCENDING)], "name": "offer_decision_exports_workspace_lookup"},
            {"keys": [("export_status", ASCENDING), ("generated_at", ASCENDING)], "name": "offer_decision_exports_status_generated_lookup"},
        ],
        "offer_decision_export_sections": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_sections_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("section_order", ASCENDING)], "name": "offer_decision_export_sections_export_order_lookup"},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("section_key", ASCENDING)], "name": "offer_decision_export_sections_pack_key_lookup"},
        ],
        "offer_decision_export_artifacts": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_artifacts_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("artifact_type", ASCENDING)], "name": "offer_decision_export_artifacts_export_type_lookup"},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING)], "name": "offer_decision_export_artifacts_pack_lookup"},
            {"keys": [("public_link_created", ASCENDING), ("automatic_sending_disabled", ASCENDING)], "name": "offer_decision_export_artifacts_safety_lookup"},
        ],
        "offer_decision_export_recipient_drafts": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_recipient_drafts_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("delivery_status", ASCENDING)], "name": "offer_decision_export_recipient_drafts_export_status_lookup"},
            {"keys": [("recipient_email", ASCENDING), ("recipient_type", ASCENDING)], "name": "offer_decision_export_recipient_drafts_recipient_lookup"},
        ],
        "offer_decision_export_audit_events": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_audit_events_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_audit_events_export_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING), ("event_type", ASCENDING)], "name": "offer_decision_export_audit_events_pack_type_lookup"},
        ],
        "offer_decision_export_previews": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_previews_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_previews_export_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("decision_pack_id", ASCENDING)], "name": "offer_decision_export_previews_pack_lookup"},
            {"keys": [("preview_status", ASCENDING), ("generated_at", ASCENDING)], "name": "offer_decision_export_previews_status_generated_lookup"},
        ],
        "offer_decision_export_preview_sections": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_preview_sections_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING), ("section_order", ASCENDING)], "name": "offer_decision_export_preview_sections_preview_order_lookup"},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("section_key", ASCENDING)], "name": "offer_decision_export_preview_sections_export_key_lookup"},
        ],
        "offer_decision_export_preview_blocks": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_preview_blocks_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING), ("block_order", ASCENDING)], "name": "offer_decision_export_preview_blocks_preview_order_lookup"},
            {"keys": [("agency_id", ASCENDING), ("section_id", ASCENDING), ("block_order", ASCENDING)], "name": "offer_decision_export_preview_blocks_section_order_lookup"},
            {"keys": [("block_type", ASCENDING), ("section_key", ASCENDING)], "name": "offer_decision_export_preview_blocks_type_section_lookup"},
        ],
        "offer_decision_export_preview_validations": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_preview_validations_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING), ("validation_key", ASCENDING)], "name": "offer_decision_export_preview_validations_preview_key_lookup"},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("validation_status", ASCENDING)], "name": "offer_decision_export_preview_validations_export_status_lookup"},
        ],
        "offer_decision_export_preview_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_preview_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_preview_snapshots_preview_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING)], "name": "offer_decision_export_preview_snapshots_export_lookup"},
            {"keys": [("immutable", ASCENDING)], "name": "offer_decision_export_preview_snapshots_immutable_lookup"},
        ],
        "offer_decision_export_approvals": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_approvals_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_approvals_preview_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING)], "name": "offer_decision_export_approvals_export_lookup"},
            {"keys": [("approval_status", ASCENDING), ("status_updated_at", ASCENDING)], "name": "offer_decision_export_approvals_status_time_lookup"},
        ],
        "offer_decision_export_approval_checkpoints": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_approval_checkpoints_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("approval_id", ASCENDING), ("sequence_order", ASCENDING)], "name": "offer_decision_export_approval_checkpoints_approval_order_lookup"},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING)], "name": "offer_decision_export_approval_checkpoints_preview_lookup"},
            {"keys": [("checkpoint_type", ASCENDING), ("checkpoint_status", ASCENDING)], "name": "offer_decision_export_approval_checkpoints_type_status_lookup"},
        ],
        "offer_decision_export_release_readiness": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_release_readiness_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_release_readiness_preview_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("approval_id", ASCENDING)], "name": "offer_decision_export_release_readiness_approval_lookup"},
            {"keys": [("readiness_status", ASCENDING), ("prepared_at", ASCENDING)], "name": "offer_decision_export_release_readiness_status_time_lookup"},
        ],
        "offer_decision_export_release_holds": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_release_holds_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("readiness_id", ASCENDING), ("hold_status", ASCENDING)], "name": "offer_decision_export_release_holds_readiness_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING)], "name": "offer_decision_export_release_holds_preview_lookup"},
            {"keys": [("hold_type", ASCENDING), ("severity", ASCENDING)], "name": "offer_decision_export_release_holds_type_severity_lookup"},
        ],
        "offer_decision_export_release_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_release_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("readiness_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_release_snapshots_readiness_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("preview_id", ASCENDING)], "name": "offer_decision_export_release_snapshots_preview_lookup"},
            {"keys": [("immutable", ASCENDING)], "name": "offer_decision_export_release_snapshots_immutable_lookup"},
        ],
        "offer_decision_export_delivery_handoffs": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_handoffs_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_handoffs_export_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("release_readiness_id", ASCENDING)], "name": "offer_decision_export_delivery_handoffs_readiness_lookup"},
            {"keys": [("status", ASCENDING), ("updated_at", ASCENDING)], "name": "offer_decision_export_delivery_handoffs_status_updated_lookup"},
        ],
        "offer_decision_export_delivery_recipients": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_recipients_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_recipients_handoff_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("delivery_status", ASCENDING)], "name": "offer_decision_export_delivery_recipients_status_lookup"},
            {"keys": [("recipient_type", ASCENDING), ("delivery_method", ASCENDING)], "name": "offer_decision_export_delivery_recipients_type_method_lookup"},
        ],
        "offer_decision_export_delivery_attachments": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_attachments_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_attachments_handoff_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("artifact_id", ASCENDING)], "name": "offer_decision_export_delivery_attachments_artifact_lookup"},
            {"keys": [("public_link_created", ASCENDING), ("real_file_delivered", ASCENDING)], "name": "offer_decision_export_delivery_attachments_safety_lookup"},
        ],
        "offer_decision_export_delivery_instructions": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_instructions_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_instructions_handoff_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("completed", ASCENDING), ("required", ASCENDING)], "name": "offer_decision_export_delivery_instructions_completion_lookup"},
            {"keys": [("instruction_type", ASCENDING)], "name": "offer_decision_export_delivery_instructions_type_lookup"},
        ],
        "offer_decision_export_delivery_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_snapshots_handoff_created_lookup"},
            {"keys": [("snapshot_type", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_snapshots_type_created_lookup"},
            {"keys": [("immutable", ASCENDING)], "name": "offer_decision_export_delivery_snapshots_immutable_lookup"},
        ],
        "offer_decision_export_delivery_outcomes": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_outcomes_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_outcomes_handoff_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("outcome_status", ASCENDING), ("updated_at", ASCENDING)], "name": "offer_decision_export_delivery_outcomes_status_updated_lookup"},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING)], "name": "offer_decision_export_delivery_outcomes_export_lookup"},
        ],
        "offer_decision_export_delivery_outcome_events": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_outcome_events_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("outcome_id", ASCENDING), ("occurred_at", ASCENDING)], "name": "offer_decision_export_delivery_outcome_events_outcome_time_lookup"},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("event_type", ASCENDING)], "name": "offer_decision_export_delivery_outcome_events_handoff_type_lookup"},
            {"keys": [("actor_type", ASCENDING), ("event_type", ASCENDING)], "name": "offer_decision_export_delivery_outcome_events_actor_type_lookup"},
        ],
        "offer_decision_export_delivery_receipts": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_receipts_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("outcome_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_receipts_outcome_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("receipt_type", ASCENDING)], "name": "offer_decision_export_delivery_receipts_handoff_type_lookup"},
        ],
        "offer_decision_export_delivery_issues": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_issues_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("outcome_id", ASCENDING), ("issue_status", ASCENDING)], "name": "offer_decision_export_delivery_issues_outcome_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING), ("issue_type", ASCENDING)], "name": "offer_decision_export_delivery_issues_handoff_type_lookup"},
            {"keys": [("issue_status", ASCENDING), ("updated_at", ASCENDING)], "name": "offer_decision_export_delivery_issues_status_updated_lookup"},
        ],
        "offer_decision_export_delivery_outcome_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_delivery_outcome_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("outcome_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_delivery_outcome_snapshots_outcome_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("handoff_id", ASCENDING)], "name": "offer_decision_export_delivery_outcome_snapshots_handoff_lookup"},
            {"keys": [("immutable", ASCENDING), ("snapshot_type", ASCENDING)], "name": "offer_decision_export_delivery_outcome_snapshots_immutable_type_lookup"},
        ],
        "offer_decision_export_audit_reviews": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_audit_reviews_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_audit_reviews_export_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("outcome_id", ASCENDING)], "name": "offer_decision_export_audit_reviews_outcome_lookup"},
            {"keys": [("agency_id", ASCENDING), ("review_status", ASCENDING), ("updated_at", ASCENDING)], "name": "offer_decision_export_audit_reviews_status_updated_lookup"},
        ],
        "offer_decision_export_audit_review_findings": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_audit_review_findings_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("review_id", ASCENDING), ("finding_status", ASCENDING)], "name": "offer_decision_export_audit_review_findings_review_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("finding_type", ASCENDING), ("severity", ASCENDING)], "name": "offer_decision_export_audit_review_findings_type_severity_lookup"},
        ],
        "offer_decision_export_audit_review_checklist_items": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_audit_review_checklist_items_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("review_id", ASCENDING), ("item_status", ASCENDING)], "name": "offer_decision_export_audit_review_checklist_items_review_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("item_key", ASCENDING)], "name": "offer_decision_export_audit_review_checklist_items_key_lookup"},
        ],
        "offer_decision_export_audit_review_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_audit_review_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("review_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_audit_review_snapshots_review_created_lookup"},
            {"keys": [("immutable", ASCENDING), ("snapshot_type", ASCENDING)], "name": "offer_decision_export_audit_review_snapshots_immutable_type_lookup"},
        ],
        "offer_decision_export_governance_records": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_governance_records_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("export_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_governance_records_export_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("audit_review_id", ASCENDING)], "name": "offer_decision_export_governance_records_audit_review_lookup"},
            {"keys": [("agency_id", ASCENDING), ("governance_status", ASCENDING), ("updated_at", ASCENDING)], "name": "offer_decision_export_governance_records_status_updated_lookup"},
        ],
        "offer_decision_export_governance_rules": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_governance_rules_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("governance_record_id", ASCENDING), ("rule_status", ASCENDING)], "name": "offer_decision_export_governance_rules_record_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("rule_type", ASCENDING)], "name": "offer_decision_export_governance_rules_type_lookup"},
        ],
        "offer_decision_export_retention_policies": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_retention_policies_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("governance_record_id", ASCENDING)], "name": "offer_decision_export_retention_policies_record_lookup"},
            {"keys": [("agency_id", ASCENDING), ("retention_action", ASCENDING)], "name": "offer_decision_export_retention_policies_action_lookup"},
        ],
        "offer_decision_export_legal_bases": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_legal_bases_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("governance_record_id", ASCENDING)], "name": "offer_decision_export_legal_bases_record_lookup"},
            {"keys": [("agency_id", ASCENDING), ("basis_type", ASCENDING)], "name": "offer_decision_export_legal_bases_type_lookup"},
        ],
        "offer_decision_export_archive_statuses": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_archive_statuses_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("governance_record_id", ASCENDING)], "name": "offer_decision_export_archive_statuses_record_lookup"},
            {"keys": [("agency_id", ASCENDING), ("archive_status", ASCENDING)], "name": "offer_decision_export_archive_statuses_status_lookup"},
        ],
        "offer_decision_export_governance_exceptions": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_governance_exceptions_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("governance_record_id", ASCENDING), ("exception_status", ASCENDING)], "name": "offer_decision_export_governance_exceptions_record_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("exception_type", ASCENDING), ("severity", ASCENDING)], "name": "offer_decision_export_governance_exceptions_type_severity_lookup"},
        ],
        "offer_decision_export_governance_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_governance_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("governance_record_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_governance_snapshots_record_created_lookup"},
            {"keys": [("immutable", ASCENDING), ("snapshot_type", ASCENDING)], "name": "offer_decision_export_governance_snapshots_immutable_type_lookup"},
        ],
        "offer_decision_export_compliance_evidence": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_compliance_evidence_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("governance_record_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_compliance_evidence_governance_created_lookup"},
            {"keys": [("agency_id", ASCENDING), ("audit_review_id", ASCENDING)], "name": "offer_decision_export_compliance_evidence_audit_review_lookup"},
            {"keys": [("agency_id", ASCENDING), ("evidence_status", ASCENDING), ("updated_at", ASCENDING)], "name": "offer_decision_export_compliance_evidence_status_updated_lookup"},
        ],
        "offer_decision_export_compliance_requirements": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_compliance_requirements_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("evidence_id", ASCENDING), ("requirement_status", ASCENDING)], "name": "offer_decision_export_compliance_requirements_evidence_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("requirement_type", ASCENDING)], "name": "offer_decision_export_compliance_requirements_type_lookup"},
        ],
        "offer_decision_export_compliance_checks": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_compliance_checks_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("evidence_id", ASCENDING), ("check_status", ASCENDING)], "name": "offer_decision_export_compliance_checks_evidence_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("requirement_id", ASCENDING)], "name": "offer_decision_export_compliance_checks_requirement_lookup"},
        ],
        "offer_decision_export_compliance_results": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_compliance_results_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("evidence_id", ASCENDING), ("result_status", ASCENDING)], "name": "offer_decision_export_compliance_results_evidence_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("check_id", ASCENDING)], "name": "offer_decision_export_compliance_results_check_lookup"},
        ],
        "offer_decision_export_compliance_exceptions": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_compliance_exceptions_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("evidence_id", ASCENDING), ("exception_status", ASCENDING)], "name": "offer_decision_export_compliance_exceptions_evidence_status_lookup"},
            {"keys": [("agency_id", ASCENDING), ("exception_type", ASCENDING), ("severity", ASCENDING)], "name": "offer_decision_export_compliance_exceptions_type_severity_lookup"},
        ],
        "offer_decision_export_compliance_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "offer_decision_export_compliance_snapshots_id_unique", "unique": True},
            {"keys": [("agency_id", ASCENDING), ("evidence_id", ASCENDING), ("created_at", ASCENDING)], "name": "offer_decision_export_compliance_snapshots_evidence_created_lookup"},
            {"keys": [("immutable", ASCENDING), ("snapshot_type", ASCENDING)], "name": "offer_decision_export_compliance_snapshots_immutable_type_lookup"},
        ],
        "airline_intelligence_data_packs": [
            {"keys": [("id", ASCENDING)], "name": "airline_intelligence_data_packs_id_unique", "unique": True},
            {"keys": [("slug", ASCENDING)], "name": "airline_intelligence_data_packs_slug_unique", "unique": True},
            {"keys": [("verification_status", ASCENDING), ("updated_at", ASCENDING)], "name": "airline_intelligence_data_packs_status_updated_lookup"},
            {"keys": [("pack_type", ASCENDING), ("source_type", ASCENDING)], "name": "airline_intelligence_data_packs_type_source_lookup"},
            {"keys": [("safe_for_agency_display", ASCENDING), ("safe_for_cms_display", ASCENDING), ("safe_for_offer_builder", ASCENDING)], "name": "airline_intelligence_data_packs_safe_surface_lookup"},
        ],
        "airline_intelligence_data_pack_items": [
            {"keys": [("id", ASCENDING)], "name": "airline_intelligence_data_pack_items_id_unique", "unique": True},
            {"keys": [("pack_id", ASCENDING), ("target_domain", ASCENDING)], "name": "airline_intelligence_data_pack_items_pack_domain_lookup"},
            {"keys": [("airline_iata_code", ASCENDING), ("target_domain", ASCENDING)], "name": "airline_intelligence_data_pack_items_airline_domain_lookup"},
            {"keys": [("validation_status", ASCENDING), ("verification_status", ASCENDING)], "name": "airline_intelligence_data_pack_items_validation_verification_lookup"},
        ],
        "airline_intelligence_data_pack_validation_issues": [
            {"keys": [("id", ASCENDING)], "name": "airline_intelligence_data_pack_validation_issues_id_unique", "unique": True},
            {"keys": [("pack_id", ASCENDING), ("status", ASCENDING), ("severity", ASCENDING)], "name": "airline_intelligence_data_pack_validation_issues_pack_status_severity_lookup"},
            {"keys": [("item_id", ASCENDING), ("status", ASCENDING)], "name": "airline_intelligence_data_pack_validation_issues_item_status_lookup"},
        ],
        "airline_intelligence_data_pack_import_runs": [
            {"keys": [("id", ASCENDING)], "name": "airline_intelligence_data_pack_import_runs_id_unique", "unique": True},
            {"keys": [("pack_id", ASCENDING), ("created_at", ASCENDING)], "name": "airline_intelligence_data_pack_import_runs_pack_created_lookup"},
            {"keys": [("run_type", ASCENDING), ("source_format", ASCENDING)], "name": "airline_intelligence_data_pack_import_runs_type_format_lookup"},
        ],
        "airline_intelligence_data_pack_review_notes": [
            {"keys": [("id", ASCENDING)], "name": "airline_intelligence_data_pack_review_notes_id_unique", "unique": True},
            {"keys": [("pack_id", ASCENDING), ("note_type", ASCENDING), ("created_at", ASCENDING)], "name": "airline_intelligence_data_pack_review_notes_pack_type_created_lookup"},
            {"keys": [("item_id", ASCENDING), ("created_at", ASCENDING)], "name": "airline_intelligence_data_pack_review_notes_item_created_lookup"},
        ],
        "airline_intelligence_coverage_snapshots": [
            {"keys": [("id", ASCENDING)], "name": "airline_intelligence_coverage_snapshots_id_unique", "unique": True},
            {"keys": [("generated_at", ASCENDING)], "name": "airline_intelligence_coverage_snapshots_generated_lookup"},
        ],
        "invoices": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("booking_id", ASCENDING)]],
        "payment_records": [[("agency_id", ASCENDING), ("invoice_id", ASCENDING)], [("agency_id", ASCENDING), ("client_id", ASCENDING)]],
        "refund_exchange_cases": [
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("case_type", ASCENDING)],
            [("agency_id", ASCENDING), ("updated_at", ASCENDING)],
        ],
        "refund_exchange_items": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("item_type", ASCENDING)]],
        "refund_exchange_financial_lines": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("line_type", ASCENDING)]],
        "refund_exchange_messages": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("visibility", ASCENDING)]],
        "refund_exchange_timeline_events": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("event_type", ASCENDING)]],
        "document_templates": [
            [("scope", ASCENDING)],
            [("agency_id", ASCENDING)],
            [("template_key", ASCENDING)],
            [("template_type", ASCENDING)],
            [("active", ASCENDING)],
        ],
        "rendered_documents": [
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("source_entity_type", ASCENDING), ("source_entity_id", ASCENDING)],
        ],
        "document_exports": [
            [("agency_id", ASCENDING), ("rendered_document_id", ASCENDING)],
            [("agency_id", ASCENDING), ("client_visible", ASCENDING)],
            [("agency_id", ASCENDING), ("retention_expires_at", ASCENDING)],
        ],
        "document_deliveries": [
            [("agency_id", ASCENDING), ("rendered_document_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("retry_status", ASCENDING)],
        ],
        "document_delivery_attempts": [
            [("agency_id", ASCENDING), ("delivery_id", ASCENDING)],
            [("agency_id", ASCENDING), ("rendered_document_id", ASCENDING)],
        ],
        "document_storage_records": [
            [("agency_id", ASCENDING), ("related_entity_type", ASCENDING), ("related_entity_id", ASCENDING)],
            [("agency_id", ASCENDING), ("storage_status", ASCENDING)],
            [("agency_id", ASCENDING), ("document_type", ASCENDING)],
            [("agency_id", ASCENDING), ("storage_backend", ASCENDING)],
        ],
        "document_render_jobs": [
            [("agency_id", ASCENDING)],
            [("agency_id", ASCENDING), ("template_id", ASCENDING)],
            [("agency_id", ASCENDING), ("template_key", ASCENDING)],
            [("agency_id", ASCENDING), ("document_type", ASCENDING)],
            [("agency_id", ASCENDING), ("source_context_type", ASCENDING), ("source_context_id", ASCENDING)],
            [("agency_id", ASCENDING), ("render_status", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "document_packages": [
            [("agency_id", ASCENDING)],
            [("agency_id", ASCENDING), ("package_type", ASCENDING)],
            [("agency_id", ASCENDING), ("source_context_type", ASCENDING), ("source_context_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "document_share_records": [
            [("agency_id", ASCENDING)],
            [("agency_id", ASCENDING), ("document_render_job_id", ASCENDING)],
            [("agency_id", ASCENDING), ("document_package_id", ASCENDING)],
            [("agency_id", ASCENDING), ("share_status", ASCENDING)],
            [("agency_id", ASCENDING), ("share_channel", ASCENDING)],
            [("agency_id", ASCENDING), ("expires_at", ASCENDING)],
            [("agency_id", ASCENDING), ("created_at", ASCENDING)],
        ],
        "agency_email_settings": [[("agency_id", ASCENDING), ("status", ASCENDING)]],
        "portal_action_events": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("status", ASCENDING)]],
        "document_acknowledgements": [[("agency_id", ASCENDING), ("rendered_document_id", ASCENDING), ("client_id", ASCENDING)]],
        "audit_events": [[("agency_id", ASCENDING), ("entity_type", ASCENDING), ("entity_id", ASCENDING)]],
        "reference_data_suggestions": [
            [("submitting_agency_id", ASCENDING), ("status", ASCENDING)],
            [("domain", ASCENDING), ("status", ASCENDING)],
        ],
        "reference_import_batches": [[("domain", ASCENDING), ("status", ASCENDING)]],
        "agency_form_profiles": [[("agency_id", ASCENDING), ("form_context", ASCENDING)], [("agency_id", ASCENDING), ("is_default", ASCENDING)]],
        "agency_form_field_settings": [[("agency_id", ASCENDING), ("form_profile_id", ASCENDING)]],
        "airline_knowledge_items": [[("airline_id", ASCENDING)], [("review_status", ASCENDING)]],
        "airline_procedures": [[("airline_id", ASCENDING)]],
        "airline_emd_rule_notes": [[("airline_id", ASCENDING)]],
        "airline_knowledge_sources": [[("airline_id", ASCENDING)]],
        "airline_intelligence_profiles": [[("airline_id", ASCENDING)], [("iata_code", ASCENDING)], [("governance_status", ASCENDING)]],
        "airline_contacts": [[("airline_id", ASCENDING)]],
        "airline_fleet_types": [[("airline_id", ASCENDING)], [("aircraft_type", ASCENDING)]],
        "aircraft_tail_numbers": [[("airline_id", ASCENDING)], [("tail_number", ASCENDING)]],
        "aircraft_configurations": [[("airline_id", ASCENDING)], [("aircraft_type", ASCENDING)]],
        "aircraft_seatmaps": [[("airline_id", ASCENDING)], [("aircraft_type", ASCENDING)]],
        "airline_routes": [[("airline_id", ASCENDING)], [("origin_airport_code", ASCENDING), ("destination_airport_code", ASCENDING)]],
        "airline_fare_families": [[("airline_id", ASCENDING)], [("family_code", ASCENDING)]],
        "airline_rbd_matrix_rows": [[("airline_id", ASCENDING)], [("rbd_code", ASCENDING)]],
        "airline_fare_rules": [[("airline_id", ASCENDING)], [("rule_category", ASCENDING)]],
        "airline_ancillaries": [[("airline_id", ASCENDING)], [("service_code", ASCENDING)]],
        "airline_interline_agreements": [[("airline_id", ASCENDING)], [("partner_iata_code", ASCENDING)]],
        "airline_distribution_profiles": [[("airline_id", ASCENDING)]],
        "airline_pss_parameters": [[("airline_id", ASCENDING)]],
        "airline_gds_parameters": [[("airline_id", ASCENDING)], [("gds_code", ASCENDING)]],
        "airline_exception_rules": [[("airline_id", ASCENDING)], [("category", ASCENDING)]],
        "airline_rules_core": [[("iata_code", ASCENDING)], [("governance_status", ASCENDING)]],
        "unified_exception_rules": [[("category", ASCENDING)], [("airline_id", ASCENDING)], [("iata_code", ASCENDING)], [("active", ASCENDING)]],
        "agency_airline_overrides": [[("agency_id", ASCENDING), ("airline_id", ASCENDING)]],
    }
    for collection_name, index_specs in compound_indexes.items():
        collection = mongo_database[collection_name]
        for spec in index_specs:
            await create_compatible_index(collection, collection_name, spec)
