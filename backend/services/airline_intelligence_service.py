from __future__ import annotations

from typing import Any

from database import Database
from models import AirlineIntelligenceProfile, AirlineIntelligenceProfileCreate, AirlineIntelligenceProfileUpdate, AuditEvent
from services.rules_and_services_registry import normalize_code


def clean_payload(payload: Any) -> dict[str, Any]:
    return payload.model_dump(mode="json", exclude_unset=True)


async def write_airline_intelligence_audit(
    db: Database,
    actor_user_id: str | None,
    event_type: str,
    entity_id: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type="airline_intelligence_profile",
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


class AirlineIntelligenceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_profile(self, airline_id_or_iata: str) -> dict[str, Any] | None:
        identifier = normalize_code(airline_id_or_iata)
        profile = await self.db.collection("airline_intelligence_profiles").find_one({"id": airline_id_or_iata})
        if profile is None:
            profile = await self.db.collection("airline_intelligence_profiles").find_one({"airline_id": airline_id_or_iata})
        if profile is None and identifier:
            profile = await self.db.collection("airline_intelligence_profiles").find_one({"iata_code": identifier})
        return profile

    async def get_airline_record(self, airline_id_or_iata: str) -> dict[str, Any] | None:
        identifier = normalize_code(airline_id_or_iata)
        airline = await self.db.collection("airline_profiles").find_one({"id": airline_id_or_iata})
        if airline is None and identifier:
            airline = await self.db.collection("airline_profiles").find_one({"airline_code": identifier})
        return airline

    async def list_airlines(self, search: str | None = None) -> list[dict[str, Any]]:
        profiles = await self.db.collection("airline_intelligence_profiles").find_many()
        profile_by_airline_id = {item.get("airline_id"): item for item in profiles if item.get("airline_id")}
        profile_by_iata = {normalize_code(item.get("iata_code")): item for item in profiles if item.get("iata_code")}
        airlines = await self.db.collection("airline_profiles").find_many()
        seen_profile_ids: set[str] = set()
        items: list[dict[str, Any]] = []
        for airline in airlines:
            profile = profile_by_airline_id.get(airline.get("id")) or profile_by_iata.get(normalize_code(airline.get("airline_code")))
            if profile:
                seen_profile_ids.add(profile["id"])
            items.append(
                {
                    "id": airline["id"],
                    "airline_id": airline["id"],
                    "iata_code": airline.get("airline_code"),
                    "icao_code": airline.get("icao_code"),
                    "legal_name": profile.get("legal_name") if profile else airline.get("airline_name"),
                    "base_country": profile.get("base_country") if profile else airline.get("country"),
                    "alliance": profile.get("alliance") if profile else airline.get("alliance"),
                    "governance_status": profile.get("governance_status") if profile else "draft",
                    "airline_profile": airline,
                    "intelligence_profile": profile,
                }
            )
        for profile in profiles:
            if profile["id"] in seen_profile_ids:
                continue
            items.append(
                {
                    "id": profile["id"],
                    "airline_id": profile.get("airline_id") or profile["id"],
                    "iata_code": profile.get("iata_code"),
                    "icao_code": profile.get("icao_code"),
                    "legal_name": profile.get("legal_name"),
                    "base_country": profile.get("base_country"),
                    "alliance": profile.get("alliance"),
                    "governance_status": profile.get("governance_status"),
                    "airline_profile": None,
                    "intelligence_profile": profile,
                }
            )
        if search:
            needle = search.lower()
            items = [
                item
                for item in items
                if any(needle in str(value or "").lower() for value in [item.get("iata_code"), item.get("icao_code"), item.get("legal_name"), item.get("base_country"), item.get("alliance")])
            ]
        return sorted(items, key=lambda item: (item.get("iata_code") or "", item.get("legal_name") or ""))

    async def create_profile(self, payload: AirlineIntelligenceProfileCreate, actor_user_id: str | None = None) -> dict[str, Any]:
        data = clean_payload(payload)
        if data.get("iata_code"):
            data["iata_code"] = normalize_code(data.get("iata_code"))
        if data.get("icao_code"):
            data["icao_code"] = normalize_code(data.get("icao_code"))
        profile = AirlineIntelligenceProfile(**data)
        created = await self.db.collection("airline_intelligence_profiles").insert_one(profile.model_dump(mode="json"))
        await write_airline_intelligence_audit(
            self.db,
            actor_user_id,
            "airline_intelligence.created",
            profile.id,
            f"Created airline intelligence profile {profile.iata_code or profile.legal_name or profile.id}.",
        )
        return created

    async def update_profile(self, airline_id_or_iata: str, payload: AirlineIntelligenceProfileUpdate, actor_user_id: str | None = None) -> dict[str, Any] | None:
        profile = await self.get_profile(airline_id_or_iata)
        if profile is None:
            return None
        updates = clean_payload(payload)
        if updates.get("iata_code"):
            updates["iata_code"] = normalize_code(updates.get("iata_code"))
        if updates.get("icao_code"):
            updates["icao_code"] = normalize_code(updates.get("icao_code"))
        updated = await self.db.collection("airline_intelligence_profiles").update_one({"id": profile["id"]}, updates)
        await write_airline_intelligence_audit(
            self.db,
            actor_user_id,
            "airline_intelligence.updated",
            profile["id"],
            "Updated airline intelligence profile.",
            {"fields": sorted(updates.keys())},
        )
        return updated
