import { useEffect, useState } from "react"
import BookingStatusBadge from "../../components/BookingStatusBadge"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function BookingDetailPage({ bookingId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ passenger_id: "", origin_airport_code: "", destination_airport_code: "", marketing_airline_code: "", flight_number: "", ticket_number: "", emd_number: "", service_code: "BAG", service_name: "Checked baggage", invoice_id: "", invoice_line_description: "", invoice_line_amount: 0, payment_amount: 0 })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/bookings/${bookingId}`)
    const passengers = await apiGet(`/api/agencies/${context.agency.id}/passengers`)
    const invoices = await apiGet(`/api/agencies/${context.agency.id}/invoices`)
    setState({ ...context, ...detail, agencyPassengers: passengers.items, allInvoices: invoices.items })
    setForm((current) => ({ ...current, passenger_id: passengers.items[0]?.id || "", invoice_id: detail.invoices[0]?.id || "", payment_amount: detail.booking.amount_due || 0 }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [bookingId])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function updateStatus(status) {
    await apiPut(`/api/agencies/${state.agency.id}/bookings/${bookingId}`, { status })
    await load()
  }

  async function addPassenger(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/bookings/${bookingId}/passengers`, { passenger_id: form.passenger_id, is_primary_traveler: state.passengers.length === 0 })
    await load()
  }

  async function addSegment(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/bookings/${bookingId}/segments`, {
      sequence: state.segments.length + 1,
      marketing_airline_code: form.marketing_airline_code,
      flight_number: form.flight_number,
      origin_airport_code: form.origin_airport_code,
      destination_airport_code: form.destination_airport_code,
      segment_status: "booked",
    })
    setForm((current) => ({ ...current, origin_airport_code: "", destination_airport_code: "", marketing_airline_code: "", flight_number: "" }))
    await load()
  }

  async function addTicket(event) {
    event.preventDefault()
    const passenger = state.passengers[0]
    await apiPost(`/api/agencies/${state.agency.id}/bookings/${bookingId}/tickets`, {
      booking_passenger_id: passenger?.id || null,
      passenger_id: passenger?.passenger_id || null,
      ticket_number: form.ticket_number,
      validating_airline_code: state.booking.validating_airline_code || "YY",
      status: "issued",
      currency: state.booking.currency,
    })
    setForm((current) => ({ ...current, ticket_number: "" }))
    await load()
  }

  async function addEmd(event) {
    event.preventDefault()
    const passenger = state.passengers[0]
    await apiPost(`/api/agencies/${state.agency.id}/bookings/${bookingId}/emds`, {
      booking_passenger_id: passenger?.id || null,
      passenger_id: passenger?.passenger_id || null,
      ticket_id: state.tickets[0]?.id || null,
      service_code: form.service_code,
      service_name: form.service_name,
      emd_number: form.emd_number,
      emd_type: "unknown",
      status: "issued",
      amount: 0,
      currency: state.booking.currency,
    })
    setForm((current) => ({ ...current, emd_number: "" }))
    await load()
  }

  async function createInvoice() {
    const result = await apiPost(`/api/agencies/${state.agency.id}/invoices`, { client_id: state.booking.client_id, booking_id: bookingId, offer_id: state.booking.offer_id, currency: state.booking.currency })
    setForm((current) => ({ ...current, invoice_id: result.invoice.id }))
    await load()
  }

  async function addInvoiceLine(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/invoices/${form.invoice_id}/line-items`, {
      booking_id: bookingId,
      line_type: "other",
      description: form.invoice_line_description,
      quantity: 1,
      unit_amount: Number(form.invoice_line_amount),
      currency: state.booking.currency,
      client_visible: true,
    })
    setForm((current) => ({ ...current, invoice_line_description: "", invoice_line_amount: 0 }))
    await load()
  }

  async function addPayment(event) {
    event.preventDefault()
    const invoice = state.invoices.find((item) => item.id === form.invoice_id)
    if (!invoice) return
    await apiPost(`/api/agencies/${state.agency.id}/payments`, {
      invoice_id: invoice.id,
      booking_id: bookingId,
      client_id: state.booking.client_id,
      status: "received",
      method: "bank_transfer",
      amount: Number(form.payment_amount),
      currency: invoice.currency,
      reconciliation_status: "unreconciled",
      internal_notes: "Payment received manually. No payment gateway connected.",
    })
    await load()
  }

  async function renderBookingDocument(documentType = "booking_confirmation") {
    const result = await apiPost(`/api/agencies/${state.agency.id}/bookings/${bookingId}/render-document`, { document_type: documentType })
    window.location.href = `/agency/documents/${result.document.id}`
  }

  async function renderTicketDocument(ticketId) {
    const result = await apiPost(`/api/agencies/${state.agency.id}/tickets/${ticketId}/render-document`, { document_type: "ticket_receipt_summary" })
    window.location.href = `/agency/documents/${result.document.id}`
  }

  async function renderEmdDocument(emdId) {
    const result = await apiPost(`/api/agencies/${state.agency.id}/emds/${emdId}/render-document`, { document_type: "emd_receipt_summary" })
    window.location.href = `/agency/documents/${result.document.id}`
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href="/agency/bookings">Back to bookings</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.booking.booking_reference}</p>
              <h2 className="text-2xl font-semibold text-slate-950">{state.client.display_name}</h2>
              <p className="mt-1 text-sm text-slate-600">Manual tracking only · PNR {state.booking.pnr || "not set"} · No ticketing integration connected.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <BookingStatusBadge status={state.booking.status} />
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => renderBookingDocument("booking_confirmation")}>Render confirmation</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => renderBookingDocument("itinerary_summary")}>Render itinerary</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => updateStatus("reserved")}>Reserved</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={() => updateStatus("ticketed")}>Ticketed</button>
              <button className="rounded-md border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700" onClick={() => updateStatus("cancelled")}>Cancel</button>
            </div>
          </div>
          <section className="grid gap-4 lg:grid-cols-3">
            <Info title="Overview" rows={[["Client", state.client.display_name], ["Channel", state.booking.booking_channel.replaceAll("_", " ")], ["Currency", state.booking.currency], ["Offer", state.booking.offer_id ? "linked" : "none"]]} />
            <Info title="Money" rows={[["Total", `${state.booking.total_amount} ${state.booking.currency}`], ["Paid", `${state.booking.amount_paid} ${state.booking.currency}`], ["Due", `${state.booking.amount_due} ${state.booking.currency}`]]} />
            <Info title="Notes" rows={[["Client", state.booking.client_visible_notes || "None"], ["Internal", state.booking.internal_notes || "None"]]} />
          </section>
          <AirlineIntelLinkPanel
            title="Search servicing/EMD/ticketing notes"
            airlineCode={state.booking.validating_airline_code || state.segments.find((segment) => segment.marketing_airline_code)?.marketing_airline_code}
            serviceCodes={state.emds.map((emd) => emd.service_code)}
          />
          <Panel title="Passengers">
            <form className="flex gap-2" onSubmit={addPassenger}>
              <select className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.passenger_id} onChange={(event) => setField("passenger_id", event.target.value)}>
                {state.agencyPassengers.map((passenger) => <option key={passenger.id} value={passenger.id}>{passenger.display_name}</option>)}
              </select>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Add</button>
            </form>
            <List items={state.passengers} empty="No booking passengers yet" render={(item) => <span>{item.snapshot_display_name} · {item.snapshot_passenger_type} · <StatusBadge status={item.ticket_status} /></span>} />
          </Panel>
          <Panel title="Segments">
            <form className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_1fr_auto]" onSubmit={addSegment}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline" value={form.marketing_airline_code} onChange={(event) => setField("marketing_airline_code", event.target.value)} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Flight" value={form.flight_number} onChange={(event) => setField("flight_number", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Origin" value={form.origin_airport_code} onChange={(event) => setField("origin_airport_code", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Destination" value={form.destination_airport_code} onChange={(event) => setField("destination_airport_code", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Add</button>
            </form>
            <List items={state.segments} empty="No booking segments yet" render={(item) => `${item.marketing_airline_code}${item.flight_number || ""} ${item.origin_airport_code}-${item.destination_airport_code} · ${item.segment_status.replaceAll("_", " ")}`} />
          </Panel>
          <Panel title="Tickets">
            <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={addTicket}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Ticket number issued externally" value={form.ticket_number} onChange={(event) => setField("ticket_number", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Record ticket</button>
            </form>
            <List items={state.tickets} empty="No tickets recorded" render={(item) => <span className="flex flex-wrap items-center justify-between gap-2"><span>{item.ticket_number} · {item.validating_airline_code} · {item.status.replaceAll("_", " ")} · {item.total_amount} {item.currency}</span><button className="text-blue-700" onClick={() => renderTicketDocument(item.id)}>Render receipt</button></span>} />
          </Panel>
          <Panel title="EMDs">
            <form className="grid gap-3 md:grid-cols-[100px_1fr_1fr_auto]" onSubmit={addEmd}>
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.service_code} onChange={(event) => setField("service_code", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.service_name} onChange={(event) => setField("service_name", event.target.value)} />
              <input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="EMD number issued externally" value={form.emd_number} onChange={(event) => setField("emd_number", event.target.value)} />
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Record EMD</button>
            </form>
            <List items={state.emds} empty="No EMD records" render={(item) => <span className="flex flex-wrap items-center justify-between gap-2"><span>{item.emd_number} · {item.service_code} {item.service_name} · {item.status.replaceAll("_", " ")}</span><button className="text-blue-700" onClick={() => renderEmdDocument(item.id)}>Render receipt</button></span>} />
          </Panel>
          <Panel title="Invoice / Payments">
            <div className="flex flex-wrap items-center gap-2">
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium" onClick={createInvoice}>Create invoice</button>
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.invoice_id} onChange={(event) => setField("invoice_id", event.target.value)}>
                <option value="">Select invoice</option>
                {state.invoices.map((invoice) => <option key={invoice.id} value={invoice.id}>{invoice.invoice_number} · {invoice.status}</option>)}
              </select>
            </div>
            <form className="mt-4 grid gap-3 md:grid-cols-[1fr_120px_auto]" onSubmit={addInvoiceLine}>
              <input required disabled={!form.invoice_id} className="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" placeholder="Line description" value={form.invoice_line_description} onChange={(event) => setField("invoice_line_description", event.target.value)} />
              <input type="number" disabled={!form.invoice_id} className="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" value={form.invoice_line_amount} onChange={(event) => setField("invoice_line_amount", event.target.value)} />
              <button disabled={!form.invoice_id} className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:bg-slate-300">Add line</button>
            </form>
            <form className="mt-3 grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={addPayment}>
              <input type="number" disabled={!form.invoice_id} className="rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100" value={form.payment_amount} onChange={(event) => setField("payment_amount", event.target.value)} />
              <button disabled={!form.invoice_id} className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:bg-slate-300">Record received payment</button>
            </form>
            <List items={state.invoices} empty="No invoices linked" render={(item) => <a className="text-blue-700" href={`/agency/invoices/${item.id}`}>{item.invoice_number} · {item.total_amount} {item.currency} · due {item.due_amount}</a>} />
            <List items={state.payments} empty="No payments linked" render={(item) => `${item.amount} ${item.currency} · ${item.status.replaceAll("_", " ")} · ${item.reconciliation_status.replaceAll("_", " ")}`} />
          </Panel>
          <Panel title="Timeline">
            <List items={state.timeline} empty="No timeline events yet" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} />
          </Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function List({ items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body="Add manual tracking records when available." />
  return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}

function Info({ title, rows }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <dl className="mt-4 space-y-3 text-sm">
        {rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value}</dd></div>)}
      </dl>
    </section>
  )
}

function AirlineIntelLinkPanel({ title, airlineCode, serviceCodes }) {
  const primaryService = serviceCodes.find(Boolean)
  const query = new URLSearchParams()
  if (airlineCode) query.set("airline", airlineCode)
  if (primaryService) query.set("service_code", primaryService)
  return (
    <section className="rounded-lg border border-emerald-100 bg-emerald-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-emerald-950">{title}</h3>
          <p className="mt-1 text-sm text-emerald-800">Manual servicing lookup only. No ticketing, EMD issuance, or pricing automation is connected.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a className="rounded-md bg-emerald-700 px-3 py-2 text-sm font-semibold text-white" href={`/agency/airline-intelligence?${query.toString()}`}>Open search</a>
          {["PETC", "AVIH", "WCHR", "WCHS", "WCHC", "UMNR"].map((code) => <a className="rounded-md border border-emerald-200 bg-white px-2 py-1 text-xs font-semibold text-emerald-800" href={`/agency/airline-intelligence?service_code=${code}`} key={code}>{code}</a>)}
        </div>
      </div>
    </section>
  )
}
