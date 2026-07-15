from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from build_phase import InvalidPhaseIdentifier, phase_is_at_least


def application_phase_is_at_least(
    actual: object,
    minimum: str,
    *,
    source: str = "application phase",
) -> bool:
    if not isinstance(actual, str):
        raise AssertionError(f"{source} did not provide a string application phase: {actual!r}")
    try:
        return phase_is_at_least(actual, minimum)
    except InvalidPhaseIdentifier as exc:
        raise AssertionError(f"{source} provided an invalid application phase {actual!r}: {exc}") from exc


def assert_application_phase_at_least(actual: object, minimum: str, *, source: str) -> None:
    if not application_phase_is_at_least(actual, minimum, source=source):
        raise AssertionError(
            f"{source} application phase {actual!r} is older than required minimum {minimum!r}."
        )
