from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from build_phase import CURRENT_BUILD_PHASE
from database import Database
from models import (
    AuditEvent,
    PilotAgencyEnrollment,
    PilotAgencyInvitationCreate,
    PilotHealthTimelineEvent,
    PilotHealthTimelineEventCreate,
    PilotOperationalEvidenceCreate,
    PilotOperationalEvidenceRecord,
    PilotReleaseProductionEvidence,
    PilotReleaseSignOff,
    PilotSyntheticDataset,
    PilotSyntheticDatasetCreate,
)
from observability import operational_diagnostics_snapshot
from persistence_query import PaginationRequest, query_diagnostic_records
from persistence_repository import PersistenceRepository
from services.final_stabilization_pilot_release_gate_service import (
    FinalStabilizationPilotReleaseGateService,
    runtime_repository_evidence,
    validate_pilot_fixture_reference,
)


PHASE_LABEL = "phase_57_0_pilot_operations_release_readiness"

PILOT_OPERATIONAL_EVIDENCE_COLLECTION = "pilot_operational_evidence"
PILOT_AGENCY_ENROLLMENTS_COLLECTION = "pilot_agency_enrollments"
PILOT_SYNTHETIC_DATASETS_COLLECTION = "pilot_synthetic_datasets"
PILOT_HEALTH_TIMELINE_COLLECTION = "pilot_health_timeline_events"

PILOT_OPERATIONS_COLLECTIONS = (
    PILOT_OPERATIONAL_EVIDENCE_COLLECTION,
    PILOT_AGENCY_ENROLLMENTS_COLLECTION,
    PILOT_SYNTHETIC_DATASETS_COLLECTION,
    PILOT_HEALTH_TIMELINE_COLLECTION,
)

EVIDENCE_TYPES = {
    "deployment",
    "smoke_run",
    "backup_verification",
    "restore_rehearsal",
    "production_validation",
    "release_assessment",
    "pilot_sign_off",
}
TIMELINE_EVENT_TYPES = {
    "deployment",
    "health",
    "readiness",
    "smoke",
    "incident",
    "backup",
    "restore",
    "pilot",
}
ASSESSMENT_STATUSES = {"PASS", "WARNING", "BLOCKED"}
ENROLLMENT_STATUSES = {"invited", "enabled", "activated", "disabled"}

CATEGORY_DIMENSIONS = {
    "infrastructure": {
        "production_deployment_alignment",
        "production_configuration",
        "docker_build",
        "deployment_rollback",
    },
    "security": {"authentication_security", "http_security", "operator_readiness"},
    "database": {"mongodb_authentication", "persistence_scalability", "query_governance"},
    "frontend": {"frontend_build"},
    "backend": {
        "source_integrity",
        "build_integrity",
        "regression_integrity",
        "documentation_completeness",
    },
    "observability": {
        "observability",
        "public_readiness_safety",
        "internal_diagnostics_protection",
    },
    "backups": {"backup_verification", "off_host_backup", "restore_rehearsal"},
    "tenant_isolation": {"tenant_isolation", "pilot_data_safety"},
}

FORBIDDEN_METADATA_KEYS = {
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "connection_string",
    "mongodb_uri",
    "passport_number",
    "payment_card",
}


class PilotOperationsError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def pilot_operations_readiness_metadata() -> dict[str, Any]:
    return {
        "pilot_readiness_dashboard_enabled": True,
        "operational_evidence_registry_enabled": True,
        "release_assessment_statuses": ["PASS", "WARNING", "BLOCKED"],
        "human_pilot_sign_off_required": True,
        "pilot_agency_enrollment_enabled": True,
        "synthetic_dataset_safety_controls_enabled": True,
        "health_timeline_enabled": True,
        "protected_production_diagnostics_enabled": True,
        "automatic_release_approval_disabled": True,
        "automatic_production_migration_disabled": True,
        "provider_execution_disabled": True,
        "readiness_required": False,
    }


class PilotOperationsReleaseReadinessService:
    def __init__(self, db: Database):
        self.db = db
        self.repository = PersistenceRepository(db)

    @staticmethod
    def safety_flags() -> dict[str, bool]:
        return {
            "automatic_release_approval_disabled": True,
            "automatic_production_migration_disabled": True,
            "provider_connectivity_disabled": True,
            "gds_execution_disabled": True,
            "payment_execution_disabled": True,
            "live_ticketing_disabled": True,
            "synthetic_records_isolated": True,
            "metadata_only": True,
        }

    async def dashboard(self) -> dict[str, Any]:
        evidence = await self.list_evidence(limit=100)
        enrollments = await self.list_enrollments()
        datasets = await self.list_synthetic_datasets(include_removed=False)
        timeline = await self.list_health_timeline(limit=50)
        latest_assessment = self._latest_assessment(evidence)
        categories = self._assessment_categories(latest_assessment)
        database_status = await self.db.readiness()

        latest = {evidence_type: self._latest_by_type(evidence, evidence_type) for evidence_type in EVIDENCE_TYPES}
        approval = latest.get("pilot_sign_off")
        smoke = latest.get("smoke_run")
        backup = latest.get("backup_verification")
        deployment = latest.get("deployment")
        production = latest.get("production_validation")
        ci_status = (smoke or {}).get("evidence_metadata", {}).get("ci_status")
        if ci_status not in ASSESSMENT_STATUSES:
            ci_status = self._dimension_status(latest_assessment, "ci_integrity")

        overview = {
            "deployment_phase": (deployment or {}).get("build_phase") or CURRENT_BUILD_PHASE,
            "health": "PASS",
            "readiness": self._normalize_assessment_status(latest_assessment.get("assessment_status")),
            "database": "PASS" if database_status.get("ok") else "BLOCKED",
            "backup_status": (backup or {}).get("status", "WARNING"),
            "smoke_status": (smoke or {}).get("status", "WARNING"),
            "ci_status": ci_status,
            "production_validation_status": (production or {}).get("status", "WARNING"),
            "pilot_approval_state": self._approval_state(approval),
        }
        return {
            "phase": PHASE_LABEL,
            "overview": overview,
            "release_assessment": latest_assessment,
            "assessment_groups": categories,
            "evidence": evidence,
            "pilot_agencies": enrollments,
            "synthetic_datasets": datasets,
            "health_timeline": timeline,
            "counts": {
                "evidence": len(evidence),
                "pilot_agencies": len(enrollments),
                "active_pilot_agencies": sum(item.get("enrollment_status") in {"enabled", "activated"} for item in enrollments),
                "synthetic_datasets": len(datasets),
                "timeline_events": len(timeline),
            },
            **self.safety_flags(),
        }

    async def list_evidence(
        self,
        *,
        evidence_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if evidence_type:
            self._require_choice(evidence_type, EVIDENCE_TYPES, "evidence_type")
            filters["evidence_type"] = evidence_type
        if status:
            self._require_choice(status, ASSESSMENT_STATUSES, "status")
            filters["status"] = status
        page = await self.repository.find_platform_records(
            collection_name=PILOT_OPERATIONAL_EVIDENCE_COLLECTION,
            filters=filters,
            sort_field="occurred_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=min(max(limit, 1), 200)),
        )
        return page.items

    async def create_evidence(
        self,
        payload: PilotOperationalEvidenceCreate,
        user: dict,
    ) -> dict[str, Any]:
        self._require_choice(payload.evidence_type, EVIDENCE_TYPES - {"release_assessment", "pilot_sign_off"}, "evidence_type")
        self._require_choice(payload.status, ASSESSMENT_STATUSES, "status")
        self._validate_metadata(payload.evidence_metadata)
        existing = await self.db.collection(PILOT_OPERATIONAL_EVIDENCE_COLLECTION).find_one(
            {"evidence_type": payload.evidence_type, "reference": payload.reference}
        )
        if existing:
            raise PilotOperationsError("Evidence reference already exists for this evidence type.")
        item = PilotOperationalEvidenceRecord(
            **payload.model_dump(mode="json"),
            build_phase=CURRENT_BUILD_PHASE,
            recorded_by_user_id=user["id"],
            recorded_by_role=user.get("global_role") or "platform_support",
        )
        stored = await self.db.collection(PILOT_OPERATIONAL_EVIDENCE_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._record_timeline_from_evidence(stored, user)
        await self._audit("pilot.evidence_recorded", stored["id"], user, payload.agency_id, {"evidence_type": payload.evidence_type, "status": payload.status})
        return stored

    async def assess_release(self, evidence: PilotReleaseProductionEvidence, user: dict) -> dict[str, Any]:
        if evidence.verified_by_role != user.get("global_role"):
            raise PilotOperationsError("Evidence verifier role must match the authenticated Platform role.")
        machine_evidence = runtime_repository_evidence()
        machine_evidence["source_integrity"] = bool(
            evidence.production_git_commit
            and evidence.github_actions_verified is True
            and evidence.complete_regression_verified is True
        )
        assessment = FinalStabilizationPilotReleaseGateService().build_assessment(
            environment_scope="production",
            machine_evidence=machine_evidence,
            production_evidence=evidence,
            git_commit=evidence.production_git_commit,
        )
        existing = await self.db.collection(PILOT_OPERATIONAL_EVIDENCE_COLLECTION).find_one(
            {"evidence_type": "release_assessment", "reference": assessment.assessment_hash}
        )
        if existing:
            return existing
        status = self._normalize_assessment_status(assessment.assessment_status)
        item = PilotOperationalEvidenceRecord(
            evidence_type="release_assessment",
            status=status,
            title="Pilot release assessment",
            summary=assessment.recommended_next_action,
            environment_scope="production",
            reference=assessment.assessment_hash,
            build_phase=CURRENT_BUILD_PHASE,
            occurred_at=assessment.generated_at,
            evidence_metadata={
                "assessment": assessment.model_dump(mode="json"),
                "operator_evidence_references": list(evidence.evidence_references),
            },
            recorded_by_user_id=user["id"],
            recorded_by_role=user.get("global_role") or "platform_support",
        )
        stored = await self.db.collection(PILOT_OPERATIONAL_EVIDENCE_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._record_timeline_from_evidence(stored, user)
        await self._audit("pilot.release_assessed", stored["id"], user, None, {"status": status, "assessment_hash": assessment.assessment_hash})
        return stored

    async def record_sign_off(self, sign_off: PilotReleaseSignOff, user: dict) -> dict[str, Any]:
        if sign_off.approved_by_role != user.get("global_role"):
            raise PilotOperationsError("Sign-off role must match the authenticated Platform role.")
        assessment_record = await self.db.collection(PILOT_OPERATIONAL_EVIDENCE_COLLECTION).find_one(
            {"evidence_type": "release_assessment", "reference": sign_off.assessment_hash}
        )
        if not assessment_record:
            raise PilotOperationsError("Sign-off must reference a persisted release assessment.")
        assessment_status = (assessment_record.get("evidence_metadata") or {}).get("assessment", {}).get("assessment_status")
        if sign_off.decision in {"approved", "approved_with_conditions"} and assessment_status != "ready":
            raise PilotOperationsError("A blocked or conditional release assessment cannot be approved.")
        existing = await self.db.collection(PILOT_OPERATIONAL_EVIDENCE_COLLECTION).find_one(
            {"evidence_type": "pilot_sign_off", "reference": sign_off.release_id}
        )
        if existing:
            raise PilotOperationsError("Pilot sign-off release ID already exists; create a superseding sign-off record.")
        status = "PASS" if sign_off.decision in {"approved", "approved_with_conditions"} else "BLOCKED"
        item = PilotOperationalEvidenceRecord(
            evidence_type="pilot_sign_off",
            status=status,
            title="Pilot release sign-off",
            summary=sign_off.decision_reason,
            environment_scope="production",
            reference=sign_off.release_id,
            build_phase=CURRENT_BUILD_PHASE,
            occurred_at=sign_off.approved_at,
            evidence_metadata={"sign_off": sign_off.model_dump(mode="json")},
            recorded_by_user_id=user["id"],
            recorded_by_role=user.get("global_role") or "platform_owner",
        )
        stored = await self.db.collection(PILOT_OPERATIONAL_EVIDENCE_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._record_timeline_from_evidence(stored, user)
        await self._audit("pilot.sign_off_recorded", stored["id"], user, None, {"decision": sign_off.decision, "assessment_hash": sign_off.assessment_hash})
        return stored

    async def list_enrollments(self) -> list[dict[str, Any]]:
        enrollment_page = await self.repository.find_platform_records(
            collection_name=PILOT_AGENCY_ENROLLMENTS_COLLECTION,
            sort_field="updated_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=200),
        )
        agency_page = await self.repository.find_global_records(
            collection_name="agencies",
            sort_field="created_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=200),
        )
        items = enrollment_page.items
        agencies = {item["id"]: item for item in agency_page.items}
        return [
            {
                **item,
                "agency_name": (agencies.get(item.get("agency_id")) or {}).get("name", "Unknown agency"),
                "agency_status": (agencies.get(item.get("agency_id")) or {}).get("status", "unknown"),
            }
            for item in items
        ]

    async def invite_agency(self, payload: PilotAgencyInvitationCreate, user: dict) -> dict[str, Any]:
        agency = await self.db.collection("agencies").find_one({"id": payload.agency_id})
        if not agency:
            raise PilotOperationsError("Pilot enrollment requires an existing agency.")
        existing = await self.db.collection(PILOT_AGENCY_ENROLLMENTS_COLLECTION).find_one({"agency_id": payload.agency_id})
        if existing:
            raise PilotOperationsError("Agency already has a pilot enrollment record.")
        item = PilotAgencyEnrollment(
            agency_id=payload.agency_id,
            invited_by_user_id=user["id"],
            last_action_by_user_id=user["id"],
            action_reason=payload.reason,
        )
        stored = await self.db.collection(PILOT_AGENCY_ENROLLMENTS_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._record_pilot_timeline("Pilot agency invited", f"{agency.get('name', payload.agency_id)} was invited to the controlled pilot.", "WARNING", f"pilot-enrollment:{stored['id']}", user, payload.agency_id)
        await self._audit("pilot.agency_invited", stored["id"], user, payload.agency_id, {"enrollment_status": "invited"})
        return stored

    async def change_enrollment_status(self, enrollment_id: str, target_status: str, reason: str, user: dict) -> dict[str, Any]:
        self._require_choice(target_status, ENROLLMENT_STATUSES - {"invited"}, "enrollment_status")
        existing = await self.db.collection(PILOT_AGENCY_ENROLLMENTS_COLLECTION).find_one({"id": enrollment_id})
        if not existing:
            raise PilotOperationsError("Pilot enrollment was not found.")
        now = utc_now()
        updates: dict[str, Any] = {
            "enrollment_status": target_status,
            "last_action_by_user_id": user["id"],
            "action_reason": reason,
            "synthetic_data_allowed": target_status in {"enabled", "activated"},
        }
        timestamp_field = {"enabled": "enabled_at", "activated": "activated_at", "disabled": "disabled_at"}[target_status]
        updates[timestamp_field] = now
        stored = await self.db.collection(PILOT_AGENCY_ENROLLMENTS_COLLECTION).update_one({"id": enrollment_id}, updates)
        await self._record_pilot_timeline(f"Pilot agency {target_status}", reason, "PASS" if target_status in {"enabled", "activated"} else "WARNING", f"pilot-enrollment:{enrollment_id}:{target_status}", user, existing["agency_id"])
        await self._audit(f"pilot.agency_{target_status}", enrollment_id, user, existing["agency_id"], {"reason": reason})
        return stored or existing

    async def list_synthetic_datasets(self, *, include_removed: bool = True) -> list[dict[str, Any]]:
        filters = {} if include_removed else {"dataset_status": "active"}
        page = await self.repository.find_platform_records(
            collection_name=PILOT_SYNTHETIC_DATASETS_COLLECTION,
            filters=filters,
            sort_field="created_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=200),
        )
        return page.items

    async def create_synthetic_dataset(self, payload: PilotSyntheticDatasetCreate, user: dict) -> dict[str, Any]:
        if not validate_pilot_fixture_reference(payload.dataset_reference):
            raise PilotOperationsError("Synthetic dataset references must use a governed pilot fixture prefix.")
        enrollment = await self.db.collection(PILOT_AGENCY_ENROLLMENTS_COLLECTION).find_one({"agency_id": payload.agency_id})
        if not enrollment or enrollment.get("enrollment_status") not in {"enabled", "activated"}:
            raise PilotOperationsError("Synthetic data requires an enabled pilot agency enrollment.")
        existing = await self.db.collection(PILOT_SYNTHETIC_DATASETS_COLLECTION).find_one({"dataset_reference": payload.dataset_reference})
        if existing:
            raise PilotOperationsError("Synthetic dataset reference already exists.")
        records = [
            {
                "reference": f"{payload.dataset_reference}_{index:03d}",
                "record_type": payload.dataset_type,
                "synthetic": True,
                "contains_real_identity_data": False,
            }
            for index in range(1, payload.record_count + 1)
        ]
        item = PilotSyntheticDataset(
            agency_id=payload.agency_id,
            dataset_reference=payload.dataset_reference,
            dataset_type=payload.dataset_type,
            synthetic_records=records,
            record_count=len(records),
            notes=payload.notes,
            created_by_user_id=user["id"],
        )
        stored = await self.db.collection(PILOT_SYNTHETIC_DATASETS_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._record_pilot_timeline("Synthetic pilot dataset created", f"Created {len(records)} isolated metadata records.", "PASS", f"synthetic-dataset:{payload.dataset_reference}:created", user, payload.agency_id)
        await self._audit("pilot.synthetic_dataset_created", stored["id"], user, payload.agency_id, {"dataset_reference": payload.dataset_reference, "record_count": len(records)})
        return stored

    async def remove_synthetic_dataset(self, dataset_id: str, reason: str, user: dict) -> dict[str, Any]:
        existing = await self.db.collection(PILOT_SYNTHETIC_DATASETS_COLLECTION).find_one({"id": dataset_id})
        if not existing:
            raise PilotOperationsError("Synthetic dataset was not found.")
        if existing.get("dataset_status") == "removed":
            return existing
        stored = await self.db.collection(PILOT_SYNTHETIC_DATASETS_COLLECTION).update_one(
            {"id": dataset_id},
            {
                "dataset_status": "removed",
                "synthetic_records": [],
                "record_count": 0,
                "removed_by_user_id": user["id"],
                "removed_at": utc_now(),
                "removal_reason": reason,
            },
        )
        await self._record_pilot_timeline("Synthetic pilot dataset removed", reason, "PASS", f"synthetic-dataset:{existing['dataset_reference']}:removed", user, existing["agency_id"])
        await self._audit("pilot.synthetic_dataset_removed", dataset_id, user, existing["agency_id"], {"dataset_reference": existing["dataset_reference"], "reason": reason})
        return stored or existing

    async def list_health_timeline(self, *, event_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if event_type:
            self._require_choice(event_type, TIMELINE_EVENT_TYPES, "event_type")
            filters["event_type"] = event_type
        page = await self.repository.find_platform_records(
            collection_name=PILOT_HEALTH_TIMELINE_COLLECTION,
            filters=filters,
            sort_field="occurred_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=min(max(limit, 1), 200)),
        )
        return page.items

    async def create_health_event(self, payload: PilotHealthTimelineEventCreate, user: dict) -> dict[str, Any]:
        self._require_choice(payload.event_type, TIMELINE_EVENT_TYPES, "event_type")
        self._require_choice(payload.status, ASSESSMENT_STATUSES, "status")
        self._validate_metadata(payload.event_metadata)
        existing = await self.db.collection(PILOT_HEALTH_TIMELINE_COLLECTION).find_one({"reference": payload.reference})
        if existing:
            raise PilotOperationsError("Health timeline reference already exists.")
        item = PilotHealthTimelineEvent(
            **payload.model_dump(mode="json"),
            build_phase=CURRENT_BUILD_PHASE,
            recorded_by_user_id=user["id"],
        )
        stored = await self.db.collection(PILOT_HEALTH_TIMELINE_COLLECTION).insert_one(item.model_dump(mode="json"))
        await self._audit("pilot.health_event_recorded", stored["id"], user, payload.agency_id, {"event_type": payload.event_type, "status": payload.status})
        return stored

    async def production_diagnostics(self) -> dict[str, Any]:
        snapshot = operational_diagnostics_snapshot()
        query_records = query_diagnostic_records()[-100:]
        slow_queries = [item for item in query_records if item.get("slow_query")][-25:]
        audit_page = await self.repository.find_platform_records(
            collection_name="audit_events",
            filters={"entity_type": "pilot_operations"},
            sort_field="created_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=25),
        )
        audit_events = audit_page.items
        return {
            "phase": PHASE_LABEL,
            "bounded_logs": audit_events,
            "telemetry_summary": {
                "process_local": snapshot.get("process_local"),
                "durable": snapshot.get("durable"),
                "reset_on_restart": snapshot.get("reset_on_restart"),
                "uptime_seconds": snapshot.get("uptime_seconds"),
                "deployment": snapshot.get("deployment"),
            },
            "slow_query_summary": {
                "bounded_count": len(slow_queries),
                "items": slow_queries,
            },
            "request_statistics": {
                "http_requests": (snapshot.get("counters") or {}).get("http_requests", {}),
                "http_errors": (snapshot.get("counters") or {}).get("http_errors", {}),
                "slow_requests": (snapshot.get("counters") or {}).get("slow_requests", {}),
                "request_timing": (snapshot.get("timings") or {}).get("http_request", {}),
            },
            "raw_logs_exposed": False,
            "sensitive_values_exposed": False,
            "bounded_aggregates_only": True,
            **self.safety_flags(),
        }

    async def _record_timeline_from_evidence(self, evidence: dict[str, Any], user: dict) -> None:
        event_type = {
            "deployment": "deployment",
            "smoke_run": "smoke",
            "backup_verification": "backup",
            "restore_rehearsal": "restore",
            "production_validation": "readiness",
            "release_assessment": "readiness",
            "pilot_sign_off": "pilot",
        }[evidence["evidence_type"]]
        await self._record_pilot_timeline(
            evidence["title"], evidence["summary"], evidence["status"], f"evidence:{evidence['evidence_type']}:{evidence['reference']}", user, evidence.get("agency_id"), event_type=event_type
        )

    async def _record_pilot_timeline(
        self,
        title: str,
        summary: str,
        status: str,
        reference: str,
        user: dict,
        agency_id: str | None,
        *,
        event_type: str = "pilot",
    ) -> dict[str, Any]:
        item = PilotHealthTimelineEvent(
            event_type=event_type,
            status=status,
            title=title,
            summary=summary,
            reference=reference,
            agency_id=agency_id,
            build_phase=CURRENT_BUILD_PHASE,
            recorded_by_user_id=user["id"],
        )
        return await self.db.collection(PILOT_HEALTH_TIMELINE_COLLECTION).insert_one(item.model_dump(mode="json"))

    async def _audit(self, event_type: str, entity_id: str, user: dict, agency_id: str | None, metadata: dict[str, Any]) -> None:
        event = AuditEvent(
            agency_id=agency_id,
            actor_user_id=user["id"],
            event_type=event_type,
            entity_type="pilot_operations",
            entity_id=entity_id,
            summary=event_type.replace(".", " ").replace("_", " ").title(),
            metadata={**metadata, "metadata_only": True},
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))

    @staticmethod
    def _latest_by_type(items: list[dict[str, Any]], evidence_type: str) -> dict[str, Any] | None:
        return next((item for item in items if item.get("evidence_type") == evidence_type), None)

    def _latest_assessment(self, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        record = self._latest_by_type(evidence, "release_assessment")
        stored = (record or {}).get("evidence_metadata", {}).get("assessment")
        if isinstance(stored, dict):
            return stored
        return FinalStabilizationPilotReleaseGateService().build_assessment(
            environment_scope="repository", machine_evidence=runtime_repository_evidence()
        ).model_dump(mode="json")

    def _assessment_categories(self, assessment: dict[str, Any]) -> list[dict[str, Any]]:
        dimensions = assessment.get("dimensions") or []
        by_key = {item.get("key"): item for item in dimensions}
        groups = []
        for category, keys in CATEGORY_DIMENSIONS.items():
            items = [by_key[key] for key in keys if key in by_key]
            statuses = [self._dimension_projection_status(item) for item in items]
            status = "BLOCKED" if "BLOCKED" in statuses else "WARNING" if "WARNING" in statuses else "PASS"
            groups.append({"category": category, "status": status, "items": [{**item, "display_status": self._dimension_projection_status(item)} for item in items]})
        return groups

    @staticmethod
    def _dimension_projection_status(item: dict[str, Any]) -> str:
        status = item.get("status")
        if status == "passed":
            return "PASS"
        if status == "blocked" or (status == "not_verified" and item.get("required_for_pilot")):
            return "BLOCKED"
        return "WARNING"

    def _dimension_status(self, assessment: dict[str, Any], key: str) -> str:
        item = next((item for item in assessment.get("dimensions") or [] if item.get("key") == key), {})
        return self._dimension_projection_status(item) if item else "WARNING"

    @staticmethod
    def _normalize_assessment_status(status: str | None) -> str:
        return {"ready": "PASS", "conditional": "WARNING", "blocked": "BLOCKED"}.get(status or "", status if status in ASSESSMENT_STATUSES else "WARNING")

    @staticmethod
    def _approval_state(record: dict[str, Any] | None) -> str:
        if not record:
            return "NOT_SIGNED_OFF"
        return (record.get("evidence_metadata") or {}).get("sign_off", {}).get("decision", "UNKNOWN").upper()

    @staticmethod
    def _require_choice(value: str, choices: set[str], field: str) -> None:
        if value not in choices:
            raise PilotOperationsError(f"{field} must be one of: {', '.join(sorted(choices))}.")

    @classmethod
    def _validate_metadata(cls, value: Any, *, depth: int = 0) -> None:
        if depth > 4:
            raise PilotOperationsError("Evidence metadata nesting is limited to four levels.")
        if isinstance(value, dict):
            if len(value) > 40:
                raise PilotOperationsError("Evidence metadata is limited to 40 fields per object.")
            for key, nested in value.items():
                if any(fragment in str(key).lower() for fragment in FORBIDDEN_METADATA_KEYS):
                    raise PilotOperationsError("Evidence metadata must not contain credentials or sensitive identity fields.")
                cls._validate_metadata(nested, depth=depth + 1)
        elif isinstance(value, list):
            if len(value) > 100:
                raise PilotOperationsError("Evidence metadata lists are limited to 100 items.")
            for nested in value:
                cls._validate_metadata(nested, depth=depth + 1)
        elif isinstance(value, str) and len(value) > 1200:
            raise PilotOperationsError("Evidence metadata strings are limited to 1200 characters.")
