from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    BookingProviderTarget,
    BookingReadinessPackage,
    BookingReadinessStatus,
    OfferAcceptance,
    OfferAcceptanceCreate,
    OfferAcceptanceStatus,
    OfferDeclineCreate,
    OfferOptionStatus,
    OfferWorkspaceStatus,
    TripAcceptedOfferSnapshot,
    new_id,
)
from services.canonical_commercial_lifecycle_service import (
    CommercialLifecycleError,
    acceptance_idempotency_key,
    canonical_json_hash,
    canonical_status,
    validate_lifecycle_transition,
    write_lifecycle_evidence,
)
from services.offer_builder_service import OfferBuilderService, write_offer_builder_audit
from services.service_catalogue_service import find_service_catalogue_record, service_catalogue_snapshot
from services.trip_dossier_service import confirm_trip_from_accepted_snapshot


def _sort_segments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            int(item.get("sequence") or item.get("segment_order") or 0),
            str(item.get("departure_at") or ""),
        ),
    )


def _sort_created(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: str(item.get("created_at") or ""))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _warning(message: str, code: str = "booking_readiness") -> dict[str, Any]:
    return {"code": code, "message": message, "severity": "warning"}


def _route_summary(segments: list[dict[str, Any]]) -> str | None:
    if not segments:
        return None
    return " / ".join(
        (
            f"{item.get('origin_airport') or item.get('origin_airport_code')}-"
            f"{item.get('destination_airport') or item.get('destination_airport_code')}"
        )
        for item in segments
    )


def _extract_rule_artifacts(
    rules_summary: dict[str, Any],
    option_warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    warnings = list(option_warnings or [])
    documents: list[dict[str, Any]] = []
    policy_violations: list[dict[str, Any]] = []
    ssr: list[dict[str, Any]] = []
    osi: list[dict[str, Any]] = []

    for evaluation in _as_list(rules_summary.get("evaluations")):
        for warning in _as_list(evaluation.get("warnings")):
            warnings.append(
                warning if isinstance(warning, dict) else _warning(str(warning), "rule_warning")
            )
        for document in _as_list(evaluation.get("required_documents")):
            documents.append(document if isinstance(document, dict) else {"label": str(document)})
        if evaluation.get("allowed") is False:
            policy_violations.append(
                {
                    "service_code": evaluation.get("service_code"),
                    "segment_id": evaluation.get("segment_id"),
                    "reason": evaluation.get("reason") or "Rule evaluation blocked this service.",
                }
            )
        for violation in _as_list(evaluation.get("policy_violations")):
            policy_violations.append(
                violation if isinstance(violation, dict) else {"reason": str(violation)}
            )
        generated_ssr = evaluation.get("generated_ssr")
        if isinstance(generated_ssr, dict):
            ssr.append(generated_ssr)
        elif isinstance(generated_ssr, list):
            ssr.extend([item for item in generated_ssr if isinstance(item, dict)])
        generated_osi = evaluation.get("generated_osi")
        if isinstance(generated_osi, dict):
            osi.append(generated_osi)
        elif isinstance(generated_osi, list):
            osi.extend([item for item in generated_osi if isinstance(item, dict)])

    return {
        "warnings": warnings,
        "required_documents": documents,
        "policy_violations": policy_violations,
        "ssr": ssr,
        "osi": osi,
    }


class OfferAcceptanceService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.builder = OfferBuilderService(db)

    async def accept_offer_option(
        self,
        agency_id: str,
        workspace_id: str,
        option_id: str,
        user: dict,
        payload: OfferAcceptanceCreate,
    ) -> dict[str, Any] | None:
        actor_user_id = user.get("id")
        workspace = await self.builder.get_workspace_or_none(agency_id, workspace_id)
        option = await self.builder.get_option_or_none(agency_id, option_id)
        if workspace is None or option is None or option.get("workspace_id") != workspace_id:
            return None
        offer_version = int(workspace.get("version") or 1)
        option_version = int(option.get("version") or 1)
        if int(option.get("offer_workspace_version") or offer_version) != offer_version:
            raise CommercialLifecycleError(
                "Offer Option belongs to a different Offer revision.",
                code="OFFER_OPTION_REVISION_MISMATCH",
            )
        if payload.offer_version is None or int(payload.offer_version) != offer_version:
            raise CommercialLifecycleError(
                "Acceptance must target the exact current Offer version.",
                code="STALE_OFFER_VERSION",
            )
        if payload.option_version is None or int(payload.option_version) != option_version:
            raise CommercialLifecycleError(
                "Acceptance must target the exact current Offer Option version.",
                code="STALE_OFFER_OPTION_VERSION",
            )
        idempotency_key = acceptance_idempotency_key(
            agency_id,
            workspace_id,
            offer_version,
            option_id,
            option_version,
            actor_user_id,
            payload.idempotency_key,
        )
        existing_idempotent = await self.db.collection("offer_acceptances").find_one(
            {"agency_id": agency_id, "idempotency_key": idempotency_key}
        )
        if existing_idempotent:
            if (
                existing_idempotent.get("workspace_id") != workspace_id
                or existing_idempotent.get("option_id") != option_id
                or int(existing_idempotent.get("offer_version") or 1) != offer_version
            ):
                raise CommercialLifecycleError(
                    "Idempotency key is already bound to another acceptance decision.",
                    code="IDEMPOTENCY_KEY_CONFLICT",
                )
            return await self._acceptance_result(existing_idempotent, idempotent=True)

        active_acceptances = await self.db.collection("offer_acceptances").find_many(
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
            }
        )
        active_for_revision = [
            item
            for item in active_acceptances
            if int(item.get("offer_version") or 1) == offer_version
            and item.get("status")
            in {
                OfferAcceptanceStatus.PENDING.value,
                OfferAcceptanceStatus.ACCEPTED.value,
            }
        ]
        if active_for_revision:
            active = self._latest(active_for_revision)
            if active and active.get("option_id") == option_id:
                return await self._acceptance_result(active, idempotent=True)
            raise CommercialLifecycleError(
                "This Offer revision already has an active acceptance.",
                code="DUPLICATE_ACTIVE_ACCEPTANCE",
            )

        self._assert_offer_actionable(workspace, payload.override_reason)
        if (option.get("pricing_summary_json") or {}).get("total_amount") is None:
            raise CommercialLifecycleError(
                "Accepted Offer Option requires a server-derived total.",
                code="OFFER_TOTAL_REQUIRED",
            )

        request_id = workspace.get("request_id") or option.get("request_id")
        trip_id = workspace.get("trip_id") or option.get("trip_id")
        if not trip_id and request_id:
            request = await self.db.collection("travel_requests").find_one(
                {"agency_id": agency_id, "id": request_id}
            )
            trip_id = (request or {}).get("trip_id")
        trip_id = trip_id or new_id()

        snapshot = await self.build_acceptance_snapshot(agency_id, option_id)
        if snapshot is None:
            return None

        client_summary = payload.client_visible_summary_json or {
            "option_label": option.get("label"),
            "route_summary": _route_summary(snapshot["routing"].get("segments", [])),
            "pricing": snapshot["pricing"].get("summary") or {},
            "fare_bundle": snapshot["fare_bundle"].get("primary") or {},
        }
        immutable_payload = self._immutable_payload(
            agency_id=agency_id,
            request_id=request_id,
            trip_id=trip_id,
            workspace=workspace,
            option=option,
            snapshot=snapshot,
            client_summary=client_summary,
            actor_user_id=actor_user_id,
            acceptance_terms_version=payload.acceptance_terms_version,
        )
        payload_hash = canonical_json_hash(immutable_payload)
        acceptance = OfferAcceptance(
            agency_id=agency_id,
            workspace_id=workspace_id,
            option_id=option_id,
            offer_version=offer_version,
            option_version=option_version,
            idempotency_key=idempotency_key,
            request_id=request_id,
            trip_id=trip_id,
            accepted_by_user_id=actor_user_id,
            actor_identity_id=user.get("identity_id"),
            accepted_at=None,
            channel=payload.channel,
            acceptance_terms_version=payload.acceptance_terms_version,
            consent_evidence_json=payload.consent_evidence_json,
            acceptance_source=payload.acceptance_source,
            status=OfferAcceptanceStatus.PENDING,
            accepted_pricing_snapshot_json=snapshot["pricing"],
            accepted_routing_snapshot_json=snapshot["routing"],
            accepted_fare_bundle_snapshot_json=snapshot["fare_bundle"],
            accepted_services_snapshot_json=snapshot["services"],
            accepted_pets_snapshot_json=snapshot["pets"],
            accepted_special_items_snapshot_json=snapshot["special_items"],
            rules_feasibility_snapshot_json=snapshot["rules_feasibility"],
            client_visible_summary_json=client_summary,
            accepted_payload_hash=payload_hash,
            reconciliation_status="snapshot_pending",
            internal_notes=payload.internal_notes,
        )
        created = await self.db.collection("offer_acceptances").insert_one(acceptance.model_dump(mode="json"))
        trip_snapshot = None
        readiness = None
        try:
            trip_snapshot = await self._create_trip_snapshot_once(
                agency_id,
                trip_id,
                created,
                immutable_payload,
                payload_hash,
            )
            trip = await confirm_trip_from_accepted_snapshot(
                self.db,
                agency_id,
                trip_snapshot,
                created,
                actor_user_id,
            )
            accepted_at = datetime.now(timezone.utc)
            created = await self.db.collection("offer_acceptances").update_one(
                {"agency_id": agency_id, "id": created["id"]},
                {
                    "status": OfferAcceptanceStatus.ACCEPTED.value,
                    "accepted_at": accepted_at,
                    "trip_id": trip["id"],
                    "accepted_snapshot_id": trip_snapshot["id"],
                    "reconciliation_status": "canonical",
                },
            ) or created
            await self.db.collection("offer_options").update_one(
                {"agency_id": agency_id, "id": option_id},
                {
                    "status": OfferOptionStatus.RECOMMENDED.value,
                    "recommendation_rank": 1,
                    "recommendation_tag": "Accepted",
                    "trip_id": trip["id"],
                    "updated_by_user_id": actor_user_id,
                },
            )
            validate_lifecycle_transition("offer", workspace.get("status"), "accepted")
            await self.db.collection("offer_workspaces").update_one(
                {"agency_id": agency_id, "id": workspace_id},
                {
                    "status": OfferWorkspaceStatus.ACCEPTED.value,
                    "trip_id": trip["id"],
                    "updated_by_user_id": actor_user_id,
                },
            )
            readiness = await self.build_booking_readiness_package(
                agency_id,
                created["id"],
                user,
                provider_target=payload.provider_target,
            )
        except Exception as exc:
            await self.db.collection("offer_acceptances").update_one(
                {"agency_id": agency_id, "id": created["id"]},
                {
                    "status": OfferAcceptanceStatus.PENDING.value,
                    "accepted_snapshot_id": (trip_snapshot or {}).get("id"),
                    "reconciliation_status": "requires_review",
                    "failure_reason": str(exc)[:500],
                },
            )
            raise

        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_acceptance.accepted",
            "offer_acceptance",
            created["id"],
            f"Accepted offer option {option.get('label') or option_id}.",
            {
                "workspace_id": workspace_id,
                "option_id": option_id,
                "trip_id": created.get("trip_id"),
                "offer_version": offer_version,
                "option_version": option_version,
                "accepted_snapshot_id": trip_snapshot.get("id"),
                "accepted_payload_hash": payload_hash,
            },
        )
        await write_lifecycle_evidence(
            self.db,
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="offer_acceptance.lifecycle.accepted",
            entity_type="offer_acceptance",
            entity_id=created["id"],
            summary="Accepted exact Offer version and created immutable evidence.",
            previous_status="pending",
            next_status="accepted",
            request_id=request_id,
            trip_id=created.get("trip_id"),
            metadata={
                "workspace_id": workspace_id,
                "offer_version": offer_version,
                "option_id": option_id,
                "option_version": option_version,
                "accepted_snapshot_id": trip_snapshot.get("id"),
                "accepted_payload_hash": payload_hash,
            },
        )
        return {
            "acceptance": created,
            "trip_snapshot": trip_snapshot,
            "booking_readiness": readiness,
            "warnings": snapshot.get("warnings", []),
            "required_documents": snapshot.get("required_documents", []),
            "ssr_osi_preview": snapshot.get("ssr_osi_preview", {}),
            "idempotent_reused": False,
        }

    async def decline_offer_option(
        self,
        agency_id: str,
        workspace_id: str,
        option_id: str,
        user: dict,
        payload: OfferDeclineCreate,
    ) -> dict[str, Any] | None:
        workspace = await self.builder.get_workspace_or_none(agency_id, workspace_id)
        option = await self.builder.get_option_or_none(agency_id, option_id)
        if workspace is None or option is None or option.get("workspace_id") != workspace_id:
            return None
        offer_version = int(workspace.get("version") or 1)
        option_version = int(option.get("version") or 1)
        if int(option.get("offer_workspace_version") or offer_version) != offer_version:
            raise CommercialLifecycleError(
                "Offer Option belongs to a different Offer revision.",
                code="OFFER_OPTION_REVISION_MISMATCH",
            )
        if payload.offer_version is None or int(payload.offer_version) != offer_version:
            raise CommercialLifecycleError(
                "Decline must target the exact current Offer version.",
                code="STALE_OFFER_VERSION",
            )
        if payload.option_version is None or int(payload.option_version) != option_version:
            raise CommercialLifecycleError(
                "Decline must target the exact current Offer Option version.",
                code="STALE_OFFER_OPTION_VERSION",
            )
        self._assert_offer_actionable(workspace, None)
        key = acceptance_idempotency_key(
            agency_id,
            workspace_id,
            offer_version,
            option_id,
            option_version,
            user.get("id"),
            payload.idempotency_key,
            decision="declined",
        )
        existing = await self.db.collection("offer_acceptances").find_one(
            {"agency_id": agency_id, "idempotency_key": key}
        )
        if existing:
            return {
                "acceptance": existing,
                "trip_snapshot": None,
                "booking_readiness": None,
                "idempotent_reused": True,
            }
        active = await self.db.collection("offer_acceptances").find_one(
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "status": OfferAcceptanceStatus.ACCEPTED.value,
            }
        )
        if active and int(active.get("offer_version") or 1) == offer_version:
            raise CommercialLifecycleError(
                "An accepted Offer revision cannot be declined.",
                code="ACCEPTANCE_ALREADY_ACTIVE",
            )
        decision_payload = {
            "workspace_id": workspace_id,
            "offer_version": offer_version,
            "option_id": option_id,
            "option_version": option_version,
            "decision": "declined",
            "reason": payload.reason,
        }
        declined_at = datetime.now(timezone.utc)
        model = OfferAcceptance(
            agency_id=agency_id,
            workspace_id=workspace_id,
            option_id=option_id,
            offer_version=offer_version,
            option_version=option_version,
            idempotency_key=key,
            request_id=workspace.get("request_id"),
            accepted_by_user_id=user.get("id"),
            actor_identity_id=user.get("identity_id"),
            channel=payload.channel,
            status=OfferAcceptanceStatus.DECLINED,
            declined_at=declined_at,
            accepted_payload_hash=canonical_json_hash(decision_payload),
            reconciliation_status="canonical",
            internal_notes=payload.reason,
        )
        created = await self.db.collection("offer_acceptances").insert_one(
            model.model_dump(mode="json")
        )
        validate_lifecycle_transition("offer", workspace.get("status"), "declined")
        await self.db.collection("offer_workspaces").update_one(
            {"agency_id": agency_id, "id": workspace_id},
            {
                "status": OfferWorkspaceStatus.DECLINED.value,
                "updated_by_user_id": user.get("id"),
            },
        )
        await write_lifecycle_evidence(
            self.db,
            agency_id=agency_id,
            actor_user_id=user.get("id"),
            event_type="offer_acceptance.lifecycle.declined",
            entity_type="offer_acceptance",
            entity_id=created["id"],
            summary="Declined exact Offer version; no Trip was created.",
            previous_status="pending",
            next_status="declined",
            request_id=workspace.get("request_id"),
            metadata=decision_payload,
        )
        return {
            "acceptance": created,
            "trip_snapshot": None,
            "booking_readiness": None,
            "idempotent_reused": False,
        }

    async def build_acceptance_snapshot(self, agency_id: str, option_id: str) -> dict[str, Any] | None:
        option = await self.builder.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        detail = await self.builder.workspace_detail(agency_id, option["workspace_id"])
        if detail is None:
            return None

        workspace = detail["workspace"]
        request_id = workspace.get("request_id") or option.get("request_id")
        trip_id = workspace.get("trip_id") or option.get("trip_id")
        option_segments = _sort_segments(
            [item for item in detail.get("segments", []) if item.get("option_id") == option_id]
        )
        option_routings = _sort_created(
            [item for item in detail.get("routing_options", []) if item.get("option_id") == option_id]
        )
        option_fares = _sort_created(
            [item for item in detail.get("fare_bundles", []) if item.get("option_id") == option_id]
        )
        option_pricing = _sort_created(
            [item for item in detail.get("pricing_lines", []) if item.get("option_id") == option_id]
        )

        trip_passengers = (
            await self.db.collection("trip_passengers").find_many(
                {"agency_id": agency_id, "trip_id": trip_id}
            )
            if trip_id
            else []
        )
        request_passengers = (
            await self.db.collection("request_passengers").find_many(
                {"agency_id": agency_id, "request_id": request_id, "status": "active"}
            )
            if request_id
            else []
        )
        passengers = trip_passengers or request_passengers
        services = await self._collect_services(agency_id, request_id, trip_id)
        pets = await self._collect_request_records(
            agency_id,
            request_id,
            "request_pets",
            "request_pet_segment_transport",
        )
        special_items = await self._collect_request_records(
            agency_id,
            request_id,
            "request_special_items",
            "request_special_item_segments",
        )

        rules_summary = option.get("rules_summary_json") or {}
        artifacts = _extract_rule_artifacts(rules_summary, option.get("warnings_json") or [])
        if not option_segments:
            artifacts["warnings"].append(_warning("Accepted option has no offer segments.", "segments_missing"))
        if not option_pricing and not (option.get("pricing_summary_json") or {}).get("total_amount"):
            artifacts["warnings"].append(_warning("Accepted option has no pricing lines or total.", "pricing_missing"))
        if not passengers:
            artifacts["warnings"].append(_warning("Linked trip or request has no passengers.", "passengers_missing"))

        pricing_summary = option.get("pricing_summary_json") or {}
        fare_primary = option_fares[0] if option_fares else {}
        return {
            "workspace": workspace,
            "option": option,
            "request": detail.get("request"),
            "passengers": passengers,
            "pricing": {"summary": pricing_summary, "lines": option_pricing},
            "routing": {"segments": option_segments, "routing_options": option_routings},
            "fare_bundle": {"primary": fare_primary, "items": option_fares},
            "services": services,
            "pets": pets,
            "special_items": special_items,
            "rules_feasibility": {
                "rules_summary": rules_summary,
                "service_feasibility": option.get("service_feasibility_json") or {},
            },
            "warnings": artifacts["warnings"],
            "required_documents": artifacts["required_documents"],
            "policy_violations": artifacts["policy_violations"],
            "ssr_osi_preview": {"ssr": artifacts["ssr"], "osi": artifacts["osi"]},
        }

    async def build_booking_readiness_package(
        self,
        agency_id: str,
        acceptance_id: str,
        user: dict,
        provider_target: str | BookingProviderTarget = BookingProviderTarget.MANUAL,
    ) -> dict[str, Any] | None:
        acceptance = await self.db.collection("offer_acceptances").find_one(
            {"agency_id": agency_id, "id": acceptance_id}
        )
        if (
            acceptance is None
            or acceptance.get("status") != OfferAcceptanceStatus.ACCEPTED.value
            or not acceptance.get("trip_id")
        ):
            return None
        trip_snapshot = await self.db.collection(
            "trip_accepted_offer_snapshots"
        ).find_one({"agency_id": agency_id, "acceptance_id": acceptance_id})
        if trip_snapshot is None:
            return None

        pricing_snapshot = trip_snapshot.get("confirmed_pricing_json") or {}
        pricing = pricing_snapshot.get("summary") or pricing_snapshot
        segments = trip_snapshot.get("confirmed_segments_json") or []
        passengers = trip_snapshot.get("confirmed_passengers_json") or []
        policy_readiness = trip_snapshot.get("policy_readiness_snapshot_json") or {}
        policy_violations = policy_readiness.get("policy_violations") or []
        warnings = policy_readiness.get("warnings") or []
        required_documents = policy_readiness.get("required_documents") or []
        ssr_osi = trip_snapshot.get("ssr_osi_preview_json") or {}
        rules_feasibility = policy_readiness.get("rules_feasibility") or {}
        checks = {
            "passengers_present": bool(passengers),
            "segments_present": bool(segments),
            "pricing_present": pricing.get("total_amount") is not None,
            "currency_present": bool(pricing.get("currency")),
            "special_service_warnings_evaluated": bool(
                rules_feasibility.get("rules_summary")
            ),
            "blocked_policy_violations_absent": not bool(policy_violations),
            "required_documents_listed": True,
            "ssr_osi_preview_generated": bool(
                ssr_osi.get("ssr") or ssr_osi.get("osi")
            ),
            "provider_target_selected": bool(provider_target),
        }
        minimum_ready = (
            checks["passengers_present"]
            and checks["segments_present"]
            and checks["pricing_present"]
            and checks["currency_present"]
        )
        if policy_violations:
            status = BookingReadinessStatus.BLOCKED.value
        elif minimum_ready:
            status = BookingReadinessStatus.READY.value
        else:
            status = BookingReadinessStatus.DRAFT.value

        package = BookingReadinessPackage(
            agency_id=agency_id,
            trip_id=acceptance["trip_id"],
            request_id=acceptance.get("request_id"),
            workspace_id=acceptance.get("workspace_id"),
            option_id=acceptance.get("option_id"),
            acceptance_id=acceptance_id,
            status=status,
            provider_target=provider_target or BookingProviderTarget.MANUAL,
            passengers_snapshot_json=passengers,
            segments_snapshot_json=segments,
            pricing_snapshot_json=pricing_snapshot,
            services_snapshot_json=trip_snapshot.get("confirmed_services_json") or {},
            pets_snapshot_json=trip_snapshot.get("confirmed_pets_json") or {},
            special_items_snapshot_json=trip_snapshot.get(
                "confirmed_special_items_json"
            )
            or {},
            ssr_json=ssr_osi.get("ssr", []),
            osi_json=ssr_osi.get("osi", []),
            warnings_json=warnings,
            required_documents_json=required_documents,
            policy_violations_json=policy_violations,
            readiness_checks_json=checks,
            created_by_user_id=user.get("id"),
        )
        existing = await self.db.collection("booking_readiness_packages").find_one(
            {"agency_id": agency_id, "acceptance_id": acceptance_id}
        )
        if existing:
            updates = package.model_dump(mode="json")
            updates.pop("id", None)
            updates.pop("created_at", None)
            created = await self.db.collection("booking_readiness_packages").update_one(
                {"agency_id": agency_id, "id": existing["id"]},
                updates,
            )
        else:
            created = await self.db.collection("booking_readiness_packages").insert_one(
                package.model_dump(mode="json")
            )
        return created

    async def get_workspace_acceptance(self, agency_id: str, workspace_id: str) -> dict[str, Any]:
        acceptances = await self.db.collection("offer_acceptances").find_many(
            {"agency_id": agency_id, "workspace_id": workspace_id}
        )
        current = self._latest(
            [item for item in acceptances if item.get("status") == OfferAcceptanceStatus.ACCEPTED.value]
        )
        latest = current or self._latest(acceptances)
        readiness = None
        trip_snapshot = None
        if latest:
            readiness = await self.db.collection("booking_readiness_packages").find_one(
                {"agency_id": agency_id, "acceptance_id": latest["id"]}
            )
            trip_snapshot = await self.db.collection("trip_accepted_offer_snapshots").find_one(
                {"agency_id": agency_id, "acceptance_id": latest["id"]}
            )
        return {
            "acceptance": latest,
            "trip_snapshot": trip_snapshot,
            "booking_readiness": readiness,
            "history": acceptances,
        }

    async def get_trip_accepted_offer(self, agency_id: str, trip_id: str) -> dict[str, Any]:
        snapshot = await self.db.collection("trip_accepted_offer_snapshots").find_one(
            {"agency_id": agency_id, "trip_id": trip_id}
        )
        acceptance = None
        if snapshot:
            acceptance = await self.db.collection("offer_acceptances").find_one(
                {"agency_id": agency_id, "id": snapshot.get("acceptance_id")}
            )
        return {"accepted_offer": snapshot, "acceptance": acceptance}

    async def get_booking_readiness_for_trip(self, agency_id: str, trip_id: str) -> dict[str, Any]:
        packages = await self.db.collection("booking_readiness_packages").find_many(
            {"agency_id": agency_id, "trip_id": trip_id}
        )
        return {"booking_readiness": self._latest(packages), "history": packages}

    async def rebuild_booking_readiness(self, agency_id: str, acceptance_id: str, user: dict) -> dict[str, Any] | None:
        acceptance = await self.db.collection("offer_acceptances").find_one(
            {"agency_id": agency_id, "id": acceptance_id}
        )
        if acceptance is None:
            return None
        existing = await self.db.collection("booking_readiness_packages").find_one(
            {"agency_id": agency_id, "acceptance_id": acceptance_id}
        )
        provider_target = (existing or {}).get("provider_target") or BookingProviderTarget.MANUAL.value
        readiness = await self.build_booking_readiness_package(
            agency_id,
            acceptance_id,
            user,
            provider_target=provider_target,
        )
        await write_offer_builder_audit(
            self.db,
            agency_id,
            user.get("id"),
            "booking_readiness.rebuilt",
            "offer_acceptance",
            acceptance_id,
            "Rebuilt booking readiness package.",
            {"trip_id": acceptance.get("trip_id")},
        )
        return readiness

    async def cancel_acceptance(self, agency_id: str, acceptance_id: str, user: dict) -> dict[str, Any] | None:
        acceptance = await self.db.collection("offer_acceptances").find_one(
            {"agency_id": agency_id, "id": acceptance_id}
        )
        if acceptance is None:
            return None
        if acceptance.get("status") != OfferAcceptanceStatus.ACCEPTED.value:
            raise CommercialLifecycleError(
                "Only an active acceptance may be revoked.",
                code="ACCEPTANCE_NOT_ACTIVE",
            )
        validate_lifecycle_transition("acceptance", acceptance.get("status"), "revoked")
        revoked_at = datetime.now(timezone.utc)
        cancelled = await self.db.collection("offer_acceptances").update_one(
            {"agency_id": agency_id, "id": acceptance_id},
            {
                "status": OfferAcceptanceStatus.REVOKED.value,
                "revoked_at": revoked_at,
                "reconciliation_status": "revoked_downstream_preserved",
            },
        )
        readiness = await self.db.collection("booking_readiness_packages").find_one(
            {"agency_id": agency_id, "acceptance_id": acceptance_id}
        )
        if readiness and readiness.get("status") != BookingReadinessStatus.BOOKED.value:
            readiness = await self.db.collection("booking_readiness_packages").update_one(
                {"agency_id": agency_id, "id": readiness["id"]},
                {"status": BookingReadinessStatus.CANCELLED.value},
            )
        await write_offer_builder_audit(
            self.db,
            agency_id,
            user.get("id"),
            "offer_acceptance.cancelled",
            "offer_acceptance",
            acceptance_id,
            "Cancelled offer acceptance.",
            {
                "trip_id": acceptance.get("trip_id"),
                "workspace_id": acceptance.get("workspace_id"),
            },
        )
        await write_lifecycle_evidence(
            self.db,
            agency_id=agency_id,
            actor_user_id=user.get("id"),
            event_type="offer_acceptance.lifecycle.revoked",
            entity_type="offer_acceptance",
            entity_id=acceptance_id,
            summary="Revoked acceptance while preserving its Trip and immutable evidence.",
            previous_status="accepted",
            next_status="revoked",
            request_id=acceptance.get("request_id"),
            trip_id=acceptance.get("trip_id"),
            metadata={
                "accepted_snapshot_id": acceptance.get("accepted_snapshot_id"),
                "downstream_records_preserved": True,
            },
        )
        return {"acceptance": cancelled, "booking_readiness": readiness}

    async def _collect_services(self, agency_id: str, request_id: str | None, trip_id: str | None) -> dict[str, Any]:
        trip_services = (
            await self.db.collection("trip_service_items").find_many(
                {"agency_id": agency_id, "trip_id": trip_id}
            )
            if trip_id
            else []
        )
        passenger_services = (
            await self.db.collection("passenger_service_requests").find_many(
                {"agency_id": agency_id, "trip_id": trip_id}
            )
            if trip_id
            else []
        )
        if request_id:
            passenger_services.extend(
                await self.db.collection("passenger_service_requests").find_many(
                    {"agency_id": agency_id, "request_id": request_id}
                )
            )
            scoped = await self.db.collection("request_passenger_segment_services").find_many(
                {"agency_id": agency_id, "request_id": request_id}
            )
            requested = await self.db.collection("requested_services").find_many(
                {"agency_id": agency_id, "request_id": request_id}
            )
        else:
            scoped = []
            requested = []
        return {
            "trip_service_items": await self._with_catalogue_snapshots(trip_services),
            "passenger_service_requests": await self._with_catalogue_snapshots(passenger_services),
            "request_passenger_segment_services": await self._with_catalogue_snapshots(scoped),
            "requested_services": await self._with_catalogue_snapshots(requested),
        }

    async def _with_catalogue_snapshots(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in items:
            row = dict(item)
            snapshot = row.get("service_catalogue_snapshot_json") or {}
            if not snapshot:
                record = await find_service_catalogue_record(
                    self.db,
                    row.get("service_key") or row.get("service_code") or row.get("service_type") or row.get("ssr_code"),
                )
                snapshot = service_catalogue_snapshot(record)
            if snapshot:
                row["service_catalogue_snapshot_json"] = snapshot
                row["service_catalogue_id"] = row.get("service_catalogue_id") or snapshot.get("service_catalogue_id")
                row["service_key"] = row.get("service_key") or snapshot.get("service_key")
                row["service_label"] = row.get("service_label") or row.get("service_name") or snapshot.get("label")
                row["service_catalogue_category"] = row.get("service_catalogue_category") or snapshot.get("category") or snapshot.get("rules_category")
            enriched.append(row)
        return enriched

    async def _collect_request_records(
        self,
        agency_id: str,
        request_id: str | None,
        parent_collection: str,
        child_collection: str,
    ) -> dict[str, Any]:
        if not request_id:
            return {"items": [], "segments": []}
        return {
            "items": await self.db.collection(parent_collection).find_many(
                {"agency_id": agency_id, "request_id": request_id, "status": "active"}
            ),
            "segments": await self.db.collection(child_collection).find_many(
                {"agency_id": agency_id, "request_id": request_id}
            ),
        }

    async def _create_trip_snapshot_once(
        self,
        agency_id: str,
        trip_id: str,
        acceptance: dict[str, Any],
        immutable_payload: dict[str, Any],
        source_hash: str,
    ) -> dict[str, Any]:
        existing = await self.db.collection("trip_accepted_offer_snapshots").find_one(
            {"agency_id": agency_id, "acceptance_id": acceptance["id"]}
        )
        if existing:
            if existing.get("source_hash") != source_hash:
                raise CommercialLifecycleError(
                    "Accepted snapshot already exists with different content.",
                    code="ACCEPTED_SNAPSHOT_HASH_CONFLICT",
                )
            return existing
        item = TripAcceptedOfferSnapshot(
            agency_id=agency_id,
            trip_id=trip_id,
            request_id=acceptance.get("request_id"),
            workspace_id=acceptance["workspace_id"],
            option_id=acceptance["option_id"],
            acceptance_id=acceptance["id"],
            request_version=immutable_payload.get("request_version"),
            offer_version=immutable_payload["offer_version"],
            option_version=immutable_payload["option_version"],
            client_profile_id=immutable_payload.get("client_profile_id"),
            confirmed_segments_json=immutable_payload["itinerary_segments"],
            confirmed_passengers_json=immutable_payload["passengers"],
            confirmed_fare_bundle_json=immutable_payload["fare"],
            confirmed_pricing_json=immutable_payload["pricing"],
            confirmed_services_json=immutable_payload["services"],
            confirmed_pets_json=immutable_payload["pets"],
            confirmed_special_items_json=immutable_payload["special_items"],
            ssr_osi_preview_json=immutable_payload.get("ssr_osi_preview", {}),
            booking_readiness_json={},
            airlines_snapshot_json=immutable_payload.get("airlines", []),
            cabins_snapshot_json=immutable_payload.get("cabins", []),
            baggage_snapshot_json=immutable_payload.get("baggage", {}),
            airline_charges_snapshot_json=immutable_payload.get("airline_charges", {}),
            agency_fees_snapshot_json=immutable_payload.get("agency_fees", {}),
            taxes_snapshot_json=immutable_payload.get("taxes", {}),
            total_snapshot_json=immutable_payload.get("total", {}),
            currency=immutable_payload.get("currency"),
            terms_snapshot_json=immutable_payload.get("terms", {}),
            policy_readiness_snapshot_json=immutable_payload.get("policy_readiness", {}),
            source_hash=source_hash,
            created_by_user_id=immutable_payload.get("created_by"),
            immutable=True,
        )
        existing_trip_snapshot = await self.db.collection(
            "trip_accepted_offer_snapshots"
        ).find_one(
            {"agency_id": agency_id, "trip_id": trip_id}
        )
        if existing_trip_snapshot:
            raise CommercialLifecycleError(
                "Trip already has immutable accepted-offer evidence.",
                code="TRIP_ACCEPTED_SNAPSHOT_CONFLICT",
            )
        return await self.db.collection("trip_accepted_offer_snapshots").insert_one(
            item.model_dump(mode="json")
        )

    def _assert_offer_actionable(
        self,
        workspace: dict[str, Any],
        override_reason: str | None,
    ) -> None:
        status_value = canonical_status("offer", workspace.get("status"))
        if status_value == "expired" or self._is_expired(workspace.get("expires_at")):
            raise CommercialLifecycleError(
                "Expired Offer versions cannot be accepted.",
                code="OFFER_EXPIRED",
            )
        if status_value == "superseded":
            raise CommercialLifecycleError(
                "Superseded Offer versions cannot be accepted.",
                code="OFFER_SUPERSEDED",
            )
        if status_value != "delivered":
            raise CommercialLifecycleError(
                "Offer must be delivered before an acceptance decision is recorded.",
                code="OFFER_NOT_DELIVERED",
            )
        if override_reason:
            raise CommercialLifecycleError(
                "Override acceptance is not enabled by this repair; use a governed current Offer revision.",
                code="OFFER_OVERRIDE_NOT_AUTHORIZED",
            )

    def _is_expired(self, value: Any) -> bool:
        if not value:
            return False
        if isinstance(value, datetime):
            expiry = value
        else:
            try:
                expiry = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return True
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry <= datetime.now(timezone.utc)

    def _immutable_payload(
        self,
        *,
        agency_id: str,
        request_id: str | None,
        trip_id: str,
        workspace: dict[str, Any],
        option: dict[str, Any],
        snapshot: dict[str, Any],
        client_summary: dict[str, Any],
        actor_user_id: str | None,
        acceptance_terms_version: str | None,
    ) -> dict[str, Any]:
        segments = snapshot["routing"].get("segments", [])
        fare = snapshot["fare_bundle"]
        pricing = snapshot["pricing"]
        pricing_summary = pricing.get("summary") or {}
        airlines = []
        cabins = []
        for segment in segments:
            airline = {
                "marketing_airline_code": segment.get("marketing_airline_code"),
                "operating_airline_code": segment.get("operating_airline_code"),
            }
            if airline not in airlines:
                airlines.append(airline)
            cabin = {
                "cabin_class": segment.get("cabin_class"),
                "booking_class": segment.get("booking_class"),
                "fare_basis": segment.get("fare_basis"),
            }
            if cabin not in cabins:
                cabins.append(cabin)
        primary_fare = fare.get("primary") or {}
        return {
            "agency_id": agency_id,
            "request_id": request_id,
            "request_version": (
                snapshot.get("request") or {}
            ).get("request_version"),
            "trip_id": trip_id,
            "offer_id": workspace["id"],
            "offer_version": int(workspace.get("version") or 1),
            "option_id": option["id"],
            "option_version": int(option.get("version") or 1),
            "client_profile_id": workspace.get("client_profile_id")
            or (workspace.get("client_summary_json") or {}).get("client_id"),
            "passengers": snapshot.get("passengers", []),
            "itinerary_segments": segments,
            "airlines": airlines,
            "cabins": cabins,
            "fare": fare,
            "baggage": primary_fare.get("included_baggage_json") or {},
            "pricing": pricing,
            "services": snapshot["services"],
            "pets": snapshot["pets"],
            "special_items": snapshot["special_items"],
            "airline_charges": option.get("airline_charge_snapshot_json") or {},
            "agency_fees": option.get("agency_fee_snapshot_json") or {},
            "taxes": option.get("tax_snapshot_json") or {},
            "total": option.get("total_snapshot_json")
            or {
                "total_amount": pricing_summary.get("total_amount"),
                "currency": pricing_summary.get("currency"),
                "server_derived": True,
            },
            "currency": pricing_summary.get("currency")
            or option.get("currency")
            or workspace.get("currency"),
            "terms": {
                "acceptance_terms_version": acceptance_terms_version,
                "offer_expires_at": workspace.get("expires_at"),
                "delivered_at": workspace.get("delivered_at"),
                "client_visible_summary": client_summary,
            },
            "policy_readiness": {
                "rules_feasibility": snapshot["rules_feasibility"],
                "warnings": snapshot.get("warnings", []),
                "required_documents": snapshot.get("required_documents", []),
                "policy_violations": snapshot.get("policy_violations", []),
            },
            "ssr_osi_preview": snapshot.get("ssr_osi_preview", {}),
            "created_by": actor_user_id,
        }

    async def _acceptance_result(
        self,
        acceptance: dict[str, Any],
        *,
        idempotent: bool,
    ) -> dict[str, Any]:
        trip_snapshot = await self.db.collection(
            "trip_accepted_offer_snapshots"
        ).find_one(
            {
                "agency_id": acceptance["agency_id"],
                "acceptance_id": acceptance["id"],
            }
        )
        readiness = await self.db.collection("booking_readiness_packages").find_one(
            {
                "agency_id": acceptance["agency_id"],
                "acceptance_id": acceptance["id"],
            }
        )
        return {
            "acceptance": acceptance,
            "trip_snapshot": trip_snapshot,
            "booking_readiness": readiness,
            "warnings": (readiness or {}).get("warnings_json") or [],
            "required_documents": (readiness or {}).get(
                "required_documents_json"
            )
            or [],
            "ssr_osi_preview": {
                "ssr": (readiness or {}).get("ssr_json") or [],
                "osi": (readiness or {}).get("osi_json") or [],
            },
            "idempotent_reused": idempotent,
        }

    def _latest(self, items: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not items:
            return None
        return sorted(
            items,
            key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
            reverse=True,
        )[0]
