#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


os.environ["AEROASSIST_DB_MODE"] = "memory"
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from commercial_ledger_smoke_support import run_suite
from build_phase import CURRENT_BUILD_PHASE
from phase_assertions import assert_application_phase_at_least


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"


if __name__ == "__main__":
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE, MINIMUM_PHASE, source="build_phase.CURRENT_BUILD_PHASE"
    )
    checks = asyncio.run(run_suite("invoice"))
    print(f"Canonical invoice lifecycle smoke passed: {len(checks)} checks.")
