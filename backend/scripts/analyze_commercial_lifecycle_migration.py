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
from services.canonical_commercial_lifecycle_service import (
    analyze_commercial_lifecycle,
)


async def run(limit: int) -> dict:
    database = await get_database()
    return await analyze_commercial_lifecycle(
        database,
        maximum_records_per_collection=limit,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only analysis of legacy Offer, Trip, Booking, Ticket, and EMD "
            "records against the canonical commercial lifecycle."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum records inspected per collection (default: 5000).",
    )
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 10000:
        parser.error("--limit must be between 1 and 10000.")
    report = asyncio.run(run(args.limit))
    print(json.dumps({"ok": True, "report": report}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
