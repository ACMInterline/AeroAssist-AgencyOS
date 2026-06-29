from __future__ import annotations

from datetime import date
from typing import Any

from database import Database


MANUAL_VERIFY_WARNING = "No airline rules configured yet — verify manually."


def normalize_code(value: str | None) -> str | None:
    if value is None:
        return None
    clean = str(value).strip().upper()
    return clean or None


def date_from_value(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def route_parts(route: dict[str, Any] | None = None) -> tuple[str | None, str | None]:
    route = route or {}
    return normalize_code(route.get("origin") or route.get("route_origin")), normalize_code(route.get("destination") or route.get("route_destination"))


class RulesAndServicesRegistry:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def resolve_airline(self, airline_id_or_iata: str | None) -> dict[str, Any]:
        identifier = normalize_code(airline_id_or_iata)
        if not identifier:
            return {"airline_id": None, "iata_code": None, "airline_profile": None, "intelligence_profile": None, "reference_record": None}

        airline_profile = await self.db.collection("airline_profiles").find_one({"id": airline_id_or_iata})
        if airline_profile is None:
            airline_profile = await self.db.collection("airline_profiles").find_one({"airline_code": identifier})

        intelligence_profile = await self.db.collection("airline_intelligence_profiles").find_one({"id": airline_id_or_iata})
        if intelligence_profile is None and airline_profile:
            intelligence_profile = await self.db.collection("airline_intelligence_profiles").find_one({"airline_id": airline_profile["id"]})
        if intelligence_profile is None:
            intelligence_profile = await self.db.collection("airline_intelligence_profiles").find_one({"iata_code": identifier})

        reference_record = await self.db.collection("global_reference_records").find_one({"id": airline_id_or_iata})
        if reference_record is None:
            reference_record = await self.db.collection("global_reference_records").find_one({"domain": "airlines", "code": identifier})
        if reference_record is None:
            reference_record = await self.db.collection("global_reference_records").find_one({"domain": "airlines", "key": identifier})
        if reference_record is None:
            references = await self.db.collection("global_reference_records").find_many({"domain": "airlines"})
            reference_record = next(
                (
                    item
                    for item in references
                    if normalize_code((item.get("metadata_json") or item.get("metadata") or {}).get("iata_code")) == identifier
                    or normalize_code((item.get("metadata_json") or item.get("metadata") or {}).get("icao_code")) == identifier
                ),
                None,
            )

        airline_id = (
            (airline_profile or {}).get("id")
            or (intelligence_profile or {}).get("airline_id")
            or (reference_record or {}).get("id")
            or airline_id_or_iata
        )
        iata_code = (
            normalize_code((airline_profile or {}).get("airline_code"))
            or normalize_code((intelligence_profile or {}).get("iata_code"))
            or normalize_code((reference_record or {}).get("code"))
            or normalize_code(((reference_record or {}).get("metadata_json") or (reference_record or {}).get("metadata") or {}).get("iata_code"))
            or (identifier if len(identifier) == 2 else None)
        )
        return {
            "airline_id": airline_id,
            "iata_code": iata_code,
            "airline_profile": airline_profile,
            "intelligence_profile": intelligence_profile,
            "reference_record": reference_record,
        }

    async def get_airline_profile(self, airline_id_or_iata: str | None) -> dict[str, Any]:
        resolved = await self.resolve_airline(airline_id_or_iata)
        warnings: list[str] = []
        if not resolved.get("airline_profile") and not resolved.get("intelligence_profile") and not resolved.get("reference_record"):
            warnings.append("Airline profile not found in platform reference or intelligence data.")
        return {**resolved, "warnings": warnings}

    async def get_airline_rules(self, airline_id_or_iata: str | None) -> dict[str, Any]:
        resolved = await self.resolve_airline(airline_id_or_iata)
        rules = None
        airline_id = resolved.get("airline_id")
        iata_code = resolved.get("iata_code")
        if airline_id:
            rules = await self.db.collection("airline_rules_core").find_one({"airline_id": airline_id})
        if rules is None and iata_code:
            rules = await self.db.collection("airline_rules_core").find_one({"iata_code": iata_code})
        warnings = [] if rules else [MANUAL_VERIFY_WARNING]
        return {"rules": rules, "airline": resolved, "warnings": warnings}

    async def get_exception_rules(
        self,
        category: str | None,
        airline_id: str | None = None,
        route: dict[str, Any] | None = None,
        aircraft_type: str | None = None,
        service_key: str | None = None,
        service_catalogue_category: str | None = None,
    ) -> list[dict[str, Any]]:
        resolved = await self.resolve_airline(airline_id)
        airline_ids = {value for value in [airline_id, resolved.get("airline_id")] if value}
        iata_codes = {value for value in [normalize_code(airline_id), resolved.get("iata_code")] if value}
        origin, destination = route_parts(route)
        aircraft = normalize_code(aircraft_type)
        service = normalize_code(service_key)
        service_category = normalize_code(service_catalogue_category) or normalize_code(category)
        today = date.today()
        filters = {"active": True}
        if category:
            filters["category"] = normalize_code(category)
        rules = await self.db.collection("unified_exception_rules").find_many(filters)

        def matches(rule: dict[str, Any]) -> bool:
            rule_airline_id = rule.get("airline_id")
            rule_iata = normalize_code(rule.get("iata_code"))
            if rule_airline_id and rule_airline_id not in airline_ids:
                return False
            if rule_iata and rule_iata not in iata_codes:
                return False
            if rule.get("route_origin") and normalize_code(rule.get("route_origin")) != origin:
                return False
            if rule.get("route_destination") and normalize_code(rule.get("route_destination")) != destination:
                return False
            if rule.get("airport_code"):
                airport = normalize_code(rule.get("airport_code"))
                if airport not in {origin, destination}:
                    return False
            if rule.get("aircraft_type") and normalize_code(rule.get("aircraft_type")) != aircraft:
                return False
            if rule.get("service_key") and normalize_code(rule.get("service_key")) != service:
                return False
            if rule.get("service_catalogue_category") and normalize_code(rule.get("service_catalogue_category")) != service_category:
                return False
            effective_from = date_from_value(rule.get("effective_from"))
            effective_to = date_from_value(rule.get("effective_to"))
            if effective_from and effective_from > today:
                return False
            if effective_to and effective_to < today:
                return False
            return True

        return sorted([rule for rule in rules if matches(rule)], key=lambda item: item.get("priority", 100))

    async def get_rules_context(
        self,
        airline_id_or_iata: str | None,
        route: dict[str, Any] | None = None,
        aircraft_type: str | None = None,
        category: str | None = None,
        service_key: str | None = None,
        service_catalogue_category: str | None = None,
    ) -> dict[str, Any]:
        resolved = await self.resolve_airline(airline_id_or_iata)
        airline_id = resolved.get("airline_id")
        rules_payload = await self.get_airline_rules(airline_id or airline_id_or_iata)
        exception_rules = await self.get_exception_rules(
            category,
            airline_id or airline_id_or_iata,
            route,
            aircraft_type,
            service_key=service_key,
            service_catalogue_category=service_catalogue_category,
        )
        ancillaries = await self.db.collection("airline_ancillaries").find_many({"airline_id": airline_id}) if airline_id else []
        distribution_profile = await self.db.collection("airline_distribution_profiles").find_one({"airline_id": airline_id}) if airline_id else None
        pss_parameters = await self.db.collection("airline_pss_parameters").find_one({"airline_id": airline_id}) if airline_id else None
        gds_parameters = await self.db.collection("airline_gds_parameters").find_many({"airline_id": airline_id}) if airline_id else []
        warnings = [*rules_payload.get("warnings", [])]
        if not resolved.get("airline_profile") and not resolved.get("intelligence_profile") and not resolved.get("reference_record"):
            warnings.append("Airline could not be resolved from existing platform data.")
        return {
            "airline": resolved,
            "airline_profile": resolved.get("airline_profile"),
            "intelligence_profile": resolved.get("intelligence_profile"),
            "reference_record": resolved.get("reference_record"),
            "rules_core": rules_payload.get("rules"),
            "exception_rules": exception_rules,
            "ancillaries": ancillaries,
            "distribution_profile": distribution_profile,
            "pss_parameters": pss_parameters,
            "gds_parameters": gds_parameters,
            "warnings": list(dict.fromkeys(warnings)),
            "fallback_used": bool(warnings),
        }
