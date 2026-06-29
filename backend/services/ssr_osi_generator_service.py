from __future__ import annotations

from typing import Any

from database import Database
from services.exception_engine_service import ExceptionEngineService
from services.rules_and_services_registry import normalize_code


SSR_REQUIRED_DOCUMENTS = {
    "UMNR": [{"code": "guardian_contacts", "label": "Guardian and handover contact details"}],
    "MEDA": [{"code": "medical_clearance", "label": "Medical clearance"}],
    "MEDIF": [{"code": "medif", "label": "MEDIF form"}],
    "OXYG": [{"code": "oxygen_clearance", "label": "Oxygen approval or medical clearance"}],
    "STCR": [{"code": "stretcher_clearance", "label": "Stretcher medical clearance"}],
    "PETC": [{"code": "pet_documents", "label": "Pet health and entry documents"}],
    "AVIH": [{"code": "pet_documents", "label": "Pet health and entry documents"}],
    "SVAN": [{"code": "service_animal_documents", "label": "Service animal documentation"}],
    "WEAP": [{"code": "regulated_items_documents", "label": "Regulated items permits"}],
    "DIPB": [{"code": "protocol_clearance", "label": "Diplomatic protocol clearance"}],
}


SSR_CODE_MAP = {
    "UMNR": "UMNR",
    "WCHR": "WCHR",
    "WCHS": "WCHS",
    "WCHC": "WCHC",
    "WCHP": "WCHP",
    "WCHD": "WCHD",
    "BLND": "BLND",
    "DEAF": "DEAF",
    "MEDA": "MEDA",
    "MEDIF": "MEDA",
    "OXYG": "OXYG",
    "STCR": "STCR",
    "PETC": "PETC",
    "AVIH": "AVIH",
    "SVAN": "SVAN",
    "EXST": "EXST",
    "SPML": "SPML",
    "SPEQ": "SPEQ",
    "WEAP": "WEAP",
    "DIPB": "DIPB",
    "VIP": "VIP",
    "VVIP": "VIP",
    "DIPLOMAT": "DIPB",
}


def payload_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if payload.get(key) not in (None, ""):
            return payload[key]
    return None


def compact_text(value: str) -> str:
    return " ".join(value.upper().split())[:180]


def build_ssr_text(service_type: str, payload: dict[str, Any]) -> str:
    service = normalize_code(service_type) or "OTHS"
    if service == "UMNR":
        age = payload_value(payload, "age", "child_age", "minor_age")
        return compact_text(f"UMNR AGE {age}" if age else "UMNR DETAILS ON FILE")
    if service in {"WCHR", "WCHS", "WCHC", "WCHP", "WCHD"}:
        return compact_text(payload_value(payload, "assistance_text", "notes") or service)
    if service in {"BLND", "DEAF"}:
        return compact_text(payload_value(payload, "assistance_text", "notes") or f"{service} ASSISTANCE REQUIRED")
    if service in {"MEDA", "MEDIF"}:
        return compact_text(payload_value(payload, "medical_text", "diagnosis_summary", "notes") or "MEDICAL CLEARANCE REQUIRED")
    if service == "OXYG":
        flow = payload_value(payload, "oxygen_flow_rate", "flow_rate")
        return compact_text(f"OXYGEN {flow}" if flow else "OXYGEN REQUEST")
    if service == "STCR":
        return compact_text(payload_value(payload, "stretcher_text", "notes") or "STRETCHER REQUEST")
    if service in {"PETC", "AVIH", "SVAN"}:
        species = payload_value(payload, "species", "animal_species", "pet_species")
        weight = payload_value(payload, "weight_kg", "combined_weight_kg")
        parts = [service, species, f"{weight}KG" if weight else None]
        return compact_text(" ".join(str(part) for part in parts if part))
    if service == "EXST":
        reason = payload_value(payload, "reason", "notes")
        return compact_text(f"EXTRA SEAT {reason}" if reason else "EXTRA SEAT REQUEST")
    if service == "SPML":
        meal = payload_value(payload, "meal_code", "meal_type", "meal_name")
        return compact_text(f"SPML {meal}" if meal else "SPECIAL MEAL REQUEST")
    if service == "SPEQ":
        item = payload_value(payload, "equipment_type", "item_type", "item_name")
        return compact_text(f"SPECIAL EQUIPMENT {item}" if item else "SPECIAL EQUIPMENT")
    if service == "WEAP":
        return compact_text(payload_value(payload, "regulated_item_text", "notes") or "REGULATED ITEMS DECLARED")
    if service in {"DIPB", "DIPLOMAT"}:
        return compact_text(payload_value(payload, "protocol_text", "notes") or "DIPLOMATIC PROTOCOL REQUEST")
    if service in {"VIP", "VVIP"}:
        return compact_text(payload_value(payload, "protocol_text", "notes") or f"{service} PROTOCOL REQUEST")
    return compact_text(payload_value(payload, "notes") or service)


def merge_documents(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for document in group or []:
            key = (str(document.get("code") or ""), str(document.get("label") or document))
            if key not in seen:
                seen.add(key)
                merged.append(document)
    return merged


def render_catalogue_template(template: str | None, values: dict[str, Any]) -> str | None:
    if not template:
        return None
    try:
        return compact_text(template.format(**values))
    except (KeyError, ValueError):
        return compact_text(template)


class SsrOsiGeneratorService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.exception_engine = ExceptionEngineService(db)

    async def generate(self, context: dict[str, Any], exception_result: dict[str, Any] | None = None) -> dict[str, Any]:
        result = exception_result or await self.exception_engine.evaluate(context)
        warnings = list(result.get("warnings") or [])
        payload = context.get("service_payload_json") or {}
        catalogue = context.get("service_catalogue_snapshot_json") or payload.get("service_catalogue_snapshot_json") or {}
        service_type = normalize_code(catalogue.get("service_key") or catalogue.get("default_service_type") or context.get("service_type")) or "OTHS"
        required_documents = merge_documents(
            SSR_REQUIRED_DOCUMENTS.get(service_type, []),
            catalogue.get("required_documents_json") or [],
            result.get("required_documents") or [],
        )
        ssr_code = normalize_code(catalogue.get("ssr_code")) or SSR_CODE_MAP.get(service_type)
        iata_code = normalize_code(context.get("iata_code")) or normalize_code((result.get("rules_context") or {}).get("airline", {}).get("iata_code"))
        template_values = {**payload, **context, "service_type": service_type, "service_key": catalogue.get("service_key") or service_type}

        if not result.get("allowed", True):
            draft_text = render_catalogue_template(catalogue.get("ssr_template"), template_values) or build_ssr_text(service_type, payload)
            return {
                "ssr": [],
                "osi": [{"airline_code": iata_code, "text": f"MANUAL REVIEW ONLY - {draft_text}", "status": "draft"}],
                "warnings": list(dict.fromkeys([*warnings, "Service is blocked by exception rules; approved SSR/OSI was not generated."])),
                "required_documents": required_documents,
                "blocked": True,
                "exception_result": result,
            }

        ssr: list[dict[str, Any]] = []
        osi: list[dict[str, Any]] = []
        text = render_catalogue_template(catalogue.get("ssr_template"), template_values) or build_ssr_text(service_type, payload)
        osi_text = render_catalogue_template(catalogue.get("osi_template"), template_values)
        if ssr_code:
            ssr.append({"airline_code": iata_code, "code": ssr_code, "text": text, "status": "preview"})
        else:
            warnings.append(f"No deterministic SSR code configured for service type {service_type}.")
        if osi_text or service_type in {"VIP", "VVIP", "DIPLOMAT", "DIPB", "WEAP"}:
            osi.append({"airline_code": iata_code, "text": osi_text or text, "status": "preview"})
        if service_type == "MEDIF":
            osi.append({"airline_code": iata_code, "text": "MEDIF FORM REQUIRED BEFORE AIRLINE CONFIRMATION", "status": "preview"})
        return {
            "ssr": ssr,
            "osi": osi,
            "warnings": list(dict.fromkeys([warning for warning in warnings if warning])),
            "required_documents": required_documents,
            "blocked": False,
            "exception_result": result,
        }
