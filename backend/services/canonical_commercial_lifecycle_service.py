from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

from database import Database
from models import AuditEvent, new_id
from persistence_query import PaginationRequest
from persistence_repository import PersistenceRepository


CANONICAL_COMMERCIAL_LIFECYCLE = (
    "TravelRequest",
    "OfferWorkspace",
    "OfferOption",
    "OfferAcceptance",
    "TripAcceptedOfferSnapshot",
    "TripDossier",
    "OfferBookingHandoff",
    "BookingRecord",
    "TicketRecord",
    "TicketCoupon",
    "EMDRecord",
    "EmdCoupon",
)

LIFECYCLE_WRITER_CLASSIFICATION: dict[str, tuple[str, ...]] = {
    "canonical_writer": (
        "backend/services/offer_builder_service.py",
        "backend/services/offer_acceptance_service.py",
        "backend/services/trip_dossier_service.py",
        "backend/services/booking_workspace_service.py",
        "backend/services/ticket_emd_service.py",
    ),
    "governed_adapter": (
        "backend/services/request_to_trip_conversion_service.py",
        "backend/services/offer_to_booking_handoff_service.py",
        "backend/services/offer_delivery_client_interaction_service.py",
    ),
    "snapshot_writer": ("backend/services/offer_acceptance_service.py",),
    "projection_writer": (
        "backend/services/request_to_trip_conversion_service.py",
    ),
    "compatibility_writer": (
        "backend/routers/offers.py",
        "backend/services/offer_workspace_service.py",
        "backend/services/trip_workspace_service.py",
        "backend/services/ticket_workspace_service.py",
        "backend/services/emd_workspace_service.py",
    ),
    "import_writer": (
        "backend/services/booking_import_service.py",
        "backend/services/ticket_emd_service.py",
    ),
    "deprecated_writer": (
        "backend/routers/bookings.py",
        "backend/routers/portal.py",
    ),
    "decision_required": (),
    "demo_or_test_writer": ("backend/seed_service.py", "backend/scripts/smoke_*.py"),
}

STATUS_COMPATIBILITY: dict[str, dict[str, str]] = {
    "offer": {
        "in_review": "ready",
        "shared": "delivered",
        "rejected": "declined",
        "archived": "cancelled",
    },
    "acceptance": {"cancelled": "revoked", "superseded": "revoked"},
    "trip": {"draft": "planning", "quoted": "planning", "in_travel": "servicing"},
    "booking_workspace": {
        "draft": "preparation",
        "ready_to_book": "ready",
        "booking_in_progress": "submitted_manual",
        "booked": "confirmed",
        "blocked": "preparation",
    },
}

LIFECYCLE_TRANSITIONS: dict[str, dict[str, frozenset[str]]] = {
    "offer": {
        "draft": frozenset({"ready", "cancelled"}),
        "ready": frozenset({"delivered", "draft", "cancelled"}),
        "delivered": frozenset({"accepted", "declined", "expired", "superseded", "cancelled"}),
        "accepted": frozenset({"superseded"}),
        "declined": frozenset({"superseded"}),
        "expired": frozenset({"superseded"}),
        "superseded": frozenset(),
        "cancelled": frozenset(),
    },
    "acceptance": {
        "pending": frozenset({"accepted", "declined", "expired"}),
        "accepted": frozenset({"revoked"}),
        "declined": frozenset(),
        "expired": frozenset(),
        "revoked": frozenset(),
    },
    "trip": {
        "planning": frozenset({"confirmed", "cancelled"}),
        "confirmed": frozenset({"booking_in_progress", "cancelled"}),
        "booking_in_progress": frozenset({"booked", "confirmed", "cancelled"}),
        "booked": frozenset({"ticketed", "servicing", "cancelled"}),
        "ticketed": frozenset({"servicing", "completed", "cancelled"}),
        "servicing": frozenset({"ticketed", "completed", "cancelled"}),
        "completed": frozenset(),
        "cancelled": frozenset(),
    },
    "booking_workspace": {
        "preparation": frozenset({"ready", "cancelled"}),
        "ready": frozenset({"submitted_manual", "preparation", "cancelled"}),
        "submitted_manual": frozenset({"confirmed", "preparation", "cancelled"}),
        "confirmed": frozenset({"cancelled"}),
        "cancelled": frozenset(),
    },
    "booking_record": {
        "draft": frozenset({"pending", "confirmed", "failed", "cancelled"}),
        "pending": frozenset({"confirmed", "partially_confirmed", "failed", "cancelled"}),
        "partially_confirmed": frozenset({"confirmed", "failed", "cancelled"}),
        "confirmed": frozenset({"cancelled"}),
        "failed": frozenset({"pending", "cancelled"}),
        "cancelled": frozenset(),
    },
}

FROZEN_OFFER_STATUSES = frozenset(
    {"delivered", "shared", "accepted", "declined", "rejected", "expired", "superseded", "cancelled", "archived"}
)
CONFIRMED_BOOKING_STATUSES = frozenset({"confirmed", "partially_confirmed"})


class CommercialLifecycleError(ValueError):
    def __init__(self, message: str, *, code: str = "COMMERCIAL_LIFECYCLE_CONFLICT") -> None:
        self.code = code
        super().__init__(message)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def canonical_status(domain: str, status: Any) -> str:
    value = str(getattr(status, "value", status) or "").strip().lower()
    return STATUS_COMPATIBILITY.get(domain, {}).get(value, value)


def validate_lifecycle_transition(domain: str, current: Any, target: Any) -> tuple[str, str]:
    current_value = canonical_status(domain, current)
    target_value = canonical_status(domain, target)
    if current_value == target_value:
        return current_value, target_value
    transitions = LIFECYCLE_TRANSITIONS.get(domain)
    if transitions is None or target_value not in transitions.get(current_value, frozenset()):
        raise CommercialLifecycleError(
            f"Invalid {domain} lifecycle transition from {current_value or 'unknown'} to {target_value or 'unknown'}.",
            code="INVALID_LIFECYCLE_TRANSITION",
        )
    return current_value, target_value


def canonical_json_hash(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def acceptance_idempotency_key(
    agency_id: str,
    workspace_id: str,
    workspace_version: int,
    option_id: str,
    option_version: int,
    actor_id: str | None,
    supplied_key: str | None,
    decision: str = "accepted",
) -> str:
    if supplied_key:
        return str(supplied_key).strip()[:180]
    return canonical_json_hash(
        {
            "agency_id": agency_id,
            "workspace_id": workspace_id,
            "workspace_version": workspace_version,
            "option_id": option_id,
            "option_version": option_version,
            "actor_id": actor_id,
            "decision": decision,
        }
    )


def booking_result_has_governed_evidence(record: dict[str, Any]) -> bool:
    source_context = str(record.get("source_context") or "")
    evidence_reference = str(
        record.get("source_evidence_reference")
        or record.get("import_draft_id")
        or record.get("pnr_locator")
        or ""
    ).strip()
    provider_evidence = bool(
        record.get("provider_response_json")
        or record.get("source_evidence_json")
        or record.get("internal_pnr_mirror_json")
    )
    return bool(
        evidence_reference
        and (
            provider_evidence
            or source_context
            in {
                "standalone_manual",
                "imported_gds",
                "imported_confirmation",
                "existing_trip_change",
            }
        )
    )


async def write_lifecycle_evidence(
    db: Database,
    *,
    agency_id: str,
    actor_user_id: str | None,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    previous_status: str | None = None,
    next_status: str | None = None,
    request_id: str | None = None,
    trip_id: str | None = None,
    booking_workspace_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, str]:
    correlation_id = str((metadata or {}).get("correlation_id") or new_id())
    evidence = {
        "correlation_id": correlation_id,
        "previous_status": previous_status,
        "next_status": next_status,
        **(metadata or {}),
    }
    audit = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=evidence,
    )
    audit_record = await db.collection("audit_events").insert_one(audit.model_dump(mode="json"))
    timeline_record = await db.collection("operational_timelines").insert_one(
        {
            "id": new_id(),
            "agency_id": agency_id,
            "timeline_reference": f"commercial-lifecycle:{correlation_id}",
            "created_at": now_utc(),
            "updated_at": now_utc(),
            "created_by": actor_user_id,
            "travel_request_workspace_id": request_id,
            "trip_workspace_id": trip_id,
            "booking_workspace_id": booking_workspace_id,
            "event_type": event_type,
            "event_category": "commercial_lifecycle",
            "event_source": "canonical_commercial_lifecycle",
            "event_status": next_status or "recorded",
            "event_priority": "normal",
            "operational_stage": entity_type,
            "operational_result": next_status,
            "summary": summary,
            "internal_only": True,
            "passenger_visible": False,
            "airline_visible": False,
            "metadata": evidence,
            "metadata_only": True,
            "automation_disabled": True,
        }
    )
    return {"audit_event_id": audit_record["id"], "timeline_event_id": timeline_record["id"]}


def canonical_commercial_lifecycle_readiness_metadata() -> dict[str, Any]:
    return {
        "canonical_flow": list(CANONICAL_COMMERCIAL_LIFECYCLE),
        "offer_workspace_is_canonical_offer_owner": True,
        "offer_option_is_canonical_alternative_owner": True,
        "offer_versioning_and_supersession_enabled": True,
        "acceptance_exact_version_required": True,
        "acceptance_idempotency_enabled": True,
        "acceptance_lifecycle_mutable_payload_immutable": True,
        "accepted_offer_snapshot_create_only": True,
        "accepted_offer_snapshot_integrity_hash_enabled": True,
        "trip_confirmation_requires_accepted_snapshot": True,
        "request_conversion_planning_only_before_acceptance": True,
        "booking_workspace_external_truth_disabled": True,
        "booking_record_evidence_required_for_confirmation": True,
        "ticket_emd_booking_lineage_enforced": True,
        "central_lifecycle_transition_validation_enabled": True,
        "audit_and_timeline_evidence_enabled": True,
        "compatibility_writers_registered": True,
        "migration_analysis_write_mode_disabled": True,
        "provider_booking_execution_disabled": True,
        "ticket_emd_issuance_disabled": True,
        "payment_execution_disabled": True,
        "readiness_required": False,
    }


def _group_by_agency(items: Iterable[dict[str, Any]]) -> Counter[str]:
    return Counter(str(item.get("agency_id") or "unscoped") for item in items)


async def find_canonical_workspace_for_legacy_offer(
    db: Database,
    *,
    agency_id: str,
    legacy_offer_id: str,
    request_id: str | None,
    maximum_records: int = 5000,
) -> dict[str, Any] | None:
    if request_id:
        workspace = await db.collection("offer_workspaces").find_one(
            {"agency_id": agency_id, "request_id": request_id}
        )
        if workspace:
            return workspace

    repository = PersistenceRepository(db)
    offset = 0
    while offset < maximum_records:
        page_request = PaginationRequest.build(
            limit=maximum_records - offset,
            offset=offset,
        )
        page = await repository.find_agency_records(
            collection_name="offer_workspaces",
            agency_id=agency_id,
            pagination=page_request,
        )
        workspace = next(
            (
                item
                for item in page.items
                if (item.get("compatibility_metadata") or {}).get(
                    "legacy_offer_id"
                )
                == legacy_offer_id
            ),
            None,
        )
        if workspace:
            return workspace
        if not page.pagination.has_more:
            return None
        offset += len(page.items)

    # Failing closed protects canonical ownership if a legacy estate exceeds
    # the bounded reconciliation scan.
    return {"id": "canonical-owner-scan-limit", "reconciliation_required": True}


async def analyze_commercial_lifecycle(
    db: Database,
    *,
    maximum_records_per_collection: int = 5000,
) -> dict[str, Any]:
    collection_names = (
        "offers",
        "offer_workspaces",
        "offer_workspaces_v2",
        "offer_options",
        "offer_acceptances",
        "trip_accepted_offer_snapshots",
        "trip_dossiers",
        "trip_workspaces",
        "offer_booking_handoffs",
        "booking_workspaces",
        "booking_records",
        "bookings",
        "ticket_records",
        "ticket_workspaces",
        "emd_records",
        "emd_workspaces",
    )
    records: dict[str, list[dict[str, Any]]] = {}
    before_counts: dict[str, int] = {}
    repository = PersistenceRepository(db)
    for collection_name in collection_names:
        before_counts[collection_name] = await db.collection(collection_name).count()
        rows: list[dict[str, Any]] = []
        offset = 0
        while len(rows) < maximum_records_per_collection:
            page_request = PaginationRequest.build(
                limit=maximum_records_per_collection - len(rows),
                offset=offset,
            )
            page = await repository.find_platform_records(
                collection_name=collection_name,
                pagination=page_request,
            )
            rows.extend(page.items)
            if len(page.items) < page_request.limit:
                break
            offset += len(page.items)
        records[collection_name] = rows

    findings: list[dict[str, Any]] = []

    def add(
        domain: str,
        issue_type: str,
        item: dict[str, Any],
        *,
        deterministic: bool,
        details: str,
    ) -> None:
        findings.append(
            {
                "domain": domain,
                "issue_type": issue_type,
                "agency_id": item.get("agency_id"),
                "record_id": item.get("id"),
                "deterministic_reconciliation_candidate": deterministic,
                "manual_review_required": not deterministic,
                "details": details,
            }
        )

    canonical_offer_keys = {
        (item.get("agency_id"), item.get("request_id"))
        for item in records["offer_workspaces"]
        if item.get("request_id")
    }
    for item in records["offers"]:
        if (item.get("agency_id"), item.get("request_id")) not in canonical_offer_keys:
            add("offer", "legacy_offer_without_canonical_workspace", item, deterministic=False, details="Legacy Offer has no canonical OfferWorkspace for the same Agency and Request.")
    for item in records["offer_options"]:
        parent = next(
            (
                workspace
                for workspace in records["offer_workspaces"]
                if workspace.get("agency_id") == item.get("agency_id")
                and workspace.get("id") == (item.get("offer_workspace_id") or item.get("workspace_id"))
            ),
            None,
        )
        if parent is None:
            add("offer", "option_without_canonical_parent", item, deterministic=False, details="OfferOption has no same-Agency canonical OfferWorkspace.")

    active_acceptances: defaultdict[tuple[str | None, str | None, int], list[dict[str, Any]]] = defaultdict(list)
    for item in records["offer_acceptances"]:
        key = (item.get("agency_id"), item.get("workspace_id"), int(item.get("offer_version") or 1))
        if canonical_status("acceptance", item.get("status")) == "accepted":
            active_acceptances[key].append(item)
        snapshot = next(
            (
                row
                for row in records["trip_accepted_offer_snapshots"]
                if row.get("agency_id") == item.get("agency_id")
                and row.get("acceptance_id") == item.get("id")
            ),
            None,
        )
        if item.get("status") == "accepted" and snapshot is None:
            add("acceptance", "accepted_without_immutable_snapshot", item, deterministic=False, details="Accepted decision has no immutable accepted-offer snapshot.")
    for duplicates in active_acceptances.values():
        if len(duplicates) > 1:
            for item in duplicates:
                add("acceptance", "multiple_active_acceptances", item, deterministic=False, details="More than one active acceptance exists for the same Offer revision.")

    snapshot_ids = {item.get("id") for item in records["trip_accepted_offer_snapshots"]}
    trip_ids = {item.get("id") for item in records["trip_dossiers"]}
    for item in records["trip_accepted_offer_snapshots"]:
        if item.get("trip_id") not in trip_ids:
            add("trip", "accepted_snapshot_without_trip", item, deterministic=True, details="Snapshot has a deterministic Trip ID but the Trip is missing.")
    for item in records["trip_dossiers"]:
        status = canonical_status("trip", item.get("trip_status"))
        if status != "planning" and item.get("creation_mode") in {None, "", "request_planning_projection"} and item.get("accepted_offer_snapshot_id") not in snapshot_ids:
            add("trip", "confirmed_trip_without_accepted_snapshot_or_exception", item, deterministic=False, details="Trip appears confirmed without accepted evidence or a governed exception mode.")

    for item in records["booking_workspaces"]:
        if canonical_status("booking_workspace", item.get("status")) == "confirmed":
            record = next(
                (
                    row
                    for row in records["booking_records"]
                    if row.get("agency_id") == item.get("agency_id")
                    and (
                        row.get("id") == item.get("booking_record_id")
                        or row.get("booking_workspace_id") == item.get("id")
                    )
                ),
                None,
            )
            if not record or canonical_status("booking_record", record.get("booking_status")) not in CONFIRMED_BOOKING_STATUSES or not booking_result_has_governed_evidence(record):
                add("booking", "workspace_represents_confirmed_result", item, deterministic=False, details="BookingWorkspace claims booked/confirmed without an evidenced BookingRecord.")
    for item in records["booking_records"]:
        if not item.get("trip_id") or (
            item.get("source_context") == "offer_readiness"
            and not (item.get("offer_booking_handoff_id") or item.get("accepted_offer_snapshot_id"))
        ):
            add("booking", "booking_record_missing_lineage", item, deterministic=False, details="BookingRecord lacks Trip or accepted-offer handoff lineage.")

    for domain, rows in (("ticket", records["ticket_records"]), ("emd", records["emd_records"])):
        for item in rows:
            if not item.get("booking_record_id") and item.get("source_context") in {
                "booking_record",
                "booking_service",
                None,
                "",
            }:
                add(domain, f"{domain}_without_booking_lineage", item, deterministic=False, details=f"{domain.title()} normal-flow record has no BookingRecord.")

    locator_groups: defaultdict[tuple[str | None, str], list[dict[str, Any]]] = defaultdict(list)
    for item in records["booking_records"]:
        locator = str(item.get("pnr_locator") or "").strip().upper()
        if locator:
            locator_groups[(item.get("agency_id"), locator)].append(item)
    for duplicates in locator_groups.values():
        if len(duplicates) > 1:
            for item in duplicates:
                add("booking", "duplicate_record_locator", item, deterministic=False, details="Record locator is duplicated within the Agency.")

    domain_counts = Counter(item["domain"] for item in findings)
    issue_counts = Counter(item["issue_type"] for item in findings)
    agency_counts = Counter(str(item.get("agency_id") or "unscoped") for item in findings)
    after_counts = {
        collection_name: await db.collection(collection_name).count()
        for collection_name in collection_names
    }
    return {
        "dry_run": True,
        "write_mode_available": False,
        "writes_performed": 0,
        "before_counts": before_counts,
        "after_counts": after_counts,
        "counts_unchanged": before_counts == after_counts,
        "records_scanned_by_collection": {
            name: len(items) for name, items in records.items()
        },
        "scan_truncated_collections": [
            name
            for name, total in before_counts.items()
            if total > maximum_records_per_collection
        ],
        "finding_count": len(findings),
        "counts_by_domain": dict(sorted(domain_counts.items())),
        "counts_by_issue_type": dict(sorted(issue_counts.items())),
        "counts_by_agency": dict(sorted(agency_counts.items())),
        "deterministic_reconciliation_candidates": [
            item for item in findings if item["deterministic_reconciliation_candidate"]
        ][:100],
        "ambiguous_cases": [
            item for item in findings if item["manual_review_required"]
        ][:100],
        "manual_review_cases": len(
            [item for item in findings if item["manual_review_required"]]
        ),
        "writer_classification": LIFECYCLE_WRITER_CLASSIFICATION,
        "future_migration_requirements": {
            "explicit_confirmation": True,
            "one_agency_and_domain_at_a_time": True,
            "before_after_manifest": True,
            "audit_evidence": True,
            "rollback_plan": True,
            "automatic_ambiguous_reconciliation": False,
        },
    }
