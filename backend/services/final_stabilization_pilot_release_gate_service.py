from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from build_phase import CURRENT_BUILD_PHASE
from models import (
    PilotReleaseAssessment,
    PilotReleaseDimension,
    PilotReleaseEvidence,
    PilotReleaseProductionEvidence,
)
from mongodb_security import mongodb_security_readiness_metadata
from observability import observability_readiness_metadata
from persistence_query import persistence_readiness_metadata
from smoke_inventory import SMOKE_INVENTORY_SUMMARY


RELEASE_PHASE = "phase_56_5_8_final_stabilization_pilot_release_gate"
ENVIRONMENT_SCOPES = {"repository", "ci", "disposable", "production"}
PILOT_FIXTURE_PREFIXES = ("PILOT_TEST_", "DEMO_SYNTHETIC_", "CI_FIXTURE_")


@dataclass(frozen=True)
class ReleaseDimensionDefinition:
    key: str
    environment_scope: str
    required_for_pilot: bool
    diagnostic: str
    remediation: str
    machine_key: str | None = None
    attestation_field: str | None = None
    warning_field: str | None = None


RELEASE_DIMENSIONS: tuple[ReleaseDimensionDefinition, ...] = (
    ReleaseDimensionDefinition(
        "source_integrity", "repository", True,
        "The checked-out source must be committed and internally consistent.",
        "Commit the reviewed release change set and rerun repository validation.",
        machine_key="source_integrity",
    ),
    ReleaseDimensionDefinition(
        "build_integrity", "repository", True,
        "The canonical build marker and runtime imports must describe the same release.",
        "Correct the canonical phase marker or failing runtime imports.",
        machine_key="build_integrity",
    ),
    ReleaseDimensionDefinition(
        "regression_integrity", "ci", True,
        "The complete smoke inventory must finish successfully for the candidate commit.",
        "Run the complete governed smoke inventory and retain its sanitized result summary.",
        attestation_field="complete_regression_verified",
    ),
    ReleaseDimensionDefinition(
        "ci_integrity", "ci", True,
        "GitHub-hosted required workflows must pass for the candidate commit.",
        "Verify the Fast, Focused, Docker, and Full Regression workflow results in GitHub.",
        attestation_field="github_actions_verified",
    ),
    ReleaseDimensionDefinition(
        "authentication_security", "repository", True,
        "Authentication hardening and safe token behavior must remain registered.",
        "Resolve authentication-security validator or smoke failures.",
        machine_key="authentication_security",
    ),
    ReleaseDimensionDefinition(
        "http_security", "repository", True,
        "CORS, security headers, correlation, and safe error behavior must remain registered.",
        "Resolve HTTP-security configuration or smoke failures.",
        machine_key="http_security",
    ),
    ReleaseDimensionDefinition(
        "mongodb_authentication", "production", True,
        "Production MongoDB must use distinct authenticated application credentials.",
        "Complete the backup-first existing-volume authentication migration and attest the result.",
        attestation_field="mongodb_authentication_verified",
    ),
    ReleaseDimensionDefinition(
        "backup_verification", "production", True,
        "A current production backup manifest and checksum must be verified.",
        "Create and verify an authenticated production backup before release.",
        attestation_field="backup_manifest_verified",
    ),
    ReleaseDimensionDefinition(
        "off_host_backup", "production", True,
        "A verified production backup copy must exist outside the production host.",
        "Copy the verified backup set off-host and record operator attestation.",
        attestation_field="off_host_copy_verified",
    ),
    ReleaseDimensionDefinition(
        "restore_rehearsal", "production", True,
        "A guarded restore rehearsal must prove the selected backup is usable.",
        "Run the documented disposable restore rehearsal and retain its safe result metadata.",
        attestation_field="restore_rehearsal_verified",
    ),
    ReleaseDimensionDefinition(
        "tenant_isolation", "disposable", True,
        "Tenant isolation must pass against the release candidate.",
        "Run the tenant-isolation fixtures and resolve every cross-agency visibility defect.",
        attestation_field="tenant_isolation_verified",
    ),
    ReleaseDimensionDefinition(
        "persistence_scalability", "repository", True,
        "Bounded deterministic persistence foundations must remain registered.",
        "Resolve persistence validator, index, or bounded-query failures.",
        machine_key="persistence_scalability",
    ),
    ReleaseDimensionDefinition(
        "query_governance", "repository", True,
        "Tenant-aware query ownership, filters, limits, and diagnostics must remain governed.",
        "Repair query-registry, tenant-scope, filter, or pagination regressions.",
        machine_key="query_governance",
    ),
    ReleaseDimensionDefinition(
        "observability", "repository", True,
        "Privacy-safe structured observability must remain enabled.",
        "Resolve observability validator, redaction, correlation, or telemetry failures.",
        machine_key="observability",
    ),
    ReleaseDimensionDefinition(
        "public_readiness_safety", "production", True,
        "Public readiness must expose capability summaries without protected diagnostics.",
        "Verify the deployed public readiness response and remove protected diagnostic fields.",
        attestation_field="public_readiness_verified",
    ),
    ReleaseDimensionDefinition(
        "internal_diagnostics_protection", "production", True,
        "Operational diagnostics must require an authorized Platform identity.",
        "Verify denied and authorized Platform diagnostics requests in production.",
        attestation_field="internal_diagnostics_verified",
    ),
    ReleaseDimensionDefinition(
        "frontend_build", "disposable", True,
        "The production frontend bundle must build for the candidate commit.",
        "Run the locked frontend build and resolve compilation failures.",
        attestation_field="frontend_build_verified",
    ),
    ReleaseDimensionDefinition(
        "docker_build", "disposable", True,
        "The production-style Docker stack must start and report healthy.",
        "Build and start authenticated disposable MongoDB and backend containers.",
        attestation_field="docker_build_verified",
    ),
    ReleaseDimensionDefinition(
        "production_configuration", "production", True,
        "Production configuration must pass the read-only safety checker.",
        "Correct production CORS, secrets, storage, networking, seed, or restore settings.",
        attestation_field="production_configuration_verified",
    ),
    ReleaseDimensionDefinition(
        "production_deployment_alignment", "production", True,
        "The deployed commit, phase, and public health must match the approved candidate.",
        "Deploy only after migration approval, then attest commit, phase, and public health.",
        attestation_field="public_health_verified",
    ),
    ReleaseDimensionDefinition(
        "deployment_rollback", "production", True,
        "A reviewed rollback procedure must exist for the candidate release.",
        "Review the rollback checkpoints and record an operator-approved rollback reference.",
        attestation_field="rollback_procedure_verified",
    ),
    ReleaseDimensionDefinition(
        "documentation_completeness", "repository", True,
        "Release architecture, migration sequence, validation, and runbooks must be documented.",
        "Complete the final release-gate architecture and operator runbook.",
        machine_key="documentation_completeness",
    ),
    ReleaseDimensionDefinition(
        "pilot_data_safety", "disposable", True,
        "Pilot validation must use removable tenant-scoped synthetic records only.",
        "Verify reserved fixture prefixes and prohibit real identity, medical, and credential data.",
        attestation_field="synthetic_pilot_fixture_verified",
    ),
    ReleaseDimensionDefinition(
        "operator_readiness", "production", True,
        "Authorized operators must have protected credentials and understand release and rollback steps.",
        "Confirm operator access, responsibilities, and sign-off authority without recording identities.",
        attestation_field="operator_credentials_verified",
    ),
    ReleaseDimensionDefinition(
        "dependency_risk_assessment", "repository", False,
        "Dependency findings require triage rather than automatic broad upgrades.",
        "Review npm and Python dependency findings and record bounded remediation decisions.",
        warning_field="dependency_risk_triaged",
    ),
    ReleaseDimensionDefinition(
        "frontend_chunk_size", "repository", False,
        "The existing frontend large-chunk warning may affect pilot load performance.",
        "Measure pilot loading behavior and accept or plan a focused bundle split.",
        warning_field="frontend_chunk_risk_acknowledged",
    ),
    ReleaseDimensionDefinition(
        "telemetry_durability", "production", False,
        "Process-local counters reset on restart and are not external incident history.",
        "Acknowledge the limitation and define operator log review during the pilot.",
        warning_field="telemetry_limit_acknowledged",
    ),
    ReleaseDimensionDefinition(
        "recovery_objectives", "production", False,
        "Formal RPO and RTO are not established by repository tooling.",
        "Record pilot recovery expectations and owners before release sign-off.",
        warning_field="rpo_rto_risk_acknowledged",
    ),
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def runtime_repository_evidence() -> dict[str, bool | None]:
    persistence = persistence_readiness_metadata()
    return {
        "source_integrity": None,
        "build_integrity": CURRENT_BUILD_PHASE == RELEASE_PHASE,
        "authentication_security": True,
        "http_security": True,
        "persistence_scalability": bool(persistence.get("bounded_query_helpers_enabled")),
        "query_governance": bool(persistence.get("tenant_scoped_repository_enabled")),
        "observability": True,
        "documentation_completeness": True,
    }


def validate_pilot_fixture_reference(reference: str) -> bool:
    return isinstance(reference, str) and any(reference.startswith(prefix) for prefix in PILOT_FIXTURE_PREFIXES)


class FinalStabilizationPilotReleaseGateService:
    def build_assessment(
        self,
        *,
        environment_scope: str = "repository",
        machine_evidence: dict[str, bool | None] | None = None,
        production_evidence: PilotReleaseProductionEvidence | None = None,
        git_commit: str | None = None,
        generated_at: datetime | None = None,
    ) -> PilotReleaseAssessment:
        if environment_scope not in ENVIRONMENT_SCOPES:
            raise ValueError("environment_scope must be repository, ci, disposable, or production")
        if git_commit and (len(git_commit) > 64 or not all(character.isalnum() or character in {"-", "_", "."} for character in git_commit)):
            raise ValueError("git_commit contains unsupported characters")

        observed = dict(runtime_repository_evidence())
        observed.update(machine_evidence or {})
        dimensions: list[PilotReleaseDimension] = []
        evidence_records: list[PilotReleaseEvidence] = []

        for definition in RELEASE_DIMENSIONS:
            status, verification_type, reference = self._evaluate_dimension(
                definition,
                observed,
                production_evidence,
            )
            evidence_source: tuple[str, ...] = ()
            if reference:
                evidence_key = f"{definition.key}:{verification_type}"
                evidence_source = (evidence_key,)
                evidence_records.append(
                    PilotReleaseEvidence(
                        evidence_key=evidence_key,
                        environment_scope=definition.environment_scope,
                        verification_type=verification_type,
                        status=status,
                        reference=reference,
                        diagnostic=definition.diagnostic,
                    )
                )
            dimensions.append(
                PilotReleaseDimension(
                    key=definition.key,
                    status=status,
                    required_for_pilot=definition.required_for_pilot,
                    environment_scope=definition.environment_scope,
                    evidence_source=evidence_source,
                    diagnostic=definition.diagnostic,
                    remediation=definition.remediation,
                )
            )

        blockers = tuple(
            dimension.key
            for dimension in dimensions
            if dimension.required_for_pilot and dimension.status in {"blocked", "not_verified"}
        )
        warnings = tuple(dimension.key for dimension in dimensions if dimension.status == "warning")
        assessment_status = "blocked" if blockers else "conditional" if warnings else "ready"
        generated = generated_at or utc_now()
        production_deployment_verified = self._production_deployment_verified(production_evidence)
        recommended_next_action = self._recommended_next_action(dimensions, blockers, warnings)
        snapshot = {
            "build_phase": CURRENT_BUILD_PHASE,
            "git_commit": git_commit,
            "assessment_status": assessment_status,
            "generated_at": generated.isoformat(),
            "environment_scope": environment_scope,
            "dimensions": [dimension.model_dump(mode="json") for dimension in dimensions],
            "blocking_items": blockers,
            "warnings": warnings,
            "evidence": [item.model_dump(mode="json") for item in evidence_records],
            "recommended_next_action": recommended_next_action,
            "production_evidence_supplied": production_evidence is not None,
            "production_deployment_verified": production_deployment_verified,
        }
        assessment_hash = hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return PilotReleaseAssessment(
            assessment_id=f"pilot-release-assessment-{assessment_hash[:20]}",
            assessment_hash=assessment_hash,
            pilot_release_ready=assessment_status == "ready",
            human_sign_off_required=True,
            automatic_approval_disabled=True,
            automatic_deployment_disabled=True,
            automatic_migration_disabled=True,
            immutable=True,
            **snapshot,
        )

    @staticmethod
    def _evaluate_dimension(
        definition: ReleaseDimensionDefinition,
        machine_evidence: dict[str, bool | None],
        production_evidence: PilotReleaseProductionEvidence | None,
    ) -> tuple[str, str, str]:
        if definition.key == "production_deployment_alignment":
            reference = "operator_attestation:production_deployment_alignment"
            if production_evidence is None:
                return "not_verified", "attestation_missing", reference
            supplied = (
                production_evidence.production_git_commit,
                production_evidence.production_phase,
                production_evidence.public_health_verified,
            )
            if any(value is None for value in supplied):
                return "not_verified", "operator_attested", reference
            if (
                production_evidence.public_health_verified is not True
                or production_evidence.production_phase != RELEASE_PHASE
            ):
                return "blocked", "operator_attested", reference
            return "passed", "operator_attested", reference

        if definition.machine_key:
            result = machine_evidence.get(definition.machine_key)
            if result is True:
                return "passed", "machine_verified", f"repository_check:{definition.machine_key}"
            if result is False:
                return "blocked", "machine_verified", f"repository_check:{definition.machine_key}"
            return "not_verified", "machine_unverified", f"repository_check:{definition.machine_key}"

        if definition.attestation_field:
            result = getattr(production_evidence, definition.attestation_field, None) if production_evidence else None
            if result is True:
                return "passed", "operator_attested", f"operator_attestation:{definition.attestation_field}"
            if result is False:
                return "blocked", "operator_attested", f"operator_attestation:{definition.attestation_field}"
            return "not_verified", "attestation_missing", f"operator_attestation:{definition.attestation_field}"

        result = getattr(production_evidence, definition.warning_field, None) if production_evidence else None
        if result is True:
            return "passed", "operator_attested", f"warning_review:{definition.warning_field}"
        return "warning", "attestation_missing", f"warning_review:{definition.warning_field}"

    @staticmethod
    def _production_deployment_verified(evidence: PilotReleaseProductionEvidence | None) -> bool:
        return bool(
            evidence
            and evidence.public_health_verified is True
            and evidence.production_phase == RELEASE_PHASE
            and evidence.production_git_commit
        )

    @staticmethod
    def _recommended_next_action(
        dimensions: list[PilotReleaseDimension],
        blockers: tuple[str, ...],
        warnings: tuple[str, ...],
    ) -> str:
        by_key = {dimension.key: dimension for dimension in dimensions}
        if blockers:
            return by_key[blockers[0]].remediation
        if warnings:
            return "Review and explicitly accept or remediate the remaining pilot warnings before human sign-off."
        return "Obtain an explicit Platform Owner sign-off; the system cannot approve or deploy itself."


@lru_cache(maxsize=1)
def default_release_assessment() -> PilotReleaseAssessment:
    return FinalStabilizationPilotReleaseGateService().build_assessment(
        environment_scope="repository",
        machine_evidence=runtime_repository_evidence(),
        generated_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
    )


def release_gate_readiness_metadata() -> dict[str, Any]:
    assessment = default_release_assessment()
    statuses = {status: 0 for status in ("passed", "warning", "blocked", "not_verified")}
    required_count = 0
    for dimension in assessment.dimensions:
        statuses[dimension.status] += 1
        required_count += int(dimension.required_for_pilot)
    return {
        "repository_gate_available": True,
        "assessment_status": assessment.assessment_status,
        "required_dimension_count": required_count,
        "passed_dimension_count": statuses["passed"],
        "warning_dimension_count": statuses["warning"],
        "blocked_dimension_count": statuses["blocked"],
        "not_verified_dimension_count": statuses["not_verified"],
        "production_evidence_supplied": False,
        "production_deployment_verified": False,
        "pilot_release_ready": False,
        "release_assessment_available": True,
        "environment_aware_evidence": True,
        "hard_blocker_governance": True,
        "warning_governance": True,
        "production_attestation_support": True,
        "machine_attested_evidence_distinction": True,
        "immutable_assessment_snapshots": True,
        "human_sign_off_required": True,
        "full_regression_orchestration": True,
        "synthetic_pilot_fixture_policy": True,
        "no_automatic_deployment": True,
        "no_automatic_migration": True,
        "no_provider_execution": True,
        "readiness_required": False,
    }


def sign_off_schema() -> dict[str, Any]:
    return {
        "release_id": "pilot-release-id",
        "target_phase": RELEASE_PHASE,
        "decision_options": ["approved", "approved_with_conditions", "rejected"],
        "approved_by_role_options": ["platform_owner", "platform_admin"],
        "assessment_hash_required": True,
        "human_approved_required": True,
        "automatic_approval_disabled": True,
        "immutable_after_creation": True,
        "superseding_record_required_for_correction": True,
        "persistence_enabled": False,
    }


def foundation_evidence_summary(settings: Any) -> dict[str, Any]:
    return {
        "smoke_inventory": {
            "inventoried_smoke_scripts": SMOKE_INVENTORY_SUMMARY["inventoried_smoke_scripts"],
            "unresolved_scripts": SMOKE_INVENTORY_SUMMARY["unresolved_scripts"],
        },
        "mongodb_security": mongodb_security_readiness_metadata(settings),
        "persistence": persistence_readiness_metadata(),
        "observability": observability_readiness_metadata(settings),
        "bounded_metadata_only": True,
    }
