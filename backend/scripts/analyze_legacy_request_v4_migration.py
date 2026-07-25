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
from services.request_v4_service import analyze_legacy_requests  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze legacy TravelRequest records for Request V4 compatibility without writing data."
    )
    parser.add_argument("--agency-id")
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    await database.connect()
    try:
        result = await analyze_legacy_requests(database, agency_id=args.agency_id)
    finally:
        await database.disconnect()
    print(json.dumps(result, indent=2, default=str))
    if not result.get("dry_run") or result.get("writes_performed") != 0:
        raise RuntimeError("Legacy Request V4 analysis violated dry-run mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
