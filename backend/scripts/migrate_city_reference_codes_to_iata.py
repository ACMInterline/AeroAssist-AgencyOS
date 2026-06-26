#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import Database  # noqa: E402
from services.reference_data_service import normalize_city_reference_codes  # noqa: E402


async def run(commit: bool) -> dict:
    db = Database()
    await db.connect()
    return await normalize_city_reference_codes(db, actor_user_id="manual_city_code_migration", dry_run=not commit)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize seeded city reference records to canonical IATA city codes.")
    parser.add_argument("--commit", action="store_true", help="Apply changes. Without this flag the script runs as a dry run.")
    args = parser.parse_args()

    report = asyncio.run(run(args.commit))
    print(json.dumps({"ok": True, "mode": "commit" if args.commit else "dry_run", "migration": report}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
