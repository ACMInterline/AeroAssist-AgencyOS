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
from services.reference_data_service import create_reference_import_batch  # noqa: E402


async def run(args: argparse.Namespace) -> dict:
    csv_path = Path(args.csv_file)
    csv_text = csv_path.read_text(encoding="utf-8")
    db = Database()
    await db.connect()
    batch = await create_reference_import_batch(
        db,
        domain=args.domain,
        filename=csv_path.name,
        csv_text=csv_text,
        scope="global",
        actor_user_id=args.actor_user_id,
        dry_run=args.dry_run,
    )
    return {"ok": batch.get("status") != "failed", "batch": batch}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely import global AeroAssist reference data from CSV.")
    parser.add_argument("domain", help="Reference domain, e.g. airports")
    parser.add_argument("csv_file", help="CSV file with domain,code,label,description,aliases,sort_order,is_active,metadata_json columns")
    parser.add_argument("--actor-user-id", default="manual_reference_import", help="Audit actor identifier")
    parser.add_argument("--dry-run", action="store_true", help="Validate without inserting/updating records")
    args = parser.parse_args()
    result = asyncio.run(run(args))
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
