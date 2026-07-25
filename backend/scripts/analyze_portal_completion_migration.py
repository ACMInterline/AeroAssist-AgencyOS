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
from services.portal_projection_service import PortalProjectionService


ANALYZED_COLLECTIONS = (
    "portal_access_mappings",
    "auth_identities",
    "portal_action_events",
    "document_acknowledgements",
    "journey_offer_client_decisions",
    "journey_offer_client_interactions",
)


async def counts(database, agency_id: str | None) -> dict[str, int]:
    query = {"agency_id": agency_id} if agency_id else None
    return {
        collection: await database.collection(collection).count(query)
        for collection in ANALYZED_COLLECTIONS
    }


async def run(agency_id: str | None) -> dict:
    database = await get_database()
    before = await counts(database, agency_id)
    report = await PortalProjectionService(database).migration_analysis(agency_id)
    after = await counts(database, agency_id)
    return {
        **report,
        "before_counts": before,
        "after_counts": after,
        "counts_unchanged": before == after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only analysis of legacy Portal mappings, missing subject links, "
            "duplicate active mappings, and historical Portal compatibility records."
        )
    )
    parser.add_argument(
        "--agency-id",
        help="Optionally restrict analysis to one Agency identifier.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Reserved safety switch; Portal migration writes are unavailable.",
    )
    args = parser.parse_args()
    if args.write:
        parser.error(
            "--write is unavailable; Portal completion analysis is permanently dry-run only."
        )

    report = asyncio.run(run(args.agency_id))
    if (
        not report["counts_unchanged"]
        or report.get("writes_performed") != 0
        or report.get("write_mode_available") is not False
    ):
        print(json.dumps({"ok": False, "report": report}, indent=2, default=str))
        return 2
    print(json.dumps({"ok": True, "report": report}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
