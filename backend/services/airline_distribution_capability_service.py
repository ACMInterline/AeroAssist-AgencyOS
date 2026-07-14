from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineDistributionCapability,
    AirlineDistributionChannel,
    AirlineDistributionEvidenceLink,
    AirlineDistributionRestriction,
    AirlineFulfillmentCapability,
    AirlineGdsParticipation,
    AirlineNdcCapability,
    AirlinePssProfile,
    AirlineServicingCapability,
    AuditEvent,
)


PHASE_LABEL = "phase_55_8_airline_contact_communication_intelligence_foundation"

AIRLINE_DISTRIBUTION_CHANNELS_COLLECTION = "airline_distribution_channels"
AIRLINE_DISTRIBUTION_CAPABILITIES_COLLECTION = "airline_distribution_capabilities"
AIRLINE_PSS_PROFILES_COLLECTION = "airline_pss_profiles"
AIRLINE_GDS_PARTICIPATIONS_COLLECTION = "airline_gds_participations"
AIRLINE_NDC_CAPABILITIES_COLLECTION = "airline_ndc_capabilities"
AIRLINE_FULFILLMENT_CAPABILITIES_COLLECTION = "airline_fulfillment_capabilities"
AIRLINE_SERVICING_CAPABILITIES_COLLECTION = "airline_servicing_capabilities"
AIRLINE_DISTRIBUTION_RESTRICTIONS_COLLECTION = "airline_distribution_restrictions"
AIRLINE_DISTRIBUTION_EVIDENCE_LINKS_COLLECTION = "airline_distribution_evidence_links"

DISTRIBUTION_COLLECTIONS = [
    AIRLINE_DISTRIBUTION_CHANNELS_COLLECTION,
    AIRLINE_DISTRIBUTION_CAPABILITIES_COLLECTION,
    AIRLINE_PSS_PROFILES_COLLECTION,
    AIRLINE_GDS_PARTICIPATIONS_COLLECTION,
    AIRLINE_NDC_CAPABILITIES_COLLECTION,
    AIRLINE_FULFILLMENT_CAPABILITIES_COLLECTION,
    AIRLINE_SERVICING_CAPABILITIES_COLLECTION,
    AIRLINE_DISTRIBUTION_RESTRICTIONS_COLLECTION,
    AIRLINE_DISTRIBUTION_EVIDENCE_LINKS_COLLECTION,
]

DISTRIBUTION_CHANNEL_CODES = [
    "direct_website",
    "call_center",
    "airport_desk",
    "amadeus",
    "sabre",
    "travelport",
    "ndc_aggregator",
    "airline_direct_ndc",
    "consolidator",
    "tour_operator",
    "manual_offline_process",
]

CAPABILITY_STATUSES = [
    "supported",
    "unsupported",
    "conditional",
    "manual_only",
    "unknown",
    "provider_specific",
    "route_specific",
    "market_specific",
]

PROVIDER_READINESS_STAGES = [
    "documented_capability",
    "configured_provider",
    "tested_sandbox",
    "production_enabled_provider",
]

CAPABILITY_CATALOG = {
    "shopping": ["schedule", "availability", "fares", "branded_fares", "ancillaries", "seat_maps", "special_service_visibility"],
    "booking": ["pnr_creation", "multi_passenger", "ssr", "osi", "apis_documents", "special_seats", "pets", "medical_requests", "groups", "interline_codeshare"],
    "fulfillment": ["ticket_issuance", "emd_a", "emd_s", "rfic_rfisc_availability", "exchanges", "refunds", "voids", "revalidation", "residual_value"],
    "servicing": ["voluntary_changes", "involuntary_changes", "schedule_changes", "split_pnr", "name_correction", "ancillary_modification", "disruption_handling"],
}

PUBLICATION_STATUSES = ["draft", "under_review", "approved", "published", "archived"]
FRESHNESS_STATUSES = ["current", "review_due", "stale", "expired", "unknown"]
AGENCY_VISIBILITY_STATUSES = ["platform_only", "all_agencies", "selected_agencies"]

SENSITIVE_KEY_PARTS = {
    "password",
    "passwd",
    "secret",
    "credential",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "private_key",
    "client_secret",
}


ENTITY_CONFIG: dict[str, dict[str, Any]] = {
    "channels": {
        "collection": AIRLINE_DISTRIBUTION_CHANNELS_COLLECTION,
        "model": AirlineDistributionChannel,
        "reference_field": "channel_reference",
        "prefix": "ADC",
    },
    "capabilities": {
        "collection": AIRLINE_DISTRIBUTION_CAPABILITIES_COLLECTION,
        "model": AirlineDistributionCapability,
        "reference_field": "capability_reference",
        "prefix": "ADP",
    },
    "pss-profiles": {
        "collection": AIRLINE_PSS_PROFILES_COLLECTION,
        "model": AirlinePssProfile,
        "reference_field": "pss_profile_reference",
        "prefix": "APS",
    },
    "gds-participations": {
        "collection": AIRLINE_GDS_PARTICIPATIONS_COLLECTION,
        "model": AirlineGdsParticipation,
        "reference_field": "gds_participation_reference",
        "prefix": "AGD",
    },
    "ndc-capabilities": {
        "collection": AIRLINE_NDC_CAPABILITIES_COLLECTION,
        "model": AirlineNdcCapability,
        "reference_field": "ndc_capability_reference",
        "prefix": "AND",
    },
    "fulfillment-capabilities": {
        "collection": AIRLINE_FULFILLMENT_CAPABILITIES_COLLECTION,
        "model": AirlineFulfillmentCapability,
        "reference_field": "fulfillment_capability_reference",
        "prefix": "AFC",
    },
    "servicing-capabilities": {
        "collection": AIRLINE_SERVICING_CAPABILITIES_COLLECTION,
        "model": AirlineServicingCapability,
        "reference_field": "servicing_capability_reference",
        "prefix": "ASC",
    },
    "restrictions": {
        "collection": AIRLINE_DISTRIBUTION_RESTRICTIONS_COLLECTION,
        "model": AirlineDistributionRestriction,
        "reference_field": "restriction_reference",
        "prefix": "ADR",
    },
    "evidence-links": {
        "collection": AIRLINE_DISTRIBUTION_EVIDENCE_LINKS_COLLECTION,
        "model": AirlineDistributionEvidenceLink,
        "reference_field": "distribution_evidence_reference",
        "prefix": "ADE",
    },
}


class AirlineDistributionCapabilityError(ValueError):
    pass


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    return {key: value for key, value in dict(payload or {}).items() if value is not None}


class AirlineDistributionCapabilityService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "planning_intelligence_only": True,
            "canonical_legacy_distribution_context_reused": True,
            "documented_configured_sandbox_production_distinction_enabled": True,
            "planning_record_does_not_imply_live_capability": True,
            "credential_storage_disabled": True,
            "live_provider_connectivity_disabled": True,
            "provider_execution_disabled": True,
            "shopping_execution_disabled": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "emd_issuance_disabled": True,
            "servicing_execution_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "agency_published_read_only": True,
            "unpublished_draft_agency_visibility_disabled": True,
            "booking_handoff_planning_integration_enabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "entity_types": list(ENTITY_CONFIG),
            "distribution_channels": DISTRIBUTION_CHANNEL_CODES,
            "capability_statuses": CAPABILITY_STATUSES,
            "provider_readiness_stages": PROVIDER_READINESS_STAGES,
            "capability_catalog": CAPABILITY_CATALOG,
            "publication_statuses": PUBLICATION_STATUSES,
            "freshness_statuses": FRESHNESS_STATUSES,
            "agency_visibility_statuses": AGENCY_VISIBILITY_STATUSES,
        }

    async def create_record(self, entity_type: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        data = payload_dict(payload)
        self._reject_credentials(data)
        data.setdefault(config["reference_field"], self._reference(config["prefix"]))
        data = await self._normalize_and_validate(entity_type, data)
        record = config["model"](**data).model_dump(mode="json")
        created = await self.db.collection(config["collection"]).insert_one(record)
        await self._audit(f"airline_distribution_capability.{entity_type}.created", created["id"], user, self._audit_metadata(created))
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": created, **self.safety_flags()}

    async def update_record(self, entity_type: str, record_id: str, payload: Any, user: dict[str, Any]) -> dict[str, Any]:
        entity_type, config = self._config(entity_type)
        existing = await self._require(entity_type, record_id)
        updates = payload_dict(payload)
        self._reject_credentials(updates)
        merged = {**existing, **updates}
        merged = await self._normalize_and_validate(entity_type, merged)
        validated = config["model"](**merged).model_dump(mode="json")
        immutable = {"id", "created_at", "agency_id", config["reference_field"]}
        safe_updates = {key: value for key, value in validated.items() if key not in immutable}
        updated = await self.db.collection(config["collection"]).update_one({"id": existing["id"]}, safe_updates)
        await self._audit(f"airline_distribution_capability.{entity_type}.updated", existing["id"], user, self._audit_metadata(updated or existing))
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": updated or existing, **self.safety_flags()}

    async def get_record(self, entity_type: str, record_id: str) -> dict[str, Any]:
        entity_type, _ = self._config(entity_type)
        return {"phase": PHASE_LABEL, "entity_type": entity_type, "item": await self._require(entity_type, record_id), **self.safety_flags()}

    async def list_records(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        entity_type, config = self._config(entity_type)
        records = await self.db.collection(config["collection"]).find_many()
        records = [record for record in records if self._matches_filters(record, filters)]
        records.sort(key=lambda item: (self._airline(item.get("airline_code")), self._sort_text(item.get("created_at"))), reverse=False)
        return records

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        records = {entity_type: await self.list_records(entity_type, **filters) for entity_type in ENTITY_CONFIG}
        channels = records["channels"]
        return {
            "phase": PHASE_LABEL,
            "summary": self._summary(records),
            "matrix": self._build_matrix(records),
            "channels": channels,
            "capabilities": records["capabilities"],
            "pss_profiles": records["pss-profiles"],
            "gds_participations": records["gds-participations"],
            "ndc_capabilities": records["ndc-capabilities"],
            "fulfillment_capabilities": records["fulfillment-capabilities"],
            "servicing_capabilities": records["servicing-capabilities"],
            "restrictions": records["restrictions"],
            "evidence_links": records["evidence-links"],
            "legacy_context": await self._legacy_context(filters.get("airline_code")),
            "filters": self.filter_metadata(),
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        scoped_filters = {**filters, "agency_id": agency_id}
        records: dict[str, list[dict[str, Any]]] = {}
        for entity_type in ENTITY_CONFIG:
            source = await self.list_records(entity_type, **{key: value for key, value in filters.items() if value is not None})
            records[entity_type] = [
                self._agency_projection(entity_type, record)
                for record in source
                if self._agency_visible(entity_type, record, agency_id)
            ]
        matrix = self._build_matrix(records)
        channels = records["channels"]
        warnings = self._agency_warnings(records)
        fallback = self._fallback_methods(channels)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self._summary(records),
            "operational_channels": [self._channel_availability(item) for item in channels],
            "matrix": matrix,
            "capabilities": records["capabilities"],
            "pss_profiles": records["pss-profiles"],
            "gds_participations": records["gds-participations"],
            "ndc_capabilities": records["ndc-capabilities"],
            "fulfillment_capabilities": records["fulfillment-capabilities"],
            "servicing_capabilities": records["servicing-capabilities"],
            "restrictions": records["restrictions"],
            "evidence": records["evidence-links"],
            "warnings": warnings,
            "fallback_methods": fallback,
            "booking_handoff": await self.booking_handoff_summary(
                agency_id,
                airline_codes=[filters["airline_code"]] if filters.get("airline_code") else None,
                channel_code=filters.get("channel_code"),
            ),
            "filters": self.filter_metadata(),
            "read_only": True,
            "agency_scope_enforced": bool(scoped_filters["agency_id"]),
            **self.safety_flags(),
        }

    async def booking_handoff_summary(
        self,
        agency_id: str,
        airline_codes: list[str] | None = None,
        channel_code: str | None = None,
    ) -> dict[str, Any]:
        requested_airlines = {self._airline(value) for value in airline_codes or [] if value}
        channels = await self.list_records("channels")
        visible_channels = [
            item
            for item in channels
            if self._agency_visible("channels", item, agency_id)
            and (not requested_airlines or self._airline(item.get("airline_code")) in requested_airlines)
            and (not channel_code or self._code(item.get("channel_code")) == self._code(channel_code))
        ]
        capabilities = await self.list_records("capabilities")
        visible_capabilities = [
            item
            for item in capabilities
            if self._agency_visible("capabilities", item, agency_id)
            and item.get("channel_id") in {channel.get("id") for channel in visible_channels}
        ]
        projected_channels = [self._channel_availability(self._agency_projection("channels", item)) for item in visible_channels]
        available = [item for item in projected_channels if item["planning_availability_status"] == "available_for_human_planning"]
        return {
            "airline_codes": sorted(requested_airlines),
            "requested_channel": self._code(channel_code) if channel_code else None,
            "channel_count": len(projected_channels),
            "available_channel_count": len(available),
            "channels": projected_channels,
            "capability_status_counts": self._counts(visible_capabilities, "capability_status"),
            "fallback_methods": self._fallback_methods(projected_channels),
            "manual_review_required": not bool(available) or any(item.get("manual_handling_required") for item in projected_channels),
            "live_connectivity_confirmed": False,
            "planning_record_only": True,
            "metadata_only": True,
        }

    async def coverage(self) -> dict[str, Any]:
        counts = {collection: await self.db.collection(collection).count() for collection in DISTRIBUTION_COLLECTIONS}
        channels = await self.db.collection(AIRLINE_DISTRIBUTION_CHANNELS_COLLECTION).find_many()
        capabilities = await self.db.collection(AIRLINE_DISTRIBUTION_CAPABILITIES_COLLECTION).find_many()
        return {
            "distribution_collection_counts": counts,
            "distribution_channel_count": len(channels),
            "distribution_capability_count": len(capabilities),
            "documented_capability_count": len([item for item in channels + capabilities if item.get("provider_stage") == "documented_capability"]),
            "configured_provider_count": len([item for item in channels + capabilities if item.get("provider_stage") == "configured_provider"]),
            "tested_sandbox_count": len([item for item in channels + capabilities if item.get("provider_stage") == "tested_sandbox"]),
            "production_enabled_provider_count": len([item for item in channels + capabilities if item.get("provider_stage") == "production_enabled_provider"]),
            "unknown_capability_count": len([item for item in channels + capabilities if item.get("capability_status") == "unknown"]),
            "credential_record_count": len([item for item in channels + capabilities if item.get("credentials_stored") is True]),
        }

    async def _normalize_and_validate(self, entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("airline_code"):
            data["airline_code"] = self._airline(data["airline_code"])
        if not data.get("airline_code"):
            raise AirlineDistributionCapabilityError("Airline code is required for distribution capability metadata.")
        data["metadata_only"] = True
        if "provider_stage" in data:
            data["provider_stage"] = self._choice(data.get("provider_stage"), PROVIDER_READINESS_STAGES, "provider stage")
        for key in ["capability_status", "participation_status", "shopping_status", "booking_status", "ticketing_status", "fulfillment_status", "servicing_status", "emd_capability_status"]:
            if key in data:
                data[key] = self._choice(data.get(key), CAPABILITY_STATUSES, key.replace("_", " "))
        if "publication_status" in data:
            data["publication_status"] = self._choice(data.get("publication_status"), PUBLICATION_STATUSES, "publication status")
        if "freshness_status" in data:
            data["freshness_status"] = self._choice(data.get("freshness_status"), FRESHNESS_STATUSES, "freshness status")
        if "agency_visibility_status" in data:
            data["agency_visibility_status"] = self._choice(data.get("agency_visibility_status"), AGENCY_VISIBILITY_STATUSES, "agency visibility status")

        if entity_type == "channels":
            data["channel_code"] = self._choice(data.get("channel_code"), DISTRIBUTION_CHANNEL_CODES, "distribution channel")
            data.setdefault("channel_name", data["channel_code"].replace("_", " ").title())
            data.setdefault("channel_type", self._channel_type(data["channel_code"]))
            data["manual_handling_required"] = bool(data.get("manual_handling_required") or data.get("capability_status") == "manual_only" or data["channel_code"] == "manual_offline_process")
            data["credentials_stored"] = False
            data["live_connectivity_confirmed"] = False
            if not data.get("distribution_channel_profile_id"):
                data["distribution_channel_profile_id"] = await self._legacy_distribution_profile_id(data)
        elif entity_type == "capabilities":
            area = self._choice(data.get("capability_area"), list(CAPABILITY_CATALOG), "capability area")
            code = self._choice(data.get("capability_code"), CAPABILITY_CATALOG[area], f"{area} capability")
            data["capability_area"] = area
            data["capability_code"] = code
            data.setdefault("capability_name", code.replace("_", " ").title())
            await self._validate_channel_link(data)
            data["live_execution_disabled"] = True
        elif entity_type == "pss-profiles":
            if not data.get("legacy_pss_parameters_id"):
                data["legacy_pss_parameters_id"] = await self._legacy_parameter_id("airline_pss_parameters", data)
        elif entity_type == "gds-participations":
            data["gds_code"] = self._choice(data.get("gds_code"), ["amadeus", "sabre", "travelport", "other"], "GDS")
            data["credentials_stored"] = False
            if not data.get("legacy_gds_parameters_id"):
                data["legacy_gds_parameters_id"] = await self._legacy_parameter_id("airline_gds_parameters", data, gds_code=data["gds_code"])
            await self._validate_optional_channel_link(data)
        elif entity_type == "ndc-capabilities":
            data["ndc_type"] = self._choice(data.get("ndc_type"), ["ndc_aggregator", "airline_direct_ndc"], "NDC type")
            data["credentials_stored"] = False
            data["live_connectivity_confirmed"] = False
            await self._validate_optional_channel_link(data)
        elif entity_type == "fulfillment-capabilities":
            data["capability_code"] = self._choice(data.get("capability_code"), CAPABILITY_CATALOG["fulfillment"], "fulfillment capability")
            data["fulfillment_execution_disabled"] = True
            await self._validate_optional_channel_link(data)
        elif entity_type == "servicing-capabilities":
            data["capability_code"] = self._choice(data.get("capability_code"), CAPABILITY_CATALOG["servicing"], "servicing capability")
            data["servicing_execution_disabled"] = True
            await self._validate_optional_channel_link(data)
        elif entity_type == "restrictions":
            data["automatic_enforcement_disabled"] = True
            await self._validate_optional_channel_link(data)
        elif entity_type == "evidence-links":
            await self._validate_evidence_link(data)
        return data

    async def _validate_channel_link(self, data: dict[str, Any]) -> None:
        if not data.get("channel_id"):
            raise AirlineDistributionCapabilityError("Channel id is required for channel capability metadata.")
        channel = await self.db.collection(AIRLINE_DISTRIBUTION_CHANNELS_COLLECTION).find_one({"id": data["channel_id"]})
        if not channel:
            raise AirlineDistributionCapabilityError("Distribution channel metadata was not found.")
        if self._airline(channel.get("airline_code")) != self._airline(data.get("airline_code")):
            raise AirlineDistributionCapabilityError("Capability airline must match its distribution channel airline.")
        if data.get("agency_id") != channel.get("agency_id"):
            raise AirlineDistributionCapabilityError("Capability and distribution channel must use the same governance scope.")
        data["channel_code"] = channel["channel_code"]

    async def _validate_optional_channel_link(self, data: dict[str, Any]) -> None:
        if data.get("channel_id"):
            channel = await self.db.collection(AIRLINE_DISTRIBUTION_CHANNELS_COLLECTION).find_one({"id": data["channel_id"]})
            if not channel or self._airline(channel.get("airline_code")) != self._airline(data.get("airline_code")):
                raise AirlineDistributionCapabilityError("Linked distribution channel does not match this airline.")
            if data.get("agency_id") != channel.get("agency_id"):
                raise AirlineDistributionCapabilityError("Linked channel and record must use the same governance scope.")
            data.setdefault("channel_code", channel.get("channel_code"))

    async def _validate_evidence_link(self, data: dict[str, Any]) -> None:
        target_type = self._code(data.get("target_type"))
        target_config = ENTITY_CONFIG.get(target_type)
        if not target_config or target_type == "evidence-links":
            raise AirlineDistributionCapabilityError("Evidence target type must be a distribution intelligence record type.")
        target = await self.db.collection(target_config["collection"]).find_one({"id": data.get("target_id")})
        if not target:
            raise AirlineDistributionCapabilityError("Distribution evidence target metadata was not found.")
        if self._airline(target.get("airline_code")) != self._airline(data.get("airline_code")):
            raise AirlineDistributionCapabilityError("Evidence link airline must match its target airline.")
        if not any(data.get(key) for key in ["evidence_source_id", "evidence_artifact_id", "evidence_assertion_id", "evidence_link_id"]):
            raise AirlineDistributionCapabilityError("At least one governed evidence reference is required.")

    async def _require(self, entity_type: str, record_id: str) -> dict[str, Any]:
        _, config = self._config(entity_type)
        record = await self.db.collection(config["collection"]).find_one({"id": record_id})
        if not record:
            record = await self.db.collection(config["collection"]).find_one({config["reference_field"]: record_id})
        if not record:
            raise AirlineDistributionCapabilityError(f"{entity_type.replace('-', ' ').title()} metadata was not found.")
        return record

    def _config(self, entity_type: str) -> tuple[str, dict[str, Any]]:
        normalized = self._code(entity_type).replace("_", "-")
        aliases = {
            "channel": "channels",
            "capability": "capabilities",
            "pss": "pss-profiles",
            "gds": "gds-participations",
            "ndc": "ndc-capabilities",
            "fulfillment": "fulfillment-capabilities",
            "servicing": "servicing-capabilities",
            "restriction": "restrictions",
            "evidence": "evidence-links",
        }
        normalized = aliases.get(normalized, normalized)
        if normalized not in ENTITY_CONFIG:
            raise AirlineDistributionCapabilityError(f"Unsupported distribution intelligence entity type: {entity_type}.")
        return normalized, ENTITY_CONFIG[normalized]

    def _matches_filters(self, record: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, expected in filters.items():
            if expected is None or expected == "":
                continue
            if key == "agency_id":
                if record.get("agency_id") not in {None, expected}:
                    return False
                continue
            actual = record.get(key)
            if key in {"airline_code", "operating_carrier", "marketing_carrier"}:
                if self._airline(actual) != self._airline(expected):
                    return False
            elif key in {"capability_area", "capability_code", "channel_code", "provider_stage", "capability_status", "publication_status", "freshness_status", "gds_code", "ndc_type"}:
                if self._code(actual) != self._code(expected):
                    return False
            elif isinstance(actual, list):
                if self._code(expected) not in {self._code(value) for value in actual}:
                    return False
            elif actual != expected:
                return False
        return True

    def _agency_visible(self, entity_type: str, record: dict[str, Any], agency_id: str) -> bool:
        if record.get("agency_id") not in {None, agency_id}:
            return False
        if entity_type == "evidence-links":
            return (
                record.get("agency_visible") is True
                and self._code(record.get("evidence_status")) in {"approved", "published", "verified"}
                and self._code(record.get("accessibility")) in {"agency_visible", "published_reference", "public"}
            )
        if self._code(record.get("publication_status")) != "published":
            return False
        visibility = self._code(record.get("agency_visibility_status"))
        return visibility == "all_agencies" or (visibility == "selected_agencies" and agency_id in set(record.get("visible_agency_ids") or []))

    def _agency_projection(self, entity_type: str, record: dict[str, Any]) -> dict[str, Any]:
        common = {
            "id", "agency_id", "canonical_airline_id", "airline_code", "airline_name", "channel_id", "channel_code",
            "capability_status", "provider_stage", "route_scope", "market_scope", "country_scope", "cabin_scope",
            "effective_from", "effective_until", "freshness_status", "publication_status", "agency_visibility_status",
            "fallback_method", "manual_handling_required", "provider_name", "provider_code", "created_at", "updated_at",
        }
        type_fields = {
            "channels": {"channel_reference", "channel_name", "channel_type", "provider_specific_notes"},
            "capabilities": {"capability_reference", "capability_area", "capability_code", "capability_name", "service_family_scope", "service_code_scope", "conditions", "provider_specific_notes"},
            "pss-profiles": {"pss_profile_reference", "known_pss", "reservation_host", "departure_control_context", "ticketing_host", "emd_host", "emd_capability_status", "confidence", "uncertainty_notes"},
            "gds-participations": {"gds_participation_reference", "gds_code", "participation_status", "shopping_status", "booking_status", "ticketing_status", "servicing_status", "provider_specific_notes"},
            "ndc-capabilities": {"ndc_capability_reference", "ndc_type", "ndc_standard_version", "shopping_status", "booking_status", "fulfillment_status", "servicing_status", "offer_order_context", "provider_specific_notes"},
            "fulfillment-capabilities": {"fulfillment_capability_reference", "capability_code", "rfic_scope", "rfisc_scope", "conditions", "provider_specific_notes"},
            "servicing-capabilities": {"servicing_capability_reference", "capability_code", "conditions", "provider_specific_notes"},
            "restrictions": {"restriction_reference", "restriction_type", "restriction_status", "title", "description", "service_scope", "manual_review_required"},
            "evidence-links": {"distribution_evidence_reference", "target_type", "target_id", "evidence_status", "authority_level", "confidence", "freshness_status", "accessibility"},
        }
        allowed = common | type_fields.get(entity_type, set())
        projected = {key: value for key, value in record.items() if key in allowed}
        projected.update({"metadata_only": True, "live_connectivity_confirmed": False, "planning_record_only": True})
        return projected

    def _build_matrix(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        capabilities = records.get("capabilities", [])
        fulfillment = records.get("fulfillment-capabilities", [])
        servicing = records.get("servicing-capabilities", [])
        gds = records.get("gds-participations", [])
        ndc = records.get("ndc-capabilities", [])
        restrictions = records.get("restrictions", [])
        matrix: list[dict[str, Any]] = []
        for channel in records.get("channels", []):
            channel_id = channel.get("id")
            channel_capabilities = [item for item in capabilities if item.get("channel_id") == channel_id]
            area_statuses = {
                area: self._aggregate_status([item.get("capability_status") for item in channel_capabilities if item.get("capability_area") == area])
                for area in CAPABILITY_CATALOG
            }
            area_statuses["fulfillment"] = self._aggregate_status([item.get("capability_status") for item in fulfillment if item.get("channel_id") == channel_id] or [area_statuses["fulfillment"]])
            area_statuses["servicing"] = self._aggregate_status([item.get("capability_status") for item in servicing if item.get("channel_id") == channel_id] or [area_statuses["servicing"]])
            matrix.append({
                "channel_id": channel_id,
                "airline_code": channel.get("airline_code"),
                "channel_code": channel.get("channel_code"),
                "channel_name": channel.get("channel_name"),
                "provider_name": channel.get("provider_name"),
                "capability_status": channel.get("capability_status"),
                "provider_stage": channel.get("provider_stage"),
                "area_statuses": area_statuses,
                "capability_count": len(channel_capabilities),
                "restriction_count": len([item for item in restrictions if item.get("channel_id") == channel_id]),
                "gds_participation_count": len([item for item in gds if item.get("channel_id") == channel_id]),
                "ndc_capability_count": len([item for item in ndc if item.get("channel_id") == channel_id]),
                "manual_handling_required": bool(channel.get("manual_handling_required")),
                "planning_availability_status": self._planning_availability(channel),
                "live_connectivity_confirmed": False,
                "metadata_only": True,
            })
        matrix.sort(key=lambda item: (self._airline(item.get("airline_code")), self._code(item.get("channel_code"))))
        return matrix

    def _summary(self, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        channels = records.get("channels", [])
        all_capabilities = [
            *records.get("capabilities", []),
            *records.get("fulfillment-capabilities", []),
            *records.get("servicing-capabilities", []),
            *records.get("ndc-capabilities", []),
        ]
        return {
            "airline_count": len({item.get("airline_code") for item in channels if item.get("airline_code")}),
            "channel_count": len(channels),
            "capability_count": len(all_capabilities),
            "pss_profile_count": len(records.get("pss-profiles", [])),
            "gds_participation_count": len(records.get("gds-participations", [])),
            "ndc_capability_count": len(records.get("ndc-capabilities", [])),
            "restriction_count": len(records.get("restrictions", [])),
            "evidence_link_count": len(records.get("evidence-links", [])),
            "channel_status_counts": self._counts(channels, "capability_status"),
            "provider_stage_counts": self._counts(channels, "provider_stage"),
            "capability_area_counts": self._counts(records.get("capabilities", []), "capability_area"),
            "unknown_count": len([item for item in channels + all_capabilities if item.get("capability_status") == "unknown"]),
            "manual_handling_count": len([item for item in channels if item.get("manual_handling_required")]),
            "production_enabled_record_count": len([item for item in channels if item.get("provider_stage") == "production_enabled_provider"]),
            "live_connectivity_confirmed_count": 0,
            "metadata_only": True,
        }

    def _agency_warnings(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        for channel in records.get("channels", []):
            status = channel.get("capability_status") or "unknown"
            stage = channel.get("provider_stage") or "documented_capability"
            if status in {"unknown", "unsupported", "conditional", "manual_only", "provider_specific", "route_specific", "market_specific"}:
                warnings.append({"airline_code": channel.get("airline_code"), "channel_code": channel.get("channel_code"), "warning_type": status, "message": f"Channel capability is {status.replace('_', ' ')} and requires human review."})
            if stage != "production_enabled_provider":
                warnings.append({"airline_code": channel.get("airline_code"), "channel_code": channel.get("channel_code"), "warning_type": stage, "message": f"Provider stage is {stage.replace('_', ' ')}; this planning record does not indicate live connectivity."})
            if channel.get("freshness_status") in {"review_due", "stale", "expired", "unknown"}:
                warnings.append({"airline_code": channel.get("airline_code"), "channel_code": channel.get("channel_code"), "warning_type": "freshness", "message": f"Capability freshness is {channel.get('freshness_status') or 'unknown'}."})
        for restriction in records.get("restrictions", []):
            warnings.append({"airline_code": restriction.get("airline_code"), "channel_code": restriction.get("channel_code"), "warning_type": "restriction", "message": restriction.get("description") or restriction.get("title")})
        return warnings

    def _channel_availability(self, channel: dict[str, Any]) -> dict[str, Any]:
        return {
            **channel,
            "planning_availability_status": self._planning_availability(channel),
            "manual_handling_indicator": bool(channel.get("manual_handling_required") or channel.get("capability_status") == "manual_only"),
            "live_connectivity_confirmed": False,
            "planning_record_only": True,
        }

    def _planning_availability(self, channel: dict[str, Any]) -> str:
        status = self._code(channel.get("capability_status"))
        stage = self._code(channel.get("provider_stage"))
        if status in {"unsupported", "unknown"}:
            return "unavailable_or_unknown"
        if status == "manual_only" or channel.get("manual_handling_required"):
            return "manual_handling"
        if stage == "production_enabled_provider":
            return "available_for_human_planning"
        if stage == "tested_sandbox":
            return "sandbox_tested_not_production"
        if stage == "configured_provider":
            return "configured_not_production"
        return "documented_only"

    def _fallback_methods(self, channels: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for item in channels:
            fallback = item.get("fallback_method")
            if not fallback and item.get("channel_code") == "manual_offline_process":
                fallback = "Manual offline process with human confirmation"
            if fallback:
                results.append({"airline_code": item.get("airline_code"), "channel_code": item.get("channel_code"), "fallback_method": fallback})
        return results

    async def _legacy_context(self, airline_code: str | None) -> dict[str, Any]:
        airline_ids: set[str] = set()
        if airline_code:
            profiles = await self.db.collection("airline_profiles").find_many()
            airline_ids = {item["id"] for item in profiles if self._airline(item.get("iata_code") or item.get("airline_code")) == self._airline(airline_code)}
        context: dict[str, Any] = {}
        for key, collection in {
            "distribution_profiles": "airline_distribution_profiles",
            "pss_parameters": "airline_pss_parameters",
            "gds_parameters": "airline_gds_parameters",
        }.items():
            records = await self.db.collection(collection).find_many()
            if airline_ids:
                records = [item for item in records if item.get("airline_id") in airline_ids]
            context[key] = {"count": len(records), "record_ids": [item.get("id") for item in records]}
        context["normalized_records_are_additive"] = True
        return context

    async def _legacy_distribution_profile_id(self, data: dict[str, Any]) -> str | None:
        airline_id = data.get("canonical_airline_id") or await self._airline_profile_id(data.get("airline_code"))
        if not airline_id:
            return None
        record = await self.db.collection("airline_distribution_profiles").find_one({"airline_id": airline_id})
        return record.get("id") if record else None

    async def _legacy_parameter_id(self, collection: str, data: dict[str, Any], gds_code: str | None = None) -> str | None:
        airline_id = data.get("canonical_airline_id") or await self._airline_profile_id(data.get("airline_code"))
        if not airline_id:
            return None
        query = {"airline_id": airline_id}
        if gds_code:
            query["gds_code"] = gds_code
        record = await self.db.collection(collection).find_one(query)
        return record.get("id") if record else None

    async def _airline_profile_id(self, airline_code: str | None) -> str | None:
        code = self._airline(airline_code)
        records = await self.db.collection("airline_profiles").find_many()
        match = next((item for item in records if self._airline(item.get("iata_code") or item.get("airline_code")) == code), None)
        return match.get("id") if match else None

    def _reject_credentials(self, value: Any, path: str = "payload") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = self._code(key)
                if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                    raise AirlineDistributionCapabilityError(f"Credential-like field is prohibited at {path}.{key}.")
                self._reject_credentials(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._reject_credentials(child, f"{path}[{index}]")

    def _aggregate_status(self, statuses: list[Any]) -> str:
        normalized = [self._code(value) for value in statuses if value]
        for status in ["unsupported", "manual_only", "conditional", "provider_specific", "route_specific", "market_specific", "supported", "unknown"]:
            if status in normalized:
                return status
        return "unknown"

    def _choice(self, value: Any, choices: list[str], label: str) -> str:
        normalized = self._code(value)
        if normalized not in set(choices):
            raise AirlineDistributionCapabilityError(f"Unsupported {label}: {value or 'unset'}.")
        return normalized

    def _channel_type(self, channel_code: str) -> str:
        if channel_code in {"amadeus", "sabre", "travelport"}:
            return "gds"
        if channel_code in {"ndc_aggregator", "airline_direct_ndc"}:
            return "ndc"
        if channel_code in {"direct_website", "call_center", "airport_desk"}:
            return "airline_direct"
        if channel_code in {"consolidator", "tour_operator"}:
            return "partner"
        return "manual_offline_process"

    def _audit_metadata(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "airline_code": record.get("airline_code"),
            "channel_code": record.get("channel_code"),
            "capability_status": record.get("capability_status") or record.get("participation_status"),
            "provider_stage": record.get("provider_stage"),
            "metadata_only": True,
            "credentials_stored": False,
        }

    async def _audit(self, event_type: str, entity_id: str, user: dict[str, Any], metadata: dict[str, Any]) -> None:
        await self.db.collection("audit_events").insert_one(
            AuditEvent(
                event_type=event_type,
                entity_type="airline_distribution_capability",
                entity_id=entity_id,
                actor_user_id=user.get("id"),
                summary=event_type.replace(".", " ").replace("_", " ").title(),
                metadata=metadata,
            ).model_dump(mode="json")
        )

    def _counts(self, items: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = str(item.get(field) or "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def _airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _sort_text(self, value: Any) -> str:
        return value.isoformat() if isinstance(value, (date, datetime)) else str(value or "")
