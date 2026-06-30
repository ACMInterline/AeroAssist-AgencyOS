from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any

from database import Database
from models import (
    DocumentPackage,
    DocumentPackageCreate,
    DocumentPackageStatus,
    DocumentRenderJob,
    DocumentRenderJobCreate,
    DocumentRenderStatus,
    DocumentShareRecord,
    DocumentShareRecordCreate,
    DocumentShareStatus,
    DocumentTemplate,
    DocumentTemplateScope,
)
from services.document_context_service import DocumentContextService


PHASE_LABEL = "phase_36_6_gds_parser_foundation"


DEFAULT_TEMPLATES = [
    ("offer_summary", "offer_summary", "Offer Summary", "Commercial summary for an offer option or workspace."),
    ("offer_comparison", "offer_comparison", "Offer Comparison", "Internal comparison of offer options."),
    ("trip_confirmation", "trip_confirmation", "Trip Confirmation", "Trip dossier confirmation from stored itinerary and service data."),
    ("booking_confirmation", "booking_confirmation", "Booking Confirmation / PNR Mirror", "Booking workspace and PNR mirror summary."),
    ("pnr_mirror", "pnr_mirror", "PNR Mirror Summary", "Internal PNR mirror data summary."),
    ("ticket_receipt", "ticket_receipt", "Ticket Receipt", "Internal ticket mirror receipt."),
    ("emd_receipt", "emd_receipt", "EMD Receipt", "Internal EMD mirror receipt."),
    ("service_confirmation", "service_confirmation", "Service Confirmation", "Service, SSR, OSI, and catalogue snapshot confirmation."),
    ("medical_assistance_summary", "medical_assistance_summary", "Medical Assistance Summary", "Medical or mobility assistance summary."),
    ("pet_travel_summary", "pet_travel_summary", "Pet Travel Summary", "Pet/service animal travel summary."),
    ("special_baggage_summary", "special_baggage_summary", "Special Baggage Summary", "Special baggage or item transport summary."),
    ("trip_change_summary", "trip_change_summary", "Trip Change Summary", "Existing-trip change operation summary."),
    ("ticket_exchange_quote", "exchange_quote", "Ticket Exchange Quote", "Ticket exchange quote summary."),
    ("emd_exchange_quote", "exchange_quote", "EMD Exchange Quote", "EMD exchange quote summary."),
    ("exchange_confirmation", "exchange_confirmation", "Exchange Confirmation", "Internal exchange/reissue mirror confirmation."),
    ("refund_quote", "refund_quote", "Refund Quote", "Internal refund quote summary."),
    ("import_review_summary", "import_review_summary", "Import Review Summary", "Booking import parse/review summary."),
    ("booking_import_review_summary", "booking_import_review_summary", "Booking Import Review Summary", "Governed booking import parser review summary."),
    ("gds_parse_review_summary", "gds_parse_review_summary", "GDS Parse Review Summary", "Parser run confidence, entities, warnings, and correction summary."),
    ("internal_case_summary", "internal_case_summary", "Internal Case Summary", "Internal operational case summary."),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _label(value: Any) -> str:
    return str(value or "not set").replace("_", " ")


def _safe(value: Any, fallback: str = "not set") -> str:
    if value is None or value == "":
        return escape(fallback)
    if isinstance(value, (list, dict)):
        return escape(_summarize(value))
    return escape(str(value))


def _summarize(value: Any) -> str:
    if isinstance(value, list):
        return f"{len(value)} item{'s' if len(value) != 1 else ''}"
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if item is not None and item != "" and not isinstance(item, (list, dict)):
                parts.append(f"{key}: {item}")
            if len(parts) >= 4:
                break
        return ", ".join(parts) if parts else f"{len(value)} fields"
    return str(value or "")


def _money(amount: Any, currency: str | None = None) -> str:
    if amount is None or amount == "":
        return "not priced"
    try:
        rendered = f"{float(amount):.2f}"
    except (TypeError, ValueError):
        rendered = str(amount)
    return f"{rendered} {currency or ''}".strip()


def _section(title: str, body: str) -> str:
    return f"""
    <section style="margin:0 0 24px">
      <h2 style="margin:0 0 10px;font-size:14px;letter-spacing:.04em;text-transform:uppercase;color:#334155">{_safe(title)}</h2>
      {body}
    </section>
    """


def _key_values(rows: list[tuple[str, Any]]) -> str:
    cards = "".join(
        f"""
        <div style="border:1px solid #e2e8f0;border-radius:8px;padding:10px">
          <div style="font-size:12px;color:#64748b">{_safe(label)}</div>
          <div style="margin-top:4px;font-weight:700;color:#0f172a">{_safe(value)}</div>
        </div>
        """
        for label, value in rows
    )
    return f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px">{cards}</div>'


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return '<p style="margin:0;color:#64748b;font-size:13px">No records available.</p>'
    head = "".join(f'<th style="text-align:left;border-bottom:1px solid #cbd5e1;background:#f8fafc;padding:8px">{_safe(header)}</th>' for header in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f'<td style="border-bottom:1px solid #e2e8f0;padding:8px;vertical-align:top">{_safe(value)}</td>' for value in row) + "</tr>"
    return f'<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _shell(title: str, context: dict[str, Any], body: str, warnings: list[dict[str, Any]]) -> str:
    agency = context.get("agency_snapshot") or {}
    primary = agency.get("primary_color") or "#2563eb"
    secondary = agency.get("secondary_color") or "#0f172a"
    brand_name = agency.get("brand_name") or agency.get("name") or "AeroAssist AgencyOS"
    warning_html = ""
    if warnings:
        warning_html = _section(
            "Warnings",
            _table(["Code", "Message"], [[item.get("code"), item.get("message")] for item in warnings]),
        )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_safe(title)}</title>
</head>
<body style="margin:0;background:#f8fafc;color:#0f172a;font-family:Inter,Arial,sans-serif">
  <main style="max-width:960px;margin:0 auto;background:#fff;min-height:100vh">
    <header style="border-bottom:4px solid {_safe(primary)};padding:28px 32px">
      <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;flex-wrap:wrap">
        <div>
          <div style="font-size:22px;font-weight:800;color:{_safe(primary)}">{_safe(brand_name)}</div>
          <p style="margin:8px 0 0;color:#64748b;font-size:13px">Internal document foundation preview</p>
        </div>
        <div style="text-align:right;color:{_safe(secondary)};font-size:12px">
          <strong>Internal mirror only</strong><br />
          Rendered {_safe(_now_iso())}<br />
          No provider execution
        </div>
      </div>
      <h1 style="margin:24px 0 0;font-size:28px;line-height:1.2;color:{_safe(secondary)}">{_safe(title)}</h1>
    </header>
    <section style="padding:28px 32px">
      {body}
      {warning_html}
    </section>
    <footer style="border-top:1px solid #e2e8f0;padding:18px 32px;color:#64748b;font-size:12px;line-height:1.5">
      Agency-generated internal document preview from stored AgencyOS records. No live booking, ticketing, EMD issuance, delivery, payment, e-signature, settlement, or provider action is performed.
    </footer>
  </main>
</body>
</html>"""


def _render_text(title: str, context: dict[str, Any], warnings: list[dict[str, Any]]) -> str:
    parts = [title, "", "Internal mirror only. No provider execution.", ""]
    trip = context.get("trip_summary") or {}
    booking = context.get("booking_summary") or {}
    ticket = context.get("ticket_summary") or {}
    emd = context.get("emd_summary") or {}
    change = context.get("change_exchange_summary") or {}
    for label, value in [
        ("Trip", trip.get("trip_reference") or trip.get("trip_title")),
        ("Booking", booking.get("pnr_locator") or booking.get("workspace_number")),
        ("Ticket", ticket.get("ticket_number")),
        ("EMD", emd.get("emd_number")),
        ("Change/exchange", change.get("operation_type")),
    ]:
        if value:
            parts.append(f"{label}: {value}")
    parts.append(f"Passengers: {len(context.get('passenger_snapshots') or [])}")
    parts.append(f"Segments: {len(context.get('itinerary_segments') or [])}")
    parts.append(f"Services: {len(context.get('service_rows') or [])}")
    if warnings:
        parts.append("")
        parts.append("Warnings:")
        parts.extend(f"- {item.get('code')}: {item.get('message')}" for item in warnings)
    return "\n".join(parts)


def _title(document_type: str, context: dict[str, Any], template: dict[str, Any] | None) -> str:
    base = (template or {}).get("title") or (template or {}).get("name") or _label(document_type).title()
    trip = context.get("trip_summary") or {}
    booking = context.get("booking_summary") or {}
    ticket = context.get("ticket_summary") or {}
    emd = context.get("emd_summary") or {}
    suffix = (
        trip.get("trip_reference")
        or booking.get("pnr_locator")
        or ticket.get("ticket_number")
        or emd.get("emd_number")
        or context.get("source_context_id")
    )
    return f"{base} {suffix}" if suffix else base


class DocumentRenderService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.contexts = DocumentContextService(db)

    async def seed_default_templates(self) -> dict[str, Any]:
        created = []
        existing_count = 0
        for template_key, template_type, title, description in DEFAULT_TEMPLATES:
            existing = await self.db.collection("document_templates").find_one({"scope": "platform", "template_key": template_key})
            if existing:
                existing_count += 1
                continue
            template = DocumentTemplate(
                agency_id=None,
                template_scope=DocumentTemplateScope.PLATFORM_DEFAULT,
                scope="platform",
                template_key=template_key,
                template_type=template_type,
                document_type=template_type,
                name=title,
                title=title,
                description=description,
                status="active",
                active=True,
                language="en",
                locale="en",
                version=1,
                layout_json={"layout": "clean_internal_html", "phase": PHASE_LABEL},
                content_blocks_json=[
                    {"block": "header", "label": "Header / branding placeholder"},
                    {"block": "client_passengers", "label": "Client / passenger section"},
                    {"block": "itinerary", "label": "Itinerary section"},
                    {"block": "services", "label": "Services / SSR / OSI section"},
                    {"block": "pricing", "label": "Pricing section"},
                    {"block": "documents_warnings", "label": "Notes and warnings"},
                ],
                required_context_json={"source_context_type": "any_supported", "provider_execution_disabled": True},
            )
            created.append(await self.db.collection("document_templates").insert_one(template.model_dump(mode="json")))
        return {"created_count": len(created), "existing_count": existing_count, "items": created}

    async def list_templates(self, agency_id: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = filters or {}
        items = [
            item
            for item in await self.db.collection("document_templates").find_many()
            if item.get("agency_id") in {None, agency_id}
        ]
        for key in ["template_key", "template_type", "document_type", "scope"]:
            if filters.get(key):
                items = [item for item in items if item.get(key) == filters[key] or item.get("document_type") == filters[key]]
        if filters.get("active") is not None:
            items = [item for item in items if bool(item.get("active", item.get("status") == "active")) is filters["active"]]
        items.sort(key=lambda item: (item.get("scope") or "", item.get("template_type") or item.get("document_type") or "", item.get("title") or item.get("name") or ""))
        return {"items": items}

    async def get_template(self, agency_id: str, template_id: str) -> dict[str, Any] | None:
        template = await self.db.collection("document_templates").find_one({"id": template_id})
        if template and template.get("agency_id") in {None, agency_id}:
            return template
        return None

    async def _select_template(self, agency_id: str, payload: DocumentRenderJobCreate | dict[str, Any]) -> dict[str, Any] | None:
        template_id = payload.template_id if hasattr(payload, "template_id") else payload.get("template_id")
        template_key = payload.template_key if hasattr(payload, "template_key") else payload.get("template_key")
        document_type = payload.document_type if hasattr(payload, "document_type") else payload.get("document_type")
        if template_id:
            return await self.get_template(agency_id, template_id)
        if template_key:
            template = await self.db.collection("document_templates").find_one({"template_key": template_key, "agency_id": agency_id})
            return template or await self.db.collection("document_templates").find_one({"template_key": template_key, "scope": "platform"})
        template = await self.db.collection("document_templates").find_one({"agency_id": agency_id, "template_type": document_type, "active": True})
        return template or await self.db.collection("document_templates").find_one({"scope": "platform", "template_type": document_type, "active": True})

    async def _build_context(self, agency_id: str, payload: DocumentRenderJobCreate | dict[str, Any]) -> dict[str, Any] | None:
        source_context_type = payload.source_context_type if hasattr(payload, "source_context_type") else payload.get("source_context_type")
        source_context_id = payload.source_context_id if hasattr(payload, "source_context_id") else payload.get("source_context_id")
        source_context_ids_json = payload.source_context_ids_json if hasattr(payload, "source_context_ids_json") else payload.get("source_context_ids_json")
        context = await self.contexts.build_context_by_type(agency_id, source_context_type, source_context_id, source_context_ids_json or {})
        extra = payload.render_context_json if hasattr(payload, "render_context_json") else payload.get("render_context_json")
        if context is not None and extra:
            context["manual_context_json"] = extra
        return context

    def _render(self, document_type: str, context: dict[str, Any], template: dict[str, Any] | None) -> tuple[str, str, str]:
        title = _title(document_type, context, template)
        client = context.get("client_snapshot") or {}
        trip = context.get("trip_summary") or {}
        booking = context.get("booking_summary") or {}
        pricing = context.get("pricing_summary") or {}
        ticket = context.get("ticket_summary") or {}
        emd = context.get("emd_summary") or {}
        change = context.get("change_exchange_summary") or {}
        warnings = list(context.get("warnings_json") or [])
        source = context.get("source_context_type")
        body = _section(
            "Overview",
            _key_values(
                [
                    ("Document type", _label(document_type)),
                    ("Source", _label(source)),
                    ("Client", client.get("display_name")),
                    ("Trip", trip.get("trip_reference") or trip.get("trip_title")),
                    ("PNR", booking.get("pnr_locator")),
                    ("Status", booking.get("status") or ticket.get("status") or emd.get("status") or change.get("status")),
                ]
            ),
        )
        body += _section("Passengers", _table(["Passenger", "Type", "Reference"], [[p.get("display_name"), p.get("passenger_type"), p.get("passenger_id") or p.get("id")] for p in context.get("passenger_snapshots") or []]))
        body += _section("Itinerary", _table(["#", "Airline", "Flight", "From", "To", "Departure", "Cabin", "Status"], [[s.get("sequence"), s.get("airline"), s.get("flight_number"), s.get("origin"), s.get("destination"), s.get("departure"), s.get("cabin"), s.get("status")] for s in context.get("itinerary_segments") or []]))
        body += _section("Services", _table(["Key", "Label", "Category", "Passenger", "Segment", "Status"], [[s.get("service_key"), s.get("service_label"), s.get("service_category"), s.get("passenger_reference"), s.get("segment_reference"), s.get("status")] for s in context.get("service_rows") or []]))
        body += _section("SSR / OSI", _table(["Type", "Code / airline", "Text"], [["SSR", item.get("ssr_code") or item.get("code"), item.get("free_text") or item.get("text")] for item in context.get("ssr_rows") or []] + [["OSI", item.get("airline_code") or item.get("airline"), item.get("text") or item.get("osi_text")] for item in context.get("osi_rows") or []]))
        if pricing:
            body += _section("Pricing", _key_values([("Currency", pricing.get("currency")), ("Base fare", _money(pricing.get("base_fare_amount"), pricing.get("currency"))), ("Taxes", _money(pricing.get("taxes_amount"), pricing.get("currency"))), ("Fees", _money(pricing.get("fees_amount"), pricing.get("currency"))), ("Total", _money(pricing.get("total_amount"), pricing.get("currency")))]))
        if ticket:
            body += _section("Ticket", _key_values([("Ticket number", ticket.get("ticket_number")), ("Validating carrier", ticket.get("validating_carrier")), ("Provider", ticket.get("provider")), ("Status", ticket.get("status")), ("Total", _money(ticket.get("total_amount"), ticket.get("currency")))]))
            body += _section("Ticket coupons", _table(["#", "Flight", "From", "To", "Status"], [[c.get("coupon_number"), " ".join(str(value or "") for value in [c.get("marketing_carrier"), c.get("flight_number")]).strip(), c.get("origin_airport_code"), c.get("destination_airport_code"), c.get("coupon_status")] for c in context.get("ticket_coupons") or []]))
        if emd:
            body += _section("EMD", _key_values([("EMD number", emd.get("emd_number")), ("Type", emd.get("emd_type")), ("Service", emd.get("service_label") or emd.get("service_key")), ("Status", emd.get("status")), ("Total", _money(emd.get("total_amount") or emd.get("amount"), emd.get("currency")))]))
            body += _section("EMD coupons", _table(["#", "Service", "Segment", "Status"], [[c.get("coupon_number"), c.get("service_label") or c.get("service_key"), c.get("segment_id"), c.get("coupon_status")] for c in context.get("emd_coupons") or []]))
        if change:
            body += _section("Change / exchange", _key_values([("Operation", change.get("operation_type")), ("Reason", change.get("reason")), ("Original", change.get("original_ticket_record_id") or change.get("original_emd_record_id") or change.get("source_booking_record_id")), ("New mirror", change.get("new_ticket_record_id") or change.get("new_emd_record_id") or change.get("new_booking_record_id"))]))
        if context.get("import_summary"):
            imported = context["import_summary"]
            body += _section("Import review", _key_values([("Source type", imported.get("source_type")), ("Parser status", imported.get("parser_status")), ("Parser run", imported.get("latest_parser_run_id")), ("Confidence", imported.get("overall_confidence")), ("Record locator", imported.get("record_locator")), ("Tickets parsed", len(context.get("ticket_numbers") or [])), ("EMDs parsed", len(context.get("emd_numbers") or []))]))
        if context.get("parser_run_summary"):
            parser = context["parser_run_summary"]
            body += _section("Parser run", _key_values([("Status", parser.get("parse_status")), ("Confidence", parser.get("overall_confidence")), ("Detected provider", parser.get("provider_family_detected")), ("Detected format", parser.get("input_format_detected")), ("Profile", parser.get("parser_profile_id")), ("Version", parser.get("parser_version_id"))]))
            body += _section("Parsed entities", _table(["Type", "Summary", "Confidence", "Status"], [[item.get("entity_type"), item.get("summary"), item.get("confidence"), item.get("status")] for item in context.get("parsed_entities") or []]))
            body += _section("Corrections", _table(["Type", "Entity", "Reason"], [[item.get("correction_type"), item.get("parsed_entity_id"), item.get("correction_reason")] for item in context.get("parse_corrections") or []]))
            body += _section("Training samples", _table(["Title", "Status", "Difficulty"], [[item.get("sample_title"), item.get("sample_status"), item.get("difficulty")] for item in context.get("training_samples") or []]))
        body += _section("Source links", _table(["Type", "Id"], [[item.get("type"), item.get("id")] for item in context.get("source_links") or []]))
        return title, _shell(title, context, body, warnings), _render_text(title, context, warnings)

    async def _prepare_render_job(self, agency_id: str, payload: DocumentRenderJobCreate, user: dict) -> tuple[DocumentRenderJob, dict[str, Any] | None]:
        template = await self._select_template(agency_id, payload)
        context = await self._build_context(agency_id, payload)
        warnings = []
        if context is None:
            context = await self.contexts.build_mixed_context(agency_id, payload.source_context_ids_json or {})
            warnings.append({"code": "source_context_missing", "message": "Primary source context was not found; rendered from available manual context only."})
        if payload.render_format == "pdf":
            warnings.append({"code": "pdf_not_required", "message": "PDF export is not required in Phase 36.6; HTML preview was rendered."})
        context.setdefault("warnings_json", []).extend(warnings)
        title, rendered_html, rendered_text = self._render(str(payload.document_type), context, template)
        job = DocumentRenderJob(
            agency_id=agency_id,
            template_id=(template or {}).get("id") or payload.template_id,
            template_key=(template or {}).get("template_key") or payload.template_key,
            document_type=payload.document_type,
            source_context_type=payload.source_context_type,
            source_context_id=payload.source_context_id,
            source_context_ids_json=payload.source_context_ids_json,
            render_status=DocumentRenderStatus.RENDERED,
            render_format=payload.render_format,
            render_context_json=context,
            rendered_html=rendered_html,
            rendered_text=rendered_text,
            warnings_json=context.get("warnings_json") or [],
            internal_notes=payload.internal_notes,
            created_by_user_id=user.get("id"),
        )
        return job, template

    async def render_document(self, agency_id: str, payload: DocumentRenderJobCreate, user: dict) -> dict[str, Any]:
        job, template = await self._prepare_render_job(agency_id, payload, user)
        created = await self.db.collection("document_render_jobs").insert_one(job.model_dump(mode="json"))
        return {"render_job": created, "template": template, "live_delivery_disabled": True, "pdf_export_required": False}

    async def rerender_document(self, agency_id: str, render_job_id: str, user: dict) -> dict[str, Any] | None:
        current = await self.get_render_job(agency_id, render_job_id)
        if not current:
            return None
        payload = DocumentRenderJobCreate(
            template_id=current.get("template_id"),
            template_key=current.get("template_key"),
            document_type=current["document_type"],
            source_context_type=current["source_context_type"],
            source_context_id=current.get("source_context_id"),
            source_context_ids_json=current.get("source_context_ids_json") or {},
            render_format=current.get("render_format") or "html",
            render_context_json=current.get("manual_context_json") or {},
            internal_notes=current.get("internal_notes"),
        )
        rendered_job, _template = await self._prepare_render_job(agency_id, payload, user)
        rendered = rendered_job.model_dump(mode="json")
        updated = await self.db.collection("document_render_jobs").update_one(
            {"agency_id": agency_id, "id": render_job_id},
            {
                "template_id": rendered.get("template_id"),
                "template_key": rendered.get("template_key"),
                "render_status": "rendered",
                "render_context_json": rendered.get("render_context_json") or {},
                "rendered_html": rendered.get("rendered_html"),
                "rendered_text": rendered.get("rendered_text"),
                "warnings_json": rendered.get("warnings_json") or [],
                "error_json": {},
                "created_by_user_id": user.get("id"),
            },
        )
        return {"render_job": updated, "live_delivery_disabled": True, "pdf_export_required": False}

    async def get_render_job(self, agency_id: str, render_job_id: str) -> dict[str, Any] | None:
        return await self.db.collection("document_render_jobs").find_one({"agency_id": agency_id, "id": render_job_id})

    async def list_render_jobs(self, agency_id: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {"agency_id": agency_id}
        for key in ["document_type", "source_context_type", "source_context_id", "render_status"]:
            if (filters or {}).get(key):
                query[key] = filters[key]
        items = await self.db.collection("document_render_jobs").find_many(query)
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def create_document_package(self, agency_id: str, payload: DocumentPackageCreate, user: dict) -> dict[str, Any]:
        jobs = []
        for job_id in payload.document_render_job_ids:
            job = await self.get_render_job(agency_id, job_id)
            if job:
                jobs.append(job)
        package = DocumentPackage(
            agency_id=agency_id,
            package_type=payload.package_type,
            title=payload.title,
            source_context_type=payload.source_context_type,
            source_context_id=payload.source_context_id,
            source_context_ids_json=payload.source_context_ids_json,
            document_render_job_ids=[item["id"] for item in jobs],
            status=DocumentPackageStatus.READY if jobs else DocumentPackageStatus.DRAFT,
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("document_packages").insert_one(package.model_dump(mode="json"))
        return {"package": created, "items": jobs}

    async def get_document_package(self, agency_id: str, package_id: str) -> dict[str, Any] | None:
        package = await self.db.collection("document_packages").find_one({"agency_id": agency_id, "id": package_id})
        if not package:
            return None
        jobs = []
        for job_id in package.get("document_render_job_ids") or []:
            job = await self.get_render_job(agency_id, job_id)
            if job:
                jobs.append(job)
        return {"package": package, "items": jobs}

    async def list_document_packages(self, agency_id: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {"agency_id": agency_id}
        for key in ["package_type", "source_context_type", "source_context_id", "status"]:
            if (filters or {}).get(key):
                query[key] = filters[key]
        items = await self.db.collection("document_packages").find_many(query)
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def create_share_record(self, agency_id: str, payload: DocumentShareRecordCreate, user: dict) -> dict[str, Any]:
        share = DocumentShareRecord(
            agency_id=agency_id,
            document_render_job_id=payload.document_render_job_id,
            document_package_id=payload.document_package_id,
            share_status=payload.share_status,
            share_channel=payload.share_channel,
            recipient_snapshot_json=payload.recipient_snapshot_json,
            expires_at=payload.expires_at,
            sent_at=datetime.now(timezone.utc) if payload.share_status == DocumentShareStatus.SENT_MANUALLY else None,
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("document_share_records").insert_one(share.model_dump(mode="json"))
        return {"share_record": created, "live_delivery_disabled": True, "public_portal_sharing_disabled": True}
