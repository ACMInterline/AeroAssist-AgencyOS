#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE  # noqa: E402
from canonical_domain_ownership import DOMAIN_OWNERSHIP_BY_KEY  # noqa: E402
from models import (  # noqa: E402
    NotificationProjection,
    OperationalDeadline,
    OperationalSlaPolicy,
    OperationalTaskAutomationRule,
    OperationalTaskAutomationRun,
    OperationalWorkItem,
)
from phase_assertions import assert_application_phase_at_least  # noqa: E402
from services.agent_work_queue_service import WORK_ITEM_STATUSES  # noqa: E402
from services.governed_automation_contract import (  # noqa: E402
    ACTION_SAFETY_CLASS,
    CANONICAL_AUTOMATION_EVENTS,
    PROHIBITED_ACTIONS,
    SUPPORTED_OPERATORS,
    TASK_TYPE_CATALOGUE,
)
from services.task_automation_dependency_service import (  # noqa: E402
    TASK_AUTOMATION_RULE_STATUSES,
    TASK_DEPENDENCY_TYPES,
)


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
CHECKS = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(f"{name}: {detail or 'condition was false'}")


def text(path: str) -> str:
    target = ROOT / path
    check(f"{path}_exists", target.is_file(), str(target))
    return target.read_text(encoding="utf-8")


def require_markers(path: str, markers: tuple[str, ...]) -> str:
    value = text(path)
    missing = [marker for marker in markers if marker not in value]
    check(f"{path}_markers", not missing, str(missing))
    return value


def assert_no_executable_rule_calls(path: str) -> None:
    source = text(path)
    tree = ast.parse(source, filename=path)
    prohibited = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in {
            "eval",
            "exec",
            "compile",
            "__import__",
        }:
            prohibited.append((node.func.id, node.lineno))
    check(f"{path}_no_executable_calls", not prohibited, str(prohibited))
    check(f"{path}_no_dynamic_import", "importlib" not in source, "importlib")


def main() -> int:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="canonical build phase",
    )

    owner = DOMAIN_OWNERSHIP_BY_KEY["task_work_item"]
    check(
        "operational_work_item_is_sole_owner",
        owner["canonical_model"] == "OperationalWorkItem"
        and owner["canonical_collection"] == "operational_work_items"
        and owner["current_write_owners"]
        == ("backend/services/agent_work_queue_service.py",),
        str(owner),
    )
    check(
        "legacy_request_tasks_are_projection_only",
        any(
            artifact["name"] == "request_tasks"
            and artifact["classification"] == "compatibility_projection"
            for artifact in owner["artifacts"]
        ),
        str(owner["artifacts"]),
    )

    check(
        "work_item_status_contract",
        set(WORK_ITEM_STATUSES)
        == {
            "open",
            "assigned",
            "in_progress",
            "waiting",
            "blocked",
            "approval_required",
            "completed",
            "cancelled",
            "overdue",
        },
        str(WORK_ITEM_STATUSES),
    )
    check(
        "rule_lifecycle_contract",
        TASK_AUTOMATION_RULE_STATUSES
        == ["draft", "active", "inactive", "superseded", "archived"],
        str(TASK_AUTOMATION_RULE_STATUSES),
    )
    check(
        "dependency_contract",
        {"mandatory", "advisory"}.issubset(TASK_DEPENDENCY_TYPES),
        str(TASK_DEPENDENCY_TYPES),
    )
    check(
        "condition_operator_contract",
        {
            "equals",
            "not_equals",
            "in",
            "not_in",
            "exists",
            "not_exists",
            "within_minutes",
            "within_hours",
            "within_days",
        }.issubset(SUPPORTED_OPERATORS),
        str(sorted(SUPPORTED_OPERATORS)),
    )
    check(
        "event_catalogue_contract",
        {
            "request.created",
            "offer.delivered",
            "offer.accepted",
            "booking.ready",
            "ticket.deadline_approaching",
            "payment.unallocated",
            "document.uploaded",
            "approval.requested",
        }.issubset(CANONICAL_AUTOMATION_EVENTS),
        str(CANONICAL_AUTOMATION_EVENTS),
    )
    check(
        "action_safety_contract",
        ACTION_SAFETY_CLASS["create_work_item"] == "A"
        and ACTION_SAFETY_CLASS["escalate_work_item"] == "B"
        and ACTION_SAFETY_CLASS["issue_invoice"] == "C"
        and {"issue_ticket", "execute_payment", "modify_permission"}.issubset(
            PROHIBITED_ACTIONS
        ),
        str(ACTION_SAFETY_CLASS),
    )
    check(
        "task_type_catalogue_contract",
        {
            "qualify_request",
            "prepare_offer",
            "prepare_booking",
            "record_ticket",
            "review_invoice_issue",
            "respond_to_client",
        }.issubset(TASK_TYPE_CATALOGUE),
        str(sorted(TASK_TYPE_CATALOGUE)),
    )

    work_fields = OperationalWorkItem.model_fields
    check(
        "work_item_lineage_fields",
        {
            "agency_id",
            "source_timeline_entry_id",
            "source_automation_rule_id",
            "source_automation_execution_id",
            "entity_references",
            "dependency_ids",
            "blockers",
            "completion_evidence",
            "version",
        }.issubset(work_fields),
        str(sorted(work_fields)),
    )
    rule_fields = OperationalTaskAutomationRule.model_fields
    check(
        "versioned_rule_fields",
        {
            "agency_id",
            "platform_scope",
            "rule_key",
            "status",
            "version",
            "conditions_json",
            "actions",
            "published_at",
            "published_by",
            "superseded_at",
            "superseded_by_rule_id",
        }.issubset(rule_fields),
        str(sorted(rule_fields)),
    )
    run_fields = OperationalTaskAutomationRun.model_fields
    check(
        "execution_evidence_fields",
        {
            "source_timeline_entry_id",
            "rules_matched",
            "evaluation_trace",
            "actions_attempted",
            "actions_completed",
            "actions_skipped",
            "tasks_created",
            "approvals_created",
            "duration_ms",
            "idempotency_key",
            "locked_until",
        }.issubset(run_fields),
        str(sorted(run_fields)),
    )
    check(
        "deadline_policy_version_fields",
        {"policy_version", "original_due_at", "override_history", "version"}.issubset(
            OperationalDeadline.model_fields
        )
        and {"version", "duration_unit", "calendar_id"}.issubset(
            OperationalSlaPolicy.model_fields
        ),
        str(sorted(OperationalDeadline.model_fields)),
    )
    check(
        "user_specific_notification_field",
        "recipient_user_id" in NotificationProjection.model_fields,
        str(sorted(NotificationProjection.model_fields)),
    )

    assert_no_executable_rule_calls(
        "backend/services/governed_automation_contract.py"
    )
    assert_no_executable_rule_calls(
        "backend/services/task_automation_dependency_service.py"
    )

    automation_service = text(
        "backend/services/task_automation_dependency_service.py"
    )
    check(
        "automation_uses_canonical_work_owner",
        'collection("operational_work_items")' in automation_service
        and 'collection("request_tasks").insert_one' not in automation_service
        and 'collection("request_tasks").update_one' not in automation_service,
    )
    request_router = require_markers(
        "backend/routers/requests.py",
        (
            '"canonical_collection": "operational_work_items"',
            '"compatibility_route": "request_tasks"',
            "AgentWorkQueueService",
        ),
    )
    check(
        "request_compatibility_has_no_legacy_write",
        'collection("request_tasks").insert_one' not in request_router
        and 'collection("request_tasks").update_one' not in request_router,
    )

    for path in (
        "backend/routers/agency_agent_work_queues.py",
        "backend/routers/agency_task_automation.py",
        "backend/routers/agency_operational_sla_deadlines.py",
    ):
        require_markers(
            path,
            (
                "assert_agency_access",
                "require_any_agency_role",
                "Depends(get_current_user)",
            ),
        )
    for path in (
        "backend/routers/platform_agent_work_queues.py",
        "backend/routers/platform_task_automation.py",
        "backend/routers/platform_operational_sla_deadlines.py",
    ):
        require_markers(
            path,
            (
                "agency_action_required",
                "HTTP_409_CONFLICT",
                "require_any_platform_role",
            ),
        )

    require_markers(
        "backend/server.py",
        (
            '"governed_automation_orchestration"',
            '"canonical_operational_work_item_owner": True',
            '"persistent_scheduler_enabled": False',
            '"class_c_approval_projection_only": True',
            '"class_d_actions_rejected": True',
        ),
    )
    require_markers(
        "backend/database.py",
        (
            "operational_notification_projections_agency_recipient_lookup",
            "operational_task_automation_rules",
            "operational_task_automation_runs",
        ),
    )

    analyzer = require_markers(
        "backend/scripts/analyze_governed_automation_migration.py",
        (
            '"--write"',
            "permanently dry-run only",
            "counts_unchanged",
        ),
    )
    check(
        "migration_entrypoint_has_no_write_call",
        not any(
            marker in analyzer
            for marker in (
                ".insert_one(",
                ".update_one(",
                ".delete_one(",
                ".delete_many(",
                ".upsert_one(",
            )
        ),
    )

    require_markers(
        "frontend/src/components/OperationalWorkPanel.jsx",
        (
            "ProductTable",
            "Work and deadlines",
            "Advanced automation explanation",
            "Next safe action",
        ),
    )
    require_markers(
        "frontend/src/components/WorkflowContinuityPanel.jsx",
        ("OperationalWorkPanel", "workEntityId", "workEntityType"),
    )
    for page in (
        "RequestDetailPage.jsx",
        "OfferWorkspaceDetailPage.jsx",
        "TripDetailPage.jsx",
        "BookingWorkspaceDetailPage.jsx",
        "TicketDetailPage.jsx",
        "EmdDetailPage.jsx",
        "InvoiceDetailPage.jsx",
        "AfterSalesPage.jsx",
        "ClientDetailPage.jsx",
        "PassengerDetailPage.jsx",
        "DocumentWorkspacesPage.jsx",
    ):
        require_markers(
            f"frontend/src/pages/agency/{page}",
            ("WorkflowContinuityPanel", "workEntityId", "workEntityType"),
        )
    require_markers(
        "frontend/src/pages/agency/TaskAutomationPage.jsx",
        (
            "ProductTable",
            "Automation rule versions",
            "Automation execution history",
            "Advanced catalogue and operational metrics",
        ),
    )

    required_docs = {
        "docs/architecture/canonical-automation-orchestration-contract.md": (
            "OperationalTimeline",
            "persistent scheduler",
        ),
        "docs/architecture/operational-work-item-contract.md": (
            "sole task truth",
            "request_tasks",
        ),
        "docs/architecture/automation-rule-and-safety-contract.md": (
            "Class A",
            "Class D",
        ),
        "docs/architecture/sla-and-deadline-contract.md": (
            "business days",
            "historical",
        ),
        "docs/architecture/assignment-and-queue-contract.md": (
            "AgencyStaffMembership",
            "deterministic",
        ),
        "docs/architecture/approval-routing-contract.md": (
            "Class C",
            "underlying commercial",
        ),
        "docs/architecture/automation-event-catalog.md": (
            "request.created",
            "exact timeline entry",
        ),
        "docs/architecture/automation-compatibility-and-migration.md": (
            "dry-run",
            "Persistent scheduler",
        ),
    }
    for path, markers in required_docs.items():
        require_markers(path, markers)

    print(f"Governed automation contract smoke passed: {CHECKS} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
