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
from services.canonical_commercial_ledger_service import (
    CanonicalCommercialLedgerService,
)


async def run(limit: int) -> dict:
    database = await get_database()
    return await CanonicalCommercialLedgerService(database).migration_analysis(
        maximum_records_per_collection=limit
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only analysis of legacy invoices, payments, refunds, supplier "
            "costs, margins, and allocations against the canonical commercial ledger."
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
        help="Reserved safety switch; commercial-ledger write migration is unavailable.",
    )
    args = parser.parse_args()
    if args.write:
        parser.error("--write is unavailable; this analysis is permanently dry-run only.")
    if args.limit < 1 or args.limit > 10000:
        parser.error("--limit must be between 1 and 10000.")
    report = asyncio.run(run(args.limit))
    if report["before_counts"] != report["after_counts"]:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Collection counts changed during dry-run analysis.",
                    "report": report,
                },
                indent=2,
                default=str,
            )
        )
        return 2
    print(json.dumps({"ok": True, "report": report}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
