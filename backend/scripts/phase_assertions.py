from __future__ import annotations

from build_phase import InvalidPhaseIdentifier, phase_is_at_least


def assert_application_phase_at_least(actual: object, minimum: str, *, source: str) -> None:
    if not isinstance(actual, str):
        raise AssertionError(f"{source} did not provide a string application phase: {actual!r}")
    try:
        current_is_supported = phase_is_at_least(actual, minimum)
    except InvalidPhaseIdentifier as exc:
        raise AssertionError(f"{source} provided an invalid application phase {actual!r}: {exc}") from exc
    if not current_is_supported:
        raise AssertionError(
            f"{source} application phase {actual!r} is older than required minimum {minimum!r}."
        )
