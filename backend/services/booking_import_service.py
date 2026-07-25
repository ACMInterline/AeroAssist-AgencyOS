from __future__ import annotations

import re
from typing import Any

from database import Database
from models import (
    BookingImportContext,
    BookingImportDraft,
    BookingImportDraftCreate,
    BookingImportDraftImportRequest,
    BookingImportDraftSourceType,
    BookingImportParserStatus,
    BookingRecordUpdate,
    BookingSourceContext,
    EmdSourceContext,
    ManualBookingWorkspaceCreate,
    ManualEmdCreate,
    ManualTicketCreate,
    TicketSourceContext,
)
from services.booking_workspace_service import BookingWorkspaceService
from services.gds_parser_service import GdsParserService
from services.ticket_emd_service import TicketEmdService


class BookingImportError(ValueError):
    pass


def _source_context(source_type: str) -> str:
    if source_type == BookingImportDraftSourceType.CRYPTIC_GDS.value:
        return BookingSourceContext.IMPORTED_GDS.value
    return BookingSourceContext.IMPORTED_CONFIRMATION.value


def _ticket_source_context(source_type: str) -> str:
    if source_type == BookingImportDraftSourceType.CRYPTIC_GDS.value:
        return TicketSourceContext.IMPORTED_GDS.value
    return TicketSourceContext.IMPORTED_CONFIRMATION.value


def _emd_source_context(source_type: str) -> str:
    if source_type == BookingImportDraftSourceType.CRYPTIC_GDS.value:
        return EmdSourceContext.IMPORTED_GDS.value
    return EmdSourceContext.IMPORTED_CONFIRMATION.value


class BookingImportService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_import_draft(
        self,
        agency_id: str,
        payload: BookingImportDraftCreate,
        user: dict,
    ) -> dict[str, Any]:
        draft = BookingImportDraft(
            agency_id=agency_id,
            created_by_user_id=user.get("id"),
            source_type=payload.source_type,
            raw_text=payload.raw_text,
            linked_client_id=payload.linked_client_id,
            linked_passenger_ids=payload.linked_passenger_ids or [],
            linked_trip_id=payload.linked_trip_id,
            import_context=payload.import_context,
            warnings_json=[],
        )
        created = await self.db.collection("booking_import_drafts").insert_one(draft.model_dump(mode="json"))
        return {"draft": created, "provider_execution_disabled": True}

    async def parse_import_draft(self, agency_id: str, draft_id: str, user: dict) -> dict[str, Any] | None:
        result = await GdsParserService(self.db).parse_booking_import_draft(agency_id, draft_id, {}, user)
        if not result:
            return None
        return {**result, "provider_execution_disabled": True}

    async def import_draft_as_booking(
        self,
        agency_id: str,
        draft_id: str,
        payload: BookingImportDraftImportRequest,
        user: dict,
    ) -> dict[str, Any] | None:
        draft = await self.get_import_draft(agency_id, draft_id)
        if not draft:
            return None
        if not draft.get("parsed_json"):
            parsed_result = await self.parse_import_draft(agency_id, draft_id, user)
            draft = (parsed_result or {}).get("draft") or draft
        parsed = draft.get("parsed_json") or self._parse_text(draft.get("raw_text") or "")
        source_context = _source_context(draft.get("source_type"))
        trip_id = draft.get("linked_trip_id")
        if draft.get("import_context") == BookingImportContext.EXISTING_TRIP_CHANGE.value and not trip_id:
            raise BookingImportError("Existing trip change imports require linked_trip_id.")
        manual_payload = ManualBookingWorkspaceCreate(
            client_id=draft.get("linked_client_id"),
            passenger_ids=draft.get("linked_passenger_ids") or [],
            trip_id=trip_id,
            title=payload.title,
            provider_target=payload.provider_target,
            pnr_locator=parsed.get("record_locator"),
            passengers_json=parsed.get("passengers") or [],
            segments_json=parsed.get("segments") or [],
            pricing_json=parsed.get("pricing") or {},
            ssr_json=parsed.get("ssr") or [],
            osi_json=parsed.get("osi") or [],
            internal_notes=payload.internal_notes,
            create_draft_record=payload.create_draft_record,
            source_context=source_context,
            import_draft_id=draft_id,
        )
        booking_service = BookingWorkspaceService(self.db)
        booking_result = await booking_service.create_manual_booking_workspace(
            agency_id,
            manual_payload,
            user,
        )
        workspace = booking_result.get("booking_workspace") or {}
        record = booking_result.get("booking_record") or {}
        imported_artifacts_requested = bool(
            (payload.create_ticket_mirrors and parsed.get("ticket_numbers"))
            or (payload.create_emd_mirrors and parsed.get("emd_numbers"))
        )
        if record and imported_artifacts_requested and not parsed.get("record_locator"):
            raise BookingImportError(
                "Imported Ticket or EMD mirrors require a reviewed booking record locator."
            )
        if record and parsed.get("record_locator"):
            await booking_service.update_booking_workspace_status(
                agency_id,
                workspace["id"],
                "ready_to_book",
                user,
                "Reviewed imported booking metadata before confirmation.",
            )
            await booking_service.update_booking_workspace_status(
                agency_id,
                workspace["id"],
                "booking_in_progress",
                user,
                "Human operator began imported booking reconciliation.",
            )
            confirmed_booking = await booking_service.update_booking_record(
                agency_id,
                record["id"],
                BookingRecordUpdate(
                    pnr_locator=parsed["record_locator"],
                    provider_status="confirmed",
                    booking_status="confirmed",
                    source_evidence_reference=f"booking-import:{draft_id}",
                    source_evidence_json={
                        "import_draft_id": draft_id,
                        "source_type": draft.get("source_type"),
                        "parser_status": draft.get("parser_status"),
                        "operator_reviewed": True,
                    },
                    expected_version=record.get("current_external_result_version"),
                    reason="Recorded a reviewed imported booking result.",
                ),
                user,
            )
            workspace = (confirmed_booking or {}).get("booking_workspace") or workspace
            record = (confirmed_booking or {}).get("booking_record") or record

        ticket_ids: list[str] = []
        if payload.create_ticket_mirrors:
            for ticket_number in parsed.get("ticket_numbers") or []:
                ticket = await TicketEmdService(self.db).create_manual_ticket(
                    agency_id,
                    ManualTicketCreate(
                        booking_record_id=record.get("id"),
                        booking_workspace_id=workspace.get("id"),
                        trip_id=trip_id,
                        client_id=draft.get("linked_client_id"),
                        ticket_number=ticket_number,
                        issuing_provider=payload.provider_target,
                        segments_snapshot_json=parsed.get("segments") or [],
                        pricing_snapshot_json=parsed.get("pricing") or {},
                        source_context=_ticket_source_context(draft.get("source_type")),
                        import_draft_id=draft_id,
                    ),
                    user,
                )
                ticket_ids.append(ticket["ticket"]["id"])

        emd_ids: list[str] = []
        if payload.create_emd_mirrors:
            for emd_number in parsed.get("emd_numbers") or []:
                emd = await TicketEmdService(self.db).create_manual_emd(
                    agency_id,
                    ManualEmdCreate(
                        booking_record_id=record.get("id"),
                        booking_workspace_id=workspace.get("id"),
                        trip_id=trip_id,
                        client_id=draft.get("linked_client_id"),
                        emd_number=emd_number,
                        service_label="Imported EMD service",
                        source_context=_emd_source_context(draft.get("source_type")),
                        import_draft_id=draft_id,
                    ),
                    user,
                )
                emd_ids.append(emd["emd"]["id"])

        updated = await self.db.collection("booking_import_drafts").update_one(
            {"agency_id": agency_id, "id": draft_id},
            {
                "parser_status": BookingImportParserStatus.IMPORTED.value,
                "linked_booking_workspace_id": workspace.get("id"),
                "linked_booking_record_id": record.get("id"),
                "linked_ticket_record_ids": ticket_ids,
                "linked_emd_record_ids": emd_ids,
            },
        )
        return {
            "draft": updated,
            "booking_workspace": workspace,
            "booking_record": record,
            "ticket_record_ids": ticket_ids,
            "emd_record_ids": emd_ids,
            "provider_execution_disabled": True,
        }

    async def list_import_drafts(self, agency_id: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {"agency_id": agency_id}
        filters = filters or {}
        for key in ["source_type", "parser_status", "linked_trip_id", "import_context"]:
            if filters.get(key):
                query[key] = filters[key]
        items = await self.db.collection("booking_import_drafts").find_many(query)
        items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return {"items": items, "provider_execution_disabled": True}

    async def get_import_draft(self, agency_id: str, draft_id: str) -> dict[str, Any] | None:
        return await self.db.collection("booking_import_drafts").find_one({"agency_id": agency_id, "id": draft_id})

    def _parse_text(self, raw_text: str) -> dict[str, Any]:
        lines = [line.rstrip() for line in raw_text.splitlines()]
        joined = "\n".join(lines)
        locator = self._record_locator(joined)
        passengers = self._passengers(lines)
        segments = self._segments(lines)
        tickets = sorted(set(re.findall(r"\b(?:TKT|TK|ETKT|TICKET)[\s:/-]*(\d{3}[- ]?\d{10})\b", joined, re.IGNORECASE)))
        emds = sorted(set(re.findall(r"\b(?:EMD|EMDS)[\s:/-]*(\d{3}[- ]?\d{10})\b", joined, re.IGNORECASE)))
        ssr = [{"line": line.strip()} for line in lines if line.strip().upper().startswith("SSR")]
        osi = [{"line": line.strip()} for line in lines if line.strip().upper().startswith("OSI")]
        warnings = []
        if not locator:
            warnings.append({"code": "locator_not_found", "message": "No obvious record locator was found.", "severity": "warning"})
        if not passengers:
            warnings.append({"code": "passengers_not_found", "message": "No obvious passenger lines were found.", "severity": "warning"})
        if not segments:
            warnings.append({"code": "segments_not_found", "message": "No obvious flight segment lines were found.", "severity": "warning"})
        return {
            "record_locator": locator,
            "passengers": passengers,
            "segments": segments,
            "ticket_numbers": tickets,
            "emd_numbers": emds,
            "ssr": ssr,
            "osi": osi,
            "pricing": {},
            "warnings": warnings,
            "confidence": "low",
            "parser": "phase_36_4_6_deterministic_stub",
        }

    def _record_locator(self, text: str) -> str | None:
        for pattern in [
            r"\b(?:PNR|LOCATOR|RECORD\s+LOCATOR|CONFIRMATION)[\s:#-]*([A-Z0-9]{5,8})\b",
            r"\b([A-Z0-9]{6})\s+(?:PNR|LOCATOR)\b",
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None

    def _passengers(self, lines: list[str]) -> list[dict[str, Any]]:
        passengers: list[dict[str, Any]] = []
        for line in lines:
            match = re.search(r"(?:PAX|PASSENGER|NM\d*|\d+\.)\s*([A-Z][A-Z'\-]+)/([A-Z][A-Z'\- ]+)", line, re.IGNORECASE)
            if match:
                last_name = match.group(1).upper()
                first_name = match.group(2).strip().upper()
                passengers.append(
                    {
                        "id": f"import-pax-{len(passengers) + 1}",
                        "first_name": first_name.title(),
                        "last_name": last_name.title(),
                        "display_name": f"{first_name.title()} {last_name.title()}",
                        "raw_line": line.strip(),
                    }
                )
        return passengers

    def _segments(self, lines: list[str]) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []
        pattern = re.compile(
            r"\b([A-Z0-9]{2})\s*([0-9]{2,4})\s+([A-Z])?\s*(\d{1,2}[A-Z]{3})?\s*([A-Z]{3})([A-Z]{3})\b",
            re.IGNORECASE,
        )
        for line in lines:
            match = pattern.search(line)
            if not match:
                continue
            segments.append(
                {
                    "id": f"import-seg-{len(segments) + 1}",
                    "sequence": len(segments) + 1,
                    "marketing_airline_code": match.group(1).upper(),
                    "flight_number": match.group(2),
                    "booking_class": (match.group(3) or "").upper() or None,
                    "departure_raw": match.group(4),
                    "origin_airport_code": match.group(5).upper(),
                    "destination_airport_code": match.group(6).upper(),
                    "raw_line": line.strip(),
                }
            )
        return segments
