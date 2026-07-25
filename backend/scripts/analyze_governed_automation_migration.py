#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_database
from services.task_automation_dependency_service import (
    TaskAutomationDependencyService,
)


ANALYZED_COLLECTIONS = (
    "request_tasks",
    "operational_work_items",
    "operational_workflow_instances",
    "operational_deadlines",
    "operational_task_dependencies",
    "operational_notification_projections",
    "operational_task_automation_rules",
    "operational_task_automation_runs",
    "operational_queue_definitions",
    "agency_staff_memberships",
    "operational_timelines",
)


async def collection_counts(database) -> dict[str, int]:
    return {
        name: await database.collection(name).count()
        for name in ANALYZED_COLLECTIONS
    }


async def run(limit: int) -> dict:
    database = await get_database()
    before = await collection_counts(database)
    report = await TaskAutomationDependencyService(database).migration_analysis(
        maximum_records_per_collection=limit
    )
    after = await collection_counts(database)
    return {
        **report,
        "before_counts": before,
        "after_counts": after,
        "counts_unchanged": before == after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Permanently read-only analysis of legacy tasks, canonical work "
            "items, deadlines, dependencies, approvals, projections, rules, "
            "and automation lineage."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum records inspected per collection (default: 5000).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Reserved safety switch; governed automation migration writes are unavailable.",
    )
    args = parser.parse_args()
    if args.write:
        parser.error(
            "--write is unavailable; governed automation migration analysis "
            "is permanently dry-run only."
        )
    if args.limit < 1 or args.limit > 10000:
        parser.error("--limit must be between 1 and 10000.")
    report = asyncio.run(run(args.limit))
    ok = report.get("writes_performed") == 0 and report.get(
        "counts_unchanged"
    )
    print(json.dumps({"ok": ok, "report": report}, indent=2, default=str))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
