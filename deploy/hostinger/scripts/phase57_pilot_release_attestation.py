#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


EVIDENCE_TYPES = {
    "deployment",
    "smoke_run",
    "backup_verification",
    "restore_rehearsal",
    "production_validation",
}
EVIDENCE_STATUSES = {"PASS", "WARNING", "BLOCKED"}
DECISIONS = {"approved", "approved_with_conditions", "rejected"}
REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,200}$")
GIT_COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{7,64}$")
FORBIDDEN_KEY_FRAGMENTS = {
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "connection_string",
    "mongodb_uri",
    "passport_number",
    "payment_card",
    "raw_log",
    "filesystem_path",
}
FORBIDDEN_VALUE_FRAGMENTS = (
    "mongodb://",
    "mongodb+srv://",
    "authorization:",
    "bearer ",
    "password=",
    "secret=",
    "token=",
    "/var/",
    "/opt/",
    "/users/",
)
PRODUCTION_EVIDENCE_FIELDS = {
    "production_git_commit",
    "production_phase",
    "mongodb_authentication_verified",
    "backup_manifest_verified",
    "off_host_copy_verified",
    "restore_rehearsal_verified",
    "public_health_verified",
    "public_readiness_verified",
    "internal_diagnostics_verified",
    "github_actions_verified",
    "complete_regression_verified",
    "tenant_isolation_verified",
    "frontend_build_verified",
    "docker_build_verified",
    "production_configuration_verified",
    "rollback_procedure_verified",
    "operator_credentials_verified",
    "synthetic_pilot_fixture_verified",
    "dependency_risk_triaged",
    "frontend_chunk_risk_acknowledged",
    "telemetry_limit_acknowledged",
    "rpo_rto_risk_acknowledged",
    "evidence_references",
}
BOOLEAN_EVIDENCE_FIELDS = PRODUCTION_EVIDENCE_FIELDS - {
    "production_git_commit",
    "production_phase",
    "evidence_references",
}
OPERATIONAL_EVIDENCE_FIELDS = {
    "evidence_type",
    "status",
    "title",
    "summary",
    "environment_scope",
    "reference",
    "agency_id",
    "occurred_at",
    "expires_at",
    "evidence_metadata",
}


class AttestationError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not REFERENCE_PATTERN.fullmatch(value):
        raise AttestationError(f"{field} must use 1-200 letters, numbers, dots, hyphens, or underscores.")
    if value.startswith("REPLACE_WITH_"):
        raise AttestationError(f"{field} still contains an example placeholder.")
    return value
    return value


def assert_safe_metadata(value: Any, *, path: str = "evidence", depth: int = 0) -> None:
    if depth > 5:
        raise AttestationError(f"{path} exceeds the bounded metadata depth.")
    if isinstance(value, dict):
        if len(value) > 50:
            raise AttestationError(f"{path} contains too many fields.")
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
                raise AttestationError(f"{path}.{key} is not allowed in release evidence.")
            assert_safe_metadata(nested, path=f"{path}.{key}", depth=depth + 1)
        return
    if isinstance(value, list):
        if len(value) > 100:
            raise AttestationError(f"{path} contains too many list entries.")
        for index, nested in enumerate(value):
            assert_safe_metadata(nested, path=f"{path}[{index}]", depth=depth + 1)
        return
    if isinstance(value, str):
        if len(value) > 1200:
            raise AttestationError(f"{path} contains an oversized string.")
        lowered = value.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_VALUE_FRAGMENTS):
            raise AttestationError(f"{path} appears to contain a secret, raw path, or connection detail.")


def load_evidence_bundle(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise AttestationError("Evidence bundle must be an existing JSON file no larger than 1 MiB.")
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AttestationError(f"Evidence bundle could not be read: {exc}") from exc
    if not isinstance(bundle, dict) or set(bundle) != {
        "schema_version", "operational_evidence", "production_evidence", "sign_off_context"
    }:
        raise AttestationError("Evidence bundle must contain only schema_version, operational_evidence, production_evidence, and sign_off_context.")
    if bundle.get("schema_version") != 1:
        raise AttestationError("Evidence bundle schema_version must be 1.")
    assert_safe_metadata(bundle)

    operational = bundle.get("operational_evidence")
    if not isinstance(operational, list) or len(operational) > 20:
        raise AttestationError("operational_evidence must be a list of at most 20 records.")
    references: set[str] = set()
    for index, item in enumerate(operational):
        if not isinstance(item, dict):
            raise AttestationError(f"operational_evidence[{index}] must be an object.")
        if not set(item).issubset(OPERATIONAL_EVIDENCE_FIELDS):
            raise AttestationError(f"operational_evidence[{index}] contains unsupported fields.")
        required = {"evidence_type", "status", "title", "summary", "reference"}
        if not required.issubset(item):
            raise AttestationError(f"operational_evidence[{index}] is missing required fields.")
        if item["evidence_type"] not in EVIDENCE_TYPES:
            raise AttestationError(f"operational_evidence[{index}].evidence_type is unsupported.")
        if item["status"] not in EVIDENCE_STATUSES:
            raise AttestationError(f"operational_evidence[{index}].status is unsupported.")
        reference = safe_identifier(item["reference"], f"operational_evidence[{index}].reference")
        if reference in references:
            raise AttestationError(f"Duplicate operational evidence reference: {reference}")
        references.add(reference)
        if item.get("environment_scope", "production") != "production":
            raise AttestationError("Pilot release operational evidence must use production scope.")
        if item.get("agency_id") is not None:
            raise AttestationError("Pilot release operational evidence must not be agency-scoped.")
        if not isinstance(item["title"], str) or not 1 <= len(item["title"]) <= 160:
            raise AttestationError(f"operational_evidence[{index}].title must contain 1-160 characters.")
        if not isinstance(item["summary"], str) or not 1 <= len(item["summary"]) <= 1200:
            raise AttestationError(f"operational_evidence[{index}].summary must contain 1-1200 characters.")
        metadata = item.get("evidence_metadata", {})
        if not isinstance(metadata, dict):
            raise AttestationError(f"operational_evidence[{index}].evidence_metadata must be an object.")

    production = bundle.get("production_evidence")
    if not isinstance(production, dict) or not set(production).issubset(PRODUCTION_EVIDENCE_FIELDS):
        raise AttestationError("production_evidence contains unsupported fields.")
    for field in ("production_git_commit", "production_phase"):
        if not isinstance(production.get(field), str) or not production[field]:
            raise AttestationError(f"production_evidence.{field} is required.")
    if not GIT_COMMIT_PATTERN.fullmatch(production["production_git_commit"]):
        raise AttestationError("production_evidence.production_git_commit must be an exact hexadecimal commit identifier.")
    if not production["production_phase"].startswith("phase_"):
        raise AttestationError("production_evidence.production_phase must use a canonical phase identifier.")
    for field in BOOLEAN_EVIDENCE_FIELDS:
        if field in production and production[field] is not None and type(production[field]) is not bool:
            raise AttestationError(f"production_evidence.{field} must be true, false, or null.")
    evidence_references = production.get("evidence_references", [])
    if not isinstance(evidence_references, list) or len(evidence_references) > 20:
        raise AttestationError("production_evidence.evidence_references must be a list of at most 20 identifiers.")
    for reference in evidence_references:
        safe_identifier(reference, "production_evidence.evidence_references")

    sign_off_context = bundle.get("sign_off_context")
    if not isinstance(sign_off_context, dict) or set(sign_off_context) != {"release_id", "rollback_reference"}:
        raise AttestationError("sign_off_context must contain only release_id and rollback_reference.")
    safe_identifier(sign_off_context.get("release_id"), "sign_off_context.release_id")
    safe_identifier(sign_off_context.get("rollback_reference"), "sign_off_context.rollback_reference")
    return bundle


class GovernanceApi:
    def __init__(self, base_url: str, *, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        parsed = urllib.parse.urlparse(self.base_url)
        if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise AttestationError("The governance API requires HTTPS except for local loopback validation.")
        self.timeout = timeout
        self.access_token: str | None = None
        self.context = ssl.create_default_context()

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        request = urllib.request.Request(
            f"{self.base_url}{path}", method=method, data=data, headers=headers
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=self.context) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read(4096).decode("utf-8", errors="replace")
            try:
                detail = json.loads(raw).get("detail", "request rejected")
            except json.JSONDecodeError:
                detail = "request rejected"
            raise AttestationError(f"Governance API {method} {path} returned HTTP {exc.code}: {detail}") from exc
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise AttestationError(f"Governance API {method} {path} failed: {exc}") from exc
        if not isinstance(result, dict):
            raise AttestationError(f"Governance API {method} {path} returned an invalid response.")
        return result

    def get(self, path: str) -> dict[str, Any]:
        return self.request("GET", path)

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", path, payload)


def authenticate_owner(api: GovernanceApi, email: str, password: str) -> dict[str, Any]:
    response = api.post("/api/auth/login", {"email": email, "password": password})
    role = (((response.get("auth") or {}).get("user") or {}).get("global_role"))
    token = ((response.get("session") or {}).get("access_token"))
    if role != "platform_owner":
        raise AttestationError("Phase 57 attestation requires an authenticated Platform Owner.")
    if not isinstance(token, str) or not token:
        raise AttestationError("Authentication did not return an active Platform session.")
    api.access_token = token
    return {"role": role, "user_id": ((response.get("auth") or {}).get("user") or {}).get("id")}


def assessment_from_record(record: dict[str, Any]) -> dict[str, Any]:
    return (((record.get("evidence_metadata") or {}).get("assessment")) or {})


def record_operational_evidence(
    api: GovernanceApi,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing_response = api.get("/api/platform/pilot-operations/evidence?limit=200")
    existing = {
        (item.get("evidence_type"), item.get("reference")): item
        for item in existing_response.get("items", [])
        if isinstance(item, dict)
    }
    stored: list[dict[str, Any]] = []
    for source in records:
        payload = {
            **source,
            "environment_scope": "production",
            "occurred_at": source.get("occurred_at") or utc_now(),
            "evidence_metadata": source.get("evidence_metadata") or {},
        }
        key = (payload["evidence_type"], payload["reference"])
        prior = existing.get(key)
        if prior:
            comparable = ("status", "title", "summary", "environment_scope", "evidence_metadata")
            if any(prior.get(field) != payload.get(field) for field in comparable):
                raise AttestationError(
                    f"Evidence {payload['reference']} already exists with different immutable content."
                )
            for optional_field in ("occurred_at", "expires_at"):
                if optional_field in source and prior.get(optional_field) != source.get(optional_field):
                    raise AttestationError(
                        f"Evidence {payload['reference']} already exists with a different {optional_field}."
                    )
            stored.append(prior)
            continue
        response = api.post("/api/platform/pilot-operations/evidence", payload)
        item = response.get("evidence")
        if not isinstance(item, dict) or item.get("reference") != payload["reference"]:
            raise AttestationError(f"Evidence {payload['reference']} was not persisted correctly.")
        stored.append(item)
        existing[key] = item
    return stored


def require_referenced_evidence(
    api: GovernanceApi,
    production_evidence: dict[str, Any],
    recorded: list[dict[str, Any]],
) -> None:
    available = {item.get("reference") for item in recorded}
    if not set(production_evidence.get("evidence_references") or []).issubset(available):
        response = api.get("/api/platform/pilot-operations/evidence?limit=200")
        available.update(item.get("reference") for item in response.get("items", []) if isinstance(item, dict))
    missing = sorted(set(production_evidence.get("evidence_references") or []) - available)
    if missing:
        raise AttestationError(f"Production attestation references evidence that is not persisted: {', '.join(missing)}")


def prompt_nonempty(prompt: str, input_fn: Callable[[str], str]) -> str:
    while True:
        value = input_fn(prompt).strip()
        if value:
            return value
        print("A value is required.")


def prompt_human_sign_off(
    assessment: dict[str, Any],
    *,
    input_fn: Callable[[str], str] = input,
) -> dict[str, Any]:
    status = assessment.get("assessment_status")
    allowed = DECISIONS if status == "ready" else {"rejected"}
    print(f"Submitted assessment status: {status or 'unknown'}")
    print(f"Allowed decisions: {', '.join(sorted(allowed))}")
    while True:
        decision = input_fn("Human decision: ").strip().lower()
        if decision in allowed:
            break
        print("That decision is not allowed for the persisted assessment state.")
    reason = prompt_nonempty("Decision reason: ", input_fn)
    conditions: list[str] = []
    if decision == "approved_with_conditions":
        print("Enter one condition per line; submit a blank line when complete.")
        while True:
            condition = input_fn("Condition: ").strip()
            if not condition:
                break
            conditions.append(condition)
        if not conditions:
            raise AttestationError("approved_with_conditions requires at least one explicit condition.")
    notes = input_fn("Optional sign-off notes: ").strip()
    confirmation = {
        "approved": "APPROVE",
        "approved_with_conditions": "APPROVE_WITH_CONDITIONS",
        "rejected": "REJECT",
    }[decision]
    if input_fn(f"Type {confirmation} to record the immutable human decision: ").strip() != confirmation:
        raise AttestationError("Human sign-off confirmation did not match; nothing was signed.")
    return {
        "decision": decision,
        "decision_reason": reason,
        "conditions": conditions,
        "notes": notes,
        "human_approved": True,
    }


def find_evidence(api: GovernanceApi, evidence_type: str, reference: str) -> dict[str, Any] | None:
    query = urllib.parse.urlencode({"evidence_type": evidence_type, "limit": 200})
    response = api.get(f"/api/platform/pilot-operations/evidence?{query}")
    return next(
        (item for item in response.get("items", []) if isinstance(item, dict) and item.get("reference") == reference),
        None,
    )


def verify_persistence(
    api: GovernanceApi,
    *,
    operational_evidence: list[dict[str, Any]],
    assessment_hash: str,
    release_id: str,
    decision: str,
) -> dict[str, Any]:
    for item in operational_evidence:
        persisted = find_evidence(api, item["evidence_type"], item["reference"])
        if not persisted or persisted.get("immutable") is not True:
            raise AttestationError(f"Operational evidence was not persisted immutably: {item['reference']}")
    assessment_record = find_evidence(api, "release_assessment", assessment_hash)
    if not assessment_record or assessment_record.get("immutable") is not True:
        raise AttestationError("Release assessment was not persisted immutably.")
    if assessment_from_record(assessment_record).get("assessment_hash") != assessment_hash:
        raise AttestationError("Persisted release assessment hash does not match the submitted assessment.")
    sign_off_record = find_evidence(api, "pilot_sign_off", release_id)
    stored_sign_off = ((sign_off_record or {}).get("evidence_metadata") or {}).get("sign_off") or {}
    if not sign_off_record or sign_off_record.get("immutable") is not True:
        raise AttestationError("Human sign-off was not persisted immutably.")
    if stored_sign_off.get("assessment_hash") != assessment_hash or stored_sign_off.get("decision") != decision:
        raise AttestationError("Persisted human sign-off does not match the submitted decision.")
    dashboard = api.get("/api/platform/pilot-operations")
    expected_state = decision.upper()
    if (dashboard.get("overview") or {}).get("pilot_approval_state") != expected_state:
        raise AttestationError("Pilot Operations dashboard does not reflect the persisted sign-off.")
    return {
        "operational_evidence_verified": len(operational_evidence),
        "assessment_record_id": assessment_record.get("id"),
        "sign_off_record_id": sign_off_record.get("id"),
        "pilot_approval_state": expected_state,
        "verified_at": utc_now(),
    }


def write_reports(output_dir: Path, release_id: str, report: dict[str, Any]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir, 0o700)
    json_path = output_dir / f"{release_id}-attestation.json"
    markdown_path = output_dir / f"{release_id}-attestation.md"
    assessment = report["assessment"]
    sign_off = report["sign_off"]
    dimensions = assessment.get("dimensions") or []
    evidence = report.get("operational_evidence") or []
    markdown = "\n".join([
        f"# Pilot Release Attestation: {release_id}",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Production phase: `{assessment.get('build_phase')}`",
        f"- Production commit: `{assessment.get('git_commit')}`",
        f"- Assessment: **{str(assessment.get('assessment_status', 'unknown')).upper()}**",
        f"- Assessment hash: `{assessment.get('assessment_hash')}`",
        f"- Human decision: **{str(sign_off.get('decision', 'unknown')).upper()}**",
        f"- Rollback reference: `{sign_off.get('rollback_reference')}`",
        f"- Persistence verification: **{report['persistence_verification']['pilot_approval_state']}**",
        "",
        "## Evidence",
        "",
        *(f"- `{item.get('reference')}`: {item.get('evidence_type')} / {item.get('status')}" for item in evidence),
        "",
        "## Assessment Dimensions",
        "",
        *(f"- `{item.get('key')}`: **{str(item.get('status', 'unknown')).upper()}**" for item in dimensions),
        "",
        "## Human Decision",
        "",
        sign_off.get("decision_reason") or "No decision reason recorded.",
        "",
        "### Conditions",
        "",
        *(f"- {condition}" for condition in sign_off.get("conditions") or ["None"]),
        "",
        "### Notes",
        "",
        sign_off.get("notes") or "None.",
        "",
        "This report records governance metadata only. It does not deploy, migrate, restore, or approve automatically.",
        "",
    ])
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_dir, delete=False) as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        json_temp = Path(handle.name)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_dir, delete=False) as handle:
        handle.write(markdown)
        markdown_temp = Path(handle.name)
    os.chmod(json_temp, 0o600)
    os.chmod(markdown_temp, 0o600)
    json_temp.replace(json_path)
    markdown_temp.replace(markdown_path)
    return json_path, markdown_path


def run_attestation(
    *,
    api: GovernanceApi,
    bundle: dict[str, Any],
    email: str,
    password: str,
    output_dir: Path,
    input_fn: Callable[[str], str] = input,
) -> tuple[Path, Path]:
    identity = authenticate_owner(api, email, password)
    health = api.get("/api/health")
    dashboard_before = api.get("/api/platform/pilot-operations")
    production_evidence = dict(bundle["production_evidence"])
    if health.get("ok") is not True or health.get("phase") != production_evidence.get("production_phase"):
        raise AttestationError("Production phase evidence does not match the current health response.")
    current = dashboard_before.get("release_assessment") or {}
    print(
        "Current persisted assessment: "
        f"{current.get('assessment_status', 'unknown')} "
        f"({len(current.get('blocking_items') or [])} blockers, {len(current.get('warnings') or [])} warnings)"
    )

    recorded = record_operational_evidence(api, bundle["operational_evidence"])
    require_referenced_evidence(api, production_evidence, recorded)
    production_evidence["verified_at"] = utc_now()
    production_evidence["verified_by_role"] = identity["role"]
    assessment_response = api.post(
        "/api/platform/pilot-operations/release-assessments", production_evidence
    )
    assessment_record = assessment_response.get("assessment_evidence")
    assessment = assessment_from_record(assessment_record or {})
    assessment_hash = assessment.get("assessment_hash")
    if not isinstance(assessment_hash, str) or len(assessment_hash) != 64:
        raise AttestationError("Release assessment did not return a valid persisted assessment hash.")

    decision = prompt_human_sign_off(assessment, input_fn=input_fn)
    context = bundle["sign_off_context"]
    sign_off_payload = {
        "release_id": context["release_id"],
        "target_phase": production_evidence["production_phase"],
        "approved_by_role": identity["role"],
        "approved_at": utc_now(),
        "assessment_hash": assessment_hash,
        "rollback_reference": context["rollback_reference"],
        **decision,
    }
    sign_off_response = api.post(
        "/api/platform/pilot-operations/pilot-sign-offs", sign_off_payload
    )
    sign_off_record = sign_off_response.get("sign_off")
    if not isinstance(sign_off_record, dict):
        raise AttestationError("Human sign-off response is invalid.")
    persistence = verify_persistence(
        api,
        operational_evidence=recorded,
        assessment_hash=assessment_hash,
        release_id=context["release_id"],
        decision=decision["decision"],
    )
    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "governance_api": api.base_url,
        "authenticated_role": identity["role"],
        "health": {"ok": health.get("ok"), "phase": health.get("phase")},
        "assessment_before": current,
        "operational_evidence": recorded,
        "assessment": assessment,
        "sign_off": sign_off_payload,
        "persistence_verification": persistence,
        "safety": {
            "automatic_approval": False,
            "deployment_performed": False,
            "backup_or_restore_performed": False,
            "credentials_exported": False,
        },
    }
    return write_reports(output_dir, context["release_id"], report)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Record a governed Phase 57 pilot release assessment and explicit Platform Owner sign-off."
    )
    value.add_argument("--base-url", default=os.getenv("AEROASSIST_BASE_URL", "https://avio.my"))
    value.add_argument("--evidence-file", required=True, type=Path)
    value.add_argument("--output-dir", required=True, type=Path)
    value.add_argument("--email", default=os.getenv("AEROASSIST_PLATFORM_EMAIL", ""))
    value.add_argument("--timeout", type=int, default=30)
    return value


def main() -> int:
    args = parser().parse_args()
    try:
        bundle = load_evidence_bundle(args.evidence_file)
        email = args.email.strip() or input("Platform Owner email: ").strip()
        if not email:
            raise AttestationError("Platform Owner email is required.")
        password = os.getenv("AEROASSIST_PLATFORM_PASSWORD") or getpass.getpass("Platform Owner password: ")
        if not password:
            raise AttestationError("Platform Owner password is required.")
        api = GovernanceApi(args.base_url, timeout=args.timeout)
        json_report, markdown_report = run_attestation(
            api=api,
            bundle=bundle,
            email=email,
            password=password,
            output_dir=args.output_dir,
        )
        print(f"PASS: Phase 57 attestation persisted and verified.")
        print(f"JSON report: {json_report}")
        print(f"Markdown report: {markdown_report}")
        return 0
    except AttestationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
