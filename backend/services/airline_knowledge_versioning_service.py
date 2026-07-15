from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineKnowledgeChangeReview,
    AirlineKnowledgeChangeSet,
    AirlineKnowledgeFieldChange,
    AirlineKnowledgeImpactAssessment,
    AirlineKnowledgeRevalidationRequest,
    AirlineKnowledgeVersion,
    AirlineKnowledgeVersionItem,
    AuditEvent,
    new_id,
)


PHASE_LABEL = "phase_56_3_journey_comparison_client_presentation_foundation"

VERSION_COLLECTION = "airline_knowledge_versions"
VERSION_ITEM_COLLECTION = "airline_knowledge_version_items"
CHANGE_SET_COLLECTION = "airline_knowledge_change_sets"
FIELD_CHANGE_COLLECTION = "airline_knowledge_field_changes"
IMPACT_ASSESSMENT_COLLECTION = "airline_knowledge_impact_assessments"
CHANGE_REVIEW_COLLECTION = "airline_knowledge_change_reviews"
REVALIDATION_REQUEST_COLLECTION = "airline_knowledge_revalidation_requests"

VERSIONING_COLLECTIONS = [
    VERSION_COLLECTION,
    VERSION_ITEM_COLLECTION,
    CHANGE_SET_COLLECTION,
    FIELD_CHANGE_COLLECTION,
    IMPACT_ASSESSMENT_COLLECTION,
    CHANGE_REVIEW_COLLECTION,
    REVALIDATION_REQUEST_COLLECTION,
]

CHANGE_CATEGORIES = [
    "added",
    "modified",
    "removed",
    "superseded",
    "effective_date_change",
    "restriction_increased",
    "restriction_reduced",
    "pricing_increase",
    "pricing_decrease",
    "support_status_change",
    "document_requirement_change",
    "approval_requirement_change",
    "distribution_change",
    "contact_change",
    "evidence_only_change",
]

VERSIONED_OBJECT_COLLECTIONS = {
    "airline_profile": "airline_master_profiles",
    "airline_policy": "visual_policy_editor_cards",
    "structured_policy_json": "visual_policy_editor_cards",
    "operational_rule": "operational_rule_composer_rules",
    "pricing_formula": "pricing_formula_builders",
    "capability_row": "airline_capability_matrix",
    "evidence_assertion": "airline_evidence_assertions",
    "service_instruction": "airline_policy_extracted_communication_rules",
    "ssr_osi_template": "ssr_osi_templates",
    "emd_rfic_rfisc_rule": "airline_policy_extracted_emd_rules",
    "distribution_capability": "airline_distribution_profiles",
    "contact": "airline_contacts",
    "service_desk": "airline_service_desk_summaries",
    "published_knowledge_package": "airline_knowledge_publications",
}

DISTRIBUTION_VERSIONED_OBJECT_COLLECTIONS = {
    "distribution_channel": "airline_distribution_channels",
    "distribution_capability_detail": "airline_distribution_capabilities",
    "pss_profile": "airline_pss_profiles",
    "gds_participation": "airline_gds_participations",
    "ndc_capability": "airline_ndc_capabilities",
    "fulfillment_capability": "airline_fulfillment_capabilities",
    "servicing_capability": "airline_servicing_capabilities",
    "distribution_restriction": "airline_distribution_restrictions",
    "carrier_relationship": "airline_carrier_relationships",
    "interline_agreement_profile": "airline_interline_agreement_profiles",
    "codeshare_rule": "airline_codeshare_rules",
    "operating_carrier_policy_rule": "airline_operating_carrier_policy_rules",
    "validating_carrier_rule": "airline_validating_carrier_rules",
    "through_check_rule": "airline_through_check_rules",
    "baggage_responsibility_rule": "airline_baggage_responsibility_rules",
    "service_responsibility_rule": "airline_service_responsibility_rules",
    "interline_emd_rule": "airline_interline_emd_rules",
    "fare_family": "airline_fare_families",
    "fare_brand_attribute": "airline_fare_brand_attributes",
    "booking_class_mapping": "airline_booking_class_mappings",
    "baggage_allowance_rule": "airline_baggage_allowance_rules",
    "baggage_exception": "airline_baggage_exceptions",
    "commercial_bundle": "airline_commercial_bundles",
    "brand_comparison_profile": "airline_brand_comparison_profiles",
    "contact_channel": "airline_contact_channels",
    "contact_scope": "airline_contact_scopes",
    "contact_availability": "airline_contact_availabilities",
    "contact_escalation_path": "airline_contact_escalation_paths",
    "communication_template": "airline_communication_templates",
    "communication_requirement": "airline_communication_requirements",
}

ALL_VERSIONED_OBJECT_COLLECTIONS = {
    **VERSIONED_OBJECT_COLLECTIONS,
    **DISTRIBUTION_VERSIONED_OBJECT_COLLECTIONS,
}

IMPACT_TARGET_COLLECTIONS = {
    "published_release": ["airline_knowledge_releases", "airline_knowledge_publications"],
    "scenario_test": ["operational_scenario_tests"],
    "policy_comparison": ["airline_policy_comparison_snapshots", "airline_policy_comparison_rows"],
    "recommendation": ["airline_recommendations"],
    "active_offer": ["offer_workspaces_v2", "intelligent_offer_builder_packages"],
    "booking_readiness_package": ["booking_readiness_packages", "offer_booking_handoffs"],
    "passenger_service_case": ["passenger_service_workflows", "operational_intelligence_cases"],
    "agency_knowledge_assignment": ["airline_intelligence_agency_knowledge_assignment_views"],
    "future_trip": ["trip_workspaces"],
    "unresolved_case": ["after_sales_cases"],
}

SEVERITY_ORDER = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
PUBLIC_VERSION_STATUSES = {"published", "effective"}
PUBLIC_RELEASE_STATUSES = {"published", "effective", "released"}
STORAGE_METADATA_FIELDS = {"_id", "created_at", "updated_at", "created_by", "updated_by"}


class AirlineKnowledgeVersioningError(ValueError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


def json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def snapshot_hash(snapshot: dict[str, Any]) -> str:
    return hashlib.sha256(stable_json(snapshot).encode("utf-8")).hexdigest()


def scalar_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "string"


class AirlineKnowledgeVersioningService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "canonical_airline_knowledge_version_reused": True,
            "structured_change_detection_enabled": True,
            "historical_snapshot_immutability_enabled": True,
            "historical_snapshot_mutation_disabled": True,
            "automatic_operational_mutation_disabled": True,
            "automatic_republication_disabled": True,
            "automatic_recommendation_mutation_disabled": True,
            "agency_published_updates_read_only": True,
            "unpublished_draft_agency_visibility_disabled": True,
            "restricted_source_details_protected": True,
            "metadata_only": True,
        }

    async def create_version(self, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        items_payload = data.pop("items", None)
        if not isinstance(items_payload, list) or not items_payload:
            raise AirlineKnowledgeVersioningError("At least one canonical knowledge object is required for a version snapshot.")
        previous = None
        if data.get("previous_version_id"):
            previous = await self._require(VERSION_COLLECTION, data["previous_version_id"], "Previous knowledge version")
        reference = str(data.get("knowledge_version_reference") or f"AKV-{new_id()[:8].upper()}")
        if await self.db.collection(VERSION_COLLECTION).find_one({"knowledge_version_reference": reference}):
            raise AirlineKnowledgeVersioningError("Knowledge version reference already exists.")

        agency_id = data.get("agency_id")
        canonical_airline_id = data.get("canonical_airline_id")
        prepared_items: list[dict[str, Any]] = []
        for item_payload in items_payload:
            prepared = await self._prepare_version_item(item_payload, agency_id=agency_id, canonical_airline_id=canonical_airline_id)
            if agency_id and prepared.get("agency_id") and prepared["agency_id"] != agency_id:
                raise AirlineKnowledgeVersioningError("A version cannot include a canonical object owned by another agency.")
            prepared_items.append(prepared)
        item_agencies = self._unique([item.get("agency_id") for item in prepared_items])
        item_airlines = self._unique([item.get("canonical_airline_id") for item in prepared_items])
        if not agency_id and len(item_agencies) == 1:
            agency_id = item_agencies[0]
        if len(item_agencies) > 1:
            raise AirlineKnowledgeVersioningError("A version cannot combine canonical objects from multiple agencies.")
        if not canonical_airline_id and len(item_airlines) == 1:
            canonical_airline_id = item_airlines[0]
        if canonical_airline_id and any(value != canonical_airline_id for value in item_airlines):
            raise AirlineKnowledgeVersioningError("A version cannot combine canonical objects from different airline identities.")
        item_keys = [f"{item['object_type']}:{item['source_entity_id']}" for item in prepared_items]
        if len(item_keys) != len(set(item_keys)):
            raise AirlineKnowledgeVersioningError("A canonical knowledge object can appear only once in a version snapshot.")

        existing_versions = await self.db.collection(VERSION_COLLECTION).find_many(
            {"canonical_airline_id": canonical_airline_id} if canonical_airline_id else None
        )
        affected_airlines = self._unique(
            data.get("affected_airline_codes") or [self._airline_code(item["snapshot_json"]) for item in prepared_items]
        )
        affected_services = self._unique(
            data.get("affected_service_families") or [item.get("service_family") for item in prepared_items]
        )
        affected_routes = self._unique(data.get("affected_route_scopes") or [item.get("route_scope") for item in prepared_items])
        triggering_source_ids = self._unique(
            [*(data.get("triggering_source_ids") or []), *[value for item in prepared_items for value in item.get("triggering_source_ids") or []]]
        )
        evidence_assertion_ids = self._unique(
            [*(data.get("evidence_assertion_ids") or []), *[value for item in prepared_items for value in item.get("evidence_assertion_ids") or []]]
        )
        release_ids = self._unique(data.get("published_release_ids") or [])
        lifecycle_status = str(data.get("lifecycle_status") or "draft")
        version = AirlineKnowledgeVersion(
            agency_id=agency_id,
            canonical_airline_id=canonical_airline_id,
            knowledge_version_reference=reference,
            version_number=int(data.get("version_number") or len(existing_versions) + 1),
            version_label=data.get("version_label") or reference,
            semantic_version=data.get("semantic_version"),
            lifecycle_status=lifecycle_status,
            draft_created_at=datetime.now(timezone.utc),
            published_at=data.get("published_at") if lifecycle_status in PUBLIC_VERSION_STATUSES else None,
            effective_from=data.get("effective_from"),
            effective_until=data.get("effective_until"),
            author=data.get("author") or user.get("email") or user.get("id"),
            review_status=data.get("review_status") or "not_started",
            approval_status=data.get("approval_status") or "not_requested",
            publication_channel=data.get("publication_channel"),
            publication_scope=data.get("publication_scope"),
            knowledge_scope=sorted({item["object_type"] for item in prepared_items}),
            evidence_ids=triggering_source_ids,
            previous_version_id=(previous or {}).get("id"),
            change_type=data.get("change_type") or ("modified" if previous else "added"),
            change_description=data.get("change_description"),
            change_reason=data.get("change_reason"),
            snapshot_schema_version="1.0",
            triggering_source_ids=triggering_source_ids,
            evidence_assertion_ids=evidence_assertion_ids,
            published_release_ids=release_ids,
            affected_airline_codes=affected_airlines,
            affected_service_families=affected_services,
            affected_route_scopes=affected_routes,
            version_item_count=len(prepared_items),
            historical_snapshot_immutable=True,
            internal_notes=data.get("internal_notes"),
            created_by=user.get("id"),
            metadata=data.get("metadata") or {},
        )
        stored_version = await self.db.collection(VERSION_COLLECTION).insert_one(version.model_dump(mode="json"))
        stored_items: list[dict[str, Any]] = []
        for prepared in prepared_items:
            prepared["version_id"] = stored_version["id"]
            stored_items.append(
                await self.db.collection(VERSION_ITEM_COLLECTION).insert_one(
                    AirlineKnowledgeVersionItem(**prepared).model_dump(mode="json")
                )
            )
        await self._audit("airline_knowledge_versioning.version_created", stored_version["id"], user, {"item_count": len(stored_items)})
        change_set = None
        if previous and data.get("detect_changes", True):
            change_set = await self.compare_versions(previous["id"], stored_version["id"], user)
        return {
            "phase": PHASE_LABEL,
            "version": stored_version,
            "items": stored_items,
            "change_set": change_set,
            **self.safety_flags(),
        }

    async def _prepare_version_item(
        self,
        payload: dict[str, Any],
        *,
        agency_id: str | None,
        canonical_airline_id: str | None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        object_type = str(data.get("object_type") or "")
        collection = ALL_VERSIONED_OBJECT_COLLECTIONS.get(object_type)
        if not collection:
            raise AirlineKnowledgeVersioningError("Knowledge object type is not registered for canonical versioning.")
        if data.get("source_collection") and data["source_collection"] != collection:
            raise AirlineKnowledgeVersioningError("Knowledge object collection must match the canonical object registry.")
        source_entity_id = str(data.get("source_entity_id") or "")
        source = await self._require(collection, source_entity_id, "Canonical knowledge object")
        source_agency_id = source.get("agency_id") or agency_id
        source_airline_id = source.get("canonical_airline_id") or canonical_airline_id
        snapshot = json_copy(source)
        return {
            "version_id": "pending",
            "agency_id": source_agency_id,
            "canonical_airline_id": source_airline_id,
            "object_type": object_type,
            "source_collection": collection,
            "source_entity_id": source_entity_id,
            "object_reference": data.get("object_reference") or self._record_reference(source),
            "service_family": data.get("service_family") or source.get("service_family") or source.get("policy_family"),
            "route_scope": data.get("route_scope") or source.get("route_scope"),
            "effective_from": data.get("effective_from") or source.get("effective_from") or source.get("effective_date"),
            "effective_until": data.get("effective_until") or source.get("effective_until") or source.get("effective_to"),
            "triggering_source_ids": self._unique(data.get("triggering_source_ids") or source.get("source_reference_ids") or source.get("evidence_ids") or []),
            "evidence_assertion_ids": self._unique(data.get("evidence_assertion_ids") or source.get("evidence_assertion_ids") or []),
            "snapshot_json": snapshot,
            "snapshot_hash": snapshot_hash(snapshot),
            "publication_status": str(data.get("publication_status") or source.get("publication_status") or source.get("lifecycle_status") or "draft"),
            "published_release_ids": self._unique(data.get("published_release_ids") or source.get("published_release_ids") or []),
            "historical_snapshot_immutable": True,
        }

    async def compare_versions(self, base_version_id: str, target_version_id: str, user: dict[str, Any]) -> dict[str, Any]:
        base = await self._require(VERSION_COLLECTION, base_version_id, "Base knowledge version")
        target = await self._require(VERSION_COLLECTION, target_version_id, "Target knowledge version")
        if base.get("agency_id") != target.get("agency_id") or base.get("canonical_airline_id") != target.get("canonical_airline_id"):
            raise AirlineKnowledgeVersioningError("Knowledge versions must share agency and canonical airline scope before comparison.")
        existing = await self.db.collection(CHANGE_SET_COLLECTION).find_one(
            {"base_version_id": base["id"], "target_version_id": target["id"]}
        )
        if existing:
            return await self.get_change_set(existing["id"])

        base_items = await self.db.collection(VERSION_ITEM_COLLECTION).find_many({"version_id": base["id"]})
        target_items = await self.db.collection(VERSION_ITEM_COLLECTION).find_many({"version_id": target["id"]})
        raw_changes = self._compare_version_items(base_items, target_items)
        release_ids = await self._published_release_ids(target)
        categories = sorted({item["change_category"] for item in raw_changes})
        highest_severity = self._highest_severity([item["severity"] for item in raw_changes])
        re_qa_required = bool([item for item in raw_changes if item["change_category"] != "evidence_only_change"])
        republish_required = bool(raw_changes and (release_ids or target.get("lifecycle_status") in PUBLIC_VERSION_STATUSES))
        agency_visible = bool(target.get("lifecycle_status") in PUBLIC_VERSION_STATUSES or release_ids)
        change_set = AirlineKnowledgeChangeSet(
            change_set_reference=f"AKC-{new_id()[:8].upper()}",
            agency_id=target.get("agency_id"),
            canonical_airline_id=target.get("canonical_airline_id"),
            base_version_id=base["id"],
            target_version_id=target["id"],
            triggering_source_ids=self._unique(target.get("triggering_source_ids") or target.get("evidence_ids") or []),
            published_release_ids=release_ids,
            change_categories=categories,
            change_summary=self._change_summary(raw_changes),
            machine_diff_json={"field_changes": raw_changes, "comparison_algorithm": "structured_recursive_v1"},
            field_change_count=len(raw_changes),
            highest_severity=highest_severity,
            affected_airline_codes=self._unique(target.get("affected_airline_codes") or []),
            affected_service_families=self._unique(target.get("affected_service_families") or []),
            affected_route_scopes=self._unique(target.get("affected_route_scopes") or []),
            re_qa_required=re_qa_required,
            republish_required=republish_required,
            agency_visible=agency_visible,
            review_status="pending",
            effective_from=target.get("effective_from"),
            rollback_version_id=base["id"],
            historical_snapshots_unchanged=True,
        )
        stored_change_set = await self.db.collection(CHANGE_SET_COLLECTION).insert_one(change_set.model_dump(mode="json"))
        stored_changes: list[dict[str, Any]] = []
        for item in raw_changes:
            stored_changes.append(
                await self.db.collection(FIELD_CHANGE_COLLECTION).insert_one(
                    AirlineKnowledgeFieldChange(
                        change_set_id=stored_change_set["id"],
                        agency_id=stored_change_set.get("agency_id"),
                        canonical_airline_id=stored_change_set.get("canonical_airline_id"),
                        **item,
                    ).model_dump(mode="json")
                )
            )
        impacts = await self._assess_impact(stored_change_set, base, target, base_items, target_items)
        stored_change_set = await self.db.collection(CHANGE_SET_COLLECTION).update_one(
            {"id": stored_change_set["id"]},
            {"potentially_affected_operation_count": len(impacts)},
        )
        change_set_ids = self._unique([*(target.get("change_set_ids") or []), stored_change_set["id"]])
        await self.db.collection(VERSION_COLLECTION).update_one(
            {"id": target["id"]},
            {
                "change_set_ids": change_set_ids,
                "comparison_base_version_id": base["id"],
                "comparison_target_version_id": target["id"],
            },
        )
        revalidations = await self._create_revalidation_requests(stored_change_set, user)
        await self._audit(
            "airline_knowledge_versioning.change_detected",
            stored_change_set["id"],
            user,
            {"field_change_count": len(stored_changes), "impact_count": len(impacts), "historical_snapshots_unchanged": True},
        )
        return {
            "change_set": stored_change_set,
            "field_changes": stored_changes,
            "impact_assessments": impacts,
            "revalidation_requests": revalidations,
            **self.safety_flags(),
        }

    def structured_diff(self, before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
        current_path = path or "$"
        if isinstance(before, dict) and isinstance(after, dict):
            changes: list[dict[str, Any]] = []
            keys = sorted((set(before) | set(after)) - STORAGE_METADATA_FIELDS)
            for key in keys:
                child_path = f"{path}.{key}" if path else key
                if key not in before:
                    changes.append(self._field_change(child_path, "added", None, after[key]))
                elif key not in after:
                    changes.append(self._field_change(child_path, "removed", before[key], None))
                else:
                    changes.extend(self.structured_diff(before[key], after[key], child_path))
            return changes
        if isinstance(before, list) and isinstance(after, list):
            return self._list_diff(before, after, current_path)
        if stable_json(before) == stable_json(after):
            return []
        return [self._field_change(current_path, "modified", before, after)]

    def _list_diff(self, before: list[Any], after: list[Any], path: str) -> list[dict[str, Any]]:
        if all(isinstance(item, dict) for item in [*before, *after]):
            before_map = {self._list_item_key(item, index): item for index, item in enumerate(before)}
            after_map = {self._list_item_key(item, index): item for index, item in enumerate(after)}
            changes: list[dict[str, Any]] = []
            for key in sorted(set(before_map) | set(after_map)):
                item_path = f"{path}[{key}]"
                if key not in before_map:
                    changes.append(self._field_change(item_path, "added", None, after_map[key]))
                elif key not in after_map:
                    changes.append(self._field_change(item_path, "removed", before_map[key], None))
                else:
                    changes.extend(self.structured_diff(before_map[key], after_map[key], item_path))
            return changes
        before_values = {stable_json(value): value for value in before}
        after_values = {stable_json(value): value for value in after}
        changes = [self._field_change(f"{path}[-]", "removed", before_values[key], None) for key in sorted(set(before_values) - set(after_values))]
        changes.extend(self._field_change(f"{path}[+]", "added", None, after_values[key]) for key in sorted(set(after_values) - set(before_values)))
        return changes

    def _list_item_key(self, item: dict[str, Any], index: int) -> str:
        for key in [
            "id",
            "reference",
            "rule_reference",
            "formula_reference",
            "fare_component_reference",
            "service_code",
            "ssr_code",
            "document_type",
            "approval_type",
            "code",
            "name",
        ]:
            if item.get(key) not in {None, ""}:
                return f"{key}={item[key]}"
        return f"value={stable_json(item)}" if item else f"index={index}"

    def _field_change(self, path: str, operation: str, before: Any, after: Any) -> dict[str, Any]:
        category = self._change_category(path, operation, before, after)
        severity = self._change_severity(category, operation, before, after)
        return {
            "version_item_key": "pending",
            "object_type": "pending",
            "source_entity_id": None,
            "field_path": path,
            "operation": operation,
            "change_category": category,
            "severity": severity,
            "before_value": json_copy(before),
            "after_value": json_copy(after),
            "before_type": scalar_type(before),
            "after_type": scalar_type(after),
            "human_summary": self._human_summary(path, operation, before, after),
            "machine_diff_json": {"path": path, "operation": operation, "before": json_copy(before), "after": json_copy(after)},
        }

    def _compare_version_items(self, base_items: list[dict[str, Any]], target_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def key(item: dict[str, Any]) -> str:
            return f"{item.get('object_type')}:{item.get('source_entity_id')}"

        base_map = {key(item): item for item in base_items}
        target_map = {key(item): item for item in target_items}
        changes: list[dict[str, Any]] = []
        for item_key in sorted(set(base_map) | set(target_map)):
            base = base_map.get(item_key)
            target = target_map.get(item_key)
            if base is None:
                item_changes = [self._field_change("$", "added", None, target.get("snapshot_json"))]
            elif target is None:
                item_changes = [self._field_change("$", "removed", base.get("snapshot_json"), None)]
            else:
                item_changes = self.structured_diff(base.get("snapshot_json") or {}, target.get("snapshot_json") or {})
            for change in item_changes:
                change["version_item_key"] = item_key
                change["object_type"] = (target or base or {}).get("object_type") or "unknown"
                change["source_entity_id"] = (target or base or {}).get("source_entity_id")
                changes.append(change)
        return changes

    def _change_category(self, path: str, operation: str, before: Any, after: Any) -> str:
        lowered = path.lower()
        if operation == "added":
            return "added"
        if operation == "removed":
            return "removed"
        if any(value in lowered for value in ["effective_from", "effective_to", "effective_until", "effective_date", "expiry"]):
            return "effective_date_change"
        if any(value in lowered for value in ["formula", "price", "pricing", "amount", "fee", "fare", "currency"]):
            if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                return "pricing_increase" if after > before else "pricing_decrease" if after < before else "modified"
            return "modified"
        if any(value in lowered for value in ["restriction", "limit", "maximum", "minimum", "advance_notice", "notice_hours"]):
            if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                minimum_like = any(value in lowered for value in ["minimum", "advance_notice", "notice_hours"])
                increased = after > before if minimum_like else after < before
                return "restriction_increased" if increased else "restriction_reduced"
            return "modified"
        if any(value in lowered for value in ["support_status", "supported", "capability_status", "service_allowed"]):
            return "support_status_change"
        if "document" in lowered:
            return "document_requirement_change"
        if "approval" in lowered:
            return "approval_requirement_change"
        if any(value in lowered for value in ["distribution", "gds", "ndc", "pss", "interline", "codeshare"]):
            return "distribution_change"
        if any(value in lowered for value in ["contact", "email", "phone", "service_desk"]):
            return "contact_change"
        if any(value in lowered for value in ["evidence", "source", "assertion", "excerpt"]):
            return "evidence_only_change"
        if any(value in lowered for value in ["superseded", "replaced_by"]):
            return "superseded"
        return "modified"

    def _change_severity(self, category: str, operation: str, before: Any, after: Any) -> str:
        if category in {"restriction_increased", "support_status_change", "document_requirement_change", "approval_requirement_change"}:
            return "critical" if category == "restriction_increased" or operation == "removed" else "high"
        if category in {"pricing_increase", "distribution_change", "removed"}:
            return "high"
        if category in {"pricing_decrease", "restriction_reduced", "effective_date_change", "added", "superseded"}:
            return "medium"
        if category in {"contact_change", "evidence_only_change"}:
            return "low"
        return "medium" if stable_json(before) != stable_json(after) else "informational"

    def _human_summary(self, path: str, operation: str, before: Any, after: Any) -> str:
        if operation == "added":
            return f"{path} was added with value {self._display_value(after)}."
        if operation == "removed":
            return f"{path} was removed; previous value was {self._display_value(before)}."
        return f"{path} changed from {self._display_value(before)} to {self._display_value(after)}."

    async def _assess_impact(
        self,
        change_set: dict[str, Any],
        base: dict[str, Any],
        target: dict[str, Any],
        base_items: list[dict[str, Any]],
        target_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        direct_references = {
            base["id"],
            target["id"],
            *(change_set.get("triggering_source_ids") or []),
            *(change_set.get("published_release_ids") or []),
            *[item.get("source_entity_id") for item in [*base_items, *target_items] if item.get("source_entity_id")],
        }
        airline_codes = {str(value).upper() for value in change_set.get("affected_airline_codes") or []}
        service_families = {str(value).upper() for value in change_set.get("affected_service_families") or []}
        route_scopes = {str(value).upper() for value in change_set.get("affected_route_scopes") or []}
        impacts: list[dict[str, Any]] = []
        for impact_type, collections in IMPACT_TARGET_COLLECTIONS.items():
            for collection in collections:
                for record in await self.db.collection(collection).find_many():
                    if not self._record_is_operationally_relevant(impact_type, record):
                        continue
                    if change_set.get("agency_id") and record.get("agency_id") and record.get("agency_id") != change_set.get("agency_id"):
                        continue
                    values = self._flatten_strings(record)
                    direct_matches = sorted(direct_references.intersection(values))
                    airline_matches = sorted(airline_codes.intersection({value.upper() for value in values}))
                    service_matches = sorted(service_families.intersection({value.upper() for value in values}))
                    route_matches = sorted(route_scopes.intersection({value.upper() for value in values}))
                    match_basis = [
                        *[f"direct_reference:{value}" for value in direct_matches],
                        *[f"airline:{value}" for value in airline_matches],
                        *[f"service:{value}" for value in service_matches],
                        *[f"route:{value}" for value in route_matches],
                    ]
                    if not match_basis:
                        continue
                    impact = AirlineKnowledgeImpactAssessment(
                        change_set_id=change_set["id"],
                        agency_id=record.get("agency_id"),
                        impact_type=impact_type,
                        target_collection=collection,
                        target_id=record["id"],
                        target_reference=self._record_reference(record),
                        impact_status="potentially_affected",
                        impact_severity=change_set.get("highest_severity") or "informational",
                        match_basis=match_basis,
                        impact_summary=f"{impact_type.replace('_', ' ').title()} may rely on changed airline knowledge and requires human review.",
                        requires_manual_review=True,
                        historical_snapshot_mutation_prohibited=True,
                    )
                    impacts.append(await self.db.collection(IMPACT_ASSESSMENT_COLLECTION).insert_one(impact.model_dump(mode="json")))
        return impacts

    async def _create_revalidation_requests(self, change_set: dict[str, Any], user: dict[str, Any]) -> list[dict[str, Any]]:
        requests: list[dict[str, Any]] = []
        specifications: list[tuple[str, str]] = []
        if change_set.get("re_qa_required"):
            specifications.append(("re_qa", "Structured operational knowledge changed and requires QA revalidation."))
        if change_set.get("republish_required"):
            specifications.append(("republish", "A published or effective knowledge version changed and requires a governed republishing decision."))
        for request_type, reason in specifications:
            request = AirlineKnowledgeRevalidationRequest(
                change_set_id=change_set["id"],
                agency_id=change_set.get("agency_id"),
                request_type=request_type,
                request_status="required",
                reason=reason,
                requested_by_user_id=user.get("id"),
            )
            requests.append(await self.db.collection(REVALIDATION_REQUEST_COLLECTION).insert_one(request.model_dump(mode="json")))
        return requests

    async def review_change_set(self, change_set_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        change_set = await self._require(CHANGE_SET_COLLECTION, change_set_id, "Knowledge change set")
        data = payload_dict(payload)
        review_status = str(data.get("review_status") or "")
        if review_status not in {"under_review", "approved", "changes_requested", "accepted", "archived"}:
            raise AirlineKnowledgeVersioningError("Change review status is not supported.")
        re_qa_required = bool(data.get("re_qa_required", change_set.get("re_qa_required")))
        republish_required = bool(data.get("republish_required", change_set.get("republish_required")))
        updated = await self.db.collection(CHANGE_SET_COLLECTION).update_one(
            {"id": change_set["id"]},
            {"review_status": review_status, "re_qa_required": re_qa_required, "republish_required": republish_required},
        )
        review = AirlineKnowledgeChangeReview(
            change_set_id=change_set["id"],
            agency_id=change_set.get("agency_id"),
            review_status=review_status,
            review_decision=data.get("review_decision"),
            re_qa_required=re_qa_required,
            republish_required=republish_required,
            reviewer_user_id=user.get("id"),
            reviewed_at=datetime.now(timezone.utc),
            review_notes=data.get("review_notes"),
            internal_notes=data.get("internal_notes"),
        )
        stored_review = await self.db.collection(CHANGE_REVIEW_COLLECTION).insert_one(review.model_dump(mode="json"))
        await self._audit("airline_knowledge_versioning.change_reviewed", change_set["id"], user, {"review_status": review_status})
        return {"change_set": updated, "review": stored_review, **self.safety_flags()}

    async def update_revalidation(self, request_id: str, payload: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        request = await self._require(REVALIDATION_REQUEST_COLLECTION, request_id, "Knowledge revalidation request")
        data = payload_dict(payload)
        status = str(data.get("request_status") or "")
        if status not in {"required", "in_progress", "completed", "waived"}:
            raise AirlineKnowledgeVersioningError("Revalidation request status is not supported.")
        updates = {
            "request_status": status,
            "completion_notes": data.get("completion_notes"),
            "completed_at": datetime.now(timezone.utc) if status in {"completed", "waived"} else None,
        }
        updated = await self.db.collection(REVALIDATION_REQUEST_COLLECTION).update_one({"id": request["id"]}, updates)
        await self._audit("airline_knowledge_versioning.revalidation_updated", request["id"], user, {"request_status": status})
        return {"revalidation_request": updated, **self.safety_flags()}

    async def list_versions(self, **filters: Any) -> list[dict[str, Any]]:
        versions = await self.db.collection(VERSION_COLLECTION).find_many()
        results = []
        for version in versions:
            if filters.get("agency_id") and version.get("agency_id") != filters["agency_id"]:
                continue
            if filters.get("airline_id") and version.get("canonical_airline_id") != filters["airline_id"]:
                continue
            if filters.get("lifecycle_status") and version.get("lifecycle_status") != filters["lifecycle_status"]:
                continue
            if filters.get("service_family") and filters["service_family"] not in (version.get("affected_service_families") or []):
                continue
            results.append(version)
        return sorted(results, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def list_change_sets(self, **filters: Any) -> list[dict[str, Any]]:
        items = await self.db.collection(CHANGE_SET_COLLECTION).find_many()
        results = []
        for item in items:
            if filters.get("agency_id") and item.get("agency_id") != filters["agency_id"]:
                continue
            if filters.get("airline_id") and item.get("canonical_airline_id") != filters["airline_id"]:
                continue
            if filters.get("category") and filters["category"] not in (item.get("change_categories") or []):
                continue
            if filters.get("review_status") and item.get("review_status") != filters["review_status"]:
                continue
            if filters.get("revalidation_required") is True and not (item.get("re_qa_required") or item.get("republish_required")):
                continue
            results.append(item)
        return sorted(results, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def get_version(self, version_id: str) -> dict[str, Any]:
        version = await self._require(VERSION_COLLECTION, version_id, "Knowledge version")
        return {
            "version": version,
            "items": await self.db.collection(VERSION_ITEM_COLLECTION).find_many({"version_id": version["id"]}),
            "change_sets": [
                item
                for item in await self.db.collection(CHANGE_SET_COLLECTION).find_many()
                if item.get("base_version_id") == version["id"] or item.get("target_version_id") == version["id"]
            ],
            "historical_snapshot_immutable": True,
            **self.safety_flags(),
        }

    async def get_change_set(self, change_set_id: str) -> dict[str, Any]:
        change_set = await self._require(CHANGE_SET_COLLECTION, change_set_id, "Knowledge change set")
        return {
            "change_set": change_set,
            "field_changes": await self.db.collection(FIELD_CHANGE_COLLECTION).find_many({"change_set_id": change_set["id"]}),
            "impact_assessments": await self.db.collection(IMPACT_ASSESSMENT_COLLECTION).find_many({"change_set_id": change_set["id"]}),
            "reviews": await self.db.collection(CHANGE_REVIEW_COLLECTION).find_many({"change_set_id": change_set["id"]}),
            "revalidation_requests": await self.db.collection(REVALIDATION_REQUEST_COLLECTION).find_many({"change_set_id": change_set["id"]}),
            **self.safety_flags(),
        }

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        versions = await self.list_versions(**filters)
        change_sets = await self.list_change_sets(**filters)
        return {
            "phase": PHASE_LABEL,
            "versions": versions,
            "change_sets": change_sets,
            "impact_assessments": await self.db.collection(IMPACT_ASSESSMENT_COLLECTION).find_many(),
            "revalidation_requests": await self.db.collection(REVALIDATION_REQUEST_COLLECTION).find_many(),
            "coverage": await self.coverage(),
            "versioned_object_types": sorted(ALL_VERSIONED_OBJECT_COLLECTIONS),
            "change_categories": CHANGE_CATEGORIES,
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        change_sets = await self.list_change_sets(**filters)
        visible: list[dict[str, Any]] = []
        for item in change_sets:
            if item.get("agency_id") and item.get("agency_id") != agency_id:
                continue
            if item.get("agency_visible") is not True:
                continue
            target = await self.db.collection(VERSION_COLLECTION).find_one({"id": item["target_version_id"]})
            if not target or target.get("lifecycle_status") not in PUBLIC_VERSION_STATUSES:
                continue
            fields = await self.db.collection(FIELD_CHANGE_COLLECTION).find_many({"change_set_id": item["id"]})
            impacts = [
                impact
                for impact in await self.db.collection(IMPACT_ASSESSMENT_COLLECTION).find_many({"change_set_id": item["id"]})
                if not impact.get("agency_id") or impact.get("agency_id") == agency_id
            ]
            visible.append(self._agency_change_projection(item, target, fields, impacts))
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "updates": visible,
            "published_update_count": len(visible),
            "read_only": True,
            **self.safety_flags(),
        }

    async def agency_change_set(self, agency_id: str, change_set_id: str) -> dict[str, Any]:
        response = await self.agency_response(agency_id)
        item = next((value for value in response["updates"] if value["id"] == change_set_id), None)
        if not item:
            raise AirlineKnowledgeVersioningError("Published agency knowledge update was not found.")
        return {"phase": PHASE_LABEL, "agency_id": agency_id, "update": item, "read_only": True, **self.safety_flags()}

    async def coverage(self) -> dict[str, Any]:
        versions = await self.db.collection(VERSION_COLLECTION).find_many()
        changes = await self.db.collection(CHANGE_SET_COLLECTION).find_many()
        fields = await self.db.collection(FIELD_CHANGE_COLLECTION).find_many()
        impacts = await self.db.collection(IMPACT_ASSESSMENT_COLLECTION).find_many()
        revalidations = await self.db.collection(REVALIDATION_REQUEST_COLLECTION).find_many()
        return {
            "version_count": len(versions),
            "immutable_version_item_count": await self.db.collection(VERSION_ITEM_COLLECTION).count(),
            "change_set_count": len(changes),
            "field_change_count": len(fields),
            "impact_assessment_count": len(impacts),
            "re_qa_required_count": len([item for item in changes if item.get("re_qa_required")]),
            "republish_required_count": len([item for item in changes if item.get("republish_required")]),
            "published_agency_update_count": len([item for item in changes if item.get("agency_visible")]),
            "open_revalidation_count": len([item for item in revalidations if item.get("request_status") in {"required", "in_progress"}]),
        }

    def _agency_change_projection(
        self,
        change_set: dict[str, Any],
        target: dict[str, Any],
        fields: list[dict[str, Any]],
        impacts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "id": change_set["id"],
            "change_set_reference": change_set.get("change_set_reference"),
            "version_reference": target.get("knowledge_version_reference"),
            "version_label": target.get("version_label"),
            "change_summary": change_set.get("change_summary"),
            "change_categories": change_set.get("change_categories") or [],
            "highest_severity": change_set.get("highest_severity"),
            "affected_airline_codes": change_set.get("affected_airline_codes") or [],
            "affected_service_families": change_set.get("affected_service_families") or [],
            "affected_route_scopes": change_set.get("affected_route_scopes") or [],
            "effective_from": target.get("effective_from"),
            "published_release_ids": change_set.get("published_release_ids") or [],
            "operational_warnings": [impact.get("impact_summary") for impact in impacts],
            "field_changes": [
                {
                    "field_path": field.get("field_path"),
                    "operation": field.get("operation"),
                    "change_category": field.get("change_category"),
                    "severity": field.get("severity"),
                    "human_summary": field.get("human_summary"),
                }
                for field in fields
            ],
            "re_qa_required": change_set.get("re_qa_required"),
            "republish_required": change_set.get("republish_required"),
            "read_only": True,
        }

    async def _published_release_ids(self, target: dict[str, Any]) -> list[str]:
        release_ids = list(target.get("published_release_ids") or [])
        for collection, field in [
            ("airline_knowledge_releases", "included_version_ids"),
            ("airline_knowledge_publications", "included_knowledge_version_ids"),
        ]:
            for record in await self.db.collection(collection).find_many():
                if target["id"] in (record.get(field) or []) and str(record.get("release_status") or record.get("publication_status") or "") in PUBLIC_RELEASE_STATUSES:
                    release_ids.append(record["id"])
        return self._unique(release_ids)

    def _record_is_operationally_relevant(self, impact_type: str, record: dict[str, Any]) -> bool:
        status = str(
            record.get("status")
            or record.get("offer_status")
            or record.get("trip_status")
            or record.get("case_status")
            or record.get("workflow_status")
            or ""
        ).lower()
        if impact_type in {"active_offer", "future_trip"} and status in {"archived", "cancelled", "rejected", "completed", "closed"}:
            return False
        if impact_type == "unresolved_case" and status in {"resolved", "rejected", "cancelled", "archived", "closed"}:
            return False
        return True

    def _flatten_strings(self, value: Any) -> set[str]:
        if isinstance(value, dict):
            return {item for child in value.values() for item in self._flatten_strings(child)}
        if isinstance(value, list):
            return {item for child in value for item in self._flatten_strings(child)}
        if value is None:
            return set()
        return {str(value)}

    def _record_reference(self, record: dict[str, Any]) -> str:
        for key in [
            "knowledge_version_reference",
            "publication_reference",
            "policy_reference",
            "formula_reference",
            "rule_reference",
            "capability_reference",
            "assertion_reference",
            "service_reference",
            "template_reference",
            "case_reference",
            "trip_reference",
            "offer_reference",
            "reference",
            "code",
            "id",
        ]:
            if record.get(key):
                return str(record[key])
        return "unknown"

    def _airline_code(self, record: dict[str, Any]) -> str | None:
        for key in ["airline_code", "iata_code", "validating_carrier", "operating_carrier", "marketing_carrier"]:
            if record.get(key):
                return str(record[key]).upper()
        return None

    def _highest_severity(self, values: list[str]) -> str:
        return max(values or ["informational"], key=lambda value: SEVERITY_ORDER.get(value, 0))

    def _change_summary(self, changes: list[dict[str, Any]]) -> str:
        if not changes:
            return "No structured airline knowledge changes were detected."
        counts: dict[str, int] = {}
        for item in changes:
            counts[item["change_category"]] = counts.get(item["change_category"], 0) + 1
        detail = ", ".join(f"{category.replace('_', ' ')}: {count}" for category, count in sorted(counts.items()))
        return f"Detected {len(changes)} structured field changes ({detail})."

    def _display_value(self, value: Any) -> str:
        rendered = stable_json(value)
        return rendered if len(rendered) <= 120 else f"{rendered[:117]}..."

    def _unique(self, values: list[Any]) -> list[str]:
        return list(dict.fromkeys(str(value) for value in values if value is not None and value != ""))

    async def _require(self, collection: str, record_id: str, label: str) -> dict[str, Any]:
        record = await self.db.collection(collection).find_one({"id": record_id})
        if not record:
            raise AirlineKnowledgeVersioningError(f"{label} was not found.")
        return record

    async def _audit(self, event_type: str, entity_id: str, user: dict[str, Any], metadata: dict[str, Any]) -> None:
        event = AuditEvent(
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="airline_knowledge_versioning",
            entity_id=entity_id,
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata=metadata,
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))
