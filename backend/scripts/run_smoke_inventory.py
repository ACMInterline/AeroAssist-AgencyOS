#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from smoke_inventory import load_smoke_inventory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run checked-in AeroAssist smoke inventory entries.")
    parser.add_argument("--focused-only", action="store_true")
    parser.add_argument("--ci-suitable-only", action="store_true")
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--script", action="append", default=[])
    parser.add_argument("--requires-backend", choices=("yes", "no"))
    parser.add_argument("--tier", action="append", choices=("static", "focused", "integration", "full_only"), default=[])
    parser.add_argument("--isolation", action="append", choices=("none", "shared_backend", "fresh_backend"), default=[])
    parser.add_argument("--result-json", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def skip_reason(entry: dict, args: argparse.Namespace) -> str | None:
    if args.focused_only and entry["test_class"] != "focused":
        return "not a focused smoke"
    if args.ci_suitable_only and not entry["suitable_for_future_ci"]:
        return "not marked suitable for future CI"
    if args.scope and not set(args.scope).intersection(entry["scope"]):
        return f"scope does not match {args.scope}"
    if args.script and entry["script_path"] not in args.script and Path(entry["script_path"]).name not in args.script:
        return "not selected by --script"
    if args.requires_backend == "yes" and not entry["requires_running_backend"]:
        return "does not require a running backend"
    if args.requires_backend == "no" and entry["requires_running_backend"]:
        return "requires a running backend"
    if args.tier and entry["ci_tier"] not in args.tier:
        return f"CI tier does not match {args.tier}"
    if args.isolation and entry["execution_isolation"] not in args.isolation:
        return f"execution isolation does not match {args.isolation}"
    return None


def main() -> int:
    args = parse_args()
    entries = load_smoke_inventory()["scripts"]
    passed = failed = skipped = selected = executed = 0
    results: list[dict] = []
    for entry in entries:
        reason = skip_reason(entry, args)
        if reason:
            skipped += 1
            print(f"SKIP {entry['script_path']}: {reason}", flush=True)
            results.append({"script_path": entry["script_path"], "status": "skipped", "reason": reason})
            continue
        selected += 1
        print(f"RUN  {entry['script_path']}", flush=True)
        if args.dry_run:
            skipped += 1
            print(f"SKIP {entry['script_path']}: dry run", flush=True)
            results.append({"script_path": entry["script_path"], "status": "skipped", "reason": "dry run"})
            continue
        executed += 1
        started = time.monotonic()
        result = subprocess.run([sys.executable, str(ROOT / entry["script_path"])], cwd=ROOT, check=False)
        duration_seconds = round(time.monotonic() - started, 3)
        if result.returncode == 0:
            passed += 1
            print(f"PASS {entry['script_path']}", flush=True)
            status = "passed"
        else:
            failed += 1
            print(f"FAIL {entry['script_path']}: exit {result.returncode}", flush=True)
            status = "failed"
        results.append(
            {
                "script_path": entry["script_path"],
                "status": status,
                "exit_code": result.returncode,
                "duration_seconds": duration_seconds,
                "ci_tier": entry["ci_tier"],
                "execution_isolation": entry["execution_isolation"],
            }
        )
    summary = {
        "discovered": len(entries),
        "selected": selected,
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }
    print("Smoke summary: " + " ".join(f"{key}={value}" for key, value in summary.items()))
    if args.result_json:
        args.result_json.parent.mkdir(parents=True, exist_ok=True)
        args.result_json.write_text(
            json.dumps({"summary": summary, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
