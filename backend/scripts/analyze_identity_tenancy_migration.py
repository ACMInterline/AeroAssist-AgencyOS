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
from services.identity_tenancy_migration_service import (
    IdentityTenancyMigrationError,
    analyze_identity_tenancy_migration,
)


async def run(agency_id: str | None, apply: bool) -> dict:
    db = await get_database()
    return await analyze_identity_tenancy_migration(
        db,
        agency_id=agency_id,
        apply=apply,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze canonical identity, portal linkage, and master-record reconciliation."
    )
    parser.add_argument("--agency-id", help="Limit analysis to one agency.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Reserved safety switch; write mode is intentionally unavailable.",
    )
    args = parser.parse_args()
    try:
        report = asyncio.run(run(args.agency_id, args.apply))
    except IdentityTenancyMigrationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps({"ok": True, "report": report}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
