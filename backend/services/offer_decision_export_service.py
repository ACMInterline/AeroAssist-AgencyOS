from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    OfferDecisionActorType,
    OfferDecisionExport,
    OfferDecisionExportArtifact,
    OfferDecisionExportArtifactType,
    OfferDecisionExportAuditEvent,
    OfferDecisionExportAuditEventType,
    OfferDecisionExportGenerateRequest,
    OfferDecisionExportRecipientDraft,
    OfferDecisionExportSection,
    now_utc,
)


PHASE_LABEL = "phase_37_5_offer_decision_export_foundation"

EXPORT_COLLECTION = "offer_decision_exports"
SECTION_COLLECTION = "offer_decision_export_sections"
ARTIFACT_COLLECTION = "offer_decision_export_artifacts"
RECIPIENT_DRAFT_COLLECTION = "offer_decision_export_recipient_drafts"
AUDIT_EVENT_COLLECTION = "offer_decision_export_audit_events"

PACK_COLLECTION = "offer_decision_packs"
PACK_OPTION_COLLECTION = "offer_decision_pack_options"
PACK_EVIDENCE_COLLECTION = "offer_decision_pack_evidence"
PACK_WARNING_COLLECTION = "offer_decision_pack_warnings"
PACK_REVIEW_NOTE_COLLECTION = "offer_decision_pack_review_notes"
PACK_SNAPSHOT_COLLECTION = "offer_decision_pack_snapshots"
EXPLANATION_COLLECTION = "offer_decision_explanations"
TIMELINE_COLLECTION = "offer_decision_timeline_events"
EVIDENCE_REFERENCE_COLLECTION = "offer_decision_evidence_references"
REASON_COLLECTION = "offer_decision_reasons"
ACKNOWLEDGEMENT_COLLECTION = "offer_decision_acknowledgements"
AUDIT_SNAPSHOT_COLLECTION = "offer_decision_audit_snapshots"


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


def safe_filename(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "offer-decision-export"


class OfferDecisionExportService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "export_count": len(await self.list_exports(agency_id=agency_id)),
            "section_count": len(await self.list_sections(agency_id=agency_id)),
            "artifact_count": len(await self.list_artifacts(agency_id=agency_id)),
            "recipient_draft_count": len(await self.list_recipient_drafts(agency_id=agency_id)),
            "audit_event_count": len(await self.list_audit_events(agency_id=agency_id)),
            "decision_exports_enabled": True,
            "export_sections_enabled": True,
            "export_artifacts_enabled": True,
            "recipient_drafts_enabled": True,
            "export_audit_events_enabled": True,
            "pdf_export_metadata_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Offer decision exports are metadata-only review snapshots. They do not generate public links, send emails, mutate offers/prices, recommend airlines, book, issue, charge, invoice, settle, or execute providers.",
        }

    async def list_exports(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(EXPORT_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def get_export(self, export_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": export_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(EXPORT_COLLECTION).find_one(filters)

    async def get_export_detail(self, export_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        export = await self.get_export(export_id, agency_id)
        if not export:
            return None
        return {
            "export": export,
            "sections": await self.list_sections(agency_id=agency_id, export_id=export_id),
            "artifacts": await self.list_artifacts(agency_id=agency_id, export_id=export_id),
            "recipient_drafts": await self.list_recipient_drafts(agency_id=agency_id, export_id=export_id),
            "audit_events": await self.list_audit_events(agency_id=agency_id, export_id=export_id),
            **self._safety_flags(),
        }

    async def generate_export(self, agency_id: str, payload: OfferDecisionExportGenerateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        pack = await self._require_pack(agency_id, data["decision_pack_id"])
        bundle = await self._source_bundle(agency_id, pack)
        export_name = data.get("export_name") or f"Offer decision review export {pack.get('pack_name') or pack['id']}"
        export = OfferDecisionExport(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            export_name=export_name,
            generated_by=actor_from_user(user),
            export_summary_json=self._export_summary(pack, bundle),
            source_counts_json=self._source_counts(bundle),
            metadata_json=data.get("metadata_json") or {},
        )
        stored_export = await self.db.collection(EXPORT_COLLECTION).insert_one(export.model_dump(mode="json"))

        sections = []
        for index, section in enumerate(self._section_specs(bundle), start=1):
            record = OfferDecisionExportSection(
                agency_id=agency_id,
                export_id=stored_export["id"],
                decision_pack_id=pack["id"],
                offer_workspace_id=pack["offer_workspace_id"],
                section_key=section["section_key"],
                section_title=section["section_title"],
                section_order=index,
                record_count=section["record_count"],
                section_json=section["section_json"],
            )
            sections.append(await self.db.collection(SECTION_COLLECTION).insert_one(record.model_dump(mode="json")))

        artifacts = await self._create_artifacts(agency_id, stored_export, pack, sections, bundle)
        recipient_drafts = []
        if data.get("include_recipient_draft"):
            recipient_drafts.append(await self._create_recipient_draft(agency_id, stored_export, pack, data, user))

        updated_export = await self.db.collection(EXPORT_COLLECTION).update_one(
            {"agency_id": agency_id, "id": stored_export["id"]},
            {
                "section_count": len(sections),
                "artifact_count": len(artifacts),
                "recipient_draft_count": len(recipient_drafts),
            },
        )
        export_for_audit = updated_export or stored_export
        generated_event = await self._record_audit_event(
            export_for_audit,
            {
                "event_type": OfferDecisionExportAuditEventType.GENERATED.value,
                "actor": actor_from_user(user),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": "Offer decision export generated as metadata-only review snapshot.",
                "event_json": {"section_count": len(sections), "artifact_count": len(artifacts), "recipient_draft_count": len(recipient_drafts)},
            },
        )
        audit_events = await self.list_audit_events(agency_id=agency_id, export_id=stored_export["id"])
        if generated_event["id"] not in {item["id"] for item in audit_events}:
            audit_events.append(generated_event)
        return {
            "export": updated_export or stored_export,
            "sections": sections,
            "artifacts": artifacts,
            "recipient_drafts": recipient_drafts,
            "audit_events": audit_events,
            **self._safety_flags(),
        }

    async def list_sections(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self._list_records(SECTION_COLLECTION, agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)
        return sorted(items, key=lambda item: int(item.get("section_order") or 0))

    async def list_artifacts(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(ARTIFACT_COLLECTION, agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def list_recipient_drafts(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(RECIPIENT_DRAFT_COLLECTION, agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def list_audit_events(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(AUDIT_EVENT_COLLECTION, agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def _list_records(
        self,
        collection_name: str,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if export_id:
            filters["export_id"] = export_id
        if decision_pack_id:
            filters["decision_pack_id"] = decision_pack_id
        if offer_workspace_id:
            filters["offer_workspace_id"] = offer_workspace_id
        items = await self.db.collection(collection_name).find_many(filters or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or item.get("generated_at") or ""), reverse=True)

    async def _require_pack(self, agency_id: str, decision_pack_id: str) -> dict[str, Any]:
        pack = await self.db.collection(PACK_COLLECTION).find_one({"agency_id": agency_id, "id": decision_pack_id})
        if not pack:
            raise ValueError("Offer decision pack not found.")
        return pack

    async def _source_bundle(self, agency_id: str, pack: dict[str, Any]) -> dict[str, Any]:
        filters = {"agency_id": agency_id, "decision_pack_id": pack["id"]}
        return {
            "decision_pack": pack,
            "options": await self.db.collection(PACK_OPTION_COLLECTION).find_many(filters),
            "evidence": await self.db.collection(PACK_EVIDENCE_COLLECTION).find_many(filters),
            "warnings": await self.db.collection(PACK_WARNING_COLLECTION).find_many(filters),
            "review_notes": await self.db.collection(PACK_REVIEW_NOTE_COLLECTION).find_many(filters),
            "decision_pack_snapshots": await self.db.collection(PACK_SNAPSHOT_COLLECTION).find_many(filters),
            "explanations": await self.db.collection(EXPLANATION_COLLECTION).find_many(filters),
            "timeline": await self.db.collection(TIMELINE_COLLECTION).find_many(filters),
            "evidence_references": await self.db.collection(EVIDENCE_REFERENCE_COLLECTION).find_many(filters),
            "reasons": await self.db.collection(REASON_COLLECTION).find_many(filters),
            "acknowledgements": await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).find_many(filters),
            "audit_snapshots": await self.db.collection(AUDIT_SNAPSHOT_COLLECTION).find_many(filters),
        }

    def _source_counts(self, bundle: dict[str, Any]) -> dict[str, int]:
        return {
            key: len(value)
            for key, value in bundle.items()
            if isinstance(value, list)
        }

    def _export_summary(self, pack: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
        counts = self._source_counts(bundle)
        return {
            "decision_pack_id": pack["id"],
            "offer_workspace_id": pack.get("offer_workspace_id"),
            "pack_name": pack.get("pack_name"),
            "warning_level": pack.get("warning_level"),
            "option_count": counts.get("options", 0),
            "evidence_count": counts.get("evidence", 0) + counts.get("evidence_references", 0),
            "explanation_count": counts.get("explanations", 0),
            "timeline_event_count": counts.get("timeline", 0),
            "metadata_only": True,
            "public_links_disabled": True,
            "automatic_sending_disabled": True,
        }

    def _section_specs(self, bundle: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            self._section("decision_pack", "Decision pack summary", {"pack": bundle["decision_pack"]}),
            self._section("options", "Decision pack options", {"items": bundle["options"]}),
            self._section("evidence", "Evidence and references", {"items": bundle["evidence"], "references": bundle["evidence_references"]}),
            self._section("warnings", "Warnings", {"items": bundle["warnings"]}),
            self._section("review_notes", "Review notes", {"items": bundle["review_notes"]}),
            self._section("explanations", "Decision explanations", {"items": bundle["explanations"]}),
            self._section("timeline", "Decision timeline", {"items": bundle["timeline"]}),
            self._section("reasons", "Decision reasons", {"items": bundle["reasons"]}),
            self._section("acknowledgements", "Acknowledgements", {"items": bundle["acknowledgements"]}),
            self._section("audit_snapshots", "Audit snapshots", {"decision_pack_snapshots": bundle["decision_pack_snapshots"], "explanation_audit_snapshots": bundle["audit_snapshots"]}),
        ]

    def _section(self, section_key: str, title: str, section_json: dict[str, Any]) -> dict[str, Any]:
        count = 0
        for value in section_json.values():
            if isinstance(value, list):
                count += len(value)
            elif isinstance(value, dict) and value:
                count += 1
        return {
            "section_key": section_key,
            "section_title": title,
            "record_count": count,
            "section_json": section_json,
        }

    async def _create_artifacts(
        self,
        agency_id: str,
        export: dict[str, Any],
        pack: dict[str, Any],
        sections: list[dict[str, Any]],
        bundle: dict[str, Any],
    ) -> list[dict[str, Any]]:
        filename_base = safe_filename(export.get("export_name") or pack.get("pack_name") or export["id"])
        pdf_artifact = OfferDecisionExportArtifact(
            agency_id=agency_id,
            export_id=export["id"],
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            artifact_type=OfferDecisionExportArtifactType.PDF_METADATA,
            artifact_name="PDF review export metadata",
            filename=f"{filename_base}.pdf",
            mime_type="application/pdf",
            artifact_json={
                "pdf_export_metadata_enabled": True,
                "file_generated": False,
                "rendering_required": False,
                "section_outline": [{"section_key": item.get("section_key"), "section_title": item.get("section_title"), "record_count": item.get("record_count")} for item in sections],
                "source_counts": self._source_counts(bundle),
            },
        )
        json_artifact = OfferDecisionExportArtifact(
            agency_id=agency_id,
            export_id=export["id"],
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            artifact_type=OfferDecisionExportArtifactType.REVIEW_JSON_SNAPSHOT,
            artifact_name="Review package JSON snapshot",
            filename=f"{filename_base}.json",
            mime_type="application/json",
            artifact_json={
                "export": export,
                "sections": sections,
                "source_counts": self._source_counts(bundle),
                "metadata_only": True,
            },
        )
        return [
            await self.db.collection(ARTIFACT_COLLECTION).insert_one(pdf_artifact.model_dump(mode="json")),
            await self.db.collection(ARTIFACT_COLLECTION).insert_one(json_artifact.model_dump(mode="json")),
        ]

    async def _create_recipient_draft(self, agency_id: str, export: dict[str, Any], pack: dict[str, Any], data: dict[str, Any], user: dict | None) -> dict[str, Any]:
        draft = OfferDecisionExportRecipientDraft(
            agency_id=agency_id,
            export_id=export["id"],
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            recipient_type=enum_value(data.get("recipient_type")) or "internal",
            recipient_name=data.get("recipient_name"),
            recipient_email=data.get("recipient_email"),
            subject=data.get("subject") or f"Draft review export: {export.get('export_name')}",
            message_body=data.get("message_body") or "Draft only. No automatic sending or public link was created.",
            metadata_json={"created_by": actor_from_user(user), **(data.get("metadata_json") or {})},
        )
        stored = await self.db.collection(RECIPIENT_DRAFT_COLLECTION).insert_one(draft.model_dump(mode="json"))
        await self._record_audit_event(
            export,
            {
                "event_type": OfferDecisionExportAuditEventType.RECIPIENT_DRAFT_CREATED.value,
                "actor": actor_from_user(user),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": "Offer decision export recipient draft created without sending.",
                "event_json": {"recipient_draft_id": stored["id"], "automatic_sending_disabled": True, "public_links_disabled": True},
            },
        )
        return stored

    async def _record_audit_event(self, export: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        event = OfferDecisionExportAuditEvent(
            agency_id=export["agency_id"],
            export_id=export["id"],
            decision_pack_id=export["decision_pack_id"],
            offer_workspace_id=export["offer_workspace_id"],
            event_type=enum_value(data.get("event_type")) or OfferDecisionExportAuditEventType.GENERATED.value,
            actor=data.get("actor"),
            actor_type=enum_value(data.get("actor_type")) or OfferDecisionActorType.SYSTEM.value,
            description=data["description"],
            event_json=data.get("event_json") or {},
        )
        return await self.db.collection(AUDIT_EVENT_COLLECTION).insert_one(event.model_dump(mode="json"))

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "automatic_sending_disabled": True,
            "public_links_disabled": True,
            "offer_price_mutation_disabled": True,
            "auto_recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
        }
