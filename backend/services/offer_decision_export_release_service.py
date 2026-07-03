from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionExportApproval,
    OfferDecisionExportApprovalCheckpoint,
    OfferDecisionExportApprovalCheckpointCreateRequest,
    OfferDecisionExportApprovalCreateRequest,
    OfferDecisionExportApprovalStatus,
    OfferDecisionExportApprovalStatusUpdateRequest,
    OfferDecisionExportReleaseHold,
    OfferDecisionExportReleaseHoldCreateRequest,
    OfferDecisionExportReleaseHoldReleaseRequest,
    OfferDecisionExportReleaseHoldStatus,
    OfferDecisionExportReleaseReadiness,
    OfferDecisionExportReleaseReadinessCreateRequest,
    OfferDecisionExportReleaseReadinessStatus,
    OfferDecisionExportReleaseSnapshot,
    OfferDecisionExportReleaseSnapshotCreateRequest,
    now_utc,
)


PHASE_LABEL = "phase_37_7_offer_decision_export_release_readiness_foundation"

APPROVAL_COLLECTION = "offer_decision_export_approvals"
CHECKPOINT_COLLECTION = "offer_decision_export_approval_checkpoints"
READINESS_COLLECTION = "offer_decision_export_release_readiness"
HOLD_COLLECTION = "offer_decision_export_release_holds"
SNAPSHOT_COLLECTION = "offer_decision_export_release_snapshots"

PREVIEW_COLLECTION = "offer_decision_export_previews"
PREVIEW_SECTION_COLLECTION = "offer_decision_export_preview_sections"
PREVIEW_BLOCK_COLLECTION = "offer_decision_export_preview_blocks"
PREVIEW_VALIDATION_COLLECTION = "offer_decision_export_preview_validations"
PREVIEW_SNAPSHOT_COLLECTION = "offer_decision_export_preview_snapshots"
EXPORT_COLLECTION = "offer_decision_exports"


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True)
    return dict(payload or {})


def enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def actor_from_user(user: dict | None) -> str | None:
    if not user:
        return None
    return user.get("id") or user.get("email") or user.get("full_name")


class OfferDecisionExportReleaseService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "approval_count": len(await self.list_approvals(agency_id=agency_id)),
            "checkpoint_count": len(await self.list_checkpoints(agency_id=agency_id)),
            "readiness_count": len(await self.list_readiness(agency_id=agency_id)),
            "hold_count": len(await self.list_holds(agency_id=agency_id)),
            "snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "export_approvals_enabled": True,
            "approval_checkpoints_enabled": True,
            "release_readiness_enabled": True,
            "release_holds_enabled": True,
            "immutable_release_snapshots_enabled": True,
            "agency_export_release_ui_enabled": True,
            "platform_export_release_ui_enabled": True,
            "human_approval_required_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Offer decision export release readiness is metadata-only. It prepares human-reviewed manual release readiness records and never sends, publishes, delivers PDFs, mutates offers/prices, recommends airlines, books, issues, charges, invoices, settles, scrapes, calls external AI, or executes providers.",
        }

    async def create_approval(
        self,
        agency_id: str,
        payload: OfferDecisionExportApprovalCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        preview = await self._require_preview(agency_id, data["preview_id"])
        approval = OfferDecisionExportApproval(
            agency_id=agency_id,
            preview_id=preview["id"],
            export_id=preview["export_id"],
            decision_pack_id=preview.get("decision_pack_id"),
            approval_name=data.get("approval_name") or f"Manual release approval for preview {preview['id']}",
            requested_by=actor_from_user(user),
            assigned_reviewer=data.get("assigned_reviewer"),
            approval_summary_json=self._approval_summary(preview),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(APPROVAL_COLLECTION).insert_one(approval.model_dump(mode="json"))
        return {"approval": stored, **self._safety_flags()}

    async def list_approvals(
        self,
        *,
        agency_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(APPROVAL_COLLECTION, agency_id=agency_id, preview_id=preview_id, export_id=export_id, approval_status=approval_status)

    async def get_approval(self, approval_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": approval_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(APPROVAL_COLLECTION).find_one(filters)

    async def get_approval_detail(self, approval_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        approval = await self.get_approval(approval_id, agency_id)
        if not approval:
            return None
        return {
            "approval": approval,
            "checkpoints": await self.list_checkpoints(agency_id=agency_id, approval_id=approval_id),
            "readiness": await self.list_readiness(agency_id=agency_id, approval_id=approval_id),
            **self._safety_flags(),
        }

    async def add_checkpoint(
        self,
        agency_id: str,
        approval_id: str,
        payload: OfferDecisionExportApprovalCheckpointCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        approval = await self._require_approval(agency_id, approval_id)
        sequence_order = len(await self.list_checkpoints(agency_id=agency_id, approval_id=approval_id)) + 1
        reviewed_by = data.get("reviewed_by") or actor_from_user(user)
        checkpoint = OfferDecisionExportApprovalCheckpoint(
            agency_id=agency_id,
            approval_id=approval_id,
            preview_id=approval["preview_id"],
            export_id=approval["export_id"],
            decision_pack_id=approval.get("decision_pack_id"),
            checkpoint_type=data.get("checkpoint_type") or "preview_review",
            checkpoint_status=data.get("checkpoint_status") or "pending",
            checkpoint_title=data["checkpoint_title"],
            notes=data.get("notes"),
            reviewed_by=reviewed_by,
            reviewed_at=now_utc() if reviewed_by else None,
            sequence_order=sequence_order,
            checkpoint_json=data.get("checkpoint_json") or {},
        )
        stored = await self.db.collection(CHECKPOINT_COLLECTION).insert_one(checkpoint.model_dump(mode="json"))
        updated_approval = await self.db.collection(APPROVAL_COLLECTION).update_one(
            {"agency_id": agency_id, "id": approval_id},
            {"checkpoint_count": len(await self.list_checkpoints(agency_id=agency_id, approval_id=approval_id))},
        )
        return {"approval": updated_approval or approval, "checkpoint": stored, **self._safety_flags()}

    async def update_approval_status(
        self,
        agency_id: str,
        approval_id: str,
        payload: OfferDecisionExportApprovalStatusUpdateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        approval = await self._require_approval(agency_id, approval_id)
        status_value = enum_value(data["approval_status"])
        actor = data.get("status_updated_by") or actor_from_user(user)
        now = now_utc()
        updates: dict[str, Any] = {
            "approval_status": status_value,
            "status_updated_by": actor,
            "status_updated_at": now,
            "status_reason": data.get("status_reason"),
            "metadata_json": {**(approval.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
        }
        if status_value == OfferDecisionExportApprovalStatus.APPROVED.value:
            updates["approved_by"] = actor
            updates["approved_at"] = now
            updates["rejected_by"] = None
            updates["rejected_at"] = None
        elif status_value == OfferDecisionExportApprovalStatus.REJECTED.value:
            updates["rejected_by"] = actor
            updates["rejected_at"] = now
        updated = await self.db.collection(APPROVAL_COLLECTION).update_one({"agency_id": agency_id, "id": approval_id}, updates)
        return {"approval": updated or approval, **self._safety_flags()}

    async def create_readiness(
        self,
        agency_id: str,
        payload: OfferDecisionExportReleaseReadinessCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        approval = None
        if data.get("approval_id"):
            approval = await self._require_approval(agency_id, data["approval_id"])
        preview_id = data.get("preview_id") or (approval or {}).get("preview_id")
        if not preview_id:
            raise ValueError("preview_id or approval_id is required.")
        preview = await self._require_preview(agency_id, preview_id)
        if approval and approval.get("preview_id") != preview["id"]:
            raise ValueError("Approval does not belong to preview.")
        bundle = await self._preview_bundle(agency_id, preview)
        approved = bool(approval and approval.get("approval_status") == OfferDecisionExportApprovalStatus.APPROVED.value)
        readiness = OfferDecisionExportReleaseReadiness(
            agency_id=agency_id,
            preview_id=preview["id"],
            export_id=preview["export_id"],
            decision_pack_id=preview.get("decision_pack_id"),
            approval_id=approval.get("id") if approval else None,
            readiness_name=data.get("readiness_name") or f"Manual release readiness for preview {preview['id']}",
            readiness_status=OfferDecisionExportReleaseReadinessStatus.READY if approved else OfferDecisionExportReleaseReadinessStatus.DRAFT,
            prepared_by=data.get("prepared_by") or actor_from_user(user),
            ready_for_manual_release=approved,
            readiness_summary_json=self._readiness_summary(preview, approval, bundle),
            source_counts_json=self._source_counts(bundle),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(READINESS_COLLECTION).insert_one(readiness.model_dump(mode="json"))
        if approval:
            await self.db.collection(APPROVAL_COLLECTION).update_one(
                {"agency_id": agency_id, "id": approval["id"]},
                {"readiness_count": len(await self.list_readiness(agency_id=agency_id, approval_id=approval["id"]))},
            )
        return {"readiness": stored, **self._safety_flags()}

    async def list_readiness(
        self,
        *,
        agency_id: str | None = None,
        approval_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
        readiness_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(READINESS_COLLECTION, agency_id=agency_id, approval_id=approval_id, preview_id=preview_id, export_id=export_id, readiness_status=readiness_status)

    async def get_readiness(self, readiness_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": readiness_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(READINESS_COLLECTION).find_one(filters)

    async def get_readiness_detail(self, readiness_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        readiness = await self.get_readiness(readiness_id, agency_id)
        if not readiness:
            return None
        return {
            "readiness": readiness,
            "approval": await self.get_approval(readiness["approval_id"], agency_id) if readiness.get("approval_id") else None,
            "holds": await self.list_holds(agency_id=agency_id, readiness_id=readiness_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, readiness_id=readiness_id),
            **self._safety_flags(),
        }

    async def add_hold(
        self,
        agency_id: str,
        readiness_id: str,
        payload: OfferDecisionExportReleaseHoldCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        readiness = await self._require_readiness(agency_id, readiness_id)
        hold = OfferDecisionExportReleaseHold(
            agency_id=agency_id,
            readiness_id=readiness_id,
            approval_id=readiness.get("approval_id"),
            preview_id=readiness["preview_id"],
            export_id=readiness["export_id"],
            decision_pack_id=readiness.get("decision_pack_id"),
            hold_type=data.get("hold_type") or "manual_review",
            severity=data.get("severity") or "medium",
            title=data["title"],
            reason=data["reason"],
            created_by=actor_from_user(user),
            hold_json=data.get("hold_json") or {},
        )
        stored = await self.db.collection(HOLD_COLLECTION).insert_one(hold.model_dump(mode="json"))
        updated_readiness = await self._refresh_readiness_hold_counts(agency_id, readiness_id)
        return {"readiness": updated_readiness or readiness, "hold": stored, **self._safety_flags()}

    async def release_hold(
        self,
        agency_id: str,
        readiness_id: str,
        hold_id: str,
        payload: OfferDecisionExportReleaseHoldReleaseRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        readiness = await self._require_readiness(agency_id, readiness_id)
        hold = await self.db.collection(HOLD_COLLECTION).find_one({"agency_id": agency_id, "readiness_id": readiness_id, "id": hold_id})
        if not hold:
            raise ValueError("Release hold not found.")
        released = await self.db.collection(HOLD_COLLECTION).update_one(
            {"agency_id": agency_id, "readiness_id": readiness_id, "id": hold_id},
            {
                "hold_status": OfferDecisionExportReleaseHoldStatus.RELEASED.value,
                "released_by": data.get("released_by") or actor_from_user(user),
                "released_at": now_utc(),
                "release_notes": data.get("release_notes"),
                "hold_json": {**(hold.get("hold_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        updated_readiness = await self._refresh_readiness_hold_counts(agency_id, readiness_id)
        return {"readiness": updated_readiness or readiness, "hold": released or hold, **self._safety_flags()}

    async def create_snapshot(
        self,
        agency_id: str,
        readiness_id: str,
        payload: OfferDecisionExportReleaseSnapshotCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        detail = await self.get_readiness_detail(readiness_id, agency_id)
        if not detail:
            raise ValueError("Release readiness record not found.")
        readiness = detail["readiness"]
        approval_detail = await self.get_approval_detail(readiness["approval_id"], agency_id) if readiness.get("approval_id") else None
        preview_bundle = await self._preview_bundle(agency_id, await self._require_preview(agency_id, readiness["preview_id"]))
        snapshot = OfferDecisionExportReleaseSnapshot(
            agency_id=agency_id,
            readiness_id=readiness_id,
            approval_id=readiness.get("approval_id"),
            preview_id=readiness["preview_id"],
            export_id=readiness["export_id"],
            decision_pack_id=readiness.get("decision_pack_id"),
            snapshot_name=data.get("snapshot_name") or f"Release readiness snapshot {readiness_id}",
            snapshot_json={
                "readiness": readiness,
                "approval_detail": approval_detail,
                "holds": detail["holds"],
                "source_counts": self._source_counts(preview_bundle),
                "safety_flags": self._safety_flags(),
                "metadata_json": data.get("metadata_json") or {},
            },
            saved_by=actor_from_user(user),
        )
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        updated_readiness = await self.db.collection(READINESS_COLLECTION).update_one(
            {"agency_id": agency_id, "id": readiness_id},
            {"snapshot_count": len(await self.list_snapshots(agency_id=agency_id, readiness_id=readiness_id))},
        )
        return {"readiness": updated_readiness or readiness, "snapshot": stored, **self._safety_flags()}

    async def list_checkpoints(
        self,
        *,
        agency_id: str | None = None,
        approval_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self._list_records(CHECKPOINT_COLLECTION, agency_id=agency_id, approval_id=approval_id, preview_id=preview_id, export_id=export_id)
        return sorted(items, key=lambda item: int(item.get("sequence_order") or 0))

    async def list_holds(
        self,
        *,
        agency_id: str | None = None,
        readiness_id: str | None = None,
        approval_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
        hold_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(HOLD_COLLECTION, agency_id=agency_id, readiness_id=readiness_id, approval_id=approval_id, preview_id=preview_id, export_id=export_id, hold_status=hold_status)

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        readiness_id: str | None = None,
        approval_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(SNAPSHOT_COLLECTION, agency_id=agency_id, readiness_id=readiness_id, approval_id=approval_id, preview_id=preview_id, export_id=export_id)

    async def _list_records(self, collection_name: str, **filters: Any) -> list[dict[str, Any]]:
        query = {key: value for key, value in filters.items() if value is not None}
        items = await self.db.collection(collection_name).find_many(query or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or item.get("prepared_at") or ""), reverse=True)

    async def _require_preview(self, agency_id: str, preview_id: str) -> dict[str, Any]:
        preview = await self.db.collection(PREVIEW_COLLECTION).find_one({"agency_id": agency_id, "id": preview_id})
        if not preview:
            raise ValueError("Offer decision export preview not found.")
        return preview

    async def _require_approval(self, agency_id: str, approval_id: str) -> dict[str, Any]:
        approval = await self.get_approval(approval_id, agency_id)
        if not approval:
            raise ValueError("Offer decision export approval not found.")
        return approval

    async def _require_readiness(self, agency_id: str, readiness_id: str) -> dict[str, Any]:
        readiness = await self.get_readiness(readiness_id, agency_id)
        if not readiness:
            raise ValueError("Release readiness record not found.")
        return readiness

    async def _preview_bundle(self, agency_id: str, preview: dict[str, Any]) -> dict[str, Any]:
        preview_filters = {"agency_id": agency_id, "preview_id": preview["id"]}
        export = await self.db.collection(EXPORT_COLLECTION).find_one({"agency_id": agency_id, "id": preview["export_id"]})
        return {
            "preview": preview,
            "export": export,
            "preview_sections": await self.db.collection(PREVIEW_SECTION_COLLECTION).find_many(preview_filters),
            "preview_blocks": await self.db.collection(PREVIEW_BLOCK_COLLECTION).find_many(preview_filters),
            "preview_validations": await self.db.collection(PREVIEW_VALIDATION_COLLECTION).find_many(preview_filters),
            "preview_snapshots": await self.db.collection(PREVIEW_SNAPSHOT_COLLECTION).find_many(preview_filters),
        }

    def _source_counts(self, bundle: dict[str, Any]) -> dict[str, int]:
        return {
            key: len(value)
            for key, value in bundle.items()
            if isinstance(value, list)
        }

    def _approval_summary(self, preview: dict[str, Any]) -> dict[str, Any]:
        return {
            "preview_id": preview["id"],
            "export_id": preview.get("export_id"),
            "decision_pack_id": preview.get("decision_pack_id"),
            "preview_status": preview.get("preview_status"),
            "section_count": preview.get("section_count", 0),
            "block_count": preview.get("block_count", 0),
            "validation_count": preview.get("validation_count", 0),
            "snapshot_count": preview.get("snapshot_count", 0),
            "metadata_only": True,
            "human_approval_required_enabled": True,
        }

    def _readiness_summary(self, preview: dict[str, Any], approval: dict[str, Any] | None, bundle: dict[str, Any]) -> dict[str, Any]:
        return {
            "preview_id": preview["id"],
            "export_id": preview.get("export_id"),
            "approval_id": approval.get("id") if approval else None,
            "approval_status": approval.get("approval_status") if approval else None,
            "preview_validation_count": len(bundle.get("preview_validations") or []),
            "preview_snapshot_count": len(bundle.get("preview_snapshots") or []),
            "ready_is_manual_metadata_only": True,
            "automatic_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
        }

    async def _refresh_readiness_hold_counts(self, agency_id: str, readiness_id: str) -> dict[str, Any] | None:
        readiness = await self._require_readiness(agency_id, readiness_id)
        holds = await self.list_holds(agency_id=agency_id, readiness_id=readiness_id)
        active_count = len([item for item in holds if item.get("hold_status") == OfferDecisionExportReleaseHoldStatus.ACTIVE.value])
        released_count = len([item for item in holds if item.get("hold_status") == OfferDecisionExportReleaseHoldStatus.RELEASED.value])
        approval = await self.get_approval(readiness["approval_id"], agency_id) if readiness.get("approval_id") else None
        approved = bool(approval and approval.get("approval_status") == OfferDecisionExportApprovalStatus.APPROVED.value)
        readiness_status = OfferDecisionExportReleaseReadinessStatus.BLOCKED.value if active_count else (
            OfferDecisionExportReleaseReadinessStatus.READY.value if approved else OfferDecisionExportReleaseReadinessStatus.DRAFT.value
        )
        return await self.db.collection(READINESS_COLLECTION).update_one(
            {"agency_id": agency_id, "id": readiness_id},
            {
                "active_hold_count": active_count,
                "released_hold_count": released_count,
                "readiness_status": readiness_status,
                "ready_for_manual_release": active_count == 0 and approved,
            },
        )

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "automatic_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_price_mutation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
        }
