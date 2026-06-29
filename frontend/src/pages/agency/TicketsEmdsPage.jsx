import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_issue", "issued", "voided", "refunded", "exchanged", "cancelled"]
const providers = ["manual", "travelport", "amadeus", "ndc", "supplier", "other"]

export default function TicketsEmdsPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("tickets")
  const [filters, setFilters] = useState({ status: "", provider: "", service_key: "", search: "" })
  const [modal, setModal] = useState("")
  const [form, setForm] = useState(defaultForm())
  const [error, setError] = useState("")
  const [working, setWorking] = useState(false)

  async function load() {
    const context = await loadCurrentAgency()
    const [tickets, emds] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/tickets`),
      apiGet(`/api/agencies/${context.agency.id}/emds`),
    ])
    setState({ ...context, tickets: tickets.items || [], emds: emds.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function submitModal(event) {
    event.preventDefault()
    setWorking(true)
    setError("")
    try {
      if (modal === "ticket") {
        const created = await apiPost(`/api/agencies/${state.agency.id}/tickets/manual`, {
          booking_record_id: form.booking_record_id || null,
          booking_workspace_id: form.booking_workspace_id || null,
          trip_id: form.trip_id || null,
          client_id: form.client_id || null,
          passenger_id: form.passenger_id || null,
          ticket_number: form.ticket_number || null,
          validating_carrier: form.validating_carrier || null,
          currency: form.currency || null,
          base_fare_amount: amount(form.base_fare_amount),
          taxes_amount: amount(form.taxes_amount),
          total_amount: amount(form.total_amount),
          segments_snapshot_json: parseJson(form.segments_snapshot_json, []),
          internal_notes: form.internal_notes || null,
          source_context: "standalone_manual",
        })
        window.location.href = `/agency/tickets/${created.ticket.id}`
        return
      }
      if (modal === "emd") {
        const created = await apiPost(`/api/agencies/${state.agency.id}/emds/manual`, {
          booking_record_id: form.booking_record_id || null,
          booking_workspace_id: form.booking_workspace_id || null,
          ticket_record_id: form.ticket_record_id || null,
          trip_id: form.trip_id || null,
          client_id: form.client_id || null,
          passenger_id: form.passenger_id || null,
          emd_number: form.emd_number || null,
          service_key: form.service_key || null,
          service_label: form.service_label || null,
          service_category: form.service_category || null,
          emd_type: form.emd_type || "manual_mirror",
          currency: form.currency || null,
          amount: amount(form.base_fare_amount),
          taxes_amount: amount(form.taxes_amount),
          total_amount: amount(form.total_amount),
          internal_notes: form.internal_notes || null,
          source_context: "standalone_manual",
        })
        window.location.href = `/agency/emds/${created.emd.id}`
        return
      }
      if (modal === "ticket_exchange") {
        await apiPost(`/api/agencies/${state.agency.id}/ticket-exchange-operations`, {
          original_ticket_record_id: form.original_record_id,
          operation_type: form.operation_type || "exchange",
          trip_id: form.trip_id || null,
          booking_record_id: form.booking_record_id || null,
          reason: form.internal_notes || null,
          currency: form.currency || null,
        })
      }
      if (modal === "emd_exchange") {
        await apiPost(`/api/agencies/${state.agency.id}/emd-exchange-operations`, {
          original_emd_record_id: form.original_record_id,
          operation_type: form.operation_type || "exchange",
          trip_id: form.trip_id || null,
          booking_record_id: form.booking_record_id || null,
          reason: form.internal_notes || null,
          currency: form.currency || null,
        })
      }
      setModal("")
      setForm(defaultForm())
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking(false)
    }
  }

  const filteredTickets = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.tickets || []).filter((item) => (
      (!filters.status || item.issue_status === filters.status)
      && (!filters.provider || item.issuing_provider === filters.provider)
      && (!search || [item.ticket_number, item.validating_carrier, item.trip_id, item.booking_workspace_id, passengerName(item)].some((value) => String(value || "").toLowerCase().includes(search)))
    ))
  }, [filters, state])

  const filteredEmds = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.emds || []).filter((item) => (
      (!filters.status || item.issue_status === filters.status)
      && (!filters.provider || item.issuing_provider === filters.provider)
      && (!filters.service_key || item.service_key === filters.service_key)
      && (!search || [item.emd_number, item.service_key, item.service_label, item.trip_id, item.booking_workspace_id, passengerName(item)].some((value) => String(value || "").toLowerCase().includes(search)))
    ))
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="text-2xl font-semibold text-slate-950">Tickets & EMDs</h2>
              <p className="mt-1 text-sm text-slate-600">Internal mirrors only. Live issuance is disabled.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => setModal("ticket")}>Create manual ticket</button>
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => setModal("emd")}>Create manual EMD</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => setModal("ticket_exchange")}>Start ticket exchange</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => setModal("emd_exchange")}>Start EMD exchange</button>
              <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/booking-workspaces">Booking workspaces</a>
            </div>
          </div>

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-[180px_minmax(0,1fr)_180px_180px_180px]">
            <div className="flex rounded-md border border-slate-300 p-1">
              <button className={`flex-1 rounded px-2 py-1.5 text-sm font-semibold ${tab === "tickets" ? "bg-blue-600 text-white" : "text-slate-700"}`} type="button" onClick={() => setTab("tickets")}>Tickets</button>
              <button className={`flex-1 rounded px-2 py-1.5 text-sm font-semibold ${tab === "emds" ? "bg-blue-600 text-white" : "text-slate-700"}`} type="button" onClick={() => setTab("emds")}>EMDs</button>
            </div>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search ticket, EMD, passenger" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {statuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.provider} onChange={(event) => setFilters({ ...filters, provider: event.target.value })}>
              <option value="">All providers</option>
              {providers.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service key" value={filters.service_key} onChange={(event) => setFilters({ ...filters, service_key: event.target.value.toUpperCase() })} disabled={tab !== "emds"} />
          </section>

          {tab === "tickets" ? <TicketList items={filteredTickets} /> : <EmdList items={filteredEmds} />}
          {modal ? <MirrorModal form={form} modal={modal} onChange={(updates) => setForm({ ...form, ...updates })} onClose={() => setModal("")} onSubmit={submitModal} working={working} /> : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function MirrorModal({ form, modal, onChange, onClose, onSubmit, working }) {
  const isTicket = modal === "ticket"
  const isEmd = modal === "emd"
  const isExchange = modal === "ticket_exchange" || modal === "emd_exchange"
  const exchangeOptions = modal === "emd_exchange" ? ["exchange", "reissue", "void", "refund", "service_change", "other"] : ["exchange", "reissue", "void", "refund", "name_correction", "schedule_change_reissue", "other"]
  const title = {
    ticket: "Create manual ticket",
    emd: "Create manual EMD",
    ticket_exchange: "Start ticket exchange",
    emd_exchange: "Start EMD exchange",
  }[modal]
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <form className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-lg bg-white shadow-xl" onSubmit={onSubmit}>
        <div className="flex items-start justify-between gap-3 border-b border-slate-200 p-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Internal mirror only</p>
            <h3 className="text-xl font-semibold text-slate-950">{title}</h3>
            <p className="mt-1 text-sm text-slate-600">No provider action, issuance, exchange, refund, or void is performed.</p>
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onClose}>Close</button>
        </div>
        <div className="space-y-4 p-5">
          <div className="grid gap-3 md:grid-cols-2">
            {isExchange ? <Field label="Original record id" value={form.original_record_id} onChange={(value) => onChange({ original_record_id: value })} required /> : null}
            {isExchange ? <Select label="Operation type" value={form.operation_type} options={exchangeOptions} onChange={(value) => onChange({ operation_type: value })} /> : null}
            <Field label="Booking record id" value={form.booking_record_id} onChange={(value) => onChange({ booking_record_id: value })} />
            <Field label="Booking workspace id" value={form.booking_workspace_id} onChange={(value) => onChange({ booking_workspace_id: value })} />
            <Field label="Trip id/reference" value={form.trip_id} onChange={(value) => onChange({ trip_id: value })} />
            <Field label="Passenger id" value={form.passenger_id} onChange={(value) => onChange({ passenger_id: value })} />
            {isTicket ? <Field label="Ticket number" value={form.ticket_number} onChange={(value) => onChange({ ticket_number: value })} /> : null}
            {isTicket ? <Field label="Validating carrier" value={form.validating_carrier} onChange={(value) => onChange({ validating_carrier: value.toUpperCase() })} /> : null}
            {isEmd ? <Field label="EMD number" value={form.emd_number} onChange={(value) => onChange({ emd_number: value })} /> : null}
            {isEmd ? <Field label="Ticket record id" value={form.ticket_record_id} onChange={(value) => onChange({ ticket_record_id: value })} /> : null}
            {isEmd ? <Field label="Service key" value={form.service_key} onChange={(value) => onChange({ service_key: value.toUpperCase() })} /> : null}
            {isEmd ? <Field label="Service label" value={form.service_label} onChange={(value) => onChange({ service_label: value })} /> : null}
            <Field label="Currency" value={form.currency} onChange={(value) => onChange({ currency: value.toUpperCase() })} />
            <Field label="Base / amount" value={form.base_fare_amount} onChange={(value) => onChange({ base_fare_amount: value })} />
            <Field label="Taxes" value={form.taxes_amount} onChange={(value) => onChange({ taxes_amount: value })} />
            <Field label="Total" value={form.total_amount} onChange={(value) => onChange({ total_amount: value })} />
          </div>
          {isTicket ? <TextArea label="Segment / coupon snapshot JSON" value={form.segments_snapshot_json} onChange={(value) => onChange({ segments_snapshot_json: value })} /> : null}
          <TextArea label={isExchange ? "Reason / notes" : "Internal notes"} value={form.internal_notes} onChange={(value) => onChange({ internal_notes: value })} plain />
        </div>
        <div className="flex justify-end border-t border-slate-200 p-5">
          <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working}>{working ? "Working..." : title}</button>
        </div>
      </form>
    </div>
  )
}

function TicketList({ items }) {
  if (!items.length) return <EmptyState title="No tickets found" body="Create draft ticket mirrors from a booking workspace." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <span>Ticket</span><span>Passenger</span><span>Booking workspace</span><span>Provider</span><span>Status</span><span>Amount</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.map((item) => (
          <a className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-4 text-sm text-slate-700 hover:bg-blue-50/60" href={`/agency/tickets/${item.id}`} key={item.id}>
            <span className="font-semibold text-slate-950">{item.ticket_number || "Draft ticket"}</span>
            <span>{passengerName(item)}</span>
            <span>{item.booking_workspace_id || "Not linked"}</span>
            <span>{label(item.issuing_provider)}</span>
            <span>{label(item.issue_status || item.status)}</span>
            <span>{money(item.total_amount, item.currency)}</span>
          </a>
        ))}
      </div>
    </div>
  )
}

function EmdList({ items }) {
  if (!items.length) return <EmptyState title="No EMDs found" body="Create draft EMD mirrors from booking services." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        <span>EMD</span><span>Service</span><span>Passenger</span><span>Provider</span><span>Status</span><span>Amount</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.map((item) => (
          <a className="grid grid-cols-[1fr_1fr_1fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-4 text-sm text-slate-700 hover:bg-blue-50/60" href={`/agency/emds/${item.id}`} key={item.id}>
            <span className="font-semibold text-slate-950">{item.emd_number || "Draft EMD"}</span>
            <span>{item.service_label || item.service_key || "Manual service"}</span>
            <span>{passengerName(item)}</span>
            <span>{label(item.issuing_provider)}</span>
            <span>{label(item.issue_status || item.status)}</span>
            <span>{money(item.total_amount ?? item.amount, item.currency)}</span>
          </a>
        ))}
      </div>
    </div>
  )
}

function Field({ label: fieldLabel, required, value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" required={required} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{label(option)}</option>)}
      </select>
    </label>
  )
}

function TextArea({ label: fieldLabel, plain, value, onChange }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {fieldLabel}
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" spellCheck={plain ? undefined : false} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function passengerName(item) {
  const passenger = item.passenger_snapshot_json || {}
  return passenger.display_name || passenger.snapshot_display_name || `${passenger.first_name || ""} ${passenger.last_name || ""}`.trim() || item.passenger_id || "Passenger"
}

function defaultForm() {
  return {
    booking_record_id: "",
    booking_workspace_id: "",
    trip_id: "",
    client_id: "",
    passenger_id: "",
    ticket_record_id: "",
    ticket_number: "",
    validating_carrier: "",
    emd_number: "",
    emd_type: "manual_mirror",
    service_key: "",
    service_label: "",
    service_category: "",
    original_record_id: "",
    operation_type: "exchange",
    currency: "EUR",
    base_fare_amount: "",
    taxes_amount: "",
    total_amount: "",
    segments_snapshot_json: "[]",
    internal_notes: "",
  }
}

function parseJson(value, fallback) {
  const text = String(value || "").trim()
  if (!text) return fallback
  return JSON.parse(text)
}

function amount(value) {
  return value === "" || value === null || value === undefined ? null : Number(value)
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function money(amount, currency) {
  if (amount === null || amount === undefined || amount === "") return "Not priced"
  return `${Number(amount).toFixed(2)} ${currency || "EUR"}`
}
