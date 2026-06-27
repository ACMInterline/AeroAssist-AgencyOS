#!/usr/bin/env python3
import asyncio
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import Database  # noqa: E402
from models import AirlineIntelligenceProfile, AirlineProfile, AirlineRulesCore, UnifiedExceptionRule  # noqa: E402


AIRLINES = [
    {
        "airline_code": "LH",
        "icao_code": "DLH",
        "numeric_code": "220",
        "airline_name": "Lufthansa",
        "legal_name": "Deutsche Lufthansa AG",
        "country": "DE",
        "alliance": "Star Alliance",
        "headquarters": "Cologne, Germany",
        "base_country": "DE",
        "hubs": [{"iata_code": "FRA", "name": "Frankfurt"}, {"iata_code": "MUC", "name": "Munich"}],
    },
    {
        "airline_code": "TK",
        "icao_code": "THY",
        "numeric_code": "235",
        "airline_name": "Turkish Airlines",
        "legal_name": "Turkish Airlines",
        "country": "TR",
        "alliance": "Star Alliance",
        "headquarters": "Istanbul, Turkiye",
        "base_country": "TR",
        "hubs": [{"iata_code": "IST", "name": "Istanbul"}],
    },
    {
        "airline_code": "AF",
        "icao_code": "AFR",
        "numeric_code": "057",
        "airline_name": "Air France",
        "legal_name": "Air France",
        "country": "FR",
        "alliance": "SkyTeam",
        "headquarters": "Tremblay-en-France, France",
        "base_country": "FR",
        "hubs": [{"iata_code": "CDG", "name": "Paris Charles de Gaulle"}, {"iata_code": "ORY", "name": "Paris Orly"}],
    },
]


async def ensure_airline_profile(db: Database, spec: dict[str, Any], created: list[str]) -> dict[str, Any]:
    existing = await db.collection("airline_profiles").find_one({"airline_code": spec["airline_code"]})
    if existing:
        return existing
    profile = AirlineProfile(
        airline_code=spec["airline_code"],
        icao_code=spec["icao_code"],
        airline_name=spec["airline_name"],
        country=spec["country"],
        alliance=spec["alliance"],
        website_url=None,
        notes="Seeded Phase 36 rules/services foundation airline.",
    )
    created_profile = await db.collection("airline_profiles").insert_one(profile.model_dump(mode="json"))
    created.append(f"airline_profile:{spec['airline_code']}")
    return created_profile


async def ensure_intelligence_profile(db: Database, airline: dict[str, Any], spec: dict[str, Any], created: list[str]) -> dict[str, Any]:
    existing = await db.collection("airline_intelligence_profiles").find_one({"airline_id": airline["id"]})
    if existing is None:
        existing = await db.collection("airline_intelligence_profiles").find_one({"iata_code": spec["airline_code"]})
    if existing:
        return existing
    profile = AirlineIntelligenceProfile(
        airline_id=airline["id"],
        iata_code=spec["airline_code"],
        icao_code=spec["icao_code"],
        numeric_code=spec["numeric_code"],
        legal_name=spec["legal_name"],
        alliance=spec["alliance"],
        headquarters=spec["headquarters"],
        base_country=spec["base_country"],
        hubs_json=spec["hubs"],
        source_metadata_json={"seed": "phase_36_rules_services_foundation"},
        governance_status="draft",
    )
    created_profile = await db.collection("airline_intelligence_profiles").insert_one(profile.model_dump(mode="json"))
    created.append(f"airline_intelligence_profile:{spec['airline_code']}")
    return created_profile


async def ensure_rules_core(db: Database, airline: dict[str, Any], spec: dict[str, Any], created: list[str]) -> dict[str, Any]:
    existing = await db.collection("airline_rules_core").find_one({"airline_id": airline["id"]})
    if existing:
        return existing
    rules = AirlineRulesCore(
        airline_id=airline["id"],
        iata_code=spec["airline_code"],
        umnr_rules_json={"advance_notice_hours": 48, "manual_verification_required": True},
        prm_rules_json={"wheelchair_codes": ["WCHR", "WCHS", "WCHC"], "airport_coordination_required": True},
        medical_rules_json={"medif_required_for": ["MEDIF", "OXYG", "STCR"], "medical_clearance_manual_review": True},
        pets_service_animals_rules_json={"supported_codes": ["PETC", "AVIH", "SVAN"], "documents_required": True},
        cargo_oversized_rules_json={"manual_review_required_for": ["SPEQ", "WEAP"]},
        vip_protocol_rules_json={"supported_codes": ["VIP", "VVIP", "DIPB"], "protocol_contact_required": True},
        general_notes="Seeded examples only. Verify against current airline sources before operational commitment.",
        source_metadata_json={"seed": "phase_36_rules_services_foundation"},
        governance_status="draft",
    )
    created_rules = await db.collection("airline_rules_core").insert_one(rules.model_dump(mode="json"))
    created.append(f"airline_rules_core:{spec['airline_code']}")
    return created_rules


async def ensure_exception_rule(db: Database, seed_key: str, payload: dict[str, Any], created: list[str]) -> dict[str, Any]:
    existing_rules = await db.collection("unified_exception_rules").find_many()
    existing = next((rule for rule in existing_rules if (rule.get("source_metadata_json") or {}).get("seed_key") == seed_key), None)
    if existing:
        return existing
    rule = UnifiedExceptionRule(**{**payload, "source_metadata_json": {"seed": "phase_36_rules_services_foundation", "seed_key": seed_key}})
    created_rule = await db.collection("unified_exception_rules").insert_one(rule.model_dump(mode="json"))
    created.append(f"unified_exception_rule:{seed_key}")
    return created_rule


async def seed_airline_rules_services_foundation(db: Database) -> dict[str, Any]:
    created: list[str] = []
    for spec in AIRLINES:
        airline = await ensure_airline_profile(db, spec, created)
        await ensure_intelligence_profile(db, airline, spec, created)
        await ensure_rules_core(db, airline, spec, created)
        iata = spec["airline_code"]
        await ensure_exception_rule(
            db,
            f"{iata}:prm-warning",
            {
                "category": "PRM",
                "airline_id": airline["id"],
                "iata_code": iata,
                "action": "WARN",
                "notes": f"{iata} PRM services require manual station and timing verification.",
                "priority": 40,
            },
            created,
        )
        await ensure_exception_rule(
            db,
            f"{iata}:pets-docs",
            {
                "category": "PETS",
                "airline_id": airline["id"],
                "iata_code": iata,
                "action": "REQUIRE_DOC",
                "required_documents_json": [{"code": "pet_health_documents", "label": "Pet health, vaccination, and entry documents"}],
                "notes": f"{iata} pet travel requires document verification before confirmation.",
                "priority": 30,
            },
            created,
        )
        await ensure_exception_rule(
            db,
            f"{iata}:medical-medif",
            {
                "category": "MEDICAL",
                "airline_id": airline["id"],
                "iata_code": iata,
                "condition_expression": {"path": "service_type", "in": ["MEDA", "MEDIF", "OXYG"]},
                "action": "REQUIRE_DOC",
                "required_documents_json": [{"code": "medif", "label": "MEDIF or medical clearance"}],
                "notes": f"{iata} medical services require MEDIF/manual medical clearance review.",
                "priority": 20,
            },
            created,
        )
        await ensure_exception_rule(
            db,
            f"{iata}:stcr-aircraft-support",
            {
                "category": "MEDICAL",
                "airline_id": airline["id"],
                "iata_code": iata,
                "condition_expression": {"path": "service_payload_json.aircraft_supports_stretcher", "equals": False},
                "action": "BLOCK",
                "required_documents_json": [{"code": "stretcher_clearance", "label": "Stretcher aircraft support confirmation"}],
                "notes": f"{iata} STCR is blocked until aircraft support is confirmed.",
                "priority": 10,
            },
            created,
        )
    return {
        "created": created,
        "airline_rules_core_count": await db.collection("airline_rules_core").count(),
        "exception_rule_count": await db.collection("unified_exception_rules").count(),
    }


async def run() -> dict[str, Any]:
    db = Database()
    await db.connect()
    return await seed_airline_rules_services_foundation(db)


def main() -> int:
    result = asyncio.run(run())
    print(json.dumps({"ok": True, "seed": result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
