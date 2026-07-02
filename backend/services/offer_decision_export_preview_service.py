from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionExportPreview,
    OfferDecisionExportPreviewBlock,
    OfferDecisionExportPreviewBlockType,
    OfferDecisionExportPreviewGenerateRequest,
    OfferDecisionExportPreviewSection,
    OfferDecisionExportPreviewSectionKey,
    OfferDecisionExportPreviewSnapshot,
    OfferDecisionExportPreviewSnapshotCreate,
    OfferDecisionExportPreviewStatus,
    OfferDecisionExportPreviewValidateRequest,
    OfferDecisionExportPreviewValidation,
    OfferDecisionExportPreviewValidationKey,
    OfferDecisionExportPreviewValidationStatus,
    now_utc,
)


PHASE_LABEL = "phase_37_6_offer_decision_export_preview_foundation"

PREVIEW_COLLECTION = "offer_decision_export_previews"
PREVIEW_SECTION_COLLECTION = "offer_decision_export_preview_sections"
PREVIEW_BLOCK_COLLECTION = "offer_decision_export_preview_blocks"
PREVIEW_VALIDATION_COLLECTION = "offer_decision_export_preview_validations"
PREVIEW_SNAPSHOT_COLLECTION = "offer_decision_export_preview_snapshots"

EXPORT_COLLECTION = "offer_decision_exports"
EXPORT_SECTION_COLLECTION = "offer_decision_export_sections"
EXPORT_ARTIFACT_COLLECTION = "offer_decision_export_artifacts"
EXPORT_RECIPIENT_DRAFT_COLLECTION = "offer_decision_export_recipient_drafts"
EXPORT_AUDIT_EVENT_COLLECTION = "offer_decision_export_audit_events"
PACK_COLLECTION = "offer_decision_packs"
EXPLANATION_COLLECTION = "offer_decision_explanations"
TIMELINE_COLLECTION = "offer_decision_timeline_events"
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


class OfferDecisionExportPreviewService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "preview_count": len(await self.list_previews(agency_id=agency_id)),
            "section_count": len(await self.list_sections(agency_id=agency_id)),
            "block_count": len(await self.list_blocks(agency_id=agency_id)),
            "validation_count": len(await self.list_validations(agency_id=agency_id)),
            "snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "export_previews_enabled": True,
            "preview_sections_enabled": True,
            "preview_blocks_enabled": True,
            "preview_validations_enabled": True,
            "immutable_preview_snapshots_enabled": True,
            "agency_export_preview_ui_enabled": True,
            "platform_export_preview_ui_enabled": True,
            "metadata_only_rendering_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Offer decision export previews are metadata-only render previews. They do not generate files, send messages, create public links, mutate offers/prices, recommend airlines, book, issue, charge, invoice, settle, or execute providers.",
        }

    async def list_previews(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(PREVIEW_COLLECTION, agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id)

    async def get_preview(self, preview_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": preview_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(PREVIEW_COLLECTION).find_one(filters)

    async def get_preview_detail(self, preview_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        preview = await self.get_preview(preview_id, agency_id)
        if not preview:
            return None
        return {
            "preview": preview,
            "sections": await self.list_sections(agency_id=agency_id, preview_id=preview_id),
            "blocks": await self.list_blocks(agency_id=agency_id, preview_id=preview_id),
            "validations": await self.list_validations(agency_id=agency_id, preview_id=preview_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, preview_id=preview_id),
            **self._safety_flags(),
        }

    async def generate_preview(
        self,
        agency_id: str,
        payload: OfferDecisionExportPreviewGenerateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        export = await self._require_export(agency_id, data["export_id"])
        bundle = await self._source_bundle(agency_id, export, data.get("source_artifact_ids") or [])
        source_artifact_ids = [item["id"] for item in bundle["artifacts"]]
        first_explanation = next(iter(bundle["explanations"]), None)
        preview = OfferDecisionExportPreview(
            agency_id=agency_id,
            export_id=export["id"],
            decision_pack_id=export.get("decision_pack_id"),
            explanation_id=first_explanation.get("id") if first_explanation else None,
            offer_workspace_id=export.get("offer_workspace_id"),
            source_artifact_ids=source_artifact_ids,
            render_profile=data.get("render_profile") or "internal_review",
            template_profile=data.get("template_profile") or "metadata_preview",
            generated_by=actor_from_user(user),
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=now_utc() if data.get("reviewed_by") else None,
            preview_summary_json=self._preview_summary(export, bundle),
            source_counts_json=self._source_counts(bundle),
            metadata_json=data.get("metadata_json") or {},
        )
        stored_preview = await self.db.collection(PREVIEW_COLLECTION).insert_one(preview.model_dump(mode="json"))

        sections: list[dict[str, Any]] = []
        blocks: list[dict[str, Any]] = []
        for section_index, section_spec in enumerate(self._section_specs(export, bundle), start=1):
            section = OfferDecisionExportPreviewSection(
                agency_id=agency_id,
                preview_id=stored_preview["id"],
                export_id=export["id"],
                decision_pack_id=export.get("decision_pack_id"),
                section_key=section_spec["section_key"],
                section_title=section_spec["section_title"],
                section_order=section_index,
                section_json=section_spec["section_json"],
            )
            stored_section = await self.db.collection(PREVIEW_SECTION_COLLECTION).insert_one(section.model_dump(mode="json"))
            section_blocks: list[dict[str, Any]] = []
            for block_index, block_spec in enumerate(self._block_specs(section_spec, export, bundle), start=1):
                block = OfferDecisionExportPreviewBlock(
                    agency_id=agency_id,
                    preview_id=stored_preview["id"],
                    section_id=stored_section["id"],
                    export_id=export["id"],
                    decision_pack_id=export.get("decision_pack_id"),
                    section_key=section_spec["section_key"],
                    block_type=block_spec["block_type"],
                    block_title=block_spec.get("block_title"),
                    block_order=block_index,
                    block_json=block_spec["block_json"],
                    source_record_type=block_spec.get("source_record_type"),
                    source_record_id=block_spec.get("source_record_id"),
                )
                section_blocks.append(await self.db.collection(PREVIEW_BLOCK_COLLECTION).insert_one(block.model_dump(mode="json")))
            blocks.extend(section_blocks)
            updated_section = await self.db.collection(PREVIEW_SECTION_COLLECTION).update_one(
                {"agency_id": agency_id, "id": stored_section["id"]},
                {"block_count": len(section_blocks)},
            )
            sections.append(updated_section or stored_section)

        updated_preview = await self.db.collection(PREVIEW_COLLECTION).update_one(
            {"agency_id": agency_id, "id": stored_preview["id"]},
            {"section_count": len(sections), "block_count": len(blocks)},
        )
        return {
            "preview": updated_preview or stored_preview,
            "sections": sections,
            "blocks": blocks,
            **self._safety_flags(),
        }

    async def validate_preview(
        self,
        agency_id: str,
        preview_id: str,
        payload: OfferDecisionExportPreviewValidateRequest | dict[str, Any] | None = None,
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload or {})
        preview = await self._require_preview(agency_id, preview_id)
        export = await self._require_export(agency_id, preview["export_id"])
        bundle = await self._source_bundle(agency_id, export, preview.get("source_artifact_ids") or [])
        internal_reviewer = data.get("internal_reviewer") or preview.get("reviewed_by")
        validations = []
        for spec in self._validation_specs(preview, bundle, internal_reviewer):
            validation = OfferDecisionExportPreviewValidation(
                agency_id=agency_id,
                preview_id=preview_id,
                export_id=preview["export_id"],
                decision_pack_id=preview.get("decision_pack_id"),
                validation_key=spec["validation_key"],
                validation_status=spec["validation_status"],
                severity=spec["severity"],
                message=spec["message"],
                checked_by=actor_from_user(user),
                validation_json={**spec["validation_json"], "metadata_json": data.get("metadata_json") or {}},
            )
            validations.append(await self.db.collection(PREVIEW_VALIDATION_COLLECTION).insert_one(validation.model_dump(mode="json")))

        updates: dict[str, Any] = {
            "preview_status": OfferDecisionExportPreviewStatus.VALIDATED.value,
            "validation_count": len(await self.list_validations(agency_id=agency_id, preview_id=preview_id)),
        }
        if internal_reviewer and internal_reviewer != preview.get("reviewed_by"):
            updates["reviewed_by"] = internal_reviewer
            updates["reviewed_at"] = now_utc()
        updated_preview = await self.db.collection(PREVIEW_COLLECTION).update_one({"agency_id": agency_id, "id": preview_id}, updates)
        return {
            "preview": updated_preview or preview,
            "validations": validations,
            **self._safety_flags(),
        }

    async def save_snapshot(
        self,
        agency_id: str,
        preview_id: str,
        payload: OfferDecisionExportPreviewSnapshotCreate | dict[str, Any] | None = None,
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload or {})
        detail = await self.get_preview_detail(preview_id, agency_id)
        if not detail:
            raise ValueError("Offer decision export preview not found.")
        preview = detail["preview"]
        snapshot = OfferDecisionExportPreviewSnapshot(
            agency_id=agency_id,
            preview_id=preview_id,
            export_id=preview["export_id"],
            decision_pack_id=preview.get("decision_pack_id"),
            snapshot_name=data.get("snapshot_name") or f"Preview snapshot {preview_id}",
            snapshot_json={
                "preview": preview,
                "sections": detail["sections"],
                "blocks": detail["blocks"],
                "validations": detail["validations"],
                "source_counts": preview.get("source_counts_json") or {},
                "safety_flags": self._safety_flags(),
                "metadata_json": data.get("metadata_json") or {},
            },
            saved_by=actor_from_user(user),
        )
        stored_snapshot = await self.db.collection(PREVIEW_SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        updated_preview = await self.db.collection(PREVIEW_COLLECTION).update_one(
            {"agency_id": agency_id, "id": preview_id},
            {
                "preview_status": OfferDecisionExportPreviewStatus.SNAPSHOT_SAVED.value,
                "snapshot_count": len(await self.list_snapshots(agency_id=agency_id, preview_id=preview_id)),
            },
        )
        return {
            "preview": updated_preview or preview,
            "snapshot": stored_snapshot,
            **self._safety_flags(),
        }

    async def list_sections(
        self,
        *,
        agency_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self._list_records(PREVIEW_SECTION_COLLECTION, agency_id=agency_id, preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id)
        return sorted(items, key=lambda item: int(item.get("section_order") or 0))

    async def list_blocks(
        self,
        *,
        agency_id: str | None = None,
        preview_id: str | None = None,
        section_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self._list_records(PREVIEW_BLOCK_COLLECTION, agency_id=agency_id, preview_id=preview_id, section_id=section_id, export_id=export_id, decision_pack_id=decision_pack_id)
        return sorted(items, key=lambda item: (str(item.get("section_key") or ""), int(item.get("block_order") or 0)))

    async def list_validations(
        self,
        *,
        agency_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(PREVIEW_VALIDATION_COLLECTION, agency_id=agency_id, preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id)

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        preview_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(PREVIEW_SNAPSHOT_COLLECTION, agency_id=agency_id, preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id)

    async def _list_records(
        self,
        collection_name: str,
        *,
        agency_id: str | None = None,
        preview_id: str | None = None,
        section_id: str | None = None,
        export_id: str | None = None,
        decision_pack_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if preview_id:
            filters["preview_id"] = preview_id
        if section_id:
            filters["section_id"] = section_id
        if export_id:
            filters["export_id"] = export_id
        if decision_pack_id:
            filters["decision_pack_id"] = decision_pack_id
        items = await self.db.collection(collection_name).find_many(filters or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or item.get("generated_at") or ""), reverse=True)

    async def _require_export(self, agency_id: str, export_id: str) -> dict[str, Any]:
        export = await self.db.collection(EXPORT_COLLECTION).find_one({"agency_id": agency_id, "id": export_id})
        if not export:
            raise ValueError("Offer decision export not found.")
        return export

    async def _require_preview(self, agency_id: str, preview_id: str) -> dict[str, Any]:
        preview = await self.get_preview(preview_id, agency_id)
        if not preview:
            raise ValueError("Offer decision export preview not found.")
        return preview

    async def _source_bundle(self, agency_id: str, export: dict[str, Any], source_artifact_ids: list[str]) -> dict[str, Any]:
        export_filters = {"agency_id": agency_id, "export_id": export["id"]}
        decision_pack_id = export.get("decision_pack_id")
        pack_filters = {"agency_id": agency_id, "decision_pack_id": decision_pack_id}
        all_artifacts = await self.db.collection(EXPORT_ARTIFACT_COLLECTION).find_many(export_filters)
        selected_artifact_ids = set(source_artifact_ids or [])
        artifacts = [item for item in all_artifacts if not selected_artifact_ids or item["id"] in selected_artifact_ids]
        return {
            "export": export,
            "export_sections": await self.db.collection(EXPORT_SECTION_COLLECTION).find_many(export_filters),
            "artifacts": artifacts,
            "recipient_drafts": await self.db.collection(EXPORT_RECIPIENT_DRAFT_COLLECTION).find_many(export_filters),
            "export_audit_events": await self.db.collection(EXPORT_AUDIT_EVENT_COLLECTION).find_many(export_filters),
            "decision_pack": await self.db.collection(PACK_COLLECTION).find_one({"agency_id": agency_id, "id": decision_pack_id}) if decision_pack_id else None,
            "explanations": await self.db.collection(EXPLANATION_COLLECTION).find_many(pack_filters) if decision_pack_id else [],
            "timeline": await self.db.collection(TIMELINE_COLLECTION).find_many(pack_filters) if decision_pack_id else [],
            "reasons": await self.db.collection(REASON_COLLECTION).find_many(pack_filters) if decision_pack_id else [],
            "acknowledgements": await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).find_many(pack_filters) if decision_pack_id else [],
            "audit_snapshots": await self.db.collection(AUDIT_SNAPSHOT_COLLECTION).find_many(pack_filters) if decision_pack_id else [],
        }

    def _source_counts(self, bundle: dict[str, Any]) -> dict[str, int]:
        return {
            key: len(value)
            for key, value in bundle.items()
            if isinstance(value, list)
        }

    def _preview_summary(self, export: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
        counts = self._source_counts(bundle)
        return {
            "export_id": export["id"],
            "decision_pack_id": export.get("decision_pack_id"),
            "export_name": export.get("export_name"),
            "artifact_count": counts.get("artifacts", 0),
            "recipient_draft_count": counts.get("recipient_drafts", 0),
            "timeline_event_count": counts.get("timeline", 0),
            "acknowledgement_count": counts.get("acknowledgements", 0),
            "metadata_only": True,
            "render_preview_only": True,
            "public_links_disabled": True,
            "automatic_sending_disabled": True,
        }

    def _section_specs(self, export: dict[str, Any], bundle: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            self._section("executive_summary", "Executive summary", {"export": export, "source_counts": self._source_counts(bundle)}),
            self._section("selected_decision_pack_overview", "Selected decision pack overview", {"decision_pack": bundle["decision_pack"]}),
            self._section("option_comparison", "Option comparison", self._export_section_payload(bundle, "options")),
            self._section("advisor_evidence", "Advisor evidence", self._export_section_payload(bundle, "evidence")),
            self._section("warnings", "Warnings", self._export_section_payload(bundle, "warnings")),
            self._section("human_review_notes", "Human review notes", self._export_section_payload(bundle, "review_notes")),
            self._section("explanation_narrative", "Explanation narrative", {"items": bundle["explanations"], "reasons": bundle["reasons"]}),
            self._section("decision_timeline", "Decision timeline", {"items": bundle["timeline"]}),
            self._section("acknowledgement_status", "Acknowledgement status", {"items": bundle["acknowledgements"]}),
            self._section("export_artifact_metadata", "Export artifact metadata", {"items": bundle["artifacts"]}),
            self._section("recipient_draft_metadata", "Recipient draft metadata", {"items": bundle["recipient_drafts"]}),
            self._section("audit_trail", "Audit trail", {"export_audit_events": bundle["export_audit_events"], "audit_snapshots": bundle["audit_snapshots"]}),
        ]

    def _section(self, section_key: str, title: str, section_json: dict[str, Any]) -> dict[str, Any]:
        return {
            "section_key": section_key,
            "section_title": title,
            "section_json": section_json,
        }

    def _export_section_payload(self, bundle: dict[str, Any], section_key: str) -> dict[str, Any]:
        for section in bundle.get("export_sections") or []:
            if section.get("section_key") == section_key:
                return section.get("section_json") or {}
        return {"items": []}

    def _block_specs(self, section: dict[str, Any], export: dict[str, Any], bundle: dict[str, Any]) -> list[dict[str, Any]]:
        key = section["section_key"]
        title = section["section_title"]
        section_json = section["section_json"]
        blocks = [
            self._block("heading", title, {"text": title}),
        ]
        if key == OfferDecisionExportPreviewSectionKey.EXECUTIVE_SUMMARY.value:
            blocks.extend(
                [
                    self._block("paragraph", "Preview purpose", {"text": "Internal render preview for human review. No file delivery or public link is created."}),
                    self._block("key_value_table", "Export summary", {"rows": self._summary_rows(export, bundle)}),
                    self._block("safety_disclaimer", "Safety boundary", self._safety_flags()),
                ]
            )
        elif key in {
            OfferDecisionExportPreviewSectionKey.SELECTED_DECISION_PACK_OVERVIEW.value,
            OfferDecisionExportPreviewSectionKey.EXPLANATION_NARRATIVE.value,
        }:
            blocks.append(self._block("key_value_table", title, {"data": section_json}))
        elif key == OfferDecisionExportPreviewSectionKey.WARNINGS.value:
            blocks.append(self._block("warning_list", title, section_json))
        elif key == OfferDecisionExportPreviewSectionKey.ADVISOR_EVIDENCE.value:
            blocks.append(self._block("evidence_list", title, section_json))
        elif key == OfferDecisionExportPreviewSectionKey.DECISION_TIMELINE.value:
            blocks.append(self._block("timeline_list", title, section_json))
        elif key == OfferDecisionExportPreviewSectionKey.EXPORT_ARTIFACT_METADATA.value:
            for artifact in bundle.get("artifacts") or []:
                blocks.append(self._block("artifact_reference", artifact.get("artifact_name") or artifact["id"], {"artifact": artifact}, "offer_decision_export_artifacts", artifact["id"]))
        elif key == OfferDecisionExportPreviewSectionKey.RECIPIENT_DRAFT_METADATA.value:
            for draft in bundle.get("recipient_drafts") or []:
                blocks.append(self._block("recipient_draft", draft.get("recipient_email") or draft["id"], {"recipient_draft": draft}, "offer_decision_export_recipient_drafts", draft["id"]))
        else:
            blocks.append(self._block("key_value_table", title, {"data": section_json}))
        return blocks

    def _block(
        self,
        block_type: str,
        block_title: str,
        block_json: dict[str, Any],
        source_record_type: str | None = None,
        source_record_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "block_type": block_type,
            "block_title": block_title,
            "block_json": block_json,
            "source_record_type": source_record_type,
            "source_record_id": source_record_id,
        }

    def _summary_rows(self, export: dict[str, Any], bundle: dict[str, Any]) -> list[dict[str, Any]]:
        counts = self._source_counts(bundle)
        return [
            {"label": "Export", "value": export.get("export_name") or export["id"]},
            {"label": "Decision pack", "value": export.get("decision_pack_id")},
            {"label": "Artifacts", "value": counts.get("artifacts", 0)},
            {"label": "Recipient drafts", "value": counts.get("recipient_drafts", 0)},
            {"label": "Timeline events", "value": counts.get("timeline", 0)},
            {"label": "Acknowledgements", "value": counts.get("acknowledgements", 0)},
        ]

    def _validation_specs(
        self,
        preview: dict[str, Any],
        bundle: dict[str, Any],
        internal_reviewer: str | None,
    ) -> list[dict[str, Any]]:
        checks = [
            ("missing_decision_pack", bool(bundle.get("decision_pack")), "Decision pack metadata is present.", "Decision pack metadata is missing."),
            ("missing_explanation", bool(bundle.get("explanations")), "Explanation metadata is present.", "Explanation metadata is missing."),
            ("missing_timeline", bool(bundle.get("timeline")), "Timeline metadata is present.", "Timeline metadata is missing."),
            ("missing_acknowledgements", bool(bundle.get("acknowledgements")), "Acknowledgement metadata is present.", "Acknowledgement metadata is missing."),
            ("missing_recipient_draft", bool(bundle.get("recipient_drafts")), "Recipient draft metadata is present.", "Recipient draft metadata is missing."),
            ("missing_artifact_metadata", bool(bundle.get("artifacts")), "Artifact metadata is present.", "Artifact metadata is missing."),
            ("missing_internal_reviewer", bool(internal_reviewer), "Internal reviewer metadata is present.", "Internal reviewer metadata is missing."),
        ]
        specs = []
        for key, passed, pass_message, warning_message in checks:
            specs.append(
                {
                    "validation_key": key,
                    "validation_status": OfferDecisionExportPreviewValidationStatus.PASS.value if passed else OfferDecisionExportPreviewValidationStatus.WARNING.value,
                    "severity": "info" if passed else "warning",
                    "message": pass_message if passed else warning_message,
                    "validation_json": {"passed": passed, "preview_id": preview["id"]},
                }
            )
        specs.append(
            {
                "validation_key": OfferDecisionExportPreviewValidationKey.SAFETY_BOUNDARY_REMINDER.value,
                "validation_status": OfferDecisionExportPreviewValidationStatus.REMINDER.value,
                "severity": "info",
                "message": "Preview is metadata-only; sending, public links, PDF delivery, provider execution, and price mutation remain disabled.",
                "validation_json": self._safety_flags(),
            }
        )
        return specs

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only_rendering_enabled": True,
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
