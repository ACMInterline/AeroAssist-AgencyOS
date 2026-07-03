from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionExportDeliveryAttachment,
    OfferDecisionExportDeliveryAttachmentCreateRequest,
    OfferDecisionExportDeliveryHandoff,
    OfferDecisionExportDeliveryHandoffCreateRequest,
    OfferDecisionExportDeliveryHandoffStatusUpdateRequest,
    OfferDecisionExportDeliveryInstruction,
    OfferDecisionExportDeliveryInstructionCompletionRequest,
    OfferDecisionExportDeliveryInstructionCreateRequest,
    OfferDecisionExportDeliveryRecipient,
    OfferDecisionExportDeliveryRecipientCreateRequest,
    OfferDecisionExportDeliveryRecipientStatusUpdateRequest,
    OfferDecisionExportDeliverySnapshot,
    OfferDecisionExportDeliverySnapshotCreateRequest,
    now_utc,
)


PHASE_LABEL = "phase_37_8_offer_decision_export_manual_delivery_handoff_foundation"

HANDOFF_COLLECTION = "offer_decision_export_delivery_handoffs"
RECIPIENT_COLLECTION = "offer_decision_export_delivery_recipients"
ATTACHMENT_COLLECTION = "offer_decision_export_delivery_attachments"
INSTRUCTION_COLLECTION = "offer_decision_export_delivery_instructions"
SNAPSHOT_COLLECTION = "offer_decision_export_delivery_snapshots"

EXPORT_COLLECTION = "offer_decision_exports"
PREVIEW_COLLECTION = "offer_decision_export_previews"
APPROVAL_COLLECTION = "offer_decision_export_approvals"
READINESS_COLLECTION = "offer_decision_export_release_readiness"
ARTIFACT_COLLECTION = "offer_decision_export_artifacts"


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


class OfferDecisionExportDeliveryService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "handoff_count": len(await self.list_handoffs(agency_id=agency_id)),
            "recipient_count": len(await self.list_recipients(agency_id=agency_id)),
            "attachment_count": len(await self.list_attachments(agency_id=agency_id)),
            "instruction_count": len(await self.list_instructions(agency_id=agency_id)),
            "snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "delivery_handoffs_enabled": True,
            "delivery_recipients_enabled": True,
            "delivery_attachment_metadata_enabled": True,
            "delivery_instructions_enabled": True,
            "immutable_delivery_snapshots_enabled": True,
            "agency_delivery_handoff_ui_enabled": True,
            "platform_delivery_handoff_ui_enabled": True,
            "manual_delivery_only_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 37.8 manual delivery handoff is metadata-only. It records human handoff intent, recipient metadata, attachment metadata, instructions, and immutable snapshots; it never sends email or SMS, creates public links, delivers real PDFs, mutates offers/prices, recommends airlines, books, issues tickets or EMDs, charges, invoices, settles, scrapes, calls external AI, or executes providers.",
        }

    async def create_handoff(
        self,
        agency_id: str,
        payload: OfferDecisionExportDeliveryHandoffCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        export = await self._require_export(agency_id, data["export_id"])
        preview = await self._require_optional(PREVIEW_COLLECTION, agency_id, data.get("preview_id"), "Offer decision export preview not found.")
        approval = await self._require_optional(APPROVAL_COLLECTION, agency_id, data.get("approval_id"), "Offer decision export approval not found.")
        readiness = await self._require_optional(READINESS_COLLECTION, agency_id, data.get("release_readiness_id"), "Release readiness record not found.")
        self._assert_links(export, preview, approval, readiness)
        handoff = OfferDecisionExportDeliveryHandoff(
            agency_id=agency_id,
            export_id=export["id"],
            preview_id=preview.get("id") if preview else None,
            approval_id=approval.get("id") if approval else None,
            release_readiness_id=readiness.get("id") if readiness else None,
            title=data.get("title") or f"Manual delivery handoff for export {export['id']}",
            delivery_method=data.get("delivery_method") or "manual_email",
            safety_summary=self._safety_summary(export, preview, approval, readiness),
            created_by=actor_from_user(user),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(HANDOFF_COLLECTION).insert_one(handoff.model_dump(mode="json"))
        return {"handoff": stored, **self._safety_flags()}

    async def list_handoffs(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        preview_id: str | None = None,
        release_readiness_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(HANDOFF_COLLECTION, agency_id=agency_id, export_id=export_id, preview_id=preview_id, release_readiness_id=release_readiness_id, status=status)

    async def get_handoff(self, handoff_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": handoff_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(HANDOFF_COLLECTION).find_one(filters)

    async def get_handoff_detail(self, handoff_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        handoff = await self.get_handoff(handoff_id, agency_id)
        if not handoff:
            return None
        return {
            "handoff": handoff,
            "recipients": await self.list_recipients(agency_id=agency_id, handoff_id=handoff_id),
            "attachments": await self.list_attachments(agency_id=agency_id, handoff_id=handoff_id),
            "instructions": await self.list_instructions(agency_id=agency_id, handoff_id=handoff_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, handoff_id=handoff_id),
            **self._safety_flags(),
        }

    async def update_handoff_status(
        self,
        agency_id: str,
        handoff_id: str,
        payload: OfferDecisionExportDeliveryHandoffStatusUpdateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        handoff = await self._require_handoff(agency_id, handoff_id)
        updated = await self.db.collection(HANDOFF_COLLECTION).update_one(
            {"agency_id": agency_id, "id": handoff_id},
            {
                "status": enum_value(data["status"]),
                "status_reason": data.get("status_reason"),
                "metadata_json": {**(handoff.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        return {"handoff": updated or handoff, **self._safety_flags()}

    async def add_recipient(
        self,
        agency_id: str,
        handoff_id: str,
        payload: OfferDecisionExportDeliveryRecipientCreateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_handoff(agency_id, handoff_id)
        recipient = OfferDecisionExportDeliveryRecipient(
            agency_id=agency_id,
            handoff_id=handoff_id,
            recipient_type=data.get("recipient_type") or "client",
            display_name=data["display_name"],
            email_metadata=data.get("email_metadata"),
            phone_metadata=data.get("phone_metadata"),
            delivery_method=data.get("delivery_method") or "manual_email",
            notes=data.get("notes"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(RECIPIENT_COLLECTION).insert_one(recipient.model_dump(mode="json"))
        handoff = await self._refresh_handoff_counts(agency_id, handoff_id)
        return {"handoff": handoff, "recipient": stored, **self._safety_flags()}

    async def list_recipients(
        self,
        *,
        agency_id: str | None = None,
        handoff_id: str | None = None,
        delivery_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(RECIPIENT_COLLECTION, agency_id=agency_id, handoff_id=handoff_id, delivery_status=delivery_status)

    async def update_recipient_status(
        self,
        agency_id: str,
        recipient_id: str,
        payload: OfferDecisionExportDeliveryRecipientStatusUpdateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        recipient = await self._require_record(RECIPIENT_COLLECTION, agency_id, recipient_id, "Delivery recipient metadata not found.")
        updated = await self.db.collection(RECIPIENT_COLLECTION).update_one(
            {"agency_id": agency_id, "id": recipient_id},
            {
                "delivery_status": enum_value(data["delivery_status"]),
                "notes": data.get("notes", recipient.get("notes")),
                "metadata_json": {**(recipient.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        return {"recipient": updated or recipient, **self._safety_flags()}

    async def add_attachment_metadata(
        self,
        agency_id: str,
        handoff_id: str,
        payload: OfferDecisionExportDeliveryAttachmentCreateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        handoff = await self._require_handoff(agency_id, handoff_id)
        if data.get("artifact_id"):
            artifact = await self._require_record(ARTIFACT_COLLECTION, agency_id, data["artifact_id"], "Offer decision export artifact metadata not found.")
            if artifact.get("export_id") != handoff.get("export_id"):
                raise ValueError("Artifact metadata does not belong to handoff export.")
        if data.get("preview_id"):
            preview = await self._require_record(PREVIEW_COLLECTION, agency_id, data["preview_id"], "Offer decision export preview not found.")
            if preview.get("export_id") != handoff.get("export_id"):
                raise ValueError("Preview metadata does not belong to handoff export.")
        attachment = OfferDecisionExportDeliveryAttachment(
            agency_id=agency_id,
            handoff_id=handoff_id,
            artifact_id=data.get("artifact_id"),
            preview_id=data.get("preview_id"),
            filename=data["filename"],
            file_type=data.get("file_type") or "pdf_metadata",
            source_type=data.get("source_type") or "manually_described_metadata",
            size_label=data.get("size_label"),
            storage_reference_metadata=data.get("storage_reference_metadata"),
            public_link_created=False,
            real_file_delivered=False,
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(ATTACHMENT_COLLECTION).insert_one(attachment.model_dump(mode="json"))
        refreshed = await self._refresh_handoff_counts(agency_id, handoff_id)
        return {"handoff": refreshed, "attachment": stored, **self._safety_flags()}

    async def list_attachments(
        self,
        *,
        agency_id: str | None = None,
        handoff_id: str | None = None,
        artifact_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(ATTACHMENT_COLLECTION, agency_id=agency_id, handoff_id=handoff_id, artifact_id=artifact_id)

    async def add_instruction(
        self,
        agency_id: str,
        handoff_id: str,
        payload: OfferDecisionExportDeliveryInstructionCreateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_handoff(agency_id, handoff_id)
        instruction = OfferDecisionExportDeliveryInstruction(
            agency_id=agency_id,
            handoff_id=handoff_id,
            instruction_type=data.get("instruction_type") or "internal_note",
            title=data["title"],
            body=data["body"],
            required=data.get("required", True),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(INSTRUCTION_COLLECTION).insert_one(instruction.model_dump(mode="json"))
        handoff = await self._refresh_handoff_counts(agency_id, handoff_id)
        return {"handoff": handoff, "instruction": stored, **self._safety_flags()}

    async def list_instructions(
        self,
        *,
        agency_id: str | None = None,
        handoff_id: str | None = None,
        completed: bool | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(INSTRUCTION_COLLECTION, agency_id=agency_id, handoff_id=handoff_id, completed=completed)

    async def update_instruction_completion(
        self,
        agency_id: str,
        instruction_id: str,
        payload: OfferDecisionExportDeliveryInstructionCompletionRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        instruction = await self._require_record(INSTRUCTION_COLLECTION, agency_id, instruction_id, "Delivery instruction not found.")
        completed = bool(data.get("completed", True))
        completed_by = data.get("completed_by") or actor_from_user(user)
        updated = await self.db.collection(INSTRUCTION_COLLECTION).update_one(
            {"agency_id": agency_id, "id": instruction_id},
            {
                "completed": completed,
                "completed_by": completed_by if completed else None,
                "completed_at": now_utc() if completed else None,
                "metadata_json": {**(instruction.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        return {"instruction": updated or instruction, **self._safety_flags()}

    async def create_snapshot(
        self,
        agency_id: str,
        handoff_id: str,
        payload: OfferDecisionExportDeliverySnapshotCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        detail = await self.get_handoff_detail(handoff_id, agency_id)
        if not detail:
            raise ValueError("Delivery handoff metadata not found.")
        snapshot = OfferDecisionExportDeliverySnapshot(
            agency_id=agency_id,
            handoff_id=handoff_id,
            snapshot_type=data.get("snapshot_type") or "prepared",
            payload={
                "handoff": detail["handoff"],
                "recipients": detail["recipients"],
                "attachments": detail["attachments"],
                "instructions": detail["instructions"],
                "safety_flags": self._safety_flags(),
                "metadata_json": data.get("metadata_json") or {},
            },
            created_by=data.get("created_by") or actor_from_user(user),
        )
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        handoff = await self._refresh_handoff_counts(agency_id, handoff_id)
        return {"handoff": handoff, "snapshot": stored, **self._safety_flags()}

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        handoff_id: str | None = None,
        snapshot_type: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(SNAPSHOT_COLLECTION, agency_id=agency_id, handoff_id=handoff_id, snapshot_type=snapshot_type)

    async def _list_records(self, collection_name: str, **filters: Any) -> list[dict[str, Any]]:
        query = {key: value for key, value in filters.items() if value is not None}
        items = await self.db.collection(collection_name).find_many(query or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _require_record(self, collection_name: str, agency_id: str, record_id: str, message: str) -> dict[str, Any]:
        record = await self.db.collection(collection_name).find_one({"agency_id": agency_id, "id": record_id})
        if not record:
            raise ValueError(message)
        return record

    async def _require_optional(self, collection_name: str, agency_id: str, record_id: str | None, message: str) -> dict[str, Any] | None:
        if not record_id:
            return None
        return await self._require_record(collection_name, agency_id, record_id, message)

    async def _require_export(self, agency_id: str, export_id: str) -> dict[str, Any]:
        return await self._require_record(EXPORT_COLLECTION, agency_id, export_id, "Offer decision export not found.")

    async def _require_handoff(self, agency_id: str, handoff_id: str) -> dict[str, Any]:
        return await self._require_record(HANDOFF_COLLECTION, agency_id, handoff_id, "Delivery handoff metadata not found.")

    def _assert_links(
        self,
        export: dict[str, Any],
        preview: dict[str, Any] | None,
        approval: dict[str, Any] | None,
        readiness: dict[str, Any] | None,
    ) -> None:
        export_id = export["id"]
        for label, record in [("Preview", preview), ("Approval", approval), ("Release readiness", readiness)]:
            if record and record.get("export_id") != export_id:
                raise ValueError(f"{label} does not belong to export.")
        if approval and preview and approval.get("preview_id") != preview.get("id"):
            raise ValueError("Approval does not belong to preview.")
        if readiness and preview and readiness.get("preview_id") != preview.get("id"):
            raise ValueError("Release readiness does not belong to preview.")
        if readiness and approval and readiness.get("approval_id") != approval.get("id"):
            raise ValueError("Release readiness does not belong to approval.")

    async def _refresh_handoff_counts(self, agency_id: str, handoff_id: str) -> dict[str, Any] | None:
        recipients = await self.list_recipients(agency_id=agency_id, handoff_id=handoff_id)
        attachments = await self.list_attachments(agency_id=agency_id, handoff_id=handoff_id)
        instructions = await self.list_instructions(agency_id=agency_id, handoff_id=handoff_id)
        snapshots = await self.list_snapshots(agency_id=agency_id, handoff_id=handoff_id)
        return await self.db.collection(HANDOFF_COLLECTION).update_one(
            {"agency_id": agency_id, "id": handoff_id},
            {
                "recipient_count": len(recipients),
                "attachment_count": len(attachments),
                "instruction_count": len(instructions),
                "checklist_count": len([item for item in instructions if item.get("required") is True]),
                "snapshot_count": len(snapshots),
            },
        )

    def _safety_summary(
        self,
        export: dict[str, Any],
        preview: dict[str, Any] | None,
        approval: dict[str, Any] | None,
        readiness: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "export_id": export.get("id"),
            "preview_id": preview.get("id") if preview else None,
            "approval_id": approval.get("id") if approval else None,
            "release_readiness_id": readiness.get("id") if readiness else None,
            "export_status": export.get("export_status"),
            "preview_status": preview.get("preview_status") if preview else None,
            "approval_status": approval.get("approval_status") if approval else None,
            "readiness_status": readiness.get("readiness_status") if readiness else None,
            "manual_delivery_only_enabled": True,
            **self._safety_flags(),
        }

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "manual_delivery_only_enabled": True,
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
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
