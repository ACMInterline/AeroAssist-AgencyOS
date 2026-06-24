#!/usr/bin/env python3
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import Database  # noqa: E402
from services.reference_data_service import bootstrap_reference_data  # noqa: E402


async def run() -> dict:
    db = Database()
    await db.connect()
    return await bootstrap_reference_data(db, actor_user_id="manual_bootstrap")


def main() -> int:
    result = asyncio.run(run())
    print(json.dumps({"ok": True, "bootstrap": result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
