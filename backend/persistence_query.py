from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Awaitable, Callable, Iterable, Mapping, TypeVar

from config import DEFAULT_QUERY_LIMIT, MAXIMUM_QUERY_LIMIT, get_settings
from observability import current_correlation_id, emit_event, increment_counter


MAXIMUM_IN_VALUES = 100
SAFE_FILTER_OPERATORS = frozenset({"$eq", "$ne", "$in", "$gt", "$gte", "$lt", "$lte"})
READINESS_QUERY_LIMIT = 25

_bounded_query_limit: ContextVar[int | None] = ContextVar("bounded_query_limit", default=None)
_diagnostic_records: list[dict[str, Any]] = []
_T = TypeVar("_T")


class QueryValidationError(ValueError):
    def __init__(self, message: str) -> None:
        emit_event(
            "query_filter_rejected",
            level="WARNING",
            outcome="denied",
            metadata={"reason": "governed_query_validation"},
            logger_name="aeroassist.persistence",
        )
        super().__init__(message)


class CollectionOwnershipType(str, Enum):
    AGENCY_OWNED = "agency_owned"
    PLATFORM_GLOBAL = "platform_global"
    MIXED_PROJECTION = "mixed_projection"
    IMMUTABLE_SNAPSHOT = "immutable_snapshot"
    AUDIT_SECURITY = "audit_security"
    OPERATIONAL_EPHEMERAL = "operational_ephemeral"
    REFERENCE_DATA = "reference_data"


@dataclass(frozen=True)
class CollectionOwnership:
    collection_name: str
    ownership: CollectionOwnershipType
    tenant_field: str | None
    default_sort: str
    allowed_sort_fields: frozenset[str]
    allowed_filter_fields: frozenset[str]
    recommended_indexes: tuple[str, ...] = ()
    pagination_supported: bool = True
    historical_reads: bool = False
    deletion_policy: str = "preserve_existing_policy"


@dataclass(frozen=True)
class PaginationRequest:
    limit: int
    offset: int = 0
    cursor: str | None = None
    include_total: bool = False

    @classmethod
    def build(
        cls,
        *,
        limit: int | None = None,
        offset: int = 0,
        cursor: str | None = None,
        include_total: bool = False,
    ) -> "PaginationRequest":
        settings = get_settings()
        default_limit = settings.query_default_limit
        maximum_limit = settings.query_maximum_limit
        requested_limit = default_limit if limit is None else limit
        if requested_limit <= 0:
            raise QueryValidationError("limit must be greater than zero.")
        if offset < 0:
            raise QueryValidationError("offset must not be negative.")
        return cls(
            limit=min(requested_limit, maximum_limit),
            offset=offset,
            cursor=cursor,
            include_total=include_total,
        )


@dataclass(frozen=True)
class SortRequest:
    field: str
    direction: int

    @classmethod
    def build(
        cls,
        field: str | None,
        direction: str | int | None,
        ownership: CollectionOwnership,
    ) -> "SortRequest":
        normalized_field = field or ownership.default_sort
        if normalized_field not in ownership.allowed_sort_fields:
            raise QueryValidationError(f"Unsupported sort field for {ownership.collection_name}.")
        direction_value = str(direction or "desc").lower()
        if direction_value not in {"-1", "desc", "descending", "1", "asc", "ascending"}:
            raise QueryValidationError("Unsupported sort direction.")
        normalized_direction = -1 if direction_value in {"-1", "desc", "descending"} else 1
        return cls(field=normalized_field, direction=normalized_direction)

    def mongo_spec(self) -> list[tuple[str, int]]:
        if self.field == "id":
            return [("id", self.direction)]
        return [(self.field, self.direction), ("id", self.direction)]


@dataclass(frozen=True)
class PaginationMetadata:
    limit: int
    offset: int
    returned: int
    has_more: bool
    next_cursor: str | None
    total: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "limit": self.limit,
            "offset": self.offset,
            "returned": self.returned,
            "has_more": self.has_more,
            "next_cursor": self.next_cursor,
            "total": self.total,
        }


@dataclass(frozen=True)
class QueryPage:
    items: list[dict[str, Any]]
    pagination: PaginationMetadata

    def as_dict(self) -> dict[str, Any]:
        return {"items": self.items, "pagination": self.pagination.as_dict()}


def _ownership(
    collection_name: str,
    ownership: CollectionOwnershipType,
    *,
    tenant_field: str | None = None,
    default_sort: str = "updated_at",
    sorts: Iterable[str] = (),
    filters: Iterable[str] = (),
    historical_reads: bool = False,
    deletion_policy: str = "preserve_existing_policy",
    recommended_indexes: Iterable[str] = (),
) -> CollectionOwnership:
    return CollectionOwnership(
        collection_name=collection_name,
        ownership=ownership,
        tenant_field=tenant_field,
        default_sort=default_sort,
        allowed_sort_fields=frozenset({default_sort, "id", "created_at", *sorts}),
        allowed_filter_fields=frozenset(filters),
        recommended_indexes=tuple(recommended_indexes),
        historical_reads=historical_reads,
        deletion_policy=deletion_policy,
    )


def _agency(
    collection_name: str,
    *,
    filters: Iterable[str] = (),
    sorts: Iterable[str] = (),
    ownership: CollectionOwnershipType = CollectionOwnershipType.AGENCY_OWNED,
    historical_reads: bool = False,
    recommended_indexes: Iterable[str] = (),
) -> CollectionOwnership:
    return _ownership(
        collection_name,
        ownership,
        tenant_field="agency_id",
        filters=filters,
        sorts=sorts,
        historical_reads=historical_reads,
        recommended_indexes=recommended_indexes,
    )


COLLECTION_OWNERSHIP_REGISTRY: dict[str, CollectionOwnership] = {
    item.collection_name: item
    for item in (
        _agency("travel_requests", filters=("status", "request_status", "client_id", "trip_id", "purpose"), sorts=("status", "request_status", "deadline"), recommended_indexes=("travel_requests_agency_updated_id",)),
        _agency("travel_request_workspaces", filters=("request_status", "request_type", "request_priority", "assigned_agent", "operational_workspace_id", "requested_departure_date"), sorts=("request_status", "request_priority", "requested_departure_date", "deadline"), recommended_indexes=("travel_request_workspaces_agency_status_updated_id",)),
        _agency("client_profiles", filters=("status", "client_type", "portal_status"), sorts=("display_name", "status")),
        _agency("passenger_profiles", filters=("first_name", "last_name", "date_of_birth", "status", "identity_integrity_status", "passenger_type_code_id", "passenger_type_code", "nationality_reference_id", "residence_country_reference_id", "passport_country_reference_id"), sorts=("last_name", "status")),
        _agency("agency_staff_memberships", filters=("user_id", "identity_id", "agency_role", "status", "workspace_id"), sorts=("status", "agency_role")),
        _agency("portal_access_mappings", filters=("auth_identity_id", "subject_type", "client_profile_id", "client_id", "passenger_profile_id", "status", "portal_status"), sorts=("status", "subject_type")),
        _agency("request_passengers", filters=("request_id", "passenger_id", "status", "identity_status", "passenger_type_code_id", "passenger_type_code", "nationality_reference_id"), sorts=("request_id", "status")),
        _agency("request_segments", filters=("request_id", "status"), sorts=("request_id", "status", "sequence")),
        _agency("request_case_flags", filters=("request_id", "status", "flag_code"), sorts=("request_id", "status", "severity")),
        _agency("client_passenger_relationships", filters=("client_id", "passenger_id", "status"), sorts=("client_id", "status")),
        _agency("request_passenger_segment_services", filters=("request_id", "request_passenger_id", "passenger_id", "status"), sorts=("request_id", "request_passenger_id")),
        _agency("request_pets", filters=("request_id", "request_passenger_id", "passenger_id", "status"), sorts=("request_id", "status")),
        _agency("request_pet_segment_transport", filters=("request_id", "request_pet_id", "request_segment_id", "status"), sorts=("request_id", "status")),
        _agency("request_special_items", filters=("request_id", "request_passenger_id", "owner_passenger_id", "status"), sorts=("request_id", "status")),
        _agency("request_special_item_segments", filters=("request_id", "request_special_item_id", "request_segment_id", "applicability_status"), sorts=("request_id", "applicability_status")),
        _agency("requested_services", filters=("request_id", "passenger_id", "status"), sorts=("request_id", "status")),
        _agency("request_messages", filters=("request_id", "sender_type", "visibility"), sorts=("request_id", "visibility")),
        _agency("request_timeline_events", filters=("request_id", "event_type", "visibility"), sorts=("request_id", "event_type")),
        _agency("trip_dossiers", filters=("request_id", "client_id", "trip_status", "trip_reference"), sorts=("trip_status", "departure_date"), recommended_indexes=("trip_dossiers_agency_updated_id",)),
        _agency("trip_workspaces", filters=("trip_status", "departure_country", "destination_country", "assigned_agent", "operational_priority", "departure_date", "operational_workspace_id"), sorts=("trip_status", "departure_date", "operational_priority"), recommended_indexes=("trip_workspaces_agency_status_updated_id",)),
        _agency("trip_segments", filters=("trip_id", "source_request_segment_id", "segment_type", "status"), sorts=("trip_id", "departure_at", "sequence")),
        _agency("trip_accepted_offer_snapshots", filters=("trip_id", "acceptance_id", "workspace_id", "option_id", "source_hash"), sorts=("trip_id",), ownership=CollectionOwnershipType.IMMUTABLE_SNAPSHOT, historical_reads=True),
        _agency("passenger_workspaces", filters=("passenger_status", "nationality", "citizenship", "operational_workspace_id"), sorts=("passenger_status", "last_name"), recommended_indexes=("passenger_workspaces_agency_status_updated_id",)),
        _agency("passenger_service_requests", filters=("request_id", "trip_id", "booking_id", "passenger_id", "service_code", "status"), sorts=("status", "service_code")),
        _agency("offers", filters=("request_id", "trip_id", "client_id", "status"), sorts=("status", "valid_until"), historical_reads=True),
        _agency("offer_workspaces", filters=("trip_id", "request_id", "client_id", "status", "offer_status"), sorts=("status", "offer_status", "valid_until"), recommended_indexes=("offer_workspaces_agency_updated_id",)),
        _agency("offer_workspaces_v2", filters=("offer_status", "offer_type", "client_id", "trip_workspace_id", "validity_date", "assigned_agent"), sorts=("offer_status", "validity_date", "total_price"), recommended_indexes=("offer_workspaces_v2_agency_status_updated_id",)),
        _agency("offer_options", filters=("workspace_id", "request_id", "trip_id", "status", "option_order"), sorts=("status", "option_order"), historical_reads=True),
        _agency("offer_booking_handoffs", filters=("acceptance_id", "booking_readiness_package_id", "trip_id", "handoff_status"), sorts=("handoff_status",), historical_reads=True),
        _agency("booking_workspaces", filters=("booking_status", "booking_type", "booking_owner", "airline_pnr", "supplier_reference", "trip_workspace_id", "offer_workspace_id"), sorts=("booking_status", "booking_created_date", "booking_deadline"), recommended_indexes=("booking_workspaces_agency_status_updated_id",)),
        _agency("booking_records", filters=("booking_status", "trip_id", "booking_reference"), sorts=("booking_status",)),
        _agency("bookings", filters=("request_id", "trip_id", "offer_id", "status", "pnr"), sorts=("status",), historical_reads=True),
        _agency("ticket_workspaces", filters=("trip_workspace_id", "booking_workspace_id", "passenger_id", "ticket_status", "ticket_document_status"), sorts=("ticket_status", "ticket_document_status", "issue_date")),
        _agency("emd_workspaces", filters=("trip_workspace_id", "booking_workspace_id", "ticket_workspace_id", "passenger_id", "emd_status", "emd_document_status"), sorts=("emd_status", "emd_document_status", "issue_date")),
        _agency("ticket_records", filters=("trip_id", "booking_id", "passenger_id", "status", "ticket_status"), sorts=("status", "ticket_status", "issue_date")),
        _agency("ticket_coupons", filters=("ticket_record_id", "booking_record_id", "trip_id", "passenger_id", "coupon_status"), sorts=("coupon_status", "coupon_number")),
        _agency("emd_records", filters=("trip_id", "booking_id", "ticket_record_id", "passenger_id", "status", "emd_status"), sorts=("status", "emd_status", "issue_date")),
        _agency("emd_coupons", filters=("emd_record_id", "ticket_record_id", "booking_record_id", "trip_id", "passenger_id", "coupon_status"), sorts=("coupon_status", "coupon_number")),
        _agency("invoices", filters=("trip_id", "booking_id", "booking_workspace_id", "booking_record_id", "client_id", "status", "invoice_status"), sorts=("status", "invoice_status", "due_date")),
        _agency("invoice_line_items", filters=("invoice_id", "trip_id", "booking_id", "status"), sorts=("invoice_id", "status")),
        _agency("payment_records", filters=("invoice_id", "trip_id", "booking_id", "status", "payment_status"), sorts=("status", "payment_status", "payment_date")),
        _agency("refund_exchange_cases", historical_reads=True),
        _agency("commercial_ledgers", filters=("currency", "status"), sorts=("currency", "status")),
        _agency("commercial_transactions", filters=("entry_type", "reporting_category", "client_id", "trip_id", "booking_id", "invoice_id", "payment_record_id", "posting_status"), sorts=("posting_time", "entry_type"), ownership=CollectionOwnershipType.IMMUTABLE_SNAPSHOT, historical_reads=True, recommended_indexes=("commercial_transactions_agency_posting_id",)),
        _agency("payment_allocations", filters=("payment_record_id", "invoice_id", "invoice_line_item_id", "status"), sorts=("allocated_at",), ownership=CollectionOwnershipType.IMMUTABLE_SNAPSHOT, historical_reads=True),
        _agency("supplier_costs", filters=("supplier_reference", "client_id", "trip_id", "booking_id", "booking_workspace_id", "ticket_id", "emd_id", "service_id", "status", "currency"), sorts=("status", "confirmed_at")),
        _agency("supplier_cost_lines", filters=("supplier_cost_id", "expense_category", "status"), sorts=("supplier_cost_id", "status")),
        _agency("credit_notes", filters=("invoice_id", "client_id", "trip_id", "booking_id", "status"), sorts=("status", "issued_at")),
        _agency("credit_note_lines", filters=("credit_note_id", "invoice_line_item_id", "status"), sorts=("credit_note_id", "status")),
        _agency("refund_ledger_entries", filters=("client_id", "trip_id", "booking_id", "ticket_id", "emd_id", "payment_record_id", "payment_allocation_id", "status"), sorts=("recorded_at",), ownership=CollectionOwnershipType.IMMUTABLE_SNAPSHOT, historical_reads=True),
        _agency("exchange_ledger_entries", filters=("client_id", "trip_id", "booking_id", "original_ticket_id", "new_ticket_id", "emd_id", "status"), sorts=("recorded_at",), ownership=CollectionOwnershipType.IMMUTABLE_SNAPSHOT, historical_reads=True),
        _agency("document_workspaces", filters=("document_status", "document_type", "passenger_id", "booking_reference", "verification_status", "required_for_travel", "requirement_deadline"), sorts=("document_status", "requirement_deadline"), recommended_indexes=("document_workspaces_agency_status_updated_id",)),
        _agency("ssr_osi_workspaces", filters=("trip_workspace_id", "booking_workspace_id", "passenger_workspace_id", "workspace_status", "service_type", "ssr_code"), sorts=("workspace_status", "service_type")),
        _agency("operational_timelines", filters=("event_type", "event_category", "event_status", "event_priority", "communication_type", "passenger_workspace_id", "booking_workspace_id", "ticket_workspace_id", "emd_workspace_id", "ssr_osi_workspace_id", "related_airline"), sorts=("event_priority", "event_status"), recommended_indexes=("operational_timelines_agency_created_id",)),
        _agency("operational_work_items", filters=("queue_code", "status", "priority", "severity", "work_item_type", "source_entity_type", "assigned_user_id", "assigned_team_code", "blocker_status", "sla_status"), sorts=("priority", "severity", "due_at", "status"), ownership=CollectionOwnershipType.OPERATIONAL_EPHEMERAL, recommended_indexes=("operational_work_items_agency_status_due_created_id",)),
        _agency("operational_assignment_events", filters=("work_item_id", "event_type"), sorts=("event_type",), ownership=CollectionOwnershipType.AUDIT_SECURITY, historical_reads=True),
        _agency("operational_queue_views", filters=("owner_user_id", "queue_code"), sorts=("queue_code",)),
        _ownership("operational_queue_definitions", CollectionOwnershipType.MIXED_PROJECTION, tenant_field="agency_id", filters=("queue_code", "is_active"), sorts=("queue_code",)),
        _agency("operational_workflow_instances", filters=("workflow_definition_id", "entity_type", "entity_id", "current_state", "workflow_status"), sorts=("workflow_status", "started_at")),
        _agency("request_tasks", filters=("status", "request_id", "assigned_to"), sorts=("status", "due_at")),
        _agency("booking_readiness_packages", filters=("trip_id", "offer_acceptance_id", "readiness_status"), sorts=("readiness_status",)),
        _agency("offer_acceptances", filters=("trip_id", "workspace_id", "option_id", "offer_version", "status", "idempotency_key"), sorts=("status", "accepted_at"), ownership=CollectionOwnershipType.AGENCY_OWNED, historical_reads=True),
        _agency("pilot_readiness_issues", filters=("issue_status", "severity"), sorts=("issue_status", "severity")),
        _ownership(
            "commercial_pilot_feedback",
            CollectionOwnershipType.AGENCY_OWNED,
            tenant_field="agency_id",
            default_sort="submitted_at",
            filters=("status", "category", "affected_area", "urgency", "related_record_type", "related_record_id"),
            sorts=("status", "category", "affected_area", "urgency"),
            historical_reads=True,
            recommended_indexes=("commercial_pilot_feedback_agency_status_submitted_lookup",),
        ),
        _ownership("pilot_operational_evidence", CollectionOwnershipType.AUDIT_SECURITY, tenant_field="agency_id", default_sort="occurred_at", filters=("evidence_type", "status", "reference"), sorts=("status", "evidence_type"), historical_reads=True),
        _agency("pilot_agency_enrollments", filters=("enrollment_status",), sorts=("enrollment_status",)),
        _agency("pilot_synthetic_datasets", filters=("dataset_status", "dataset_type"), sorts=("dataset_status", "dataset_type"), historical_reads=True),
        _ownership("pilot_health_timeline_events", CollectionOwnershipType.AUDIT_SECURITY, tenant_field="agency_id", default_sort="occurred_at", filters=("event_type", "status", "reference"), sorts=("event_type", "status"), historical_reads=True),
        _ownership("agencies", CollectionOwnershipType.PLATFORM_GLOBAL, default_sort="created_at", filters=("status", "slug"), sorts=("name", "status")),
        _ownership("global_reference_records", CollectionOwnershipType.REFERENCE_DATA, default_sort="key", filters=("domain", "key", "code", "status", "is_active", "scope", "agency_id"), sorts=("domain", "status", "sort_order", "label", "key"), historical_reads=True, recommended_indexes=("global_reference_records_domain_active_sort_label", "global_reference_records_agency_domain_active_sort")),
        _ownership("service_catalogue", CollectionOwnershipType.REFERENCE_DATA, default_sort="service_code", filters=("service_code", "service_family", "status"), sorts=("service_family", "status")),
        _ownership("airline_profiles", CollectionOwnershipType.PLATFORM_GLOBAL, default_sort="airline_code", filters=("airline_code", "status"), sorts=("status",)),
        *(
            _ownership(name, CollectionOwnershipType.MIXED_PROJECTION, tenant_field="agency_id", filters=("assessment_id", "airline_code", "service_family", "service_code", "coverage_status", "gap_type", "gap_status", "plan_status", "target_status", "assessment_status"), sorts=("airline_code", "service_family", "coverage_status", "gap_status", "plan_status", "target_status", "assessment_status"), recommended_indexes=(("airline_service_coverage_cells_airline_service_updated_id",) if name == "airline_service_coverage_cells" else ()))
            for name in (
                "airline_service_coverage_profiles",
                "airline_service_coverage_cells",
                "airline_knowledge_gaps",
                "airline_coverage_targets",
                "airline_coverage_assessments",
                "airline_coverage_remediation_plans",
            )
        ),
        *(
            _ownership(name, CollectionOwnershipType.PLATFORM_GLOBAL, filters=("assessment_id", "candidate_id", "candidate_status", "profile_status", "assessment_status", "wave_status", "issue_status", "severity", "airline_code", "status", "publication_status"), sorts=("airline_code", "candidate_status", "profile_status", "assessment_status", "wave_status", "issue_status", "severity", "status"), historical_reads=True, recommended_indexes=(("airline_intelligence_release_candidates_status_updated_id",) if name == "airline_intelligence_release_candidates" else ()))
            for name in (
                "airline_intelligence_readiness_profiles",
                "airline_intelligence_readiness_assessments",
                "airline_intelligence_readiness_checks",
                "airline_intelligence_release_candidates",
                "airline_intelligence_release_gates",
                "airline_intelligence_release_decisions",
                "airline_intelligence_population_waves",
                "airline_intelligence_scale_issues",
                "airline_knowledge_publications",
                "airline_recommendations",
            )
        ),
        _agency("journey_representations", filters=("status", "presentation_status", "source_entity_type", "source_entity_id", "client_id"), sorts=("status", "presentation_status")),
        _agency("journey_option_compositions", filters=("journey_id", "trip_id", "status", "offer_id", "offer_workspace_id"), sorts=("status",)),
        _agency("journey_offer_deliveries", filters=("journey_id", "offer_id", "status"), sorts=("status",)),
        _agency("journey_offer_acceptance_handoffs", filters=("journey_id", "offer_id", "status"), sorts=("status",), ownership=CollectionOwnershipType.IMMUTABLE_SNAPSHOT, historical_reads=True),
        _agency("audit_events", filters=("entity_type", "entity_id", "event_type", "action"), sorts=("event_type", "action"), ownership=CollectionOwnershipType.AUDIT_SECURITY, historical_reads=True),
    )
}


GOVERNED_INDEX_SPECS: tuple[dict[str, Any], ...] = (
    {"collection": "travel_requests", "name": "travel_requests_agency_updated_id", "keys": (("agency_id", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant request list"},
    {"collection": "travel_request_workspaces", "name": "travel_request_workspaces_agency_status_updated_id", "keys": (("agency_id", 1), ("request_status", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant request queue"},
    {"collection": "trip_dossiers", "name": "trip_dossiers_agency_updated_id", "keys": (("agency_id", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant trip list"},
    {"collection": "trip_workspaces", "name": "trip_workspaces_agency_status_updated_id", "keys": (("agency_id", 1), ("trip_status", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant trip queue"},
    {"collection": "passenger_workspaces", "name": "passenger_workspaces_agency_status_updated_id", "keys": (("agency_id", 1), ("passenger_status", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant passenger list"},
    {"collection": "offer_workspaces", "name": "offer_workspaces_agency_updated_id", "keys": (("agency_id", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant offer list"},
    {"collection": "offer_workspaces_v2", "name": "offer_workspaces_v2_agency_status_updated_id", "keys": (("agency_id", 1), ("offer_status", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant offer queue"},
    {"collection": "booking_workspaces", "name": "booking_workspaces_agency_status_updated_id", "keys": (("agency_id", 1), ("booking_status", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant booking queue"},
    {"collection": "commercial_transactions", "name": "commercial_transactions_agency_posting_id", "keys": (("agency_id", 1), ("posting_time", -1), ("id", -1)), "rationale": "tenant commercial ledger timeline"},
    {"collection": "document_workspaces", "name": "document_workspaces_agency_status_updated_id", "keys": (("agency_id", 1), ("document_status", 1), ("updated_at", -1), ("id", -1)), "rationale": "tenant document queue"},
    {"collection": "operational_work_items", "name": "operational_work_items_agency_status_due_created_id", "keys": (("agency_id", 1), ("status", 1), ("due_at", 1), ("created_at", 1), ("id", 1)), "rationale": "tenant work queue"},
    {"collection": "operational_timelines", "name": "operational_timelines_agency_created_id", "keys": (("agency_id", 1), ("created_at", -1), ("id", -1)), "rationale": "tenant timeline"},
    {"collection": "airline_service_coverage_cells", "name": "airline_service_coverage_cells_airline_service_updated_id", "keys": (("airline_code", 1), ("service_family", 1), ("updated_at", -1), ("id", -1)), "rationale": "global coverage matrix"},
    {"collection": "airline_intelligence_release_candidates", "name": "airline_intelligence_release_candidates_status_updated_id", "keys": (("candidate_status", 1), ("updated_at", -1), ("id", -1)), "rationale": "release readiness queue"},
)


def get_collection_ownership(collection_name: str) -> CollectionOwnership:
    try:
        return COLLECTION_OWNERSHIP_REGISTRY[collection_name]
    except KeyError as exc:
        raise QueryValidationError(f"Collection {collection_name!r} is not registered for governed queries.") from exc


def validate_filters(
    filters: Mapping[str, Any] | None,
    ownership: CollectionOwnership,
    *,
    reserved_fields: Iterable[str] = (),
) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    reserved = set(reserved_fields)
    for field, value in (filters or {}).items():
        if field in reserved or field == ownership.tenant_field:
            raise QueryValidationError("The tenant predicate is controlled by the repository.")
        if field.startswith("$") or "." in field or field not in ownership.allowed_filter_fields:
            raise QueryValidationError(f"Unsupported filter field for {ownership.collection_name}.")
        if isinstance(value, dict):
            if len(value) != 1:
                raise QueryValidationError("Each structured filter must contain exactly one operator.")
            operator, operand = next(iter(value.items()))
            if operator not in SAFE_FILTER_OPERATORS:
                raise QueryValidationError("Unsupported filter operator.")
            if operator == "$in":
                if not isinstance(operand, list) or not operand or len(operand) > MAXIMUM_IN_VALUES:
                    raise QueryValidationError("$in filters require a non-empty bounded list.")
            clean[field] = {operator: operand}
        elif isinstance(value, (str, int, float, bool, type(None))):
            clean[field] = value
        else:
            raise QueryValidationError("Unsupported filter value type.")
    return clean


def validate_projection(projection: Iterable[str] | None, allowed_fields: Iterable[str]) -> dict[str, int] | None:
    if projection is None:
        return None
    allowed = set(allowed_fields) | {"id"}
    requested = set(projection)
    if not requested or not requested.issubset(allowed) or any("." in field or field.startswith("$") for field in requested):
        raise QueryValidationError("Unsupported projection.")
    return {field: 1 for field in requested | {"id"}}


def current_bounded_query_limit() -> int | None:
    return _bounded_query_limit.get()


def bounded_query_context(limit: int = READINESS_QUERY_LIMIT) -> Callable[[Callable[..., Awaitable[_T]]], Callable[..., Awaitable[_T]]]:
    if limit <= 0:
        raise QueryValidationError("Bounded query context requires a positive limit.")

    def decorator(function: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[_T]]:
        @wraps(function)
        async def wrapped(*args: Any, **kwargs: Any) -> _T:
            token = _bounded_query_limit.set(limit)
            try:
                return await function(*args, **kwargs)
            finally:
                _bounded_query_limit.reset(token)

        setattr(wrapped, "bounded_query_limit", limit)
        return wrapped

    return decorator


def record_query_diagnostic(
    *,
    collection_category: str,
    operation: str,
    duration_ms: float,
    returned_count: int,
    requested_limit: int | None,
    tenant_scoped: bool,
    query_class: str,
    correlation_id: str | None = None,
    index_classification: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    effective_query_class = query_class if settings.log_include_query_names else "governed_query"
    payload = {
        "collection_category": collection_category,
        "operation": operation,
        "duration_ms": round(duration_ms, 3),
        "returned_count": returned_count,
        "requested_limit": requested_limit,
        "tenant_scoped": tenant_scoped,
        "query_class": effective_query_class,
        "slow_query": duration_ms >= settings.query_slow_threshold_ms,
        "correlation_id": correlation_id or current_correlation_id(),
        "index_classification": index_classification or "unspecified",
    }
    if settings.query_diagnostics_enabled:
        _diagnostic_records.append(payload)
        del _diagnostic_records[:-100]
        if payload["slow_query"]:
            increment_counter("slow_queries", "slow")
        emit_event(
            "database_query_completed",
            level="WARNING" if payload["slow_query"] else "DEBUG",
            outcome="success",
            duration_ms=duration_ms,
            correlation_id=payload["correlation_id"],
            metadata={
                "collection_category": collection_category,
                "requested_limit": requested_limit,
                "returned_count": returned_count,
                "tenant_scoped": tenant_scoped,
                "query_class": effective_query_class,
                "slow_operation": payload["slow_query"],
                "index_classification": payload["index_classification"],
            },
            logger_name="aeroassist.persistence",
        )
    return payload


def query_diagnostic_records() -> list[dict[str, Any]]:
    return [dict(item) for item in _diagnostic_records]


def encode_cursor(*, collection: str, tenant: str | None, offset: int, sort: SortRequest) -> str:
    payload = {"collection": collection, "tenant": tenant, "offset": offset, "sort": sort.field, "direction": sort.direction}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    secret = (get_settings().auth_token_secret or "aeroassist-development-cursor-key").encode()
    signature = hmac.new(secret, raw, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(raw + b"." + signature.encode()).decode().rstrip("=")


def decode_cursor(cursor: str, *, collection: str, tenant: str | None, sort: SortRequest) -> int:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw_and_signature = base64.urlsafe_b64decode(padded.encode())
        raw, signature = raw_and_signature.rsplit(b".", 1)
        secret = (get_settings().auth_token_secret or "aeroassist-development-cursor-key").encode()
        expected = hmac.new(secret, raw, hashlib.sha256).hexdigest().encode()
        if not hmac.compare_digest(signature, expected):
            raise QueryValidationError("Invalid pagination cursor.")
        payload = json.loads(raw)
    except QueryValidationError:
        raise
    except Exception as exc:
        raise QueryValidationError("Invalid pagination cursor.") from exc
    if payload != {
        "collection": collection,
        "tenant": tenant,
        "offset": payload.get("offset"),
        "sort": sort.field,
        "direction": sort.direction,
    } or not isinstance(payload.get("offset"), int) or payload["offset"] < 0:
        raise QueryValidationError("Pagination cursor does not match the governed query scope.")
    return payload["offset"]


def persistence_readiness_metadata() -> dict[str, Any]:
    settings = get_settings()
    return {
        "bounded_query_helpers_enabled": True,
        "tenant_scoped_repository_enabled": True,
        "platform_global_repository_enabled": True,
        "pagination_contract_enabled": True,
        "deterministic_sorting_enabled": True,
        "sort_allowlist_enabled": True,
        "filter_operator_allowlist_enabled": True,
        "tenant_override_prevention_enabled": True,
        "collection_ownership_registry_enabled": True,
        "index_governance_enabled": True,
        "slow_query_diagnostics_enabled": settings.query_diagnostics_enabled,
        "readiness_queries_bounded": True,
        "destructive_index_changes_disabled": True,
        "cross_tenant_querying_disabled": True,
        "default_query_limit": settings.query_default_limit,
        "maximum_query_limit": settings.query_maximum_limit,
        "registered_collection_count": len(COLLECTION_OWNERSHIP_REGISTRY),
        "governed_index_count": len(GOVERNED_INDEX_SPECS),
        "readiness_required": False,
    }


def monotonic_ms() -> float:
    return time.perf_counter() * 1000
