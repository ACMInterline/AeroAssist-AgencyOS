import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_issue", "issued", "voided", "refunded", "exchanged", "cancelled"]

export default function TicketDetailPage({ ticketRecordId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ ticket_number: "", validating_carrier: "", issue_status: "draft", currency: "EUR", base_fare_amount: "", taxes_amount: "", total_amount: "", internal_notes: "" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/tickets/${ticketRecordId}`)
    setState({ ...context, ...detail })
    setForm({
      ticket_number: detail.ticket?.ticket_number || "",
      validating_carrier: detail.ticket?.validating_carrier || detail.ticket?.validating_airline_code || "",
      issue_status: detail.ticket?.issue_status || detail.ticket?.status || "draft",
      currency: detail.ticket?.currency || "EUR",
      base_fare_amount: amountValue(detail.ticket?.base_fare_amount),
      taxes_amount: amountValue(detail.ticket?.taxes_amount),
      total_amount: amountValue(detail.ticket?.total_amount),
      internal_notes: detail.ticket?.internal_notes || "",
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [ticketRecordId])

  async function save(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await apiPut(`/api/agencies/${state.agency.id}/tickets/${ticketRecordId}`, {
        ticket_number: form.ticket_number || null,
        validating_carrier: form.validating_carrier || null,
        issue_status: form.issue_status,
        currency: form.currency || null,
        base_fare_amount: numberOrNull(form.base_fare_amount),
        taxes_amount: numberOrNull(form.taxes_amount),
        total_amount: numberOrNull(form.total_amount),
        internal_notes: form.internal_notes || null,
      })
      setMessage("Ticket mirror updated.")
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const ticket = state?.ticket
  const passenger = ticket?.passenger_snapshot_json || {}

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <a className="text-sm font-medium text-blue-700" href="/agency/tickets-emds">Back to Tickets & EMDs</a>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{label(ticket?.issue_status || ticket?.status)} · {label(ticket?.issuing_provider)}</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{ticket?.ticket_number || "Draft ticket mirror"}</h2>
                <p className="mt-1 text-sm text-slate-600">Provider ticketing is disabled in this phase.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {ticket?.booking_workspace_id ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/booking-workspaces/${ticket.booking_workspace_id}`}>Booking workspace</a> : null}
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-400" type="button" disabled>Issue ticket</button>
              </div>
            </div>
          </div>

          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}
          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div> : null}

          <section className="grid gap-4 lg:grid-cols-4">
            <Metric label="Passenger" value={passengerName(passenger, ticket?.passenger_id)} />
            <Metric label="PNR" value={state?.booking_record_summary?.pnr_locator || "Pending"} />
            <Metric label="Coupons" value={state?.coupons?.length || 0} />
            <Metric label="Amount" value={money(ticket?.total_amount, ticket?.currency)} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <Panel title="Manual Update">
              <form className="space-y-3" onSubmit={save}>
                <Field label="Ticket number" value={form.ticket_number} onChange={(value) => setForm({ ...form, ticket_number: value })} />
                <Field label="Validating carrier" value={form.validating_carrier} onChange={(value) => setForm({ ...form, validating_carrier: value.toUpperCase() })} />
                <Select label="Issue status" value={form.issue_status} options={statuses} onChange={(value) => setForm({ ...form, issue_status: value })} />
                <Field label="Currency" value={form.currency} onChange={(value) => setForm({ ...form, currency: value.toUpperCase() })} />
                <Field label="Base fare" value={form.base_fare_amount} onChange={(value) => setForm({ ...form, base_fare_amount: value })} />
                <Field label="Taxes" value={form.taxes_amount} onChange={(value) => setForm({ ...form, taxes_amount: value })} />
                <Field label="Total" value={form.total_amount} onChange={(value) => setForm({ ...form, total_amount: value })} />
                <Textarea label="Internal notes" value={form.internal_notes} onChange={(value) => setForm({ ...form, internal_notes: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="submit">Save ticket mirror</button>
              </form>
            </Panel>

            <div className="space-y-4">
              <Panel title="Coupons by Segment">
                <SnapshotList items={state?.coupons} render={(item) => `${item.coupon_number}. ${item.origin_airport_code || "?"} to ${item.destination_airport_code || "?"}${item.flight_number ? ` · ${item.flight_number}` : ""} · ${label(item.coupon_status)}`} />
              </Panel>
              <section className="grid gap-4 lg:grid-cols-2">
                <Panel title="Pricing"><JsonBlock value={ticket?.pricing_snapshot_json} /></Panel>
                <Panel title="Fare / Rules"><JsonBlock value={{ fare_basis: ticket?.fare_basis_json, fare_bundle: ticket?.fare_bundle_snapshot_json, rules: ticket?.rules_snapshot_json }} /></Panel>
              </section>
              <Panel title="Warnings">
                <SnapshotList items={state?.warnings} render={(item) => item.message || JSON.stringify(item)} />
              </Panel>
              <Panel title="Linked EMDs">
                {state?.linked_emds?.length ? (
                  <div className="divide-y divide-slate-100 rounded-md border border-slate-200">
                    {state.linked_emds.map((emd) => <a className="block p-3 text-sm font-medium text-blue-700" href={`/agency/emds/${emd.id}`} key={emd.id}>{emd.emd_number || "Draft EMD"} · {emd.service_label || emd.service_key || "Service"}</a>)}
                  </div>
                ) : <EmptyState title="No linked EMDs" body="Draft EMD mirrors linked to this ticket appear here." />}
              </Panel>
              <Panel title="Timeline">
                <SnapshotList items={state?.timeline} render={(item) => `${item.title}${item.description ? ` · ${item.description}` : ""}`} />
              </Panel>
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-slate-950">{value}</p></div>
}

function Field({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Textarea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<textarea className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, options, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{labelValue(option)}</option>)}</select></label>
}

function SnapshotList({ items, render }) {
  const list = items || []
  if (!list.length) return <p className="text-sm text-slate-500">None recorded.</p>
  return <div className="divide-y divide-slate-100 rounded-md border border-slate-200">{list.map((item, index) => <div className="p-3 text-sm text-slate-700" key={item.id || index}>{render(item)}</div>)}</div>
}

function JsonBlock({ value }) {
  const hasValue = value && Object.keys(value).length
  if (!hasValue) return <p className="text-sm text-slate-500">None recorded.</p>
  return <pre className="max-h-72 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">{JSON.stringify(value, null, 2)}</pre>
}

function passengerName(passenger, fallback) {
  return passenger.display_name || passenger.snapshot_display_name || `${passenger.first_name || ""} ${passenger.last_name || ""}`.trim() || fallback || "Passenger"
}

function amountValue(value) {
  return value === null || value === undefined ? "" : String(value)
}

function numberOrNull(value) {
  return value === "" || value === null || value === undefined ? null : Number(value)
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function labelValue(value) {
  return String(value || "").replaceAll("_", " ")
}

function money(amount, currency) {
  if (amount === null || amount === undefined || amount === "") return "Not priced"
  return `${Number(amount).toFixed(2)} ${currency || "EUR"}`
}
