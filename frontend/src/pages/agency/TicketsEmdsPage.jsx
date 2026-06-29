import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_issue", "issued", "voided", "refunded", "exchanged", "cancelled"]
const providers = ["manual", "travelport", "amadeus", "ndc", "supplier", "other"]

export default function TicketsEmdsPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("tickets")
  const [filters, setFilters] = useState({ status: "", provider: "", service_key: "", search: "" })
  const [error, setError] = useState("")

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
            <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/booking-workspaces">Booking workspaces</a>
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
        </div>
      </ProtectedRoute>
    </AgencyLayout>
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

function passengerName(item) {
  const passenger = item.passenger_snapshot_json || {}
  return passenger.display_name || passenger.snapshot_display_name || `${passenger.first_name || ""} ${passenger.last_name || ""}`.trim() || item.passenger_id || "Passenger"
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function money(amount, currency) {
  if (amount === null || amount === undefined || amount === "") return "Not priced"
  return `${Number(amount).toFixed(2)} ${currency || "EUR"}`
}
