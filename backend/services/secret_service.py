import os
import re
from dataclasses import dataclass


class SecretResolutionError(ValueError):
    pass


@dataclass
class SecretResolutionResult:
    ok: bool
    value: str | None = None
    diagnostic: str | None = None


ENV_REF_PATTERN = re.compile(r"^env:([A-Za-z_][A-Za-z0-9_]*)$")


def mask_secret_ref(secret_ref: str | None) -> str | None:
    if not secret_ref:
        return None
    match = ENV_REF_PATTERN.match(secret_ref)
    if match:
        variable = match.group(1)
        if len(variable) <= 8:
            masked_variable = f"{variable[:2]}***"
        else:
            masked_variable = f"{variable[:4]}***{variable[-2:]}"
        return f"env:{masked_variable}"
    scheme = secret_ref.split(":", 1)[0] if ":" in secret_ref else "unknown"
    return f"{scheme}:***"


def resolve_secret(secret_ref: str | None) -> str | None:
    if not secret_ref:
        return None
    match = ENV_REF_PATTERN.match(secret_ref)
    if not match:
        raise SecretResolutionError("Unsupported secret reference. Use env:VARIABLE_NAME.")
    value = os.getenv(match.group(1))
    return value or None


def check_secret(secret_ref: str | None) -> SecretResolutionResult:
    if not secret_ref:
        return SecretResolutionResult(ok=False, diagnostic="Secret reference is missing.")
    try:
        value = resolve_secret(secret_ref)
    except SecretResolutionError as exc:
        return SecretResolutionResult(ok=False, diagnostic=str(exc))
    if not value:
        return SecretResolutionResult(ok=False, diagnostic="Secret reference is configured, but the environment variable is missing or empty.")
    return SecretResolutionResult(ok=True, diagnostic="Secret reference resolved from environment.")
