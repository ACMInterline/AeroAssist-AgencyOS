from __future__ import annotations

from typing import Any

from database import Database


def _warning(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _compact(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if value is not None and value != ""}


def _display_name(item: dict[str, Any] | None) -> str | None:
    if not item:
        return None
    return (
        item.get("display_name")
        or item.get("snapshot_display_name")
        or item.get("name")
        or " ".join([str(item.get("first_name") or "").strip(), str(item.get("last_name") or "").strip()]).strip()
        or None
    )


def _pricing_summary(value: Any) -> dict[str, Any]:
    data = _as_dict(value)
    summary = _as_dict(data.get("summary")) or data
    return _compact(
        {
            "currency": summary.get("currency"),
            "base_fare_amount": summary.get("base_fare_amount") or summary.get("base_fare"),
            "taxes_amount": summary.get("taxes_amount") or summary.get("taxes"),
            "fees_amount": summary.get("fees_amount") or summary.get("fees"),
            "total_amount": summary.get("total_amount") or summary.get("total"),
            "fare_basis": summary.get("fare_basis"),
            "pricing_notes": summary.get("pricing_notes"),
        }
    )


def _segment_row(item: dict[str, Any]) -> dict[str, Any]:
    return _compact(
        {
            "id": item.get("id") or item.get("segment_id"),
            "sequence": item.get("sequence") or item.get("segment_order") or item.get("segment_number"),
            "airline": item.get("marketing_airline_code") or item.get("marketing_airline") or item.get("airline"),
            "operating_airline": item.get("operating_airline_code") or item.get("operating_airline"),
            "flight_number": item.get("flight_number"),
            "origin": item.get("origin_airport_code") or item.get("origin_airport") or item.get("origin"),
            "destination": item.get("destination_airport_code") or item.get("destination_airport") or item.get("destination"),
            "departure": item.get("departure_datetime") or item.get("departure_at") or item.get("departure_date"),
            "arrival": item.get("arrival_datetime") or item.get("arrival_at") or item.get("arrival_date"),
            "cabin": item.get("cabin") or item.get("cabin_class"),
            "booking_class": item.get("booking_class") or item.get("rbd"),
            "status": item.get("segment_status") or item.get("status_code") or item.get("status"),
            "notes": item.get("notes"),
        }
    )


def _passenger_row(item: dict[str, Any]) -> dict[str, Any]:
    return _compact(
        {
            "id": item.get("id") or item.get("passenger_id"),
            "passenger_id": item.get("passenger_id") or item.get("id"),
            "display_name": _display_name(item),
            "passenger_type": item.get("passenger_type") or item.get("snapshot_passenger_type"),
            "date_of_birth": item.get("date_of_birth") or item.get("snapshot_date_of_birth"),
            "nationality": item.get("nationality"),
            "notes": item.get("notes") or item.get("assistance_summary"),
        }
    )


def _service_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict):
        rows = []
        for key in ["items", "trip_service_items", "passenger_service_requests", "requested_services", "services"]:
            rows.extend(_as_list(value.get(key)))
    else:
        rows = []
    return [
        _compact(
            {
                "id": item.get("id"),
                "service_key": item.get("service_key") or item.get("service_code"),
                "service_label": item.get("service_label") or item.get("service_name") or item.get("label"),
                "service_category": item.get("service_category") or item.get("category"),
                "passenger_reference": item.get("passenger_reference") or ", ".join(_as_list(item.get("passenger_ids"))),
                "segment_reference": item.get("segment_reference") or ", ".join(_as_list(item.get("segment_ids"))),
                "status": item.get("status"),
                "notes": item.get("notes"),
            }
        )
        for item in rows
        if isinstance(item, dict)
    ]


class DocumentContextService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def _base(self, agency_id: str) -> dict[str, Any]:
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        workspace = await self.db.collection("agency_workspaces").find_one({"agency_id": agency_id})
        return {
            "agency_snapshot": _compact(
                {
                    "id": agency_id,
                    "name": (agency or {}).get("name"),
                    "legal_name": (agency or {}).get("legal_name"),
                    "default_currency": (agency or {}).get("default_currency"),
                    "brand_name": (workspace or {}).get("brand_name"),
                    "logo_url": (workspace or {}).get("logo_url"),
                    "primary_color": (workspace or {}).get("primary_color"),
                    "secondary_color": (workspace or {}).get("secondary_color"),
                }
            ),
            "client_snapshot": {},
            "passenger_snapshots": [],
            "trip_summary": {},
            "itinerary_segments": [],
            "booking_summary": {},
            "pricing_summary": {},
            "ticket_summary": {},
            "ticket_coupons": [],
            "emd_summary": {},
            "emd_coupons": [],
            "service_rows": [],
            "ssr_rows": [],
            "osi_rows": [],
            "pets_rows": [],
            "special_items_rows": [],
            "change_exchange_summary": {},
            "parser_run_summary": {},
            "parsed_entities": [],
            "parse_corrections": [],
            "training_samples": [],
            "warnings_json": [],
            "source_links": [],
        }

    async def _client_snapshot(self, agency_id: str, client_id: str | None) -> dict[str, Any]:
        if not client_id:
            return {}
        client = await self.db.collection("client_profiles").find_one({"agency_id": agency_id, "id": client_id})
        if not client:
            return {"id": client_id}
        return _compact({"id": client["id"], "display_name": client.get("display_name"), "email": client.get("email"), "phone": client.get("phone")})

    async def _trip_summary(self, agency_id: str, trip_id: str | None) -> dict[str, Any]:
        if not trip_id:
            return {}
        trip = await self.db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": trip_id})
        if not trip:
            return {"id": trip_id}
        return _compact(
            {
                "id": trip["id"],
                "trip_reference": trip.get("trip_reference"),
                "trip_title": trip.get("trip_title"),
                "route_summary": trip.get("route_summary"),
                "date_summary": trip.get("date_summary"),
                "status": trip.get("trip_status"),
                "primary_client_id": trip.get("primary_client_id"),
            }
        )

    async def build_request_context(self, agency_id: str, request_id: str) -> dict[str, Any] | None:
        request = await self.db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
        if not request:
            return None
        context = await self._base(agency_id)
        context["source_context_type"] = "request"
        context["source_context_id"] = request_id
        context["client_snapshot"] = await self._client_snapshot(agency_id, request.get("client_id"))
        context["passenger_snapshots"] = [_passenger_row(item) for item in await self.db.collection("request_passengers").find_many({"agency_id": agency_id, "request_id": request_id})]
        context["itinerary_segments"] = [_segment_row(item) for item in await self.db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": request_id})]
        context["service_rows"] = _service_rows(await self.db.collection("requested_services").find_many({"agency_id": agency_id, "request_id": request_id}))
        context["source_record"] = request
        context["source_links"].append({"type": "request", "id": request_id})
        return context

    async def build_offer_context(self, agency_id: str, offer_workspace_id: str, offer_option_id: str | None = None) -> dict[str, Any] | None:
        workspace = await self.db.collection("offer_workspaces").find_one({"agency_id": agency_id, "id": offer_workspace_id})
        if not workspace:
            return None
        if not offer_option_id:
            option = await self.db.collection("offer_options").find_one({"agency_id": agency_id, "workspace_id": offer_workspace_id})
        else:
            option = await self.db.collection("offer_options").find_one({"agency_id": agency_id, "id": offer_option_id})
        context = await self._base(agency_id)
        request = await self.db.collection("travel_requests").find_one({"agency_id": agency_id, "id": workspace.get("request_id")}) if workspace.get("request_id") else None
        context["source_context_type"] = "offer_option" if offer_option_id else "offer_workspace"
        context["source_context_id"] = offer_option_id or offer_workspace_id
        context["client_snapshot"] = await self._client_snapshot(agency_id, (request or {}).get("client_id"))
        context["trip_summary"] = await self._trip_summary(agency_id, workspace.get("trip_id") or workspace.get("existing_trip_id"))
        context["offer_summary"] = _compact(
            {
                "workspace_id": workspace["id"],
                "title": workspace.get("title"),
                "status": workspace.get("status"),
                "currency": workspace.get("currency"),
                "option_id": (option or {}).get("id"),
                "option_label": (option or {}).get("label"),
                "recommendation": (option or {}).get("recommendation_tag"),
            }
        )
        if option:
            context["itinerary_segments"] = [_segment_row(item) for item in await self.db.collection("offer_builder_segments").find_many({"agency_id": agency_id, "option_id": option["id"]})]
            context["pricing_summary"] = _pricing_summary(option.get("pricing_summary_json"))
            context["fare_rows"] = await self.db.collection("offer_fare_bundles").find_many({"agency_id": agency_id, "option_id": option["id"]})
            context["pricing_lines"] = await self.db.collection("offer_pricing_lines").find_many({"agency_id": agency_id, "option_id": option["id"]})
            context["warnings_json"].extend(_as_list(option.get("warnings_json")))
        else:
            context["warnings_json"].append(_warning("offer_option_missing", "No offer option was selected for this offer document."))
        context["source_links"].append({"type": "offer_workspace", "id": offer_workspace_id})
        if option:
            context["source_links"].append({"type": "offer_option", "id": option["id"]})
        return context

    async def build_trip_context(self, agency_id: str, trip_id: str) -> dict[str, Any] | None:
        trip = await self.db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": trip_id})
        if not trip:
            return None
        context = await self._base(agency_id)
        context["source_context_type"] = "trip"
        context["source_context_id"] = trip_id
        context["trip_summary"] = await self._trip_summary(agency_id, trip_id)
        context["client_snapshot"] = await self._client_snapshot(agency_id, trip.get("primary_client_id"))
        context["passenger_snapshots"] = [_passenger_row(item) for item in await self.db.collection("trip_passengers").find_many({"agency_id": agency_id, "trip_id": trip_id})]
        context["itinerary_segments"] = [_segment_row(item) for item in await self.db.collection("trip_segments").find_many({"agency_id": agency_id, "trip_id": trip_id})]
        context["service_rows"] = _service_rows(await self.db.collection("trip_service_items").find_many({"agency_id": agency_id, "trip_id": trip_id}))
        context["booking_workspaces"] = await self.db.collection("booking_workspaces").find_many({"agency_id": agency_id, "trip_id": trip_id})
        context["tickets"] = await self.db.collection("ticket_records").find_many({"agency_id": agency_id, "trip_id": trip_id})
        context["emds"] = await self.db.collection("emd_records").find_many({"agency_id": agency_id, "trip_id": trip_id})
        context["change_operations"] = await self.db.collection("trip_change_operations").find_many({"agency_id": agency_id, "trip_id": trip_id})
        context["source_links"].append({"type": "trip", "id": trip_id})
        return context

    async def build_booking_context(self, agency_id: str, booking_workspace_id: str | None = None, booking_record_id: str | None = None) -> dict[str, Any] | None:
        workspace = await self.db.collection("booking_workspaces").find_one({"agency_id": agency_id, "id": booking_workspace_id}) if booking_workspace_id else None
        record = await self.db.collection("booking_records").find_one({"agency_id": agency_id, "id": booking_record_id}) if booking_record_id else None
        if record and not workspace:
            workspace = await self.db.collection("booking_workspaces").find_one({"agency_id": agency_id, "id": record.get("booking_workspace_id")})
        if workspace and not record and workspace.get("booking_record_id"):
            record = await self.db.collection("booking_records").find_one({"agency_id": agency_id, "id": workspace.get("booking_record_id")})
        if not workspace and not record:
            return None
        source = record or workspace or {}
        context = await self._base(agency_id)
        context["source_context_type"] = "booking_record" if record else "booking_workspace"
        context["source_context_id"] = (record or workspace or {}).get("id")
        context["client_snapshot"] = await self._client_snapshot(agency_id, source.get("client_id") or (workspace or {}).get("client_id"))
        context["trip_summary"] = await self._trip_summary(agency_id, source.get("trip_id") or (workspace or {}).get("trip_id"))
        context["passenger_snapshots"] = [_passenger_row(item) for item in (_as_list((record or {}).get("passengers_json")) or _as_list((workspace or {}).get("passengers_snapshot_json")))]
        context["itinerary_segments"] = [_segment_row(item) for item in (_as_list((record or {}).get("segments_json")) or _as_list((workspace or {}).get("segments_snapshot_json")))]
        context["pricing_summary"] = _pricing_summary((record or {}).get("pricing_json") or (workspace or {}).get("pricing_snapshot_json"))
        context["service_rows"] = _service_rows((record or {}).get("services_json") or (workspace or {}).get("services_snapshot_json"))
        context["ssr_rows"] = _as_list((record or {}).get("ssr_json")) or _as_list((workspace or {}).get("ssr_json"))
        context["osi_rows"] = _as_list((record or {}).get("osi_json")) or _as_list((workspace or {}).get("osi_json"))
        context["pets_rows"] = _as_list(_as_dict((record or {}).get("pets_json") or (workspace or {}).get("pets_snapshot_json")).get("items"))
        context["special_items_rows"] = _as_list(_as_dict((record or {}).get("special_items_json") or (workspace or {}).get("special_items_snapshot_json")).get("items"))
        context["booking_summary"] = _compact(
            {
                "booking_workspace_id": (workspace or {}).get("id"),
                "workspace_number": (workspace or {}).get("workspace_number"),
                "booking_record_id": (record or {}).get("id"),
                "title": (workspace or {}).get("title"),
                "pnr_locator": (record or {}).get("pnr_locator"),
                "provider": (record or {}).get("provider") or (workspace or {}).get("provider_target"),
                "status": (record or {}).get("booking_status") or (workspace or {}).get("status"),
                "source_context": source.get("source_context"),
            }
        )
        context["warnings_json"].extend(_as_list((record or {}).get("warnings_json")) + _as_list((workspace or {}).get("warnings_json")))
        if workspace:
            context["source_links"].append({"type": "booking_workspace", "id": workspace["id"]})
        if record:
            context["source_links"].append({"type": "booking_record", "id": record["id"]})
        return context

    async def build_ticket_context(self, agency_id: str, ticket_record_id: str) -> dict[str, Any] | None:
        ticket = await self.db.collection("ticket_records").find_one({"agency_id": agency_id, "id": ticket_record_id})
        if not ticket:
            return None
        context = await self.build_booking_context(agency_id, ticket.get("booking_workspace_id"), ticket.get("booking_record_id")) or await self._base(agency_id)
        context["source_context_type"] = "ticket_record"
        context["source_context_id"] = ticket_record_id
        context["client_snapshot"] = context.get("client_snapshot") or await self._client_snapshot(agency_id, ticket.get("client_id"))
        context["trip_summary"] = context.get("trip_summary") or await self._trip_summary(agency_id, ticket.get("trip_id"))
        if ticket.get("passenger_snapshot_json"):
            context["passenger_snapshots"] = [_passenger_row(ticket.get("passenger_snapshot_json") or {})]
        context["ticket_summary"] = _compact(
            {
                "id": ticket["id"],
                "ticket_number": ticket.get("ticket_number"),
                "validating_carrier": ticket.get("validating_carrier") or ticket.get("validating_airline_code"),
                "status": ticket.get("issue_status") or ticket.get("status"),
                "provider": ticket.get("issuing_provider"),
                "currency": ticket.get("currency"),
                "base_fare_amount": ticket.get("base_fare_amount"),
                "taxes_amount": ticket.get("taxes_amount"),
                "total_amount": ticket.get("total_amount"),
            }
        )
        context["ticket_coupons"] = await self.db.collection("ticket_coupons").find_many({"agency_id": agency_id, "ticket_record_id": ticket_record_id}) or _as_list(ticket.get("coupons_json"))
        context["itinerary_segments"] = context.get("itinerary_segments") or [_segment_row(item) for item in _as_list(ticket.get("segments_snapshot_json"))]
        context["pricing_summary"] = context.get("pricing_summary") or _pricing_summary(ticket.get("pricing_snapshot_json") or ticket)
        context["warnings_json"].extend(_as_list(ticket.get("warnings_json")))
        context["source_links"].append({"type": "ticket_record", "id": ticket_record_id})
        return context

    async def build_emd_context(self, agency_id: str, emd_record_id: str) -> dict[str, Any] | None:
        emd = await self.db.collection("emd_records").find_one({"agency_id": agency_id, "id": emd_record_id})
        if not emd:
            return None
        context = await self.build_booking_context(agency_id, emd.get("booking_workspace_id"), emd.get("booking_record_id")) or await self._base(agency_id)
        context["source_context_type"] = "emd_record"
        context["source_context_id"] = emd_record_id
        context["client_snapshot"] = context.get("client_snapshot") or await self._client_snapshot(agency_id, emd.get("client_id"))
        context["trip_summary"] = context.get("trip_summary") or await self._trip_summary(agency_id, emd.get("trip_id"))
        context["emd_summary"] = _compact(
            {
                "id": emd["id"],
                "emd_number": emd.get("emd_number"),
                "emd_type": emd.get("emd_type"),
                "status": emd.get("issue_status") or emd.get("status"),
                "service_key": emd.get("service_key"),
                "service_label": emd.get("service_label"),
                "service_category": emd.get("service_category"),
                "currency": emd.get("currency"),
                "amount": emd.get("amount"),
                "taxes_amount": emd.get("taxes_amount"),
                "total_amount": emd.get("total_amount"),
            }
        )
        context["emd_coupons"] = await self.db.collection("emd_coupons").find_many({"agency_id": agency_id, "emd_record_id": emd_record_id})
        service = emd.get("linked_service_snapshot_json") or {"service_key": emd.get("service_key"), "service_label": emd.get("service_label"), "service_category": emd.get("service_category")}
        context["service_rows"] = _service_rows([service])
        context["warnings_json"].extend(_as_list(emd.get("warnings_json")))
        context["source_links"].append({"type": "emd_record", "id": emd_record_id})
        return context

    async def build_import_review_context(self, agency_id: str, booking_import_draft_id: str) -> dict[str, Any] | None:
        draft = await self.db.collection("booking_import_drafts").find_one({"agency_id": agency_id, "id": booking_import_draft_id})
        if not draft:
            return None
        parsed = _as_dict(draft.get("normalized_preview_json")) or _as_dict(draft.get("parsed_json"))
        context = await self._base(agency_id)
        context["source_context_type"] = "booking_import_draft"
        context["source_context_id"] = booking_import_draft_id
        context["client_snapshot"] = await self._client_snapshot(agency_id, draft.get("linked_client_id"))
        context["trip_summary"] = await self._trip_summary(agency_id, draft.get("linked_trip_id"))
        context["passenger_snapshots"] = [_passenger_row(item) for item in _as_list(parsed.get("passengers"))]
        context["itinerary_segments"] = [_segment_row(item) for item in _as_list(parsed.get("segments"))]
        context["ssr_rows"] = _as_list(parsed.get("ssr"))
        context["osi_rows"] = _as_list(parsed.get("osi"))
        context["ticket_numbers"] = _as_list(parsed.get("ticket_numbers"))
        context["emd_numbers"] = _as_list(parsed.get("emd_numbers"))
        context["import_summary"] = _compact(
            {
                "id": draft["id"],
                "source_type": draft.get("source_type"),
                "parser_status": draft.get("parser_status"),
                "latest_parser_run_id": draft.get("latest_parser_run_id"),
                "overall_confidence": draft.get("overall_confidence"),
                "record_locator": parsed.get("record_locator"),
                "import_context": draft.get("import_context"),
            }
        )
        if draft.get("latest_parser_run_id"):
            parser_context = await self.build_gds_parser_run_context(agency_id, draft["latest_parser_run_id"])
            if parser_context:
                context["parser_run_summary"] = parser_context.get("parser_run_summary") or {}
                context["parsed_entities"] = parser_context.get("parsed_entities") or []
                context["parse_corrections"] = parser_context.get("parse_corrections") or []
                context["training_samples"] = parser_context.get("training_samples") or []
        context["warnings_json"].extend(_as_list(draft.get("warnings_json")) + _as_list(parsed.get("warnings")))
        context["source_links"].append({"type": "booking_import_draft", "id": booking_import_draft_id})
        return context

    async def build_gds_parser_run_context(self, agency_id: str, parser_run_id: str) -> dict[str, Any] | None:
        run = await self.db.collection("gds_parser_runs").find_one({"agency_id": agency_id, "id": parser_run_id})
        if not run:
            return None
        preview = _as_dict(run.get("normalized_preview_json"))
        context = await self._base(agency_id)
        context["source_context_type"] = "gds_parser_run"
        context["source_context_id"] = parser_run_id
        context["passenger_snapshots"] = [_passenger_row(item) for item in _as_list(preview.get("passengers"))]
        context["itinerary_segments"] = [_segment_row(item) for item in _as_list(preview.get("segments"))]
        context["ssr_rows"] = _as_list(preview.get("ssr"))
        context["osi_rows"] = _as_list(preview.get("osi"))
        context["ticket_numbers"] = _as_list(preview.get("ticket_numbers"))
        context["emd_numbers"] = _as_list(preview.get("emd_numbers"))
        context["pricing_summary"] = _pricing_summary(preview.get("pricing"))
        context["parser_run_summary"] = _compact(
            {
                "id": run["id"],
                "booking_import_draft_id": run.get("booking_import_draft_id"),
                "parser_profile_id": run.get("parser_profile_id"),
                "parser_version_id": run.get("parser_version_id"),
                "provider_family_detected": run.get("provider_family_detected"),
                "input_format_detected": run.get("input_format_detected"),
                "parse_status": run.get("parse_status"),
                "overall_confidence": run.get("overall_confidence"),
                "record_locator": preview.get("record_locator"),
                "passengers": run.get("extracted_passenger_count"),
                "segments": run.get("extracted_segment_count"),
                "tickets": run.get("extracted_ticket_count"),
                "emds": run.get("extracted_emd_count"),
            }
        )
        entities = await self.db.collection("gds_parsed_entities").find_many({"agency_id": agency_id, "parser_run_id": parser_run_id})
        context["parsed_entities"] = [
            _compact(
                {
                    "id": item.get("id"),
                    "entity_type": item.get("entity_type"),
                    "summary": _as_dict(item.get("normalized_json")).get("summary"),
                    "confidence": item.get("confidence"),
                    "status": item.get("status"),
                    "source_text": item.get("source_text"),
                }
            )
            for item in entities
        ]
        context["parse_corrections"] = await self.db.collection("gds_parse_corrections").find_many({"agency_id": agency_id, "parser_run_id": parser_run_id})
        context["training_samples"] = await self.db.collection("gds_parse_training_samples").find_many({"agency_id": agency_id, "parser_run_id": parser_run_id})
        context["warnings_json"].extend(_as_list(run.get("warnings_json")) + _as_list(preview.get("warnings")))
        if run.get("booking_import_draft_id"):
            context["source_links"].append({"type": "booking_import_draft", "id": run["booking_import_draft_id"]})
        context["source_links"].append({"type": "gds_parser_run", "id": parser_run_id})
        return context

    async def build_trip_change_context(self, agency_id: str, trip_change_operation_id: str) -> dict[str, Any] | None:
        operation = await self.db.collection("trip_change_operations").find_one({"agency_id": agency_id, "id": trip_change_operation_id})
        if not operation:
            return None
        context = await self.build_trip_context(agency_id, operation.get("trip_id")) or await self._base(agency_id)
        context["source_context_type"] = "trip_change_operation"
        context["source_context_id"] = trip_change_operation_id
        context["change_exchange_summary"] = _compact(
            {
                "id": operation["id"],
                "operation_type": operation.get("operation_type"),
                "status": operation.get("status"),
                "reason": operation.get("reason"),
                "source_booking_workspace_id": operation.get("source_booking_workspace_id"),
                "source_booking_record_id": operation.get("source_booking_record_id"),
                "new_booking_workspace_id": operation.get("new_booking_workspace_id"),
                "new_booking_record_id": operation.get("new_booking_record_id"),
                "summary": operation.get("change_summary_json"),
            }
        )
        context["warnings_json"].extend(_as_list(operation.get("warnings_json")))
        context["source_links"].append({"type": "trip_change_operation", "id": trip_change_operation_id})
        return context

    async def build_ticket_exchange_context(self, agency_id: str, ticket_exchange_operation_id: str) -> dict[str, Any] | None:
        operation = await self.db.collection("ticket_exchange_operations").find_one({"agency_id": agency_id, "id": ticket_exchange_operation_id})
        if not operation:
            return None
        context = await self.build_ticket_context(agency_id, operation.get("original_ticket_record_id")) or await self._base(agency_id)
        context["source_context_type"] = "ticket_exchange_operation"
        context["source_context_id"] = ticket_exchange_operation_id
        context["change_exchange_summary"] = _compact(
            {
                "id": operation["id"],
                "operation_type": operation.get("operation_type"),
                "status": operation.get("status"),
                "reason": operation.get("reason"),
                "original_ticket_record_id": operation.get("original_ticket_record_id"),
                "new_ticket_record_id": operation.get("new_ticket_record_id"),
                "currency": operation.get("currency"),
                "fare_difference": operation.get("fare_difference_json"),
            }
        )
        context["warnings_json"].extend(_as_list(operation.get("warnings_json")))
        context["source_links"].append({"type": "ticket_exchange_operation", "id": ticket_exchange_operation_id})
        return context

    async def build_emd_exchange_context(self, agency_id: str, emd_exchange_operation_id: str) -> dict[str, Any] | None:
        operation = await self.db.collection("emd_exchange_operations").find_one({"agency_id": agency_id, "id": emd_exchange_operation_id})
        if not operation:
            return None
        context = await self.build_emd_context(agency_id, operation.get("original_emd_record_id")) or await self._base(agency_id)
        context["source_context_type"] = "emd_exchange_operation"
        context["source_context_id"] = emd_exchange_operation_id
        context["change_exchange_summary"] = _compact(
            {
                "id": operation["id"],
                "operation_type": operation.get("operation_type"),
                "status": operation.get("status"),
                "reason": operation.get("reason"),
                "original_emd_record_id": operation.get("original_emd_record_id"),
                "new_emd_record_id": operation.get("new_emd_record_id"),
                "currency": operation.get("currency"),
            }
        )
        context["warnings_json"].extend(_as_list(operation.get("warnings_json")))
        context["source_links"].append({"type": "emd_exchange_operation", "id": emd_exchange_operation_id})
        return context

    async def build_mixed_context(self, agency_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        context = await self._base(agency_id)
        context["source_context_type"] = "mixed_context"
        context["source_context_ids_json"] = payload
        context["warnings_json"].append(_warning("mixed_context_manual_review", "Mixed context preview preserves selected ids for staff review."))
        for source_type, source_id in payload.items():
            if source_id:
                context["source_links"].append({"type": source_type, "id": source_id})
        return context

    async def build_context_by_type(
        self,
        agency_id: str,
        source_context_type: str,
        source_context_id: str | None = None,
        source_context_ids_json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        ids = source_context_ids_json or {}
        if source_context_type == "request" and source_context_id:
            return await self.build_request_context(agency_id, source_context_id)
        if source_context_type == "offer_workspace" and source_context_id:
            return await self.build_offer_context(agency_id, source_context_id, ids.get("offer_option_id"))
        if source_context_type == "offer_option" and source_context_id:
            option = await self.db.collection("offer_options").find_one({"agency_id": agency_id, "id": source_context_id})
            if not option:
                return None
            return await self.build_offer_context(agency_id, option["workspace_id"], source_context_id)
        if source_context_type == "offer_acceptance" and source_context_id:
            acceptance = await self.db.collection("offer_acceptances").find_one({"agency_id": agency_id, "id": source_context_id})
            if not acceptance:
                return None
            return await self.build_offer_context(agency_id, acceptance["workspace_id"], acceptance["option_id"])
        if source_context_type == "trip" and source_context_id:
            return await self.build_trip_context(agency_id, source_context_id)
        if source_context_type == "booking_workspace" and source_context_id:
            return await self.build_booking_context(agency_id, booking_workspace_id=source_context_id)
        if source_context_type == "booking_record" and source_context_id:
            return await self.build_booking_context(agency_id, booking_record_id=source_context_id)
        if source_context_type == "ticket_record" and source_context_id:
            return await self.build_ticket_context(agency_id, source_context_id)
        if source_context_type == "emd_record" and source_context_id:
            return await self.build_emd_context(agency_id, source_context_id)
        if source_context_type == "booking_import_draft" and source_context_id:
            return await self.build_import_review_context(agency_id, source_context_id)
        if source_context_type == "gds_parser_run" and source_context_id:
            return await self.build_gds_parser_run_context(agency_id, source_context_id)
        if source_context_type == "trip_change_operation" and source_context_id:
            return await self.build_trip_change_context(agency_id, source_context_id)
        if source_context_type == "ticket_exchange_operation" and source_context_id:
            return await self.build_ticket_exchange_context(agency_id, source_context_id)
        if source_context_type == "emd_exchange_operation" and source_context_id:
            return await self.build_emd_exchange_context(agency_id, source_context_id)
        if source_context_type == "service_request" and source_context_id:
            service = await self.db.collection("passenger_service_requests").find_one({"agency_id": agency_id, "id": source_context_id})
            if not service:
                return None
            context = await self._base(agency_id)
            context["source_context_type"] = "service_request"
            context["source_context_id"] = source_context_id
            context["trip_summary"] = await self._trip_summary(agency_id, service.get("trip_id"))
            context["service_rows"] = _service_rows([service])
            context["ssr_rows"] = _as_list(service.get("generated_ssr_json"))
            context["osi_rows"] = _as_list(service.get("generated_osi_json"))
            context["warnings_json"].extend(_as_list(service.get("warnings_json")))
            context["source_links"].append({"type": "service_request", "id": source_context_id})
            return context
        if source_context_type == "mixed_context":
            return await self.build_mixed_context(agency_id, ids)
        return None
