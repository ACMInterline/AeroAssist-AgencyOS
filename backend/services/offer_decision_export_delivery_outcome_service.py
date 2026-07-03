from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionExportDeliveryIssue,
    OfferDecisionExportDeliveryIssueCreateRequest,
    OfferDecisionExportDeliveryIssueUpdateRequest,
    OfferDecisionExportDeliveryOutcome,
    OfferDecisionExportDeliveryOutcomeCreateRequest,
    OfferDecisionExportDeliveryOutcomeEvent,
    OfferDecisionExportDeliveryOutcomeEventCreateRequest,
    OfferDecisionExportDeliveryOutcomeSnapshot,
    OfferDecisionExportDeliveryOutcomeSnapshotCreateRequest,
    OfferDecisionExportDeliveryOutcomeUpdateRequest,
    OfferDecisionExportDeliveryReceipt,
    OfferDecisionExportDeliveryReceiptCreateRequest,
    now_utc,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_37_9_offer_decision_export_manual_delivery_outcome_foundation"

HANDOFF_COLLECTION = "offer_decision_export_delivery_handoffs"
OUTCOME_COLLECTION = "offer_decision_export_delivery_outcomes"
EVENT_COLLECTION = "offer_decision_export_delivery_outcome_events"
RECEIPT_COLLECTION = "offer_decision_export_delivery_receipts"
ISSUE_COLLECTION = "offer_decision_export_delivery_issues"
SNAPSHOT_COLLECTION = "offer_decision_export_delivery_outcome_snapshots"


class OfferDecisionExportDeliveryOutcomeService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "outcome_count": len(await self.list_outcomes(agency_id=agency_id)),
            "event_count": len(await self.list_events(agency_id=agency_id)),
            "receipt_count": len(await self.list_receipts(agency_id=agency_id)),
            "issue_count": len(await self.list_issues(agency_id=agency_id)),
            "snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "delivery_outcomes_enabled": True,
            "delivery_outcome_events_enabled": True,
            "delivery_receipts_enabled": True,
            "delivery_issues_enabled": True,
            "immutable_outcome_snapshots_enabled": True,
            "agency_delivery_outcome_ui_enabled": True,
            "platform_delivery_outcome_ui_enabled": True,
            "manual_tracking_only_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 37.9 manual delivery outcome tracking is metadata-only. It records human-entered outcome status, manual events, receipt metadata, issue metadata, and immutable snapshots after delivery occurs outside AgencyOS; it never sends email or SMS, creates public links, delivers real PDFs, mutates offers/prices, recommends airlines, books, mutates PNRs, issues tickets or EMDs, charges, invoices, settles, scrapes, calls external AI, or executes providers.",
        }

    async def create_outcome(
        self,
        agency_id: str,
        payload: OfferDecisionExportDeliveryOutcomeCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        handoff = await self._require_handoff(agency_id, data["handoff_id"])
        outcome = OfferDecisionExportDeliveryOutcome(
            agency_id=agency_id,
            handoff_id=handoff["id"],
            export_id=handoff.get("export_id"),
            preview_id=handoff.get("preview_id"),
            release_readiness_id=handoff.get("release_readiness_id"),
            title=data.get("title") or f"Manual delivery outcome for handoff {handoff['id']}",
            outcome_status=data.get("outcome_status") or "pending",
            actor_type=data.get("actor_type") or "agency_user",
            recorded_by=data.get("recorded_by") or actor_from_user(user),
            outcome_summary=self._outcome_summary(handoff),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(OUTCOME_COLLECTION).insert_one(outcome.model_dump(mode="json"))
        return {"outcome": stored, **self._safety_flags()}

    async def list_outcomes(
        self,
        *,
        agency_id: str | None = None,
        handoff_id: str | None = None,
        outcome_status: str | None = None,
        export_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(OUTCOME_COLLECTION, agency_id=agency_id, handoff_id=handoff_id, outcome_status=outcome_status, export_id=export_id)

    async def get_outcome(self, outcome_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": outcome_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(OUTCOME_COLLECTION).find_one(filters)

    async def get_outcome_detail(self, outcome_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        outcome = await self.get_outcome(outcome_id, agency_id)
        if not outcome:
            return None
        return {
            "outcome": outcome,
            "events": await self.list_events(agency_id=agency_id, outcome_id=outcome_id),
            "receipts": await self.list_receipts(agency_id=agency_id, outcome_id=outcome_id),
            "issues": await self.list_issues(agency_id=agency_id, outcome_id=outcome_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, outcome_id=outcome_id),
            **self._safety_flags(),
        }

    async def update_outcome(
        self,
        agency_id: str,
        outcome_id: str,
        payload: OfferDecisionExportDeliveryOutcomeUpdateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        outcome = await self._require_outcome(agency_id, outcome_id)
        updated = await self.db.collection(OUTCOME_COLLECTION).update_one(
            {"agency_id": agency_id, "id": outcome_id},
            {
                "outcome_status": enum_value(data["outcome_status"]),
                "status_reason": data.get("status_reason"),
                "actor_type": data.get("actor_type") or outcome.get("actor_type") or "agency_user",
                "recorded_by": data.get("recorded_by") or actor_from_user(user) or outcome.get("recorded_by"),
                "metadata_json": {**(outcome.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        return {"outcome": updated or outcome, **self._safety_flags()}

    async def add_event(
        self,
        agency_id: str,
        outcome_id: str,
        payload: OfferDecisionExportDeliveryOutcomeEventCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        outcome = await self._require_outcome(agency_id, outcome_id)
        event = OfferDecisionExportDeliveryOutcomeEvent(
            agency_id=agency_id,
            outcome_id=outcome_id,
            handoff_id=outcome["handoff_id"],
            event_type=data.get("event_type") or "sent_recorded",
            actor_type=data.get("actor_type") or "agency_user",
            actor_label=data.get("actor_label") or actor_from_user(user),
            event_title=data.get("event_title"),
            event_note=data.get("event_note"),
            occurred_at=data.get("occurred_at") or now_utc(),
            event_json=data.get("event_json") or {},
        )
        stored = await self.db.collection(EVENT_COLLECTION).insert_one(event.model_dump(mode="json"))
        refreshed = await self._refresh_outcome_counts(agency_id, outcome_id)
        return {"outcome": refreshed, "event": stored, **self._safety_flags()}

    async def list_events(
        self,
        *,
        agency_id: str | None = None,
        outcome_id: str | None = None,
        handoff_id: str | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(EVENT_COLLECTION, agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, event_type=event_type, date_key="occurred_at")

    async def add_receipt(
        self,
        agency_id: str,
        outcome_id: str,
        payload: OfferDecisionExportDeliveryReceiptCreateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        outcome = await self._require_outcome(agency_id, outcome_id)
        receipt = OfferDecisionExportDeliveryReceipt(
            agency_id=agency_id,
            outcome_id=outcome_id,
            handoff_id=outcome["handoff_id"],
            receipt_type=data.get("receipt_type") or "manual_note",
            reference_label=data.get("reference_label"),
            received_from=data.get("received_from"),
            received_at=data.get("received_at"),
            notes=data.get("notes"),
            external_reference_metadata=data.get("external_reference_metadata"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(RECEIPT_COLLECTION).insert_one(receipt.model_dump(mode="json"))
        refreshed = await self._refresh_outcome_counts(agency_id, outcome_id)
        return {"outcome": refreshed, "receipt": stored, **self._safety_flags()}

    async def list_receipts(
        self,
        *,
        agency_id: str | None = None,
        outcome_id: str | None = None,
        handoff_id: str | None = None,
        receipt_type: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(RECEIPT_COLLECTION, agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, receipt_type=receipt_type)

    async def add_issue(
        self,
        agency_id: str,
        outcome_id: str,
        payload: OfferDecisionExportDeliveryIssueCreateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        outcome = await self._require_outcome(agency_id, outcome_id)
        issue = OfferDecisionExportDeliveryIssue(
            agency_id=agency_id,
            outcome_id=outcome_id,
            handoff_id=outcome["handoff_id"],
            issue_type=data.get("issue_type") or "other",
            severity=data.get("severity") or "medium",
            title=data["title"],
            description=data.get("description"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(ISSUE_COLLECTION).insert_one(issue.model_dump(mode="json"))
        refreshed = await self._refresh_outcome_counts(agency_id, outcome_id)
        return {"outcome": refreshed, "issue": stored, **self._safety_flags()}

    async def update_issue(
        self,
        agency_id: str,
        issue_id: str,
        payload: OfferDecisionExportDeliveryIssueUpdateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        issue = await self._require_record(ISSUE_COLLECTION, agency_id, issue_id, "Delivery outcome issue metadata not found.")
        resolved = enum_value(data["issue_status"]) == "resolved"
        updated = await self.db.collection(ISSUE_COLLECTION).update_one(
            {"agency_id": agency_id, "id": issue_id},
            {
                "issue_status": enum_value(data["issue_status"]),
                "resolved_by": data.get("resolved_by") or (actor_from_user(user) if resolved else issue.get("resolved_by")),
                "resolved_at": now_utc() if resolved else None,
                "resolution_notes": data.get("resolution_notes"),
                "metadata_json": {**(issue.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_outcome_counts(agency_id, issue["outcome_id"])
        return {"outcome": refreshed, "issue": updated or issue, **self._safety_flags()}

    async def list_issues(
        self,
        *,
        agency_id: str | None = None,
        outcome_id: str | None = None,
        handoff_id: str | None = None,
        issue_status: str | None = None,
        issue_type: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(ISSUE_COLLECTION, agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, issue_status=issue_status, issue_type=issue_type)

    async def create_snapshot(
        self,
        agency_id: str,
        outcome_id: str,
        payload: OfferDecisionExportDeliveryOutcomeSnapshotCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        detail = await self.get_outcome_detail(outcome_id, agency_id)
        if not detail:
            raise ValueError("Delivery outcome metadata not found.")
        outcome = detail["outcome"]
        snapshot = OfferDecisionExportDeliveryOutcomeSnapshot(
            agency_id=agency_id,
            outcome_id=outcome_id,
            handoff_id=outcome["handoff_id"],
            snapshot_type=data.get("snapshot_type") or "outcome_recorded",
            payload={
                "outcome": outcome,
                "events": detail["events"],
                "receipts": detail["receipts"],
                "issues": detail["issues"],
                "safety_flags": self._safety_flags(),
                "metadata_json": data.get("metadata_json") or {},
            },
            created_by=data.get("created_by") or actor_from_user(user),
        )
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        refreshed = await self._refresh_outcome_counts(agency_id, outcome_id)
        return {"outcome": refreshed, "snapshot": stored, **self._safety_flags()}

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        outcome_id: str | None = None,
        handoff_id: str | None = None,
        snapshot_type: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(SNAPSHOT_COLLECTION, agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, snapshot_type=snapshot_type)

    async def _list_records(self, collection_name: str, date_key: str = "created_at", **filters: Any) -> list[dict[str, Any]]:
        query = {key: value for key, value in filters.items() if value is not None}
        items = await self.db.collection(collection_name).find_many(query or None)
        return sorted(items, key=lambda item: str(item.get(date_key) or item.get("created_at") or ""), reverse=True)

    async def _require_record(self, collection_name: str, agency_id: str, record_id: str, message: str) -> dict[str, Any]:
        record = await self.db.collection(collection_name).find_one({"agency_id": agency_id, "id": record_id})
        if not record:
            raise ValueError(message)
        return record

    async def _require_handoff(self, agency_id: str, handoff_id: str) -> dict[str, Any]:
        return await self._require_record(HANDOFF_COLLECTION, agency_id, handoff_id, "Delivery handoff metadata not found.")

    async def _require_outcome(self, agency_id: str, outcome_id: str) -> dict[str, Any]:
        return await self._require_record(OUTCOME_COLLECTION, agency_id, outcome_id, "Delivery outcome metadata not found.")

    async def _refresh_outcome_counts(self, agency_id: str, outcome_id: str) -> dict[str, Any] | None:
        outcome = await self._require_outcome(agency_id, outcome_id)
        events = await self.list_events(agency_id=agency_id, outcome_id=outcome_id)
        receipts = await self.list_receipts(agency_id=agency_id, outcome_id=outcome_id)
        issues = await self.list_issues(agency_id=agency_id, outcome_id=outcome_id)
        snapshots = await self.list_snapshots(agency_id=agency_id, outcome_id=outcome_id)
        return await self.db.collection(OUTCOME_COLLECTION).update_one(
            {"agency_id": agency_id, "id": outcome_id},
            {
                "event_count": len(events),
                "receipt_count": len(receipts),
                "issue_count": len(issues),
                "unresolved_issue_count": len([item for item in issues if item.get("issue_status") != "resolved"]),
                "snapshot_count": len(snapshots),
                "outcome_summary": {**(outcome.get("outcome_summary") or {}), "latest_counts_refreshed_at": now_utc()},
            },
        )

    def _outcome_summary(self, handoff: dict[str, Any]) -> dict[str, Any]:
        return {
            "handoff_id": handoff.get("id"),
            "handoff_status": handoff.get("status"),
            "export_id": handoff.get("export_id"),
            "preview_id": handoff.get("preview_id"),
            "release_readiness_id": handoff.get("release_readiness_id"),
            "manual_tracking_only_enabled": True,
            **self._safety_flags(),
        }

    def _safety_flags(self) -> dict[str, bool]:
        return {
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
            "offer_price_mutation_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
        }
