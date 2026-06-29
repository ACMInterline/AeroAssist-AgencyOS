from __future__ import annotations

from typing import Any

from database import Database
from models import ServiceCatalogueRecord


SERVICE_RULES_CATEGORY_BY_CODE = {
    "UMNR": "UMNR",
    "WCHR": "PRM",
    "WCHS": "PRM",
    "WCHC": "PRM",
    "WCHP": "PRM",
    "WCHD": "PRM",
    "BLND": "PRM",
    "DEAF": "PRM",
    "MEDA": "MEDICAL",
    "MEDIF": "MEDICAL",
    "OXYG": "MEDICAL",
    "STCR": "MEDICAL",
    "PETC": "PETS",
    "AVIH": "PETS",
    "SVAN": "SERVICE_ANIMAL",
    "EXST": "SEATING",
    "SPML": "MEAL",
    "MOBILITY_DEVICE": "PRM",
    "SPORTS_EQUIPMENT": "CARGO",
    "MUSICAL_INSTRUMENT": "CARGO",
    "FRAGILE_VALUABLE": "CARGO",
}


def normalize_service_key(value: Any) -> str:
    return str(value or "").strip().upper()


def default_required_documents(record: dict[str, Any]) -> list[dict[str, Any]]:
    if record.get("required_documents_json"):
        return record["required_documents_json"]
    if not record.get("requires_document_check"):
        return []
    code = normalize_service_key(record.get("service_code") or record.get("service_key"))
    return [{"code": f"{code.lower()}_documents", "label": f"{code} supporting documents"}]


def normalize_service_catalogue_payload(payload: dict[str, Any], actor_user_id: str | None = None) -> dict[str, Any]:
    data = dict(payload)
    service_key = normalize_service_key(data.get("service_key") or data.get("service_code"))
    label = data.get("label") or data.get("service_label")
    category = data.get("category") or data.get("service_family_code")
    status = data.get("status") or ("active" if data.get("is_active", data.get("active", True)) else "archived")
    active = bool(data.get("active", data.get("is_active", True))) and status != "archived"
    default_ssr = data.get("default_ssr_code") or data.get("ssr_code")
    rules_category = data.get("rules_category") or SERVICE_RULES_CATEGORY_BY_CODE.get(service_key) or str(category or "OTHER").upper()
    beneficiary_type = data.get("beneficiary_type") or "passenger"
    requires_segment = data.get("requires_segment_scope", data.get("requires_segment_scoping", True))
    requires_policy = data.get("policy_check_required", data.get("requires_policy_check", True))
    requires_pricing = data.get("fee_expected", data.get("requires_manual_pricing", False))
    source_type = data.get("source_type") or "platform"

    normalized = {
        **data,
        "service_key": service_key,
        "service_code": service_key,
        "label": label,
        "service_label": label,
        "category": category,
        "service_family_code": category,
        "status": status,
        "active": active,
        "is_active": active,
        "default_ssr_code": default_ssr,
        "ssr_code": data.get("ssr_code") or default_ssr,
        "beneficiary_type": beneficiary_type,
        "requires_segment_scoping": bool(data.get("requires_segment_scoping", requires_segment)),
        "requires_segment_scope": bool(requires_segment),
        "requires_policy_check": bool(data.get("requires_policy_check", requires_policy)),
        "policy_check_required": bool(requires_policy),
        "requires_document_check": bool(data.get("requires_document_check", bool(data.get("required_documents_json")))),
        "requires_manual_pricing": bool(data.get("requires_manual_pricing", requires_pricing)),
        "fee_expected": bool(requires_pricing),
        "offer_pricing_enabled": bool(data.get("offer_pricing_enabled", requires_pricing)),
        "default_service_type": data.get("default_service_type") or service_key,
        "rules_category": rules_category,
        "request_form_enabled": bool(data.get("request_form_enabled", True)),
        "maps_to_passenger_service_request": bool(data.get("maps_to_passenger_service_request", True)),
        "exception_engine_enabled": bool(data.get("exception_engine_enabled", True)),
        "booking_preview_enabled": bool(data.get("booking_preview_enabled", True)),
        "offer_feasibility_enabled": bool(data.get("offer_feasibility_enabled", True)),
        "acceptance_snapshot_enabled": bool(data.get("acceptance_snapshot_enabled", True)),
        "booking_readiness_enabled": bool(data.get("booking_readiness_enabled", True)),
        "client_document_summary_enabled": bool(data.get("client_document_summary_enabled", True)),
        "links_to_pet_taxonomy": bool(data.get("links_to_pet_taxonomy", beneficiary_type == "pet")),
        "links_to_special_item_taxonomy": bool(data.get("links_to_special_item_taxonomy", beneficiary_type == "special_item")),
        "required_documents_json": default_required_documents(data),
        "source_type": source_type,
        "updated_by_user_id": actor_user_id if actor_user_id is not None else data.get("updated_by_user_id"),
    }
    return {key: value for key, value in normalized.items() if value is not None}


def safe_service_catalogue_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_service_catalogue_payload(record)
    return {
        **record,
        **normalized,
        "operational_mappings": {
            "request": {
                "request_form_enabled": normalized.get("request_form_enabled", True),
                "requires_passenger_scope": normalized.get("requires_passenger_scope", False),
                "requires_segment_scope": normalized.get("requires_segment_scope", True),
                "segment_scope_default": normalized.get("segment_scope_default", "all_segments"),
                "required_fields_json": normalized.get("required_fields_json") or {},
            },
            "rules_services": {
                "rules_category": normalized.get("rules_category"),
                "default_service_type": normalized.get("default_service_type"),
                "exception_engine_enabled": normalized.get("exception_engine_enabled", True),
                "policy_check_required": normalized.get("policy_check_required", True),
            },
            "ssr_osi": {
                "ssr_code": normalized.get("ssr_code"),
                "ssr_template": normalized.get("ssr_template"),
                "osi_template": normalized.get("osi_template"),
                "booking_preview_enabled": normalized.get("booking_preview_enabled", True),
            },
            "offer": {
                "offer_feasibility_enabled": normalized.get("offer_feasibility_enabled", True),
                "offer_pricing_enabled": normalized.get("offer_pricing_enabled", False),
                "default_pricing_category": normalized.get("default_pricing_category"),
            },
            "acceptance_booking_readiness": {
                "acceptance_snapshot_enabled": normalized.get("acceptance_snapshot_enabled", True),
                "booking_readiness_enabled": normalized.get("booking_readiness_enabled", True),
                "emd_applicability": normalized.get("emd_applicability", "none"),
                "fee_expected": normalized.get("fee_expected", False),
            },
            "documents": {
                "required_documents_json": normalized.get("required_documents_json") or [],
                "client_document_summary_enabled": normalized.get("client_document_summary_enabled", True),
            },
        },
    }


def service_catalogue_snapshot(record: dict[str, Any] | None) -> dict[str, Any]:
    if not record:
        return {}
    safe = safe_service_catalogue_record(record)
    return {
        "service_catalogue_id": safe.get("id"),
        "service_key": safe.get("service_key"),
        "label": safe.get("label"),
        "category": safe.get("category"),
        "subcategory": safe.get("subcategory"),
        "status": safe.get("status"),
        "ssr_code": safe.get("ssr_code"),
        "osi_template": safe.get("osi_template"),
        "ssr_template": safe.get("ssr_template"),
        "rules_category": safe.get("rules_category"),
        "default_service_type": safe.get("default_service_type"),
        "default_pricing_category": safe.get("default_pricing_category"),
        "required_documents_json": safe.get("required_documents_json") or [],
        "booking_readiness_enabled": safe.get("booking_readiness_enabled", True),
        "emd_applicability": safe.get("emd_applicability", "none"),
        "operational_mappings": safe.get("operational_mappings") or {},
    }


async def find_service_catalogue_record(db: Database, service_key: str | None) -> dict[str, Any] | None:
    key = normalize_service_key(service_key)
    if not key:
        return None
    records = await db.collection("service_catalogue").find_many()
    for record in records:
        safe = safe_service_catalogue_record(record)
        candidates = {
            normalize_service_key(safe.get("service_key")),
            normalize_service_key(safe.get("service_code")),
            normalize_service_key(safe.get("default_ssr_code")),
            normalize_service_key(safe.get("ssr_code")),
            normalize_service_key(safe.get("default_service_type")),
        }
        if key in candidates:
            return safe
    return None


async def insert_service_catalogue_record(db: Database, payload: dict[str, Any], actor_user_id: str | None) -> dict[str, Any]:
    normalized = normalize_service_catalogue_payload(payload, actor_user_id)
    record = ServiceCatalogueRecord(**{**normalized, "created_by_user_id": actor_user_id})
    return await db.collection("service_catalogue").insert_one(record.model_dump(mode="json"))


async def update_service_catalogue_record(
    db: Database,
    existing: dict[str, Any],
    payload: dict[str, Any],
    actor_user_id: str | None,
) -> dict[str, Any]:
    normalized = normalize_service_catalogue_payload({**existing, **payload}, actor_user_id)
    normalized.pop("id", None)
    normalized.pop("created_at", None)
    normalized.pop("created_by_user_id", None)
    return await db.collection("service_catalogue").update_one({"id": existing["id"]}, normalized)
