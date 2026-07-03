from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionExportArchiveStatus,
    OfferDecisionExportArchiveStatusCreateRequest,
    OfferDecisionExportArchiveStatusUpdateRequest,
    OfferDecisionExportGovernanceException,
    OfferDecisionExportGovernanceExceptionCreateRequest,
    OfferDecisionExportGovernanceExceptionUpdateRequest,
    OfferDecisionExportGovernanceRecord,
    OfferDecisionExportGovernanceRecordCreateRequest,
    OfferDecisionExportGovernanceRecordUpdateRequest,
    OfferDecisionExportGovernanceRule,
    OfferDecisionExportGovernanceRuleCreateRequest,
    OfferDecisionExportGovernanceRuleUpdateRequest,
    OfferDecisionExportGovernanceSnapshot,
    OfferDecisionExportGovernanceSnapshotCreateRequest,
    OfferDecisionExportLegalBasis,
    OfferDecisionExportLegalBasisCreateRequest,
    OfferDecisionExportLegalBasisUpdateRequest,
    OfferDecisionExportRetentionPolicy,
    OfferDecisionExportRetentionPolicyCreateRequest,
    OfferDecisionExportRetentionPolicyUpdateRequest,
    now_utc,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_38_1_offer_decision_export_governance_foundation"

RECORD_COLLECTION = "offer_decision_export_governance_records"
RULE_COLLECTION = "offer_decision_export_governance_rules"
RETENTION_COLLECTION = "offer_decision_export_retention_policies"
LEGAL_BASIS_COLLECTION = "offer_decision_export_legal_bases"
ARCHIVE_STATUS_COLLECTION = "offer_decision_export_archive_statuses"
EXCEPTION_COLLECTION = "offer_decision_export_governance_exceptions"
SNAPSHOT_COLLECTION = "offer_decision_export_governance_snapshots"

AUDIT_REVIEW_COLLECTION = "offer_decision_export_audit_reviews"
EXPORT_COLLECTION = "offer_decision_exports"
OUTCOME_COLLECTION = "offer_decision_export_delivery_outcomes"


class OfferDecisionExportGovernanceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "governance_record_count": len(await self.list_records(agency_id=agency_id)),
            "rule_count": len(await self.list_rules(agency_id=agency_id)),
            "retention_policy_count": len(await self.list_retention_policies(agency_id=agency_id)),
            "legal_basis_count": len(await self.list_legal_bases(agency_id=agency_id)),
            "archive_status_count": len(await self.list_archive_statuses(agency_id=agency_id)),
            "exception_count": len(await self.list_exceptions(agency_id=agency_id)),
            "snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "governance_records_enabled": True,
            "governance_rules_enabled": True,
            "retention_policies_enabled": True,
            "legal_bases_enabled": True,
            "archive_status_metadata_enabled": True,
            "governance_exceptions_enabled": True,
            "immutable_governance_snapshots_enabled": True,
            "agency_governance_ui_enabled": True,
            "platform_governance_ui_enabled": True,
            "metadata_only_governance_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 38.1 offer decision export governance records are metadata-only. They record governance rules, retention policy metadata, legal basis metadata, archive status metadata, exceptions, and immutable snapshots without delivery, offer or price mutation, recommendation, booking, PNR mutation, ticketing, EMD issuance, payment, invoice, settlement, scraping, external AI, or provider execution.",
        }

    async def create_record(
        self,
        agency_id: str,
        payload: OfferDecisionExportGovernanceRecordCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        source = await self._source_summary(agency_id, data)
        record = OfferDecisionExportGovernanceRecord(
            agency_id=agency_id,
            governance_scope=data.get("governance_scope") or "export_lifecycle",
            title=data.get("title") or f"Governance metadata for export {source.get('export_id') or 'review'}",
            export_id=source.get("export_id"),
            audit_review_id=source.get("audit_review_id"),
            decision_pack_id=source.get("decision_pack_id"),
            outcome_id=source.get("outcome_id"),
            owner_label=data.get("owner_label") or actor_from_user(user),
            policy_summary_json={**source, **(data.get("policy_summary_json") or {})},
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(RECORD_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {"governance_record": stored, **self._safety_flags()}

    async def update_record(
        self,
        agency_id: str,
        record_id: str,
        payload: OfferDecisionExportGovernanceRecordUpdateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        record = await self._require_record(agency_id, record_id)
        updated = await self.db.collection(RECORD_COLLECTION).update_one(
            {"agency_id": agency_id, "id": record_id},
            {
                "governance_status": enum_value(data["governance_status"]),
                "status_reason": data.get("status_reason"),
                "owner_label": data.get("owner_label") or record.get("owner_label"),
                "policy_summary_json": {**(record.get("policy_summary_json") or {}), **(data.get("policy_summary_json") or {})},
                "metadata_json": {**(record.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        return {"governance_record": updated or record, **self._safety_flags()}

    async def list_records(
        self,
        *,
        agency_id: str | None = None,
        export_id: str | None = None,
        audit_review_id: str | None = None,
        governance_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(RECORD_COLLECTION, agency_id=agency_id, export_id=export_id, audit_review_id=audit_review_id, governance_status=governance_status)

    async def get_record(self, record_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": record_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(RECORD_COLLECTION).find_one(filters)

    async def get_record_detail(self, record_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        record = await self.get_record(record_id, agency_id)
        if not record:
            return None
        return {
            "governance_record": record,
            "rules": await self.list_rules(agency_id=agency_id, governance_record_id=record_id),
            "retention_policies": await self.list_retention_policies(agency_id=agency_id, governance_record_id=record_id),
            "legal_bases": await self.list_legal_bases(agency_id=agency_id, governance_record_id=record_id),
            "archive_statuses": await self.list_archive_statuses(agency_id=agency_id, governance_record_id=record_id),
            "governance_exceptions": await self.list_exceptions(agency_id=agency_id, governance_record_id=record_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, governance_record_id=record_id),
            **self._safety_flags(),
        }

    async def create_rule(self, agency_id: str, record_id: str, payload: OfferDecisionExportGovernanceRuleCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_record(agency_id, record_id)
        rule = OfferDecisionExportGovernanceRule(agency_id=agency_id, governance_record_id=record_id, **data)
        stored = await self.db.collection(RULE_COLLECTION).insert_one(rule.model_dump(mode="json"))
        refreshed = await self._refresh_record_counts(agency_id, record_id)
        return {"governance_record": refreshed, "rule": stored, **self._safety_flags()}

    async def update_rule(self, agency_id: str, rule_id: str, payload: OfferDecisionExportGovernanceRuleUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        rule = await self._require_child(RULE_COLLECTION, agency_id, rule_id, "Governance rule not found.")
        updated = await self.db.collection(RULE_COLLECTION).update_one(
            {"agency_id": agency_id, "id": rule_id},
            {
                "rule_status": enum_value(data["rule_status"]),
                "rule_text": data.get("rule_text", rule.get("rule_text")),
                "effective_to": data.get("effective_to", rule.get("effective_to")),
                "metadata_json": {**(rule.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_record_counts(agency_id, rule.get("governance_record_id"))
        return {"governance_record": refreshed, "rule": updated or rule, **self._safety_flags()}

    async def list_rules(self, *, agency_id: str | None = None, governance_record_id: str | None = None, rule_status: str | None = None, rule_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(RULE_COLLECTION, agency_id=agency_id, governance_record_id=governance_record_id, rule_status=rule_status, rule_type=rule_type)

    async def create_retention_policy(self, agency_id: str, record_id: str, payload: OfferDecisionExportRetentionPolicyCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_record(agency_id, record_id)
        policy = OfferDecisionExportRetentionPolicy(agency_id=agency_id, governance_record_id=record_id, **data)
        stored = await self.db.collection(RETENTION_COLLECTION).insert_one(policy.model_dump(mode="json"))
        refreshed = await self._refresh_record_counts(agency_id, record_id)
        return {"governance_record": refreshed, "retention_policy": stored, **self._safety_flags()}

    async def update_retention_policy(self, agency_id: str, policy_id: str, payload: OfferDecisionExportRetentionPolicyUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        policy = await self._require_child(RETENTION_COLLECTION, agency_id, policy_id, "Retention policy metadata not found.")
        updated = await self.db.collection(RETENTION_COLLECTION).update_one(
            {"agency_id": agency_id, "id": policy_id},
            {
                "retention_action": enum_value(data["retention_action"]),
                "review_required": data.get("review_required", policy.get("review_required", True)),
                "notes": data.get("notes", policy.get("notes")),
                "metadata_json": {**(policy.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_record_counts(agency_id, policy.get("governance_record_id"))
        return {"governance_record": refreshed, "retention_policy": updated or policy, **self._safety_flags()}

    async def list_retention_policies(self, *, agency_id: str | None = None, governance_record_id: str | None = None, retention_action: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(RETENTION_COLLECTION, agency_id=agency_id, governance_record_id=governance_record_id, retention_action=retention_action)

    async def create_legal_basis(self, agency_id: str, record_id: str, payload: OfferDecisionExportLegalBasisCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_record(agency_id, record_id)
        basis = OfferDecisionExportLegalBasis(agency_id=agency_id, governance_record_id=record_id, **data)
        stored = await self.db.collection(LEGAL_BASIS_COLLECTION).insert_one(basis.model_dump(mode="json"))
        refreshed = await self._refresh_record_counts(agency_id, record_id)
        return {"governance_record": refreshed, "legal_basis": stored, **self._safety_flags()}

    async def update_legal_basis(self, agency_id: str, basis_id: str, payload: OfferDecisionExportLegalBasisUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        basis = await self._require_child(LEGAL_BASIS_COLLECTION, agency_id, basis_id, "Legal basis metadata not found.")
        updated = await self.db.collection(LEGAL_BASIS_COLLECTION).update_one(
            {"agency_id": agency_id, "id": basis_id},
            {
                "notes": data.get("notes", basis.get("notes")),
                "evidence_reference_metadata": data.get("evidence_reference_metadata", basis.get("evidence_reference_metadata")),
                "metadata_json": {**(basis.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_record_counts(agency_id, basis.get("governance_record_id"))
        return {"governance_record": refreshed, "legal_basis": updated or basis, **self._safety_flags()}

    async def list_legal_bases(self, *, agency_id: str | None = None, governance_record_id: str | None = None, basis_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(LEGAL_BASIS_COLLECTION, agency_id=agency_id, governance_record_id=governance_record_id, basis_type=basis_type)

    async def create_archive_status(self, agency_id: str, record_id: str, payload: OfferDecisionExportArchiveStatusCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        record = await self._require_record(agency_id, record_id)
        status = OfferDecisionExportArchiveStatus(
            agency_id=agency_id,
            governance_record_id=record_id,
            export_id=record.get("export_id"),
            archive_status=data.get("archive_status") or "not_archived",
            status_reason=data.get("status_reason"),
            reviewed_by=data.get("reviewed_by") or actor_from_user(user),
            reviewed_at=now_utc(),
            archive_reference_metadata=data.get("archive_reference_metadata"),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(ARCHIVE_STATUS_COLLECTION).insert_one(status.model_dump(mode="json"))
        refreshed = await self._refresh_record_counts(agency_id, record_id)
        return {"governance_record": refreshed, "archive_status": stored, **self._safety_flags()}

    async def update_archive_status(self, agency_id: str, status_id: str, payload: OfferDecisionExportArchiveStatusUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        status = await self._require_child(ARCHIVE_STATUS_COLLECTION, agency_id, status_id, "Archive status metadata not found.")
        updated = await self.db.collection(ARCHIVE_STATUS_COLLECTION).update_one(
            {"agency_id": agency_id, "id": status_id},
            {
                "archive_status": enum_value(data["archive_status"]),
                "status_reason": data.get("status_reason"),
                "reviewed_by": data.get("reviewed_by") or actor_from_user(user) or status.get("reviewed_by"),
                "reviewed_at": now_utc(),
                "archive_reference_metadata": data.get("archive_reference_metadata", status.get("archive_reference_metadata")),
                "metadata_json": {**(status.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_record_counts(agency_id, status.get("governance_record_id"))
        return {"governance_record": refreshed, "archive_status": updated or status, **self._safety_flags()}

    async def list_archive_statuses(self, *, agency_id: str | None = None, governance_record_id: str | None = None, archive_status: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(ARCHIVE_STATUS_COLLECTION, agency_id=agency_id, governance_record_id=governance_record_id, archive_status=archive_status)

    async def create_exception(self, agency_id: str, record_id: str, payload: OfferDecisionExportGovernanceExceptionCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_record(agency_id, record_id)
        exception = OfferDecisionExportGovernanceException(agency_id=agency_id, governance_record_id=record_id, **data)
        stored = await self.db.collection(EXCEPTION_COLLECTION).insert_one(exception.model_dump(mode="json"))
        refreshed = await self._refresh_record_counts(agency_id, record_id)
        return {"governance_record": refreshed, "governance_exception": stored, **self._safety_flags()}

    async def update_exception(self, agency_id: str, exception_id: str, payload: OfferDecisionExportGovernanceExceptionUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        exception = await self._require_child(EXCEPTION_COLLECTION, agency_id, exception_id, "Governance exception metadata not found.")
        resolved = enum_value(data["exception_status"]) in {"resolved", "waived", "accepted"}
        updated = await self.db.collection(EXCEPTION_COLLECTION).update_one(
            {"agency_id": agency_id, "id": exception_id},
            {
                "exception_status": enum_value(data["exception_status"]),
                "resolved_by": data.get("resolved_by") or (actor_from_user(user) if resolved else exception.get("resolved_by")),
                "resolved_at": now_utc() if resolved else None,
                "resolution_notes": data.get("resolution_notes"),
                "metadata_json": {**(exception.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_record_counts(agency_id, exception.get("governance_record_id"))
        return {"governance_record": refreshed, "governance_exception": updated or exception, **self._safety_flags()}

    async def list_exceptions(self, *, agency_id: str | None = None, governance_record_id: str | None = None, exception_status: str | None = None, exception_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(EXCEPTION_COLLECTION, agency_id=agency_id, governance_record_id=governance_record_id, exception_status=exception_status, exception_type=exception_type)

    async def create_snapshot(self, agency_id: str, record_id: str, payload: OfferDecisionExportGovernanceSnapshotCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        detail = await self.get_record_detail(record_id, agency_id)
        if not detail:
            raise ValueError("Governance record not found.")
        snapshot = OfferDecisionExportGovernanceSnapshot(
            agency_id=agency_id,
            governance_record_id=record_id,
            snapshot_type=data.get("snapshot_type") or "governance_created",
            payload={
                **detail,
                "safety_flags": self._safety_flags(),
                "metadata_json": data.get("metadata_json") or {},
            },
            created_by=data.get("created_by") or actor_from_user(user),
        )
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        refreshed = await self._refresh_record_counts(agency_id, record_id)
        return {"governance_record": refreshed, "snapshot": stored, **self._safety_flags()}

    async def list_snapshots(self, *, agency_id: str | None = None, governance_record_id: str | None = None, snapshot_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(SNAPSHOT_COLLECTION, agency_id=agency_id, governance_record_id=governance_record_id, snapshot_type=snapshot_type)

    async def _source_summary(self, agency_id: str, data: dict[str, Any]) -> dict[str, Any]:
        audit_review = await self._optional_record(AUDIT_REVIEW_COLLECTION, agency_id, data.get("audit_review_id"))
        export_id = data.get("export_id") or (audit_review or {}).get("export_id")
        outcome_id = data.get("outcome_id") or (audit_review or {}).get("outcome_id")
        export = await self._optional_record(EXPORT_COLLECTION, agency_id, export_id)
        outcome = await self._optional_record(OUTCOME_COLLECTION, agency_id, outcome_id)
        return {
            "audit_review_id": (audit_review or {}).get("id"),
            "export_id": (export or {}).get("id") or export_id,
            "decision_pack_id": (export or {}).get("decision_pack_id") or (audit_review or {}).get("decision_pack_id"),
            "outcome_id": (outcome or {}).get("id") or outcome_id,
            "audit_review_status": (audit_review or {}).get("review_status"),
            "export_status": (export or {}).get("export_status"),
            "outcome_status": (outcome or {}).get("outcome_status"),
            "metadata_only_governance_enabled": True,
            **self._safety_flags(),
        }

    async def _refresh_record_counts(self, agency_id: str, record_id: str | None) -> dict[str, Any] | None:
        if not record_id:
            return None
        exceptions = await self.list_exceptions(agency_id=agency_id, governance_record_id=record_id)
        return await self.db.collection(RECORD_COLLECTION).update_one(
            {"agency_id": agency_id, "id": record_id},
            {
                "rule_count": len(await self.list_rules(agency_id=agency_id, governance_record_id=record_id)),
                "retention_policy_count": len(await self.list_retention_policies(agency_id=agency_id, governance_record_id=record_id)),
                "legal_basis_count": len(await self.list_legal_bases(agency_id=agency_id, governance_record_id=record_id)),
                "archive_status_count": len(await self.list_archive_statuses(agency_id=agency_id, governance_record_id=record_id)),
                "exception_count": len(exceptions),
                "open_exception_count": len([item for item in exceptions if item.get("exception_status") == "open"]),
                "snapshot_count": len(await self.list_snapshots(agency_id=agency_id, governance_record_id=record_id)),
            },
        )

    async def _list_records(self, collection_name: str, **filters: Any) -> list[dict[str, Any]]:
        query = {key: value for key, value in filters.items() if value is not None}
        items = await self.db.collection(collection_name).find_many(query or None)
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def _optional_record(self, collection_name: str, agency_id: str, record_id: str | None) -> dict[str, Any] | None:
        if not record_id:
            return None
        return await self.db.collection(collection_name).find_one({"agency_id": agency_id, "id": record_id})

    async def _require_record(self, agency_id: str, record_id: str) -> dict[str, Any]:
        record = await self.db.collection(RECORD_COLLECTION).find_one({"agency_id": agency_id, "id": record_id})
        if not record:
            raise ValueError("Governance record not found.")
        return record

    async def _require_child(self, collection_name: str, agency_id: str, record_id: str, message: str) -> dict[str, Any]:
        record = await self.db.collection(collection_name).find_one({"agency_id": agency_id, "id": record_id})
        if not record:
            raise ValueError(message)
        return record

    def _safety_flags(self) -> dict[str, bool]:
        return {
            "automatic_sending_disabled": True,
            "sms_sending_disabled": True,
            "public_links_disabled": True,
            "real_pdf_delivery_disabled": True,
            "offer_mutation_disabled": True,
            "price_mutation_disabled": True,
            "offer_price_mutation_disabled": True,
            "recommendation_disabled": True,
            "automatic_recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "ticket_emd_issuance_disabled": True,
            "emd_issuance_disabled": True,
            "payment_disabled": True,
            "invoice_disabled": True,
            "settlement_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "scraping_disabled": True,
            "external_ai_disabled": True,
        }
