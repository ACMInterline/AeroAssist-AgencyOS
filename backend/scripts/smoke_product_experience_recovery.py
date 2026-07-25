#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from build_phase import CURRENT_BUILD_PHASE, phase_is_exact
from services.product_experience_recovery_service import PHASE_LABEL
from validate_product_experience_recovery import main


if __name__ == "__main__":
    assert phase_is_exact(CURRENT_BUILD_PHASE, CURRENT_BUILD_PHASE)
    assert CURRENT_BUILD_PHASE == PHASE_LABEL
    raise SystemExit(main())
