from __future__ import annotations

from collections import Counter
from typing import Any

from config import validate_config
from database import Database
from models import (
    AuditEvent,
    CommercialPilotFeedback,
    CommercialPilotFeedbackCreate,
    CommercialPilotFeedbackReviewUpdate,
    CommercialPilotFeedbackStatus,
    CommercialPilotReadinessAssessment,
    CommercialPilotReadinessCheck,
    CommercialPilotReadinessStatus,
    now_utc,
)
from persistence_query import PaginationRequest
from persistence_repository import PersistenceRepository
from services.aeroassist_product_standards_service import (
    aeroassist_product_standards_readiness_metadata,
)
from services.agency_onboarding_service import (
    agency_onboarding_readiness_metadata,
    complete_pilot_agency_experience_readiness_metadata,
)
from services.commercial_pilot_operations_command_centre_service import (
    commercial_pilot_operations_command_centre_readiness_metadata,
)
from smoke_inventory import SMOKE_INVENTORY_SUMMARY


PHASE_LABEL = "phase_58_5_commercial_pilot_readiness"
COMMERCIAL_PILOT_FEEDBACK_COLLECTION = "commercial_pilot_feedback"

FEEDBACK_CATEGORIES = [
    "usability",
    "workflow",
    "data",
    "documentation",
    "defect",
    "suggestion",
    "other",
]
FEEDBACK_STATUSES = ["submitted", "reviewing", "planned", "resolved", "closed"]
FEEDBACK_URGENCIES = ["low", "normal", "high", "urgent"]
FEEDBACK_AFFECTED_AREAS = [
    "onboarding",
    "operations",
    "requests",
    "offers",
    "booking",
    "passengers",
    "documents",
    "tasks",
    "finance",
    "after_sales",
    "other",
]

PILOT_DOCUMENTS = [
    {"key": "package_index", "label": "Commercial Pilot package index", "path": "docs/pilot/README.md"},
    {"key": "overview", "label": "Pilot overview and supported scope", "path": "docs/pilot/pilot-overview.md"},
    {"key": "onboarding", "label": "Agency onboarding guide", "path": "docs/pilot/agency-onboarding-guide.md"},
    {"key": "administrator", "label": "Administrator guide", "path": "docs/pilot/administrator-guide.md"},
    {"key": "consultant", "label": "Travel consultant guide", "path": "docs/pilot/travel-consultant-guide.md"},
    {"key": "first_day", "label": "First-day checklist", "path": "docs/pilot/first-day-checklist.md"},
    {"key": "daily_operations", "label": "Daily operations checklist", "path": "docs/pilot/daily-operations-checklist.md"},
    {"key": "demo_workspace", "label": "Demo workspace guide", "path": "docs/pilot/demo-workspace-guide.md"},
    {"key": "backup_recovery", "label": "Backup and recovery guide", "path": "docs/pilot/backup-and-recovery-guide.md"},
    {"key": "incidents", "label": "Incident reporting guide", "path": "docs/pilot/incident-reporting-guide.md"},
    {"key": "feedback", "label": "Pilot feedback guide", "path": "docs/pilot/pilot-feedback-guide.md"},
    {"key": "acceptance", "label": "Pilot acceptance checklist", "path": "docs/pilot/pilot-acceptance-checklist.md"},
    {"key": "exit", "label": "Pilot exit checklist", "path": "docs/pilot/pilot-exit-checklist.md"},
]

RELATED_RECORD_COLLECTIONS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "client": (("client_profiles", ("display_name", "company_name", "email")),),
    "passenger": (("passenger_workspaces", ("passenger_reference", "first_name", "last_name")),),
    "request": (
        ("travel_requests", ("request_reference", "title", "purpose")),
        ("travel_request_workspaces", ("request_reference", "request_title")),
    ),
    "trip": (("trip_workspaces", ("trip_reference", "itinerary_summary")),),
    "offer": (
        ("offer_workspaces", ("offer_reference", "title")),
        ("offer_workspaces_v2", ("offer_reference", "offer_title")),
    ),
    "accepted_offer": (("trip_accepted_offer_snapshots", ("offer_id", "trip_id")),),
    "booking": (("booking_workspaces", ("booking_reference", "airline_pnr")),),
    "ticket": (("ticket_workspaces", ("ticket_reference", "ticket_number")),),
    "emd": (("emd_workspaces", ("emd_reference", "emd_number")),),
    "passenger_service": (("ssr_osi_workspaces", ("workspace_reference", "ssr_code", "service_type")),),
    "document": (("document_workspaces", ("document_reference", "document_title")),),
    "task": (("operational_work_items", ("work_item_code", "title")),),
    "invoice": (("invoices", ("invoice_number", "invoice_reference")),),
    "payment": (("payment_records", ("payment_reference", "status")),),
    "after_sales": (("after_sales_cases", ("case_reference", "title", "case_type")),),
}

STATUS_TRANSITIONS = {
    "submitted": {"reviewing", "closed"},
    "reviewing": {"planned", "resolved", "closed"},
    "planned": {"reviewing", "resolved", "closed"},
    "resolved": {"reviewing", "closed"},
    "closed": {"reviewing"},
}


class CommercialPilotReadinessError(ValueError):
    pass


def commercial_pilot_readiness_metadata() -> dict[str, Any]:
    return {
        "phase": PHASE_LABEL,
        "pilot_package_registered": True,
        "pilot_document_count": len(PILOT_DOCUMENTS),
        "tenant_scoped_feedback_enabled": True,
        "platform_feedback_review_enabled": True,
        "commercial_pilot_assessment_enabled": True,
        "phase_57_release_gate_preserved": True,
        "anonymous_feedback_enabled": False,
        "public_feedback_endpoint_enabled": False,
        "external_support_integration_enabled": False,
        "automatic_release_approval_enabled": False,
        "automatic_production_seeding_enabled": False,
        "provider_execution_enabled": False,
        "payment_execution_enabled": False,
        "ticketing_execution_enabled": False,
        "readiness_required": False,
    }


class CommercialPilotReadinessService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.repository = PersistenceRepository(db)

    async def submit_feedback(
        self,
        agency_id: str,
        payload: CommercialPilotFeedbackCreate,
        user: dict[str, Any],
    ) -> dict[str, Any]:
        await self._require_agency(agency_id)
        if payload.affected_area not in FEEDBACK_AFFECTED_AREAS:
            raise CommercialPilotReadinessError("Unsupported affected area.")
        related_record_label = await self._validate_related_record(
            agency_id,
            payload.related_record_type,
            payload.related_record_id,
        )
        feedback = CommercialPilotFeedback(
            agency_id=agency_id,
            category=payload.category,
            title=payload.title.strip(),
            description=payload.description.strip(),
            affected_area=payload.affected_area,
            urgency=payload.urgency,
            related_record_type=payload.related_record_type,
            related_record_id=payload.related_record_id,
            related_record_label=related_record_label,
            submitted_by=user["id"],
            submitted_by_name=user.get("full_name") or user.get("email") or "Agency user",
        )
        created = await self.db.collection(COMMERCIAL_PILOT_FEEDBACK_COLLECTION).insert_one(
            feedback.model_dump(mode="json")
        )
        await self._audit(
            created,
            user["id"],
            "commercial_pilot_feedback.submitted",
            "Pilot feedback submitted.",
            {"category": created["category"], "affected_area": created["affected_area"]},
        )
        return self._agency_projection(created)

    async def list_agency_feedback(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        category: str | None = None,
        affected_area: str | None = None,
    ) -> dict[str, Any]:
        await self._require_agency(agency_id)
        filters = self._feedback_filters(status=status, category=category, affected_area=affected_area)
        page = await self.repository.find_agency_records(
            collection_name=COMMERCIAL_PILOT_FEEDBACK_COLLECTION,
            agency_id=agency_id,
            filters=filters or None,
            sort_field="submitted_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=100, include_total=True),
        )
        items = [self._agency_projection(item) for item in page.items]
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "summary": self._summary(items),
            "filters": self.feedback_options(),
            "documentation": PILOT_DOCUMENTS,
            "pagination": page.pagination.__dict__,
            "tenant_scoped": True,
            "anonymous_submission_enabled": False,
        }

    async def get_agency_feedback(self, agency_id: str, feedback_id: str) -> dict[str, Any]:
        item = await self.db.collection(COMMERCIAL_PILOT_FEEDBACK_COLLECTION).find_one(
            {"id": feedback_id, "agency_id": agency_id}
        )
        if item is None:
            raise CommercialPilotReadinessError("Pilot feedback not found.")
        return self._agency_projection(item)

    async def list_platform_feedback(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        category: str | None = None,
        affected_area: str | None = None,
        urgency: str | None = None,
    ) -> dict[str, Any]:
        filters = self._feedback_filters(
            status=status,
            category=category,
            affected_area=affected_area,
            urgency=urgency,
        )
        page = await self.repository.find_platform_records(
            collection_name=COMMERCIAL_PILOT_FEEDBACK_COLLECTION,
            agency_id=agency_id,
            filters=filters or None,
            sort_field="submitted_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=100, include_total=True),
        )
        agency_names = await self._agency_names(page.items)
        items = [
            {**item, "agency_name": agency_names.get(item.get("agency_id"), "Unknown agency")}
            for item in page.items
        ]
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "summary": self._summary(items),
            "filters": self.feedback_options(),
            "pagination": page.pagination.__dict__,
            "platform_review": True,
            "agency_mutation_enabled": False,
        }

    async def get_platform_feedback(self, feedback_id: str) -> dict[str, Any]:
        item = await self.db.collection(COMMERCIAL_PILOT_FEEDBACK_COLLECTION).find_one({"id": feedback_id})
        if item is None:
            raise CommercialPilotReadinessError("Pilot feedback not found.")
        agency = await self.db.collection("agencies").find_one({"id": item["agency_id"]})
        return {**item, "agency_name": (agency or {}).get("name", "Unknown agency")}

    async def review_feedback(
        self,
        feedback_id: str,
        payload: CommercialPilotFeedbackReviewUpdate,
        user: dict[str, Any],
    ) -> dict[str, Any]:
        existing = await self.get_platform_feedback(feedback_id)
        current_status = str(existing.get("status"))
        next_status = payload.status.value
        status_changed = next_status != current_status
        if status_changed and next_status not in STATUS_TRANSITIONS.get(current_status, set()):
            raise CommercialPilotReadinessError(
                f"Pilot feedback cannot move from {current_status} to {next_status}."
            )
        updated = await self.db.collection(COMMERCIAL_PILOT_FEEDBACK_COLLECTION).update_one(
            {"id": feedback_id},
            {
                "status": next_status,
                "review_notes": payload.review_notes.strip(),
                "reviewed_by_user_id": user["id"],
                "reviewed_by_name": user.get("full_name") or user.get("email") or "Platform user",
                "reviewed_at": now_utc(),
            },
        )
        if updated is None:
            raise CommercialPilotReadinessError("Pilot feedback not found.")
        await self._audit(
            updated,
            user["id"],
            "commercial_pilot_feedback.reviewed",
            (
                f"Pilot feedback moved from {current_status} to {next_status}."
                if status_changed
                else f"Pilot feedback review notes updated in {current_status}."
            ),
            {
                "from_status": current_status,
                "to_status": next_status,
                "status_changed": status_changed,
            },
        )
        agency = await self.db.collection("agencies").find_one({"id": updated["agency_id"]})
        return {**updated, "agency_name": (agency or {}).get("name", "Unknown agency")}

    async def assess(self, agency_id: str | None = None) -> dict[str, Any]:
        agency = None
        onboarding_profile = None
        if agency_id:
            agency = await self._require_agency(agency_id)
            onboarding_profile = await self.db.collection("agency_onboarding_profiles").find_one(
                {"agency_id": agency_id, "profile_key": "first_time_setup"}
            )

        config = validate_config(include_storage=False)
        database = await self.db.readiness()
        checks = self.build_checks(
            {
                "configuration_ready": bool(config.get("ok")),
                "configuration_warnings": int(config.get("warning_count") or 0),
                "database_ready": bool(database.get("ok")),
                "smoke_inventory_ready": bool(
                    SMOKE_INVENTORY_SUMMARY.get("inventory_validation_ready")
                    and not SMOKE_INVENTORY_SUMMARY.get("unresolved_scripts")
                ),
                "onboarding_ready": agency_onboarding_readiness_metadata().get(
                    "resumable_wizard_enabled", False
                ),
                "demo_profiles_ready": complete_pilot_agency_experience_readiness_metadata().get(
                    "selectable_demo_profiles_enabled", False
                ),
                "operations_ready": commercial_pilot_operations_command_centre_readiness_metadata().get(
                    "agency_operations_home_enabled", False
                ),
                "product_standards_ready": aeroassist_product_standards_readiness_metadata().get(
                    "shared_product_components_enabled", False
                ),
                "documentation_ready": len(PILOT_DOCUMENTS) == 13,
                "feedback_ready": True,
                "execution_boundaries_disabled": all(
                    not commercial_pilot_readiness_metadata()[key]
                    for key in (
                        "automatic_release_approval_enabled",
                        "automatic_production_seeding_enabled",
                        "provider_execution_enabled",
                        "payment_execution_enabled",
                        "ticketing_execution_enabled",
                    )
                ),
                "agency_onboarding_state": (
                    "legacy_exempt"
                    if agency_id and onboarding_profile is None
                    else (onboarding_profile or {}).get("onboarding_status")
                    if agency_id
                    else None
                ),
                "agency_demo_ready": (
                    None
                    if not agency_id or onboarding_profile is None
                    else bool(onboarding_profile.get("demo_workspace_seeded"))
                ),
            }
        )
        assessment = self.classify_checks(checks, agency_id=agency_id)
        return {
            **assessment.model_dump(mode="json"),
            "agency": {"id": agency["id"], "name": agency["name"]} if agency else None,
            "documentation": PILOT_DOCUMENTS,
            "smoke_inventory": {
                "inventoried_smoke_scripts": SMOKE_INVENTORY_SUMMARY.get("inventoried_smoke_scripts"),
                "unresolved_scripts": SMOKE_INVENTORY_SUMMARY.get("unresolved_scripts"),
                "inventory_validation_ready": SMOKE_INVENTORY_SUMMARY.get("inventory_validation_ready"),
            },
            "phase_57_release_gate": {
                "preserved": True,
                "replaced_by_commercial_assessment": False,
                "human_release_sign_off_still_required": True,
            },
            "safety": commercial_pilot_readiness_metadata(),
        }

    @staticmethod
    def build_checks(signals: dict[str, Any]) -> list[CommercialPilotReadinessCheck]:
        checks = [
            CommercialPilotReadinessCheck(
                key="health_readiness",
                label="Health and readiness",
                status="pass"
                if signals.get("configuration_ready") and signals.get("database_ready")
                else "blocked",
                critical=True,
                summary="Application configuration and database readiness are available."
                if signals.get("configuration_ready") and signals.get("database_ready")
                else "Application configuration or database readiness requires attention.",
                remediation="Resolve configuration and database readiness failures before pilot use.",
            ),
            CommercialPilotReadinessCheck(
                key="smoke_inventory",
                label="Smoke inventory",
                status="pass" if signals.get("smoke_inventory_ready") else "blocked",
                critical=True,
                summary="The smoke inventory is registered with no unresolved scripts."
                if signals.get("smoke_inventory_ready")
                else "The smoke inventory contains unresolved registration.",
                remediation="Resolve the smoke inventory before pilot use.",
            ),
            CommercialPilotReadinessCheck(
                key="agency_onboarding",
                label="Agency onboarding",
                status="pass" if signals.get("onboarding_ready") else "blocked",
                critical=True,
                summary="Resumable first-time agency onboarding is registered.",
            ),
            CommercialPilotReadinessCheck(
                key="demo_workspace_profiles",
                label="Demo workspace profiles",
                status="pass" if signals.get("demo_profiles_ready") else "blocked",
                critical=True,
                summary="Selectable synthetic demo profiles are registered.",
            ),
            CommercialPilotReadinessCheck(
                key="operations_command_centre",
                label="Operations Command Centre",
                status="pass" if signals.get("operations_ready") else "blocked",
                critical=True,
                summary="The canonical agency operational home is registered.",
            ),
            CommercialPilotReadinessCheck(
                key="product_standards",
                label="Product standards",
                status="pass" if signals.get("product_standards_ready") else "blocked",
                critical=True,
                summary="Shared product and accessibility patterns are registered.",
            ),
            CommercialPilotReadinessCheck(
                key="pilot_documentation",
                label="Pilot documentation",
                status="pass" if signals.get("documentation_ready") else "blocked",
                critical=True,
                summary="The controlled pilot package has stable documentation references.",
            ),
            CommercialPilotReadinessCheck(
                key="pilot_feedback",
                label="Pilot feedback",
                status="pass" if signals.get("feedback_ready") else "blocked",
                critical=True,
                summary="Tenant-scoped submission and Platform review are registered.",
            ),
            CommercialPilotReadinessCheck(
                key="execution_boundaries",
                label="Execution boundaries",
                status="pass" if signals.get("execution_boundaries_disabled") else "blocked",
                critical=True,
                summary="Provider, payment, ticketing, production seeding, and automatic approval remain disabled.",
            ),
        ]
        if signals.get("configuration_warnings"):
            checks.append(
                CommercialPilotReadinessCheck(
                    key="configuration_warnings",
                    label="Configuration warnings",
                    status="warning",
                    summary=f"{signals['configuration_warnings']} non-blocking configuration warning(s) require review.",
                    remediation="Review the configuration warnings in protected readiness diagnostics.",
                )
            )
        agency_state = signals.get("agency_onboarding_state")
        if agency_state == "legacy_exempt":
            checks.append(
                CommercialPilotReadinessCheck(
                    key="selected_agency_onboarding",
                    label="Selected agency onboarding",
                    status="pass",
                    summary="This historical agency is explicitly compatible without a first-time onboarding profile.",
                )
            )
        elif agency_state and agency_state != "completed":
            checks.append(
                CommercialPilotReadinessCheck(
                    key="selected_agency_onboarding",
                    label="Selected agency onboarding",
                    status="warning",
                    summary="The selected agency has not completed first-time onboarding.",
                    remediation="Resume and complete the Agency onboarding wizard.",
                )
            )
        elif agency_state == "completed":
            checks.append(
                CommercialPilotReadinessCheck(
                    key="selected_agency_onboarding",
                    label="Selected agency onboarding",
                    status="pass",
                    summary="The selected agency completed first-time onboarding.",
                )
            )
        if signals.get("agency_demo_ready") is False:
            checks.append(
                CommercialPilotReadinessCheck(
                    key="selected_agency_demo",
                    label="Selected agency demo workspace",
                    status="warning",
                    summary="The selected agency has not created a synthetic demo workspace.",
                    remediation="Create a demo workspace from Agency onboarding before guided pilot exercises.",
                )
            )
        elif signals.get("agency_demo_ready") is True:
            checks.append(
                CommercialPilotReadinessCheck(
                    key="selected_agency_demo",
                    label="Selected agency demo workspace",
                    status="pass",
                    summary="The selected agency has a synthetic demo workspace.",
                )
            )
        return checks

    @staticmethod
    def classify_checks(
        checks: list[CommercialPilotReadinessCheck],
        *,
        agency_id: str | None = None,
    ) -> CommercialPilotReadinessAssessment:
        blockers = [item for item in checks if item.status == "blocked"]
        warnings = [item for item in checks if item.status == "warning"]
        status = (
            CommercialPilotReadinessStatus.BLOCKED
            if blockers
            else CommercialPilotReadinessStatus.CONDITIONALLY_READY
            if warnings
            else CommercialPilotReadinessStatus.READY
        )
        return CommercialPilotReadinessAssessment(
            phase=PHASE_LABEL,
            status=status,
            agency_id=agency_id,
            checks=checks,
            blocker_count=len(blockers),
            warning_count=len(warnings),
        )

    @staticmethod
    def feedback_options() -> dict[str, Any]:
        return {
            "categories": FEEDBACK_CATEGORIES,
            "statuses": FEEDBACK_STATUSES,
            "urgencies": FEEDBACK_URGENCIES,
            "affected_areas": FEEDBACK_AFFECTED_AREAS,
            "related_record_types": sorted(RELATED_RECORD_COLLECTIONS),
        }

    @staticmethod
    def _feedback_filters(
        *,
        status: str | None = None,
        category: str | None = None,
        affected_area: str | None = None,
        urgency: str | None = None,
    ) -> dict[str, Any]:
        values = {
            "status": status,
            "category": category,
            "affected_area": affected_area,
            "urgency": urgency,
        }
        return {key: value for key, value in values.items() if value}

    @staticmethod
    def _summary(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total": len(items),
            "by_status": dict(Counter(str(item.get("status") or "submitted") for item in items)),
            "by_category": dict(Counter(str(item.get("category") or "other") for item in items)),
            "urgent_or_high": sum(
                1 for item in items if item.get("urgency") in {"urgent", "high"}
            ),
        }

    async def _require_agency(self, agency_id: str) -> dict[str, Any]:
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if agency is None:
            raise CommercialPilotReadinessError("Agency not found.")
        return agency

    async def _validate_related_record(
        self,
        agency_id: str,
        record_type: str | None,
        record_id: str | None,
    ) -> str | None:
        if bool(record_type) != bool(record_id):
            raise CommercialPilotReadinessError(
                "Related record type and related record ID must be supplied together."
            )
        if not record_type:
            return None
        candidates = RELATED_RECORD_COLLECTIONS.get(record_type)
        if candidates is None:
            raise CommercialPilotReadinessError("Unsupported related record type.")
        for collection_name, label_fields in candidates:
            record = await self.db.collection(collection_name).find_one(
                {"id": record_id, "agency_id": agency_id}
            )
            if record is None:
                continue
            label_parts = [str(record.get(field)).strip() for field in label_fields if record.get(field)]
            return " · ".join(label_parts[:2]) or f"{record_type.replace('_', ' ').title()} record"
        raise CommercialPilotReadinessError(
            "Related record was not found in this agency. Cross-agency records cannot be linked."
        )

    async def _agency_names(self, items: list[dict[str, Any]]) -> dict[str, str]:
        names: dict[str, str] = {}
        for agency_id in {str(item.get("agency_id")) for item in items if item.get("agency_id")}:
            agency = await self.db.collection("agencies").find_one({"id": agency_id})
            names[agency_id] = (agency or {}).get("name", "Unknown agency")
        return names

    @staticmethod
    def _agency_projection(item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in item.items()
            if key != "reviewed_by_user_id"
        }

    async def _audit(
        self,
        feedback: dict[str, Any],
        actor_user_id: str,
        event_type: str,
        summary: str,
        metadata: dict[str, Any],
    ) -> None:
        event = AuditEvent(
            agency_id=feedback["agency_id"],
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type="commercial_pilot_feedback",
            entity_id=feedback["id"],
            summary=summary,
            metadata={**metadata, "metadata_only": True},
        )
        await self.db.collection("audit_events").insert_one(event.model_dump(mode="json"))
