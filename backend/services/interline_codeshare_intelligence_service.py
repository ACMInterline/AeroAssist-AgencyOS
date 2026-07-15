from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineBaggageResponsibilityRule,
    AirlineCarrierRelationship,
    AirlineCodeshareRule,
    AirlineInterlineAgreementProfile,
    AirlineInterlineEmdRule,
    AirlineOperatingCarrierPolicyRule,
    AirlineServiceResponsibilityRule,
    AirlineThroughCheckRule,
    AirlineValidatingCarrierRule,
    AuditEvent,
)


PHASE_LABEL = "phase_56_0_canonical_journey_itinerary_representation_foundation"

AIRLINE_CARRIER_RELATIONSHIPS_COLLECTION = "airline_carrier_relationships"
AIRLINE_INTERLINE_AGREEMENT_PROFILES_COLLECTION = "airline_interline_agreement_profiles"
AIRLINE_CODESHARE_RULES_COLLECTION = "airline_codeshare_rules"
AIRLINE_OPERATING_CARRIER_POLICY_RULES_COLLECTION = "airline_operating_carrier_policy_rules"
AIRLINE_VALIDATING_CARRIER_RULES_COLLECTION = "airline_validating_carrier_rules"
AIRLINE_THROUGH_CHECK_RULES_COLLECTION = "airline_through_check_rules"
AIRLINE_BAGGAGE_RESPONSIBILITY_RULES_COLLECTION = "airline_baggage_responsibility_rules"
AIRLINE_SERVICE_RESPONSIBILITY_RULES_COLLECTION = "airline_service_responsibility_rules"
AIRLINE_INTERLINE_EMD_RULES_COLLECTION = "airline_interline_emd_rules"

INTERLINE_INTELLIGENCE_COLLECTIONS = [
    AIRLINE_CARRIER_RELATIONSHIPS_COLLECTION,
    AIRLINE_INTERLINE_AGREEMENT_PROFILES_COLLECTION,
    AIRLINE_CODESHARE_RULES_COLLECTION,
    AIRLINE_OPERATING_CARRIER_POLICY_RULES_COLLECTION,
    AIRLINE_VALIDATING_CARRIER_RULES_COLLECTION,
    AIRLINE_THROUGH_CHECK_RULES_COLLECTION,
    AIRLINE_BAGGAGE_RESPONSIBILITY_RULES_COLLECTION,
    AIRLINE_SERVICE_RESPONSIBILITY_RULES_COLLECTION,
    AIRLINE_INTERLINE_EMD_RULES_COLLECTION,
]

CARRIER_ROLES = [
    "marketing_carrier",
    "operating_carrier",
    "validating_carrier",
    "ticketing_carrier",
    "plating_carrier",
    "handling_carrier",
]

RELATIONSHIP_TYPES = ["codeshare", "interline", "spa", "alliance", "wet_lease", "franchise", "regional_affiliate"]
RULE_STATUSES = ["supported", "unsupported", "conditional", "manual_only", "unknown", "route_specific", "market_specific"]
CONFIDENCE_LEVELS = ["official", "high", "medium", "low", "unknown"]
FRESHNESS_STATUSES = ["current", "review_due", "stale", "expired", "unknown"]
PUBLICATION_STATUSES = ["draft", "under_review", "approved", "published", "archived"]
AGENCY_VISIBILITY_STATUSES = ["platform_only", "all_agencies", "selected_agencies"]

RESPONSIBILITY_AREAS = [
    "policy_owner",
    "ssr_request_owner",
    "service_confirmation_owner",
    "ancillary_pricing_owner",
    "ticket_issue_owner",
    "emd_issuer",
    "airport_fulfillment_owner",
    "baggage_rule_owner",
    "medical_pet_rule_owner",
    "contact_desk_owner",
    "exchange_owner",
    "disruption_owner",
]

JOURNEY_CAPABILITIES = [
    "through_check_in",
    "through_baggage",
    "seat_assignment_continuity",
    "special_service_continuity",
    "emd_interline_support",
    "ticket_exchange_responsibility",
    "disruption_responsibility",
]

ENTITY_CONFIG: dict[str, dict[str, Any]] = {
    "relationships": {"collection": AIRLINE_CARRIER_RELATIONSHIPS_COLLECTION, "model": AirlineCarrierRelationship, "reference": "relationship_reference", "prefix": "ACR"},
    "interline-agreements": {"collection": AIRLINE_INTERLINE_AGREEMENT_PROFILES_COLLECTION, "model": AirlineInterlineAgreementProfile, "reference": "agreement_profile_reference", "prefix": "AIA"},
    "codeshare-rules": {"collection": AIRLINE_CODESHARE_RULES_COLLECTION, "model": AirlineCodeshareRule, "reference": "codeshare_rule_reference", "prefix": "ACRUL"},
    "operating-carrier-rules": {"collection": AIRLINE_OPERATING_CARRIER_POLICY_RULES_COLLECTION, "model": AirlineOperatingCarrierPolicyRule, "reference": "operating_policy_rule_reference", "prefix": "AOP"},
    "validating-carrier-rules": {"collection": AIRLINE_VALIDATING_CARRIER_RULES_COLLECTION, "model": AirlineValidatingCarrierRule, "reference": "validating_carrier_rule_reference", "prefix": "AVC"},
    "through-check-rules": {"collection": AIRLINE_THROUGH_CHECK_RULES_COLLECTION, "model": AirlineThroughCheckRule, "reference": "through_check_rule_reference", "prefix": "ATC"},
    "baggage-rules": {"collection": AIRLINE_BAGGAGE_RESPONSIBILITY_RULES_COLLECTION, "model": AirlineBaggageResponsibilityRule, "reference": "baggage_responsibility_rule_reference", "prefix": "ABR"},
    "service-responsibility-rules": {"collection": AIRLINE_SERVICE_RESPONSIBILITY_RULES_COLLECTION, "model": AirlineServiceResponsibilityRule, "reference": "service_responsibility_rule_reference", "prefix": "ASR"},
    "interline-emd-rules": {"collection": AIRLINE_INTERLINE_EMD_RULES_COLLECTION, "model": AirlineInterlineEmdRule, "reference": "interline_emd_rule_reference", "prefix": "AER"},
}

REFERENCE_FIELDS = {config["reference"] for config in ENTITY_CONFIG.values()}
INTERNAL_FIELDS = {"internal_notes", "visible_agency_ids", "metadata", "legacy_interline_agreement_id", "legacy_emd_interline_rule_id"}


class InterlineCodeshareIntelligenceError(ValueError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class InterlineCodeshareIntelligenceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "advisory_intelligence_only": True,
            "unknown_state_preserved": True,
            "unsupported_certainty_disabled": True,
            "human_authority_final": True,
            "legacy_interline_truth_preserved": True,
            "operational_constraint_integration_enabled": True,
            "feasibility_integration_enabled": True,
            "recommendation_integration_enabled": True,
            "offer_intelligence_integration_enabled": True,
            "agency_published_read_only": True,
            "unpublished_draft_agency_visibility_disabled": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "emd_issuance_disabled": True,
            "provider_connectivity_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "entity_types": list(ENTITY_CONFIG),
            "carrier_roles": CARRIER_ROLES,
            "relationship_types": RELATIONSHIP_TYPES,
            "rule_statuses": RULE_STATUSES,
            "confidence_levels": CONFIDENCE_LEVELS,
            "freshness_statuses": FRESHNESS_STATUSES,
            "publication_statuses": PUBLICATION_STATUSES,
            "responsibility_areas": RESPONSIBILITY_AREAS,
            "journey_capabilities": JOURNEY_CAPABILITIES,
        }

    async def create_record(self, entity_type: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        data = payload_dict(payload)
        data.setdefault(config["reference"], self._reference(config["prefix"]))
        normalized = await self._normalize_and_validate(entity_type, data)
        record = config["model"](**normalized).model_dump(mode="json")
        created = await self.db.collection(config["collection"]).insert_one(record)
        await self._audit(f"interline_codeshare_intelligence.{entity_type}.created", created, user)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": created, **self.safety_flags()}

    async def update_record(self, entity_type: str, record_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        existing = await self._require(entity_type, record_id)
        merged = await self._normalize_and_validate(entity_type, {**existing, **payload_dict(payload)})
        validated = config["model"](**merged).model_dump(mode="json")
        immutable = {"id", "created_at", "agency_id", config["reference"]}
        updates = {key: value for key, value in validated.items() if key not in immutable}
        updated = await self.db.collection(config["collection"]).update_one({"id": existing["id"]}, updates)
        await self._audit(f"interline_codeshare_intelligence.{entity_type}.updated", updated or existing, user)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": updated or existing, **self.safety_flags()}

    async def get_record(self, entity_type: str, record_id: str) -> dict[str, Any]:
        entity_type, _ = self._config(entity_type)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": await self._require(entity_type, record_id), **self.safety_flags()}

    async def list_records(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        entity_type, config = self._config(entity_type)
        records = await self.db.collection(config["collection"]).find_many()
        records = [item for item in records if self._matches_filters(item, filters)]
        records.sort(key=lambda item: (self._carrier(self._primary_carrier(item)), self._sort_text(item.get("updated_at"))), reverse=False)
        return records

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        records = {key: await self.list_records(key, **filters) for key in ENTITY_CONFIG}
        return {
            "phase": PHASE_LABEL,
            "summary": self._summary(records),
            "relationships": records["relationships"],
            "interline_agreements": records["interline-agreements"],
            "codeshare_rules": records["codeshare-rules"],
            "operating_carrier_rules": records["operating-carrier-rules"],
            "validating_carrier_rules": records["validating-carrier-rules"],
            "through_check_rules": records["through-check-rules"],
            "baggage_rules": records["baggage-rules"],
            "service_responsibility_rules": records["service-responsibility-rules"],
            "interline_emd_rules": records["interline-emd-rules"],
            "responsibility_matrix": self._responsibility_matrix(records),
            "legacy_context": await self._legacy_context(filters.get("airline_code")),
            "filters": self.filter_metadata(),
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        records: dict[str, list[dict[str, Any]]] = {}
        for entity_type in ENTITY_CONFIG:
            source = await self.list_records(entity_type, **filters)
            records[entity_type] = [self._agency_projection(item) for item in source if self._agency_visible(item, agency_id)]
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self._summary(records),
            "relationships": records["relationships"],
            "rules": {key: value for key, value in records.items() if key != "relationships"},
            "responsibility_matrix": self._responsibility_matrix(records),
            "warnings": self._knowledge_warnings(records),
            "filters": self.filter_metadata(),
            "read_only": True,
            **self.safety_flags(),
        }

    async def evaluate_itinerary(self, payload: Any, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        request = payload_dict(payload)
        segments = request.get("segments") or []
        if not isinstance(segments, list) or not segments:
            raise InterlineCodeshareIntelligenceError("At least one itinerary segment is required for advisory evaluation.")
        normalized_segments = [self._normalize_segment(item, index) for index, item in enumerate(segments)]
        travel_date = self._date_value(request.get("travel_date"))
        records: dict[str, list[dict[str, Any]]] = {}
        for entity_type in ENTITY_CONFIG:
            source = await self.list_records(entity_type)
            if agency_safe:
                source = [item for item in source if agency_id and self._agency_visible(item, agency_id)]
            elif agency_id:
                source = [item for item in source if item.get("agency_id") in {None, agency_id}]
            records[entity_type] = source

        role_map: list[dict[str, Any]] = []
        segment_results: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        manual_review: list[dict[str, Any]] = []
        unsupported: list[dict[str, Any]] = []
        previous_segment: dict[str, Any] | None = None

        for segment in normalized_segments:
            role_map.append({"segment_reference": segment["segment_reference"], **{role: segment.get(role) for role in CARRIER_ROLES}})
            services = segment.get("service_requirements") or request.get("service_requirements") or []
            matches = self._segment_matches(records, segment, services, travel_date, previous_segment)
            responsibilities = self._segment_responsibilities(segment, matches, services)
            capabilities = self._journey_capabilities(matches, previous_segment is not None)
            result = {
                "segment_reference": segment["segment_reference"],
                "route": self._segment_route(segment),
                "carrier_roles": role_map[-1],
                "relationships": [self._trace(item) for item in matches["relationships"]],
                "responsibilities": responsibilities,
                "journey_capabilities": capabilities,
                "rule_trace": {key: [self._trace(item) for item in value] for key, value in matches.items() if key != "relationships"},
                "metadata_only": True,
            }
            segment_results.append(result)
            self._collect_evaluation_findings(segment, matches, responsibilities, capabilities, warnings, manual_review, unsupported)
            previous_segment = segment

        foundation_context = await self._foundation_context(agency_id, normalized_segments)
        owner_summary = {
            area: self._unique_owners([item["responsibilities"].get(area) for item in segment_results])
            for area in RESPONSIBILITY_AREAS
        }
        if unsupported:
            outcome = "unsupported_combination"
        elif manual_review or warnings:
            outcome = "manual_review_required"
        else:
            outcome = "responsibilities_resolved"
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "evaluation_reference": request.get("evaluation_reference") or self._reference("ICE"),
            "evaluation_status": outcome,
            "carrier_role_map": role_map,
            "segments": segment_results,
            "responsibility_summary": owner_summary,
            "applicable_policy_owner": owner_summary["policy_owner"],
            "service_confirmation_owner": owner_summary["service_confirmation_owner"],
            "pricing_owner": owner_summary["ancillary_pricing_owner"],
            "ticket_emd_owner": {
                "ticket": owner_summary["ticket_issue_owner"],
                "emd": owner_summary["emd_issuer"],
            },
            "baggage_responsibility": owner_summary["baggage_rule_owner"],
            "warnings": warnings,
            "manual_review_requirements": manual_review,
            "unsupported_combinations": unsupported,
            "recommended_action": self._recommended_action(outcome),
            "foundation_context": foundation_context,
            "read_only": True,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            **self.safety_flags(),
        }

    async def coverage(self) -> dict[str, Any]:
        counts = {name: await self.db.collection(name).count() for name in INTERLINE_INTELLIGENCE_COLLECTIONS}
        all_records: list[dict[str, Any]] = []
        for collection in INTERLINE_INTELLIGENCE_COLLECTIONS:
            all_records.extend(await self.db.collection(collection).find_many())
        return {
            "interline_intelligence_collection_counts": counts,
            "carrier_relationship_count": counts[AIRLINE_CARRIER_RELATIONSHIPS_COLLECTION],
            "interline_agreement_profile_count": counts[AIRLINE_INTERLINE_AGREEMENT_PROFILES_COLLECTION],
            "responsibility_rule_count": sum(counts[name] for name in INTERLINE_INTELLIGENCE_COLLECTIONS[2:]),
            "published_interline_record_count": len([item for item in all_records if item.get("publication_status") == "published"]),
            "unknown_interline_record_count": len([item for item in all_records if self._record_status(item) == "unknown"]),
            "manual_review_interline_record_count": len([item for item in all_records if self._record_status(item) in {"unknown", "conditional", "manual_only"}]),
        }

    async def _normalize_and_validate(self, entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
        data["metadata_only"] = True
        for field in [key for key in data if "carrier" in key and key.endswith(("_code", "_carrier"))]:
            if data.get(field):
                data[field] = self._carrier(data[field])
        for field in ["airline_code", "partner_airline_code", "carrier_a_code", "carrier_b_code"]:
            if data.get(field):
                data[field] = self._carrier(data[field])
        if "relationship_type" in data:
            data["relationship_type"] = self._choice(data.get("relationship_type"), RELATIONSHIP_TYPES, "relationship type")
        for status_field in [
            "relationship_status", "agreement_status", "ticketing_status", "through_check_status", "through_baggage_status",
            "special_service_status", "emd_interline_status", "rule_status", "through_check_in_status",
            "seat_assignment_continuity_status", "special_service_continuity_status", "emd_a_status", "emd_s_status",
        ]:
            if status_field in data:
                data[status_field] = self._choice(data.get(status_field), RULE_STATUSES, status_field.replace("_", " "))
        if "confidence" in data:
            data["confidence"] = self._choice(data.get("confidence"), CONFIDENCE_LEVELS, "confidence")
        if "freshness_status" in data:
            data["freshness_status"] = self._choice(data.get("freshness_status"), FRESHNESS_STATUSES, "freshness status")
        if "publication_status" in data:
            data["publication_status"] = self._choice(data.get("publication_status"), PUBLICATION_STATUSES, "publication status")
        if "agency_visibility_status" in data:
            data["agency_visibility_status"] = self._choice(data.get("agency_visibility_status"), AGENCY_VISIBILITY_STATUSES, "agency visibility status")
        if entity_type == "interline-agreements" and not data.get("legacy_interline_agreement_id"):
            data["legacy_interline_agreement_id"] = await self._legacy_interline_id(data)
        if entity_type == "interline-emd-rules":
            data["emd_execution_disabled"] = True
            if not data.get("legacy_emd_interline_rule_id"):
                data["legacy_emd_interline_rule_id"] = await self._legacy_emd_rule_id(data)
        return data

    def _segment_matches(
        self,
        records: dict[str, list[dict[str, Any]]],
        segment: dict[str, Any],
        services: list[Any],
        travel_date: date | None,
        previous_segment: dict[str, Any] | None,
    ) -> dict[str, list[dict[str, Any]]]:
        marketing = segment.get("marketing_carrier")
        operating = segment.get("operating_carrier")
        validating = segment.get("validating_carrier")
        pair = {marketing, operating} - {None, ""}
        service_codes = {self._code(item.get("service_code") or item.get("code") or item.get("service_family") or item) if isinstance(item, dict) else self._code(item) for item in services}
        matches = {
            "relationships": [item for item in records["relationships"] if {item.get("carrier_a_code"), item.get("carrier_b_code")} == pair and self._scope_matches(item, segment, travel_date)],
            "interline_agreements": [item for item in records["interline-agreements"] if self._pair_matches(item.get("airline_code"), item.get("partner_airline_code"), marketing, operating) and self._scope_matches(item, segment, travel_date)],
            "codeshare_rules": [item for item in records["codeshare-rules"] if self._carrier(item.get("marketing_carrier_code")) == marketing and self._carrier(item.get("operating_carrier_code")) == operating and self._scope_matches(item, segment, travel_date)],
            "operating_rules": [item for item in records["operating-carrier-rules"] if self._carrier(item.get("operating_carrier_code")) == operating and (not item.get("marketing_carrier_code") or self._carrier(item.get("marketing_carrier_code")) == marketing) and self._scope_matches(item, segment, travel_date)],
            "validating_rules": [item for item in records["validating-carrier-rules"] if validating and self._carrier(item.get("validating_carrier_code")) == validating and self._scope_matches(item, segment, travel_date)],
            "baggage_rules": [item for item in records["baggage-rules"] if self._carrier(item.get("operating_carrier_code")) == operating and (not item.get("marketing_carrier_code") or self._carrier(item.get("marketing_carrier_code")) == marketing) and self._scope_matches(item, segment, travel_date)],
            "service_rules": [item for item in records["service-responsibility-rules"] if self._carrier(item.get("operating_carrier_code")) == operating and (not item.get("marketing_carrier_code") or self._carrier(item.get("marketing_carrier_code")) == marketing) and (not service_codes or self._code(item.get("service_code") or item.get("service_family")) in service_codes) and self._scope_matches(item, segment, travel_date)],
            "emd_rules": [item for item in records["interline-emd-rules"] if self._pair_matches(item.get("airline_code"), item.get("partner_airline_code"), operating, validating or marketing) and self._scope_matches(item, segment, travel_date)],
            "through_rules": [],
        }
        if previous_segment:
            prior = previous_segment.get("operating_carrier")
            matches["through_rules"] = [item for item in records["through-check-rules"] if self._pair_matches(item.get("airline_code"), item.get("partner_airline_code"), prior, operating) and self._scope_matches(item, segment, travel_date)]
        return matches

    def _segment_responsibilities(self, segment: dict[str, Any], matches: dict[str, list[dict[str, Any]]], services: list[Any]) -> dict[str, Any]:
        service = self._best(matches["service_rules"])
        codeshare = self._best(matches["codeshare_rules"])
        operating = self._best(matches["operating_rules"])
        validating = self._best(matches["validating_rules"])
        baggage = self._best(matches["baggage_rules"])
        emd = self._best(matches["emd_rules"])
        return {
            "policy_owner": self._owner(service, "policy_owner_carrier_code") or self._owner(codeshare, "policy_owner_carrier_code") or self._owner(operating, "policy_owner_carrier_code"),
            "ssr_request_owner": self._owner(service, "ssr_request_owner_carrier_code") or self._owner(codeshare, "ssr_request_owner_carrier_code"),
            "service_confirmation_owner": self._owner(service, "service_confirmation_owner_carrier_code") or self._owner(codeshare, "service_confirmation_owner_carrier_code") or self._owner(operating, "service_confirmation_owner_carrier_code"),
            "ancillary_pricing_owner": self._owner(service, "pricing_owner_carrier_code") or self._owner(codeshare, "ancillary_pricing_owner_carrier_code"),
            "ticket_issue_owner": self._owner(validating, "ticket_issue_owner_carrier_code"),
            "emd_issuer": self._owner(service, "emd_issuer_carrier_code") or self._owner(emd, "emd_issuer_carrier_code") or self._owner(codeshare, "emd_issuer_carrier_code"),
            "airport_fulfillment_owner": self._owner(service, "airport_fulfillment_owner_carrier_code") or self._owner(operating, "airport_fulfillment_owner_carrier_code") or self._owner(codeshare, "airport_fulfillment_owner_carrier_code"),
            "baggage_rule_owner": self._owner(baggage, "baggage_rule_owner_carrier_code") or self._owner(codeshare, "baggage_rule_owner_carrier_code"),
            "medical_pet_rule_owner": self._owner(codeshare, "medical_pet_rule_owner_carrier_code") or self._owner(operating, "medical_rule_owner_carrier_code") or self._owner(operating, "pet_rule_owner_carrier_code"),
            "contact_desk_owner": self._owner(service, "contact_desk_owner_carrier_code"),
            "exchange_owner": self._owner(validating, "exchange_owner_carrier_code"),
            "disruption_owner": self._owner(validating, "disruption_owner_carrier_code"),
            "service_requirements": services,
        }

    def _journey_capabilities(self, matches: dict[str, list[dict[str, Any]]], has_connection: bool) -> dict[str, Any]:
        through = self._best(matches["through_rules"])
        emd = self._best(matches["emd_rules"])
        validating = self._best(matches["validating_rules"])
        if not has_connection:
            through_values = {key: "not_applicable" for key in ["through_check_in", "through_baggage", "seat_assignment_continuity", "special_service_continuity"]}
        else:
            through_values = {
                "through_check_in": (through or {}).get("through_check_in_status", "unknown"),
                "through_baggage": (through or {}).get("through_baggage_status", "unknown"),
                "seat_assignment_continuity": (through or {}).get("seat_assignment_continuity_status", "unknown"),
                "special_service_continuity": (through or {}).get("special_service_continuity_status", "unknown"),
            }
        return {
            **through_values,
            "emd_interline_support": (emd or {}).get("interline_emd_status", "unknown"),
            "ticket_exchange_responsibility": self._owner(validating, "exchange_owner_carrier_code"),
            "disruption_responsibility": self._owner(validating, "disruption_owner_carrier_code"),
        }

    def _collect_evaluation_findings(self, segment: dict[str, Any], matches: dict[str, list[dict[str, Any]]], responsibilities: dict[str, Any], capabilities: dict[str, Any], warnings: list[dict[str, Any]], manual_review: list[dict[str, Any]], unsupported: list[dict[str, Any]]) -> None:
        reference = segment["segment_reference"]
        marketing = segment.get("marketing_carrier")
        operating = segment.get("operating_carrier")
        if marketing != operating and not matches["codeshare_rules"]:
            warnings.append({"segment_reference": reference, "code": "missing_codeshare_rule", "message": "No published codeshare responsibility rule resolves this marketed/operated segment."})
        for area, owner in responsibilities.items():
            if area == "service_requirements":
                continue
            if owner is None:
                manual_review.append({"segment_reference": reference, "area": area, "reason": "No governed responsibility owner is established."})
        for family, records in matches.items():
            for record in records:
                status = self._record_status(record)
                if status == "unsupported":
                    unsupported.append({"segment_reference": reference, "rule_family": family, "record_id": record.get("id"), "reason": "A governed rule marks this combination unsupported."})
                elif status in {"unknown", "conditional", "manual_only", "route_specific", "market_specific"}:
                    manual_review.append({"segment_reference": reference, "area": family, "record_id": record.get("id"), "reason": f"Rule status is {status.replace('_', ' ')}."})
                if record.get("freshness_status") in {"stale", "expired", "review_due", "unknown"}:
                    warnings.append({"segment_reference": reference, "code": "knowledge_freshness", "record_id": record.get("id"), "message": f"Responsibility knowledge freshness is {record.get('freshness_status') or 'unknown'}."})
        for capability, status in capabilities.items():
            if status in {None, "unknown", "unsupported"}:
                warnings.append({"segment_reference": reference, "code": capability, "message": f"{capability.replace('_', ' ').title()} is {status or 'unknown'}."})

    async def _foundation_context(self, agency_id: str | None, segments: list[dict[str, Any]]) -> dict[str, Any]:
        carriers = {value for segment in segments for key, value in segment.items() if "carrier" in key and value}
        mappings = {
            "operational_constraint_ids": "operational_constraints",
            "feasibility_ids": "passenger_service_feasibilities",
            "recommendation_ids": "airline_recommendations",
            "offer_intelligence_package_ids": "intelligent_offer_builder_packages",
        }
        result: dict[str, Any] = {}
        for result_key, collection in mappings.items():
            records = await self.db.collection(collection).find_many()
            if agency_id:
                records = [item for item in records if item.get("agency_id") == agency_id]
            matches = [item for item in records if self._record_has_carrier(item, carriers)]
            result[result_key] = [item.get("id") for item in matches if item.get("id")]
        result.update({"reference_only": True, "historical_snapshots_unchanged": True, "automatic_mutation_disabled": True})
        return result

    def _responsibility_matrix(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for rule in records.get("service-responsibility-rules", []):
            rows.append({
                "record_id": rule.get("id"),
                "marketing_carrier": rule.get("marketing_carrier_code"),
                "operating_carrier": rule.get("operating_carrier_code"),
                "service": rule.get("service_code") or rule.get("service_family"),
                "policy_owner": rule.get("policy_owner_carrier_code"),
                "ssr_owner": rule.get("ssr_request_owner_carrier_code"),
                "confirmation_owner": rule.get("service_confirmation_owner_carrier_code"),
                "pricing_owner": rule.get("pricing_owner_carrier_code"),
                "emd_owner": rule.get("emd_issuer_carrier_code"),
                "airport_owner": rule.get("airport_fulfillment_owner_carrier_code"),
                "status": rule.get("rule_status"),
                "confidence": rule.get("confidence"),
            })
        return rows

    def _summary(self, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        all_records = [item for values in records.values() for item in values]
        return {
            "relationship_count": len(records.get("relationships", [])),
            "interline_agreement_count": len(records.get("interline-agreements", [])),
            "codeshare_rule_count": len(records.get("codeshare-rules", [])),
            "responsibility_rule_count": sum(len(records.get(key, [])) for key in list(ENTITY_CONFIG)[3:]),
            "airline_count": len({carrier for item in all_records for carrier in self._record_carriers(item)}),
            "unknown_count": len([item for item in all_records if self._record_status(item) == "unknown"]),
            "unsupported_count": len([item for item in all_records if self._record_status(item) == "unsupported"]),
            "manual_review_count": len([item for item in all_records if self._record_status(item) in {"unknown", "conditional", "manual_only"}]),
            "evidence_link_count": sum(len(item.get("evidence_link_ids") or []) for item in all_records),
            "metadata_only": True,
        }

    def _knowledge_warnings(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        for entity_type, values in records.items():
            for item in values:
                status = self._record_status(item)
                if status in {"unknown", "unsupported", "conditional", "manual_only"}:
                    warnings.append({"record_id": item.get("id"), "entity_type": entity_type, "status": status, "message": f"{entity_type.replace('-', ' ').title()} is {status.replace('_', ' ')}; human review is required."})
        return warnings

    async def _legacy_context(self, airline_code: str | None) -> dict[str, Any]:
        legacy_interline = await self.db.collection("airline_interline_agreements").find_many()
        legacy_emd = await self.db.collection("airline_emd_interline_rules").find_many()
        if airline_code:
            airline = self._carrier(airline_code)
            legacy_interline = [item for item in legacy_interline if airline in self._record_carriers(item)]
            legacy_emd = [item for item in legacy_emd if airline in self._record_carriers(item)]
        return {
            "airline_interline_agreement_ids": [item.get("id") for item in legacy_interline],
            "airline_emd_interline_rule_ids": [item.get("id") for item in legacy_emd],
            "legacy_records_preserved": True,
            "normalized_records_are_additive": True,
        }

    async def _legacy_interline_id(self, data: dict[str, Any]) -> str | None:
        records = await self.db.collection("airline_interline_agreements").find_many()
        airline = self._carrier(data.get("airline_code"))
        partner = self._carrier(data.get("partner_airline_code"))
        match = next((item for item in records if self._pair_matches(item.get("airline_code") or item.get("airline_id"), item.get("partner_iata_code") or item.get("partner_airline_id"), airline, partner)), None)
        return match.get("id") if match else None

    async def _legacy_emd_rule_id(self, data: dict[str, Any]) -> str | None:
        records = await self.db.collection("airline_emd_interline_rules").find_many()
        airline = self._carrier(data.get("airline_code"))
        match = next((item for item in records if self._carrier(item.get("airline_code")) == airline), None)
        return match.get("id") if match else None

    def _agency_visible(self, item: dict[str, Any], agency_id: str) -> bool:
        if item.get("agency_id") not in {None, agency_id} or self._code(item.get("publication_status")) != "published":
            return False
        visibility = self._code(item.get("agency_visibility_status"))
        return visibility == "all_agencies" or (visibility == "selected_agencies" and agency_id in set(item.get("visible_agency_ids") or []))

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = {key: value for key, value in item.items() if key not in INTERNAL_FIELDS}
        projected.update({"read_only": True, "metadata_only": True, "advisory_only": True})
        return projected

    def _matches_filters(self, item: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, expected in filters.items():
            if expected is None or expected == "":
                continue
            if key == "agency_id":
                if item.get(key) not in {None, expected}:
                    return False
            elif key == "airline_code":
                if self._carrier(expected) not in self._record_carriers(item):
                    return False
            elif key in {"carrier_code", "marketing_carrier_code", "operating_carrier_code", "validating_carrier_code"}:
                if self._carrier(item.get(key) or "") != self._carrier(expected):
                    return False
            elif key in {"relationship_type", "relationship_status", "rule_status", "service_family", "service_code", "publication_status", "confidence", "freshness_status"}:
                if self._code(item.get(key)) != self._code(expected):
                    return False
            elif isinstance(item.get(key), list):
                if self._code(expected) not in {self._code(value) for value in item.get(key) or []}:
                    return False
        return True

    def _scope_matches(self, rule: dict[str, Any], segment: dict[str, Any], travel_date: date | None) -> bool:
        if travel_date:
            start = self._date_value(rule.get("effective_from"))
            end = self._date_value(rule.get("effective_until"))
            if start and travel_date < start or end and travel_date > end:
                return False
        route_scope = {self._code(value) for value in rule.get("route_scope") or []}
        if route_scope and self._code(self._segment_route(segment)) not in route_scope:
            return False
        market_scope = {self._code(value) for value in rule.get("market_scope") or []}
        if market_scope and self._code(segment.get("market")) not in market_scope:
            return False
        return True

    def _normalize_segment(self, value: Any, index: int) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise InterlineCodeshareIntelligenceError(f"Segment {index + 1} must be an object.")
        segment = dict(value)
        for role in CARRIER_ROLES:
            if segment.get(role):
                segment[role] = self._carrier(segment[role])
        segment.setdefault("segment_reference", f"SEG-{index + 1}")
        if not segment.get("marketing_carrier") or not segment.get("operating_carrier"):
            raise InterlineCodeshareIntelligenceError(f"Segment {segment['segment_reference']} requires marketing and operating carrier codes.")
        return segment

    async def _require(self, entity_type: str, record_id: str) -> dict[str, Any]:
        _, config = self._config(entity_type)
        record = await self.db.collection(config["collection"]).find_one({"id": record_id})
        if not record:
            record = await self.db.collection(config["collection"]).find_one({config["reference"]: record_id})
        if not record:
            raise InterlineCodeshareIntelligenceError(f"{entity_type.replace('-', ' ').title()} metadata was not found.")
        return record

    def _config(self, entity_type: str) -> tuple[str, dict[str, Any]]:
        normalized = self._code(entity_type).replace("_", "-")
        aliases = {"relationship": "relationships", "interline": "interline-agreements", "codeshare": "codeshare-rules", "operating": "operating-carrier-rules", "validating": "validating-carrier-rules", "through-check": "through-check-rules", "baggage": "baggage-rules", "service": "service-responsibility-rules", "emd": "interline-emd-rules"}
        normalized = aliases.get(normalized, normalized)
        if normalized not in ENTITY_CONFIG:
            raise InterlineCodeshareIntelligenceError(f"Unsupported interline intelligence entity type: {entity_type}.")
        return normalized, ENTITY_CONFIG[normalized]

    async def _audit(self, event_type: str, item: dict[str, Any], user: dict[str, Any]) -> None:
        await self.db.collection("audit_events").insert_one(AuditEvent(
            agency_id=item.get("agency_id"),
            actor_user_id=user.get("id"),
            event_type=event_type,
            entity_type="interline_codeshare_intelligence",
            entity_id=item["id"],
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata={"carriers": sorted(self._record_carriers(item)), "status": self._record_status(item), "metadata_only": True},
        ).model_dump(mode="json"))

    def _trace(self, item: dict[str, Any]) -> dict[str, Any]:
        return {"id": item.get("id"), "reference": next((item.get(key) for key in REFERENCE_FIELDS if item.get(key)), None), "status": self._record_status(item), "confidence": item.get("confidence"), "freshness_status": item.get("freshness_status"), "evidence_link_ids": item.get("evidence_link_ids") or []}

    def _best(self, records: list[dict[str, Any]]) -> dict[str, Any] | None:
        rank = {"supported": 0, "route_specific": 1, "market_specific": 1, "conditional": 2, "manual_only": 3, "unknown": 4, "unsupported": 5}
        return sorted(records, key=lambda item: (rank.get(self._record_status(item), 9), 0 if item.get("confidence") in {"official", "high"} else 1))[0] if records else None

    def _owner(self, record: dict[str, Any] | None, field: str) -> str | None:
        value = (record or {}).get(field)
        return self._carrier(value) if value else None

    def _record_status(self, item: dict[str, Any]) -> str:
        for field in ["rule_status", "relationship_status", "agreement_status", "interline_emd_status"]:
            if item.get(field):
                return self._code(item[field])
        return "unknown"

    def _record_carriers(self, item: dict[str, Any]) -> set[str]:
        carriers = set()
        for key, value in item.items():
            if ("carrier" in key or key in {"airline_code", "partner_airline_code"}) and isinstance(value, str) and value:
                carriers.add(self._carrier(value))
        return carriers

    def _record_has_carrier(self, item: dict[str, Any], carriers: set[str]) -> bool:
        if not carriers:
            return False
        values = self._record_carriers(item)
        for key in ["airline_codes", "recommended_airline_codes", "candidate_airline_codes"]:
            values.update(self._carrier(value) for value in item.get(key) or [])
        return bool(values & carriers)

    def _primary_carrier(self, item: dict[str, Any]) -> str:
        for field in ["airline_code", "marketing_carrier_code", "operating_carrier_code", "validating_carrier_code", "carrier_a_code"]:
            if item.get(field):
                return str(item[field])
        return ""

    def _pair_matches(self, left: Any, right: Any, first: Any, second: Any) -> bool:
        return {self._carrier(left), self._carrier(right)} == {self._carrier(first), self._carrier(second)}

    def _segment_route(self, segment: dict[str, Any]) -> str:
        return f"{str(segment.get('origin') or '').upper()}-{str(segment.get('destination') or '').upper()}".strip("-")

    def _unique_owners(self, values: list[Any]) -> dict[str, Any]:
        owners = sorted({self._carrier(value) for value in values if value})
        return {"status": "resolved" if len(owners) == 1 else "multiple" if len(owners) > 1 else "unknown", "owners": owners}

    def _recommended_action(self, outcome: str) -> str:
        return {
            "responsibilities_resolved": "Review the governed responsibility trace with an authorized agent before operational action.",
            "manual_review_required": "Resolve unknown or conditional ownership with the responsible carrier desks before fulfillment.",
            "unsupported_combination": "Do not assume continuity; obtain explicit carrier confirmation or select a supported alternative.",
        }[outcome]

    def _date_value(self, value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
        return None

    def _choice(self, value: Any, choices: list[str], label: str) -> str:
        normalized = self._code(value)
        if normalized not in set(choices):
            raise InterlineCodeshareIntelligenceError(f"Unsupported {label}: {value or 'unset'}.")
        return normalized

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def _carrier(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _sort_text(self, value: Any) -> str:
        return value.isoformat() if isinstance(value, (date, datetime)) else str(value or "")
