from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionExportAuditReview,
    OfferDecisionExportAuditReviewChecklistItem,
    OfferDecisionExportAuditReviewChecklistItemCreateRequest,
    OfferDecisionExportAuditReviewChecklistItemUpdateRequest,
    OfferDecisionExportAuditReviewCreateRequest,
    OfferDecisionExportAuditReviewFinding,
    OfferDecisionExportAuditReviewFindingCreateRequest,
    OfferDecisionExportAuditReviewFindingUpdateRequest,
    OfferDecisionExportAuditReviewSnapshot,
    OfferDecisionExportAuditReviewSnapshotCreateRequest,
    OfferDecisionExportAuditReviewStatusUpdateRequest,
    now_utc,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_38_0_offer_decision_export_audit_review_foundation"

REVIEW_COLLECTION = "offer_decision_export_audit_reviews"
FINDING_COLLECTION = "offer_decision_export_audit_review_findings"
CHECKLIST_COLLECTION = "offer_decision_export_audit_review_checklist_items"
SNAPSHOT_COLLECTION = "offer_decision_export_audit_review_snapshots"

PACK_COLLECTION = "offer_decision_packs"
PACK_SNAPSHOT_COLLECTION = "offer_decision_pack_snapshots"
EXPLANATION_COLLECTION = "offer_decision_explanations"
EXPLANATION_SNAPSHOT_COLLECTION = "offer_decision_audit_snapshots"
EXPORT_COLLECTION = "offer_decision_exports"
PREVIEW_COLLECTION = "offer_decision_export_previews"
PREVIEW_SNAPSHOT_COLLECTION = "offer_decision_export_preview_snapshots"
RELEASE_READINESS_COLLECTION = "offer_decision_export_release_readiness"
RELEASE_SNAPSHOT_COLLECTION = "offer_decision_export_release_snapshots"
HANDOFF_COLLECTION = "offer_decision_export_delivery_handoffs"
HANDOFF_SNAPSHOT_COLLECTION = "offer_decision_export_delivery_snapshots"
OUTCOME_COLLECTION = "offer_decision_export_delivery_outcomes"
OUTCOME_EVENT_COLLECTION = "offer_decision_export_delivery_outcome_events"
OUTCOME_RECEIPT_COLLECTION = "offer_decision_export_delivery_receipts"
OUTCOME_ISSUE_COLLECTION = "offer_decision_export_delivery_issues"
OUTCOME_SNAPSHOT_COLLECTION = "offer_decision_export_delivery_outcome_snapshots"


class OfferDecisionExportAuditReviewService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "review_count": len(await self.list_reviews(agency_id=agency_id)),
            "finding_count": len(await self.list_findings(agency_id=agency_id)),
            "checklist_item_count": len(await self.list_checklist_items(agency_id=agency_id)),
            "snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "audit_reviews_enabled": True,
            "audit_review_findings_enabled": True,
            "audit_review_checklists_enabled": True,
            "immutable_audit_review_snapshots_enabled": True,
            "agency_audit_review_ui_enabled": True,
            "platform_audit_review_ui_enabled": True,
            "metadata_only_review_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 38.0 audit reviews are metadata-only. They review lifecycle completeness, approval trail, handoff trail, outcome trail, unresolved issues, and immutable snapshot coverage without sending, delivery, booking, PNR mutation, ticketing, EMD issuance, payment, invoice, settlement, scraping, external AI, or provider execution.",
        }

    async def create_review(
        self,
        agency_id: str,
        payload: OfferDecisionExportAuditReviewCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        bundle = await self._source_bundle(agency_id, data)
        coverage = self._coverage_summary(bundle)
        review = OfferDecisionExportAuditReview(
            agency_id=agency_id,
            review_scope=data.get("review_scope") or "full_lifecycle",
            title=data.get("title") or f"Audit review for export {coverage.get('export_id') or 'metadata'}",
            decision_pack_id=coverage.get("decision_pack_id"),
            explanation_id=coverage.get("explanation_id"),
            export_id=coverage.get("export_id"),
            preview_id=coverage.get("preview_id"),
            release_readiness_id=coverage.get("release_readiness_id"),
            handoff_id=coverage.get("handoff_id"),
            outcome_id=coverage.get("outcome_id"),
            coverage_summary=coverage,
            completion_score=coverage.get("completion_score", 0),
            reviewed_by=data.get("reviewed_by") or actor_from_user(user),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(REVIEW_COLLECTION).insert_one(review.model_dump(mode="json"))
        for item in self._checklist_specs(bundle):
            checklist = OfferDecisionExportAuditReviewChecklistItem(agency_id=agency_id, review_id=stored["id"], **item)
            await self.db.collection(CHECKLIST_COLLECTION).insert_one(checklist.model_dump(mode="json"))
        for item in self._finding_specs(bundle):
            finding = OfferDecisionExportAuditReviewFinding(agency_id=agency_id, review_id=stored["id"], **item)
            await self.db.collection(FINDING_COLLECTION).insert_one(finding.model_dump(mode="json"))
        refreshed = await self._refresh_review_counts(agency_id, stored["id"])
        return {"review": refreshed or stored, **self._safety_flags()}

    async def list_reviews(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        outcome_id: str | None = None,
        review_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(REVIEW_COLLECTION, agency_id=agency_id, export_id=export_id, outcome_id=outcome_id, review_status=review_status)

    async def get_review(self, review_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": review_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(REVIEW_COLLECTION).find_one(filters)

    async def get_review_detail(self, review_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        review = await self.get_review(review_id, agency_id)
        if not review:
            return None
        return {
            "review": review,
            "findings": await self.list_findings(agency_id=agency_id, review_id=review_id),
            "checklist_items": await self.list_checklist_items(agency_id=agency_id, review_id=review_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, review_id=review_id),
            "source_summary": review.get("coverage_summary") or {},
            **self._safety_flags(),
        }

    async def update_review_status(
        self,
        agency_id: str,
        review_id: str,
        payload: OfferDecisionExportAuditReviewStatusUpdateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        review = await self._require_review(agency_id, review_id)
        updated = await self.db.collection(REVIEW_COLLECTION).update_one(
            {"agency_id": agency_id, "id": review_id},
            {
                "review_status": enum_value(data["review_status"]),
                "status_reason": data.get("status_reason"),
                "reviewed_by": data.get("reviewed_by") or actor_from_user(user) or review.get("reviewed_by"),
                "metadata_json": {**(review.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        return {"review": updated or review, **self._safety_flags()}

    async def add_finding(
        self,
        agency_id: str,
        review_id: str,
        payload: OfferDecisionExportAuditReviewFindingCreateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_review(agency_id, review_id)
        finding = OfferDecisionExportAuditReviewFinding(
            agency_id=agency_id,
            review_id=review_id,
            finding_type=data.get("finding_type") or "other",
            severity=data.get("severity") or "medium",
            title=data["title"],
            description=data.get("description"),
            source_entity_type=data.get("source_entity_type"),
            source_entity_id=data.get("source_entity_id"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(FINDING_COLLECTION).insert_one(finding.model_dump(mode="json"))
        refreshed = await self._refresh_review_counts(agency_id, review_id)
        return {"review": refreshed, "finding": stored, **self._safety_flags()}

    async def update_finding(
        self,
        agency_id: str,
        finding_id: str,
        payload: OfferDecisionExportAuditReviewFindingUpdateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        finding = await self._require_record(FINDING_COLLECTION, agency_id, finding_id, "Audit review finding not found.")
        resolved = enum_value(data["finding_status"]) == "resolved"
        updated = await self.db.collection(FINDING_COLLECTION).update_one(
            {"agency_id": agency_id, "id": finding_id},
            {
                "finding_status": enum_value(data["finding_status"]),
                "resolved_by": data.get("resolved_by") or (actor_from_user(user) if resolved else finding.get("resolved_by")),
                "resolved_at": now_utc() if resolved else None,
                "resolution_notes": data.get("resolution_notes"),
                "metadata_json": {**(finding.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_review_counts(agency_id, finding["review_id"])
        return {"review": refreshed, "finding": updated or finding, **self._safety_flags()}

    async def list_findings(
        self,
        *,
        agency_id: str | None = None,
        review_id: str | None = None,
        finding_status: str | None = None,
        finding_type: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(FINDING_COLLECTION, agency_id=agency_id, review_id=review_id, finding_status=finding_status, finding_type=finding_type)

    async def add_checklist_item(
        self,
        agency_id: str,
        review_id: str,
        payload: OfferDecisionExportAuditReviewChecklistItemCreateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_review(agency_id, review_id)
        item = OfferDecisionExportAuditReviewChecklistItem(
            agency_id=agency_id,
            review_id=review_id,
            item_key=data["item_key"],
            label=data["label"],
            item_status=data.get("item_status") or "pending",
            required=data.get("required", True),
            notes=data.get("notes"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(CHECKLIST_COLLECTION).insert_one(item.model_dump(mode="json"))
        refreshed = await self._refresh_review_counts(agency_id, review_id)
        return {"review": refreshed, "checklist_item": stored, **self._safety_flags()}

    async def update_checklist_item(
        self,
        agency_id: str,
        item_id: str,
        payload: OfferDecisionExportAuditReviewChecklistItemUpdateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        item = await self._require_record(CHECKLIST_COLLECTION, agency_id, item_id, "Audit review checklist item not found.")
        updated = await self.db.collection(CHECKLIST_COLLECTION).update_one(
            {"agency_id": agency_id, "id": item_id},
            {
                "item_status": enum_value(data["item_status"]),
                "notes": data.get("notes", item.get("notes")),
                "metadata_json": {**(item.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_review_counts(agency_id, item["review_id"])
        return {"review": refreshed, "checklist_item": updated or item, **self._safety_flags()}

    async def list_checklist_items(
        self,
        *,
        agency_id: str | None = None,
        review_id: str | None = None,
        item_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(CHECKLIST_COLLECTION, agency_id=agency_id, review_id=review_id, item_status=item_status)

    async def create_snapshot(
        self,
        agency_id: str,
        review_id: str,
        payload: OfferDecisionExportAuditReviewSnapshotCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        detail = await self.get_review_detail(review_id, agency_id)
        if not detail:
            raise ValueError("Audit review not found.")
        snapshot = OfferDecisionExportAuditReviewSnapshot(
            agency_id=agency_id,
            review_id=review_id,
            snapshot_type=data.get("snapshot_type") or "review_created",
            payload={
                "review": detail["review"],
                "findings": detail["findings"],
                "checklist_items": detail["checklist_items"],
                "source_summary": detail["source_summary"],
                "safety_flags": self._safety_flags(),
                "metadata_json": data.get("metadata_json") or {},
            },
            created_by=data.get("created_by") or actor_from_user(user),
        )
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        refreshed = await self._refresh_review_counts(agency_id, review_id)
        return {"review": refreshed, "snapshot": stored, **self._safety_flags()}

    async def list_snapshots(
        self,
        *,
        agency_id: str | None = None,
        review_id: str | None = None,
        snapshot_type: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(SNAPSHOT_COLLECTION, agency_id=agency_id, review_id=review_id, snapshot_type=snapshot_type)

    async def _source_bundle(self, agency_id: str, data: dict[str, Any]) -> dict[str, Any]:
        outcome = await self._optional_record(OUTCOME_COLLECTION, agency_id, data.get("outcome_id"))
        handoff_id = data.get("handoff_id") or (outcome or {}).get("handoff_id")
        handoff = await self._optional_record(HANDOFF_COLLECTION, agency_id, handoff_id)
        export_id = data.get("export_id") or (outcome or {}).get("export_id") or (handoff or {}).get("export_id")
        preview_id = data.get("preview_id") or (outcome or {}).get("preview_id") or (handoff or {}).get("preview_id")
        release_readiness_id = data.get("release_readiness_id") or (outcome or {}).get("release_readiness_id") or (handoff or {}).get("release_readiness_id")
        export = await self._optional_record(EXPORT_COLLECTION, agency_id, export_id)
        if not export and not handoff and not outcome:
            raise ValueError("Audit review requires an outcome_id, handoff_id, or export_id that exists for this agency.")
        if not preview_id and export:
            preview = await self._find_one(PREVIEW_COLLECTION, {"agency_id": agency_id, "export_id": export["id"]})
        else:
            preview = await self._optional_record(PREVIEW_COLLECTION, agency_id, preview_id)
        if not release_readiness_id and preview:
            release_readiness = await self._find_one(RELEASE_READINESS_COLLECTION, {"agency_id": agency_id, "preview_id": preview["id"]})
        else:
            release_readiness = await self._optional_record(RELEASE_READINESS_COLLECTION, agency_id, release_readiness_id)
        if not handoff and export:
            handoff = await self._find_one(HANDOFF_COLLECTION, {"agency_id": agency_id, "export_id": export["id"]})
        if not outcome and handoff:
            outcome = await self._find_one(OUTCOME_COLLECTION, {"agency_id": agency_id, "handoff_id": handoff["id"]})
        decision_pack = await self._optional_record(PACK_COLLECTION, agency_id, (export or {}).get("decision_pack_id"))
        explanation = None
        if decision_pack:
            explanation = await self._find_one(EXPLANATION_COLLECTION, {"agency_id": agency_id, "decision_pack_id": decision_pack["id"]})
        return {
            "decision_pack": decision_pack,
            "explanation": explanation,
            "export": export,
            "preview": preview,
            "release_readiness": release_readiness,
            "handoff": handoff,
            "outcome": outcome,
            "delivery_issues": await self._list_records(OUTCOME_ISSUE_COLLECTION, agency_id=agency_id, outcome_id=(outcome or {}).get("id")) if outcome else [],
            "outcome_events": await self._list_records(OUTCOME_EVENT_COLLECTION, agency_id=agency_id, outcome_id=(outcome or {}).get("id")) if outcome else [],
            "outcome_receipts": await self._list_records(OUTCOME_RECEIPT_COLLECTION, agency_id=agency_id, outcome_id=(outcome or {}).get("id")) if outcome else [],
            "pack_snapshots": await self._list_records(PACK_SNAPSHOT_COLLECTION, agency_id=agency_id, decision_pack_id=(decision_pack or {}).get("id")) if decision_pack else [],
            "explanation_snapshots": await self._list_records(EXPLANATION_SNAPSHOT_COLLECTION, agency_id=agency_id, decision_pack_id=(decision_pack or {}).get("id")) if decision_pack else [],
            "preview_snapshots": await self._list_records(PREVIEW_SNAPSHOT_COLLECTION, agency_id=agency_id, preview_id=(preview or {}).get("id")) if preview else [],
            "release_snapshots": await self._list_records(RELEASE_SNAPSHOT_COLLECTION, agency_id=agency_id, readiness_id=(release_readiness or {}).get("id")) if release_readiness else [],
            "handoff_snapshots": await self._list_records(HANDOFF_SNAPSHOT_COLLECTION, agency_id=agency_id, handoff_id=(handoff or {}).get("id")) if handoff else [],
            "outcome_snapshots": await self._list_records(OUTCOME_SNAPSHOT_COLLECTION, agency_id=agency_id, outcome_id=(outcome or {}).get("id")) if outcome else [],
        }

    def _coverage_summary(self, bundle: dict[str, Any]) -> dict[str, Any]:
        keys = ["decision_pack", "explanation", "export", "preview", "release_readiness", "handoff", "outcome"]
        present = {key: bool(bundle.get(key)) for key in keys}
        snapshot_counts = {
            "decision_pack_snapshots": len(bundle.get("pack_snapshots") or []),
            "explanation_snapshots": len(bundle.get("explanation_snapshots") or []),
            "preview_snapshots": len(bundle.get("preview_snapshots") or []),
            "release_snapshots": len(bundle.get("release_snapshots") or []),
            "handoff_snapshots": len(bundle.get("handoff_snapshots") or []),
            "outcome_snapshots": len(bundle.get("outcome_snapshots") or []),
        }
        unresolved_issues = [item for item in bundle.get("delivery_issues") or [] if item.get("issue_status") != "resolved"]
        passed = sum(1 for value in present.values() if value)
        snapshot_passed = sum(1 for value in snapshot_counts.values() if value > 0)
        denominator = len(keys) + len(snapshot_counts) + 1
        numerator = passed + snapshot_passed + (0 if unresolved_issues else 1)
        export = bundle.get("export") or {}
        return {
            "decision_pack_id": (bundle.get("decision_pack") or {}).get("id"),
            "explanation_id": (bundle.get("explanation") or {}).get("id"),
            "export_id": export.get("id"),
            "preview_id": (bundle.get("preview") or {}).get("id"),
            "release_readiness_id": (bundle.get("release_readiness") or {}).get("id"),
            "handoff_id": (bundle.get("handoff") or {}).get("id"),
            "outcome_id": (bundle.get("outcome") or {}).get("id"),
            "present": present,
            "snapshot_counts": snapshot_counts,
            "unresolved_delivery_issue_count": len(unresolved_issues),
            "completion_score": round((numerator / denominator) * 100),
            "metadata_only_review_enabled": True,
            **self._safety_flags(),
        }

    def _checklist_specs(self, bundle: dict[str, Any]) -> list[dict[str, Any]]:
        coverage = self._coverage_summary(bundle)
        specs = []
        labels = {
            "decision_pack": "Decision pack exists",
            "explanation": "Explanation exists",
            "export": "Export exists",
            "preview": "Preview exists",
            "release_readiness": "Release readiness exists",
            "handoff": "Manual handoff exists",
            "outcome": "Manual outcome exists",
        }
        for key, label in labels.items():
            specs.append({"item_key": key, "label": label, "item_status": "passed" if coverage["present"].get(key) else "failed", "required": True})
        for key, count in coverage["snapshot_counts"].items():
            specs.append({"item_key": key, "label": key.replace("_", " ").title(), "item_status": "passed" if count > 0 else "failed", "required": True})
        specs.append({"item_key": "unresolved_delivery_issues", "label": "No unresolved delivery issues", "item_status": "passed" if coverage["unresolved_delivery_issue_count"] == 0 else "failed", "required": True})
        return specs

    def _finding_specs(self, bundle: dict[str, Any]) -> list[dict[str, Any]]:
        specs = []
        coverage = self._coverage_summary(bundle)
        finding_by_key = {
            "decision_pack": "missing_decision_pack",
            "explanation": "missing_explanation",
            "export": "missing_export",
            "preview": "missing_preview",
            "release_readiness": "missing_release_readiness",
            "handoff": "missing_handoff",
            "outcome": "missing_outcome",
        }
        for key, present in coverage["present"].items():
            if not present:
                specs.append({"finding_type": finding_by_key[key], "severity": "high", "title": f"Missing {key.replace('_', ' ')} metadata", "description": "Lifecycle audit review could not locate this required metadata record."})
        for key, count in coverage["snapshot_counts"].items():
            if count == 0:
                specs.append({"finding_type": "missing_immutable_snapshot", "severity": "medium", "title": f"Missing {key.replace('_', ' ')}", "description": "Lifecycle audit review could not locate immutable snapshot coverage for this stage.", "source_entity_type": key})
        for issue in [item for item in bundle.get("delivery_issues") or [] if item.get("issue_status") != "resolved"]:
            specs.append({"finding_type": "unresolved_delivery_issue", "severity": "high", "title": issue.get("title") or "Unresolved delivery issue", "description": issue.get("description"), "source_entity_type": "delivery_issue", "source_entity_id": issue.get("id")})
        return specs

    async def _refresh_review_counts(self, agency_id: str, review_id: str) -> dict[str, Any] | None:
        findings = await self.list_findings(agency_id=agency_id, review_id=review_id)
        checklist = await self.list_checklist_items(agency_id=agency_id, review_id=review_id)
        snapshots = await self.list_snapshots(agency_id=agency_id, review_id=review_id)
        passed = len([item for item in checklist if item.get("item_status") in {"passed", "not_applicable"}])
        denominator = max(len(checklist), 1)
        return await self.db.collection(REVIEW_COLLECTION).update_one(
            {"agency_id": agency_id, "id": review_id},
            {
                "finding_count": len(findings),
                "unresolved_finding_count": len([item for item in findings if item.get("finding_status") == "open"]),
                "checklist_count": len(checklist),
                "passed_checklist_count": passed,
                "snapshot_count": len(snapshots),
                "completion_score": round((passed / denominator) * 100),
            },
        )

    async def _list_records(self, collection_name: str, **filters: Any) -> list[dict[str, Any]]:
        query = {key: value for key, value in filters.items() if value is not None}
        items = await self.db.collection(collection_name).find_many(query or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _find_one(self, collection_name: str, filters: dict[str, Any]) -> dict[str, Any] | None:
        return await self.db.collection(collection_name).find_one(filters)

    async def _optional_record(self, collection_name: str, agency_id: str, record_id: str | None) -> dict[str, Any] | None:
        if not record_id:
            return None
        return await self.db.collection(collection_name).find_one({"agency_id": agency_id, "id": record_id})

    async def _require_record(self, collection_name: str, agency_id: str, record_id: str, message: str) -> dict[str, Any]:
        record = await self.db.collection(collection_name).find_one({"agency_id": agency_id, "id": record_id})
        if not record:
            raise ValueError(message)
        return record

    async def _require_review(self, agency_id: str, review_id: str) -> dict[str, Any]:
        return await self._require_record(REVIEW_COLLECTION, agency_id, review_id, "Audit review not found.")

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only_review_enabled": True,
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_price_mutation_disabled": True,
            "automatic_recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
        }
