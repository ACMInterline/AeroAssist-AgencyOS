from __future__ import annotations

import json
from typing import Any

from database import Database
from services.rules_and_services_registry import RulesAndServicesRegistry, normalize_code


ExceptionResult = dict[str, Any]


def value_at_path(payload: dict[str, Any], path: str | None) -> Any:
    if not path:
        return None
    current: Any = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def normalized_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def condition_matches(expression: Any, context: dict[str, Any]) -> tuple[bool, bool]:
    if expression in (None, "", {}):
        return True, True
    if isinstance(expression, str):
        try:
            expression = json.loads(expression)
        except json.JSONDecodeError:
            return False, False
    if not isinstance(expression, dict):
        return False, False
    if "all" in expression:
        results = [condition_matches(item, context) for item in normalized_list(expression.get("all"))]
        return all(result[0] for result in results), all(result[1] for result in results)
    if "any" in expression:
        results = [condition_matches(item, context) for item in normalized_list(expression.get("any"))]
        return any(result[0] for result in results), all(result[1] for result in results)

    path = expression.get("path") or expression.get("field")
    if not path:
        return False, False
    actual = value_at_path(context, path)
    if "equals" in expression:
        return actual == expression.get("equals"), True
    if "not_equals" in expression:
        return actual != expression.get("not_equals"), True
    if "in" in expression:
        return actual in normalized_list(expression.get("in")), True
    if "exists" in expression:
        return (actual is not None) == bool(expression.get("exists")), True
    if "contains" in expression:
        expected = expression.get("contains")
        if isinstance(actual, list):
            return expected in actual, True
        return str(expected).lower() in str(actual or "").lower(), True
    return False, False


class ExceptionEngineService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.registry = RulesAndServicesRegistry(db)

    async def evaluate(self, context: dict[str, Any]) -> ExceptionResult:
        category = normalize_code(context.get("service_category")) or "GENERAL"
        route = {
            "origin": context.get("route_origin"),
            "destination": context.get("route_destination"),
        }
        airline_identifier = context.get("airline_id") or context.get("iata_code")
        rules_context = await self.registry.get_rules_context(
            airline_identifier,
            route=route,
            aircraft_type=context.get("aircraft_type"),
            category=category,
        )
        warnings = list(rules_context.get("warnings") or [])
        actions: list[dict[str, Any]] = []
        required_documents: list[dict[str, Any]] = []
        policy_violations: list[dict[str, Any]] = []
        rules_fired: list[dict[str, Any]] = []
        allowed = True
        fallback_used = bool(rules_context.get("fallback_used"))

        for rule in rules_context.get("exception_rules") or []:
            matched, supported = condition_matches(rule.get("condition_expression"), context)
            if not supported:
                warnings.append(f"Rule {rule.get('id')} has an informational condition that requires manual review.")
                rules_fired.append(
                    {
                        "id": rule.get("id"),
                        "category": rule.get("category"),
                        "action": rule.get("action"),
                        "priority": rule.get("priority", 100),
                        "notes": rule.get("notes"),
                        "informational": True,
                    }
                )
                continue
            if not matched:
                continue

            action = normalize_code(rule.get("action")) or "WARN"
            fired = {
                "id": rule.get("id"),
                "category": rule.get("category"),
                "action": action,
                "priority": rule.get("priority", 100),
                "notes": rule.get("notes"),
            }
            rules_fired.append(fired)
            actions.append({"action": action, "rule_id": rule.get("id"), "notes": rule.get("notes")})
            docs = rule.get("required_documents_json") or []
            if docs:
                required_documents.extend(docs)
            if action == "BLOCK":
                allowed = False
                message = rule.get("notes") or "Service blocked by platform exception rule."
                warnings.append(message)
                policy_violations.append({"rule_id": rule.get("id"), "message": message})
            elif action == "WARN":
                warnings.append(rule.get("notes") or "Platform exception rule requires manual review.")
            elif action == "REQUIRE_DOC" and not docs:
                warnings.append(rule.get("notes") or "Platform exception rule requires supporting documents.")
            elif action == "OVERRIDE":
                warnings.append(rule.get("notes") or "Platform exception rule applies an override.")

        if not rules_context.get("exception_rules"):
            fallback_used = True
        confidence = 0.95 if rules_fired and allowed and not fallback_used else 0.75 if rules_fired else 0.5
        return {
            "allowed": allowed,
            "actions": actions,
            "warnings": list(dict.fromkeys([warning for warning in warnings if warning])),
            "required_documents": required_documents,
            "policy_violations": policy_violations,
            "rules_fired": rules_fired,
            "confidence": confidence,
            "fallback_used": fallback_used,
            "rules_context": rules_context,
        }
