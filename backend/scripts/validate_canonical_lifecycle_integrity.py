#!/usr/bin/env python3
"""Deterministic Product Kernel lifecycle integrity validation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from smoke_v1_golden_path_integration import run_golden_path, verify_static_contracts


INVARIANTS = (
    "same Agency across lineage",
    "stable canonical IDs",
    "no duplicate active acceptance",
    "no duplicate Trip from one accepted snapshot",
    "no Booking result without evidence",
    "no normal Ticket or EMD without Booking",
    "server-derived Invoice totals",
    "no Payment over-allocation",
    "bounded Credit Note and Refund values",
    "no Portal internal-data leakage",
    "idempotent timeline and work replay",
    "no unresolved fake PassengerProfile",
)


def main() -> int:
    verify_static_contracts()
    asyncio.run(run_golden_path())
    print(
        "Canonical lifecycle integrity validation passed: "
        f"{len(INVARIANTS)} invariants exercised through the persisted disposable Golden Path."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
