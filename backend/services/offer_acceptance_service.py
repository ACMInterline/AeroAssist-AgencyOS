from __future__ import annotations

from typing import Any

from database import Database
from models import (
    BookingProviderTarget,
    BookingReadinessPackage,
    BookingReadinessStatus,
    OfferAcceptance,
    OfferAcceptanceCreate,
    OfferAcceptanceStatus,
    OfferOptionStatus,
    OfferWorkspaceStatus,
    TripAcceptedOfferSnapshot,
)
from services.offer_builder_service import OfferBuilderService, write_offer_builder_audit
from services.service_catalogue_service import find_service_catalogue_record, service_catalogue_snapshot
from services.trip_dossier_service import create_trip_from_request


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

        request_id = workspace.get("request_id") or option.get("request_id")
        trip_id = workspace.get("trip_id") or option.get("trip_id")
        lifecycle_warnings: list[dict[str, Any]] = []
        if not trip_id and request_id:
            trip = await create_trip_from_request(self.db, agency_id, request_id, actor_user_id)
            trip_id = trip["id"]
            workspace = await self.db.collection("offer_workspaces").update_one(
                {"agency_id": agency_id, "id": workspace_id},
                {
                    "trip_id": trip_id,
                    "status": OfferWorkspaceStatus.ACCEPTED.value,
                    "updated_by_user_id": actor_user_id,
                },
            ) or workspace
            await self.db.collection("offer_options").update_one(
                {"agency_id": agency_id, "id": option_id},
                {"trip_id": trip_id},
            )
        elif not trip_id:
            lifecycle_warnings.append(
                _warning("Accepted offer has no linked trip; booking readiness was not created.", "trip_missing")
            )

        if not (option.get("pricing_summary_json") or {}).get("total_amount"):
            await self.builder.recalculate_option_pricing(agency_id, option_id, actor_user_id)
        await self.builder.evaluate_option_rules(agency_id, option_id, actor_user_id)
        snapshot = await self.build_acceptance_snapshot(agency_id, option_id)
        if snapshot is None:
            return None
        snapshot["warnings"] = [*snapshot.get("warnings", []), *lifecycle_warnings]

        previous_acceptances = await self.db.collection("offer_acceptances").find_many(
            {
                "agency_id": agency_id,
                "workspace_id": workspace_id,
                "status": OfferAcceptanceStatus.ACCEPTED.value,
            }
        )
        superseded_ids: list[str] = []
        for previous in previous_acceptances:
            superseded = await self.db.collection("offer_acceptances").update_one(
                {"agency_id": agency_id, "id": previous["id"]},
                {"status": OfferAcceptanceStatus.SUPERSEDED.value},
            )
            if superseded:
                superseded_ids.append(superseded["id"])

        client_summary = payload.client_visible_summary_json or {
            "option_label": option.get("label"),
            "route_summary": _route_summary(snapshot["routing"].get("segments", [])),
            "pricing": snapshot["pricing"].get("summary") or {},
            "fare_bundle": snapshot["fare_bundle"].get("primary") or {},
        }
        acceptance = OfferAcceptance(
            agency_id=agency_id,
            workspace_id=workspace_id,
            option_id=option_id,
            request_id=request_id,
            trip_id=trip_id,
            accepted_by_user_id=actor_user_id,
            acceptance_source=payload.acceptance_source,
            status=OfferAcceptanceStatus.ACCEPTED,
            accepted_pricing_snapshot_json=snapshot["pricing"],
            accepted_routing_snapshot_json=snapshot["routing"],
            accepted_fare_bundle_snapshot_json=snapshot["fare_bundle"],
            accepted_services_snapshot_json=snapshot["services"],
            accepted_pets_snapshot_json=snapshot["pets"],
            accepted_special_items_snapshot_json=snapshot["special_items"],
            rules_feasibility_snapshot_json=snapshot["rules_feasibility"],
            client_visible_summary_json=client_summary,
            internal_notes=payload.internal_notes,
        )
        created = await self.db.collection("offer_acceptances").insert_one(acceptance.model_dump(mode="json"))

        await self.db.collection("offer_options").update_one(
            {"agency_id": agency_id, "id": option_id},
            {
                "status": OfferOptionStatus.RECOMMENDED.value,
                "recommendation_rank": 1,
                "recommendation_tag": "Accepted",
            },
        )
        await self.db.collection("offer_workspaces").update_one(
            {"agency_id": agency_id, "id": workspace_id},
            {
                "status": OfferWorkspaceStatus.ACCEPTED.value,
                "trip_id": trip_id,
                "updated_by_user_id": actor_user_id,
            },
        )

        trip_snapshot = None
        readiness = None
        if trip_id:
            trip_snapshot = await self._upsert_trip_snapshot(agency_id, trip_id, created, snapshot)
            readiness = await self.build_booking_readiness_package(
                agency_id,
                created["id"],
                user,
                provider_target=payload.provider_target,
            )

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
                "trip_id": trip_id,
                "superseded_acceptance_ids": superseded_ids,
            },
        )
        return {
            "acceptance": created,
            "trip_snapshot": trip_snapshot,
            "booking_readiness": readiness,
            "warnings": snapshot.get("warnings", []),
            "required_documents": snapshot.get("required_documents", []),
            "ssr_osi_preview": snapshot.get("ssr_osi_preview", {}),
            "superseded_acceptance_ids": superseded_ids,
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
        if acceptance is None or not acceptance.get("trip_id"):
            return None
        snapshot = await self.build_acceptance_snapshot(agency_id, acceptance["option_id"])
        if snapshot is None:
            return None

        pricing = snapshot["pricing"].get("summary") or {}
        segments = snapshot["routing"].get("segments", [])
        passengers = snapshot.get("passengers", [])
        policy_violations = snapshot.get("policy_violations", [])
        checks = {
            "passengers_present": bool(passengers),
            "segments_present": bool(segments),
            "pricing_present": pricing.get("total_amount") is not None,
            "currency_present": bool(pricing.get("currency")),
            "special_service_warnings_evaluated": bool(snapshot["rules_feasibility"].get("rules_summary")),
            "blocked_policy_violations_absent": not bool(policy_violations),
            "required_documents_listed": True,
            "ssr_osi_preview_generated": bool(
                snapshot["ssr_osi_preview"].get("ssr") or snapshot["ssr_osi_preview"].get("osi")
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
            pricing_snapshot_json=snapshot["pricing"],
            services_snapshot_json=snapshot["services"],
            pets_snapshot_json=snapshot["pets"],
            special_items_snapshot_json=snapshot["special_items"],
            ssr_json=snapshot["ssr_osi_preview"].get("ssr", []),
            osi_json=snapshot["ssr_osi_preview"].get("osi", []),
            warnings_json=snapshot.get("warnings", []),
            required_documents_json=snapshot.get("required_documents", []),
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
        await self._refresh_trip_snapshot_readiness(agency_id, acceptance, created)
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
        cancelled = await self.db.collection("offer_acceptances").update_one(
            {"agency_id": agency_id, "id": acceptance_id},
            {"status": OfferAcceptanceStatus.CANCELLED.value},
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

    async def _upsert_trip_snapshot(
        self,
        agency_id: str,
        trip_id: str,
        acceptance: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        item = TripAcceptedOfferSnapshot(
            agency_id=agency_id,
            trip_id=trip_id,
            request_id=acceptance.get("request_id"),
            workspace_id=acceptance["workspace_id"],
            option_id=acceptance["option_id"],
            acceptance_id=acceptance["id"],
            confirmed_segments_json=snapshot["routing"].get("segments", []),
            confirmed_passengers_json=snapshot.get("passengers", []),
            confirmed_fare_bundle_json=snapshot["fare_bundle"],
            confirmed_pricing_json=snapshot["pricing"],
            confirmed_services_json=snapshot["services"],
            confirmed_pets_json=snapshot["pets"],
            confirmed_special_items_json=snapshot["special_items"],
            ssr_osi_preview_json=snapshot.get("ssr_osi_preview", {}),
            booking_readiness_json={},
        )
        existing = await self.db.collection("trip_accepted_offer_snapshots").find_one(
            {"agency_id": agency_id, "trip_id": trip_id}
        )
        if existing:
            updates = item.model_dump(mode="json")
            updates.pop("id", None)
            updates.pop("created_at", None)
            return await self.db.collection("trip_accepted_offer_snapshots").update_one(
                {"agency_id": agency_id, "id": existing["id"]},
                updates,
            )
        return await self.db.collection("trip_accepted_offer_snapshots").insert_one(
            item.model_dump(mode="json")
        )

    async def _refresh_trip_snapshot_readiness(
        self,
        agency_id: str,
        acceptance: dict[str, Any],
        readiness: dict[str, Any] | None,
    ) -> None:
        if not readiness or not acceptance.get("trip_id"):
            return
        await self.db.collection("trip_accepted_offer_snapshots").update_one(
            {"agency_id": agency_id, "trip_id": acceptance["trip_id"]},
            {
                "booking_readiness_json": {
                    "package_id": readiness.get("id"),
                    "status": readiness.get("status"),
                    "readiness_checks": readiness.get("readiness_checks_json") or {},
                    "warnings": readiness.get("warnings_json") or [],
                    "required_documents": readiness.get("required_documents_json") or [],
                }
            },
        )

    def _latest(self, items: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not items:
            return None
        return sorted(
            items,
            key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
            reverse=True,
        )[0]
