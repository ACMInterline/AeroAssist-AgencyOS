#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from database import database  # noqa: E402
from services.canonical_reference_service import analyze_reference_wiring  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze canonical reference wiring and reconciliation candidates "
            "without writing any records."
        )
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Reserved safety flag. Write mode is intentionally unavailable.",
    )
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    if args.write:
        raise RuntimeError(
            "Reference wiring migration write mode is not implemented. "
            "Use the dry-run report for governed planning."
        )
    await database.connect()
    try:
        result = await analyze_reference_wiring(database)
    finally:
        await database.disconnect()
    if (
        result.get("dry_run") is not True
        or result.get("writes_performed") != 0
        or result.get("write_mode_available") is not False
        or result.get("before_counts") != result.get("after_counts")
    ):
        raise RuntimeError("Canonical reference analysis violated dry-run guarantees.")
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
