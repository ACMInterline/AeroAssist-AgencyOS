#!/usr/bin/env python3
"""Source-level accessibility acceptance for Product Recovery stabilization."""

from __future__ import annotations

import re
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
FRONTEND = ROOT / "frontend" / "src"


def read(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.is_file(), f"Missing accessibility source: {relative_path}"
    return path.read_text(encoding="utf-8")


def require(relative_path: str, markers: list[str]) -> None:
    source = read(relative_path)
    for marker in markers:
        assert marker in source, f"{relative_path} missing accessibility marker {marker!r}"


def main() -> int:
    require(
        "frontend/src/styles.css",
        [
            ".aa-skip-link",
            ":focus-visible",
            "prefers-reduced-motion",
        ],
    )
    for layout in [
        "frontend/src/layouts/PlatformLayout.jsx",
        "frontend/src/layouts/AgencyLayout.jsx",
        "frontend/src/layouts/ClientPortalLayout.jsx",
    ]:
        require(layout, ['href="#main-content"', 'id="main-content"'])

    require(
        "frontend/src/components/LoadingState.jsx",
        ['aria-live="polite"', 'role="status"'],
    )
    require("frontend/src/components/ErrorState.jsx", ['role="alert"'])
    require(
        "frontend/src/components/ProductTable.jsx",
        ["<caption", 'scope="col"', "aria-sort"],
    )
    require(
        "frontend/src/pages/auth/LoginPage.jsx",
        [
            'autoComplete="email"',
            '"current-password"',
            'role="status"',
            'role="alert"',
            "required",
        ],
    )
    require(
        "frontend/src/components/NotFoundPage.jsx",
        [">Page not found</h1>", 'id="main-content"'],
    )
    require(
        "frontend/src/hooks/useDialogFocus.js",
        [
            'event.key === "Escape"',
            'event.key !== "Tab"',
            "previousFocus?.focus?.()",
        ],
    )

    dialog_sources = []
    for path in FRONTEND.rglob("*.jsx"):
        source = path.read_text(encoding="utf-8")
        if 'role="dialog"' not in source and 'role="alertdialog"' not in source:
            continue
        relative = str(path.relative_to(ROOT))
        dialog_sources.append(relative)
        for marker in [
            "useDialogFocus",
            'aria-modal="true"',
            'tabIndex="-1"',
        ]:
            assert marker in source, f"{relative} lacks governed dialog marker {marker!r}"
        assert "aria-label=" in source or "aria-labelledby=" in source, (
            f"{relative} dialog has no accessible name"
        )

    assert len(dialog_sources) == 5, (
        f"Review new dialog sources before approval; expected 5, found {len(dialog_sources)}"
    )

    status_badge = read("frontend/src/components/StatusBadge.jsx")
    assert "children" in status_badge or "label" in status_badge or "replaceAll" in status_badge

    browser = read("frontend/tests/e2e/full-system-acceptance.spec.js")
    assert len(re.findall(r'test\.step\("', browser)) >= 35
    for marker in [
        "Shared page search restores keyboard focus",
        "toBeFocused()",
        'page.keyboard.press("Escape")',
        "Browser journey has no uncaught page errors",
    ]:
        assert marker in browser, f"Browser accessibility acceptance missing {marker!r}"

    print(
        "Stabilization accessibility source validation passed: "
        f"{len(dialog_sources)} governed dialogs plus keyboard-assisted browser coverage."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
