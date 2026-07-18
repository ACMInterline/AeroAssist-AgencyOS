#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run bounded repository or complete disposable pilot-release validation."
    )
    parser.add_argument("--profile", choices=("quick", "full"), default="quick")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--port", type=int, default=18084)
    parser.add_argument("--include-docker-config", action="store_true")
    return parser.parse_args()


class ValidationOrchestrator:
    def __init__(self, *, profile: str, port: int, include_docker_config: bool) -> None:
        self.profile = profile
        self.port = port
        self.include_docker_config = include_docker_config
        self.results: list[dict[str, Any]] = []
        self.backend_process: subprocess.Popen[str] | None = None
        self.backend_log_handle: Any = None
        self.temp_directory = tempfile.TemporaryDirectory(prefix="aeroassist-release-validation-")
        self.temp_root = Path(self.temp_directory.name)

    def run_stage(
        self,
        name: str,
        command: list[str],
        *,
        expected_exit_codes: tuple[int, ...] = (0,),
        environment: dict[str, str] | None = None,
    ) -> bool:
        print(f"RUN  {name}", flush=True)
        started_at = utc_timestamp()
        started = time.monotonic()
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            check=False,
        )
        passed = result.returncode in expected_exit_codes
        stage = {
            "name": name,
            "status": "passed" if passed else "failed",
            "exit_code": result.returncode,
            "started_at": started_at,
            "completed_at": utc_timestamp(),
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        self.results.append(stage)
        print(f"{'PASS' if passed else 'FAIL'} {name}", flush=True)
        return passed

    def start_backend(self, label: str) -> bool:
        self.stop_backend()
        log_path = self.temp_root / f"{label}-backend.log"
        self.backend_log_handle = log_path.open("w", encoding="utf-8")
        base_url = f"http://127.0.0.1:{self.port}"
        environment = {
            **os.environ,
            "APP_ENV": "development",
            "AEROASSIST_DB_MODE": "memory",
            "DEMO_AUTH_ENABLED": "true",
            "SEED_ON_STARTUP": "true",
            "SEED_ENDPOINT_ENABLED": "true",
            "READINESS_PUBLIC_MODE": "detailed",
            "READINESS_AUTHENTICATED_DETAIL_ENABLED": "true",
            "READINESS_INTERNAL_ENABLED": "true",
            "DOCUMENT_EXPORT_STORAGE_DIR": str(self.temp_root / "document-exports"),
            "AEROASSIST_SMOKE_BASE_URL": base_url,
            "SMOKE_BASE_URL": base_url,
            "AEROASSIST_BASE_URL": base_url,
        }
        (self.temp_root / "document-exports").mkdir(parents=True, exist_ok=True)
        self.backend_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--no-access-log",
            ],
            cwd=BACKEND,
            env=environment,
            stdout=self.backend_log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        started_at = utc_timestamp()
        started = time.monotonic()
        healthy = False
        for _ in range(60):
            if self.backend_process.poll() is not None:
                break
            try:
                with urlopen(f"{base_url}/api/health", timeout=2) as response:
                    healthy = response.status == 200
                if healthy:
                    break
            except OSError:
                time.sleep(0.5)
        self.results.append(
            {
                "name": f"{label}_backend_startup",
                "status": "passed" if healthy else "failed",
                "exit_code": 0 if healthy else 1,
                "started_at": started_at,
                "completed_at": utc_timestamp(),
                "duration_seconds": round(time.monotonic() - started, 3),
            }
        )
        print(f"{'PASS' if healthy else 'FAIL'} {label} backend startup", flush=True)
        return healthy

    def stop_backend(self) -> None:
        if self.backend_process is not None and self.backend_process.poll() is None:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                self.backend_process.wait(timeout=5)
        self.backend_process = None
        if self.backend_log_handle is not None:
            self.backend_log_handle.close()
            self.backend_log_handle = None

    def run(self) -> dict[str, Any]:
        started_at = utc_timestamp()
        python = sys.executable
        stages = (
            ("git_diff_check", ["git", "diff", "--check"]),
            ("backend_compile", [python, "-m", "compileall", "-q", "backend"]),
            ("smoke_inventory_validator", [python, "backend/scripts/validate_smoke_inventory.py"]),
            ("ci_validator", [python, "backend/scripts/validate_ci_foundation.py"]),
            ("persistence_validator", [python, "backend/scripts/validate_persistence_query_foundation.py"]),
            ("observability_validator", [python, "backend/scripts/validate_observability_foundation.py"]),
            ("release_gate_validator", [python, "backend/scripts/validate_final_stabilization_pilot_release_gate.py"]),
            ("release_gate_static_smoke", [python, "backend/scripts/smoke_final_stabilization_pilot_release_gate.py", "--static"]),
            ("pilot_operations_static_smoke", [python, "backend/scripts/smoke_pilot_operations_release_readiness.py", "--static"]),
        )
        for name, command in stages:
            self.run_stage(name, command)

        self.run_stage(
            "release_assessment_expected_blocked",
            [
                python,
                "backend/scripts/assess_pilot_release_readiness.py",
                "--output",
                str(self.temp_root / "blocked-assessment.json"),
            ],
            expected_exit_codes=(1,),
        )

        if self.profile == "full":
            self.run_stage("frontend_build", ["npm", "run", "build", "--prefix", "frontend"])
            self.run_stage(
                "backend_free_smoke_inventory",
                [python, "backend/scripts/run_smoke_inventory.py", "--isolation", "none", "--result-json", str(self.temp_root / "none.json")],
            )
            shared_ready = self.start_backend("shared")
            if shared_ready:
                self.run_stage(
                    "shared_backend_smoke_inventory",
                    [python, "backend/scripts/run_smoke_inventory.py", "--isolation", "shared_backend", "--result-json", str(self.temp_root / "shared.json")],
                    environment={**os.environ, "AEROASSIST_SMOKE_BASE_URL": f"http://127.0.0.1:{self.port}"},
                )
            self.stop_backend()
            fresh_ready = self.start_backend("fresh")
            if fresh_ready:
                self.run_stage(
                    "fresh_backend_smoke_inventory",
                    [python, "backend/scripts/run_smoke_inventory.py", "--isolation", "fresh_backend", "--result-json", str(self.temp_root / "fresh.json")],
                    environment={**os.environ, "AEROASSIST_SMOKE_BASE_URL": f"http://127.0.0.1:{self.port}"},
                )
            self.stop_backend()

        if self.include_docker_config:
            self.run_stage(
                "production_compose_config",
                [
                    "docker", "compose", "--env-file", ".env.production.example",
                    "-f", "docker-compose.production.yml", "config", "--quiet",
                ],
                environment={**os.environ, "AEROASSIST_ENV_FILE": ".env.production.example"},
            )

        failed = sum(1 for item in self.results if item["status"] == "failed")
        return {
            "schema_version": 1,
            "profile": self.profile,
            "environment_scope": "disposable",
            "started_at": started_at,
            "completed_at": utc_timestamp(),
            "status": "failed" if failed else "passed",
            "stage_count": len(self.results),
            "passed_stage_count": len(self.results) - failed,
            "failed_stage_count": failed,
            "production_access_performed": False,
            "deployment_performed": False,
            "stages": self.results,
        }

    def close(self) -> None:
        self.stop_backend()
        self.temp_directory.cleanup()


def main() -> int:
    args = parse_args()
    orchestrator = ValidationOrchestrator(
        profile=args.profile,
        port=args.port,
        include_docker_config=args.include_docker_config,
    )
    try:
        report = orchestrator.run()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "stages"}, sort_keys=True))
        return 1 if report["status"] == "failed" else 0
    finally:
        orchestrator.close()


if __name__ == "__main__":
    raise SystemExit(main())
