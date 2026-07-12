from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import RequestSegmentServiceScope, RequestSegmentServiceScopeCreate, RequestSegmentServiceScopeUpdate


PHASE_LABEL = "phase_54_1_operational_workflow_orchestration_foundation"
REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION = "request_segment_service_scopes"

REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES = ["draft", "captured", "needs_review", "ready", "converted", "archived"]
REQUEST_SEGMENT_SERVICE_READINESS_STATUSES = [
    "missing_information",
    "needs_review",
    "blocked",
    "ready_for_agent_review",
    "ready_for_trip_conversion",
    "converted",
    "unknown",
]
REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES = [
    "requested",
    "pending_information",
    "confirmed_by_client",
    "cancelled",
    "carried_forward",
    "unknown",
]
REQUEST_SEGMENT_SCOPE_TYPES = ["single_segment", "all_segments", "selected_segments", "direction", "unknown"]

KNOWLEDGE_LINK_FIELDS = [
    "service_parameter_taxonomy_ids",
    "operational_constraint_ids",
    "capability_matrix_ids",
    "operational_evaluation_ids",
    "feasibility_ids",
    "recommendation_ids",
]
OPERATIONAL_FLAG_FIELDS = [
    "requires_airline_policy_review",
    "requires_medical_review",
    "requires_document_followup",
    "requires_airline_approval",
    "requires_manual_review",
    "requires_pricing_review",
]


class RequestSegmentServicePrecisionError(ValueError):
    pass


class RequestSegmentServicePrecisionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        scopes = await self.list_platform_scopes(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": scopes,
            "scopes": scopes,
            "summary": self.summarize_counts(scopes),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Request Segment Services store passenger + segment + service precision metadata. They do not convert trips automatically, evaluate policy, calculate pricing, book, ticket, call providers, use AI/LLM logic, or run workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        scopes = await self.list_agency_scopes(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": scopes,
            "scopes": scopes,
            "summary": self.summarize_counts(scopes),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency request segment service scopes preserve segment-first passenger service metadata for human review.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        scopes = await self.list_platform_scopes(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(scopes),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        scopes = await self.list_agency_scopes(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(scopes),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_scopes(
        self,
        *,
        agency_id: str | None = None,
        request: str | None = None,
        passenger: str | None = None,
        segment: str | None = None,
        service_family: str | None = None,
        ssr_code: str | None = None,
        pet_transport_mode: str | None = None,
        item_category: str | None = None,
        readiness_status: str | None = None,
        requires_policy_review: bool | None = None,
        requires_document_followup: bool | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if service_family:
            filters["service_family"] = service_family
        if ssr_code:
            filters["ssr_code"] = ssr_code
        if pet_transport_mode:
            filters["pet_transport_mode"] = pet_transport_mode
        if item_category:
            filters["item_category"] = item_category
        if readiness_status:
            filters["readiness_status"] = readiness_status
        if requires_policy_review is not None:
            filters["requires_airline_policy_review"] = requires_policy_review
        if requires_document_followup is not None:
            filters["requires_document_followup"] = requires_document_followup

        items = await self.db.collection(REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("scope_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["travel_request_id", "request_reference", "source_entry_path"], request)
            and self._any_field_matches(
                item,
                ["request_passenger_reference", "passenger_workspace_id", "passenger_id", "passenger_snapshot"],
                passenger,
            )
            and self._any_field_matches(
                item,
                ["request_segment_reference", "segment_order", "origin", "destination"],
                segment,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._scope_projection(item, read_only=False) for item in items]

    async def list_agency_scopes(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_scopes(agency_id=agency_id, **filters)
        return [await self._scope_projection(item, read_only=False) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_scope(self, scope_id: str) -> dict[str, Any]:
        item = await self._require_scope(scope_id)
        return await self._scope_projection(item, read_only=False)

    async def get_agency_scope(self, agency_id: str, scope_id: str) -> dict[str, Any]:
        item = await self._require_scope(scope_id, agency_id=agency_id)
        return await self._scope_projection(item, read_only=False)

    async def create_scope(
        self,
        payload: RequestSegmentServiceScopeCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("scope_reference", self._scope_reference())
        data.setdefault("scope_status", "draft")
        data.setdefault("requested_status", "requested")
        data.setdefault("readiness_status", "missing_information")
        data.setdefault("created_by", user.get("id"))
        self._validate_payload(data)
        data.update(self.safety_flags())
        record = RequestSegmentServiceScope(**data)
        created = await self.db.collection(REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "request_segment_service_scope": await self._scope_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_scope(
        self,
        scope_id: str,
        payload: RequestSegmentServiceScopeUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_scope(scope_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        self._validate_payload(updates, partial=True)
        updates.update(self.safety_flags())
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise RequestSegmentServicePrecisionError("Request segment service scope metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "request_segment_service_scope": await self._scope_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_scope(self, scope_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_scope(scope_id, agency_id=agency_id)
        updates = {
            "scope_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise RequestSegmentServicePrecisionError("Request segment service scope metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "request_segment_service_scope": await self._scope_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "scope_count": len(items),
            "by_scope_status": self._counts(items, "scope_status", REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES),
            "by_readiness_status": self._counts(items, "readiness_status", REQUEST_SEGMENT_SERVICE_READINESS_STATUSES),
            "by_requested_status": self._counts(items, "requested_status", REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES),
            "policy_review_count": len([item for item in items if item.get("requires_airline_policy_review")]),
            "document_followup_count": len([item for item in items if item.get("requires_document_followup")]),
            "medical_review_count": len([item for item in items if item.get("requires_medical_review")]),
            "airline_approval_count": len([item for item in items if item.get("requires_airline_approval")]),
            "pricing_review_count": len([item for item in items if item.get("requires_pricing_review")]),
            "pet_transport_scope_count": len([item for item in items if item.get("pet_reference") or item.get("pet_id")]),
            "special_item_scope_count": len([item for item in items if item.get("special_item_reference") or item.get("special_item_id")]),
            "converted_to_trip_count": len([item for item in items if item.get("converted_to_trip")]),
            "knowledge_link_count": sum(sum(len(item.get(field) or []) for field in KNOWLEDGE_LINK_FIELDS) for item in items),
            "missing_field_count": sum(len(item.get("missing_fields") or []) for item in items),
            "missing_document_count": sum(len(item.get("missing_documents") or []) for item in items),
            "readiness_warning_count": sum(len(item.get("readiness_warnings") or []) for item in items),
            "readiness_blocker_count": sum(len(item.get("readiness_blockers") or []) for item in items),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "request": "travel_request_id, request_reference, or source_entry_path metadata match",
            "passenger": "request_passenger_reference, passenger_workspace_id, passenger_id, or passenger_snapshot metadata match",
            "segment": "request_segment_reference, segment_order, origin, or destination metadata match",
            "service_family": "service_family exact metadata match",
            "ssr_code": "ssr_code exact metadata match",
            "pet_transport_mode": "pet_transport_mode exact metadata match",
            "item_category": "item_category exact metadata match",
            "readiness_status": REQUEST_SEGMENT_SERVICE_READINESS_STATUSES,
            "requires_policy_review": "requires_airline_policy_review boolean metadata match",
            "requires_document_followup": "requires_document_followup boolean metadata match",
            "metadata_only": True,
        }

    async def _scope_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["scope_display_name"] = projected.get("scope_reference") or projected.get("id")
        projected["passenger_segment_service_summary"] = self._passenger_segment_service_summary(projected)
        projected["operational_flag_summary"] = self._operational_flag_summary(projected)
        projected["knowledge_link_summary"] = self._knowledge_link_summary(projected)
        projected["readiness_summary"] = self._readiness_summary(projected)
        projected["conversion_summary"] = self._conversion_summary(projected)
        projected["read_only"] = read_only
        projected.update(self.safety_flags())
        return projected

    async def _require_scope(self, scope_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": scope_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION).find_one(filters)
        if not item:
            raise RequestSegmentServicePrecisionError("Request segment service scope metadata not found.")
        return item

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "scope_status", REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES)
        self._validate_choice(data, "readiness_status", REQUEST_SEGMENT_SERVICE_READINESS_STATUSES)
        self._validate_choice(data, "requested_status", REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES)
        self._validate_choice(data, "segment_scope_type", REQUEST_SEGMENT_SCOPE_TYPES)
        if data.get("linked_trip_id") and data.get("travel_request_id") and data["linked_trip_id"] == data["travel_request_id"]:
            raise RequestSegmentServicePrecisionError("linked_trip_id must not reuse travel_request_id. Request remains intake; Trip remains operational dossier.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data:
            return
        value = data.get(field)
        if value is None:
            return
        if value not in allowed:
            raise RequestSegmentServicePrecisionError(f"Unsupported {field} metadata value: {value}.")

    def _passenger_segment_service_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "travel_request_id": item.get("travel_request_id"),
            "request_passenger_reference": item.get("request_passenger_reference"),
            "passenger_id": item.get("passenger_id"),
            "request_segment_reference": item.get("request_segment_reference"),
            "segment_order": item.get("segment_order"),
            "origin": item.get("origin"),
            "destination": item.get("destination"),
            "service_family": item.get("service_family"),
            "service_code": item.get("service_code"),
            "ssr_code": item.get("ssr_code"),
            "scope_is_precise": bool(item.get("request_passenger_reference") or item.get("passenger_id"))
            and bool(item.get("request_segment_reference") or item.get("segment_order"))
            and bool(item.get("service_code") or item.get("ssr_code") or item.get("selected_service_key")),
        }

    def _operational_flag_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {field: bool(item.get(field)) for field in OPERATIONAL_FLAG_FIELDS}

    def _knowledge_link_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {field: len(item.get(field) or []) for field in KNOWLEDGE_LINK_FIELDS}

    def _readiness_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "readiness_status": item.get("readiness_status"),
            "missing_field_count": len(item.get("missing_fields") or []),
            "missing_document_count": len(item.get("missing_documents") or []),
            "warning_count": len(item.get("readiness_warnings") or []),
            "blocker_count": len(item.get("readiness_blockers") or []),
        }

    def _conversion_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "linked_trip_id": item.get("linked_trip_id"),
            "converted_to_trip": bool(item.get("converted_to_trip")),
            "converted_at": item.get("converted_at"),
            "trip_segment_count": len(item.get("trip_segment_ids") or []),
            "carried_forward_to_trip": bool(item.get("carried_forward_to_trip")),
            "request_id_not_trip_id": item.get("linked_trip_id") != item.get("travel_request_id"),
        }

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "request_segment_service_precision_foundation": True,
            "request_intake_segment_first": True,
            "passenger_segment_service_scope": True,
            "pets_segment_scoped": True,
            "special_items_segment_scoped": True,
            "request_remains_intake": True,
            "trip_remains_operational_dossier": True,
            "never_use_travel_request_id_as_trip_id": True,
            "trip_conversion_metadata_only": True,
            "policy_evaluation_disabled": True,
            "pricing_calculation_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
        }

    def _scope_reference(self) -> str:
        return f"RSS-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _sort_text(self, value: Any) -> str:
        return str(value or "")

    def _counts(self, items: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        return {value: len([item for item in items if item.get(field) == value]) for value in values}

    def _any_field_matches(self, item: dict[str, Any], fields: list[str], expected: Any) -> bool:
        if expected in (None, ""):
            return True
        expected_text = str(expected).lower()
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                if any(expected_text in str(entry).lower() for entry in value):
                    return True
            elif isinstance(value, dict):
                if expected_text in str(value).lower():
                    return True
            elif value is not None and expected_text in str(value).lower():
                return True
        return False
