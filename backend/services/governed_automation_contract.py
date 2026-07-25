from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


MAX_CONDITION_DEPTH = 4
MAX_CONDITIONS_PER_GROUP = 20
MAX_LIST_VALUES = 50
MAX_ACTIONS_PER_RULE = 12
MAX_CHAINED_ACTIONS = 25
MAX_RECURSION_DEPTH = 3
MAX_TRACE_ITEMS = 100
MAX_TRACE_TEXT = 500

CANONICAL_AUTOMATION_EVENTS = (
    "request.created",
    "request.submitted",
    "request.qualified",
    "request.missing_information",
    "request.updated",
    "request.cancelled",
    "offer.created",
    "offer.ready",
    "offer.delivered",
    "offer.revised",
    "offer.accepted",
    "offer.declined",
    "offer.expired",
    "offer.superseded",
    "trip.confirmed",
    "trip.updated",
    "trip.cancelled",
    "trip.service_added",
    "trip.document_required",
    "booking.preparation_started",
    "booking.ready",
    "booking.blocked",
    "booking.confirmed",
    "booking.failed",
    "booking.cancelled",
    "ticket.recorded",
    "ticket.deadline_approaching",
    "ticket.refund_requested",
    "ticket.exchange_requested",
    "emd.required",
    "emd.recorded",
    "invoice.draft_created",
    "invoice.issued",
    "invoice.due_soon",
    "invoice.overdue",
    "payment.received",
    "payment.unallocated",
    "supplier_cost.missing",
    "supplier_cost.confirmed",
    "margin.below_threshold",
    "credit_note.issued",
    "refund.requested",
    "refund.posted",
    "exchange.requested",
    "exchange.confirmed",
    "communication.received",
    "client_reply_received",
    "passenger_reply_received",
    "supplier_reply_received",
    "document.requested",
    "document.uploaded",
    "document.review_required",
    "approval.requested",
    "approval.completed",
)

LEGACY_EVENT_ALIASES = {
    "request_created": "request.created",
    "service_requirement_detected": "trip.service_added",
    "offer_needed": "offer.created",
    "offer_sent": "offer.delivered",
    "offer_accepted": "offer.accepted",
    "booking_ready": "booking.ready",
    "ticket_emd_linked": "ticket.recorded",
    "payment_due": "invoice.due_soon",
    "disruption_reported": "booking.blocked",
    "refund_change_claim_opened": "refund.requested",
    "after_sales_case_opened": "refund.requested",
    "pre_trip_check": "trip.document_required",
}

SUPPORTED_OPERATORS = {
    "equals",
    "not_equals",
    "in",
    "not_in",
    "exists",
    "not_exists",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "before",
    "after",
    "within_minutes",
    "within_hours",
    "within_days",
    "contains",
    "starts_with",
    "ends_with",
}

_ALLOWED_ROOTS = {
    "event",
    "source",
    "request",
    "offer",
    "trip",
    "booking",
    "ticket",
    "emd",
    "invoice",
    "document",
    "communication",
    "work",
}
_ALLOWED_LEAVES = {
    "event_type",
    "event_subtype",
    "event_time",
    "entity_type",
    "entity_id",
    "status",
    "priority",
    "severity",
    "visibility",
    "source",
    "source_type",
    "source_id",
    "expires_at",
    "due_at",
    "deadline",
    "deadline_type",
    "approval_required",
    "approval_status",
    "document_required",
    "missing_information",
    "assigned_user_id",
    "assigned_team_code",
    "queue_code",
    "blocker_status",
    "service_code",
    "service_family",
    "booking_status",
    "offer_status",
    "request_status",
    "trip_status",
    "ticket_status",
    "payment_status",
    "verification_status",
    "direction",
    "channel",
    "created_at",
    "updated_at",
    "title",
    "reference",
}
_SENSITIVE_SEGMENTS = {
    "password",
    "secret",
    "token",
    "credential",
    "authorization",
    "passport",
    "medical",
    "health",
    "supplier_cost",
    "margin",
    "commission",
    "payment_reference",
    "card",
    "email",
    "phone",
    "raw_payload",
    "request_body",
    "internal_notes",
}

ACTION_SAFETY_CLASS = {
    "create_work_item": "A",
    "assign_work_item": "A",
    "update_work_item_priority": "A",
    "set_work_item_deadline": "A",
    "add_work_item_dependency": "A",
    "create_notification_projection": "A",
    "create_internal_timeline_entry": "A",
    "create_internal_note": "A",
    "add_readiness_blocker": "A",
    "clear_resolved_readiness_blocker": "A",
    "place_in_queue": "A",
    "escalate_work_item": "B",
    "reopen_work_item": "B",
    "close_work_item_when_conditions_met": "B",
    "request_document": "B",
    "request_missing_information": "B",
    "create_supplier_follow_up": "B",
    "create_client_follow_up": "B",
    "create_accounting_review": "B",
    "create_policy_review": "B",
    "create_manual_booking_review": "B",
    "create_approval_request": "B",
    "deliver_offer": "C",
    "revise_offer": "C",
    "accept_offer": "C",
    "decline_offer": "C",
    "confirm_trip": "C",
    "cancel_trip": "C",
    "record_booking_result": "C",
    "modify_ticket_emd_truth": "C",
    "issue_invoice": "C",
    "allocate_payment": "C",
    "issue_credit_note": "C",
    "post_refund": "C",
    "confirm_exchange": "C",
    "publish_portal_record": "C",
    "publish_client_document": "C",
    "send_external_communication": "C",
    "change_external_lifecycle_status": "C",
}

PROHIBITED_ACTIONS = {
    "execute_provider",
    "execute_airline",
    "execute_gds",
    "execute_ndc",
    "issue_ticket",
    "issue_emd",
    "execute_payment",
    "execute_refund",
    "delete_record",
    "reassign_tenant",
    "modify_permission",
    "run_code",
    "run_python",
    "run_javascript",
    "autonomous_legal_decision",
    "autonomous_medical_decision",
    "autonomous_safety_decision",
    "fabricate_evidence",
}

TASK_TYPE_CATALOGUE = {
    "qualify_request": ("request", "high", "edit_requests", False, False),
    "request_missing_information": ("request", "high", "edit_requests", False, False),
    "review_passenger_identity": ("request", "high", "edit_passengers", False, False),
    "review_ptc": ("request", "normal", "edit_passengers", False, False),
    "review_service_requirements": ("request", "high", "edit_requests", False, False),
    "prepare_offer": ("offer", "normal", "edit_offers", False, False),
    "review_offer": ("offer", "normal", "edit_offers", False, False),
    "approve_offer_delivery": ("offer", "high", "edit_offers", False, True),
    "deliver_offer": ("offer", "high", "edit_offers", True, True),
    "follow_up_offer": ("offer", "normal", "edit_offers", False, False),
    "review_expiring_offer": ("offer", "high", "edit_offers", False, False),
    "confirm_trip_details": ("trip", "normal", "edit_trips", False, True),
    "collect_documents": ("trip", "high", "edit_documents", False, False),
    "review_special_service": ("trip", "high", "edit_tickets_emds", False, False),
    "review_pet_request": ("trip", "high", "edit_tickets_emds", False, False),
    "review_special_item": ("trip", "normal", "edit_tickets_emds", False, False),
    "prepare_client_documents": ("trip", "normal", "edit_documents", False, False),
    "prepare_booking": ("booking", "high", "edit_bookings", False, False),
    "verify_passenger_data": ("booking", "high", "edit_passengers", False, False),
    "verify_fare": ("booking", "high", "edit_bookings", False, False),
    "verify_services": ("booking", "high", "edit_tickets_emds", False, False),
    "verify_documents": ("booking", "high", "edit_documents", False, False),
    "approve_booking_result": ("booking", "high", "edit_bookings", False, True),
    "record_booking_result": ("booking", "high", "edit_bookings", True, True),
    "resolve_booking_failure": ("booking", "urgent", "edit_bookings", False, False),
    "record_ticket": ("ticket", "high", "edit_tickets_emds", True, True),
    "verify_coupon_status": ("ticket", "high", "edit_tickets_emds", False, False),
    "review_emd_requirement": ("emd", "high", "edit_tickets_emds", False, False),
    "record_emd": ("emd", "high", "edit_tickets_emds", True, True),
    "verify_ticketing_deadline": ("ticket", "urgent", "edit_tickets_emds", False, False),
    "review_invoice_issue": ("invoice", "high", "edit_commercial_ledger", False, True),
    "allocate_payment": ("payment", "high", "edit_commercial_ledger", True, True),
    "investigate_unallocated_payment": ("payment", "high", "edit_commercial_ledger", False, False),
    "confirm_supplier_cost": ("supplier_cost", "high", "edit_commercial_ledger", False, True),
    "review_low_margin": ("invoice", "high", "view_margins", False, True),
    "review_credit_note": ("credit_note", "high", "edit_commercial_ledger", False, True),
    "review_refund": ("refund", "high", "edit_finance", False, True),
    "review_exchange": ("exchange", "high", "edit_finance", False, True),
    "respond_to_client": ("communication", "normal", "edit_tasks", True, True),
    "respond_to_passenger": ("communication", "normal", "edit_tasks", True, True),
    "respond_to_supplier": ("communication", "high", "edit_tasks", True, True),
    "review_uploaded_document": ("document", "normal", "edit_documents", False, False),
    "complete_approval": ("approval", "high", "edit_tasks", False, True),
}


class GovernedAutomationContractError(ValueError):
    pass


def canonical_event_type(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace(" ", "_")
    return LEGACY_EVENT_ALIASES.get(normalized, normalized)


def action_safety_class(action_type: str) -> str:
    if action_type in PROHIBITED_ACTIONS:
        return "D"
    safety_class = ACTION_SAFETY_CLASS.get(action_type)
    if not safety_class:
        raise GovernedAutomationContractError(
            f"Unknown automation action is not allowlisted: {action_type}."
        )
    return safety_class


def validate_rule_contract(rule: dict[str, Any]) -> dict[str, Any]:
    events = rule.get("trigger_event_types") or (
        [rule.get("trigger_event")] if rule.get("trigger_event") else []
    )
    normalized_events = [canonical_event_type(item) for item in events]
    if not normalized_events:
        raise GovernedAutomationContractError(
            "At least one canonical trigger event type is required."
        )
    unknown_events = sorted(set(normalized_events) - set(CANONICAL_AUTOMATION_EVENTS))
    if unknown_events:
        raise GovernedAutomationContractError(
            f"Unknown canonical trigger event type: {', '.join(unknown_events)}."
        )
    validate_conditions(rule.get("conditions_json") or {})
    actions = normalized_actions(rule)
    if len(actions) > MAX_ACTIONS_PER_RULE:
        raise GovernedAutomationContractError(
            f"Rules may contain at most {MAX_ACTIONS_PER_RULE} actions."
        )
    declared = str(rule.get("execution_safety_class") or "A").upper()
    if declared not in {"A", "B", "C"}:
        raise GovernedAutomationContractError(
            "Rule execution_safety_class must be A, B, or C."
        )
    ranks = {"A": 1, "B": 2, "C": 3, "D": 4}
    for action in actions:
        actual = action_safety_class(action["action_type"])
        if actual == "D":
            raise GovernedAutomationContractError(
                f"Class D action is prohibited: {action['action_type']}."
            )
        if ranks[declared] < ranks[actual]:
            raise GovernedAutomationContractError(
                f"Rule safety class {declared} cannot lower action "
                f"{action['action_type']} from class {actual}."
            )
        if _contains_forbidden_payload_key(action.get("parameters") or {}):
            raise GovernedAutomationContractError(
                f"Action {action['action_type']} contains a forbidden tenant, "
                "permission, executable, credential, or external-delivery field."
            )
    rule["trigger_event_types"] = normalized_events
    rule["trigger_event"] = normalized_events[0]
    rule["actions"] = actions
    return rule


def normalized_actions(rule: dict[str, Any]) -> list[dict[str, Any]]:
    raw_actions = list(rule.get("actions") or [])
    template_code = rule.get("generated_template_code")
    if not raw_actions and template_code:
        raw_actions = [
            {
                "action_type": "create_work_item",
                "parameters": {"template_code": template_code},
            }
        ]
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(raw_actions):
        if not isinstance(item, dict):
            raise GovernedAutomationContractError(
                f"Action at index {index} must be an object."
            )
        unexpected = set(item) - {"action_type", "action", "parameters", "safety_class"}
        if unexpected:
            raise GovernedAutomationContractError(
                f"Action at index {index} contains unknown fields: "
                f"{', '.join(sorted(unexpected))}."
            )
        action_type = str(item.get("action_type") or item.get("action") or "").strip()
        if not action_type:
            raise GovernedAutomationContractError(
                f"Action at index {index} is missing action_type."
            )
        safety_class = action_safety_class(action_type)
        if safety_class == "D":
            raise GovernedAutomationContractError(
                f"Class D action is prohibited: {action_type}."
            )
        parameters = item.get("parameters") or {}
        if not isinstance(parameters, dict):
            raise GovernedAutomationContractError(
                f"Action {action_type} parameters must be an object."
            )
        normalized.append(
            {
                "action_type": action_type,
                "parameters": bounded_safe_snapshot(parameters, max_depth=4),
                "safety_class": safety_class,
            }
        )
    return normalized


def validate_conditions(node: Any, *, depth: int = 0, path: str = "conditions") -> None:
    if node in ({}, None):
        return
    if depth > MAX_CONDITION_DEPTH:
        raise GovernedAutomationContractError(
            f"Condition nesting exceeds {MAX_CONDITION_DEPTH} levels at {path}."
        )
    if not isinstance(node, dict):
        raise GovernedAutomationContractError(f"Condition node at {path} must be an object.")
    logical_keys = [key for key in ("all", "any", "not") if key in node]
    if logical_keys:
        if len(logical_keys) != 1 or len(node) != 1:
            raise GovernedAutomationContractError(
                f"Condition group at {path} must contain exactly one of all, any, or not."
            )
        key = logical_keys[0]
        children = node[key]
        if key == "not":
            children = [children]
        if not isinstance(children, list):
            raise GovernedAutomationContractError(
                f"Condition group {path}.{key} must be a list."
            )
        if not children or len(children) > MAX_CONDITIONS_PER_GROUP:
            raise GovernedAutomationContractError(
                f"Condition group {path}.{key} must contain 1 to "
                f"{MAX_CONDITIONS_PER_GROUP} items."
            )
        for index, child in enumerate(children):
            validate_conditions(child, depth=depth + 1, path=f"{path}.{key}[{index}]")
        return

    unexpected = set(node) - {"field", "operator", "value"}
    if unexpected:
        raise GovernedAutomationContractError(
            f"Condition at {path} contains unknown fields: {', '.join(sorted(unexpected))}."
        )
    field = str(node.get("field") or "")
    operator = str(node.get("operator") or "")
    _validate_field_path(field)
    if operator not in SUPPORTED_OPERATORS:
        raise GovernedAutomationContractError(f"Unknown condition operator: {operator}.")
    value = node.get("value")
    if isinstance(value, list) and len(value) > MAX_LIST_VALUES:
        raise GovernedAutomationContractError(
            f"Condition list at {path} exceeds {MAX_LIST_VALUES} values."
        )
    if isinstance(value, (dict, tuple, set)):
        raise GovernedAutomationContractError(
            f"Condition value at {path} must be a scalar or bounded list."
        )


def evaluate_conditions(
    conditions: dict[str, Any],
    context: dict[str, Any],
    *,
    evaluation_time: datetime | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    validate_conditions(conditions)
    trace: list[dict[str, Any]] = []
    anchor = evaluation_time or _parse_datetime(
        ((context.get("event") or {}).get("event_time"))
    ) or datetime.now(timezone.utc)

    def evaluate(node: dict[str, Any], path: str) -> bool:
        if not node:
            trace.append(
                {
                    "condition_path": path,
                    "operator": "always",
                    "expected_value": True,
                    "evaluated_value": True,
                    "matched": True,
                }
            )
            return True
        if "all" in node:
            results = [
                evaluate(child, f"{path}.all[{index}]")
                for index, child in enumerate(node["all"])
            ]
            return all(results)
        if "any" in node:
            results = [
                evaluate(child, f"{path}.any[{index}]")
                for index, child in enumerate(node["any"])
            ]
            return any(results)
        if "not" in node:
            children = node["not"]
            if not isinstance(children, list):
                children = [children]
            results = [
                evaluate(child, f"{path}.not[{index}]")
                for index, child in enumerate(children)
            ]
            return not all(results)
        field = node["field"]
        operator = node["operator"]
        expected = node.get("value")
        exists, actual = _read_field(context, field)
        matched = _compare(
            operator,
            actual,
            expected,
            exists=exists,
            evaluation_time=anchor,
        )
        trace.append(
            {
                "condition_path": path,
                "field": field,
                "operator": operator,
                "expected_value": safe_trace_value(field, expected),
                "evaluated_value": safe_trace_value(field, actual)
                if exists
                else None,
                "matched": matched,
                "skipped_reason": None if exists or operator in {"not_exists"} else "field_missing",
            }
        )
        return matched

    return evaluate(conditions or {}, "conditions"), trace[:MAX_TRACE_ITEMS]


def safe_trace_value(field: str, value: Any) -> Any:
    if any(segment in field.lower() for segment in _SENSITIVE_SEGMENTS):
        return "[REDACTED]"
    return bounded_safe_snapshot(value, max_depth=2)


def bounded_safe_snapshot(
    value: Any,
    *,
    max_depth: int = 4,
    _depth: int = 0,
) -> Any:
    if _depth >= max_depth:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key in sorted(value)[:MAX_LIST_VALUES]:
            lowered = str(key).lower()
            if any(segment in lowered for segment in _SENSITIVE_SEGMENTS):
                output[str(key)] = "[REDACTED]"
            else:
                output[str(key)] = bounded_safe_snapshot(
                    value[key], max_depth=max_depth, _depth=_depth + 1
                )
        return output
    if isinstance(value, (list, tuple)):
        return [
            bounded_safe_snapshot(item, max_depth=max_depth, _depth=_depth + 1)
            for item in list(value)[:MAX_LIST_VALUES]
        ]
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str):
        return value[:MAX_TRACE_TEXT]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:MAX_TRACE_TEXT]


def task_type_contract(task_type: str) -> dict[str, Any]:
    record = TASK_TYPE_CATALOGUE.get(task_type)
    if not record:
        return {
            "task_type": task_type,
            "applicable_entity_types": [],
            "default_priority": "normal",
            "required_permission": "edit_tasks",
            "external_action_required": False,
            "human_confirmation_required": False,
            "timeline_event_on_completion": "task.completed",
            "portal_visibility": "internal_only",
            "finance_visibility": "permission_filtered",
        }
    entity_type, priority, permission, external, confirmation = record
    return {
        "task_type": task_type,
        "applicable_entity_types": [entity_type],
        "default_priority": priority,
        "required_permission": permission,
        "external_action_required": external,
        "human_confirmation_required": confirmation,
        "timeline_event_on_completion": "task.completed",
        "portal_visibility": "internal_only",
        "finance_visibility": "permission_filtered",
    }


def _validate_field_path(field: str) -> None:
    parts = field.split(".")
    if len(parts) != 2 or parts[0] not in _ALLOWED_ROOTS or parts[1] not in _ALLOWED_LEAVES:
        raise GovernedAutomationContractError(
            f"Condition field path is not allowlisted: {field or '[missing]'}."
        )
    if any(segment in field.lower() for segment in _SENSITIVE_SEGMENTS):
        raise GovernedAutomationContractError(
            f"Condition field path is restricted: {field}."
        )


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(segment in lowered for segment in _SENSITIVE_SEGMENTS):
                return True
            if lowered in {
                "agency_id",
                "workspace_id",
                "permission",
                "permissions",
                "role",
                "roles",
                "code",
                "python",
                "javascript",
                "expression",
                "eval",
                "credential",
                "credentials",
                "secret",
                "token",
                "authorization",
                "external_delivery",
                "provider_execution",
            }:
                return True
            if _contains_forbidden_payload_key(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_payload_key(item) for item in value)
    return False


def _read_field(context: dict[str, Any], field: str) -> tuple[bool, Any]:
    value: Any = context
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


def _compare(
    operator: str,
    actual: Any,
    expected: Any,
    *,
    exists: bool,
    evaluation_time: datetime,
) -> bool:
    if operator == "exists":
        return exists
    if operator == "not_exists":
        return not exists
    if not exists:
        return False
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "in":
        return isinstance(expected, list) and actual in expected
    if operator == "not_in":
        return isinstance(expected, list) and actual not in expected
    if operator in {
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
    }:
        try:
            if operator == "greater_than":
                return actual > expected
            if operator == "greater_than_or_equal":
                return actual >= expected
            if operator == "less_than":
                return actual < expected
            return actual <= expected
        except TypeError:
            return False
    if operator in {"before", "after"}:
        actual_dt = _parse_datetime(actual)
        expected_dt = _parse_datetime(expected)
        if not actual_dt or not expected_dt:
            return False
        return actual_dt < expected_dt if operator == "before" else actual_dt > expected_dt
    if operator in {"within_minutes", "within_hours", "within_days"}:
        actual_dt = _parse_datetime(actual)
        if not actual_dt or not isinstance(expected, (int, float)) or expected < 0:
            return False
        factor = {
            "within_minutes": timedelta(minutes=float(expected)),
            "within_hours": timedelta(hours=float(expected)),
            "within_days": timedelta(days=float(expected)),
        }[operator]
        return evaluation_time <= actual_dt <= evaluation_time + factor
    if operator == "contains":
        if isinstance(actual, (str, list, tuple)):
            return expected in actual
        return False
    if operator == "starts_with":
        return isinstance(actual, str) and isinstance(expected, str) and actual.startswith(expected)
    if operator == "ends_with":
        return isinstance(actual, str) and isinstance(expected, str) and actual.endswith(expected)
    return False


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
