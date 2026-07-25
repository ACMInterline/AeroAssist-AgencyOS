#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable


BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Database
from build_phase import CURRENT_BUILD_PHASE
from phase_assertions import assert_application_phase_at_least
from services.agent_work_queue_service import (
    AgentWorkQueueError,
    AgentWorkQueueService,
    WORK_ITEM_STATUSES,
)
from services.governed_automation_contract import (
    GovernedAutomationContractError,
    action_safety_class,
    evaluate_conditions,
    validate_rule_contract,
)
from services.operational_collaboration_service import (
    OperationalCollaborationError,
    OperationalCollaborationService,
)
from services.operational_sla_deadline_service import (
    OperationalSlaDeadlineService,
)
from services.task_automation_dependency_service import (
    MAX_PROCESS_BATCH,
    TaskAutomationDependencyError,
    TaskAutomationDependencyService,
)


AGENCY_A = "agency-governed-a"
AGENCY_B = "agency-governed-b"
MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
OWNER = {"id": "owner-a", "identity_id": "identity-owner-a"}
APPROVER = {"id": "approver-a", "identity_id": "identity-approver-a"}
AGENT_A = {"id": "agent-a", "identity_id": "identity-agent-a"}
AGENT_B = {"id": "agent-b", "identity_id": "identity-agent-b"}
REVOKED = {"id": "revoked-a", "identity_id": "identity-revoked-a"}

CHECKS: list[str] = []


def check(name: str, condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    CHECKS.append(name)


async def expect_error(
    name: str,
    operation: Callable[[], Awaitable[Any]],
    exception_types: tuple[type[BaseException], ...],
    text: str,
) -> None:
    try:
        await operation()
    except exception_types as exc:
        check(name, text.lower() in str(exc).lower(), str(exc))
        return
    raise AssertionError(f"{name}: expected {exception_types}")


async def seed_membership(
    db: Database,
    agency_id: str,
    user_id: str,
    role: str,
    status: str = "active",
) -> None:
    await db.collection("agency_staff_memberships").insert_one(
        {
            "id": f"membership-{agency_id}-{user_id}",
            "agency_id": agency_id,
            "user_id": user_id,
            "identity_id": f"identity-{user_id}",
            "agency_role": role,
            "status": status,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )


async def timeline_event(
    collaboration: OperationalCollaborationService,
    agency_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    suffix: str,
) -> dict[str, Any]:
    return await collaboration.record_business_event(
        agency_id=agency_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        summary=f"Governed automation smoke {event_type}.",
        actor=OWNER,
        visibility="internal",
        details={"source_label": entity_id},
        idempotency_key=f"smoke:{event_type}:{entity_id}:{suffix}",
        event_source="governed_automation_smoke",
    )


def rule_payload(
    *,
    agency_id: str,
    key: str,
    event_type: str,
    entity_type: str,
    action_type: str,
    safety_class: str,
    parameters: dict[str, Any] | None = None,
    conditions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "agency_id": agency_id,
        "rule_key": key,
        "name": key.replace("_", " ").title(),
        "description": "Disposable governed automation smoke rule.",
        "trigger_event_types": [event_type],
        "trigger_entity_types": [entity_type],
        "conditions_json": conditions
        or {
            "all": [
                {
                    "field": "event.event_type",
                    "operator": "equals",
                    "value": event_type,
                }
            ]
        },
        "actions": [
            {
                "action_type": action_type,
                "parameters": parameters or {},
            }
        ],
        "priority": 10,
        "execution_safety_class": safety_class,
        "dry_run_supported": True,
    }


async def create_manual_item(
    queue: AgentWorkQueueService,
    source_id: str,
    actor: dict[str, Any] = OWNER,
    *,
    agency_id: str = AGENCY_A,
) -> dict[str, Any]:
    result = await queue.create_work_item(
        {
            "agency_id": agency_id,
            "work_item_type": "manual",
            "source_entity_type": "request",
            "source_entity_id": source_id,
            "title": f"Review {source_id}",
            "summary": "Disposable canonical operational work.",
            "status": "open",
            "priority": "normal",
            "severity": "medium",
            "queue_code": "unassigned",
            "blocker_status": "not_blocked",
        },
        actor,
        agency_id=agency_id,
    )
    return result["work_item"]


async def verify_rule_contract(
    db: Database,
    automation: TaskAutomationDependencyService,
    collaboration: OperationalCollaborationService,
) -> tuple[dict[str, Any], dict[str, Any]]:
    draft = (
        await automation.create_rule(
            rule_payload(
                agency_id=AGENCY_A,
                key="request_qualification",
                event_type="request.created",
                entity_type="request",
                action_type="create_work_item",
                safety_class="A",
                parameters={
                    "task_type": "qualify_request",
                    "title": "Qualify new request",
                    "queue_code": "unassigned",
                },
            ),
            OWNER,
        )
    )["rule"]
    check("draft_rule_created", draft["status"] == "draft", str(draft))
    check("draft_rule_disabled", draft["enabled"] is False, str(draft))

    draft_event = await timeline_event(
        collaboration,
        AGENCY_A,
        "request.created",
        "request",
        "request-draft",
        "draft",
    )
    draft_run = await automation.run_automation(
        {
            "agency_id": AGENCY_A,
            "trigger_event": "request.created",
            "source_entity_type": "request",
            "source_entity_id": "request-draft",
            "source_timeline_entry_id": draft_event["id"],
            "event_snapshot_json": {"request": {"status": "new"}},
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    check(
        "draft_rule_does_not_execute",
        not draft_run["run"].get("actions_completed"),
        str(draft_run),
    )

    published = (
        await automation.publish_rule(
            draft["id"],
            {"reason": "Focused smoke publication."},
            OWNER,
            agency_id=AGENCY_A,
        )
    )["rule"]
    check(
        "published_rule_active",
        published["status"] == "active" and published["enabled"],
        str(published),
    )

    duplicate = (
        await automation.create_rule(
            rule_payload(
                agency_id=AGENCY_A,
                key="request_qualification",
                event_type="request.created",
                entity_type="request",
                action_type="create_work_item",
                safety_class="A",
                parameters={"task_type": "qualify_request"},
            ),
            OWNER,
        )
    )["rule"]
    await expect_error(
        "duplicate_active_rule_key_rejected",
        lambda: automation.publish_rule(
            duplicate["id"],
            {"reason": "Must not create a second active key."},
            OWNER,
            agency_id=AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "active published rule",
    )

    active_event = await timeline_event(
        collaboration,
        AGENCY_A,
        "request.created",
        "request",
        "request-active",
        "active",
    )
    run_payload = {
        "agency_id": AGENCY_A,
        "trigger_event": "request.created",
        "source_entity_type": "request",
        "source_entity_id": "request-active",
        "source_timeline_entry_id": active_event["id"],
        "event_snapshot_json": {
            "request": {"status": "new", "password": "must-redact"}
        },
    }
    first = await automation.run_automation(
        run_payload, OWNER, agency_id=AGENCY_A
    )
    replay = await automation.run_automation(
        run_payload, OWNER, agency_id=AGENCY_A
    )
    check(
        "class_a_action_created_work",
        len(first["run"].get("tasks_created") or []) == 1,
        str(first),
    )
    check(
        "event_replay_idempotent",
        replay.get("idempotent_reused") is True
        and replay["run"]["id"] == first["run"]["id"],
        str(replay),
    )
    work_id = first["run"]["tasks_created"][0]["task_id"]
    work = await db.collection("operational_work_items").find_one({"id": work_id})
    check(
        "work_has_exact_timeline_lineage",
        work
        and work.get("source_timeline_entry_id") == active_event["id"]
        and work.get("source_automation_rule_id") == published["id"]
        and work.get("source_automation_execution_id") == first["run"]["id"],
        str(work),
    )
    check(
        "execution_trace_redacts_secret",
        "must-redact" not in str(first["run"]),
        str(first["run"]),
    )

    dry_one = await automation.dry_run_rule(
        published["id"],
        {"source_timeline_entry_id": active_event["id"]},
        OWNER,
        agency_id=AGENCY_A,
    )
    dry_two = await automation.dry_run_rule(
        published["id"],
        {"source_timeline_entry_id": active_event["id"]},
        OWNER,
        agency_id=AGENCY_A,
    )
    check(
        "evaluation_trace_deterministic",
        dry_one["evaluation_trace"] == dry_two["evaluation_trace"],
        f"{dry_one} != {dry_two}",
    )
    check(
        "dry_run_zero_writes",
        dry_one["writes_performed"] == 0 and dry_one["dry_run"],
        str(dry_one),
    )

    version_two = (
        await automation.update_rule(
            published["id"],
            {
                "description": "Material version two.",
                "expected_version": published["version"],
            },
            OWNER,
            agency_id=AGENCY_A,
        )
    )["rule"]
    check(
        "material_change_creates_version",
        version_two["version"] > published["version"]
        and version_two["status"] == "draft",
        str(version_two),
    )
    superseded = await automation.supersede_rule(
        version_two["id"],
        {"reason": "Publish reviewed replacement."},
        OWNER,
        agency_id=AGENCY_A,
    )
    predecessor = await db.collection(
        "operational_task_automation_rules"
    ).find_one({"id": published["id"]})
    check(
        "superseded_history_preserved",
        predecessor
        and predecessor["status"] == "superseded"
        and predecessor["superseded_by_rule_id"] == version_two["id"],
        str(predecessor),
    )
    check(
        "replacement_is_only_active_version",
        superseded["rule"]["status"] == "active",
        str(superseded),
    )
    await automation.deactivate_rule(
        version_two["id"],
        {"reason": "Prove inactive versions do not execute."},
        OWNER,
        agency_id=AGENCY_A,
    )
    inactive_event = await timeline_event(
        collaboration,
        AGENCY_A,
        "request.created",
        "request",
        "request-inactive",
        "inactive",
    )
    inactive_run = await automation.run_automation(
        {
            "agency_id": AGENCY_A,
            "trigger_event": "request.created",
            "source_entity_type": "request",
            "source_entity_id": "request-inactive",
            "source_timeline_entry_id": inactive_event["id"],
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    check(
        "inactive_rule_does_not_execute",
        not inactive_run["run"].get("actions_completed"),
        str(inactive_run),
    )

    await expect_error(
        "rule_scope_immutable",
        lambda: automation.update_rule(
            version_two["id"],
            {"agency_id": AGENCY_B, "name": "Unsafe scope change"},
            OWNER,
            agency_id=AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "scope",
    )
    for name, payload, expected in [
        (
            "unknown_field_rejected",
            rule_payload(
                agency_id=AGENCY_A,
                key="bad_field",
                event_type="request.created",
                entity_type="request",
                action_type="create_work_item",
                safety_class="A",
                conditions={
                    "field": "request.supplier_cost",
                    "operator": "equals",
                    "value": 1,
                },
            ),
            "field",
        ),
        (
            "unknown_operator_rejected",
            rule_payload(
                agency_id=AGENCY_A,
                key="bad_operator",
                event_type="request.created",
                entity_type="request",
                action_type="create_work_item",
                safety_class="A",
                conditions={
                    "field": "request.status",
                    "operator": "matches_regex",
                    "value": ".*",
                },
            ),
            "operator",
        ),
        (
            "class_d_action_rejected",
            rule_payload(
                agency_id=AGENCY_A,
                key="class_d",
                event_type="request.created",
                entity_type="request",
                action_type="execute_payment",
                safety_class="C",
            ),
            "class d",
        ),
        (
            "safety_class_cannot_be_lowered",
            rule_payload(
                agency_id=AGENCY_A,
                key="lowered_class",
                event_type="offer.delivered",
                entity_type="offer",
                action_type="send_external_communication",
                safety_class="A",
            ),
            "cannot lower",
        ),
    ]:
        await expect_error(
            name,
            lambda payload=payload: automation.create_rule(payload, OWNER),
            (TaskAutomationDependencyError,),
            expected,
        )

    await expect_error(
        "arbitrary_expression_rejected",
        lambda: automation.create_rule(
            {
                **rule_payload(
                    agency_id=AGENCY_A,
                    key="bad_expression",
                    event_type="request.created",
                    entity_type="request",
                    action_type="create_work_item",
                    safety_class="A",
                ),
                "conditions_json": {"expression": "__import__('os')"},
            },
            OWNER,
        ),
        (TaskAutomationDependencyError,),
        "unknown fields",
    )
    check(
        "class_d_catalogue_rejects_directly",
        action_safety_class("execute_provider") == "D",
        "execute_provider was not classified D",
    )
    return first["run"], work


async def verify_class_c_and_approvals(
    db: Database,
    automation: TaskAutomationDependencyService,
    collaboration: OperationalCollaborationService,
) -> None:
    class_c_rule = (
        await automation.create_rule(
            rule_payload(
                agency_id=AGENCY_A,
                key="external_message_approval",
                event_type="offer.delivered",
                entity_type="offer",
                action_type="send_external_communication",
                safety_class="C",
            ),
            OWNER,
        )
    )["rule"]
    await automation.publish_rule(
        class_c_rule["id"],
        {"reason": "Test Class C approval projection."},
        OWNER,
        agency_id=AGENCY_A,
    )
    source = await timeline_event(
        collaboration,
        AGENCY_A,
        "offer.delivered",
        "offer",
        "offer-class-c",
        "class-c",
    )
    result = await automation.run_automation(
        {
            "agency_id": AGENCY_A,
            "trigger_event": "offer.delivered",
            "source_entity_type": "offer",
            "source_entity_id": "offer-class-c",
            "source_timeline_entry_id": source["id"],
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    approval_ids = result["run"].get("approvals_created") or []
    check("class_c_creates_approval", len(approval_ids) == 1, str(result))
    check(
        "class_c_does_not_send",
        await db.collection("communication_messages").count() == 0,
        "Class C action wrote communication truth.",
    )
    approval_id = approval_ids[0]
    await expect_error(
        "approval_separation_of_duties",
        lambda: automation.decide_approval(
            approval_id,
            {"decision": "approved", "reason": "Requester cannot approve."},
            OWNER,
            AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "different users",
    )
    rejected = await automation.decide_approval(
        approval_id,
        {"decision": "rejected", "reason": "Human review rejected the action."},
        APPROVER,
        AGENCY_A,
    )
    check(
        "rejected_approval_executes_nothing",
        rejected["approval"]["approval_status"] == "rejected"
        and rejected["underlying_action_executed"] is False,
        str(rejected),
    )
    replay = await automation.decide_approval(
        approval_id,
        {"decision": "rejected", "reason": "Same immutable decision."},
        APPROVER,
        AGENCY_A,
    )
    check("approval_decision_idempotent", replay["idempotent_reused"], str(replay))


async def verify_work_items_and_dependencies(
    db: Database,
    queue: AgentWorkQueueService,
    automation: TaskAutomationDependencyService,
) -> None:
    item = await create_manual_item(queue, "assignment-source")
    assigned = await queue.route_assignment(
        item["id"],
        strategy="least_open_eligible",
        user=OWNER,
        agency_id=AGENCY_A,
        reason="Deterministic least-open assignment.",
        expected_version=item["version"],
    )
    chosen = assigned["work_item"]["assigned_user_id"]
    check(
        "least_workload_assignment_is_eligible",
        chosen in {OWNER["id"], APPROVER["id"], AGENT_A["id"], AGENT_B["id"]},
        str(assigned),
    )
    routed_again = await queue.route_assignment(
        item["id"],
        strategy="least_open_eligible",
        user=OWNER,
        agency_id=AGENCY_A,
        reason="Repeat deterministic least-open assignment.",
        expected_version=assigned["work_item"]["version"],
    )
    check(
        "least_workload_assignment_deterministic",
        routed_again["work_item"]["assigned_user_id"] == chosen,
        str(routed_again),
    )

    round_item = await create_manual_item(queue, "round-robin-source")
    round_one = await queue.route_assignment(
        round_item["id"],
        strategy="round_robin",
        user=OWNER,
        agency_id=AGENCY_A,
        reason="Deterministic round robin.",
        expected_version=round_item["version"],
    )
    round_two = await queue.route_assignment(
        round_item["id"],
        strategy="round_robin",
        user=OWNER,
        agency_id=AGENCY_A,
        reason="Repeat deterministic round robin.",
        expected_version=round_one["work_item"]["version"],
    )
    check(
        "round_robin_assignment_deterministic",
        round_one["work_item"]["assigned_user_id"]
        == round_two["work_item"]["assigned_user_id"],
        f"{round_one} != {round_two}",
    )
    await expect_error(
        "revoked_member_not_assignable",
        lambda: queue.apply_action(
            round_item["id"],
            "reassign",
            {"to_user_id": REVOKED["id"], "reason": "Must reject revoked user."},
            OWNER,
            agency_id=AGENCY_A,
        ),
        (AgentWorkQueueError,),
        "active member",
    )

    predecessor = await create_manual_item(queue, "dependency-predecessor")
    successor = await create_manual_item(queue, "dependency-successor")
    dependency = (
        await automation.create_dependency(
            {
                "agency_id": AGENCY_A,
                "predecessor_task_id": predecessor["id"],
                "successor_task_id": successor["id"],
                "dependency_type": "mandatory",
            },
            OWNER,
            agency_id=AGENCY_A,
        )
    )["dependency"]
    check(
        "mandatory_dependency_blocks_successor",
        dependency["status"] in {"pending", "blocked"},
        str(dependency),
    )
    await expect_error(
        "blocked_successor_cannot_complete",
        lambda: queue.apply_action(
            successor["id"],
            "complete",
            {"completion_evidence": {"reviewed": True}},
            OWNER,
            agency_id=AGENCY_A,
        ),
        (AgentWorkQueueError,),
        "dependencies",
    )
    await expect_error(
        "dependency_cycle_rejected",
        lambda: automation.create_dependency(
            {
                "agency_id": AGENCY_A,
                "predecessor_task_id": successor["id"],
                "successor_task_id": predecessor["id"],
                "dependency_type": "mandatory",
            },
            OWNER,
            agency_id=AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "cycle",
    )
    await queue.apply_action(
        predecessor["id"],
        "complete",
        {"completion_evidence": {"reviewed": True}},
        OWNER,
        agency_id=AGENCY_A,
    )
    updated_dependency = await db.collection(
        "operational_task_dependencies"
    ).find_one({"id": dependency["id"]})
    check(
        "predecessor_completion_unblocks",
        updated_dependency and updated_dependency["status"] == "satisfied",
        str(updated_dependency),
    )

    current_successor = await queue.get_work_item(successor["id"], AGENCY_A)
    blocked = await queue.apply_action(
        successor["id"],
        "block",
        {
            "reason": "Human evidence remains unresolved.",
            "expected_version": current_successor["version"],
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    await expect_error(
        "human_blocker_prevents_completion",
        lambda: queue.apply_action(
            successor["id"],
            "complete",
            {
                "completion_evidence": {"reviewed": True},
                "expected_version": blocked["work_item"]["version"],
            },
            OWNER,
            agency_id=AGENCY_A,
        ),
        (AgentWorkQueueError,),
        "blockers",
    )
    resolved = await queue.apply_action(
        successor["id"],
        "resolve_blocker",
        {
            "reason": "Evidence was reviewed by the operator.",
            "expected_version": blocked["work_item"]["version"],
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    completed = await queue.apply_action(
        successor["id"],
        "complete",
        {
            "completion_evidence": {"reviewed": True, "source": "smoke"},
            "expected_version": resolved["work_item"]["version"],
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    check(
        "completion_records_actor_and_evidence",
        completed["work_item"]["status"] == "completed"
        and completed["work_item"].get("completed_at"),
        str(completed),
    )
    reopened = await queue.apply_action(
        successor["id"],
        "reopen",
        {
            "reason": "New internal evidence requires review.",
            "expected_version": completed["work_item"]["version"],
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    check(
        "reopen_normalizes_to_open",
        reopened["work_item"]["status"] == "open",
        str(reopened),
    )
    await expect_error(
        "stale_work_item_version_rejected",
        lambda: queue.update_work_item(
            successor["id"],
            {"title": "Stale update", "expected_version": 1},
            OWNER,
            agency_id=AGENCY_A,
        ),
        (AgentWorkQueueError,),
        "version conflict",
    )

    other = await create_manual_item(
        queue,
        "other-agency-source",
        agency_id=AGENCY_B,
    )
    await expect_error(
        "cross_agency_dependency_rejected",
        lambda: automation.create_dependency(
            {
                "agency_id": AGENCY_A,
                "predecessor_task_id": predecessor["id"],
                "successor_task_id": other["id"],
                "dependency_type": "mandatory",
            },
            OWNER,
            agency_id=AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "not found",
    )
    check(
        "canonical_status_catalog_has_no_legacy_states",
        "accepted" not in WORK_ITEM_STATUSES and "reopened" not in WORK_ITEM_STATUSES,
        str(WORK_ITEM_STATUSES),
    )


async def verify_notifications(
    db: Database,
    queue: AgentWorkQueueService,
    collaboration: OperationalCollaborationService,
) -> None:
    item = await create_manual_item(queue, "notification-source")
    assigned = await queue.apply_action(
        item["id"],
        "assign",
        {
            "to_user_id": AGENT_A["id"],
            "reason": "User-scoped assignment notification.",
            "expected_version": item["version"],
        },
        OWNER,
        agency_id=AGENCY_A,
    )
    agent_notifications = await collaboration.list_notifications(
        AGENCY_A, visibility={"internal"}, user_id=AGENT_A["id"]
    )
    other_notifications = await collaboration.list_notifications(
        AGENCY_A, visibility={"internal"}, user_id=AGENT_B["id"]
    )
    targeted = [
        item
        for item in agent_notifications
        if item.get("recipient_user_id") == AGENT_A["id"]
    ]
    check("assignment_notification_is_user_scoped", bool(targeted), str(assigned))
    check(
        "other_user_cannot_list_targeted_notification",
        all(
            item.get("recipient_user_id") != AGENT_A["id"]
            for item in other_notifications
        ),
        str(other_notifications),
    )
    notification = targeted[-1]
    await expect_error(
        "other_user_cannot_acknowledge_targeted_notification",
        lambda: collaboration.mark_notification_read(
            AGENCY_A, notification["id"], AGENT_B["id"]
        ),
        (OperationalCollaborationError,),
        "not found",
    )
    read = await collaboration.mark_notification_read(
        AGENCY_A, notification["id"], AGENT_A["id"]
    )
    check(
        "notification_read_state_is_user_specific",
        read["status"] == "read"
        and AGENT_A["id"] in read["read_by_user_ids"],
        str(read),
    )
    before = await db.collection("operational_notification_projections").count(
        {"agency_id": AGENCY_A}
    )
    rebuilt = await collaboration.rebuild_notification_projections(AGENCY_A)
    after = await db.collection("operational_notification_projections").count(
        {"agency_id": AGENCY_A}
    )
    check(
        "notification_projection_regeneration_deduplicates",
        before == after and rebuilt["business_truth_mutated"] is False,
        str(rebuilt),
    )


async def verify_sla_reminders_locks_and_migration(
    db: Database,
    queue: AgentWorkQueueService,
    automation: TaskAutomationDependencyService,
) -> None:
    sla = OperationalSlaDeadlineService(db)
    calendar = (
        await sla.create_business_calendar(
            {
                "agency_id": AGENCY_A,
                "calendar_code": "sofia_business",
                "name": "Sofia Business Calendar",
                "timezone": "Europe/Sofia",
                "working_days": [0, 1, 2, 3, 4],
                "working_hours_json": {"start": "09:00", "end": "17:00"},
                "holidays": [],
                "exceptions": [],
                "status": "active",
            },
            OWNER,
        )
    )["business_calendar"]
    policy = (
        await sla.create_policy(
            {
                "agency_id": AGENCY_A,
                "scope": "agency",
                "policy_code": "request_business_day",
                "name": "Request one business day",
                "entity_type": "request",
                "deadline_type": "request_response_sla",
                "duration_value": 1,
                "duration_unit": "business_days",
                "business_hours_behavior": "business_hours",
                "calendar_id": calendar["id"],
                "status": "active",
                "timezone": "Europe/Sofia",
            },
            OWNER,
        )
    )["policy"]
    friday = datetime(2026, 7, 24, 7, 0, tzinfo=timezone.utc)
    first = (
        await sla.create_deadline(
            {
                "agency_id": AGENCY_A,
                "policy_id": policy["id"],
                "source_entity_type": "request",
                "source_entity_id": "sla-request-one",
                "deadline_type": "request_response_sla",
                "started_at": friday,
            },
            OWNER,
            agency_id=AGENCY_A,
        )
    )["deadline"]
    check(
        "business_day_calculation_skips_weekend",
        first["due_at"].startswith("2026-07-27T07:00:00"),
        str(first["due_at"]),
    )
    updated_policy = (
        await sla.update_policy(
            policy["id"],
            {
                "duration_value": 2,
                "expected_version": policy["version"],
            },
            OWNER,
            agency_id=AGENCY_A,
        )
    )["policy"]
    second = (
        await sla.create_deadline(
            {
                "agency_id": AGENCY_A,
                "policy_id": updated_policy["id"],
                "source_entity_type": "request",
                "source_entity_id": "sla-request-two",
                "deadline_type": "request_response_sla",
                "started_at": friday,
            },
            OWNER,
            agency_id=AGENCY_A,
        )
    )["deadline"]
    check(
        "deadline_records_policy_version",
        first["policy_version"] == 1 and second["policy_version"] == 2,
        f"{first['policy_version']} / {second['policy_version']}",
    )
    persisted_first = await db.collection("operational_deadlines").find_one(
        {"id": first["id"]}
    )
    check(
        "historical_deadline_not_rewritten",
        persisted_first
        and persisted_first["due_at"] == first["due_at"]
        and persisted_first["policy_version"] == 1,
        str(persisted_first),
    )

    reminder_item = await create_manual_item(queue, "deadline-reminder-source")
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    reminder_deadline = (
        await sla.create_deadline(
            {
                "agency_id": AGENCY_A,
                "source_entity_type": "request",
                "source_entity_id": "deadline-reminder-source",
                "work_item_id": reminder_item["id"],
                "deadline_type": "task_deadline",
                "due_at": past,
            },
            OWNER,
            agency_id=AGENCY_A,
        )
    )["deadline"]
    first_projection = await automation.process_reminders_and_escalations(
        {"batch_limit": 20}, OWNER, agency_id=AGENCY_A
    )
    second_projection = await automation.process_reminders_and_escalations(
        {"batch_limit": 20}, OWNER, agency_id=AGENCY_A
    )
    check(
        "overdue_reminder_projection_deduplicated",
        any(
            item["deadline_id"] == reminder_deadline["id"]
            for item in first_projection["projections"]
        )
        and second_projection["deduplicated_count"] >= 1,
        f"{first_projection} / {second_projection}",
    )
    check(
        "reminder_processing_is_bounded",
        first_projection["bounded_record_limit"] <= MAX_PROCESS_BATCH,
        str(first_projection),
    )

    await db.collection("operational_task_automation_runs").insert_one(
        {
            "id": "stale-run",
            "agency_id": AGENCY_A,
            "run_reference": "RUN-STALE",
            "trigger_event": "request.created",
            "source_entity_type": "request",
            "source_entity_id": "stale-source",
            "source_timeline_entry_id": "stale-timeline",
            "idempotency_key": "stale-run-key",
            "status": "processing",
            "lock_token": "stale-token",
            "locked_until": datetime.now(timezone.utc) - timedelta(minutes=1),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )
    recovered = await automation.recover_stale_execution_locks(AGENCY_A, OWNER)
    stale = await db.collection("operational_task_automation_runs").find_one(
        {"id": "stale-run"}
    )
    check(
        "stale_execution_lock_recovers_to_manual_review",
        recovered["recovered_count"] == 1
        and stale
        and stale["status"] == "manual_review"
        and stale["lock_token"] is None,
        f"{recovered} / {stale}",
    )

    before = {
        name: await db.collection(name).count()
        for name in (
            "request_tasks",
            "operational_work_items",
            "operational_deadlines",
            "operational_task_automation_rules",
            "operational_task_automation_runs",
        )
    }
    analysis = await automation.migration_analysis(
        maximum_records_per_collection=500
    )
    after = {
        name: await db.collection(name).count()
        for name in before
    }
    check(
        "migration_analysis_performs_zero_writes",
        analysis["writes_performed"] == 0 and before == after,
        str(analysis),
    )
    check(
        "migration_analysis_is_bounded",
        analysis["maximum_records_per_collection"] == 500,
        str(analysis),
    )
    metrics = await automation.operational_metrics(AGENCY_A)
    check(
        "metrics_derive_from_canonical_work",
        metrics["bounded_record_limit"] == 500
        and metrics["predictive_ai_disabled"]
        and metrics["supplier_cost_margin_metrics_excluded"],
        str(metrics),
    )


async def verify_cross_agency_event(
    automation: TaskAutomationDependencyService,
    collaboration: OperationalCollaborationService,
) -> None:
    other_event = await timeline_event(
        collaboration,
        AGENCY_B,
        "request.created",
        "request",
        "request-other-agency",
        "other-agency",
    )
    await expect_error(
        "cross_agency_source_event_rejected",
        lambda: automation.run_automation(
            {
                "agency_id": AGENCY_A,
                "trigger_event": "request.created",
                "source_entity_type": "request",
                "source_entity_id": "request-other-agency",
                "source_timeline_entry_id": other_event["id"],
            },
            OWNER,
            agency_id=AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "not found",
    )
    await expect_error(
        "recursion_limit_enforced",
        lambda: automation.run_automation(
            {
                "agency_id": AGENCY_A,
                "trigger_event": "request.created",
                "source_entity_type": "request",
                "source_entity_id": "recursive",
                "recursion_depth": 99,
            },
            OWNER,
            agency_id=AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "recursion",
    )
    await expect_error(
        "chain_limit_enforced",
        lambda: automation.run_automation(
            {
                "agency_id": AGENCY_A,
                "trigger_event": "request.created",
                "source_entity_type": "request",
                "source_entity_id": "chain",
                "chained_action_count": 99,
            },
            OWNER,
            agency_id=AGENCY_A,
        ),
        (TaskAutomationDependencyError,),
        "chain",
    )


def verify_pure_contract() -> None:
    context = {
        "event": {
            "event_type": "offer.delivered",
            "event_time": "2026-07-25T10:00:00Z",
        },
        "offer": {"status": "delivered", "expires_at": "2026-07-26T09:00:00Z"},
    }
    conditions = {
        "all": [
            {
                "field": "event.event_type",
                "operator": "equals",
                "value": "offer.delivered",
            },
            {
                "field": "offer.expires_at",
                "operator": "within_hours",
                "value": 24,
            },
        ]
    }
    matched, trace = evaluate_conditions(
        conditions,
        context,
        evaluation_time=datetime(2026, 7, 25, 10, 0, tzinfo=timezone.utc),
    )
    check(
        "bounded_condition_engine_matches",
        matched and len(trace) == 2,
        str(trace),
    )
    try:
        validate_rule_contract(
            {
                "trigger_event_types": ["request.created"],
                "conditions_json": {
                    "field": "request.status",
                    "operator": "equals",
                    "value": "new",
                },
                "actions": [
                    {
                        "action_type": "create_work_item",
                        "parameters": {"password": "unsafe"},
                    }
                ],
                "execution_safety_class": "A",
            }
        )
    except GovernedAutomationContractError as exc:
        check(
            "sensitive_action_payload_rejected",
            "forbidden" in str(exc).lower(),
            str(exc),
        )
    else:
        raise AssertionError("sensitive_action_payload_rejected")


async def main_async() -> None:
    verify_pure_contract()
    db = Database()
    for agency_id in (AGENCY_A, AGENCY_B):
        await seed_membership(db, agency_id, OWNER["id"], "agency_owner")
    await seed_membership(db, AGENCY_A, APPROVER["id"], "agency_owner")
    await seed_membership(db, AGENCY_A, AGENT_A["id"], "agency_agent")
    await seed_membership(db, AGENCY_A, AGENT_B["id"], "agency_agent")
    await seed_membership(
        db, AGENCY_A, REVOKED["id"], "agency_agent", status="suspended"
    )

    queue = AgentWorkQueueService(db)
    automation = TaskAutomationDependencyService(db)
    collaboration = OperationalCollaborationService(db)

    await verify_rule_contract(db, automation, collaboration)
    await verify_class_c_and_approvals(db, automation, collaboration)
    await verify_work_items_and_dependencies(db, queue, automation)
    await verify_notifications(db, queue, collaboration)
    await verify_sla_reminders_locks_and_migration(db, queue, automation)
    await verify_cross_agency_event(automation, collaboration)

    check(
        "focused_behavior_check_floor",
        len(CHECKS) >= 45,
        f"Expected at least 45 focused checks, ran {len(CHECKS)}.",
    )


def main() -> int:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="canonical build phase",
    )
    asyncio.run(main_async())
    print(
        "Governed automation orchestration smoke passed: "
        f"{len(CHECKS)} checks."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"Governed automation orchestration smoke failed: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
