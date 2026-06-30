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
        await collection.create_index([("id", ASCENDING)], unique=True)
        await collection.create_index([("agency_id", ASCENDING)])

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
        "airline_rules_core": [[("airline_id", ASCENDING)], [("id", ASCENDING)]],
        "unified_exception_rules": [[("id", ASCENDING)]],
        "agency_staff_memberships": [[("agency_id", ASCENDING), ("user_id", ASCENDING)]],
        "portal_access_mappings": [[("agency_id", ASCENDING), ("user_email", ASCENDING)]],
        "auth_identities": [[("normalized_email", ASCENDING)], [("id", ASCENDING)]],
        "auth_sessions": [[("token_hash", ASCENDING)], [("id", ASCENDING)]],
        "invitations": [[("token_hash", ASCENDING)], [("id", ASCENDING)]],
    }
    for collection_name, index_specs in unique_indexes.items():
        for spec in index_specs:
            await mongo_database[collection_name].create_index(spec, unique=True)

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
        for spec in index_specs:
            await mongo_database[collection_name].create_index(spec)
