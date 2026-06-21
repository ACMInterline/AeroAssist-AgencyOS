from datetime import datetime, timezone
from html import escape
from typing import Any

from fastapi import HTTPException, status

from database import Database


LABELS = {
    "offer_summary": "Agency-generated offer summary",
    "booking_confirmation": "Agency-generated booking confirmation",
    "itinerary_summary": "Agency-generated itinerary summary",
    "ticket_receipt_summary": "Agency-generated ticket receipt summary",
    "emd_receipt_summary": "Agency-generated EMD receipt summary",
    "invoice_summary": "Agency invoice summary",
    "service_summary": "Agency-generated service summary",
}


def text(value: Any, fallback: str = "") -> str:
    if value is None or value == "":
        return fallback
    return escape(str(value))


def money(amount: Any, currency: str | None = None) -> str:
    try:
        rendered = f"{float(amount):.2f}"
    except (TypeError, ValueError):
        rendered = "0.00"
    return f"{rendered} {text(currency or '')}".strip()


def brand_snapshot(workspace: dict | None, agency: dict | None) -> dict:
    workspace = workspace or {}
    agency = agency or {}
    return {
        "brand_name": workspace.get("brand_name") or agency.get("name") or "Agency",
        "logo_url": workspace.get("logo_url"),
        "primary_color": workspace.get("primary_color") or "#2563eb",
        "secondary_color": workspace.get("secondary_color") or "#0f172a",
        "font_family": workspace.get("font_family") or "Inter",
        "agency_name": agency.get("name"),
    }


def shell(label: str, title: str, brand: dict, body: str, disclaimer: str) -> str:
    primary = text(brand.get("primary_color") or "#2563eb")
    secondary = text(brand.get("secondary_color") or "#0f172a")
    font = text(brand.get("font_family") or "Inter")
    brand_name = text(brand.get("brand_name") or "Agency")
    logo = brand.get("logo_url")
    logo_html = f'<img src="{text(logo)}" alt="{brand_name}" style="max-height:48px;max-width:180px;object-fit:contain" />' if logo else f'<div style="font-size:22px;font-weight:800;color:{primary}">{brand_name}</div>'
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{text(title)}</title>
</head>
<body style="margin:0;background:#f8fafc;color:#0f172a;font-family:{font}, Arial, sans-serif">
  <main style="max-width:920px;margin:0 auto;background:white;min-height:100vh">
    <header style="border-bottom:4px solid {primary};padding:28px 32px 22px">
      <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;flex-wrap:wrap">
        <div>{logo_html}<p style="margin:10px 0 0;color:#64748b;font-size:13px">{text(label)}</p></div>
        <div style="text-align:right;color:{secondary};font-size:13px">
          <strong>Preview only</strong><br />HTML document<br />Snapshot captured at render time
        </div>
      </div>
      <h1 style="margin:24px 0 0;font-size:28px;line-height:1.2;color:{secondary}">{text(title)}</h1>
    </header>
    <section style="padding:28px 32px">{body}</section>
    <footer style="border-top:1px solid #e2e8f0;padding:18px 32px;color:#64748b;font-size:12px;line-height:1.5">
      {text(disclaimer)}
    </footer>
  </main>
</body>
</html>"""


def section(title: str, content: str) -> str:
    return f'<section style="margin:0 0 24px"><h2 style="margin:0 0 10px;font-size:15px;text-transform:uppercase;letter-spacing:.04em;color:#334155">{text(title)}</h2>{content}</section>'


def table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return '<p style="margin:0;color:#64748b">No records available.</p>'
    head = "".join(f'<th style="text-align:left;border-bottom:1px solid #cbd5e1;padding:9px;background:#f8fafc">{text(header)}</th>' for header in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f'<td style="border-bottom:1px solid #e2e8f0;padding:9px;vertical-align:top">{text(value, "n/a")}</td>' for value in row) + "</tr>"
    return f'<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;font-size:13px"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def key_values(rows: list[tuple[str, Any]]) -> str:
    return '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px">' + "".join(
        f'<div style="border:1px solid #e2e8f0;border-radius:8px;padding:10px"><div style="font-size:12px;color:#64748b">{text(label)}</div><div style="margin-top:4px;font-weight:700">{text(value, "n/a")}</div></div>'
        for label, value in rows
    ) + "</div>"


async def agency_brand(db: Database, agency_id: str) -> dict:
    agency = await db.collection("agencies").find_one({"id": agency_id})
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": agency_id})
    return brand_snapshot(workspace, agency)


async def active_template(db: Database, agency_id: str, document_type: str, template_id: str | None = None) -> dict | None:
    if template_id:
        template = await db.collection("document_templates").find_one({"id": template_id})
        if not template or template.get("agency_id") not in {None, agency_id}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document template not found.")
        return template
    agency_template = await db.collection("document_templates").find_one({"agency_id": agency_id, "document_type": document_type, "status": "active"})
    if agency_template:
        return agency_template
    return await db.collection("document_templates").find_one({"agency_id": None, "document_type": document_type, "status": "active"})


async def offer_snapshot(db: Database, agency_id: str, offer_id: str) -> dict:
    offer = await db.collection("offers").find_one({"agency_id": agency_id, "id": offer_id})
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return {
        "offer": offer,
        "client": await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": offer["client_id"]}),
        "passengers": await db.collection("offer_passengers").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"}),
        "routes": await db.collection("offer_route_alternatives").find_many({"agency_id": agency_id, "offer_id": offer_id}),
        "segments": await db.collection("offer_segments").find_many({"agency_id": agency_id, "offer_id": offer_id}),
        "fare_options": await db.collection("offer_fare_options").find_many({"agency_id": agency_id, "offer_id": offer_id}),
        "price_lines": await db.collection("offer_price_lines").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"}),
        "service_checks": await db.collection("offer_service_checks").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"}),
    }


async def booking_snapshot(db: Database, agency_id: str, booking_id: str) -> dict:
    booking = await db.collection("bookings").find_one({"agency_id": agency_id, "id": booking_id})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    invoices = await db.collection("invoices").find_many({"agency_id": agency_id, "booking_id": booking_id})
    payments = []
    for invoice in invoices:
        payments.extend(await db.collection("payment_records").find_many({"agency_id": agency_id, "invoice_id": invoice["id"]}))
    return {
        "booking": booking,
        "client": await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": booking["client_id"]}),
        "passengers": await db.collection("booking_passengers").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "segments": await db.collection("booking_segments").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "tickets": await db.collection("ticket_records").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "emds": await db.collection("emd_records").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "invoices": invoices,
        "payments": payments,
    }


async def invoice_snapshot(db: Database, agency_id: str, invoice_id: str) -> dict:
    invoice = await db.collection("invoices").find_one({"agency_id": agency_id, "id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return {
        "invoice": invoice,
        "client": await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": invoice["client_id"]}),
        "booking": await db.collection("bookings").find_one({"agency_id": agency_id, "id": invoice.get("booking_id")}) if invoice.get("booking_id") else None,
        "line_items": await db.collection("invoice_line_items").find_many({"agency_id": agency_id, "invoice_id": invoice_id}),
        "payments": await db.collection("payment_records").find_many({"agency_id": agency_id, "invoice_id": invoice_id}),
    }


async def ticket_snapshot(db: Database, agency_id: str, ticket_id: str) -> dict:
    ticket = await db.collection("ticket_records").find_one({"agency_id": agency_id, "id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    booking = await booking_snapshot(db, agency_id, ticket["booking_id"])
    passenger = next((item for item in booking["passengers"] if item.get("passenger_id") == ticket.get("passenger_id") or item.get("id") == ticket.get("booking_passenger_id")), None)
    return {**booking, "ticket": ticket, "passenger": passenger}


async def emd_snapshot(db: Database, agency_id: str, emd_id: str) -> dict:
    emd = await db.collection("emd_records").find_one({"agency_id": agency_id, "id": emd_id})
    if not emd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EMD not found.")
    booking = await booking_snapshot(db, agency_id, emd["booking_id"])
    passenger = next((item for item in booking["passengers"] if item.get("passenger_id") == emd.get("passenger_id") or item.get("id") == emd.get("booking_passenger_id")), None)
    ticket = await db.collection("ticket_records").find_one({"agency_id": agency_id, "id": emd.get("ticket_id")}) if emd.get("ticket_id") else None
    return {**booking, "emd": emd, "passenger": passenger, "ticket": ticket}


def render_offer(snapshot: dict, brand: dict) -> tuple[str, str]:
    offer = snapshot["offer"]
    client = snapshot.get("client") or {}
    title = f"Offer summary {offer.get('offer_reference')}"
    rows = [
        ("Client", client.get("display_name")),
        ("Offer", offer.get("offer_reference")),
        ("Status", offer.get("status")),
        ("Valid until", offer.get("valid_until")),
        ("Currency", offer.get("currency")),
    ]
    body = section("Overview", key_values(rows))
    body += section("Passengers", table(["Passenger", "Type", "Role"], [[p.get("snapshot_display_name"), p.get("snapshot_passenger_type"), p.get("role_in_offer")] for p in snapshot["passengers"]]))
    body += section("Route alternatives", table(["Label", "Title", "Carrier", "Route", "Schedule"], [[r.get("label"), r.get("title"), r.get("carrier_summary"), r.get("route_summary"), r.get("schedule_summary")] for r in snapshot["routes"]]))
    body += section("Segments", table(["Airline", "Flight", "From", "To", "Cabin"], [[s.get("marketing_airline_code"), s.get("flight_number"), s.get("origin_airport_code"), s.get("destination_airport_code"), s.get("cabin")] for s in snapshot["segments"]]))
    body += section("Fare options", table(["Label", "Fare family", "Baggage", "Total"], [[f.get("label"), f.get("fare_family_code") or f.get("branded_fare_name"), f.get("baggage_summary"), money(f.get("total_amount"), f.get("currency"))] for f in snapshot["fare_options"]]))
    body += section("Service checks", table(["Code", "Service", "Support", "Client summary"], [[s.get("service_code"), s.get("service_name"), s.get("support_status"), s.get("client_visible_summary")] for s in snapshot["service_checks"]]))
    if offer.get("client_visible_terms"):
        body += section("Terms", f'<p style="line-height:1.6">{text(offer.get("client_visible_terms"))}</p>')
    return title, shell(LABELS["offer_summary"], title, brand, body, "Prices and schedules are subject to verification until ticketed. This is not an airline-issued document.")


def render_booking(snapshot: dict, brand: dict, document_type: str) -> tuple[str, str]:
    booking = snapshot["booking"]
    client = snapshot.get("client") or {}
    title = ("Itinerary summary" if document_type == "itinerary_summary" else "Booking confirmation") + f" {booking.get('booking_reference')}"
    body = section("Overview", key_values([("Client", client.get("display_name")), ("Booking", booking.get("booking_reference")), ("PNR", booking.get("pnr")), ("Status", booking.get("status")), ("Channel", booking.get("booking_channel"))]))
    body += section("Passengers", table(["Passenger", "Type", "Ticket status"], [[p.get("snapshot_display_name"), p.get("snapshot_passenger_type"), p.get("ticket_status")] for p in snapshot["passengers"]]))
    body += section("Flight segments", table(["Airline", "Flight", "From", "To", "Departure", "Arrival", "Cabin", "Baggage"], [[s.get("marketing_airline_code"), s.get("flight_number"), s.get("origin_airport_code"), s.get("destination_airport_code"), s.get("departure_datetime"), s.get("arrival_datetime"), s.get("cabin"), s.get("baggage_summary")] for s in snapshot["segments"]]))
    if booking.get("client_visible_notes"):
        body += section("Notes", f'<p style="line-height:1.6">{text(booking.get("client_visible_notes"))}</p>')
    return title, shell(LABELS[document_type], title, brand, body, "Agency-generated summary from stored booking data. Verify schedule and service status before travel.")


def render_ticket(snapshot: dict, brand: dict) -> tuple[str, str]:
    ticket = snapshot["ticket"]
    passenger = snapshot.get("passenger") or {}
    title = f"Ticket receipt summary {ticket.get('ticket_number')}"
    body = section("Ticket", key_values([("Ticket number", ticket.get("ticket_number")), ("Passenger", passenger.get("snapshot_display_name")), ("Validating carrier", ticket.get("validating_airline_code")), ("Issue date", ticket.get("issue_date")), ("Status", ticket.get("status")), ("Fare", money(ticket.get("base_fare_amount"), ticket.get("currency"))), ("Taxes", money(ticket.get("taxes_amount"), ticket.get("currency"))), ("Total", money(ticket.get("total_amount"), ticket.get("currency")))]))
    body += section("Context", key_values([("Booking", snapshot["booking"].get("booking_reference")), ("PNR", snapshot["booking"].get("pnr")), ("Client", (snapshot.get("client") or {}).get("display_name"))]))
    return title, shell(LABELS["ticket_receipt_summary"], title, brand, body, "Agency-generated ticket receipt summary. It is not an airline-issued document unless a ticket number is present.")


def render_emd(snapshot: dict, brand: dict) -> tuple[str, str]:
    emd = snapshot["emd"]
    passenger = snapshot.get("passenger") or {}
    ticket = snapshot.get("ticket") or {}
    title = f"EMD receipt summary {emd.get('emd_number')}"
    body = section("EMD", key_values([("EMD number", emd.get("emd_number")), ("Passenger", passenger.get("snapshot_display_name")), ("Service", f"{emd.get('service_code')} {emd.get('service_name')}"), ("RFIC/RFISC", f"{emd.get('rfic_code') or 'n/a'} / {emd.get('rfisc_code') or 'n/a'}"), ("EMD type", emd.get("emd_type")), ("Amount", money(emd.get("amount"), emd.get("currency"))), ("Status", emd.get("status")), ("Linked ticket", ticket.get("ticket_number"))]))
    return title, shell(LABELS["emd_receipt_summary"], title, brand, body, "Agency-generated EMD receipt summary. It is not an airline-issued document unless an EMD number is present.")


def render_invoice(snapshot: dict, brand: dict) -> tuple[str, str]:
    invoice = snapshot["invoice"]
    client = snapshot.get("client") or {}
    title = f"Invoice summary {invoice.get('invoice_number')}"
    body = section("Invoice", key_values([("Invoice", invoice.get("invoice_number")), ("Client", client.get("display_name")), ("Status", invoice.get("status")), ("Issue date", invoice.get("issue_date")), ("Due date", invoice.get("due_date"))]))
    body += section("Line items", table(["Type", "Description", "Qty", "Amount"], [[l.get("line_type"), l.get("description"), l.get("quantity"), money(l.get("total_amount"), l.get("currency"))] for l in snapshot["line_items"] if l.get("status") == "active"]))
    body += section("Totals", key_values([("Subtotal", money(invoice.get("subtotal_amount"), invoice.get("currency"))), ("Tax lines", money(invoice.get("tax_amount"), invoice.get("currency"))), ("Total", money(invoice.get("total_amount"), invoice.get("currency"))), ("Paid", money(invoice.get("paid_amount"), invoice.get("currency"))), ("Due", money(invoice.get("due_amount"), invoice.get("currency")))]))
    body += section("Payments", table(["Status", "Method", "Amount", "Reconciliation"], [[p.get("status"), p.get("method"), money(p.get("amount"), p.get("currency")), p.get("reconciliation_status")] for p in snapshot["payments"]]))
    return title, shell(LABELS["invoice_summary"], title, brand, body, "Agency invoice summary from manually tracked records. This is not fiscal/legal compliance output.")


async def render_document_payload(db: Database, agency_id: str, source_entity_type: str, source_entity_id: str, document_type: str, template_id: str | None, language: str) -> dict:
    brand = await agency_brand(db, agency_id)
    template = await active_template(db, agency_id, document_type, template_id)
    if source_entity_type == "offer":
        snapshot = await offer_snapshot(db, agency_id, source_entity_id)
        title, html = render_offer(snapshot, brand)
        client_id = snapshot["offer"].get("client_id")
        passenger_id = None
    elif source_entity_type == "booking":
        snapshot = await booking_snapshot(db, agency_id, source_entity_id)
        title, html = render_booking(snapshot, brand, document_type)
        client_id = snapshot["booking"].get("client_id")
        passenger_id = None
    elif source_entity_type == "invoice":
        snapshot = await invoice_snapshot(db, agency_id, source_entity_id)
        title, html = render_invoice(snapshot, brand)
        client_id = snapshot["invoice"].get("client_id")
        passenger_id = None
    elif source_entity_type == "ticket":
        snapshot = await ticket_snapshot(db, agency_id, source_entity_id)
        title, html = render_ticket(snapshot, brand)
        client_id = snapshot["booking"].get("client_id")
        passenger_id = snapshot["ticket"].get("passenger_id")
    elif source_entity_type == "emd":
        snapshot = await emd_snapshot(db, agency_id, source_entity_id)
        title, html = render_emd(snapshot, brand)
        client_id = snapshot["booking"].get("client_id")
        passenger_id = snapshot["emd"].get("passenger_id")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported document source.")
    snapshot["snapshot_reason"] = "document_generated"
    snapshot["source_record_type"] = source_entity_type
    snapshot["source_record_id"] = source_entity_id
    snapshot["rendered_at"] = datetime.now(timezone.utc).isoformat()
    return {
        "document_type": document_type,
        "template_id": template.get("id") if template else None,
        "source_entity_type": source_entity_type,
        "source_entity_id": source_entity_id,
        "client_id": client_id,
        "passenger_id": passenger_id,
        "title": title,
        "language": language,
        "brand_snapshot": brand,
        "source_snapshot": snapshot,
        "rendered_html": html,
    }
