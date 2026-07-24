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
from services.operational_collaboration_service import (
    ATTACHMENT_COLLECTION,
    LEGACY_COMMUNICATION_STRUCTURES,
    LEGACY_TIMELINE_STRUCTURES,
    MESSAGE_COLLECTION,
    NOTIFICATION_COLLECTION,
    PARTICIPANT_COLLECTION,
    THREAD_COLLECTION,
    OperationalCollaborationService,
)


ANALYZED_COLLECTIONS = tuple(
    dict.fromkeys(
        [
            *(item["structure"] for item in LEGACY_COMMUNICATION_STRUCTURES),
            *(item["structure"] for item in LEGACY_TIMELINE_STRUCTURES),
            THREAD_COLLECTION,
            MESSAGE_COLLECTION,
            PARTICIPANT_COLLECTION,
            ATTACHMENT_COLLECTION,
            NOTIFICATION_COLLECTION,
        ]
    )
)


async def counts(database) -> dict[str, int]:
    return {
        collection: await database.collection(collection).count()
        for collection in ANALYZED_COLLECTIONS
    }


async def run(limit: int) -> dict:
    database = await get_database()
    before = await counts(database)
    report = await OperationalCollaborationService(database).migration_analysis(
        maximum_records_per_collection=limit
    )
    after = await counts(database)
    return {
        **report,
        "before_counts": before,
        "after_counts": after,
        "counts_unchanged": before == after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only analysis of legacy timelines, messages, internal notes, "
            "threads, entity links, and attachment references against the "
            "canonical operational collaboration contract."
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
        help="Reserved safety switch; collaboration migration writes are unavailable.",
    )
    args = parser.parse_args()
    if args.write:
        parser.error(
            "--write is unavailable; operational collaboration analysis is permanently dry-run only."
        )
    if args.limit < 1 or args.limit > 10000:
        parser.error("--limit must be between 1 and 10000.")
    report = asyncio.run(run(args.limit))
    if not report["counts_unchanged"] or report.get("writes_performed") != 0:
        print(json.dumps({"ok": False, "report": report}, indent=2, default=str))
        return 2
    print(json.dumps({"ok": True, "report": report}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
