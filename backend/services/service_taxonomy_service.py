from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    AirlineServiceAlias,
    AirlineServiceAliasType,
    CanonicalServiceDomain,
    CanonicalServiceFamily,
    CanonicalServiceVariant,
    PolicyCandidateTaxonomyCandidateType,
    PolicyCandidateTaxonomyLink,
    ServiceApplicabilityDimension,
    ServicePolicyOutcomeSeverity,
    ServicePolicyOutcomeType,
    ServiceTaxonomyCorrectionScope,
    ServiceTaxonomyGovernanceStatus,
    ServiceTaxonomyMappingRule,
    ServiceTaxonomyMatchType,
    ServiceTaxonomyPromotionStatus,
    ServiceTaxonomyReviewCorrection,
    ServiceTaxonomyReviewStatus,
    ServiceTaxonomyRuleScope,
    ServiceTaxonomyStatus,
)


PHASE_LABEL = "phase_36_8_service_taxonomy_foundation"

DOMAIN_COLLECTION = "canonical_service_domains"
FAMILY_COLLECTION = "canonical_service_families"
VARIANT_COLLECTION = "canonical_service_variants"
ALIAS_COLLECTION = "airline_service_aliases"
DIMENSION_COLLECTION = "service_applicability_dimensions"
OUTCOME_COLLECTION = "service_policy_outcome_types"
RULE_COLLECTION = "service_taxonomy_mapping_rules"
LINK_COLLECTION = "policy_candidate_taxonomy_links"
CORRECTION_COLLECTION = "service_taxonomy_review_corrections"

CANDIDATE_COLLECTIONS = {
    PolicyCandidateTaxonomyCandidateType.EXTRACTED_RULE.value: "airline_policy_extracted_rules",
    PolicyCandidateTaxonomyCandidateType.EXTRACTED_PRICE.value: "airline_policy_extracted_prices",
    PolicyCandidateTaxonomyCandidateType.EXTRACTED_COMMUNICATION.value: "airline_policy_extracted_communication_rules",
    PolicyCandidateTaxonomyCandidateType.EXTRACTED_EMD_RULE.value: "airline_policy_extracted_emd_rules",
    PolicyCandidateTaxonomyCandidateType.EXTRACTED_EXCEPTION.value: "airline_policy_extracted_exceptions",
    PolicyCandidateTaxonomyCandidateType.APPROVED_KNOWLEDGE.value: "airline_policy_approved_knowledge_records",
}


def normalize_taxonomy_code(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def normalize_alias_text(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())).strip()


def normalize_airline_code(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text or None


def enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def payload_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json", exclude_unset=True)
    return dict(payload or {})


def clean_updates(payload: Any) -> dict[str, Any]:
    return {key: value for key, value in payload_dict(payload).items() if value is not None}


def sorted_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: (item.get("sort_order", 100), item.get("name") or item.get("rule_name") or item.get("alias_text") or ""))


def visible_scoped(item: dict[str, Any], agency_id: str | None) -> bool:
    if item.get("is_global", item.get("scope") == "global"):
        return True
    return bool(agency_id and item.get("agency_id") == agency_id)


def _tokens(text: str) -> set[str]:
    return {token for token in normalize_alias_text(text).split(" ") if token}


def _safe_regex_match(pattern: str, text: str) -> bool:
    if len(pattern or "") > 96:
        return False
    if re.search(r"(\.\*.*\.\*)|([+*?{][+*?{])|(\([^)]*[+*][^)]*\)[+*])", pattern or ""):
        return False
    try:
        return re.search(pattern, text, flags=re.IGNORECASE) is not None
    except re.error:
        return False


def _candidate_excerpt(candidate: dict[str, Any] | None, fallback: str | None = None) -> str:
    if not candidate:
        return fallback or ""
    pieces = [
        candidate.get("source_excerpt"),
        candidate.get("service_variant"),
        candidate.get("ssr_code"),
        candidate.get("osi_keyword"),
        candidate.get("associated_ssr_code"),
        candidate.get("rfic"),
        candidate.get("rfisc"),
        candidate.get("service_subcode"),
        candidate.get("exception_type"),
        candidate.get("rule_type"),
        candidate.get("knowledge_type"),
    ]
    if candidate.get("currency") and candidate.get("amount") is not None:
        pieces.append(f"{candidate.get('currency')} {candidate.get('amount')}")
    if candidate.get("normalized_payload_json"):
        pieces.append(str(candidate.get("normalized_payload_json")))
    return " ".join(str(piece) for piece in pieces if piece).strip() or (fallback or "")


BASELINE_DOMAINS = [
    ("passenger_assistance", "Passenger Assistance", "General assistance services for travelers who need airport, airline, or journey support."),
    ("mobility", "Mobility", "Wheelchair, reduced mobility, and sensory assistance services."),
    ("medical", "Medical", "Medical clearance, oxygen, stretcher, allergy, medication, and health-related service needs."),
    ("children", "Children", "Unaccompanied minor, young passenger, and child-specific travel assistance."),
    ("pets_animals", "Pets & Animals", "Pets in cabin, animals in hold, service animals, and animal assistance categories."),
    ("baggage_special_items", "Baggage & Special Items", "Sports equipment, musical instruments, weapons, diplomatic bags, human remains, and oversized items."),
    ("seating", "Seating", "Extra seat, family seating, and seat-restriction service families."),
    ("meals", "Meals", "Special meal service families and variants."),
    ("vip_protocol", "VIP & Protocol", "Meet, assist, lounge, VIP, and corporate protocol service families."),
    ("disruption", "Disruption", "Disruption assistance service families."),
    ("documents", "Documents", "Document and eligibility check service families."),
    ("claims", "Claims", "Refund, claim, and after-sales assistance families."),
    ("distribution_payment", "Distribution & Payment", "Distribution and payment-related policy categories kept separate from execution."),
    ("other", "Other", "Fallback taxonomy domain for unknown or unclassified service wording."),
]

BASELINE_FAMILIES = [
    ("children", "unaccompanied_minor", "Unaccompanied Minor", ["UMNR"], ["UMNR"]),
    ("children", "young_passenger", "Young Passenger", [], []),
    ("mobility", "wheelchair", "Wheelchair", ["WCHR", "WCHS", "WCHC"], ["WCHR", "WCHS", "WCHC"]),
    ("passenger_assistance", "passenger_requiring_assistance", "Passenger Requiring Assistance", ["MAAS"], ["MAAS"]),
    ("mobility", "blind_assistance", "Blind Assistance", ["BLND"], ["BLND"]),
    ("mobility", "deaf_assistance", "Deaf Assistance", ["DEAF"], ["DEAF"]),
    ("medical", "medical_clearance", "Medical Clearance", ["MEDA"], ["MEDA"]),
    ("medical", "medif", "MEDIF", [], ["MEDIF"]),
    ("medical", "oxygen", "Oxygen", ["OXYG"], ["OXYG"]),
    ("medical", "stretcher", "Stretcher", ["STCR"], ["STCR"]),
    ("medical", "respiratory_device", "Respiratory Device", [], []),
    ("medical", "severe_allergy", "Severe Allergy", [], []),
    ("medical", "pregnancy", "Pregnancy", [], []),
    ("medical", "medication_transport", "Medication Transport", [], []),
    ("pets_animals", "pet_in_cabin", "Pet In Cabin", ["PETC"], ["PETC"]),
    ("pets_animals", "animal_in_hold", "Animal In Hold", ["AVIH"], ["AVIH"]),
    ("pets_animals", "service_animal", "Service Animal", ["SVAN"], ["SVAN"]),
    ("pets_animals", "emotional_support_animal", "Emotional Support Animal", [], []),
    ("baggage_special_items", "sports_equipment", "Sports Equipment", [], []),
    ("baggage_special_items", "musical_instrument", "Musical Instrument", [], []),
    ("baggage_special_items", "oversized_baggage", "Oversized Baggage", [], []),
    ("baggage_special_items", "weapon_regulated_item", "Weapon / Regulated Item", [], []),
    ("baggage_special_items", "diplomatic_bag", "Diplomatic Bag", [], []),
    ("baggage_special_items", "human_remains", "Human Remains", [], []),
    ("seating", "extra_seat", "Extra Seat", ["EXST"], ["EXST"]),
    ("meals", "special_meal", "Special Meal", ["SPML"], ["SPML"]),
    ("seating", "family_seating", "Family Seating", [], []),
    ("seating", "seat_restriction", "Seat Restriction", [], []),
    ("passenger_assistance", "meet_and_assist", "Meet and Assist", ["MAAS"], ["MAAS"]),
    ("vip_protocol", "lounge_assistance", "Lounge Assistance", [], []),
    ("vip_protocol", "vip_protocol", "VIP Protocol", [], []),
    ("vip_protocol", "corporate_protocol", "Corporate Protocol", [], []),
    ("disruption", "disruption_assistance", "Disruption Assistance", [], []),
    ("claims", "refund_assistance", "Refund Assistance", [], []),
    ("documents", "document_check", "Document Check", [], []),
]

BASELINE_VARIANTS = [
    ("children", "unaccompanied_minor", "kids_solo", "Kids Solo", None, ["Kids Solo"]),
    ("children", "unaccompanied_minor", "unaccompanied_teenager", "Unaccompanied Teenager", None, ["UMT", "teen assistance"]),
    ("children", "unaccompanied_minor", "optional_um", "Optional UM", "UMNR", ["adolescent", "optional UM"]),
    ("mobility", "wheelchair", "wchr", "WCHR", "WCHR", ["WCHR"]),
    ("mobility", "wheelchair", "wchs", "WCHS", "WCHS", ["WCHS"]),
    ("mobility", "wheelchair", "wchc", "WCHC", "WCHC", ["WCHC"]),
    ("passenger_assistance", "passenger_requiring_assistance", "maas", "MAAS", "MAAS", ["MAAS"]),
    ("medical", "medical_clearance", "meda", "MEDA", "MEDA", ["MEDA"]),
    ("medical", "oxygen", "oxyg", "OXYG", "OXYG", ["OXYG"]),
    ("medical", "stretcher", "stcr", "STCR", "STCR", ["STCR"]),
    ("pets_animals", "pet_in_cabin", "petc", "PETC", "PETC", ["PETC"]),
    ("pets_animals", "animal_in_hold", "avih", "AVIH", "AVIH", ["AVIH"]),
    ("pets_animals", "service_animal", "svan", "SVAN", "SVAN", ["SVAN"]),
    ("seating", "extra_seat", "extra_seat_service", "Extra Seat Service", "EXST", ["extra seat", "EXST"]),
    ("meals", "special_meal", "special_meal_generic", "Special Meal Generic", "SPML", ["SPML", "special meal"]),
]

BASELINE_ALIASES = [
    ("AF", "Kids Solo", "commercial_name", "children", "unaccompanied_minor", "kids_solo", 0.96),
    ("AF", "UMT", "policy_term", "children", "unaccompanied_minor", "unaccompanied_teenager", 0.94),
    ("KL", "adolescent", "policy_term", "children", "unaccompanied_minor", "optional_um", 0.86),
    (None, "PETC", "ssr_code", "pets_animals", "pet_in_cabin", "petc", 0.97),
    (None, "AVIH", "ssr_code", "pets_animals", "animal_in_hold", "avih", 0.97),
    (None, "WCHR", "ssr_code", "mobility", "wheelchair", "wchr", 0.97),
    (None, "WCHS", "ssr_code", "mobility", "wheelchair", "wchs", 0.97),
    (None, "WCHC", "ssr_code", "mobility", "wheelchair", "wchc", 0.97),
    (None, "MAAS", "ssr_code", "passenger_assistance", "passenger_requiring_assistance", "maas", 0.94),
    (None, "MEDA", "ssr_code", "medical", "medical_clearance", "meda", 0.97),
    (None, "OXYG", "ssr_code", "medical", "oxygen", "oxyg", 0.97),
    (None, "STCR", "ssr_code", "medical", "stretcher", "stcr", 0.97),
    (None, "SVAN", "ssr_code", "pets_animals", "service_animal", "svan", 0.95),
]

BASELINE_DIMENSIONS = [
    ("passenger_age", "Passenger Age", "number"),
    ("passenger_type", "Passenger Type", "enum"),
    ("route_type", "Route Type", "enum"),
    ("direct_vs_connecting", "Direct vs Connecting", "enum"),
    ("origin_country", "Origin Country", "country"),
    ("destination_country", "Destination Country", "country"),
    ("airport", "Airport", "airport"),
    ("marketing_carrier", "Marketing Carrier", "carrier"),
    ("operating_carrier", "Operating Carrier", "carrier"),
    ("validating_carrier", "Validating Carrier", "carrier"),
    ("cabin", "Cabin", "enum"),
    ("aircraft", "Aircraft", "text"),
    ("flight_duration", "Flight Duration", "duration"),
    ("booking_deadline", "Booking Deadline", "duration"),
    ("document_required", "Document Required", "boolean"),
    ("manual_contact_required", "Manual Contact Required", "boolean"),
    ("ndc_supported", "NDC Supported", "boolean"),
    ("gds_supported", "GDS Supported", "boolean"),
    ("interline_allowed", "Interline Allowed", "boolean"),
]

BASELINE_OUTCOMES = [
    ("mandatory", "Mandatory", "info"),
    ("optional", "Optional", "info"),
    ("not_permitted", "Not Permitted", "blocker"),
    ("permitted_on_request", "Permitted On Request", "advisory"),
    ("requires_airline_confirmation", "Requires Airline Confirmation", "warning"),
    ("requires_manual_contact", "Requires Manual Contact", "warning"),
    ("requires_document", "Requires Document", "warning"),
    ("requires_medical_clearance", "Requires Medical Clearance", "warning"),
    ("requires_emd", "Requires EMD", "warning"),
    ("included_in_fare", "Included In Fare", "info"),
    ("restricted", "Restricted", "warning"),
    ("embargoed", "Embargoed", "blocker"),
    ("unknown_review_required", "Unknown / Review Required", "advisory"),
]


class ServiceTaxonomyService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "domain_count": await self.db.collection(DOMAIN_COLLECTION).count(),
            "family_count": await self.db.collection(FAMILY_COLLECTION).count(),
            "variant_count": await self.db.collection(VARIANT_COLLECTION).count(),
            "alias_count": len(await self.list_aliases(agency_id=agency_id)),
            "applicability_dimension_count": await self.db.collection(DIMENSION_COLLECTION).count(),
            "outcome_type_count": await self.db.collection(OUTCOME_COLLECTION).count(),
            "mapping_rule_count": len(await self.list_mapping_rules(agency_id=agency_id)),
            "candidate_link_count": len(await self.list_candidate_links(agency_id=agency_id)),
            "review_correction_count": len(await self.list_review_corrections(agency_id=agency_id)),
            "deterministic_taxonomy_mapping_enabled": True,
            "external_ai_taxonomy_mapping_disabled": True,
            "agency_auto_promotion_disabled": True,
            "taxonomy_seeding_enabled": True,
            "diagnostic": "Canonical service taxonomy maps policy wording and service codes only; it does not execute SSR/OSI/EMD/payment/provider workflows.",
        }

    async def seed_baseline(self, user: dict | None = None) -> dict[str, Any]:
        actor_id = (user or {}).get("id")
        created = {
            "domains": 0,
            "families": 0,
            "variants": 0,
            "aliases": 0,
            "applicability_dimensions": 0,
            "outcome_types": 0,
            "mapping_rules": 0,
        }

        for index, (code, name, description) in enumerate(BASELINE_DOMAINS, start=1):
            existing = await self.db.collection(DOMAIN_COLLECTION).find_one({"code": code})
            if not existing:
                record = CanonicalServiceDomain(
                    code=code,
                    name=name,
                    description=description,
                    sort_order=index * 10,
                    governance_status=ServiceTaxonomyGovernanceStatus.SEED,
                    created_by_user_id=actor_id,
                )
                await self.db.collection(DOMAIN_COLLECTION).insert_one(record.model_dump(mode="json"))
                created["domains"] += 1

        domains_by_code = {item["code"]: item for item in await self.db.collection(DOMAIN_COLLECTION).find_many()}
        for index, (domain_code, code, name, ssr_codes, service_keys) in enumerate(BASELINE_FAMILIES, start=1):
            existing = await self.db.collection(FAMILY_COLLECTION).find_one({"domain_code": domain_code, "code": code})
            if not existing:
                record = CanonicalServiceFamily(
                    domain_id=(domains_by_code.get(domain_code) or {}).get("id"),
                    domain_code=domain_code,
                    code=code,
                    name=name,
                    description=f"Canonical family for {name.lower()} policy and service terminology.",
                    default_ssr_codes=ssr_codes,
                    related_service_catalogue_keys=service_keys,
                    sort_order=index * 10,
                    governance_status=ServiceTaxonomyGovernanceStatus.SEED,
                )
                await self.db.collection(FAMILY_COLLECTION).insert_one(record.model_dump(mode="json"))
                created["families"] += 1

        for index, (domain_code, family_code, code, name, standard_ssr_code, known_terms) in enumerate(BASELINE_VARIANTS, start=1):
            existing = await self.db.collection(VARIANT_COLLECTION).find_one({"domain_code": domain_code, "family_code": family_code, "code": code})
            if not existing:
                record = CanonicalServiceVariant(
                    domain_code=domain_code,
                    family_code=family_code,
                    code=code,
                    name=name,
                    description=f"Canonical variant for {name}.",
                    standard_ssr_code=standard_ssr_code,
                    known_airline_terms=known_terms,
                    sort_order=index * 10,
                    governance_status=ServiceTaxonomyGovernanceStatus.SEED,
                )
                await self.db.collection(VARIANT_COLLECTION).insert_one(record.model_dump(mode="json"))
                created["variants"] += 1

        for airline_code, alias_text, alias_type, domain_code, family_code, variant_code, confidence in BASELINE_ALIASES:
            normalized = normalize_alias_text(alias_text)
            existing = await self.db.collection(ALIAS_COLLECTION).find_one({"airline_code": airline_code, "normalized_alias_text": normalized})
            if not existing:
                record = AirlineServiceAlias(
                    airline_code=airline_code,
                    alias_text=alias_text,
                    alias_type=alias_type,
                    normalized_alias_text=normalized,
                    domain_code=domain_code,
                    family_code=family_code,
                    variant_code=variant_code,
                    confidence_score=confidence,
                    review_status=ServiceTaxonomyReviewStatus.CONFIRMED,
                    is_global=True,
                    status=ServiceTaxonomyStatus.ACTIVE,
                )
                await self.db.collection(ALIAS_COLLECTION).insert_one(record.model_dump(mode="json"))
                created["aliases"] += 1
            rule_name = f"Baseline {alias_text} mapping"
            rule_existing = await self.db.collection(RULE_COLLECTION).find_one({"rule_name": rule_name, "normalized_match_value": normalized})
            if not rule_existing:
                record = ServiceTaxonomyMappingRule(
                    rule_name=rule_name,
                    airline_code=airline_code,
                    match_type=ServiceTaxonomyMatchType.SSR_CODE if alias_type in {"ssr_code", "gds_code"} else ServiceTaxonomyMatchType.EXACT,
                    match_value=alias_text,
                    normalized_match_value=normalized,
                    domain_code=domain_code,
                    family_code=family_code,
                    variant_code=variant_code,
                    alias_type=alias_type,
                    confidence_score=confidence - 0.02,
                    priority=20 if alias_type in {"ssr_code", "gds_code"} else 30,
                    scope=ServiceTaxonomyRuleScope.GLOBAL,
                    status=ServiceTaxonomyStatus.ACTIVE,
                    created_by_user_id=actor_id,
                    notes="Phase 36.8 baseline deterministic taxonomy seed.",
                )
                await self.db.collection(RULE_COLLECTION).insert_one(record.model_dump(mode="json"))
                created["mapping_rules"] += 1

        for index, (code, name, value_type) in enumerate(BASELINE_DIMENSIONS, start=1):
            existing = await self.db.collection(DIMENSION_COLLECTION).find_one({"code": code})
            if not existing:
                record = ServiceApplicabilityDimension(
                    code=code,
                    name=name,
                    value_type=value_type,
                    description=f"Applicability dimension for {name.lower()} policy comparison.",
                    sort_order=index * 10,
                )
                await self.db.collection(DIMENSION_COLLECTION).insert_one(record.model_dump(mode="json"))
                created["applicability_dimensions"] += 1

        for index, (code, name, severity) in enumerate(BASELINE_OUTCOMES, start=1):
            existing = await self.db.collection(OUTCOME_COLLECTION).find_one({"code": code})
            if not existing:
                record = ServicePolicyOutcomeType(
                    code=code,
                    name=name,
                    severity=severity,
                    description=f"Policy outcome type for {name.lower()} decisions.",
                    sort_order=index * 10,
                )
                await self.db.collection(OUTCOME_COLLECTION).insert_one(record.model_dump(mode="json"))
                created["outcome_types"] += 1

        return {
            "created": created,
            "summary": await self.summary(),
            "idempotent": True,
            "external_ai_taxonomy_mapping_disabled": True,
            "agency_auto_promotion_disabled": True,
        }

    async def list_domains(self, include_archived: bool = False) -> list[dict[str, Any]]:
        items = await self.db.collection(DOMAIN_COLLECTION).find_many()
        if not include_archived:
            items = [item for item in items if item.get("status") != ServiceTaxonomyStatus.ARCHIVED.value]
        return sorted_items(items)

    async def get_domain(self, domain_id: str) -> dict[str, Any] | None:
        return await self.db.collection(DOMAIN_COLLECTION).find_one({"id": domain_id})

    async def create_domain(self, payload: Any, user: dict) -> dict[str, Any]:
        data = payload_dict(payload)
        data["code"] = normalize_taxonomy_code(data.get("code"))
        if await self.db.collection(DOMAIN_COLLECTION).find_one({"code": data["code"]}):
            raise ValueError("domain_exists")
        record = CanonicalServiceDomain(**data, created_by_user_id=user.get("id"), updated_by_user_id=user.get("id"))
        return await self.db.collection(DOMAIN_COLLECTION).insert_one(record.model_dump(mode="json"))

    async def update_domain(self, domain_id: str, payload: Any, user: dict) -> dict[str, Any] | None:
        updates = clean_updates(payload)
        if "code" in updates:
            updates["code"] = normalize_taxonomy_code(updates["code"])
        updates["updated_by_user_id"] = user.get("id")
        return await self.db.collection(DOMAIN_COLLECTION).update_one({"id": domain_id}, updates)

    async def list_families(self, domain_code: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
        items = await self.db.collection(FAMILY_COLLECTION).find_many()
        if domain_code:
            items = [item for item in items if item.get("domain_code") == normalize_taxonomy_code(domain_code)]
        if not include_archived:
            items = [item for item in items if item.get("status") != ServiceTaxonomyStatus.ARCHIVED.value]
        return sorted_items(items)

    async def get_family(self, family_id: str) -> dict[str, Any] | None:
        return await self.db.collection(FAMILY_COLLECTION).find_one({"id": family_id})

    async def create_family(self, payload: Any) -> dict[str, Any]:
        data = payload_dict(payload)
        data["domain_code"] = normalize_taxonomy_code(data.get("domain_code"))
        data["code"] = normalize_taxonomy_code(data.get("code"))
        if await self.db.collection(FAMILY_COLLECTION).find_one({"domain_code": data["domain_code"], "code": data["code"]}):
            raise ValueError("family_exists")
        record = CanonicalServiceFamily(**data)
        return await self.db.collection(FAMILY_COLLECTION).insert_one(record.model_dump(mode="json"))

    async def update_family(self, family_id: str, payload: Any) -> dict[str, Any] | None:
        updates = clean_updates(payload)
        if "domain_code" in updates:
            updates["domain_code"] = normalize_taxonomy_code(updates["domain_code"])
        if "code" in updates:
            updates["code"] = normalize_taxonomy_code(updates["code"])
        return await self.db.collection(FAMILY_COLLECTION).update_one({"id": family_id}, updates)

    async def list_variants(self, domain_code: str | None = None, family_code: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
        items = await self.db.collection(VARIANT_COLLECTION).find_many()
        if domain_code:
            items = [item for item in items if item.get("domain_code") == normalize_taxonomy_code(domain_code)]
        if family_code:
            items = [item for item in items if item.get("family_code") == normalize_taxonomy_code(family_code)]
        if not include_archived:
            items = [item for item in items if item.get("status") != ServiceTaxonomyStatus.ARCHIVED.value]
        return sorted_items(items)

    async def get_variant(self, variant_id: str) -> dict[str, Any] | None:
        return await self.db.collection(VARIANT_COLLECTION).find_one({"id": variant_id})

    async def create_variant(self, payload: Any) -> dict[str, Any]:
        data = payload_dict(payload)
        data["domain_code"] = normalize_taxonomy_code(data.get("domain_code"))
        data["family_code"] = normalize_taxonomy_code(data.get("family_code"))
        data["code"] = normalize_taxonomy_code(data.get("code"))
        if await self.db.collection(VARIANT_COLLECTION).find_one({"domain_code": data["domain_code"], "family_code": data["family_code"], "code": data["code"]}):
            raise ValueError("variant_exists")
        record = CanonicalServiceVariant(**data)
        return await self.db.collection(VARIANT_COLLECTION).insert_one(record.model_dump(mode="json"))

    async def update_variant(self, variant_id: str, payload: Any) -> dict[str, Any] | None:
        updates = clean_updates(payload)
        for key in ["domain_code", "family_code", "code"]:
            if key in updates:
                updates[key] = normalize_taxonomy_code(updates[key])
        return await self.db.collection(VARIANT_COLLECTION).update_one({"id": variant_id}, updates)

    async def list_aliases(self, airline_code: str | None = None, agency_id: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
        airline_code = normalize_airline_code(airline_code)
        items = await self.db.collection(ALIAS_COLLECTION).find_many()
        items = [item for item in items if visible_scoped(item, agency_id)]
        if airline_code:
            items = [item for item in items if item.get("airline_code") in {None, airline_code}]
        if not include_archived:
            items = [item for item in items if item.get("status") != ServiceTaxonomyStatus.ARCHIVED.value]
        return sorted_items(items)

    async def create_alias(self, payload: Any) -> dict[str, Any]:
        data = payload_dict(payload)
        data["airline_code"] = normalize_airline_code(data.get("airline_code"))
        data["normalized_alias_text"] = normalize_alias_text(data.get("alias_text"))
        record = AirlineServiceAlias(**data)
        return await self.db.collection(ALIAS_COLLECTION).insert_one(record.model_dump(mode="json"))

    async def update_alias(self, alias_id: str, payload: Any) -> dict[str, Any] | None:
        updates = clean_updates(payload)
        if "airline_code" in updates:
            updates["airline_code"] = normalize_airline_code(updates["airline_code"])
        if "alias_text" in updates:
            updates["normalized_alias_text"] = normalize_alias_text(updates["alias_text"])
        return await self.db.collection(ALIAS_COLLECTION).update_one({"id": alias_id}, updates)

    async def list_mapping_rules(self, airline_code: str | None = None, agency_id: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
        airline_code = normalize_airline_code(airline_code)
        items = await self.db.collection(RULE_COLLECTION).find_many()
        items = [
            item
            for item in items
            if item.get("scope") == ServiceTaxonomyRuleScope.GLOBAL.value
            or (agency_id and item.get("scope") == ServiceTaxonomyRuleScope.AGENCY.value and item.get("agency_id") == agency_id)
        ]
        if airline_code:
            items = [item for item in items if item.get("airline_code") in {None, airline_code}]
        if not include_archived:
            items = [item for item in items if item.get("status") != ServiceTaxonomyStatus.ARCHIVED.value]
        return sorted(items, key=lambda item: (item.get("priority", 100), item.get("rule_name") or ""))

    async def create_mapping_rule(self, payload: Any, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        data["airline_code"] = normalize_airline_code(data.get("airline_code"))
        data["normalized_match_value"] = normalize_alias_text(data.get("match_value"))
        if agency_id:
            data["scope"] = ServiceTaxonomyRuleScope.AGENCY.value
            data["agency_id"] = agency_id
        record = ServiceTaxonomyMappingRule(**data, created_by_user_id=user.get("id"))
        return await self.db.collection(RULE_COLLECTION).insert_one(record.model_dump(mode="json"))

    async def update_mapping_rule(self, rule_id: str, payload: Any) -> dict[str, Any] | None:
        updates = clean_updates(payload)
        if "airline_code" in updates:
            updates["airline_code"] = normalize_airline_code(updates["airline_code"])
        if "match_value" in updates:
            updates["normalized_match_value"] = normalize_alias_text(updates["match_value"])
        return await self.db.collection(RULE_COLLECTION).update_one({"id": rule_id}, updates)

    async def list_applicability_dimensions(self) -> list[dict[str, Any]]:
        return sorted_items(await self.db.collection(DIMENSION_COLLECTION).find_many())

    async def list_outcome_types(self) -> list[dict[str, Any]]:
        return sorted_items(await self.db.collection(OUTCOME_COLLECTION).find_many())

    async def map_candidate_text(self, text: str, airline_code: str | None = None, agency_id: str | None = None) -> dict[str, Any]:
        airline_code = normalize_airline_code(airline_code)
        normalized = normalize_alias_text(text)
        tokens = _tokens(text)
        if not normalized:
            return self._unknown_result(text, "No text or service code was supplied.")

        aliases = await self.list_aliases(airline_code=airline_code, agency_id=agency_id)
        aliases.sort(key=lambda item: (0 if item.get("airline_code") == airline_code else 1, -(item.get("confidence_score") or 0)))
        for alias in aliases:
            alias_norm = alias.get("normalized_alias_text") or normalize_alias_text(alias.get("alias_text"))
            alias_type = alias.get("alias_type")
            exact_alias = alias_norm == normalized
            exact_code = alias_type in {AirlineServiceAliasType.SSR_CODE.value, AirlineServiceAliasType.GDS_CODE.value} and alias_norm in tokens
            if exact_alias or exact_code:
                return self._mapped_result(
                    text=text,
                    domain_code=alias["domain_code"],
                    family_code=alias["family_code"],
                    variant_code=alias.get("variant_code"),
                    confidence=min(0.99, float(alias.get("confidence_score") or 0.75) + (0.02 if alias.get("airline_code") == airline_code else 0)),
                    review_status=alias.get("review_status") or ServiceTaxonomyReviewStatus.CONFIRMED.value,
                    explanation=f"Matched {'airline-specific ' if alias.get('airline_code') else ''}{alias_type} alias '{alias.get('alias_text')}'.",
                    alias_id=alias.get("id"),
                )

        rules = await self.list_mapping_rules(airline_code=airline_code, agency_id=agency_id)
        for rule in rules:
            if self._rule_matches(rule, normalized, tokens, text):
                return self._mapped_result(
                    text=text,
                    domain_code=rule["domain_code"],
                    family_code=rule["family_code"],
                    variant_code=rule.get("variant_code"),
                    confidence=float(rule.get("confidence_score") or 0.7),
                    review_status=ServiceTaxonomyReviewStatus.SUGGESTED.value,
                    explanation=f"Matched mapping rule '{rule.get('rule_name')}' using {rule.get('match_type')} match.",
                    mapping_rule_id=rule.get("id"),
                )

        return self._unknown_result(text, "No canonical alias or mapping rule matched; manual taxonomy review is required.")

    def _rule_matches(self, rule: dict[str, Any], normalized: str, tokens: set[str], raw_text: str) -> bool:
        match_type = rule.get("match_type")
        value = rule.get("normalized_match_value") or normalize_alias_text(rule.get("match_value"))
        if not value:
            return False
        if match_type == ServiceTaxonomyMatchType.EXACT.value:
            return normalized == value
        if match_type == ServiceTaxonomyMatchType.SSR_CODE.value:
            return value in tokens or normalized == value
        if match_type == ServiceTaxonomyMatchType.CONTAINS.value:
            return value in normalized
        if match_type == ServiceTaxonomyMatchType.TOKEN.value:
            return set(value.split(" ")).issubset(tokens)
        if match_type == ServiceTaxonomyMatchType.REGEX.value:
            return _safe_regex_match(rule.get("match_value") or "", raw_text)
        return False

    def _mapped_result(
        self,
        *,
        text: str,
        domain_code: str,
        family_code: str,
        variant_code: str | None,
        confidence: float,
        review_status: str,
        explanation: str,
        alias_id: str | None = None,
        mapping_rule_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "input_text": text,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "confidence_score": round(confidence, 4),
            "review_status": review_status,
            "outcome_type": None,
            "explanation": explanation,
            "alias_id": alias_id,
            "mapping_rule_id": mapping_rule_id,
            "deterministic_taxonomy_mapping_enabled": True,
            "external_ai_taxonomy_mapping_disabled": True,
        }

    def _unknown_result(self, text: str, explanation: str) -> dict[str, Any]:
        return {
            "input_text": text,
            "domain_code": "other",
            "family_code": "unknown_review_required",
            "variant_code": None,
            "confidence_score": 0.0,
            "review_status": ServiceTaxonomyReviewStatus.NEEDS_REVIEW.value,
            "outcome_type": "unknown_review_required",
            "explanation": explanation,
            "alias_id": None,
            "mapping_rule_id": None,
            "deterministic_taxonomy_mapping_enabled": True,
            "external_ai_taxonomy_mapping_disabled": True,
        }

    async def create_candidate_link(self, payload: Any, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        data["agency_id"] = agency_id
        candidate_type = enum_value(data.get("candidate_type"))
        candidate = await self._get_candidate(candidate_type, data.get("candidate_id"))
        evidence_text = data.get("evidence_text") or _candidate_excerpt(candidate)
        airline_code = normalize_airline_code(data.get("airline_code") or (candidate or {}).get("airline_iata_code") or (candidate or {}).get("airline_code"))

        if not data.get("domain_code") or not data.get("family_code"):
            mapping = await self.map_candidate_text(evidence_text, airline_code=airline_code, agency_id=agency_id)
            data["domain_code"] = mapping["domain_code"]
            data["family_code"] = mapping["family_code"]
            data["variant_code"] = data.get("variant_code") or mapping.get("variant_code")
            data["mapping_rule_id"] = data.get("mapping_rule_id") or mapping.get("mapping_rule_id")
            data["alias_id"] = data.get("alias_id") or mapping.get("alias_id")
            data["confidence_score"] = data.get("confidence_score") if data.get("confidence_score") is not None else mapping["confidence_score"]
            data["review_status"] = data.get("review_status") or mapping["review_status"]
        data["candidate_type"] = candidate_type
        data["airline_code"] = airline_code
        data["policy_source_id"] = data.get("policy_source_id") or (candidate or {}).get("policy_source_id")
        data["extraction_run_id"] = data.get("extraction_run_id") or (candidate or {}).get("extraction_run_id")
        data["evidence_text"] = evidence_text
        record = PolicyCandidateTaxonomyLink(**data)
        created = await self.db.collection(LINK_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "link": created,
            "external_ai_taxonomy_mapping_disabled": True,
            "agency_auto_promotion_disabled": True,
        }

    async def _get_candidate(self, candidate_type: str, candidate_id: str | None) -> dict[str, Any] | None:
        collection_name = CANDIDATE_COLLECTIONS.get(candidate_type)
        if not collection_name or not candidate_id:
            return None
        return await self.db.collection(collection_name).find_one({"id": candidate_id})

    async def list_candidate_links(
        self,
        agency_id: str | None = None,
        candidate_type: str | None = None,
        candidate_id: str | None = None,
        policy_source_id: str | None = None,
        extraction_run_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.db.collection(LINK_COLLECTION).find_many()
        if agency_id:
            items = [item for item in items if item.get("agency_id") in {None, agency_id}]
        if candidate_type:
            items = [item for item in items if item.get("candidate_type") == candidate_type]
        if candidate_id:
            items = [item for item in items if item.get("candidate_id") == candidate_id]
        if policy_source_id:
            items = [item for item in items if item.get("policy_source_id") == policy_source_id]
        if extraction_run_id:
            items = [item for item in items if item.get("extraction_run_id") == extraction_run_id]
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)

    async def update_candidate_link(self, link_id: str, payload: Any, agency_id: str | None = None) -> dict[str, Any] | None:
        existing = await self.db.collection(LINK_COLLECTION).find_one({"id": link_id})
        if not existing:
            return None
        if agency_id and existing.get("agency_id") not in {None, agency_id}:
            return None
        updates = clean_updates(payload)
        return await self.db.collection(LINK_COLLECTION).update_one({"id": link_id}, updates)

    async def create_review_correction(self, payload: Any, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        data["agency_id"] = agency_id
        if agency_id:
            data["correction_scope"] = ServiceTaxonomyCorrectionScope.AGENCY_LOCAL.value
            if data.get("promotion_requested"):
                data["promotion_status"] = ServiceTaxonomyPromotionStatus.PENDING_REVIEW.value
            else:
                data["promotion_status"] = ServiceTaxonomyPromotionStatus.NOT_REQUESTED.value
        data["reviewer_user_id"] = user.get("id")
        record = ServiceTaxonomyReviewCorrection(**data)
        created = await self.db.collection(CORRECTION_COLLECTION).insert_one(record.model_dump(mode="json"))
        link_id = created.get("policy_candidate_taxonomy_link_id")
        if link_id:
            await self.update_candidate_link(
                link_id,
                {
                    "domain_code": created["corrected_domain_code"],
                    "family_code": created["corrected_family_code"],
                    "variant_code": created.get("corrected_variant_code"),
                    "review_status": ServiceTaxonomyReviewStatus.CORRECTED.value,
                    "reviewer_notes": created.get("correction_reason"),
                },
                agency_id=agency_id,
            )
        return {
            "correction": created,
            "agency_auto_promotion_disabled": True,
            "promotion_status": created.get("promotion_status"),
        }

    async def list_review_corrections(
        self,
        agency_id: str | None = None,
        candidate_type: str | None = None,
        candidate_id: str | None = None,
        promotion_status: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.db.collection(CORRECTION_COLLECTION).find_many()
        if agency_id:
            items = [item for item in items if item.get("agency_id") in {None, agency_id}]
        if candidate_type:
            items = [item for item in items if item.get("candidate_type") == candidate_type]
        if candidate_id:
            items = [item for item in items if item.get("candidate_id") == candidate_id]
        if promotion_status:
            items = [item for item in items if item.get("promotion_status") == promotion_status]
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)
