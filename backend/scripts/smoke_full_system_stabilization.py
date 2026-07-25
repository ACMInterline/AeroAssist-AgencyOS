#!/usr/bin/env python3
"""Registered source-level gate for Product Recovery 11B stabilization."""

from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from build_phase import CURRENT_BUILD_PHASE
from phase_assertions import assert_application_phase_at_least
from validate_full_system_stabilization import main as validate_stabilization
from validate_stabilization_accessibility import main as validate_accessibility


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"


def main() -> int:
    assert_application_phase_at_least(
        CURRENT_BUILD_PHASE,
        MINIMUM_PHASE,
        source="canonical build phase",
    )
    assert validate_accessibility() == 0
    assert validate_stabilization() == 0
    print("Product Recovery 11B full-system stabilization smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
