from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    AirlineEmdInterlineRule,
    AirlineEmdIssuanceRule,
    AirlineEmdLifecycleRule,
    AirlineRejectionPattern,
    AirlineRficRfiscMapping,
    AirlineServiceCommunicationRule,
    AirlineServicePaymentRule,
    PolicyCandidateMechanicsLink,
    ServiceMechanicsStatus,
    SsrOsiRequirement,
    SsrOsiTemplate,
    SsrStatusRecognitionRule,
)


PHASE_LABEL = "phase_36_9_service_mechanics_mapping_foundation"

COMMUNICATION_RULE_COLLECTION = "airline_service_communication_rules"
SSR_OSI_TEMPLATE_COLLECTION = "ssr_osi_templates"
SSR_OSI_REQUIREMENT_COLLECTION = "ssr_osi_requirements"
SSR_STATUS_RECOGNITION_COLLECTION = "ssr_status_recognition_rules"
AIRLINE_REJECTION_PATTERN_COLLECTION = "airline_rejection_patterns"
PAYMENT_RULE_COLLECTION = "airline_service_payment_rules"
EMD_ISSUANCE_RULE_COLLECTION = "airline_emd_issuance_rules"
RFIC_RFISC_MAPPING_COLLECTION = "airline_rfic_rfisc_mappings"
EMD_INTERLINE_RULE_COLLECTION = "airline_emd_interline_rules"
EMD_LIFECYCLE_RULE_COLLECTION = "airline_emd_lifecycle_rules"
CANDIDATE_MECHANICS_LINK_COLLECTION = "policy_candidate_mechanics_links"


RESOURCE_SPECS: dict[str, dict[str, Any]] = {
    "communication_rules": {"collection": COMMUNICATION_RULE_COLLECTION, "model": AirlineServiceCommunicationRule, "singular": "communication_rule"},
    "ssr_osi_templates": {"collection": SSR_OSI_TEMPLATE_COLLECTION, "model": SsrOsiTemplate, "singular": "ssr_osi_template"},
    "requirements": {"collection": SSR_OSI_REQUIREMENT_COLLECTION, "model": SsrOsiRequirement, "singular": "requirement"},
    "status_recognition_rules": {"collection": SSR_STATUS_RECOGNITION_COLLECTION, "model": SsrStatusRecognitionRule, "singular": "status_recognition_rule"},
    "rejection_patterns": {"collection": AIRLINE_REJECTION_PATTERN_COLLECTION, "model": AirlineRejectionPattern, "singular": "rejection_pattern"},
    "payment_rules": {"collection": PAYMENT_RULE_COLLECTION, "model": AirlineServicePaymentRule, "singular": "payment_rule"},
    "emd_issuance_rules": {"collection": EMD_ISSUANCE_RULE_COLLECTION, "model": AirlineEmdIssuanceRule, "singular": "emd_issuance_rule"},
    "rfic_rfisc_mappings": {"collection": RFIC_RFISC_MAPPING_COLLECTION, "model": AirlineRficRfiscMapping, "singular": "rfic_rfisc_mapping"},
    "emd_interline_rules": {"collection": EMD_INTERLINE_RULE_COLLECTION, "model": AirlineEmdInterlineRule, "singular": "emd_interline_rule"},
    "emd_lifecycle_rules": {"collection": EMD_LIFECYCLE_RULE_COLLECTION, "model": AirlineEmdLifecycleRule, "singular": "emd_lifecycle_rule"},
    "candidate_mechanics_links": {"collection": CANDIDATE_MECHANICS_LINK_COLLECTION, "model": PolicyCandidateMechanicsLink, "singular": "link"},
}

COMMUNICATION_RESOURCES = [
    "communication_rules",
    "ssr_osi_templates",
    "requirements",
    "status_recognition_rules",
    "rejection_patterns",
]

PAYMENT_RESOURCES = [
    "payment_rules",
    "emd_issuance_rules",
    "rfic_rfisc_mappings",
    "emd_interline_rules",
    "emd_lifecycle_rules",
]


def normalize_taxonomy_code(value: Any) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or None


def normalize_airline_code(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text or None


def normalize_lookup_text(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())).strip()


def enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True)
    return dict(payload or {})


def clean_updates(payload: Any) -> dict[str, Any]:
    return {key: value for key, value in payload_dict(payload).items() if value is not None}


def visible_scoped(item: dict[str, Any], agency_id: str | None) -> bool:
    if item.get("is_global", item.get("agency_id") is None):
        return True
    return bool(agency_id and item.get("agency_id") == agency_id)


def resource_spec(resource: str) -> dict[str, Any]:
    if resource not in RESOURCE_SPECS:
        raise ValueError(f"Unknown mechanics resource: {resource}")
    return RESOURCE_SPECS[resource]


class ServiceMechanicsService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "communication_rule_count": len(await self.list_records("communication_rules", agency_id=agency_id)),
            "ssr_osi_template_count": len(await self.list_records("ssr_osi_templates", agency_id=agency_id)),
            "ssr_osi_requirement_count": len(await self.list_records("requirements", agency_id=agency_id)),
            "status_recognition_rule_count": len(await self.list_records("status_recognition_rules", agency_id=agency_id)),
            "rejection_pattern_count": len(await self.list_records("rejection_patterns", agency_id=agency_id)),
            "payment_rule_count": len(await self.list_records("payment_rules", agency_id=agency_id)),
            "emd_issuance_rule_count": len(await self.list_records("emd_issuance_rules", agency_id=agency_id)),
            "rfic_rfisc_mapping_count": len(await self.list_records("rfic_rfisc_mappings", agency_id=agency_id)),
            "emd_interline_rule_count": len(await self.list_records("emd_interline_rules", agency_id=agency_id)),
            "emd_lifecycle_rule_count": len(await self.list_records("emd_lifecycle_rules", agency_id=agency_id)),
            "candidate_mechanics_link_count": len(await self.list_records("candidate_mechanics_links", agency_id=agency_id)),
            "deterministic_mechanics_lookup_enabled": True,
            "communication_payment_separation_enforced": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "agency_auto_promotion_disabled": True,
            "diagnostic": "Service mechanics map SSR/OSI communication and EMD/RFIC/RFISC payment metadata separately; no provider execution or EMD issuance is performed.",
        }

    async def list_records(
        self,
        resource: str,
        *,
        agency_id: str | None = None,
        airline_code: str | None = None,
        domain_code: str | None = None,
        family_code: str | None = None,
        variant_code: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        spec = resource_spec(resource)
        items = await self.db.collection(spec["collection"]).find_many()
        airline_code = normalize_airline_code(airline_code)
        domain_code = normalize_taxonomy_code(domain_code)
        family_code = normalize_taxonomy_code(family_code)
        variant_code = normalize_taxonomy_code(variant_code)

        items = [item for item in items if visible_scoped(item, agency_id)]
        if airline_code:
            items = [item for item in items if item.get("airline_code") in {None, airline_code}]
        if domain_code:
            items = [item for item in items if item.get("domain_code") in {None, domain_code}]
        if family_code:
            items = [item for item in items if item.get("family_code") in {None, family_code}]
        if variant_code:
            items = [item for item in items if item.get("variant_code") in {None, variant_code}]
        if not include_archived:
            items = [item for item in items if item.get("status") != ServiceMechanicsStatus.ARCHIVED.value]
        return sorted(items, key=lambda item: (item.get("priority", 100), str(item.get("created_at") or "")), reverse=False)

    async def create_record(self, resource: str, payload: Any, user: dict | None = None, agency_id: str | None = None) -> dict[str, Any]:
        spec = resource_spec(resource)
        data = self._normalize_payload(payload_dict(payload), resource)
        if agency_id:
            data["agency_id"] = agency_id
            if "is_global" in spec["model"].model_fields:
                data["is_global"] = False
        record = spec["model"](**data)
        return await self.db.collection(spec["collection"]).insert_one(record.model_dump(mode="json"))

    async def update_record(self, resource: str, record_id: str, payload: Any, agency_id: str | None = None) -> dict[str, Any] | None:
        spec = resource_spec(resource)
        existing = await self.db.collection(spec["collection"]).find_one({"id": record_id})
        if not existing:
            return None
        if agency_id and existing.get("agency_id") not in {agency_id}:
            return None
        updates = self._normalize_payload(clean_updates(payload), resource)
        return await self.db.collection(spec["collection"]).update_one({"id": record_id}, updates)

    async def archive_record(self, resource: str, record_id: str, agency_id: str | None = None) -> dict[str, Any] | None:
        return await self.update_record(resource, record_id, {"status": ServiceMechanicsStatus.ARCHIVED.value}, agency_id=agency_id)

    async def lookup(
        self,
        *,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None = None,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        airline_code = normalize_airline_code(airline_code) or ""
        domain_code = normalize_taxonomy_code(domain_code) or ""
        family_code = normalize_taxonomy_code(family_code) or ""
        variant_code = normalize_taxonomy_code(variant_code)

        communication = {
            "communication_rules": await self._matching_records("communication_rules", airline_code, domain_code, family_code, variant_code, agency_id),
            "ssr_osi_templates": await self._matching_records("ssr_osi_templates", airline_code, domain_code, family_code, variant_code, agency_id),
            "requirements": await self._matching_records("requirements", airline_code, domain_code, family_code, variant_code, agency_id),
            "status_recognition_rules": await self._matching_records("status_recognition_rules", airline_code, domain_code, family_code, variant_code, agency_id),
            "rejection_patterns": await self._matching_records("rejection_patterns", airline_code, domain_code, family_code, variant_code, agency_id),
        }
        payment = {
            "payment_rules": await self._matching_records("payment_rules", airline_code, domain_code, family_code, variant_code, agency_id),
            "emd_issuance_rules": await self._matching_records("emd_issuance_rules", airline_code, domain_code, family_code, variant_code, agency_id),
            "rfic_rfisc_mappings": await self._matching_records("rfic_rfisc_mappings", airline_code, domain_code, family_code, variant_code, agency_id),
            "emd_interline_rules": await self._matching_records("emd_interline_rules", airline_code, domain_code, family_code, variant_code, agency_id),
            "emd_lifecycle_rules": await self._matching_records("emd_lifecycle_rules", airline_code, domain_code, family_code, variant_code, agency_id),
        }
        warnings = []
        if not any(communication.values()):
            warnings.append("No communication mechanics matched this airline and canonical service.")
        if not any(payment.values()):
            warnings.append("No payment or EMD mechanics matched this airline and canonical service.")

        return {
            "input": {
                "airline_code": airline_code,
                "domain_code": domain_code,
                "family_code": family_code,
                "variant_code": variant_code,
            },
            "communication": communication,
            "payment": payment,
            "warnings": warnings,
            "deterministic_mechanics_lookup_enabled": True,
            "communication_payment_separation_enforced": True,
            "provider_execution_disabled": True,
            "emd_issuance_disabled": True,
            "agency_auto_promotion_disabled": True,
        }

    async def _matching_records(
        self,
        resource: str,
        airline_code: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None,
        agency_id: str | None,
    ) -> list[dict[str, Any]]:
        items = await self.list_records(
            resource,
            agency_id=agency_id,
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            include_archived=False,
        )
        return [
            item
            for item in items
            if (not item.get("variant_code") or item.get("variant_code") == variant_code)
            and item.get("status", ServiceMechanicsStatus.ACTIVE.value) == ServiceMechanicsStatus.ACTIVE.value
        ]

    def _normalize_payload(self, data: dict[str, Any], resource: str) -> dict[str, Any]:
        normalized = dict(data)
        if "airline_code" in normalized:
            normalized["airline_code"] = normalize_airline_code(normalized.get("airline_code"))
        for key in ["domain_code", "family_code", "variant_code"]:
            if key in normalized:
                normalized[key] = normalize_taxonomy_code(normalized.get(key))
        for key in ["ssr_code", "rfic", "rfisc", "service_subcode"]:
            if key in normalized and normalized.get(key) is not None:
                normalized[key] = str(normalized[key]).strip().upper() or None
        if resource == "status_recognition_rules" and "match_value" in normalized:
            normalized["normalized_match_value"] = normalize_lookup_text(normalized.get("match_value"))
        if resource == "rejection_patterns" and "pattern_text" in normalized:
            normalized["normalized_pattern_text"] = normalize_lookup_text(normalized.get("pattern_text"))
        for key, value in list(normalized.items()):
            normalized[key] = enum_value(value)
        return normalized
