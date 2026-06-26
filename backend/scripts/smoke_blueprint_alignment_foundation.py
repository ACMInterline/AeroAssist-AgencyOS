#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
EXPECTED_PHASE = "phase_35_trip_dossier_foundation"


def request(method: str, path: str, body: dict | None = None, expect: int | None = None) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", method=method, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = response.read().decode("utf-8")
            status = response.status
            result = json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        status = exc.code
        result = json.loads(payload) if payload else {}
    if expect is not None and status != expect:
        raise AssertionError(f"{method} {path} expected {expect}, got {status}: {result}")
    if expect is None and status >= 400:
        raise AssertionError(f"{method} {path} failed with {status}: {result}")
    return status, result


def get(path: str) -> dict:
    return request("GET", path)[1]


def main() -> int:
    from models import (  # noqa: F401
        AccountOriginAtSubmission,
        PassengerLinkMode,
        RequestCaseFlag,
        RequestPassengerSegmentService,
        RequestPet,
        RequestPetSegmentTransport,
        RequestSpecialItem,
        RequestSpecialItemSegment,
        SubmissionChannel,
        TripDossier,
        TripPassenger,
        TripSegment,
    )

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    readiness = get("/api/readiness")
    alignment = readiness.get("blueprint_alignment") or {}
    for key in [
        "blueprint_alignment_documented",
        "canonical_operations_model_documented",
        "current_model_inventory_documented",
        "trip_dossier_foundation_ready",
        "reference_data_phase_ready",
    ]:
        if alignment.get(key) is not True:
            raise AssertionError(f"Readiness missing blueprint alignment flag: {key}")
    for path in [
        "docs/architecture/agencyos-blueprint-alignment-gap-map.md",
        "docs/architecture/canonical-operations-model.md",
        "docs/architecture/current-model-inventory.md",
        "PHASE_32_BLUEPRINT_ALIGNMENT_CANONICAL_OPERATIONS_MODEL.md",
    ]:
        if not Path(path).exists():
            raise AssertionError(f"Missing Phase 32 document: {path}")
    print("Blueprint alignment foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Blueprint alignment foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
