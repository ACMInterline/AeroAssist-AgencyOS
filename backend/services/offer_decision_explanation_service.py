from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionAcknowledgement,
    OfferDecisionAcknowledgementCreate,
    OfferDecisionActorType,
    OfferDecisionAuditSnapshot,
    OfferDecisionAuditSnapshotCreate,
    OfferDecisionEvidenceReference,
    OfferDecisionEvidenceReferenceType,
    OfferDecisionExplanation,
    OfferDecisionExplanationCreate,
    OfferDecisionExplanationUpdate,
    OfferDecisionReason,
    OfferDecisionReasonCreate,
    OfferDecisionReasonUpdate,
    OfferDecisionTimelineEvent,
    OfferDecisionTimelineEventCreate,
    OfferDecisionTimelineEventType,
    now_utc,
)


PHASE_LABEL = "phase_37_4_offer_explanation_decision_timeline_foundation"

EXPLANATION_COLLECTION = "offer_decision_explanations"
TIMELINE_COLLECTION = "offer_decision_timeline_events"
EVIDENCE_REFERENCE_COLLECTION = "offer_decision_evidence_references"
REASON_COLLECTION = "offer_decision_reasons"
ACKNOWLEDGEMENT_COLLECTION = "offer_decision_acknowledgements"
AUDIT_SNAPSHOT_COLLECTION = "offer_decision_audit_snapshots"

DECISION_PACK_COLLECTION = "offer_decision_packs"
DECISION_PACK_EVIDENCE_COLLECTION = "offer_decision_pack_evidence"
DECISION_PACK_WARNING_COLLECTION = "offer_decision_pack_warnings"
DECISION_PACK_REVIEW_NOTE_COLLECTION = "offer_decision_pack_review_notes"


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


class OfferDecisionExplanationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "explanations": len(await self.list_explanations(agency_id=agency_id)),
            "timeline_events": len(await self.list_timeline(agency_id=agency_id)),
            "reasons": len(await self.list_reasons(agency_id=agency_id)),
            "evidence_references": len(await self.list_evidence_references(agency_id=agency_id)),
            "acknowledgements": len(await self.list_acknowledgements(agency_id=agency_id)),
            "snapshots": len(await self.list_snapshots(agency_id=agency_id)),
            "decision_explanations_enabled": True,
            "decision_timeline_enabled": True,
            "decision_reasons_enabled": True,
            "evidence_reference_enabled": True,
            "acknowledgements_enabled": True,
            "immutable_snapshots_enabled": True,
            "human_review_only_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Offer decision explanations and timelines are metadata-only audit records for human review. They never rank, price, book, issue, charge, invoice, settle, scrape, call AI, or execute providers.",
        }

    async def list_explanations(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(EXPLANATION_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def get_explanation(self, explanation_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": explanation_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(EXPLANATION_COLLECTION).find_one(filters)

    async def create_explanation(self, agency_id: str, payload: OfferDecisionExplanationCreate | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        pack = await self._require_pack(agency_id, data["decision_pack_id"])
        references = await self.ensure_evidence_references(agency_id, pack)
        explanation = OfferDecisionExplanation(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            offer_option_id=data.get("offer_option_id"),
            title=data["title"],
            explanation_type=enum_value(data.get("explanation_type")) or "summary",
            explanation_text=data["explanation_text"],
            created_by=actor_from_user(user),
            finalized=bool(data.get("finalized", False)),
            finalized_at=now_utc() if data.get("finalized") else None,
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(EXPLANATION_COLLECTION).insert_one(explanation.model_dump(mode="json"))
        event = await self._append_timeline(
            agency_id,
            pack,
            {
                "offer_option_id": stored.get("offer_option_id"),
                "event_type": OfferDecisionTimelineEventType.CREATED.value,
                "actor": actor_from_user(user),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": f"Decision explanation created: {stored.get('title')}",
                "metadata_json": {"explanation_id": stored["id"]},
            },
        )
        return {"explanation": stored, "evidence_references": references, "timeline_event": event, **self._safety_flags()}

    async def update_explanation(self, agency_id: str, explanation_id: str, payload: OfferDecisionExplanationUpdate | dict[str, Any], user: dict | None = None) -> dict[str, Any] | None:
        current = await self.get_explanation(explanation_id, agency_id)
        if not current:
            return None
        data = payload_dict(payload)
        archive_only = set(data.keys()).issubset({"archived"})
        if current.get("finalized") and not archive_only:
            raise ValueError("Finalized explanations are immutable except archive state.")
        updates = {
            key: enum_value(value)
            for key, value in {
                "title": data.get("title"),
                "explanation_type": data.get("explanation_type"),
                "explanation_text": data.get("explanation_text"),
                "finalized": data.get("finalized"),
                "archived": data.get("archived"),
                "metadata_json": data.get("metadata_json"),
            }.items()
            if value is not None
        }
        if data.get("finalized") is True and not current.get("finalized"):
            updates["finalized_at"] = now_utc()
        updated = await self.db.collection(EXPLANATION_COLLECTION).update_one({"agency_id": agency_id, "id": explanation_id}, updates)
        pack = await self._require_pack(agency_id, current["decision_pack_id"])
        event_type = OfferDecisionTimelineEventType.REVIEW_COMPLETED.value if updates.get("finalized") else OfferDecisionTimelineEventType.MANUAL_OVERRIDE_RECORDED.value
        event = await self._append_timeline(
            agency_id,
            pack,
            {
                "offer_option_id": current.get("offer_option_id"),
                "event_type": event_type,
                "actor": actor_from_user(user),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": f"Decision explanation updated: {current.get('title')}",
                "metadata_json": {"explanation_id": explanation_id, "archived": updates.get("archived", current.get("archived"))},
            },
        )
        return {"explanation": updated, "timeline_event": event, **self._safety_flags()}

    async def list_timeline(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self._list_records(TIMELINE_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)
        return sorted(items, key=lambda item: str(item.get("timestamp") or item.get("created_at") or ""), reverse=True)

    async def append_timeline_event(self, agency_id: str, payload: OfferDecisionTimelineEventCreate | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        pack = await self._require_pack(agency_id, data["decision_pack_id"])
        event = await self._append_timeline(
            agency_id,
            pack,
            {
                "offer_option_id": data.get("offer_option_id"),
                "event_type": enum_value(data.get("event_type")) or OfferDecisionTimelineEventType.CREATED.value,
                "actor": data.get("actor") or actor_from_user(user),
                "actor_type": enum_value(data.get("actor_type")) or OfferDecisionActorType.AGENCY.value,
                "description": data["description"],
                "metadata_json": data.get("metadata_json") or {},
            },
        )
        return {"timeline_event": event, **self._safety_flags()}

    async def list_evidence_references(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(EVIDENCE_REFERENCE_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def ensure_evidence_references(self, agency_id: str, pack: dict[str, Any]) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        for reference in await self._derived_references(agency_id, pack):
            existing = await self.db.collection(EVIDENCE_REFERENCE_COLLECTION).find_one(
                {
                    "agency_id": agency_id,
                    "decision_pack_id": pack["id"],
                    "reference_type": reference["reference_type"],
                    "reference_id": reference["reference_id"],
                }
            )
            if existing:
                continue
            record = OfferDecisionEvidenceReference(
                agency_id=agency_id,
                decision_pack_id=pack["id"],
                offer_workspace_id=pack["offer_workspace_id"],
                offer_option_id=reference.get("offer_option_id"),
                reference_type=reference["reference_type"],
                reference_id=reference["reference_id"],
                display_name=reference["display_name"],
                summary=reference.get("summary"),
                source_collection=reference.get("source_collection"),
                source_record_id=reference.get("source_record_id"),
                metadata_json=reference.get("metadata_json") or {},
            )
            created.append(await self.db.collection(EVIDENCE_REFERENCE_COLLECTION).insert_one(record.model_dump(mode="json")))
        return created

    async def list_reasons(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(REASON_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def create_reason(self, agency_id: str, payload: OfferDecisionReasonCreate | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        pack = await self._require_pack(agency_id, data["decision_pack_id"])
        reason = OfferDecisionReason(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            offer_option_id=data.get("offer_option_id"),
            reason_category=enum_value(data.get("reason_category")) or "manual",
            importance=enum_value(data.get("importance")) or "medium",
            text=data["text"],
            created_by=actor_from_user(user),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(REASON_COLLECTION).insert_one(reason.model_dump(mode="json"))
        event = await self._append_timeline(
            agency_id,
            pack,
            {
                "offer_option_id": stored.get("offer_option_id"),
                "event_type": OfferDecisionTimelineEventType.NOTE_ADDED.value,
                "actor": actor_from_user(user),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": f"Decision reason recorded: {stored.get('reason_category')}",
                "metadata_json": {"reason_id": stored["id"], "importance": stored.get("importance")},
            },
        )
        return {"reason": stored, "timeline_event": event, **self._safety_flags()}

    async def update_reason(self, agency_id: str, reason_id: str, payload: OfferDecisionReasonUpdate | dict[str, Any], user: dict | None = None) -> dict[str, Any] | None:
        current = await self.db.collection(REASON_COLLECTION).find_one({"agency_id": agency_id, "id": reason_id})
        if not current:
            return None
        data = payload_dict(payload)
        updates = {
            key: enum_value(value)
            for key, value in {
                "reason_category": data.get("reason_category"),
                "importance": data.get("importance"),
                "text": data.get("text"),
                "archived": data.get("archived"),
                "metadata_json": data.get("metadata_json"),
            }.items()
            if value is not None
        }
        updated = await self.db.collection(REASON_COLLECTION).update_one({"agency_id": agency_id, "id": reason_id}, updates)
        pack = await self._require_pack(agency_id, current["decision_pack_id"])
        event = await self._append_timeline(
            agency_id,
            pack,
            {
                "offer_option_id": current.get("offer_option_id"),
                "event_type": OfferDecisionTimelineEventType.MANUAL_OVERRIDE_RECORDED.value,
                "actor": actor_from_user(user),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": "Decision reason updated.",
                "metadata_json": {"reason_id": reason_id},
            },
        )
        return {"reason": updated, "timeline_event": event, **self._safety_flags()}

    async def list_acknowledgements(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(ACKNOWLEDGEMENT_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def create_acknowledgement(self, agency_id: str, payload: OfferDecisionAcknowledgementCreate | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        pack = await self._require_pack(agency_id, data["decision_pack_id"])
        acknowledgement = OfferDecisionAcknowledgement(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            acknowledged_by=data.get("acknowledged_by") or actor_from_user(user) or "unknown",
            acknowledgement_type=enum_value(data.get("acknowledgement_type")) or "reviewed",
            notes=data.get("notes"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(ACKNOWLEDGEMENT_COLLECTION).insert_one(acknowledgement.model_dump(mode="json"))
        event = await self._append_timeline(
            agency_id,
            pack,
            {
                "event_type": OfferDecisionTimelineEventType.REVIEW_COMPLETED.value,
                "actor": stored.get("acknowledged_by"),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": f"Decision acknowledgement recorded: {stored.get('acknowledgement_type')}",
                "metadata_json": {"acknowledgement_id": stored["id"]},
            },
        )
        return {"acknowledgement": stored, "timeline_event": event, **self._safety_flags()}

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(AUDIT_SNAPSHOT_COLLECTION, agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)

    async def create_snapshot(self, agency_id: str, payload: OfferDecisionAuditSnapshotCreate | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        pack = await self._require_pack(agency_id, data["decision_pack_id"])
        await self.ensure_evidence_references(agency_id, pack)
        snapshot_event = await self._append_timeline(
            agency_id,
            pack,
            {
                "event_type": OfferDecisionTimelineEventType.SNAPSHOT_SAVED.value,
                "actor": actor_from_user(user),
                "actor_type": OfferDecisionActorType.AGENCY.value,
                "description": "Offer decision audit snapshot saved.",
                "metadata_json": data.get("metadata_json") or {},
            },
        )
        explanations = await self.list_explanations(agency_id=agency_id, decision_pack_id=pack["id"])
        timeline = await self.list_timeline(agency_id=agency_id, decision_pack_id=pack["id"])
        evidence = await self.list_evidence_references(agency_id=agency_id, decision_pack_id=pack["id"])
        reasons = await self.list_reasons(agency_id=agency_id, decision_pack_id=pack["id"])
        acknowledgements = await self.list_acknowledgements(agency_id=agency_id, decision_pack_id=pack["id"])
        snapshot = OfferDecisionAuditSnapshot(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            snapshot_name=data.get("snapshot_name") or f"Offer decision audit snapshot {pack.get('pack_name') or pack['id']}",
            explanation_ids=[item["id"] for item in explanations],
            timeline_event_ids=[item["id"] for item in timeline],
            evidence_reference_ids=[item["id"] for item in evidence],
            reason_ids=[item["id"] for item in reasons],
            acknowledgement_ids=[item["id"] for item in acknowledgements],
            snapshot_json={
                "decision_pack": pack,
                "explanations": explanations,
                "timeline": timeline,
                "evidence_references": evidence,
                "reasons": reasons,
                "acknowledgements": acknowledgements,
                "snapshot_event": snapshot_event,
                "metadata_json": data.get("metadata_json") or {},
                "metadata_only": True,
                "human_review_only": True,
            },
        )
        stored = await self.db.collection(AUDIT_SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        return {"snapshot": stored, "timeline_event": snapshot_event, **self._safety_flags()}

    async def _list_records(
        self,
        collection_name: str,
        *,
        agency_id: str | None = None,
        decision_pack_id: str | None = None,
        offer_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if decision_pack_id:
            filters["decision_pack_id"] = decision_pack_id
        if offer_workspace_id:
            filters["offer_workspace_id"] = offer_workspace_id
        items = await self.db.collection(collection_name).find_many(filters or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _require_pack(self, agency_id: str, decision_pack_id: str) -> dict[str, Any]:
        pack = await self.db.collection(DECISION_PACK_COLLECTION).find_one({"agency_id": agency_id, "id": decision_pack_id})
        if not pack:
            raise ValueError("Offer decision pack not found.")
        return pack

    async def _append_timeline(self, agency_id: str, pack: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        event = OfferDecisionTimelineEvent(
            agency_id=agency_id,
            decision_pack_id=pack["id"],
            offer_workspace_id=pack["offer_workspace_id"],
            offer_option_id=data.get("offer_option_id"),
            event_type=enum_value(data.get("event_type")) or OfferDecisionTimelineEventType.CREATED.value,
            actor=data.get("actor"),
            actor_type=enum_value(data.get("actor_type")) or OfferDecisionActorType.SYSTEM.value,
            description=data["description"],
            metadata_json=data.get("metadata_json") or {},
        )
        return await self.db.collection(TIMELINE_COLLECTION).insert_one(event.model_dump(mode="json"))

    async def _derived_references(self, agency_id: str, pack: dict[str, Any]) -> list[dict[str, Any]]:
        references: list[dict[str, Any]] = []
        for advisor_result_id in pack.get("advisor_result_ids") or []:
            references.append(self._reference("advisor_result", advisor_result_id, "Advisor result", "Advisor result linked to the decision pack."))
        for snapshot_id in pack.get("policy_comparison_snapshot_ids") or []:
            references.append(self._reference("comparison_snapshot", snapshot_id, "Policy comparison snapshot", "Comparison snapshot linked to the decision pack."))
        for quote_id in pack.get("quote_result_ids") or []:
            references.append(self._reference("pricing_rule", quote_id, "Ancillary quote result", "Pricing quote metadata linked to the decision pack."))
        for mechanics_id in pack.get("service_mechanics_record_ids") or []:
            references.append(self._reference("mechanics_rule", mechanics_id, "Service mechanics record", "Mechanics metadata linked to the decision pack."))

        taxonomy_refs = (pack.get("taxonomy_refs_json") or {}).get("refs") or []
        for item in taxonomy_refs:
            reference_id = "/".join([str(item.get(key) or "") for key in ["domain_code", "family_code", "variant_code"]]).strip("/")
            if reference_id:
                references.append(self._reference("taxonomy", reference_id, "Taxonomy reference", "Canonical taxonomy reference used by the decision pack.", metadata_json=item))

        pack_evidence = await self.db.collection(DECISION_PACK_EVIDENCE_COLLECTION).find_many({"agency_id": agency_id, "decision_pack_id": pack["id"]})
        for item in pack_evidence:
            references.extend(self._references_from_pack_evidence(item))

        warnings = await self.db.collection(DECISION_PACK_WARNING_COLLECTION).find_many({"agency_id": agency_id, "decision_pack_id": pack["id"]})
        for item in warnings:
            references.append(
                self._reference(
                    "warning",
                    item["id"],
                    item.get("warning_type") or "Decision pack warning",
                    item.get("message"),
                    offer_option_id=item.get("offer_option_id"),
                    source_collection=DECISION_PACK_WARNING_COLLECTION,
                    source_record_id=item["id"],
                )
            )

        review_notes = await self.db.collection(DECISION_PACK_REVIEW_NOTE_COLLECTION).find_many({"agency_id": agency_id, "decision_pack_id": pack["id"]})
        for item in review_notes:
            references.append(
                self._reference(
                    "review_note",
                    item["id"],
                    item.get("note_title") or "Review note",
                    item.get("note_body"),
                    offer_option_id=item.get("offer_option_id"),
                    source_collection=DECISION_PACK_REVIEW_NOTE_COLLECTION,
                    source_record_id=item["id"],
                )
            )
        return self._dedupe_references(references)

    def _references_from_pack_evidence(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        references = []
        if item.get("advisor_result_id"):
            references.append(self._reference("advisor_result", item["advisor_result_id"], "Advisor result", item.get("evidence_summary"), item.get("offer_option_id"), item.get("source_collection"), item.get("source_record_id")))
        if item.get("policy_comparison_snapshot_id"):
            references.append(self._reference("comparison_snapshot", item["policy_comparison_snapshot_id"], "Policy comparison snapshot", item.get("evidence_summary"), item.get("offer_option_id"), item.get("source_collection"), item.get("source_record_id")))
        if item.get("quote_result_id"):
            references.append(self._reference("pricing_rule", item["quote_result_id"], "Ancillary quote result", item.get("evidence_summary"), item.get("offer_option_id"), item.get("source_collection"), item.get("source_record_id")))
        if item.get("service_mechanics_record_id"):
            references.append(self._reference("mechanics_rule", item["service_mechanics_record_id"], "Service mechanics record", item.get("evidence_summary"), item.get("offer_option_id"), item.get("source_collection"), item.get("source_record_id")))
        if item.get("source_record_id") and not references:
            references.append(self._reference("policy_record", item["source_record_id"], item.get("evidence_title") or "Decision pack evidence", item.get("evidence_summary"), item.get("offer_option_id"), item.get("source_collection"), item.get("source_record_id")))
        return references

    def _reference(
        self,
        reference_type: str,
        reference_id: str,
        display_name: str,
        summary: str | None,
        offer_option_id: str | None = None,
        source_collection: str | None = None,
        source_record_id: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "reference_type": reference_type,
            "reference_id": str(reference_id),
            "display_name": display_name,
            "summary": summary,
            "offer_option_id": offer_option_id,
            "source_collection": source_collection,
            "source_record_id": source_record_id,
            "metadata_json": metadata_json or {},
        }

    def _dedupe_references(self, references: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        seen = set()
        for item in references:
            key = (item.get("reference_type"), item.get("reference_id"))
            if not item.get("reference_id") or key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "human_review_only": True,
            "human_review_only_enabled": True,
            "provider_execution_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_disabled": True,
            "payment_disabled": True,
            "invoice_disabled": True,
            "settlement_disabled": True,
            "automatic_recommendation_disabled": True,
            "offer_price_mutation_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
        }
