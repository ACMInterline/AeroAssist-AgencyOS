import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import RefundExchangeStatusBadge from "../../components/RefundExchangeStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const CASE_TYPES = [
  "refund",
  "exchange",
  "void",
  "schedule_change",
  "involuntary_change",
  "cancellation",
  "other",
]

const PRIORITY_OPTIONS = ["low", "normal", "high", "urgent"]
const STATUSES = [
  "draft",
  "client_requested",
  "review_needed",
  "checking_supplier_rules",
  "waiting_for_client",
  "waiting_for_supplier",
  "approved",
  "processing_externally",
  "completed",
  "rejected",
  "cancelled",
  "archived",
]

export default function RefundExchangeCasesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "", case_type: "", priority: "", client_id: "" })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [casesData, clientsData] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/refund-exchange-cases`),
      apiGet(`/api/agencies/${context.agency.id}/clients`),
    ])
    setState({
      ...context,
      cases: casesData.items,
      clients: clientsData.items,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    return (state?.cases || []).filter((item) => {
      const clientMatch = !filters.client_id || item.client_id === filters.client_id
      const caseMatch = !filters.case_type || item.case_type === filters.case_type
      const priorityMatch = !filters.priority || item.priority === filters.priority
      const statusMatch = !filters.status || item.status === filters.status
      const search = filters.search.toLowerCase()
      const searchMatch = !search
        || String(item.case_reference || "").toLowerCase().includes(search)
        || String(item.client?.display_name || "").toLowerCase().includes(search)
        || String(item.booking?.booking_reference || "").toLowerCase().includes(search)

      return clientMatch && caseMatch && priorityMatch && statusMatch && searchMatch
    })
  }, [state?.cases, filters])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Refunds and exchanges</p>
              <h2 className="text-2xl font-semibold text-slate-950">Refund / Exchange Cases</h2>
              <p className="mt-1 text-sm text-slate-600">Track manual refund and exchange cases without automating airline operations.</p>
            </div>
            <a className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" href="/agency/refunds-exchanges/new">
              Create case
            </a>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2 lg:grid-cols-5">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search reference, client, booking" value={filters.search} onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
              <option value="">All statuses</option>
              {STATUSES.map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.case_type} onChange={(event) => setFilters((current) => ({ ...current, case_type: event.target.value }))}>
              <option value="">All types</option>
              {CASE_TYPES.map((caseType) => <option key={caseType} value={caseType}>{caseType.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.priority} onChange={(event) => setFilters((current) => ({ ...current, priority: event.target.value }))}>
              <option value="">All priorities</option>
              {PRIORITY_OPTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.client_id} onChange={(event) => setFilters((current) => ({ ...current, client_id: event.target.value }))}>
              <option value="">All clients</option>
              {(state?.clients || []).map((client) => <option key={client.id} value={client.id}>{client.display_name}</option>)}
            </select>
          </section>

          {!filtered.length ? <EmptyState title="No matching cases" body="Create a new refund/exchange case from a booking or manually." /> : (
            <div className="grid gap-4">
              {filtered.map((item) => (
                <section key={item.id} className="rounded-lg border border-slate-200 bg-white p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.case_reference}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{item.client?.display_name || "Client"}</h3>
                      <p className="mt-1 text-sm text-slate-600">{item.case_type} · {item.booking?.booking_reference || "No booking"}</p>
                    </div>
                    <RefundExchangeStatusBadge status={item.status} />
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                    <p>Priority: <span className="font-medium text-slate-900">{item.priority}</span></p>
                    <p>Reason: <span className="font-medium text-slate-900">{item.reason_category}</span></p>
                    <p>Due / ETA: <span className="font-medium text-slate-900">{item.estimated_total_due_from_client || 0} {item.currency}</span></p>
                    <p>Due to client: <span className="font-medium text-slate-900">{item.estimated_total_due_to_client || 0} {item.currency}</span></p>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-blue-700" href={`/agency/refunds-exchanges/${item.id}`}>Open</a>
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
