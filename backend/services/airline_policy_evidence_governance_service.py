from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineEvidenceAccessClassification,
    AirlineEvidenceArtifact,
    AirlineEvidenceAssertion,
    AirlineEvidenceConflict,
    AirlineEvidenceFreshnessAssessment,
    AirlineEvidenceLink,
    AirlineEvidenceReview,
    AirlineEvidenceSource,
    AirlineEvidenceSourceCreate,
    AirlineEvidenceSourceUpdate,
    AuditEvent,
    new_id,
)


PHASE_LABEL = "phase_55_3_airline_knowledge_versioning_change_detection_foundation"

SOURCE_COLLECTION = "airline_evidence_sources"
ARTIFACT_COLLECTION = "airline_evidence_artifacts"
ASSERTION_COLLECTION = "airline_evidence_assertions"
LINK_COLLECTION = "airline_evidence_links"
REVIEW_COLLECTION = "airline_evidence_reviews"
CONFLICT_COLLECTION = "airline_evidence_conflicts"
FRESHNESS_COLLECTION = "airline_evidence_freshness_assessments"
ACCESS_COLLECTION = "airline_evidence_access_classifications"

EVIDENCE_COLLECTIONS = [
    SOURCE_COLLECTION,
    ARTIFACT_COLLECTION,
    ASSERTION_COLLECTION,
    LINK_COLLECTION,
    REVIEW_COLLECTION,
    CONFLICT_COLLECTION,
    FRESHNESS_COLLECTION,
    ACCESS_COLLECTION,
]

SOURCE_TYPES = [
    "airline_public_website",
    "airline_conditions_of_carriage",
    "airline_tariff",
    "airline_agent_manual",
    "gds_help_page",
    "gds_cryptic_response",
    "airline_operational_bulletin",
    "airline_trade_communication",
    "airline_email_confirmation",
    "airline_support_desk_response",
    "airport_handling_response",
    "internal_operational_observation",
    "historical_case_evidence",
    "regulator_government_source",
    "iata_industry_publication",
    "supplier_consolidator_instruction",
    "screenshot",
    "pdf_manual",
    "structured_import",
    "api_response",
]

CONFLICT_STATUSES = ["detected", "under_review", "accepted_variant", "superseded", "unresolved", "resolved", "archived"]
PUBLIC_EVIDENCE_STATUSES = {"approved", "published", "verified"}
AGENCY_ACCESS_LEVELS = {"agency_visible", "published_reference", "public"}
RAW_SOURCE_COLLECTIONS = {"airline_policy_sources", "airline_knowledge_acquisitions", "airline_knowledge_sources"}

TARGET_COLLECTIONS = {
    "airline_profile": "airline_master_profiles",
    "airline_profile_field": "airline_master_profiles",
    "airline_policy": "visual_policy_editor_cards",
    "pricing_formula": "pricing_formula_builders",
    "operational_rule": "operational_rule_composer_rules",
    "capability_matrix": "airline_capability_matrix",
    "distribution_fact": "airline_distribution_profiles",
    "pss_fact": "airline_pss_parameters",
    "gds_fact": "airline_gds_parameters",
    "interline_codeshare_rule": "airline_interline_agreements",
    "contact": "airline_contacts",
    "published_knowledge": "airline_knowledge_publications",
    "knowledge_item": "airline_knowledge_items",
}

AUTHORITY_SCORES = {
    "airline_direct_confirmation": 95,
    "regulator": 95,
    "official_airline_controlled": 90,
    "industry_authoritative": 85,
    "contractual_trade": 80,
    "supplier_instruction": 70,
    "operational_observation": 55,
    "historical_case": 45,
    "unknown": 25,
}

SOURCE_AUTHORITY_DEFAULTS = {
    "airline_conditions_of_carriage": "official_airline_controlled",
    "airline_tariff": "official_airline_controlled",
    "airline_agent_manual": "official_airline_controlled",
    "airline_public_website": "official_airline_controlled",
    "airline_operational_bulletin": "official_airline_controlled",
    "airline_email_confirmation": "airline_direct_confirmation",
    "airline_support_desk_response": "airline_direct_confirmation",
    "airport_handling_response": "airline_direct_confirmation",
    "regulator_government_source": "regulator",
    "iata_industry_publication": "industry_authoritative",
    "airline_trade_communication": "contractual_trade",
    "gds_help_page": "contractual_trade",
    "gds_cryptic_response": "contractual_trade",
    "supplier_consolidator_instruction": "supplier_instruction",
    "internal_operational_observation": "operational_observation",
    "historical_case_evidence": "historical_case",
}


class AirlinePolicyEvidenceGovernanceError(ValueError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def stable_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


class AirlinePolicyEvidenceGovernanceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "canonical_evidence_governance_enabled": True,
            "raw_source_truth_preserved": True,
            "normalized_assertions_separate": True,
            "conflicting_sources_preserved": True,
            "physical_evidence_deletion_disabled": True,
            "agency_read_only": True,
            "restricted_evidence_protected": True,
            "automatic_production_seeding_disabled": True,
            "automatic_extraction_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "provider_execution_disabled": True,
            "ai_disabled": True,
            "metadata_only": True,
        }

    async def list_sources(
        self,
        *,
        agency_id: str | None = None,
        airline_id: str | None = None,
        source_type: str | None = None,
        evidence_status: str | None = None,
        freshness_status: str | None = None,
        agency_safe: bool = False,
    ) -> list[dict[str, Any]]:
        sources = await self.db.collection(SOURCE_COLLECTION).find_many()
        results: list[dict[str, Any]] = []
        for source in sources:
            if airline_id and source.get("canonical_airline_id") != airline_id:
                continue
            if source_type and source.get("source_type") != source_type:
                continue
            if evidence_status and source.get("evidence_status") != evidence_status:
                continue
            if agency_safe and not await self._agency_can_see_source(source, agency_id):
                continue
            freshness = await self.latest_freshness(source_id=source["id"])
            if freshness_status and (freshness or {}).get("freshness_status") != freshness_status:
                continue
            results.append(await self._source_projection(source, freshness, agency_safe=agency_safe))
        return sorted(results, key=lambda item: str(item.get("captured_at") or ""), reverse=True)

    async def get_source(self, source_id: str, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        source = await self._require(SOURCE_COLLECTION, source_id, "Evidence source")
        if agency_safe and not await self._agency_can_see_source(source, agency_id):
            raise AirlinePolicyEvidenceGovernanceError("Approved agency-visible evidence source was not found.")
        return await self._source_projection(source, await self.latest_freshness(source_id=source["id"]), agency_safe=agency_safe)

    async def create_source(self, payload: AirlineEvidenceSourceCreate, user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_source(data)
        if data.get("canonical_airline_id"):
            await self._require_canonical_airline(data["canonical_airline_id"])
        if data.get("raw_source_collection"):
            if data["raw_source_collection"] not in RAW_SOURCE_COLLECTIONS:
                raise AirlinePolicyEvidenceGovernanceError("Raw source collection is not an approved evidence intake collection.")
            if not data.get("raw_source_record_id"):
                raise AirlinePolicyEvidenceGovernanceError("Raw source record id is required when an intake collection is linked.")
            if not await self.db.collection(data["raw_source_collection"]).find_one({"id": data["raw_source_record_id"]}):
                raise AirlinePolicyEvidenceGovernanceError("Linked raw source record was not found; source truth cannot be replaced by a copy.")
        data.setdefault("source_reference", f"AES-{new_id()[:8].upper()}")
        data.setdefault("authority_level", self.assess_authority(data.get("source_type")))
        data.setdefault("captured_at", datetime.now(timezone.utc))
        created = await self.db.collection(SOURCE_COLLECTION).insert_one(AirlineEvidenceSource(**data).model_dump(mode="json"))
        await self.assess_freshness(source_id=created["id"], actor_user_id=user.get("id"))
        await self._audit("airline_evidence.source_created", created["id"], user, {"source_reference": created["source_reference"]})
        return await self.get_source(created["id"])

    async def update_source(self, source_id: str, payload: AirlineEvidenceSourceUpdate, user: dict[str, Any]) -> dict[str, Any]:
        source = await self._require(SOURCE_COLLECTION, source_id, "Evidence source")
        updates = payload_dict(payload)
        if not updates:
            raise AirlinePolicyEvidenceGovernanceError("At least one evidence source field is required.")
        updated = await self.db.collection(SOURCE_COLLECTION).update_one({"id": source["id"]}, updates)
        await self.assess_freshness(source_id=source["id"], actor_user_id=user.get("id"))
        await self._audit("airline_evidence.source_updated", source["id"], user, {"changed_fields": sorted(updates)})
        return await self.get_source(updated["id"])

    async def archive_source(self, source_id: str, user: dict[str, Any]) -> dict[str, Any]:
        source = await self._require(SOURCE_COLLECTION, source_id, "Evidence source")
        updated = await self.db.collection(SOURCE_COLLECTION).update_one(
            {"id": source["id"]},
            {"evidence_status": "archived", "review_decision": "archived", "reviewer_user_id": user.get("id")},
        )
        await self._audit("airline_evidence.source_archived", source["id"], user, {"physical_delete": False})
        return {"source": updated, "archived": True, "physical_delete_disabled": True, **self.safety_flags()}

    async def register_artifact(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        source = await self._require(SOURCE_COLLECTION, str(data.get("source_id") or ""), "Evidence source")
        data.setdefault("artifact_reference", f"AEA-{new_id()[:8].upper()}")
        data["agency_id"] = source.get("agency_id")
        created = await self.db.collection(ARTIFACT_COLLECTION).insert_one(AirlineEvidenceArtifact(**data).model_dump(mode="json"))
        await self._audit("airline_evidence.artifact_registered", created["id"], user, {"source_id": source["id"]})
        return created

    async def create_access_classification(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        code = str(data.get("classification_code") or "").strip().lower()
        if not code:
            raise AirlinePolicyEvidenceGovernanceError("Access classification code is required.")
        if await self.db.collection(ACCESS_COLLECTION).find_one({"classification_code": code}):
            raise AirlinePolicyEvidenceGovernanceError("Access classification code already exists.")
        data["classification_code"] = code
        created = await self.db.collection(ACCESS_COLLECTION).insert_one(AirlineEvidenceAccessClassification(**data).model_dump(mode="json"))
        await self._audit("airline_evidence.access_classification_created", created["id"], user, {"classification_code": code})
        return created

    async def register_assertion(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        source = await self._require(SOURCE_COLLECTION, str(data.get("source_id") or ""), "Evidence source")
        data.setdefault("assertion_reference", f"EAS-{new_id()[:8].upper()}")
        data["agency_id"] = source.get("agency_id")
        data["canonical_airline_id"] = source.get("canonical_airline_id")
        data.setdefault("authority_level", source.get("authority_level") or self.assess_authority(source.get("source_type")))
        if data.get("confidence") in {None, "", "unknown"}:
            confidence = self.calculate_confidence(source, data)
            data["confidence"] = confidence["level"]
        created = await self.db.collection(ASSERTION_COLLECTION).insert_one(AirlineEvidenceAssertion(**data).model_dump(mode="json"))
        conflicts = await self.detect_conflicts(created)
        await self.assess_freshness(assertion_id=created["id"], actor_user_id=user.get("id"))
        await self._audit("airline_evidence.assertion_registered", created["id"], user, {"conflict_count": len(conflicts)})
        return {"assertion": created, "conflicts": conflicts, "confidence": self.calculate_confidence(source, created), **self.safety_flags()}

    async def link_evidence(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        source = await self._require(SOURCE_COLLECTION, str(data.get("source_id") or ""), "Evidence source")
        if data.get("assertion_id"):
            assertion = await self._require(ASSERTION_COLLECTION, data["assertion_id"], "Evidence assertion")
            if assertion.get("source_id") != source["id"]:
                raise AirlinePolicyEvidenceGovernanceError("Evidence assertion does not belong to the selected source.")
        target_type = str(data.get("target_type") or "")
        collection = TARGET_COLLECTIONS.get(target_type)
        if collection is None:
            raise AirlinePolicyEvidenceGovernanceError("Evidence target type is not part of the canonical knowledge graph.")
        if not await self.db.collection(collection).find_one({"id": str(data.get("target_id") or "")}):
            raise AirlinePolicyEvidenceGovernanceError("Evidence target record was not found.")
        data["agency_id"] = source.get("agency_id")
        data["canonical_airline_id"] = source.get("canonical_airline_id")
        duplicate = await self.db.collection(LINK_COLLECTION).find_one(
            {"assertion_id": data.get("assertion_id"), "target_type": target_type, "target_id": data["target_id"]}
        )
        if duplicate:
            return duplicate
        created = await self.db.collection(LINK_COLLECTION).insert_one(AirlineEvidenceLink(**data).model_dump(mode="json"))
        await self._audit("airline_evidence.link_created", created["id"], user, {"target_type": target_type, "target_id": data["target_id"]})
        return created

    async def detect_conflicts(self, assertion: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = await self.db.collection(ASSERTION_COLLECTION).find_many({"assertion_key": assertion["assertion_key"]})
        conflicts: list[dict[str, Any]] = []
        for candidate in candidates:
            if candidate["id"] == assertion["id"]:
                continue
            if candidate.get("canonical_airline_id") != assertion.get("canonical_airline_id"):
                continue
            if candidate.get("superseded") or assertion.get("superseded"):
                continue
            if stable_value(candidate.get("structured_value")) == stable_value(assertion.get("structured_value")):
                continue
            assertion_ids = sorted([candidate["id"], assertion["id"]])
            existing = [
                item
                for item in await self.db.collection(CONFLICT_COLLECTION).find_many({"assertion_key": assertion["assertion_key"]})
                if sorted(item.get("assertion_ids") or []) == assertion_ids and item.get("status") != "archived"
            ]
            if existing:
                conflicts.extend(existing)
                continue
            conflict_type = self._conflict_type(candidate, assertion)
            conflict = AirlineEvidenceConflict(
                agency_id=assertion.get("agency_id") or candidate.get("agency_id"),
                canonical_airline_id=assertion.get("canonical_airline_id"),
                conflict_reference=f"EAC-{new_id()[:8].upper()}",
                conflict_type=conflict_type,
                assertion_key=assertion["assertion_key"],
                source_ids=sorted({candidate["source_id"], assertion["source_id"]}),
                assertion_ids=assertion_ids,
                conflicting_values=[candidate.get("structured_value"), assertion.get("structured_value")],
                distribution_channels=sorted({value for value in [candidate.get("distribution_channel"), assertion.get("distribution_channel")] if value}),
                route_scopes=sorted({value for value in [candidate.get("route_scope"), assertion.get("route_scope")] if value}),
                status="detected",
                source_truth_preserved=True,
            )
            conflicts.append(await self.db.collection(CONFLICT_COLLECTION).insert_one(conflict.model_dump(mode="json")))
        return conflicts

    def _conflict_type(self, first: dict[str, Any], second: dict[str, Any]) -> str:
        if first.get("distribution_channel") != second.get("distribution_channel") and first.get("distribution_channel") and second.get("distribution_channel"):
            return "distribution_channel_difference"
        if first.get("route_scope") != second.get("route_scope") and first.get("route_scope") and second.get("route_scope"):
            return "route_specific_exception"
        if first.get("effective_from") != second.get("effective_from"):
            return "effective_date_conflict"
        if "support" in str(first.get("assertion_key") or ""):
            return "support_status_conflict"
        if "limit" in str(first.get("assertion_key") or ""):
            return "limit_conflict"
        return "assertion_value_conflict"

    async def review_conflict(self, conflict_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        conflict = await self._require(CONFLICT_COLLECTION, conflict_id, "Evidence conflict")
        data = payload_dict(payload)
        next_status = str(data.get("status") or "")
        if next_status not in CONFLICT_STATUSES:
            raise AirlinePolicyEvidenceGovernanceError("Conflict status is not supported.")
        updates = {
            "status": next_status,
            "accepted_assertion_ids": data.get("accepted_assertion_ids") or [],
            "resolution_summary": data.get("resolution_summary"),
            "reviewer_user_id": user.get("id"),
            "reviewed_at": datetime.now(timezone.utc),
            "source_truth_preserved": True,
        }
        updated = await self.db.collection(CONFLICT_COLLECTION).update_one({"id": conflict["id"]}, updates)
        review = AirlineEvidenceReview(
            agency_id=conflict.get("agency_id"),
            conflict_id=conflict["id"],
            review_type="conflict_review",
            review_status="completed" if next_status in {"accepted_variant", "superseded", "resolved", "archived"} else "under_review",
            review_decision=next_status,
            reviewer_user_id=user.get("id"),
            reviewed_at=datetime.now(timezone.utc),
            review_notes=data.get("resolution_summary"),
        )
        await self.db.collection(REVIEW_COLLECTION).insert_one(review.model_dump(mode="json"))
        await self._audit("airline_evidence.conflict_reviewed", conflict["id"], user, {"status": next_status, "source_truth_preserved": True})
        return {"conflict": updated, "source_truth_preserved": True, **self.safety_flags()}

    async def supersede_source(self, source_id: str, replacement_source_id: str, user: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
        source = await self._require(SOURCE_COLLECTION, source_id, "Evidence source")
        replacement = await self._require(SOURCE_COLLECTION, replacement_source_id, "Replacement evidence source")
        if source["id"] == replacement["id"]:
            raise AirlinePolicyEvidenceGovernanceError("An evidence source cannot supersede itself.")
        updated_source = await self.db.collection(SOURCE_COLLECTION).update_one(
            {"id": source["id"]},
            {"superseded": True, "superseded_by_source_id": replacement["id"], "evidence_status": "superseded", "review_decision": reason or "superseded"},
        )
        supersedes = list(dict.fromkeys([*(replacement.get("supersedes_source_ids") or []), source["id"]]))
        updated_replacement = await self.db.collection(SOURCE_COLLECTION).update_one({"id": replacement["id"]}, {"supersedes_source_ids": supersedes})
        await self._audit("airline_evidence.source_superseded", source["id"], user, {"replacement_source_id": replacement["id"], "source_truth_preserved": True})
        return {"superseded_source": updated_source, "replacement_source": updated_replacement, "source_truth_preserved": True, **self.safety_flags()}

    def assess_authority(self, source_type: str | None, explicit_level: str | None = None) -> str:
        return explicit_level or SOURCE_AUTHORITY_DEFAULTS.get(str(source_type or ""), "unknown")

    def calculate_confidence(self, source: dict[str, Any], assertion: dict[str, Any] | None = None) -> dict[str, Any]:
        authority_level = self.assess_authority(source.get("source_type"), (assertion or {}).get("authority_level") or source.get("authority_level"))
        score = AUTHORITY_SCORES.get(authority_level, AUTHORITY_SCORES["unknown"])
        if source.get("checksum"):
            score += 3
        if source.get("effective_from"):
            score += 3
        if source.get("review_decision") in {"approved", "verified", "accepted"}:
            score += 5
        if source.get("superseded"):
            score -= 30
        score = max(0, min(100, score))
        level = "high" if score >= 80 else "medium" if score >= 55 else "low"
        return {"score": score, "level": level, "authority_level": authority_level}

    async def assess_freshness(
        self,
        *,
        source_id: str | None = None,
        assertion_id: str | None = None,
        actor_user_id: str | None = None,
        as_of: date | None = None,
    ) -> dict[str, Any]:
        if not source_id and not assertion_id:
            raise AirlinePolicyEvidenceGovernanceError("Source or assertion is required for freshness assessment.")
        record = await self._require(ASSERTION_COLLECTION if assertion_id else SOURCE_COLLECTION, assertion_id or source_id or "", "Evidence record")
        today = as_of or datetime.now(timezone.utc).date()
        captured = parse_date(record.get("captured_at") or record.get("created_at"))
        review_due = parse_date(record.get("review_due_date"))
        effective_to = parse_date(record.get("effective_to") or record.get("expiry_date"))
        age_days = (today - captured).days if captured else None
        if record.get("superseded"):
            status = "superseded"
            explanation = "Evidence has been superseded but remains retained for audit history."
        elif effective_to and effective_to < today:
            status = "expired"
            explanation = "Evidence effective or expiry date has passed."
        elif review_due and review_due < today:
            status = "review_overdue"
            explanation = "Evidence review date has passed."
        elif review_due and (review_due - today).days <= 30:
            status = "review_due_soon"
            explanation = "Evidence review is due within 30 days."
        elif captured and age_days is not None and age_days <= 365:
            status = "fresh"
            explanation = "Evidence was captured within the last 365 days."
        elif captured:
            status = "stale"
            explanation = "Evidence is older than 365 days and should be reviewed."
        else:
            status = "unknown"
            explanation = "Evidence capture date is unknown."
        assessment = AirlineEvidenceFreshnessAssessment(
            agency_id=record.get("agency_id"),
            source_id=source_id,
            assertion_id=assertion_id,
            freshness_status=status,
            age_days=age_days,
            review_due_date=review_due,
            effective_to=effective_to,
            explanation=explanation,
            assessed_by_user_id=actor_user_id,
        )
        return await self.db.collection(FRESHNESS_COLLECTION).insert_one(assessment.model_dump(mode="json"))

    async def latest_freshness(self, *, source_id: str | None = None, assertion_id: str | None = None) -> dict[str, Any] | None:
        filters = {"source_id": source_id} if source_id else {"assertion_id": assertion_id}
        items = await self.db.collection(FRESHNESS_COLLECTION).find_many(filters)
        return max(items, key=lambda item: str(item.get("assessed_at") or ""), default=None)

    async def unsupported_knowledge(self) -> list[dict[str, Any]]:
        links = await self.db.collection(LINK_COLLECTION).find_many()
        linked = {(item.get("target_type"), item.get("target_id")) for item in links if item.get("link_status") == "active"}
        results: list[dict[str, Any]] = []
        for target_type, collection in TARGET_COLLECTIONS.items():
            for record in await self.db.collection(collection).find_many():
                if (target_type, record.get("id")) in linked:
                    continue
                results.append(
                    {
                        "target_type": target_type,
                        "target_id": record.get("id"),
                        "collection": collection,
                        "airline_id": record.get("canonical_airline_id") or record.get("airline_id") or record.get("airline_code"),
                        "status": "unsupported",
                        "manual_review_required": True,
                    }
                )
        return results

    async def evidence_trace(self, target_type: str, target_id: str, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        links = await self.db.collection(LINK_COLLECTION).find_many({"target_type": target_type, "target_id": target_id})
        if agency_safe:
            links = [item for item in links if item.get("agency_visible") is True]
        assertion_ids = {item.get("assertion_id") for item in links if item.get("assertion_id")}
        source_ids = {item.get("source_id") for item in links if item.get("source_id")}
        assertions = [item for item in await self.db.collection(ASSERTION_COLLECTION).find_many() if item.get("id") in assertion_ids]
        sources = [item for item in await self.db.collection(SOURCE_COLLECTION).find_many() if item.get("id") in source_ids]
        if agency_safe:
            visible_sources = [item for item in sources if await self._agency_can_see_source(item, agency_id)]
            visible_ids = {item["id"] for item in visible_sources}
            sources = visible_sources
            assertions = [item for item in assertions if item.get("source_id") in visible_ids and item.get("evidence_status") in PUBLIC_EVIDENCE_STATUSES]
            visible_assertion_ids = {item["id"] for item in assertions}
            links = [
                item
                for item in links
                if item.get("source_id") in visible_ids
                and (not item.get("assertion_id") or item.get("assertion_id") in visible_assertion_ids)
            ]
            assertion_ids = visible_assertion_ids
        conflicts = [
            item
            for item in await self.db.collection(CONFLICT_COLLECTION).find_many()
            if assertion_ids.intersection(item.get("assertion_ids") or [])
        ]
        if agency_safe:
            agency_conflicts: list[dict[str, Any]] = []
            for item in conflicts:
                if item.get("status") not in {"accepted_variant", "resolved", "superseded"}:
                    continue
                projected = self._safe_record(item) or {}
                projected["source_ids"] = [source_id for source_id in item.get("source_ids") or [] if source_id in visible_ids]
                projected["assertion_ids"] = [assertion_id for assertion_id in item.get("assertion_ids") or [] if assertion_id in assertion_ids]
                projected["accepted_assertion_ids"] = [assertion_id for assertion_id in item.get("accepted_assertion_ids") or [] if assertion_id in assertion_ids]
                agency_conflicts.append(projected)
            conflicts = agency_conflicts
        return {
            "target_type": target_type,
            "target_id": target_id,
            "links": [self._safe_record(item) if agency_safe else item for item in links],
            "assertions": [self._safe_record(item) if agency_safe else item for item in assertions],
            "sources": [await self._source_projection(item, await self.latest_freshness(source_id=item["id"]), agency_safe=agency_safe) for item in sources],
            "conflicts": conflicts,
            "trace_complete": bool(links and assertions and sources),
            "manual_review_required": not bool(links and assertions and sources) or any(item.get("status") in {"detected", "under_review", "unresolved"} for item in conflicts),
            **self.safety_flags(),
        }

    async def coverage(self) -> dict[str, Any]:
        sources = await self.db.collection(SOURCE_COLLECTION).find_many()
        assertions = await self.db.collection(ASSERTION_COLLECTION).find_many()
        conflicts = await self.db.collection(CONFLICT_COLLECTION).find_many()
        freshness = await self.db.collection(FRESHNESS_COLLECTION).find_many()
        unsupported = await self.unsupported_knowledge()
        return {
            "source_count": len(sources),
            "artifact_count": await self.db.collection(ARTIFACT_COLLECTION).count(),
            "assertion_count": len(assertions),
            "evidence_link_count": await self.db.collection(LINK_COLLECTION).count(),
            "conflict_count": len(conflicts),
            "unresolved_conflict_count": len([item for item in conflicts if item.get("status") in {"detected", "under_review", "unresolved"}]),
            "freshness_assessment_count": len(freshness),
            "stale_or_expired_count": len([item for item in freshness if item.get("freshness_status") in {"stale", "expired", "review_overdue"}]),
            "unsupported_knowledge_count": len(unsupported),
            "source_type_counts": {source_type: len([item for item in sources if item.get("source_type") == source_type]) for source_type in SOURCE_TYPES},
            "conflict_status_counts": {status: len([item for item in conflicts if item.get("status") == status]) for status in CONFLICT_STATUSES},
        }

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        sources = await self.list_sources(**filters)
        return {
            "phase": PHASE_LABEL,
            "sources": sources,
            "artifacts": await self.db.collection(ARTIFACT_COLLECTION).find_many(),
            "assertions": await self.db.collection(ASSERTION_COLLECTION).find_many(),
            "links": await self.db.collection(LINK_COLLECTION).find_many(),
            "conflicts": await self.db.collection(CONFLICT_COLLECTION).find_many(),
            "reviews": await self.db.collection(REVIEW_COLLECTION).find_many(),
            "freshness_assessments": await self.db.collection(FRESHNESS_COLLECTION).find_many(),
            "access_classifications": await self.db.collection(ACCESS_COLLECTION).find_many(),
            "unsupported_knowledge": await self.unsupported_knowledge(),
            "coverage": await self.coverage(),
            "source_types": SOURCE_TYPES,
            "conflict_statuses": CONFLICT_STATUSES,
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        sources = await self.list_sources(agency_id=agency_id, agency_safe=True, **filters)
        source_ids = {item["id"] for item in sources}
        assertions = [
            self._safe_record(item)
            for item in await self.db.collection(ASSERTION_COLLECTION).find_many()
            if item.get("source_id") in source_ids and item.get("evidence_status") in PUBLIC_EVIDENCE_STATUSES
        ]
        links = [
            self._safe_record(item)
            for item in await self.db.collection(LINK_COLLECTION).find_many()
            if item.get("source_id") in source_ids and item.get("agency_visible") is True
        ]
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "sources": sources,
            "assertions": assertions,
            "published_evidence_links": links,
            "visible_source_count": len(sources),
            "visible_assertion_count": len(assertions),
            "visible_link_count": len(links),
            "read_only": True,
            **self.safety_flags(),
        }

    async def _source_projection(self, source: dict[str, Any], freshness: dict[str, Any] | None, *, agency_safe: bool) -> dict[str, Any]:
        projected = self._safe_record(source) if agency_safe else dict(source)
        projected["authority_assessment"] = self.calculate_confidence(source)
        projected["freshness"] = self._safe_record(freshness) if agency_safe else freshness
        projected["read_only"] = agency_safe
        return projected

    async def _agency_can_see_source(self, source: dict[str, Any], agency_id: str | None) -> bool:
        if source.get("agency_id") and source.get("agency_id") != agency_id:
            return False
        if source.get("evidence_status") not in PUBLIC_EVIDENCE_STATUSES:
            return False
        classification_id = source.get("access_classification_id")
        if classification_id:
            classification = await self.db.collection(ACCESS_COLLECTION).find_one({"id": classification_id})
            return bool(classification and classification.get("agency_visible") and not classification.get("internal_only"))
        return source.get("accessibility") in AGENCY_ACCESS_LEVELS

    def _safe_record(self, record: dict[str, Any] | None) -> dict[str, Any] | None:
        if record is None:
            return None
        restricted = {
            "internal_notes",
            "review_notes",
            "reviewer_user_id",
            "assessed_by_user_id",
            "storage_reference",
            "raw_source_collection",
            "raw_source_record_id",
            "checksum",
            "source_url",
            "conflicting_values",
        }
        return {key: value for key, value in record.items() if key not in restricted}

    def _validate_source(self, data: dict[str, Any]) -> None:
        if data.get("source_type") not in SOURCE_TYPES:
            raise AirlinePolicyEvidenceGovernanceError("Evidence source type is not supported.")
        if data.get("scope") not in {"platform", "agency"}:
            raise AirlinePolicyEvidenceGovernanceError("Evidence scope must be platform or agency.")
        if data.get("scope") == "agency" and not data.get("agency_id"):
            raise AirlinePolicyEvidenceGovernanceError("Agency-scoped evidence requires agency_id.")
        if data.get("effective_from") and data.get("effective_to") and parse_date(data["effective_from"]) > parse_date(data["effective_to"]):
            raise AirlinePolicyEvidenceGovernanceError("Evidence effective_from must not be after effective_to.")

    async def _require_canonical_airline(self, airline_id: str) -> dict[str, Any]:
        airline = await self.db.collection("airline_profiles").find_one({"id": airline_id})
        if not airline:
            raise AirlinePolicyEvidenceGovernanceError("Canonical airline identity was not found.")
        return airline

    async def _require(self, collection: str, record_id: str, label: str) -> dict[str, Any]:
        record = await self.db.collection(collection).find_one({"id": record_id})
        if not record:
            raise AirlinePolicyEvidenceGovernanceError(f"{label} was not found.")
        return record

    async def _audit(self, event_type: str, entity_id: str, user: dict[str, Any], metadata: dict[str, Any]) -> None:
        event = AuditEvent(
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="airline_policy_evidence_governance",
            entity_id=entity_id,
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata=metadata,
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))
