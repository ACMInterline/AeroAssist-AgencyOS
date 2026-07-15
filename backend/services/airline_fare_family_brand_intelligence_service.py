from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineBaggageAllowanceRule,
    AirlineBaggageException,
    AirlineBookingClassMapping,
    AirlineBrandComparisonProfile,
    AirlineCommercialBundle,
    AirlineFareBrandAttribute,
    AirlineFareFamily,
    AirlineFareFamilyEvidenceLink,
    AuditEvent,
)


PHASE_LABEL = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"

AIRLINE_FARE_FAMILIES_COLLECTION = "airline_fare_families"
AIRLINE_FARE_BRAND_ATTRIBUTES_COLLECTION = "airline_fare_brand_attributes"
AIRLINE_BOOKING_CLASS_MAPPINGS_COLLECTION = "airline_booking_class_mappings"
AIRLINE_BAGGAGE_ALLOWANCE_RULES_COLLECTION = "airline_baggage_allowance_rules"
AIRLINE_BAGGAGE_EXCEPTIONS_COLLECTION = "airline_baggage_exceptions"
AIRLINE_COMMERCIAL_BUNDLES_COLLECTION = "airline_commercial_bundles"
AIRLINE_FARE_FAMILY_EVIDENCE_LINKS_COLLECTION = "airline_fare_family_evidence_links"
AIRLINE_BRAND_COMPARISON_PROFILES_COLLECTION = "airline_brand_comparison_profiles"

FARE_BRAND_INTELLIGENCE_COLLECTIONS = [
    AIRLINE_FARE_FAMILIES_COLLECTION,
    AIRLINE_FARE_BRAND_ATTRIBUTES_COLLECTION,
    AIRLINE_BOOKING_CLASS_MAPPINGS_COLLECTION,
    AIRLINE_BAGGAGE_ALLOWANCE_RULES_COLLECTION,
    AIRLINE_BAGGAGE_EXCEPTIONS_COLLECTION,
    AIRLINE_COMMERCIAL_BUNDLES_COLLECTION,
    AIRLINE_FARE_FAMILY_EVIDENCE_LINKS_COLLECTION,
    AIRLINE_BRAND_COMPARISON_PROFILES_COLLECTION,
]

COMMERCIAL_ATTRIBUTE_CODES = [
    "seat_selection",
    "changeability",
    "refundability",
    "same_day_change",
    "priority",
    "lounge",
    "meals",
    "fast_track",
    "mileage_accrual",
    "no_show_conditions",
    "ancillary_inclusion",
]

ATTRIBUTE_STATUSES = ["included", "not_included", "chargeable", "conditional", "variable", "unknown", "not_applicable"]
MAPPING_STATUSES = ["known", "variable", "unknown", "not_applicable"]
ALLOWANCE_STATUSES = ["known", "conditional", "variable", "unknown", "not_included"]
BAGGAGE_CONCEPTS = ["piece", "weight", "hybrid", "unknown"]
INTERLINE_BAGGAGE_STATUSES = ["supported", "unsupported", "conditional", "variable", "unknown"]
EXCEPTION_TYPES = ["passenger_type", "status_member", "route", "market", "codeshare", "interline", "special_item", "distribution_channel", "other"]
EXCEPTION_STATUSES = ["active", "conditional", "unknown", "inactive", "archived"]
CONFIDENCE_LEVELS = ["official", "high", "medium", "low", "unknown"]
FRESHNESS_STATUSES = ["current", "review_due", "stale", "expired", "unknown"]
PUBLICATION_STATUSES = ["draft", "under_review", "approved", "published", "archived"]
AGENCY_VISIBILITY_STATUSES = ["platform_only", "all_agencies", "selected_agencies"]

ENTITY_CONFIG: dict[str, dict[str, Any]] = {
    "fare-families": {"collection": AIRLINE_FARE_FAMILIES_COLLECTION, "model": AirlineFareFamily, "reference": "fare_family_reference", "prefix": "AFF"},
    "attributes": {"collection": AIRLINE_FARE_BRAND_ATTRIBUTES_COLLECTION, "model": AirlineFareBrandAttribute, "reference": "attribute_reference", "prefix": "AFA"},
    "rbd-mappings": {"collection": AIRLINE_BOOKING_CLASS_MAPPINGS_COLLECTION, "model": AirlineBookingClassMapping, "reference": "booking_class_mapping_reference", "prefix": "ABM"},
    "baggage-rules": {"collection": AIRLINE_BAGGAGE_ALLOWANCE_RULES_COLLECTION, "model": AirlineBaggageAllowanceRule, "reference": "baggage_rule_reference", "prefix": "ABG"},
    "baggage-exceptions": {"collection": AIRLINE_BAGGAGE_EXCEPTIONS_COLLECTION, "model": AirlineBaggageException, "reference": "baggage_exception_reference", "prefix": "ABX"},
    "commercial-bundles": {"collection": AIRLINE_COMMERCIAL_BUNDLES_COLLECTION, "model": AirlineCommercialBundle, "reference": "commercial_bundle_reference", "prefix": "ACB"},
    "evidence-links": {"collection": AIRLINE_FARE_FAMILY_EVIDENCE_LINKS_COLLECTION, "model": AirlineFareFamilyEvidenceLink, "reference": "fare_family_evidence_reference", "prefix": "AFE"},
    "comparison-profiles": {"collection": AIRLINE_BRAND_COMPARISON_PROFILES_COLLECTION, "model": AirlineBrandComparisonProfile, "reference": "comparison_profile_reference", "prefix": "ABC"},
}

INTERNAL_FIELDS = {
    "internal_notes",
    "visible_agency_ids",
    "evidence_link_ids",
    "source_metadata_json",
    "metadata",
    "legacy_rbd_matrix_row_id",
    "evidence_source_id",
    "evidence_artifact_id",
    "evidence_assertion_id",
    "evidence_link_id",
    "internal_column_notes",
}


class AirlineFareFamilyBrandIntelligenceError(ValueError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class AirlineFareFamilyBrandIntelligenceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "commercial_product_intelligence_only": True,
            "canonical_fare_family_reused": True,
            "live_availability_disabled": True,
            "live_pricing_disabled": True,
            "fare_pricing_engine_disabled": True,
            "fare_quote_commitment_disabled": True,
            "provider_connectivity_disabled": True,
            "booking_execution_disabled": True,
            "ticketing_execution_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "unknown_and_variable_states_preserved": True,
            "interline_uncertainty_preserved": True,
            "client_internal_separation_enabled": True,
            "evidence_governance_integration_enabled": True,
            "knowledge_versioning_integration_enabled": True,
            "offer_builder_integration_enabled": True,
            "agency_published_read_only": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "entity_types": list(ENTITY_CONFIG),
            "commercial_attribute_codes": COMMERCIAL_ATTRIBUTE_CODES,
            "attribute_statuses": ATTRIBUTE_STATUSES,
            "mapping_statuses": MAPPING_STATUSES,
            "allowance_statuses": ALLOWANCE_STATUSES,
            "baggage_concepts": BAGGAGE_CONCEPTS,
            "interline_baggage_statuses": INTERLINE_BAGGAGE_STATUSES,
            "exception_types": EXCEPTION_TYPES,
            "exception_statuses": EXCEPTION_STATUSES,
            "freshness_statuses": FRESHNESS_STATUSES,
            "publication_statuses": PUBLICATION_STATUSES,
            "agency_visibility_statuses": AGENCY_VISIBILITY_STATUSES,
        }

    async def create_record(self, entity_type: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        data = payload_dict(payload)
        data.setdefault(config["reference"], self._reference(config["prefix"]))
        normalized = await self._normalize_and_validate(entity_type, data)
        record = config["model"](**normalized).model_dump(mode="json")
        created = await self.db.collection(config["collection"]).insert_one(record)
        await self._audit(f"airline_fare_brand_intelligence.{entity_type}.created", created, user)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": created, **self.safety_flags()}

    async def update_record(self, entity_type: str, record_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        existing = await self._require(entity_type, record_id)
        normalized = await self._normalize_and_validate(entity_type, {**existing, **payload_dict(payload)}, current_id=existing["id"])
        validated = config["model"](**normalized).model_dump(mode="json")
        immutable = {"id", "created_at", "agency_id", "airline_id", config["reference"]}
        updates = {key: value for key, value in validated.items() if key not in immutable}
        updated = await self.db.collection(config["collection"]).update_one({"id": existing["id"]}, updates)
        await self._audit(f"airline_fare_brand_intelligence.{entity_type}.updated", updated or existing, user)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": updated or existing, **self.safety_flags()}

    async def get_record(self, entity_type: str, record_id: str) -> dict[str, Any]:
        entity_type, _ = self._config(entity_type)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": await self._require(entity_type, record_id), **self.safety_flags()}

    async def list_records(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        entity_type, config = self._config(entity_type)
        records = await self.db.collection(config["collection"]).find_many()
        records = [item for item in records if self._matches_filters(item, filters)]
        records.sort(key=lambda item: (self._airline(item.get("airline_code")), int(item.get("display_order") or item.get("hierarchy_rank") or 0), self._sort_text(item.get("updated_at"))))
        return records

    async def list_agency_records(self, entity_type: str, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        normalized, _ = self._config(entity_type)
        records = await self.list_records(normalized, **filters)
        return [
            self._agency_projection(normalized, item)
            for item in records
            if self._agency_visible(normalized, item, agency_id)
        ]

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        records = {key: await self.list_records(key, **filters) for key in ENTITY_CONFIG}
        return {
            "phase": PHASE_LABEL,
            "summary": self._summary(records),
            "fare_families": records["fare-families"],
            "hierarchy": self._hierarchy(records["fare-families"]),
            "attributes": records["attributes"],
            "rbd_mappings": records["rbd-mappings"],
            "baggage_rules": records["baggage-rules"],
            "baggage_exceptions": records["baggage-exceptions"],
            "commercial_bundles": records["commercial-bundles"],
            "evidence_links": records["evidence-links"],
            "comparison_profiles": records["comparison-profiles"],
            "stale_or_incomplete": self._stale_or_incomplete(records),
            "legacy_context": await self._legacy_context(filters.get("airline_code")),
            "filters": self.filter_metadata(),
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        records: dict[str, list[dict[str, Any]]] = {}
        for entity_type in ENTITY_CONFIG:
            records[entity_type] = await self.list_agency_records(entity_type, agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self._summary(records),
            "fare_families": records["fare-families"],
            "hierarchy": self._hierarchy(records["fare-families"]),
            "attributes": records["attributes"],
            "rbd_mappings": records["rbd-mappings"],
            "baggage_rules": records["baggage-rules"],
            "baggage_exceptions": records["baggage-exceptions"],
            "commercial_bundles": records["commercial-bundles"],
            "comparison_profiles": records["comparison-profiles"],
            "operational_caveats": self._agency_caveats(records),
            "filters": self.filter_metadata(),
            "read_only": True,
            **self.safety_flags(),
        }

    async def resolve_rbd(self, payload: Any, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        data = payload_dict(payload)
        airline_code = self._airline(data.get("airline_code"))
        rbd_code = self._airline(data.get("rbd_code"))
        if not airline_code or not rbd_code:
            raise AirlineFareFamilyBrandIntelligenceError("Airline code and RBD code are required.")
        mappings = await self.list_records("rbd-mappings", airline_code=airline_code, rbd_code=rbd_code)
        mappings = self._visibility_scope("rbd-mappings", mappings, agency_id, agency_safe)
        applicable = [item for item in mappings if self._context_matches(item, data)]
        mapping = self._best_scoped(applicable, data)
        family = await self._family_from_mapping(mapping, agency_id, agency_safe) if mapping else None
        status = (mapping or {}).get("mapping_status") or "unknown"
        warnings = []
        if not mapping:
            warnings.append("No governed RBD-to-brand mapping is available.")
        elif status in {"unknown", "variable"} or mapping.get("variable_by_fare_basis"):
            warnings.append("RBD mapping is variable or unknown and requires fare-basis review.")
        return {
            "phase": PHASE_LABEL,
            "airline_code": airline_code,
            "rbd_code": rbd_code,
            "mapping_status": status,
            "mapping": self._agency_projection("rbd-mappings", mapping) if mapping and agency_safe else mapping,
            "fare_family": self._agency_projection("fare-families", family) if family and agency_safe else family,
            "warnings": warnings,
            "manual_review_required": bool(warnings),
            "read_only": True,
            **self.safety_flags(),
        }

    async def resolve_baggage(self, payload: Any, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        context = payload_dict(payload)
        airline_code = self._airline(context.get("airline_code"))
        if not airline_code:
            raise AirlineFareFamilyBrandIntelligenceError("Airline code is required for baggage allowance resolution.")
        family = await self._resolve_family(context, agency_id, agency_safe)
        if family:
            context.setdefault("fare_family_id", family["id"])
            context.setdefault("brand_code", family.get("brand_code") or family.get("family_code"))
            context.setdefault("cabin", family.get("cabin"))
        rules = await self.list_records("baggage-rules", airline_code=airline_code)
        rules = self._visibility_scope("baggage-rules", rules, agency_id, agency_safe)
        rules = [item for item in rules if self._context_matches(item, context) and self._family_matches(item, context)]
        rule = self._best_scoped(rules, context)
        warnings: list[str] = []
        caveats: list[str] = []
        applied_exceptions: list[dict[str, Any]] = []
        allowance = self._allowance_snapshot(rule)
        if not rule:
            warnings.append("No governed baggage allowance rule matches this fare context.")
        else:
            exceptions = await self.list_records("baggage-exceptions", airline_code=airline_code)
            exceptions = self._visibility_scope("baggage-exceptions", exceptions, agency_id, agency_safe)
            for exception in sorted(exceptions, key=lambda item: int(item.get("priority") or 100)):
                if self._exception_matches(exception, context, rule):
                    allowance.update(exception.get("allowance_overrides") or {})
                    allowance["special_item_inclusions"] = self._ordered_union(allowance.get("special_item_inclusions"), exception.get("special_item_inclusions"))
                    allowance["special_item_exclusions"] = self._ordered_union(allowance.get("special_item_exclusions"), exception.get("special_item_exclusions"))
                    applied_exceptions.append(self._trace(exception))
                    if exception.get("warning_message"):
                        warnings.append(str(exception["warning_message"]))
                    if exception.get("client_safe_message"):
                        caveats.append(str(exception["client_safe_message"]))
            self._apply_passenger_and_status_allowance(allowance, rule, context)

        interline = await self._interline_baggage_assessment(context, agency_id, agency_safe)
        if interline["uncertain"]:
            warnings.append(interline["warning"])
            caveats.append("Baggage allowance may differ on flights operated by another carrier.")
        if rule and rule.get("allowance_status") in {"unknown", "variable", "conditional"}:
            warnings.append(f"Baggage allowance status is {rule.get('allowance_status')}; verify the fare basis and ticketed itinerary.")
        return {
            "phase": PHASE_LABEL,
            "airline_code": airline_code,
            "fare_family": self._client_family(family),
            "allowance": allowance,
            "allowance_summary": self._baggage_summary(allowance),
            "applied_rule": self._trace(rule) if rule else None,
            "applied_exceptions": applied_exceptions,
            "interline_assessment": interline,
            "warnings": self._ordered_union([], warnings),
            "operational_caveats": self._ordered_union([], caveats),
            "manual_review_required": bool(warnings),
            "live_price_or_availability_asserted": False,
            "read_only": True,
            **self.safety_flags(),
        }

    async def compare_brands(self, payload: Any, *, agency_id: str | None = None, agency_safe: bool = False) -> dict[str, Any]:
        data = payload_dict(payload)
        requested = set(data.get("fare_family_ids") or [])
        families = await self.list_records("fare-families", airline_code=data.get("airline_code"))
        families = self._visibility_scope("fare-families", families, agency_id, agency_safe)
        if requested:
            families = [item for item in families if item.get("id") in requested or item.get("family_code") in requested or item.get("brand_code") in requested]
        if not families:
            raise AirlineFareFamilyBrandIntelligenceError("No governed fare families match the comparison request.")
        attribute_codes = data.get("attribute_codes") or COMMERCIAL_ATTRIBUTE_CODES
        rows = []
        for family in families:
            attributes = await self.list_records("attributes", fare_family_id=family["id"])
            attributes = self._visibility_scope("attributes", attributes, agency_id, agency_safe)
            attributes = [item for item in attributes if self._context_matches(item, data)]
            by_code = {item.get("attribute_code"): item for item in attributes}
            baggage = await self.resolve_baggage({**data, "airline_code": family.get("airline_code"), "fare_family_id": family["id"], "cabin": family.get("cabin")}, agency_id=agency_id, agency_safe=agency_safe)
            rows.append({
                "fare_family_id": family["id"],
                "airline_code": family.get("airline_code"),
                "brand_code": family.get("brand_code") or family.get("family_code"),
                "label": family.get("client_safe_label") or family.get("commercial_name") or family.get("family_name"),
                "cabin": family.get("cabin"),
                "hierarchy_level": family.get("hierarchy_level", 0),
                "attributes": {code: self._client_attribute(by_code.get(code), code) for code in attribute_codes},
                "baggage_summary": baggage["allowance_summary"],
                "operational_caveats": baggage["operational_caveats"],
                "warnings": baggage["warnings"],
            })
        rows.sort(key=lambda item: (item["airline_code"] or "", item["hierarchy_level"], item["label"] or ""))
        return {
            "phase": PHASE_LABEL,
            "comparison_title": data.get("comparison_title") or "Fare brand comparison",
            "rows": rows,
            "attribute_codes": attribute_codes,
            "client_safe": True,
            "internal_evidence_excluded": agency_safe,
            "read_only": True,
            **self.safety_flags(),
        }

    async def offer_builder_attributes(self, payload: Any, *, agency_id: str | None = None, agency_safe: bool = True) -> dict[str, Any]:
        data = payload_dict(payload)
        family = await self._resolve_family(data, agency_id, agency_safe)
        rbd = await self.resolve_rbd(data, agency_id=agency_id, agency_safe=agency_safe) if data.get("rbd_code") else None
        if not family and rbd:
            family = rbd.get("fare_family")
            if family:
                data["fare_family_id"] = family.get("id")
        attributes = []
        if family:
            attributes = await self.list_records("attributes", fare_family_id=family["id"])
            attributes = self._visibility_scope("attributes", attributes, agency_id, agency_safe)
        baggage = await self.resolve_baggage(data, agency_id=agency_id, agency_safe=agency_safe)
        commercial = {item.get("attribute_code"): self._client_attribute(item, item.get("attribute_code")) for item in attributes}
        return {
            "fare_family": self._client_family(family),
            "rbd_mapping": rbd,
            "commercial_attributes": commercial,
            "baggage": baggage,
            "flexibility_summary": self._flexibility_summary(commercial),
            "service_inclusions": [value for key, value in commercial.items() if value.get("status") == "included"],
            "operational_caveats": baggage.get("operational_caveats") or [],
            "manual_review_required": baggage.get("manual_review_required") or bool(rbd and rbd.get("manual_review_required")),
            "offer_builder_should_not_invent_intelligence": True,
            "live_price_or_availability_asserted": False,
            "read_only": True,
            **self.safety_flags(),
        }

    async def offer_builder_package_attributes(self, item: dict[str, Any]) -> dict[str, Any]:
        agency_id = item.get("agency_id")
        metadata = item.get("metadata") or {}
        requested = metadata.get("fare_family_ids") or []
        airline_codes = item.get("recommended_airlines") or []
        families = []
        for airline in airline_codes:
            airline_code = airline.get("airline_code") if isinstance(airline, dict) else airline
            source = await self.list_records("fare-families", airline_code=airline_code)
            source = self._visibility_scope("fare-families", source, agency_id, True)
            families.extend([family for family in source if not requested or family.get("id") in requested or family.get("family_code") in requested])
        return {
            "fare_family_count": len(families),
            "fare_families": [self._client_family(item) for item in families],
            "source": "published_fare_brand_intelligence",
            "availability_asserted": False,
            "pricing_calculated": False,
            "metadata_only": True,
        }

    async def coverage(self) -> dict[str, Any]:
        counts = {name: await self.db.collection(name).count() for name in FARE_BRAND_INTELLIGENCE_COLLECTIONS}
        families = await self.db.collection(AIRLINE_FARE_FAMILIES_COLLECTION).find_many()
        attributes = await self.db.collection(AIRLINE_FARE_BRAND_ATTRIBUTES_COLLECTION).find_many()
        mappings = await self.db.collection(AIRLINE_BOOKING_CLASS_MAPPINGS_COLLECTION).find_many()
        baggage = await self.db.collection(AIRLINE_BAGGAGE_ALLOWANCE_RULES_COLLECTION).find_many()
        return {
            "fare_brand_intelligence_collection_counts": counts,
            "fare_family_count": len(families),
            "fare_brand_attribute_count": len(attributes),
            "rbd_mapping_count": len(mappings),
            "baggage_allowance_rule_count": len(baggage),
            "published_fare_family_count": len([item for item in families if item.get("publication_status") == "published"]),
            "stale_fare_family_count": len([item for item in families if item.get("freshness_status") in {"stale", "expired", "review_due"}]),
            "incomplete_fare_family_count": len([item for item in families if not item.get("airline_code") or not (item.get("brand_code") or item.get("family_code")) or not item.get("cabin")]),
            "unknown_rbd_mapping_count": len([item for item in mappings if item.get("mapping_status") in {"unknown", "variable"}]),
            "unknown_baggage_rule_count": len([item for item in baggage if item.get("allowance_status") in {"unknown", "variable"}]),
        }

    async def _normalize_and_validate(self, entity_type: str, data: dict[str, Any], current_id: str | None = None) -> dict[str, Any]:
        data["metadata_only"] = True
        if data.get("airline_code"):
            data["airline_code"] = self._airline(data["airline_code"])
        if entity_type == "fare-families":
            await self._normalize_family(data)
            await self._validate_hierarchy(data, current_id)
        elif not data.get("airline_code") and entity_type != "comparison-profiles":
            raise AirlineFareFamilyBrandIntelligenceError("Airline code is required for fare-brand intelligence metadata.")
        if entity_type == "attributes":
            data["attribute_code"] = self._choice(data.get("attribute_code"), COMMERCIAL_ATTRIBUTE_CODES, "commercial attribute")
            data["attribute_status"] = self._choice(data.get("attribute_status") or "unknown", ATTRIBUTE_STATUSES, "attribute status")
            await self._validate_family_link(data)
        elif entity_type == "rbd-mappings":
            data["rbd_code"] = self._airline(data.get("rbd_code"))
            if not data["rbd_code"]:
                raise AirlineFareFamilyBrandIntelligenceError("RBD code is required.")
            data["mapping_status"] = self._choice(data.get("mapping_status") or "unknown", MAPPING_STATUSES, "RBD mapping status")
            data["upgrade_to_rbd_codes"] = [self._airline(value) for value in data.get("upgrade_to_rbd_codes") or []]
            data["downgrade_to_rbd_codes"] = [self._airline(value) for value in data.get("downgrade_to_rbd_codes") or []]
            if data.get("fare_family_id"):
                await self._validate_family_link(data)
            if not data.get("legacy_rbd_matrix_row_id"):
                data["legacy_rbd_matrix_row_id"] = await self._legacy_rbd_id(data)
        elif entity_type == "baggage-rules":
            data["allowance_status"] = self._choice(data.get("allowance_status") or "unknown", ALLOWANCE_STATUSES, "baggage allowance status")
            data["baggage_concept"] = self._choice(data.get("baggage_concept") or "unknown", BAGGAGE_CONCEPTS, "baggage concept")
            data["codeshare_interline_status"] = self._choice(
                data.get("codeshare_interline_status") or "unknown",
                INTERLINE_BAGGAGE_STATUSES,
                "codeshare/interline baggage status",
            )
            if data.get("fare_family_id"):
                await self._validate_family_link(data)
        elif entity_type == "baggage-exceptions":
            data["exception_type"] = self._choice(data.get("exception_type"), EXCEPTION_TYPES, "baggage exception type")
            data["exception_status"] = self._choice(data.get("exception_status") or "unknown", EXCEPTION_STATUSES, "baggage exception status")
        elif entity_type == "commercial-bundles":
            data["bundle_status"] = self._choice(data.get("bundle_status") or "unknown", ATTRIBUTE_STATUSES, "commercial bundle status")
        elif entity_type == "evidence-links":
            await self._validate_evidence_link(data)
        for field, choices in [("confidence", CONFIDENCE_LEVELS), ("freshness_status", FRESHNESS_STATUSES), ("publication_status", PUBLICATION_STATUSES), ("agency_visibility_status", AGENCY_VISIBILITY_STATUSES)]:
            if field in data:
                data[field] = self._choice(data.get(field), choices, field.replace("_", " "))
        return data

    async def _normalize_family(self, data: dict[str, Any]) -> None:
        airline_id = data.get("airline_id") or data.get("canonical_airline_id")
        profile = None
        if not airline_id and data.get("airline_code"):
            profile = await self._airline_profile(data["airline_code"])
            airline_id = (profile or {}).get("id")
        if not airline_id:
            raise AirlineFareFamilyBrandIntelligenceError("Canonical airline id or resolvable airline code is required.")
        data["airline_id"] = airline_id
        data.setdefault("canonical_airline_id", airline_id)
        if not data.get("airline_code"):
            profile = profile or await self.db.collection("airline_profiles").find_one({"id": airline_id})
            data["airline_code"] = self._airline((profile or {}).get("airline_code") or (profile or {}).get("iata_code"))
        data["family_code"] = self._airline(data.get("family_code") or data.get("brand_code"))
        data["brand_code"] = self._airline(data.get("brand_code") or data.get("family_code"))
        if not data["family_code"]:
            raise AirlineFareFamilyBrandIntelligenceError("Fare family or brand code is required.")
        data["family_name"] = data.get("family_name") or data.get("commercial_name") or data["family_code"]
        data["commercial_name"] = data.get("commercial_name") or data["family_name"]
        data["client_safe_label"] = data.get("client_safe_label") or data["commercial_name"]
        if not data.get("fare_family_reference"):
            data["fare_family_reference"] = self._reference("AFF")

    async def _validate_hierarchy(self, data: dict[str, Any], current_id: str | None) -> None:
        parent_id = data.get("parent_fare_family_id")
        if not parent_id:
            data["hierarchy_level"] = max(0, int(data.get("hierarchy_level") or 0))
            return
        if parent_id == current_id:
            raise AirlineFareFamilyBrandIntelligenceError("Fare family cannot be its own parent.")
        parent = await self.db.collection(AIRLINE_FARE_FAMILIES_COLLECTION).find_one({"id": parent_id})
        if not parent:
            raise AirlineFareFamilyBrandIntelligenceError("Parent fare family metadata was not found.")
        if self._airline(parent.get("airline_code")) != self._airline(data.get("airline_code")):
            raise AirlineFareFamilyBrandIntelligenceError("Parent and child fare families must belong to the same airline.")
        ancestor = parent
        seen = {current_id} if current_id else set()
        while ancestor and ancestor.get("parent_fare_family_id"):
            if ancestor.get("parent_fare_family_id") in seen:
                raise AirlineFareFamilyBrandIntelligenceError("Fare family hierarchy cycle detected.")
            seen.add(ancestor["id"])
            ancestor = await self.db.collection(AIRLINE_FARE_FAMILIES_COLLECTION).find_one({"id": ancestor["parent_fare_family_id"]})
        data["parent_family_code"] = parent.get("family_code")
        data["hierarchy_level"] = int(parent.get("hierarchy_level") or 0) + 1

    async def _validate_family_link(self, data: dict[str, Any]) -> None:
        family = await self.db.collection(AIRLINE_FARE_FAMILIES_COLLECTION).find_one({"id": data.get("fare_family_id")})
        if not family:
            raise AirlineFareFamilyBrandIntelligenceError("Linked fare family metadata was not found.")
        if self._airline(family.get("airline_code")) != self._airline(data.get("airline_code")):
            raise AirlineFareFamilyBrandIntelligenceError("Linked fare family must belong to the same airline.")
        data.setdefault("brand_code", family.get("brand_code") or family.get("family_code"))

    async def _validate_evidence_link(self, data: dict[str, Any]) -> None:
        target_type = self._config(data.get("target_type"))[0]
        if target_type == "evidence-links":
            raise AirlineFareFamilyBrandIntelligenceError("Evidence links cannot target another fare-brand evidence link.")
        target = await self.db.collection(ENTITY_CONFIG[target_type]["collection"]).find_one({"id": data.get("target_id")})
        if not target:
            raise AirlineFareFamilyBrandIntelligenceError("Fare-brand evidence target metadata was not found.")
        if not any(data.get(field) for field in ["evidence_source_id", "evidence_artifact_id", "evidence_assertion_id", "evidence_link_id"]):
            raise AirlineFareFamilyBrandIntelligenceError("At least one governed evidence reference is required.")

    async def _resolve_family(self, context: dict[str, Any], agency_id: str | None, agency_safe: bool) -> dict[str, Any] | None:
        families = await self.list_records("fare-families", airline_code=context.get("airline_code"))
        families = self._visibility_scope("fare-families", families, agency_id, agency_safe)
        family_id = context.get("fare_family_id")
        brand = self._airline(context.get("brand_code") or context.get("fare_family_code"))
        return next((item for item in families if (family_id and item.get("id") == family_id) or (brand and brand in {self._airline(item.get("brand_code")), self._airline(item.get("family_code"))})), None)

    async def _family_from_mapping(self, mapping: dict[str, Any] | None, agency_id: str | None, agency_safe: bool) -> dict[str, Any] | None:
        if not mapping or not mapping.get("fare_family_id"):
            return None
        family = await self.db.collection(AIRLINE_FARE_FAMILIES_COLLECTION).find_one({"id": mapping["fare_family_id"]})
        if family and (not agency_safe or agency_id and self._agency_visible("fare-families", family, agency_id)):
            return family
        return None

    def _context_matches(self, item: dict[str, Any], context: dict[str, Any]) -> bool:
        if not self._date_matches(item, context.get("travel_date")):
            return False
        checks = [
            ("cabin", context.get("cabin")),
            ("distribution_channel_scope", context.get("distribution_channel")),
            ("route_scope", self._route(context)),
            ("market_scope", context.get("market")),
        ]
        for field, expected in checks:
            actual = item.get(field)
            if not expected:
                continue
            if isinstance(actual, list) and actual and self._code(expected) not in {self._code(value) for value in actual}:
                return False
            if field == "cabin" and actual and self._code(actual) != self._code(expected):
                return False
        if item.get("rbd_scope") and context.get("rbd_code") and self._airline(context["rbd_code"]) not in {self._airline(value) for value in item["rbd_scope"]}:
            return False
        return True

    def _family_matches(self, item: dict[str, Any], context: dict[str, Any]) -> bool:
        if item.get("fare_family_id") and context.get("fare_family_id") and item["fare_family_id"] != context["fare_family_id"]:
            return False
        if item.get("brand_code") and context.get("brand_code") and self._airline(item["brand_code"]) != self._airline(context["brand_code"]):
            return False
        return True

    def _exception_matches(self, item: dict[str, Any], context: dict[str, Any], rule: dict[str, Any]) -> bool:
        if item.get("exception_status") not in {"active", "conditional", "unknown"}:
            return False
        if item.get("baggage_rule_id") and item["baggage_rule_id"] != rule.get("id"):
            return False
        if not self._date_matches(item, context.get("travel_date")):
            return False
        scoped = [
            ("passenger_type_scope", context.get("passenger_type")),
            ("status_tier_scope", context.get("status_tier")),
            ("route_scope", self._route(context)),
            ("market_scope", context.get("market")),
            ("marketing_carrier_scope", context.get("marketing_carrier")),
            ("operating_carrier_scope", context.get("operating_carrier")),
            ("special_item_scope", context.get("special_item")),
        ]
        return all(not item.get(field) or expected and self._code(expected) in {self._code(value) for value in item.get(field) or []} for field, expected in scoped)

    def _best_scoped(self, items: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any] | None:
        def score(item: dict[str, Any]) -> tuple[int, int, str]:
            fields = ["fare_family_id", "brand_code", "cabin", "rbd_scope", "route_scope", "market_scope", "distribution_channel_scope"]
            specificity = sum(1 for field in fields if item.get(field))
            confidence = {"official": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}.get(item.get("confidence"), 5)
            return (-specificity, confidence, self._sort_text(item.get("updated_at")))
        return sorted(items, key=score)[0] if items else None

    def _allowance_snapshot(self, rule: dict[str, Any] | None) -> dict[str, Any]:
        if not rule:
            return {"status": "unknown", "baggage_concept": "unknown", "special_item_inclusions": [], "special_item_exclusions": []}
        fields = ["allowance_status", "baggage_concept", "cabin_baggage_pieces", "cabin_baggage_weight_kg", "personal_item_included", "checked_baggage_pieces", "checked_baggage_weight_kg", "checked_baggage_weight_per_piece_kg", "infant_allowance", "child_allowance", "special_item_inclusions", "special_item_exclusions", "codeshare_interline_status"]
        result = {field: rule.get(field) for field in fields}
        result["status"] = result.pop("allowance_status", "unknown")
        return result

    def _apply_passenger_and_status_allowance(self, allowance: dict[str, Any], rule: dict[str, Any], context: dict[str, Any]) -> None:
        passenger_type = self._code(context.get("passenger_type"))
        if passenger_type == "infant":
            allowance.update(rule.get("infant_allowance") or {})
        elif passenger_type == "child":
            allowance.update(rule.get("child_allowance") or {})
        status_tier = self._code(context.get("status_tier"))
        for exception in rule.get("status_member_exceptions") or []:
            tiers = {self._code(value) for value in exception.get("status_tiers") or []}
            if status_tier and status_tier in tiers:
                allowance.update(exception.get("allowance_overrides") or {})

    async def _interline_baggage_assessment(self, context: dict[str, Any], agency_id: str | None, agency_safe: bool) -> dict[str, Any]:
        marketing = self._airline(context.get("marketing_carrier") or context.get("airline_code"))
        operating = self._airline(context.get("operating_carrier") or context.get("airline_code"))
        if not marketing or not operating or marketing == operating:
            return {"uncertain": False, "status": "single_carrier_or_same_carrier", "warning": None, "responsibility_rule_id": None}
        rules = await self.db.collection("airline_baggage_responsibility_rules").find_many()
        matches = [item for item in rules if self._airline(item.get("marketing_carrier_code")) in {"", marketing} and self._airline(item.get("operating_carrier_code")) == operating]
        if agency_safe:
            matches = [
                item
                for item in matches
                if agency_id
                and item.get("agency_id") in {None, agency_id}
                and self._published_visible(item, agency_id)
            ]
        rule = matches[0] if matches else None
        status = (rule or {}).get("rule_status") or "unknown"
        uncertain = status != "supported" or not rule
        return {
            "uncertain": uncertain,
            "status": status,
            "warning": "Codeshare/interline baggage responsibility is not confirmed by a published supported rule." if uncertain else None,
            "responsibility_rule_id": (rule or {}).get("id"),
            "baggage_rule_owner": (rule or {}).get("baggage_rule_owner_carrier_code"),
        }

    def _baggage_summary(self, allowance: dict[str, Any]) -> str:
        if allowance.get("status") in {"unknown", None}:
            return "Baggage allowance unknown; verify fare basis and operating-carrier rules."
        parts = []
        if allowance.get("personal_item_included") is True:
            parts.append("personal item included")
        if allowance.get("cabin_baggage_pieces") is not None:
            text = f"{allowance['cabin_baggage_pieces']} cabin bag"
            if allowance.get("cabin_baggage_weight_kg") is not None:
                text += f" up to {allowance['cabin_baggage_weight_kg']:g} kg"
            parts.append(text)
        if allowance.get("checked_baggage_pieces") is not None:
            text = f"{allowance['checked_baggage_pieces']} checked bag"
            if allowance.get("checked_baggage_weight_per_piece_kg") is not None:
                text += f" up to {allowance['checked_baggage_weight_per_piece_kg']:g} kg each"
            parts.append(text)
        elif allowance.get("checked_baggage_weight_kg") is not None:
            parts.append(f"{allowance['checked_baggage_weight_kg']:g} kg checked baggage")
        return "; ".join(parts) if parts else "No included baggage is documented."

    def _client_attribute(self, item: dict[str, Any] | None, code: str | None) -> dict[str, Any]:
        if not item:
            return {"code": code, "label": str(code or "Attribute").replace("_", " ").title(), "status": "unknown", "value": "Not confirmed"}
        value = item.get("client_safe_value") or item.get("value_text")
        if value is None and item.get("value_boolean") is not None:
            value = "Included" if item.get("value_boolean") else "Not included"
        if value is None and item.get("value_number") is not None:
            value = f"{item['value_number']:g} {item.get('unit') or ''}".strip()
        return {"code": item.get("attribute_code"), "label": item.get("client_safe_label") or item.get("attribute_label"), "status": item.get("attribute_status"), "value": value or str(item.get("attribute_status") or "unknown").replace("_", " ")}

    def _client_family(self, family: dict[str, Any] | None) -> dict[str, Any] | None:
        if not family:
            return None
        return {"id": family.get("id"), "airline_code": family.get("airline_code"), "brand_code": family.get("brand_code") or family.get("family_code"), "label": family.get("client_safe_label") or family.get("commercial_name") or family.get("family_name"), "cabin": family.get("cabin"), "hierarchy_level": family.get("hierarchy_level", 0)}

    def _flexibility_summary(self, attributes: dict[str, dict[str, Any]]) -> str:
        change = attributes.get("changeability", {}).get("status", "unknown")
        refund = attributes.get("refundability", {}).get("status", "unknown")
        no_show = attributes.get("no_show_conditions", {}).get("status", "unknown")
        return f"Changes: {change.replace('_', ' ')}; refunds: {refund.replace('_', ' ')}; no-show: {no_show.replace('_', ' ')}."

    def _hierarchy(self, families: list[dict[str, Any]]) -> list[dict[str, Any]]:
        children: dict[str | None, list[dict[str, Any]]] = {}
        for family in families:
            children.setdefault(family.get("parent_fare_family_id"), []).append(family)
        def build(parent_id: str | None) -> list[dict[str, Any]]:
            nodes = []
            for family in sorted(children.get(parent_id, []), key=lambda item: (int(item.get("display_order") or 0), item.get("family_name") or "")):
                nodes.append({"id": family.get("id"), "airline_code": family.get("airline_code"), "brand_code": family.get("brand_code") or family.get("family_code"), "label": family.get("commercial_name") or family.get("family_name"), "cabin": family.get("cabin"), "hierarchy_level": family.get("hierarchy_level", 0), "children": build(family.get("id"))})
            return nodes
        return build(None)

    def _summary(self, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        families = records.get("fare-families", [])
        return {
            "airline_count": len({item.get("airline_code") for item in families if item.get("airline_code")}),
            "fare_family_count": len(families),
            "attribute_count": len(records.get("attributes", [])),
            "rbd_mapping_count": len(records.get("rbd-mappings", [])),
            "baggage_rule_count": len(records.get("baggage-rules", [])),
            "baggage_exception_count": len(records.get("baggage-exceptions", [])),
            "commercial_bundle_count": len(records.get("commercial-bundles", [])),
            "evidence_link_count": len(records.get("evidence-links", [])),
            "stale_or_incomplete_count": len(self._stale_or_incomplete(records)),
            "unknown_mapping_count": len([item for item in records.get("rbd-mappings", []) if item.get("mapping_status") in {"unknown", "variable"}]),
            "metadata_only": True,
        }

    def _stale_or_incomplete(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        findings = []
        for family in records.get("fare-families", []):
            reasons = []
            if family.get("freshness_status") in {"stale", "expired", "review_due", "unknown"}:
                reasons.append(f"freshness is {family.get('freshness_status') or 'unknown'}")
            if not family.get("airline_code") or not (family.get("brand_code") or family.get("family_code")) or not family.get("cabin"):
                reasons.append("required brand identity or cabin metadata is incomplete")
            if not family.get("evidence_link_ids"):
                reasons.append("no governed evidence link is recorded")
            if reasons:
                findings.append({"fare_family_id": family.get("id"), "airline_code": family.get("airline_code"), "brand_code": family.get("brand_code") or family.get("family_code"), "reasons": reasons})
        return findings

    def _agency_caveats(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        caveats = []
        for mapping in records.get("rbd-mappings", []):
            if mapping.get("mapping_status") in {"unknown", "variable"} or mapping.get("variable_by_fare_basis"):
                caveats.append({"type": "rbd_mapping", "record_id": mapping.get("id"), "message": f"RBD {mapping.get('rbd_code')} mapping is variable or unknown."})
        for rule in records.get("baggage-rules", []):
            if rule.get("allowance_status") in {"unknown", "variable", "conditional"} or rule.get("codeshare_interline_status") != "supported":
                caveats.append({"type": "baggage", "record_id": rule.get("id"), "message": "Baggage allowance requires fare-basis and operating-carrier review."})
        return caveats

    async def _legacy_context(self, airline_code: str | None) -> dict[str, Any]:
        profile = await self._airline_profile(airline_code) if airline_code else None
        airline_id = (profile or {}).get("id")
        rbd_rows = await self.db.collection("airline_rbd_matrix_rows").find_many()
        fare_rules = await self.db.collection("airline_fare_rules").find_many()
        ancillaries = await self.db.collection("airline_ancillaries").find_many()
        if airline_id:
            rbd_rows = [item for item in rbd_rows if item.get("airline_id") == airline_id]
            fare_rules = [item for item in fare_rules if item.get("airline_id") == airline_id]
            ancillaries = [item for item in ancillaries if item.get("airline_id") == airline_id]
        return {"rbd_matrix_row_ids": [item.get("id") for item in rbd_rows], "fare_rule_ids": [item.get("id") for item in fare_rules], "ancillary_ids": [item.get("id") for item in ancillaries], "canonical_fare_family_collection_reused": True, "legacy_records_preserved": True}

    async def _legacy_rbd_id(self, data: dict[str, Any]) -> str | None:
        family = await self.db.collection(AIRLINE_FARE_FAMILIES_COLLECTION).find_one({"id": data.get("fare_family_id")}) if data.get("fare_family_id") else None
        airline_id = (family or {}).get("airline_id") or (await self._airline_profile(data.get("airline_code")) or {}).get("id")
        rows = await self.db.collection("airline_rbd_matrix_rows").find_many()
        match = next((item for item in rows if item.get("airline_id") == airline_id and self._airline(item.get("rbd_code")) == self._airline(data.get("rbd_code"))), None)
        return match.get("id") if match else None

    async def _airline_profile(self, airline_code: Any) -> dict[str, Any] | None:
        code = self._airline(airline_code)
        profiles = await self.db.collection("airline_profiles").find_many()
        return next((item for item in profiles if self._airline(item.get("airline_code") or item.get("iata_code")) == code), None)

    def _visibility_scope(self, entity_type: str, records: list[dict[str, Any]], agency_id: str | None, agency_safe: bool) -> list[dict[str, Any]]:
        if not agency_safe:
            return [item for item in records if not agency_id or item.get("agency_id") in {None, agency_id}]
        return [item for item in records if agency_id and self._agency_visible(entity_type, item, agency_id)]

    def _agency_visible(self, entity_type: str, item: dict[str, Any], agency_id: str) -> bool:
        if item.get("agency_id") not in {None, agency_id}:
            return False
        if entity_type == "evidence-links":
            return item.get("agency_visible") is True and self._code(item.get("evidence_status")) in {"approved", "published", "verified"} and self._code(item.get("accessibility")) in {"agency_visible", "published_reference", "public"}
        return self._published_visible(item, agency_id)

    def _published_visible(self, item: dict[str, Any], agency_id: str) -> bool:
        if self._code(item.get("publication_status")) != "published":
            return False
        visibility = self._code(item.get("agency_visibility_status"))
        return visibility == "all_agencies" or (visibility == "selected_agencies" and agency_id in set(item.get("visible_agency_ids") or []))

    def _agency_projection(self, entity_type: str, item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not item:
            return None
        projected = {key: value for key, value in item.items() if key not in INTERNAL_FIELDS}
        projected.update({"read_only": True, "metadata_only": True, "live_price_or_availability_asserted": False})
        return projected

    async def _require(self, entity_type: str, record_id: str) -> dict[str, Any]:
        _, config = self._config(entity_type)
        record = await self.db.collection(config["collection"]).find_one({"id": record_id})
        if not record:
            record = await self.db.collection(config["collection"]).find_one({config["reference"]: record_id})
        if not record:
            raise AirlineFareFamilyBrandIntelligenceError(f"{entity_type.replace('-', ' ').title()} metadata was not found.")
        return record

    def _config(self, entity_type: Any) -> tuple[str, dict[str, Any]]:
        normalized = self._code(entity_type).replace("_", "-")
        aliases = {"family": "fare-families", "families": "fare-families", "fare-family": "fare-families", "attribute": "attributes", "rbd": "rbd-mappings", "booking-class": "rbd-mappings", "baggage": "baggage-rules", "exception": "baggage-exceptions", "bundle": "commercial-bundles", "evidence": "evidence-links", "comparison": "comparison-profiles"}
        normalized = aliases.get(normalized, normalized)
        if normalized not in ENTITY_CONFIG:
            raise AirlineFareFamilyBrandIntelligenceError(f"Unsupported fare-brand intelligence entity type: {entity_type}.")
        return normalized, ENTITY_CONFIG[normalized]

    def _matches_filters(self, item: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, expected in filters.items():
            if expected is None or expected == "":
                continue
            if key == "agency_id":
                if item.get(key) not in {None, expected}:
                    return False
            elif key in {"airline_code", "rbd_code", "brand_code", "family_code"}:
                if self._airline(item.get(key)) != self._airline(expected):
                    return False
            elif key in {"cabin", "attribute_code", "attribute_status", "mapping_status", "allowance_status", "exception_type", "publication_status", "freshness_status"}:
                if self._code(item.get(key)) != self._code(expected):
                    return False
            elif isinstance(item.get(key), list):
                if self._code(expected) not in {self._code(value) for value in item.get(key) or []}:
                    return False
            elif item.get(key) != expected:
                return False
        return True

    def _date_matches(self, item: dict[str, Any], travel_date: Any) -> bool:
        target = self._date_value(travel_date)
        if not target:
            return True
        start = self._date_value(item.get("effective_from"))
        end = self._date_value(item.get("effective_until"))
        return not (start and target < start or end and target > end)

    def _trace(self, item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not item:
            return None
        reference = next((item.get(config["reference"]) for config in ENTITY_CONFIG.values() if item.get(config["reference"])), None)
        return {"id": item.get("id"), "reference": reference, "status": item.get("allowance_status") or item.get("exception_status") or item.get("mapping_status") or item.get("attribute_status") or item.get("publication_status"), "confidence": item.get("confidence"), "freshness_status": item.get("freshness_status"), "evidence_reference_count": len(item.get("evidence_link_ids") or [])}

    async def _audit(self, event_type: str, item: dict[str, Any], user: dict[str, Any]) -> None:
        await self.db.collection("audit_events").insert_one(AuditEvent(agency_id=item.get("agency_id"), actor_user_id=user.get("id"), event_type=event_type, entity_type="airline_fare_brand_intelligence", entity_id=item["id"], summary=event_type.replace(".", " ").replace("_", " ").title(), metadata={"airline_code": item.get("airline_code"), "brand_code": item.get("brand_code") or item.get("family_code"), "metadata_only": True}).model_dump(mode="json"))

    def _route(self, context: dict[str, Any]) -> str:
        return f"{str(context.get('origin') or '').upper()}-{str(context.get('destination') or '').upper()}".strip("-")

    def _ordered_union(self, left: Any, right: Any) -> list[Any]:
        result = []
        for value in [*(left or []), *(right or [])]:
            if value not in result:
                result.append(value)
        return result

    def _choice(self, value: Any, choices: list[str], label: str) -> str:
        normalized = self._code(value)
        if normalized not in set(choices):
            raise AirlineFareFamilyBrandIntelligenceError(f"Unsupported {label}: {value or 'unset'}.")
        return normalized

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

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def _airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _sort_text(self, value: Any) -> str:
        return value.isoformat() if isinstance(value, (date, datetime)) else str(value or "")
