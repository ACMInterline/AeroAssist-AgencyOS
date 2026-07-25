#!/usr/bin/env python3
"""Static integration, routing, safety, and release-contract validation."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("AEROASSIST_DB_MODE", "memory")
os.environ.setdefault("DEMO_AUTH_ENABLED", "false")
os.environ.setdefault("SEED_ON_STARTUP", "false")
os.environ.setdefault("READINESS_PUBLIC_MODE", "summary")

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from phase_assertions import application_phase_is_at_least
from server import app
from services.product_experience_recovery_service import (
    product_experience_recovery_readiness_metadata,
)


MINIMUM_PHASE = "phase_59_0_product_experience_recovery"
REQUIRED_REPORTS = [
    "docs/stabilization/full-system-stabilization-report.md",
    "docs/stabilization/frontend-performance-report.md",
    "docs/stabilization/browser-acceptance-contract.md",
    "docs/stabilization/accessibility-findings.md",
    "docs/stabilization/security-stabilization-review.md",
    "docs/stabilization/compatibility-retirement-register.md",
    "docs/stabilization/release-candidate-gap-register.md",
]


def read(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.is_file(), f"Missing stabilization source: {relative_path}"
    return path.read_text(encoding="utf-8")


def require(relative_path: str, markers: list[str]) -> None:
    source = read(relative_path)
    for marker in markers:
        assert marker in source, f"{relative_path} missing {marker!r}"


def validate_backend_routes() -> int:
    route_pairs: list[tuple[str, str]] = []
    for route in app.routes:
        path = getattr(route, "path", "")
        for method in sorted(getattr(route, "methods", set()) - {"HEAD", "OPTIONS"}):
            route_pairs.append((method, path))
    duplicates = [pair for pair, count in Counter(route_pairs).items() if count > 1]
    assert not duplicates, f"Duplicate backend method/path routes: {duplicates[:10]}"
    assert not any(path.startswith(("/api/admin", "/api/agent")) for _, path in route_pairs)
    return len(route_pairs)


def validate_frontend_routes() -> tuple[int, int]:
    app_source = read("frontend/src/App.jsx")
    route_source = read("frontend/src/routes/RoutedApplication.jsx")
    assert 'lazy(() => import("./routes/RoutedApplication"))' in app_source
    assert "ApplicationErrorBoundary" in app_source
    assert "<Suspense" in app_source
    assert not re.search(r'^import .+ from "\.\./pages/', route_source, re.MULTILINE)
    lazy_pages = re.findall(
        r'^const \w+ = lazy\(\(\) => import\("\.\./pages/',
        route_source,
        re.MULTILINE,
    )
    assert len(lazy_pages) >= 300
    assert "NotFoundPage" in route_source
    assert "|| HomePage" not in route_source
    route_paths = set(re.findall(r'"(/(?:platform|agency|portal)[^"]*)"', route_source))
    assert not any(path.startswith(("/admin", "/agent")) for path in route_paths)
    return len(route_paths), len(lazy_pages)


def validate_security_and_errors() -> None:
    require(
        "frontend/src/lib/api.js",
        [
            "DEFAULT_STATUS_MESSAGES",
            "UNSAFE_ERROR_PATTERN",
            "X-Correlation-ID",
            "responseError(response, data)",
            "validation_error",
            "throttled",
        ],
    )
    require(
        "frontend/src/components/ApplicationErrorBoundary.jsx",
        [
            "getDerivedStateFromError",
            "Your existing work has not been changed.",
            "window.location.reload()",
        ],
    )
    require(
        "backend/services/portal_projection_service.py",
        [
            "_portal_upload_content_type",
            "MAX_UPLOAD_BYTES",
            "DOCUMENT_CONTENT_MISMATCH",
            "DOCUMENT_UPLOAD_NOT_REQUESTED",
            "Path(str(payload.get",
        ],
    )
    server = read("backend/server.py")
    audit_source = server[server.index('@app.get("/api/audit-events"') :]
    next_route = audit_source.find("\n\n@app.", 1)
    next_router_registration = audit_source.find("\n\napp.include_router", 1)
    boundaries = [
        boundary
        for boundary in (next_route, next_router_registration)
        if boundary >= 0
    ]
    if boundaries:
        audit_source = audit_source[: min(boundaries)]
    assert "require_platform_role" in audit_source
    require(
        "frontend/src/context/AuthorizationContext.jsx",
        [
            "An active Agency membership is required.",
            "portalAccess",
            "passengerPortalPathAllowed",
        ],
    )
    require(
        "backend/services/governed_automation_contract.py",
        [
            "Class D action is prohibited",
        ],
    )


def validate_query_and_integrity_contracts() -> None:
    require(
        "backend/persistence_query.py",
        [
            '"operational_work_items"',
            '"source_entity_id"',
            "DEFAULT_QUERY_LIMIT",
            "MAXIMUM_QUERY_LIMIT",
        ],
    )
    require(
        "backend/scripts/validate_canonical_lifecycle_integrity.py",
        [
            "run_golden_path",
            "no duplicate active acceptance",
            "no unresolved fake PassengerProfile",
        ],
    )
    require(
        "backend/scripts/smoke_agent_work_queue_assignment_foundation.py",
        [
            "Governed source-entity work queue filtering failed.",
            "source_entity_id",
        ],
    )
    require(
        "backend/scripts/smoke_canonical_request_v4.py",
        [
            "passenger_context_notes",
            "non-canonical notes field",
        ],
    )


def validate_browser_contract() -> int:
    package = json.loads(read("frontend/package.json"))
    assert "@playwright/test" not in (package.get("dependencies") or {})
    assert "@playwright/test" in (package.get("devDependencies") or {})
    assert package.get("scripts", {}).get("test:e2e") == "playwright test"
    browser = read("frontend/tests/e2e/full-system-acceptance.spec.js")
    steps = len(re.findall(r'test\.step\("', browser))
    assert steps >= 35
    for marker in [
        "Cross-Agency record access is rejected",
        "Read-only Agency user cannot mutate",
        "Internal Offer notes are not exposed to Portal",
        "Revoked Portal mapping loses access",
        "Browser journey has no uncaught page errors",
    ]:
        assert marker in browser
    return steps


def validate_documentation() -> None:
    for relative_path in REQUIRED_REPORTS:
        require(relative_path, ["Status", "Evidence"])
    for relative_path in [
        "README.md",
        "BUILD_PHASES.md",
        "docs/architecture/canonical-domain-ownership-map.md",
        "docs/architecture/canonical-domain-migration-register.md",
        "docs/architecture/canonical-route-policy.md",
        "docs/architecture/current-model-inventory.md",
        "docs/product/aeroassist-product-standards.md",
        "docs/pilot/pilot-acceptance-checklist.md",
    ]:
        require(relative_path, ["Product Recovery 11B"])


def main() -> int:
    assert application_phase_is_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE)
    backend_routes = validate_backend_routes()
    frontend_routes, lazy_pages = validate_frontend_routes()
    validate_security_and_errors()
    validate_query_and_integrity_contracts()
    browser_steps = validate_browser_contract()
    validate_documentation()

    metadata = product_experience_recovery_readiness_metadata()
    for key in [
        "full_system_stabilization_review_enabled",
        "browser_acceptance_contract_enabled",
        "accessibility_source_validation_enabled",
        "safe_application_error_boundary_enabled",
        "initial_javascript_payload_reduction_target_met",
    ]:
        assert metadata.get(key) is True, key
    assert metadata.get("readiness_required") is False

    print(
        "Full-system stabilization validation passed: "
        f"{backend_routes} backend method/path routes, "
        f"{frontend_routes} frontend route strings, "
        f"{lazy_pages} lazy page imports, {browser_steps} browser checks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
