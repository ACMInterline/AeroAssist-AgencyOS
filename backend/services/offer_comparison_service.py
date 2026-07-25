from __future__ import annotations

from datetime import datetime
from typing import Any

from database import Database
from models import OfferComparisonSnapshot, OfferOptionStatus
from services.offer_builder_service import OfferBuilderService, write_offer_builder_audit


def _money_label(amount: Any, currency: str | None) -> str:
    if amount in (None, ""):
        return "Not priced"
    return f"{float(amount):,.2f} {currency or 'EUR'}"


def _route_from_segments(segments: list[dict[str, Any]]) -> str | None:
    if not segments:
        return None
    points = [segments[0].get("origin_airport"), *[segment.get("destination_airport") for segment in segments if segment.get("destination_airport")]]
    return " - ".join(str(point) for point in points if point)


def _duration_label(minutes: Any) -> str | None:
    if minutes in (None, ""):
        return None
    minutes = int(minutes)
    hours = minutes // 60
    remainder = minutes % 60
    if hours and remainder:
        return f"{hours}h {remainder}m"
    if hours:
        return f"{hours}h"
    return f"{remainder}m"


class OfferComparisonService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.builder = OfferBuilderService(db)

    async def build_matrix(self, agency_id: str, workspace_id: str) -> dict[str, Any] | None:
        detail = await self.builder.workspace_detail(agency_id, workspace_id)
        if detail is None:
            return None
        options = detail["options"]
        option_ids = [option["id"] for option in options]
        segments_by_option = {
            option_id: [segment for segment in detail["segments"] if segment.get("option_id") == option_id]
            for option_id in option_ids
        }
        routings_by_option = {
            option_id: [routing for routing in detail["routing_options"] if routing.get("option_id") == option_id]
            for option_id in option_ids
        }
        bundles_by_option = {
            option_id: [bundle for bundle in detail["fare_bundles"] if bundle.get("option_id") == option_id]
            for option_id in option_ids
        }
        prices_by_option = {
            option_id: [line for line in detail["pricing_lines"] if line.get("option_id") == option_id]
            for option_id in option_ids
        }
        columns = [
            {
                "option_id": option["id"],
                "label": option.get("label"),
                "status": option.get("status"),
                "recommendation_rank": option.get("recommendation_rank"),
                "recommendation_tag": option.get("recommendation_tag"),
            }
            for option in options
        ]

        option_map = {option["id"]: option for option in options}

        def row(key: str, label: str, values: dict[str, Any], group: str = "summary", severity: str | None = None) -> dict[str, Any]:
            return {"key": key, "label": label, "group": group, "severity": severity, "values": values}

        route_values = {option_id: _route_from_segments(segments_by_option[option_id]) for option_id in option_ids}
        carrier_values = {
            option_id: (
                (routings_by_option[option_id][0].get("validating_carrier_code") if routings_by_option[option_id] else None)
                or option_map[option_id].get("main_airline_code")
                or (segments_by_option[option_id][0].get("marketing_airline_code") if segments_by_option[option_id] else None)
            )
            for option_id in option_ids
        }
        duration_values = {
            option_id: _duration_label(routings_by_option[option_id][0].get("total_duration_minutes")) if routings_by_option[option_id] else None
            for option_id in option_ids
        }
        cabin_values = {
            option_id: ", ".join(sorted({str(segment.get("cabin_class")) for segment in segments_by_option[option_id] if segment.get("cabin_class")}))
            or (bundles_by_option[option_id][0].get("cabin_class") if bundles_by_option[option_id] else None)
            for option_id in option_ids
        }
        fare_values = {
            option_id: ", ".join(bundle.get("fare_family_name") for bundle in bundles_by_option[option_id] if bundle.get("fare_family_name")) or None
            for option_id in option_ids
        }
        booking_values = {
            option_id: ", ".join(
                sorted(
                    {
                        str(value)
                        for value in [
                            *[segment.get("booking_class") for segment in segments_by_option[option_id]],
                            *[bundle.get("booking_class") for bundle in bundles_by_option[option_id]],
                        ]
                        if value
                    }
                )
            )
            or None
            for option_id in option_ids
        }
        pricing_values = {
            option_id: _money_label(
                (option_map[option_id].get("pricing_summary_json") or {}).get("total_amount"),
                (option_map[option_id].get("pricing_summary_json") or {}).get("currency"),
            )
            for option_id in option_ids
        }
        pricing_line_values = {option_id: len(prices_by_option[option_id]) for option_id in option_ids}
        rules_values = {
            option_id: (option_map[option_id].get("rules_summary_json") or {}).get("status") or "Not evaluated"
            for option_id in option_ids
        }
        service_values = {
            option_id: (option_map[option_id].get("service_feasibility_json") or {}).get("overall_status") or "Not evaluated"
            for option_id in option_ids
        }
        warning_values = {
            option_id: len(option_map[option_id].get("warnings_json") or [])
            for option_id in option_ids
        }
        rows = [
            row("route", "Route", route_values, "routing"),
            row("segments", "Segments", {option_id: len(segments_by_option[option_id]) for option_id in option_ids}, "routing"),
            row(
                "stops",
                "Stops",
                {
                    option_id: (
                        routings_by_option[option_id][0].get("stops_count")
                        if routings_by_option[option_id]
                        else max(len(segments_by_option[option_id]) - 1, 0)
                    )
                    for option_id in option_ids
                },
                "routing",
            ),
            row("duration", "Duration", duration_values, "routing"),
            row("validating_carrier", "Validating carrier", carrier_values, "routing"),
            row("cabin", "Cabin", cabin_values, "fare"),
            row("booking_class", "Booking class", booking_values, "fare"),
            row("fare_family", "Fare family", fare_values, "fare"),
            row("total", "Total", pricing_values, "pricing"),
            row("pricing_lines", "Pricing lines", pricing_line_values, "pricing"),
            row("rule_status", "Rule status", rules_values, "rules", "manual_review" if any(value != "clear" for value in rules_values.values()) else None),
            row("service_feasibility", "Service feasibility", service_values, "rules", "manual_review" if any(value != "clear" for value in service_values.values()) else None),
            row("warnings", "Warnings", warning_values, "rules", "manual_review" if any(value for value in warning_values.values()) else None),
        ]
        warnings_summary = [
            {
                "option_id": option["id"],
                "label": option.get("label"),
                "warnings": option.get("warnings_json") or [],
            }
            for option in options
            if option.get("warnings_json")
        ]
        recommended = next((option for option in options if option.get("status") == OfferOptionStatus.RECOMMENDED.value), None)
        if recommended is None and options:
            priced_options = [
                option
                for option in options
                if (option.get("pricing_summary_json") or {}).get("total_amount") not in (None, "")
            ]
            recommended = min(
                priced_options,
                key=lambda item: float((item.get("pricing_summary_json") or {}).get("total_amount") or 0),
                default=options[0],
            )
        return {
            "workspace": detail["workspace"],
            "columns": columns,
            "rows": rows,
            "warnings_summary": warnings_summary,
            "option_count": len(options),
            "recommended_option_id": recommended.get("id") if recommended else None,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def save_snapshot(self, agency_id: str, workspace_id: str, actor_user_id: str | None) -> dict[str, Any] | None:
        matrix = await self.build_matrix(agency_id, workspace_id)
        if matrix is None:
            return None
        snapshot = OfferComparisonSnapshot(
            agency_id=agency_id,
            workspace_id=workspace_id,
            matrix_json=matrix,
            generated_by_user_id=actor_user_id,
        )
        created = await self.db.collection("offer_comparison_snapshots").insert_one(snapshot.model_dump(mode="json"))
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_comparison_snapshot.created",
            "offer_workspace",
            workspace_id,
            "Saved offer comparison snapshot.",
            {"snapshot_id": created["id"]},
        )
        return created

    async def recommend_option(self, agency_id: str, workspace_id: str, option_id: str, tag: str | None, rank: int | None, actor_user_id: str | None) -> dict[str, Any] | None:
        workspace = await self.builder.get_workspace_or_none(agency_id, workspace_id)
        option = await self.builder.get_option_or_none(agency_id, option_id)
        if workspace is None or option is None or option.get("workspace_id") != workspace_id:
            return None
        self.builder.assert_workspace_mutable(workspace)
        options = await self.db.collection("offer_options").find_many({"agency_id": agency_id, "workspace_id": workspace_id})
        for other in options:
            if other["id"] == option_id:
                continue
            if other.get("status") == OfferOptionStatus.RECOMMENDED.value:
                await self.db.collection("offer_options").update_one(
                    {"agency_id": agency_id, "id": other["id"]},
                    {
                        "status": OfferOptionStatus.ALTERNATE.value,
                        "version": int(other.get("version") or 1) + 1,
                        "updated_by_user_id": actor_user_id,
                    },
                )
        updated = await self.db.collection("offer_options").update_one(
            {"agency_id": agency_id, "id": option_id},
            {
                "status": OfferOptionStatus.RECOMMENDED.value,
                "recommendation_tag": tag or "Recommended",
                "recommendation_rank": rank if rank is not None else 1,
                "version": int(option.get("version") or 1) + 1,
                "updated_by_user_id": actor_user_id,
            },
        )
        await self.db.collection("offer_workspaces").update_one({"agency_id": agency_id, "id": workspace_id}, {"updated_by_user_id": actor_user_id})
        await write_offer_builder_audit(
            self.db,
            agency_id,
            actor_user_id,
            "offer_option.recommended",
            "offer_option",
            option_id,
            "Marked offer option as recommended.",
            {"workspace_id": workspace_id, "tag": tag, "rank": rank},
        )
        return {"workspace": workspace, "option": updated, "matrix": await self.build_matrix(agency_id, workspace_id)}
