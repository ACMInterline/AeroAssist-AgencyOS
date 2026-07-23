#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from database import database
from services.request_passenger_identity_service import (
    quarantine_legacy_intake_placeholders,
)


APPLY_CONFIRMATION = "QUARANTINE_LEGACY_INTAKE_PLACEHOLDERS"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find legacy synthetic passenger profiles created by intake conversion. "
            "The default mode is read-only."
        )
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--agency-id")
    scope.add_argument("--all-agencies", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--actor-user-id", default="p0-passenger-integrity-maintenance")
    parser.add_argument(
        "--confirmation",
        help=f"Required with --apply: {APPLY_CONFIRMATION}",
    )
    args = parser.parse_args()
    if args.apply and args.confirmation != APPLY_CONFIRMATION:
        parser.error(f"--apply requires --confirmation {APPLY_CONFIRMATION}")
    return args


async def run(args: argparse.Namespace) -> int:
    await database.connect()
    try:
        if args.all_agencies:
            agencies = await database.collection("agencies").find_many({}, limit=10000)
            agency_ids = [item["id"] for item in agencies]
        else:
            agency = await database.collection("agencies").find_one({"id": args.agency_id})
            if not agency:
                raise RuntimeError("Agency not found.")
            agency_ids = [args.agency_id]

        reports = [
            await quarantine_legacy_intake_placeholders(
                database,
                agency_id,
                args.actor_user_id,
                apply=args.apply,
            )
            for agency_id in agency_ids
        ]
        print(
            json.dumps(
                {
                    "mode": "apply" if args.apply else "dry_run",
                    "agency_count": len(agency_ids),
                    "candidate_count": sum(item["candidate_count"] for item in reports),
                    "quarantined_count": sum(item["quarantined_count"] for item in reports),
                    "migrated_request_passenger_count": sum(
                        item["migrated_request_passenger_count"] for item in reports
                    ),
                    "reports": reports,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    finally:
        await database.disconnect()


def main() -> int:
    return asyncio.run(run(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
