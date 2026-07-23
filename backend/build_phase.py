from __future__ import annotations

import re
from dataclasses import dataclass


CURRENT_BUILD_PHASE = "phase_59_0_product_experience_recovery"

_PHASE_PATTERN = re.compile(
    r"^phase_(?P<numeric>\d+(?:_\d+)+)_(?P<label>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)$"
)


class InvalidPhaseIdentifier(ValueError):
    pass


@dataclass(frozen=True)
class PhaseIdentifier:
    value: str
    numeric_components: tuple[int, ...]
    label: str


def parse_phase_identifier(value: str) -> PhaseIdentifier:
    if not isinstance(value, str):
        raise InvalidPhaseIdentifier("Phase identifier must be a string.")
    match = _PHASE_PATTERN.fullmatch(value)
    if match is None:
        raise InvalidPhaseIdentifier(
            "Phase identifier must use phase_<major>_<minor>[_<patch>...]_<label>."
        )
    return PhaseIdentifier(
        value=value,
        numeric_components=tuple(int(component) for component in match.group("numeric").split("_")),
        label=match.group("label"),
    )


def compare_phase_identifiers(left: str, right: str) -> int:
    left_phase = parse_phase_identifier(left)
    right_phase = parse_phase_identifier(right)
    component_count = max(len(left_phase.numeric_components), len(right_phase.numeric_components))
    left_components = left_phase.numeric_components + (0,) * (component_count - len(left_phase.numeric_components))
    right_components = right_phase.numeric_components + (0,) * (component_count - len(right_phase.numeric_components))
    if left_components < right_components:
        return -1
    if left_components > right_components:
        return 1
    return 0


def phase_is_exact(actual: str, expected: str) -> bool:
    parse_phase_identifier(actual)
    parse_phase_identifier(expected)
    return actual == expected


def phase_is_at_least(actual: str, minimum: str) -> bool:
    return compare_phase_identifiers(actual, minimum) >= 0


# Validate the checked-in release marker when this dependency-free module is imported.
parse_phase_identifier(CURRENT_BUILD_PHASE)
