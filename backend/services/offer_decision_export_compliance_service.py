from __future__ import annotations

from typing import Any

from database import Database
from models import (
    OfferDecisionExportComplianceCheck,
    OfferDecisionExportComplianceCheckCreateRequest,
    OfferDecisionExportComplianceCheckUpdateRequest,
    OfferDecisionExportComplianceEvidence,
    OfferDecisionExportComplianceEvidenceCreateRequest,
    OfferDecisionExportComplianceEvidenceUpdateRequest,
    OfferDecisionExportComplianceException,
    OfferDecisionExportComplianceExceptionCreateRequest,
    OfferDecisionExportComplianceExceptionUpdateRequest,
    OfferDecisionExportComplianceRequirement,
    OfferDecisionExportComplianceRequirementCreateRequest,
    OfferDecisionExportComplianceRequirementUpdateRequest,
    OfferDecisionExportComplianceResult,
    OfferDecisionExportComplianceResultCreateRequest,
    OfferDecisionExportComplianceResultUpdateRequest,
    OfferDecisionExportComplianceSnapshot,
    OfferDecisionExportComplianceSnapshotCreateRequest,
    now_utc,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_38_2_offer_decision_export_compliance_foundation"

EVIDENCE_COLLECTION = "offer_decision_export_compliance_evidence"
REQUIREMENT_COLLECTION = "offer_decision_export_compliance_requirements"
CHECK_COLLECTION = "offer_decision_export_compliance_checks"
RESULT_COLLECTION = "offer_decision_export_compliance_results"
EXCEPTION_COLLECTION = "offer_decision_export_compliance_exceptions"
SNAPSHOT_COLLECTION = "offer_decision_export_compliance_snapshots"

GOVERNANCE_COLLECTION = "offer_decision_export_governance_records"
AUDIT_REVIEW_COLLECTION = "offer_decision_export_audit_reviews"
EXPORT_COLLECTION = "offer_decision_exports"
OUTCOME_COLLECTION = "offer_decision_export_delivery_outcomes"


class OfferDecisionExportComplianceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "evidence_count": len(await self.list_evidence(agency_id=agency_id)),
            "requirement_count": len(await self.list_requirements(agency_id=agency_id)),
            "check_count": len(await self.list_checks(agency_id=agency_id)),
            "result_count": len(await self.list_results(agency_id=agency_id)),
            "exception_count": len(await self.list_exceptions(agency_id=agency_id)),
            "snapshot_count": len(await self.list_snapshots(agency_id=agency_id)),
            "compliance_evidence_enabled": True,
            "compliance_requirements_enabled": True,
            "compliance_checks_enabled": True,
            "compliance_results_enabled": True,
            "compliance_exceptions_enabled": True,
            "immutable_compliance_snapshots_enabled": True,
            "agency_compliance_ui_enabled": True,
            "platform_compliance_ui_enabled": True,
            "metadata_only_enabled": True,
            **self._safety_flags(),
            "diagnostic": "Phase 38.2 offer decision export compliance evidence records are metadata-only. They document requirements, checks, pass/fail result metadata, exceptions, and immutable snapshots without delivery, offer or price mutation, recommendation, booking, PNR mutation, ticketing, EMD issuance, payment, invoice, settlement, scraping, external AI, GDS execution, or provider execution.",
        }

    async def create_evidence(
        self,
        agency_id: str,
        payload: OfferDecisionExportComplianceEvidenceCreateRequest | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        source = await self._source_summary(agency_id, data)
        evidence = OfferDecisionExportComplianceEvidence(
            agency_id=agency_id,
            evidence_scope=data.get("evidence_scope") or "governance_record",
            title=data.get("title") or f"Compliance evidence for export {source.get('export_id') or 'governance'}",
            governance_record_id=source.get("governance_record_id"),
            audit_review_id=source.get("audit_review_id"),
            export_id=source.get("export_id"),
            decision_pack_id=source.get("decision_pack_id"),
            outcome_id=source.get("outcome_id"),
            owner_label=data.get("owner_label") or actor_from_user(user),
            evidence_summary_json={**source, **(data.get("evidence_summary_json") or {})},
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(EVIDENCE_COLLECTION).insert_one(evidence.model_dump(mode="json"))
        return {"evidence": stored, **self._safety_flags()}

    async def update_evidence(
        self,
        agency_id: str,
        evidence_id: str,
        payload: OfferDecisionExportComplianceEvidenceUpdateRequest | dict[str, Any],
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        evidence = await self._require_evidence(agency_id, evidence_id)
        updated = await self.db.collection(EVIDENCE_COLLECTION).update_one(
            {"agency_id": agency_id, "id": evidence_id},
            {
                "evidence_status": enum_value(data["evidence_status"]),
                "status_reason": data.get("status_reason"),
                "owner_label": data.get("owner_label") or evidence.get("owner_label"),
                "evidence_summary_json": {**(evidence.get("evidence_summary_json") or {}), **(data.get("evidence_summary_json") or {})},
                "metadata_json": {**(evidence.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        return {"evidence": updated or evidence, **self._safety_flags()}

    async def list_evidence(
        self,
        *,
        agency_id: str | None = None,
        governance_record_id: str | None = None,
        audit_review_id: str | None = None,
        evidence_status: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._list_records(EVIDENCE_COLLECTION, agency_id=agency_id, governance_record_id=governance_record_id, audit_review_id=audit_review_id, evidence_status=evidence_status)

    async def get_evidence(self, evidence_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": evidence_id}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(EVIDENCE_COLLECTION).find_one(filters)

    async def get_evidence_detail(self, evidence_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        evidence = await self.get_evidence(evidence_id, agency_id)
        if not evidence:
            return None
        return {
            "evidence": evidence,
            "requirements": await self.list_requirements(agency_id=agency_id, evidence_id=evidence_id),
            "checks": await self.list_checks(agency_id=agency_id, evidence_id=evidence_id),
            "results": await self.list_results(agency_id=agency_id, evidence_id=evidence_id),
            "exceptions": await self.list_exceptions(agency_id=agency_id, evidence_id=evidence_id),
            "snapshots": await self.list_snapshots(agency_id=agency_id, evidence_id=evidence_id),
            **self._safety_flags(),
        }

    async def create_requirement(self, agency_id: str, evidence_id: str, payload: OfferDecisionExportComplianceRequirementCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_evidence(agency_id, evidence_id)
        requirement = OfferDecisionExportComplianceRequirement(agency_id=agency_id, evidence_id=evidence_id, **data)
        stored = await self.db.collection(REQUIREMENT_COLLECTION).insert_one(requirement.model_dump(mode="json"))
        refreshed = await self._refresh_evidence_counts(agency_id, evidence_id)
        return {"evidence": refreshed, "requirement": stored, **self._safety_flags()}

    async def update_requirement(self, agency_id: str, requirement_id: str, payload: OfferDecisionExportComplianceRequirementUpdateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        requirement = await self._require_child(REQUIREMENT_COLLECTION, agency_id, requirement_id, "Compliance requirement not found.")
        updated = await self.db.collection(REQUIREMENT_COLLECTION).update_one(
            {"agency_id": agency_id, "id": requirement_id},
            {
                "requirement_status": enum_value(data["requirement_status"]),
                "description": data.get("description", requirement.get("description")),
                "source_reference_metadata": data.get("source_reference_metadata", requirement.get("source_reference_metadata")),
                "required": data.get("required", requirement.get("required", True)),
                "metadata_json": {**(requirement.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_evidence_counts(agency_id, requirement.get("evidence_id"))
        return {"evidence": refreshed, "requirement": updated or requirement, **self._safety_flags()}

    async def list_requirements(self, *, agency_id: str | None = None, evidence_id: str | None = None, requirement_status: str | None = None, requirement_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(REQUIREMENT_COLLECTION, agency_id=agency_id, evidence_id=evidence_id, requirement_status=requirement_status, requirement_type=requirement_type)

    async def create_check(self, agency_id: str, evidence_id: str, payload: OfferDecisionExportComplianceCheckCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_evidence(agency_id, evidence_id)
        if data.get("requirement_id"):
            await self._require_child(REQUIREMENT_COLLECTION, agency_id, data["requirement_id"], "Compliance requirement not found.")
        check_status = enum_value(data.get("check_status") or "not_started")
        check = OfferDecisionExportComplianceCheck(
            agency_id=agency_id,
            evidence_id=evidence_id,
            requirement_id=data.get("requirement_id"),
            check_type=data.get("check_type") or "other",
            check_status=check_status,
            check_name=data["check_name"],
            check_metadata_json=data.get("check_metadata_json") or {},
            performed_by=data.get("performed_by") or (actor_from_user(user) if check_status != "not_started" else None),
            performed_at=now_utc() if check_status != "not_started" else None,
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(CHECK_COLLECTION).insert_one(check.model_dump(mode="json"))
        refreshed = await self._refresh_evidence_counts(agency_id, evidence_id)
        return {"evidence": refreshed, "check": stored, **self._safety_flags()}

    async def update_check(self, agency_id: str, check_id: str, payload: OfferDecisionExportComplianceCheckUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        check = await self._require_child(CHECK_COLLECTION, agency_id, check_id, "Compliance check not found.")
        updated = await self.db.collection(CHECK_COLLECTION).update_one(
            {"agency_id": agency_id, "id": check_id},
            {
                "check_status": enum_value(data["check_status"]),
                "check_metadata_json": {**(check.get("check_metadata_json") or {}), **(data.get("check_metadata_json") or {})},
                "performed_by": data.get("performed_by") or actor_from_user(user) or check.get("performed_by"),
                "performed_at": now_utc(),
                "metadata_json": {**(check.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_evidence_counts(agency_id, check.get("evidence_id"))
        return {"evidence": refreshed, "check": updated or check, **self._safety_flags()}

    async def list_checks(self, *, agency_id: str | None = None, evidence_id: str | None = None, requirement_id: str | None = None, check_status: str | None = None, check_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(CHECK_COLLECTION, agency_id=agency_id, evidence_id=evidence_id, requirement_id=requirement_id, check_status=check_status, check_type=check_type)

    async def create_result(self, agency_id: str, evidence_id: str, payload: OfferDecisionExportComplianceResultCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_evidence(agency_id, evidence_id)
        if data.get("requirement_id"):
            await self._require_child(REQUIREMENT_COLLECTION, agency_id, data["requirement_id"], "Compliance requirement not found.")
        if data.get("check_id"):
            await self._require_child(CHECK_COLLECTION, agency_id, data["check_id"], "Compliance check not found.")
        result = OfferDecisionExportComplianceResult(
            agency_id=agency_id,
            evidence_id=evidence_id,
            requirement_id=data.get("requirement_id"),
            check_id=data.get("check_id"),
            result_status=data.get("result_status") or "warning",
            result_name=data["result_name"],
            result_summary=data.get("result_summary"),
            evidence_reference_metadata=data.get("evidence_reference_metadata"),
            evaluated_by=data.get("evaluated_by") or actor_from_user(user),
            evaluated_at=now_utc(),
            metadata_json=data.get("metadata_json") or {},
        )
        stored = await self.db.collection(RESULT_COLLECTION).insert_one(result.model_dump(mode="json"))
        refreshed = await self._refresh_evidence_counts(agency_id, evidence_id)
        return {"evidence": refreshed, "result": stored, **self._safety_flags()}

    async def update_result(self, agency_id: str, result_id: str, payload: OfferDecisionExportComplianceResultUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        result = await self._require_child(RESULT_COLLECTION, agency_id, result_id, "Compliance result not found.")
        updated = await self.db.collection(RESULT_COLLECTION).update_one(
            {"agency_id": agency_id, "id": result_id},
            {
                "result_status": enum_value(data["result_status"]),
                "result_summary": data.get("result_summary", result.get("result_summary")),
                "evidence_reference_metadata": data.get("evidence_reference_metadata", result.get("evidence_reference_metadata")),
                "evaluated_by": data.get("evaluated_by") or actor_from_user(user) or result.get("evaluated_by"),
                "evaluated_at": now_utc(),
                "metadata_json": {**(result.get("metadata_json") or {}), **(data.get("metadata_json") or {})},
            },
        )
        refreshed = await self._refresh_evidence_counts(agency_id, result.get("evidence_id"))
        return {"evidence": refreshed, "result": updated or result, **self._safety_flags()}

    async def list_results(self, *, agency_id: str | None = None, evidence_id: str | None = None, requirement_id: str | None = None, check_id: str | None = None, result_status: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(RESULT_COLLECTION, agency_id=agency_id, evidence_id=evidence_id, requirement_id=requirement_id, check_id=check_id, result_status=result_status)

    async def create_exception(self, agency_id: str, evidence_id: str, payload: OfferDecisionExportComplianceExceptionCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_evidence(agency_id, evidence_id)
        if data.get("requirement_id"):
            await self._require_child(REQUIREMENT_COLLECTION, agency_id, data["requirement_id"], "Compliance requirement not found.")
        if data.get("check_id"):
            await self._require_child(CHECK_COLLECTION, agency_id, data["check_id"], "Compliance check not found.")
        exception = OfferDecisionExportComplianceException(agency_id=agency_id, evidence_id=evidence_id, **data)
        stored = await self.db.collection(EXCEPTION_COLLECTION).insert_one(exception.model_dump(mode="json"))
        refreshed = await self._refresh_evidence_counts(agency_id, evidence_id)
        return {"evidence": refreshed, "exception": stored, **self._safety_flags()}

    async def update_exception(self, agency_id: str, exception_id: str, payload: OfferDecisionExportComplianceExceptionUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        exception = await self._require_child(EXCEPTION_COLLECTION, agency_id, exception_id, "Compliance exception metadata not found.")
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
        refreshed = await self._refresh_evidence_counts(agency_id, exception.get("evidence_id"))
        return {"evidence": refreshed, "exception": updated or exception, **self._safety_flags()}

    async def list_exceptions(self, *, agency_id: str | None = None, evidence_id: str | None = None, exception_status: str | None = None, exception_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(EXCEPTION_COLLECTION, agency_id=agency_id, evidence_id=evidence_id, exception_status=exception_status, exception_type=exception_type)

    async def create_snapshot(self, agency_id: str, evidence_id: str, payload: OfferDecisionExportComplianceSnapshotCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        detail = await self.get_evidence_detail(evidence_id, agency_id)
        if not detail:
            raise ValueError("Compliance evidence not found.")
        snapshot = OfferDecisionExportComplianceSnapshot(
            agency_id=agency_id,
            evidence_id=evidence_id,
            snapshot_type=data.get("snapshot_type") or "evidence_created",
            payload={
                **detail,
                "safety_flags": self._safety_flags(),
                "metadata_json": data.get("metadata_json") or {},
            },
            created_by=data.get("created_by") or actor_from_user(user),
        )
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        refreshed = await self._refresh_evidence_counts(agency_id, evidence_id)
        return {"evidence": refreshed, "snapshot": stored, **self._safety_flags()}

    async def list_snapshots(self, *, agency_id: str | None = None, evidence_id: str | None = None, snapshot_type: str | None = None) -> list[dict[str, Any]]:
        return await self._list_records(SNAPSHOT_COLLECTION, agency_id=agency_id, evidence_id=evidence_id, snapshot_type=snapshot_type)

    async def _source_summary(self, agency_id: str, data: dict[str, Any]) -> dict[str, Any]:
        governance_record = await self._optional_record(GOVERNANCE_COLLECTION, agency_id, data.get("governance_record_id"))
        audit_review_id = data.get("audit_review_id") or (governance_record or {}).get("audit_review_id")
        export_id = data.get("export_id") or (governance_record or {}).get("export_id")
        outcome_id = data.get("outcome_id") or (governance_record or {}).get("outcome_id")
        audit_review = await self._optional_record(AUDIT_REVIEW_COLLECTION, agency_id, audit_review_id)
        export = await self._optional_record(EXPORT_COLLECTION, agency_id, export_id or (audit_review or {}).get("export_id"))
        outcome = await self._optional_record(OUTCOME_COLLECTION, agency_id, outcome_id or (audit_review or {}).get("outcome_id"))
        return {
            "governance_record_id": (governance_record or {}).get("id"),
            "governance_status": (governance_record or {}).get("governance_status"),
            "audit_review_id": (audit_review or {}).get("id") or audit_review_id,
            "audit_review_status": (audit_review or {}).get("review_status"),
            "export_id": (export or {}).get("id") or export_id,
            "export_status": (export or {}).get("export_status"),
            "decision_pack_id": (export or {}).get("decision_pack_id") or (audit_review or {}).get("decision_pack_id") or (governance_record or {}).get("decision_pack_id"),
            "outcome_id": (outcome or {}).get("id") or outcome_id,
            "outcome_status": (outcome or {}).get("outcome_status"),
            "metadata_only_enabled": True,
            **self._safety_flags(),
        }

    async def _refresh_evidence_counts(self, agency_id: str, evidence_id: str | None) -> dict[str, Any] | None:
        if not evidence_id:
            return None
        checks = await self.list_checks(agency_id=agency_id, evidence_id=evidence_id)
        exceptions = await self.list_exceptions(agency_id=agency_id, evidence_id=evidence_id)
        return await self.db.collection(EVIDENCE_COLLECTION).update_one(
            {"agency_id": agency_id, "id": evidence_id},
            {
                "requirement_count": len(await self.list_requirements(agency_id=agency_id, evidence_id=evidence_id)),
                "check_count": len(checks),
                "result_count": len(await self.list_results(agency_id=agency_id, evidence_id=evidence_id)),
                "failed_check_count": len([item for item in checks if item.get("check_status") == "failed"]),
                "exception_count": len(exceptions),
                "open_exception_count": len([item for item in exceptions if item.get("exception_status") == "open"]),
                "snapshot_count": len(await self.list_snapshots(agency_id=agency_id, evidence_id=evidence_id)),
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

    async def _require_evidence(self, agency_id: str, evidence_id: str) -> dict[str, Any]:
        evidence = await self.db.collection(EVIDENCE_COLLECTION).find_one({"agency_id": agency_id, "id": evidence_id})
        if not evidence:
            raise ValueError("Compliance evidence not found.")
        return evidence

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
