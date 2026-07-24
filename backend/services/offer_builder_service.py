from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AuditEvent,
    OfferBuilderPricingLineType,
    OfferBuilderSegment,
    OfferBuilderSegmentCreate,
    OfferFareBundle,
    OfferFareBundleCreate,
    OfferOption,
    OfferOptionCreate,
    OfferOptionStatus,
    OfferOptionUpdate,
    OfferPricingLine,
    OfferPricingLineCreate,
    OfferRoutingOption,
    OfferRoutingOptionCreate,
    OfferWorkspace,
    OfferWorkspaceCreate,
    OfferWorkspaceStatus,
    OfferWorkspaceTransitionRequest,
    OfferWorkspaceUpdate,
    OperationalTimelineCreate,
    new_id,
)
from services.canonical_commercial_lifecycle_service import (
    CommercialLifecycleError,
    FROZEN_OFFER_STATUSES,
    canonical_status,
    validate_lifecycle_transition,
    write_lifecycle_evidence,
)
from services.canonical_reference_service import reference_snapshot, resolve_reference
from services.exception_engine_service import ExceptionEngineService
from services.rules_and_services_registry import normalize_code
from services.service_catalogue_service import find_service_catalogue_record, service_catalogue_snapshot
from services.special_services_service import category_for_service_type
from services.ssr_osi_generator_service import SsrOsiGeneratorService
from services.timeline_workspace_service import OperationalTimelineService


def clean_update_payload(payload: Any) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True, mode="json")


def _compact(value: Any, limit: int = 180) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:limit] if text else None


def _sort_by_created(items: list[dict[str, Any]], reverse: bool = False) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=reverse)


def _sort_segments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (int(item.get("sequence") or 0), str(item.get("departure_at") or "")),
    )


def _service_type(service: dict[str, Any]) -> str:
    return normalize_code(service.get("service_key") or service.get("service_type") or service.get("service_code") or service.get("ssr_code")) or "OTHS"


async def write_offer_builder_audit(
    db: Database,
    agency_id: str,
    actor_user_id: str | None,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


class OfferBuilderService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.exception_engine = ExceptionEngineService(db)
        self.ssr_osi_generator = SsrOsiGeneratorService(db)
        self.timelines = OperationalTimelineService(db)

    async def get_request_or_none(self, agency_id: str, request_id: str | None) -> dict[str, Any] | None:
        if not request_id:
            return None
        return await self.db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})

    async def get_trip_or_none(self, agency_id: str, trip_id: str | None) -> dict[str, Any] | None:
        if not trip_id:
            return None
        return await self.db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": trip_id})

    async def get_workspace_or_none(self, agency_id: str, workspace_id: str) -> dict[str, Any] | None:
        return await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "id": workspace_id})

    async def get_option_or_none(self, agency_id: str, option_id: str) -> dict[str, Any] | None:
        return await self.db.collection("offer_options").find_one({"agency_id": agency_id, "id": option_id})

    async def list_workspaces(
        self,
        agency_id: str,
        request_id: str | None = None,
        trip_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {"agency_id": agency_id}
        if request_id:
            filters["request_id"] = request_id
        if trip_id:
            filters["trip_id"] = trip_id
        if status:
            filters["status"] = status
        items = await self.db.collection("offer_workspaces").find_many(filters)
        option_counts: dict[str, int] = {}
        for option in await self.db.collection("offer_options").find_many({"agency_id": agency_id}):
            option_counts[option.get("workspace_id")] = option_counts.get(option.get("workspace_id"), 0) + 1
        request_ids = {item.get("request_id") for item in items if item.get("request_id")}
        trip_ids = {item.get("trip_id") for item in items if item.get("trip_id")}
        requests = {
            request["id"]: request
            for request in await self.db.collection("travel_requests").find_many({"agency_id": agency_id})
            if request["id"] in request_ids
        }
        trips = {
            trip["id"]: trip
            for trip in await self.db.collection("trip_dossiers").find_many({"agency_id": agency_id})
            if trip["id"] in trip_ids
        }
        enriched = [
            {
                **item,
                "option_count": option_counts.get(item["id"], 0),
                "request": requests.get(item.get("request_id")),
                "trip": trips.get(item.get("trip_id")),
            }
            for item in items
        ]
        return sorted(
            enriched,
            key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
            reverse=True,
        )

    async def workspace_detail(self, agency_id: str, workspace_id: str) -> dict[str, Any] | None:
        workspace = await self.get_workspace_or_none(agency_id, workspace_id)
        if workspace is None:
            return None
        options = await self.db.collection("offer_options").find_many({"agency_id": agency_id, "workspace_id": workspace_id})
        options = sorted(
            options,
            key=lambda item: (
                int(item.get("option_order") or 0),
                str(item.get("created_at") or ""),
                str(item.get("id") or ""),
            ),
        )
        option_ids = {option["id"] for option in options}
        routings = [
            item
            for item in await self.db.collection("offer_routing_options").find_many({"agency_id": agency_id})
            if item.get("option_id") in option_ids
        ]
        segments = [
            item
            for item in await self.db.collection("offer_builder_segments").find_many({"agency_id": agency_id})
            if item.get("option_id") in option_ids
        ]
        fare_bundles = [
            item
            for item in await self.db.collection("offer_fare_bundles").find_many({"agency_id": agency_id})
            if item.get("option_id") in option_ids
        ]
        pricing_lines = [
            item
            for item in await self.db.collection("offer_pricing_lines").find_many({"agency_id": agency_id})
            if item.get("option_id") in option_ids
        ]
        snapshots = await self.db.collection("offer_comparison_snapshots").find_many({"agency_id": agency_id, "workspace_id": workspace_id})
        return {
            "workspace": workspace,
            "request": await self.get_request_or_none(agency_id, workspace.get("request_id")),
            "trip": await self.get_trip_or_none(agency_id, workspace.get("trip_id")),
            "options": options,
            "routing_options": _sort_by_created(routings),
            "segments": _sort_segments(segments),
            "fare_bundles": _sort_by_created(fare_bundles),
            "pricing_lines": _sort_by_created(pricing_lines),
            "comparison_snapshots": _sort_by_created(snapshots, reverse=True),
        }

    async def create_workspace(self, agency_id: str, payload: OfferWorkspaceCreate, actor_user_id: str | None) -> dict[str, Any]:
        data = payload.model_dump(mode="json")
        request = await self.get_request_or_none(agency_id, data.get("request_id"))
        trip = await self.get_trip_or_none(agency_id, data.get("trip_id"))
        if data.get("request_id") and request is None:
            raise ValueError("Request not found.")
        if data.get("trip_id") and trip is None:
            raise ValueError("Trip not found.")
        if request and not data.get("trip_id") and request.get("trip_id"):
            data["trip_id"] = request["trip_id"]
        if trip and not data.get("request_id") and trip.get("primary_request_id"):
            data["request_id"] = trip["primary_request_id"]
        if not data.get("request_id"):
            raise ValueError("Canonical OfferWorkspace requires a TravelRequest.")
        currency_record, currency_state = await resolve_reference(
            self.db,
            "currencies",
            reference_id=data.get("currency_reference_id"),
            code=None if data.get("currency_reference_id") else data.get("currency"),
            agency_id=agency_id,
            allow_uninitialized_legacy=True,
        )
        if currency_record:
            currency = reference_snapshot(currency_record)
            data["currency"] = currency["code"]
            data["currency_reference_id"] = currency["id"]
            data["currency_label_snapshot"] = currency["label"]
        else:
            data["compatibility_metadata"] = {
                "currency_resolution": currency_state,
            }
        workspace = OfferWorkspace(
            agency_id=agency_id,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
            **data,
        )
        created = await self.db.collection("offer_workspaces").insert_one(workspace.model_dump(mode="json"))
        if not created.get("revision_root_id"):
            created = await self.db.collection("offer_workspaces").update_one(
                {"agency_id": agency_id, "id": created["id"]},
                {"revision_root_id": created["id"]},
            ) or created
        source_type = "trip" if created.get("trip_id") else "travel_request"
        source_id = created.get("trip_id") or created.get("request_id")
        transition = {
            "agency_id": agency_id,
            "actor_user_id": actor_user_id,
            "source_entity_type": source_type,
            "source_entity_id": source_id,
            "target_entity_type": "offer_workspace",
            "target_entity_id": created["id"],
            "correlation_id": f"{source_type}:{source_id}:offer-workspace:{created['id']}",
            "occurred_at": str(created.get("created_at") or datetime.utcnow().isoformat()),
            "result": "created",
            "warnings": [],
            "internal_only": True,
            "client_visible_summary": {
                "offer_workspace_id": created["id"],
                "title": created.get("title"),
            },
        }
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_workspace.created",
            "offer_workspace",
            created["id"],
            f"Created offer workspace {created['title']}.",
            {"request_id": created.get("request_id"), "trip_id": created.get("trip_id"), **transition},
        )
        if created.get("trip_id"):
            await self.timelines.create_entry(
                OperationalTimelineCreate(
                    agency_id=agency_id,
                    created_by=actor_user_id,
                    trip_workspace_id=created["trip_id"],
                    event_type="Offer created",
                    event_category="offer_preparation",
                    event_source="offer_builder",
                    event_status="recorded",
                    event_priority="normal",
                    operational_stage="offer_preparation",
                    summary="Offer workspace created from the canonical trip record.",
                    internal_only=True,
                    operational_notes="No live fare search, availability confirmation, or provider action occurred.",
                    metadata=transition,
                ),
                {"id": actor_user_id},
            )
        return created

    async def update_workspace(self, agency_id: str, workspace_id: str, payload: OfferWorkspaceUpdate, actor_user_id: str | None) -> dict[str, Any] | None:
        workspace = await self.get_workspace_or_none(agency_id, workspace_id)
        if workspace is None:
            return None
        updates = clean_update_payload(payload)
        expected_version = updates.pop("expected_version", None)
        revision_reason = updates.pop("revision_reason", None)
        current_version = int(workspace.get("version") or 1)
        if expected_version is not None and expected_version != current_version:
            raise CommercialLifecycleError(
                "Offer changed after it was opened. Refresh before updating.",
                code="STALE_OFFER_VERSION",
            )
        if updates.get("request_id") and await self.get_request_or_none(agency_id, updates["request_id"]) is None:
            raise ValueError("Request not found.")
        if updates.get("trip_id") and await self.get_trip_or_none(agency_id, updates["trip_id"]) is None:
            raise ValueError("Trip not found.")
        if "currency" in updates or "currency_reference_id" in updates:
            currency_record, currency_state = await resolve_reference(
                self.db,
                "currencies",
                reference_id=updates.get("currency_reference_id"),
                code=None if updates.get("currency_reference_id") else updates.get("currency"),
                agency_id=agency_id,
                allow_uninitialized_legacy=True,
            )
            if currency_record:
                currency = reference_snapshot(currency_record)
                updates["currency"] = currency["code"]
                updates["currency_reference_id"] = currency["id"]
                updates["currency_label_snapshot"] = currency["label"]
            else:
                updates["compatibility_metadata"] = {
                    **(workspace.get("compatibility_metadata") or {}),
                    "currency_resolution": currency_state,
                }
        material_fields = {
            "request_id",
            "client_profile_id",
            "trip_id",
            "offer_purpose",
            "title",
            "currency",
            "currency_reference_id",
            "expires_at",
            "client_summary_json",
        }
        if canonical_status("offer", workspace.get("status")) in {
            "delivered",
            "accepted",
            "declined",
            "expired",
            "superseded",
            "cancelled",
        } and material_fields.intersection(updates):
            if not revision_reason:
                raise CommercialLifecycleError(
                    "Commercial edits to a delivered or accepted Offer require a governed revision reason.",
                    code="OFFER_REVISION_REQUIRED",
                )
            return await self._create_workspace_revision(
                agency_id,
                workspace,
                updates,
                actor_user_id,
                revision_reason,
            )
        previous_status = workspace.get("status")
        if "status" in updates:
            requested_status = canonical_status("offer", updates["status"])
            if requested_status in {
                "delivered",
                "accepted",
                "declined",
                "expired",
                "superseded",
            }:
                raise CommercialLifecycleError(
                    "This Offer status requires its dedicated lifecycle action.",
                    code="OFFER_DEDICATED_TRANSITION_REQUIRED",
                )
            validate_lifecycle_transition("offer", previous_status, updates["status"])
        updates["version"] = current_version + 1
        updates["updated_by_user_id"] = actor_user_id
        updated = await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": workspace_id}, updates)
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_workspace.updated",
            "offer_workspace",
            workspace_id,
            "Updated offer workspace.",
            {"fields": sorted(updates.keys())},
        )
        if "status" in updates:
            await write_lifecycle_evidence(
                self.db,
                agency_id=agency_id,
                actor_user_id=actor_user_id,
                event_type="offer.lifecycle.transitioned",
                entity_type="offer_workspace",
                entity_id=workspace_id,
                summary=f"Offer status changed to {updates['status']}.",
                previous_status=previous_status,
                next_status=updates["status"],
                request_id=workspace.get("request_id"),
                trip_id=workspace.get("trip_id"),
            )
        return updated

    async def deliver_workspace(
        self,
        agency_id: str,
        workspace_id: str,
        payload: OfferWorkspaceTransitionRequest,
        actor_user_id: str | None,
    ) -> dict[str, Any] | None:
        workspace = await self.get_workspace_or_none(agency_id, workspace_id)
        if workspace is None:
            return None
        expected_version = payload.expected_version
        current_version = int(workspace.get("version") or 1)
        if expected_version is not None and expected_version != current_version:
            raise CommercialLifecycleError(
                "Offer changed after it was opened. Refresh before delivery.",
                code="STALE_OFFER_VERSION",
            )
        if canonical_status("offer", workspace.get("status")) == "delivered":
            return workspace
        options = await self.db.collection("offer_options").find_many(
            {"agency_id": agency_id, "workspace_id": workspace_id}
        )
        if not options:
            raise CommercialLifecycleError(
                "Offer cannot be delivered without at least one option.",
                code="OFFER_OPTION_REQUIRED",
            )
        for option in options:
            await self.recalculate_option_pricing(
                agency_id, option["id"], actor_user_id
            )
            refreshed = await self.get_option_or_none(agency_id, option["id"])
            if (refreshed or {}).get("pricing_summary_json", {}).get("total_amount") is None:
                raise CommercialLifecycleError(
                    "Every delivered option requires a server-derived total.",
                    code="OFFER_TOTAL_REQUIRED",
                )
        previous_status = workspace.get("status")
        normalized = canonical_status("offer", previous_status)
        if normalized == "draft":
            await self.db.collection("offer_workspaces").update_one(
                {"agency_id": agency_id, "id": workspace_id},
                {
                    "status": OfferWorkspaceStatus.READY.value,
                    "version": current_version + 1,
                    "updated_by_user_id": actor_user_id,
                },
            )
            current_version += 1
            previous_status = OfferWorkspaceStatus.READY.value
        validate_lifecycle_transition("offer", previous_status, "delivered")
        delivered_at = datetime.now(timezone.utc)
        updated = await self.db.collection("offer_workspaces").update_one(
            {"agency_id": agency_id, "id": workspace_id},
            {
                "status": OfferWorkspaceStatus.DELIVERED.value,
                "delivered_at": delivered_at,
                "version": current_version + 1,
                "updated_by_user_id": actor_user_id,
            },
        )
        for option in options:
            await self.db.collection("offer_options").update_one(
                {"agency_id": agency_id, "id": option["id"]},
                {"offer_workspace_version": current_version + 1},
            )
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_workspace.delivered",
            "offer_workspace",
            workspace_id,
            "Recorded Offer delivery readiness without sending a message.",
            {"reason": payload.reason, "version": current_version + 1},
        )
        await write_lifecycle_evidence(
            self.db,
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="offer.lifecycle.delivered",
            entity_type="offer_workspace",
            entity_id=workspace_id,
            summary="Offer marked delivered; no communication was sent.",
            previous_status=previous_status,
            next_status="delivered",
            request_id=workspace.get("request_id"),
            trip_id=workspace.get("trip_id"),
            metadata={"reason": payload.reason, "version": current_version + 1},
        )
        return updated

    async def create_workspace_from_request(self, agency_id: str, request_id: str, actor_user_id: str | None) -> dict[str, Any] | None:
        existing = await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "request_id": request_id})
        if existing:
            return existing
        request = await self.get_request_or_none(agency_id, request_id)
        if request is None:
            return None
        payload = OfferWorkspaceCreate(
            request_id=request_id,
            trip_id=request.get("trip_id"),
            title=f"Offer workspace for {request.get('request_reference') or request.get('title') or request_id}",
            currency="EUR",
            client_summary_json={
                "client_id": request.get("client_id"),
                "request_reference": request.get("request_reference"),
                "title": request.get("title"),
                "route_summary": request.get("route_summary"),
                "service_summary": request.get("service_summary"),
                "passenger_count": request.get("passenger_count"),
                "special_service_count": request.get("special_service_count"),
            },
            internal_notes=request.get("internal_notes"),
        )
        return await self.create_workspace(agency_id, payload, actor_user_id)

    async def create_workspace_from_trip(self, agency_id: str, trip_id: str, actor_user_id: str | None) -> dict[str, Any] | None:
        existing = await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "trip_id": trip_id})
        if existing:
            return existing
        trip = await self.get_trip_or_none(agency_id, trip_id)
        if trip is None:
            return None
        payload = OfferWorkspaceCreate(
            request_id=trip.get("primary_request_id"),
            trip_id=trip_id,
            title=f"Offer workspace for {trip.get('trip_reference') or trip.get('trip_title') or trip_id}",
            currency="EUR",
            client_summary_json={
                "client_id": trip.get("primary_client_id"),
                "trip_reference": trip.get("trip_reference"),
                "title": trip.get("trip_title"),
                "route_summary": trip.get("route_summary"),
                "service_summary": trip.get("service_summary"),
                "passenger_count": trip.get("passenger_count"),
            },
            internal_notes=trip.get("internal_notes"),
        )
        return await self.create_workspace(agency_id, payload, actor_user_id)

    async def create_option(self, agency_id: str, workspace_id: str, payload: OfferOptionCreate, actor_user_id: str | None) -> dict[str, Any] | None:
        workspace = await self.get_workspace_or_none(agency_id, workspace_id)
        if workspace is None:
            return None
        self._assert_workspace_mutable(workspace)
        data = payload.model_dump(mode="json")
        submitted_pricing = data.pop("pricing_summary_json", None)
        if submitted_pricing:
            data["source_payload_json"] = {
                **(data.get("source_payload_json") or {}),
                "submitted_pricing_summary": submitted_pricing,
                "authoritative_pricing": False,
            }
        requested_order = data.pop("option_order", None)
        existing_options = await self.db.collection("offer_options").find_many(
            {"agency_id": agency_id, "workspace_id": workspace_id}
        )
        existing_orders = {
            int(item.get("option_order") or index)
            for index, item in enumerate(existing_options, start=1)
        }
        option_order = int(requested_order or (max(existing_orders, default=0) + 1))
        if option_order in existing_orders:
            raise CommercialLifecycleError(
                "Option order must be unique within the Offer.",
                code="DUPLICATE_OFFER_OPTION_ORDER",
            )
        option = OfferOption(
            agency_id=agency_id,
            workspace_id=workspace_id,
            offer_workspace_id=workspace_id,
            offer_workspace_version=int(workspace.get("version") or 1),
            option_order=option_order,
            currency=workspace.get("currency") or "EUR",
            request_id=workspace.get("request_id"),
            trip_id=workspace.get("trip_id"),
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
            **data,
        )
        created = await self.db.collection("offer_options").insert_one(option.model_dump(mode="json"))
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": workspace_id}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_option.created",
            "offer_option",
            created["id"],
            f"Created offer option {created['label']}.",
            {"workspace_id": workspace_id},
        )
        return created

    async def update_option(self, agency_id: str, option_id: str, payload: OfferOptionUpdate, actor_user_id: str | None) -> dict[str, Any] | None:
        option = await self.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        workspace = await self.get_workspace_or_none(agency_id, option["workspace_id"])
        if workspace is None:
            raise CommercialLifecycleError(
                "OfferOption has no same-Agency canonical OfferWorkspace.",
                code="OFFER_OPTION_PARENT_MISSING",
            )
        self._assert_workspace_mutable(workspace)
        updates = clean_update_payload(payload)
        expected_version = updates.pop("expected_version", None)
        current_version = int(option.get("version") or 1)
        if expected_version is not None and expected_version != current_version:
            raise CommercialLifecycleError(
                "Offer option changed after it was opened. Refresh before updating.",
                code="STALE_OFFER_OPTION_VERSION",
            )
        submitted_pricing = updates.pop("pricing_summary_json", None)
        if submitted_pricing is not None:
            updates["source_payload_json"] = {
                **(option.get("source_payload_json") or {}),
                **(updates.get("source_payload_json") or {}),
                "submitted_pricing_summary": submitted_pricing,
                "authoritative_pricing": False,
            }
        if not updates:
            return option
        updates["version"] = current_version + 1
        updates["updated_by_user_id"] = actor_user_id
        updated = await self.db.collection("offer_options").update_one({"agency_id": agency_id, "id": option_id}, updates)
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": option["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_option.updated",
            "offer_option",
            option_id,
            "Updated offer option.",
            {"fields": sorted(updates.keys())},
        )
        return updated

    async def clone_option(self, agency_id: str, option_id: str, actor_user_id: str | None) -> dict[str, Any] | None:
        source = await self.get_option_or_none(agency_id, option_id)
        if source is None:
            return None
        workspace = await self.get_workspace_or_none(agency_id, source["workspace_id"])
        if workspace is None:
            return None
        self._assert_workspace_mutable(workspace)
        clone_payload = {
            key: value
            for key, value in source.items()
            if key
            not in {
                "id",
                "created_at",
                "updated_at",
                "agency_id",
            }
        }
        clone_payload["label"] = f"Copy of {source.get('label') or 'option'}"
        clone_payload["status"] = OfferOptionStatus.DRAFT.value
        clone_payload["recommendation_rank"] = None
        clone_payload["recommendation_tag"] = None
        option_orders = [
            int(item.get("option_order") or 0)
            for item in await self.db.collection("offer_options").find_many(
                {"agency_id": agency_id, "workspace_id": source["workspace_id"]}
            )
        ]
        clone_payload["option_order"] = max(option_orders, default=0) + 1
        clone_payload["version"] = 1
        clone_payload["created_by_user_id"] = actor_user_id
        clone_payload["updated_by_user_id"] = actor_user_id
        clone = OfferOption(agency_id=agency_id, **clone_payload)
        created = await self.db.collection("offer_options").insert_one(clone.model_dump(mode="json"))

        async def clone_collection(collection_name: str, model_cls: Any, immutable_keys: set[str], overrides: dict[str, Any]) -> None:
            items = await self.db.collection(collection_name).find_many({"agency_id": agency_id, "option_id": option_id})
            for item in items:
                payload = {key: value for key, value in item.items() if key not in immutable_keys}
                payload.update(overrides)
                cloned_item = model_cls(**payload)
                await self.db.collection(collection_name).insert_one(cloned_item.model_dump(mode="json"))

        immutable = {"id", "created_at", "updated_at", "agency_id", "option_id"}
        await clone_collection(
            "offer_routing_options",
            OfferRoutingOption,
            immutable,
            {"agency_id": agency_id, "option_id": created["id"]},
        )
        await clone_collection(
            "offer_builder_segments",
            OfferBuilderSegment,
            immutable,
            {"agency_id": agency_id, "option_id": created["id"]},
        )
        await clone_collection(
            "offer_fare_bundles",
            OfferFareBundle,
            immutable,
            {"agency_id": agency_id, "option_id": created["id"]},
        )
        await clone_collection(
            "offer_pricing_lines",
            OfferPricingLine,
            immutable,
            {"agency_id": agency_id, "option_id": created["id"]},
        )
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": source["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_option.cloned",
            "offer_option",
            created["id"],
            "Cloned offer option.",
            {"source_option_id": option_id},
        )
        return created

    async def add_routing_option(self, agency_id: str, option_id: str, payload: OfferRoutingOptionCreate, actor_user_id: str | None) -> dict[str, Any] | None:
        option = await self.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        self._assert_workspace_mutable(
            await self.get_workspace_or_none(agency_id, option["workspace_id"]) or {}
        )
        routing = OfferRoutingOption(agency_id=agency_id, option_id=option_id, **payload.model_dump(mode="json"))
        created = await self.db.collection("offer_routing_options").insert_one(routing.model_dump(mode="json"))
        await self._touch_option_version(agency_id, option)
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": option["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        return created

    async def add_segment(self, agency_id: str, option_id: str, payload: OfferBuilderSegmentCreate, actor_user_id: str | None) -> dict[str, Any] | None:
        option = await self.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        self._assert_workspace_mutable(
            await self.get_workspace_or_none(agency_id, option["workspace_id"]) or {}
        )
        segment = OfferBuilderSegment(agency_id=agency_id, option_id=option_id, **payload.model_dump(mode="json"))
        created = await self.db.collection("offer_builder_segments").insert_one(segment.model_dump(mode="json"))
        await self._touch_option_version(agency_id, option)
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": option["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_segment.created",
            "offer_builder_segment",
            created["id"],
            "Added offer route segment.",
            {"option_id": option_id},
        )
        return created

    async def add_fare_bundle(self, agency_id: str, option_id: str, payload: OfferFareBundleCreate, actor_user_id: str | None) -> dict[str, Any] | None:
        option = await self.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        self._assert_workspace_mutable(
            await self.get_workspace_or_none(agency_id, option["workspace_id"]) or {}
        )
        bundle = OfferFareBundle(agency_id=agency_id, option_id=option_id, **payload.model_dump(mode="json"))
        created = await self.db.collection("offer_fare_bundles").insert_one(bundle.model_dump(mode="json"))
        await self._touch_option_version(agency_id, option)
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": option["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_fare_bundle.created",
            "offer_fare_bundle",
            created["id"],
            "Added fare bundle.",
            {"option_id": option_id},
        )
        return created

    async def add_pricing_line(self, agency_id: str, option_id: str, payload: OfferPricingLineCreate, actor_user_id: str | None) -> dict[str, Any] | None:
        option = await self.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        self._assert_workspace_mutable(
            await self.get_workspace_or_none(agency_id, option["workspace_id"]) or {}
        )
        line = OfferPricingLine(agency_id=agency_id, option_id=option_id, **payload.model_dump(mode="json"))
        created = await self.db.collection("offer_pricing_lines").insert_one(line.model_dump(mode="json"))
        await self._touch_option_version(agency_id, option)
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": option["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_pricing_line.created",
            "offer_pricing_line",
            created["id"],
            "Added pricing line.",
            {"option_id": option_id, "line_type": created.get("line_type")},
        )
        return created

    async def recalculate_option_pricing(self, agency_id: str, option_id: str, actor_user_id: str | None) -> dict[str, Any] | None:
        option = await self.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        workspace = await self.get_workspace_or_none(agency_id, option["workspace_id"])
        self._assert_workspace_mutable(workspace or {})
        lines = await self.db.collection("offer_pricing_lines").find_many({"agency_id": agency_id, "option_id": option_id})
        totals: dict[str, float] = {line_type.value: 0.0 for line_type in OfferBuilderPricingLineType}
        currency = option.get("currency") or (lines[0].get("currency") if lines else "EUR")
        for line in lines:
            line_type = line.get("line_type") or OfferBuilderPricingLineType.OTHER.value
            amount = float(line.get("amount") or 0)
            if line_type == OfferBuilderPricingLineType.DISCOUNT.value and amount > 0:
                amount = -amount
            totals[line_type] = totals.get(line_type, 0.0) + amount
            currency = line.get("currency") or currency
        subtotal_before_discounts = sum(
            amount
            for key, amount in totals.items()
            if key not in {OfferBuilderPricingLineType.DISCOUNT.value, OfferBuilderPricingLineType.COMMISSION.value}
        )
        total = sum(totals.values())
        pricing_summary = {
            "currency": currency or "EUR",
            "line_count": len(lines),
            "totals_by_type": {key: round(value, 2) for key, value in totals.items() if value},
            "subtotal_before_discounts": round(subtotal_before_discounts, 2),
            "total_amount": round(total, 2),
            "commission_amount": round(totals.get(OfferBuilderPricingLineType.COMMISSION.value, 0.0), 2),
            "discount_amount": round(totals.get(OfferBuilderPricingLineType.DISCOUNT.value, 0.0), 2),
            "recalculated_at": datetime.utcnow().isoformat(),
        }
        updated = await self.db.collection("offer_options").update_one(
            {"agency_id": agency_id, "id": option_id},
            {
                "pricing_summary_json": pricing_summary,
                "airline_charge_snapshot_json": {
                    key: round(value, 2)
                    for key, value in totals.items()
                    if key in {"base_fare", "surcharge", "ancillary"} and value
                },
                "agency_fee_snapshot_json": {
                    "service_fee": round(
                        totals.get(OfferBuilderPricingLineType.SERVICE_FEE.value, 0.0),
                        2,
                    )
                },
                "tax_snapshot_json": {
                    "tax": round(
                        totals.get(OfferBuilderPricingLineType.TAX.value, 0.0), 2
                    )
                },
                "total_snapshot_json": {
                    "total_amount": round(total, 2),
                    "currency": currency or "EUR",
                    "server_derived": True,
                },
                "currency": currency or "EUR",
                "version": int(option.get("version") or 1) + 1,
                "updated_by_user_id": actor_user_id,
            },
        )
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": option["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_option.pricing_recalculated",
            "offer_option",
            option_id,
            "Recalculated offer option pricing.",
            pricing_summary,
        )
        return {"option": updated, "pricing_summary": pricing_summary, "pricing_lines": lines}

    def _assert_workspace_mutable(self, workspace: dict[str, Any]) -> None:
        if not workspace or str(workspace.get("status") or "") in FROZEN_OFFER_STATUSES:
            raise CommercialLifecycleError(
                "Delivered, accepted, expired, superseded, or cancelled Offer evidence cannot be edited. Create a governed revision.",
                code="OFFER_EVIDENCE_FROZEN",
            )

    def assert_workspace_mutable(self, workspace: dict[str, Any]) -> None:
        self._assert_workspace_mutable(workspace)

    async def _create_workspace_revision(
        self,
        agency_id: str,
        workspace: dict[str, Any],
        updates: dict[str, Any],
        actor_user_id: str | None,
        revision_reason: str,
    ) -> dict[str, Any]:
        current_version = int(workspace.get("version") or 1)
        new_id_value = new_id()
        timestamp = datetime.now(timezone.utc)
        revision = {
            **workspace,
            **updates,
            "id": new_id_value,
            "status": OfferWorkspaceStatus.DRAFT.value,
            "version": current_version + 1,
            "revision_root_id": workspace.get("revision_root_id") or workspace["id"],
            "previous_version_id": workspace["id"],
            "created_at": timestamp,
            "updated_at": timestamp,
            "created_by_user_id": actor_user_id,
            "updated_by_user_id": actor_user_id,
            "delivered_at": None,
            "superseded_at": None,
            "superseded_by_offer_id": None,
            "reconciliation_status": "canonical_revision",
            "compatibility_metadata": {
                **(workspace.get("compatibility_metadata") or {}),
                "revision_reason": revision_reason,
            },
        }
        created = await self.db.collection("offer_workspaces").insert_one(revision)
        option_id_map: dict[str, str] = {}
        options = await self.db.collection("offer_options").find_many(
            {"agency_id": agency_id, "workspace_id": workspace["id"]}
        )
        for option in options:
            cloned_option_id = new_id()
            option_id_map[option["id"]] = cloned_option_id
            await self.db.collection("offer_options").insert_one(
                {
                    **option,
                    "id": cloned_option_id,
                    "workspace_id": created["id"],
                    "offer_workspace_id": created["id"],
                    "offer_workspace_version": created["version"],
                    "version": 1,
                    "status": OfferOptionStatus.DRAFT.value,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "created_by_user_id": actor_user_id,
                    "updated_by_user_id": actor_user_id,
                }
            )
        for collection_name in (
            "offer_routing_options",
            "offer_builder_segments",
            "offer_fare_bundles",
            "offer_pricing_lines",
        ):
            for source_option_id, cloned_option_id in option_id_map.items():
                children = await self.db.collection(collection_name).find_many(
                    {"agency_id": agency_id, "option_id": source_option_id}
                )
                for child in children:
                    await self.db.collection(collection_name).insert_one(
                        {
                            **child,
                            "id": new_id(),
                            "option_id": cloned_option_id,
                            "created_at": timestamp,
                            "updated_at": timestamp,
                        }
                    )
        superseded = await self.db.collection("offer_workspaces").update_one(
            {"agency_id": agency_id, "id": workspace["id"]},
            {
                "status": OfferWorkspaceStatus.SUPERSEDED.value,
                "superseded_at": timestamp,
                "superseded_by_offer_id": created["id"],
                "updated_by_user_id": actor_user_id,
            },
        )
        if superseded is None:
            await self.db.collection("offer_workspaces").update_one(
                {"agency_id": agency_id, "id": created["id"]},
                {"reconciliation_status": "supersession_requires_review"},
            )
            raise CommercialLifecycleError(
                "Offer revision was staged but supersession needs reconciliation.",
                code="OFFER_REVISION_RECONCILIATION_REQUIRED",
            )
        await write_lifecycle_evidence(
            self.db,
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="offer.lifecycle.revised",
            entity_type="offer_workspace",
            entity_id=created["id"],
            summary="Created a governed Offer revision and preserved the superseded version.",
            previous_status=workspace.get("status"),
            next_status="draft",
            request_id=created.get("request_id"),
            trip_id=created.get("trip_id"),
            metadata={
                "previous_version_id": workspace["id"],
                "revision_root_id": created["revision_root_id"],
                "revision_reason": revision_reason,
            },
        )
        return created

    async def _touch_option_version(
        self,
        agency_id: str,
        option: dict[str, Any],
    ) -> dict[str, Any] | None:
        return await self.db.collection("offer_options").update_one(
            {"agency_id": agency_id, "id": option["id"]},
            {"version": int(option.get("version") or 1) + 1},
        )

    async def touch_option_version(
        self,
        agency_id: str,
        option: dict[str, Any],
    ) -> dict[str, Any] | None:
        return await self._touch_option_version(agency_id, option)

    async def _workspace_services(self, agency_id: str, workspace: dict[str, Any]) -> list[dict[str, Any]]:
        if workspace.get("trip_id"):
            services = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "trip_id": workspace["trip_id"]})
            if services:
                return services
            trip_items = await self.db.collection("trip_service_items").find_many({"agency_id": agency_id, "trip_id": workspace["trip_id"]})
            mapped = []
            for item in trip_items:
                snapshot = item.get("service_catalogue_snapshot_json") or service_catalogue_snapshot(
                    await find_service_catalogue_record(self.db, item.get("service_key") or item.get("service_code"))
                )
                mapped.append(
                    {
                        "id": item.get("id"),
                        "service_key": item.get("service_key") or snapshot.get("service_key"),
                        "service_label": item.get("service_label") or snapshot.get("label"),
                        "service_catalogue_category": item.get("service_catalogue_category") or snapshot.get("category"),
                        "service_catalogue_snapshot_json": snapshot,
                        "service_type": snapshot.get("service_key") or item.get("service_code"),
                        "category": category_for_service_type(snapshot.get("service_key") or item.get("service_code"), snapshot.get("rules_category") or item.get("service_family_code") or "OTHER"),
                        "metadata_json": {
                            "notes": item.get("notes"),
                            "passenger_ids": item.get("passenger_ids") or [],
                            "segment_ids": item.get("segment_ids") or [],
                            "service_catalogue_snapshot_json": snapshot,
                            "source": "trip_service_item",
                        },
                    }
                )
            return mapped
        if workspace.get("request_id"):
            services = await self.db.collection("passenger_service_requests").find_many({"agency_id": agency_id, "request_id": workspace["request_id"]})
            if services:
                return services
            requested = await self.db.collection("requested_services").find_many({"agency_id": agency_id, "request_id": workspace["request_id"], "status": "active"})
            mapped = []
            for item in requested:
                snapshot = item.get("service_catalogue_snapshot_json") or service_catalogue_snapshot(
                    await find_service_catalogue_record(self.db, item.get("service_key") or item.get("service_code"))
                )
                mapped.append(
                    {
                        "id": item.get("id"),
                        "service_key": item.get("service_key") or snapshot.get("service_key"),
                        "service_label": item.get("service_name") or snapshot.get("label"),
                        "service_catalogue_category": item.get("service_catalogue_category") or snapshot.get("category"),
                        "service_catalogue_snapshot_json": snapshot,
                        "service_type": snapshot.get("service_key") or item.get("service_code") or item.get("service_family_code"),
                        "category": category_for_service_type(snapshot.get("service_key") or item.get("service_code"), snapshot.get("rules_category") or item.get("service_family_code") or "OTHER"),
                        "metadata_json": {
                            "service_label": item.get("service_name") or snapshot.get("label"),
                            "notes": item.get("notes"),
                            "service_catalogue_snapshot_json": snapshot,
                            "source": "requested_service",
                        },
                    }
                )
            return mapped
        return []

    def _segment_rule_context(self, option: dict[str, Any], segment: dict[str, Any], service: dict[str, Any]) -> dict[str, Any]:
        metadata = service.get("metadata_json") or {}
        catalogue_snapshot = service.get("service_catalogue_snapshot_json") or metadata.get("service_catalogue_snapshot_json") or {}
        service_type = _service_type(service)
        return {
            "airline_id": option.get("main_airline_id"),
            "iata_code": normalize_code(segment.get("marketing_airline_code") or option.get("main_airline_code") or segment.get("operating_airline_code")),
            "route_origin": normalize_code(segment.get("origin_airport")),
            "route_destination": normalize_code(segment.get("destination_airport")),
            "aircraft_type": normalize_code(segment.get("aircraft_type")),
            "passenger_summary_json": metadata.get("passenger_summary_json") or {},
            "service_category": service.get("service_catalogue_category") or service.get("category") or category_for_service_type(service_type),
            "service_key": service.get("service_key") or catalogue_snapshot.get("service_key"),
            "service_label": service.get("service_label") or catalogue_snapshot.get("label"),
            "service_catalogue_category": service.get("service_catalogue_category") or catalogue_snapshot.get("category"),
            "service_type": service_type,
            "service_payload_json": metadata,
            "service_catalogue_snapshot_json": catalogue_snapshot,
            "segment_refs_json": [{"offer_segment_id": segment.get("id"), "sequence": segment.get("sequence")}],
        }

    async def evaluate_option_rules(self, agency_id: str, option_id: str, actor_user_id: str | None) -> dict[str, Any] | None:
        option = await self.get_option_or_none(agency_id, option_id)
        if option is None:
            return None
        workspace = await self.get_workspace_or_none(agency_id, option["workspace_id"])
        if workspace is None:
            return None
        self._assert_workspace_mutable(workspace)
        segments = _sort_segments(await self.db.collection("offer_builder_segments").find_many({"agency_id": agency_id, "option_id": option_id}))
        services = await self._workspace_services(agency_id, workspace)
        evaluations: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        if not segments:
            warnings.append({"severity": "manual_review", "message": "No offer segments are available; rule evaluation requires manual verification."})
        if not services:
            warnings.append({"severity": "info", "message": "No special services are linked to this workspace."})

        for segment in segments:
            scoped_services = services or [
                {
                    "id": "general",
                    "service_type": "GENERAL",
                    "category": "GENERAL",
                    "metadata_json": {"source": "automatic_general_review"},
                }
            ]
            for service in scoped_services:
                context = self._segment_rule_context(option, segment, service)
                result = await self.exception_engine.evaluate(context)
                generated = await self.ssr_osi_generator.generate(context, result)
                row = {
                    "segment_id": segment.get("id"),
                    "segment_sequence": segment.get("sequence"),
                    "service_id": service.get("id"),
                    "service_key": service.get("service_key"),
                    "service_label": service.get("service_label"),
                    "service_catalogue_category": service.get("service_catalogue_category"),
                    "service_type": _service_type(service),
                    "allowed": result.get("allowed", True),
                    "confidence": result.get("confidence"),
                    "fallback_used": result.get("fallback_used"),
                    "rules_fired": result.get("rules_fired") or [],
                    "required_documents": generated.get("required_documents") or result.get("required_documents") or [],
                    "policy_violations": result.get("policy_violations") or [],
                    "generated_ssr": generated.get("ssr") or [],
                    "generated_osi": generated.get("osi") or [],
                    "warnings": list(dict.fromkeys([*(result.get("warnings") or []), *(generated.get("warnings") or [])])),
                    "context": context,
                }
                evaluations.append(row)
                for warning in row["warnings"]:
                    warnings.append(
                        {
                            "severity": "blocked" if not row["allowed"] else "manual_review" if row.get("fallback_used") else "info",
                            "message": warning,
                            "segment_id": segment.get("id"),
                            "service_type": row["service_type"],
                        }
                    )
        blocked_count = len([item for item in evaluations if not item.get("allowed")])
        manual_review_count = len([item for item in evaluations if item.get("fallback_used")])
        rules_summary = {
            "evaluated_at": datetime.utcnow().isoformat(),
            "segment_count": len(segments),
            "service_count": len(services),
            "evaluation_count": len(evaluations),
            "blocked_count": blocked_count,
            "manual_review_count": manual_review_count,
            "rules_fired_count": sum(len(item.get("rules_fired") or []) for item in evaluations),
            "status": "blocked" if blocked_count else "manual_review" if manual_review_count or warnings else "clear",
            "evaluations": evaluations,
        }
        service_feasibility = {
            "overall_status": rules_summary["status"],
            "services": [
                {
                    "service_id": service.get("id"),
                    "service_key": service.get("service_key"),
                    "service_label": service.get("service_label"),
                    "service_type": _service_type(service),
                    "category": service.get("category"),
                    "evaluation_count": len([item for item in evaluations if item.get("service_id") == service.get("id")]),
                    "blocked": any(item for item in evaluations if item.get("service_id") == service.get("id") and not item.get("allowed")),
                }
                for service in services
            ],
            "manual_verification_required": bool(manual_review_count or not segments),
        }
        unique_warnings: list[dict[str, Any]] = []
        seen: set[tuple[Any, Any, Any]] = set()
        for warning in warnings:
            key = (warning.get("severity"), warning.get("message"), warning.get("service_type"))
            if key not in seen:
                seen.add(key)
                unique_warnings.append(warning)
        updates = {
            "rules_summary_json": rules_summary,
            "service_feasibility_json": service_feasibility,
            "warnings_json": unique_warnings,
            "version": int(option.get("version") or 1) + 1,
            "updated_by_user_id": actor_user_id,
        }
        updated = await self.db.collection("offer_options").update_one({"agency_id": agency_id, "id": option_id}, updates)
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": option["workspace_id"]}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_option.rules_evaluated",
            "offer_option",
            option_id,
            "Evaluated offer option rules and service feasibility.",
            {"blocked_count": blocked_count, "manual_review_count": manual_review_count},
        )
        return {"option": updated, "rules_summary": rules_summary, "service_feasibility": service_feasibility, "warnings": unique_warnings}

    async def option_summary(self, agency_id: str, option: dict[str, Any]) -> dict[str, Any]:
        segments = _sort_segments(await self.db.collection("offer_builder_segments").find_many({"agency_id": agency_id, "option_id": option["id"]}))
        pricing_lines = await self.db.collection("offer_pricing_lines").find_many({"agency_id": agency_id, "option_id": option["id"]})
        bundles = await self.db.collection("offer_fare_bundles").find_many({"agency_id": agency_id, "option_id": option["id"]})
        route = " - ".join(
            [segments[0].get("origin_airport"), *[segment.get("destination_airport") for segment in segments]]
        ) if segments else None
        return {
            "option": option,
            "route": route,
            "first_departure_at": segments[0].get("departure_at") if segments else None,
            "segment_count": len(segments),
            "fare_bundle_count": len(bundles),
            "pricing_line_count": len(pricing_lines),
            "total_amount": (option.get("pricing_summary_json") or {}).get("total_amount"),
            "currency": (option.get("pricing_summary_json") or {}).get("currency") or "EUR",
            "warning_count": len(option.get("warnings_json") or []),
            "rules_status": (option.get("rules_summary_json") or {}).get("status"),
            "service_status": (option.get("service_feasibility_json") or {}).get("overall_status"),
        }
