import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import RequestStatusBadge from "../../components/RequestStatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RequestsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "", priority: "", source: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const requests = context.agency ? await apiGet(`/api/agencies/${context.agency.id}/requests`) : { items: [] }
      setState({ ...context, requests: requests.items })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.requests || []).filter((request) => {
      const matchesSearch = !search || [request.request_reference, request.title, request.route_summary, request.service_summary, request.client?.display_name].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch
        && (!filters.status || request.status === filters.status)
        && (!filters.priority || request.priority === filters.priority)
        && (!filters.source || request.source === filters.source)
    })
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Request Intake</p>
              <h2 className="text-2xl font-semibold text-slate-950">Requests</h2>
              <p className="mt-1 text-sm text-slate-600">Inquiry/case records before offers or bookings exist.</p>
            </div>
            <a className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/agency/requests/new">Create request</a>
          </div>
          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-4">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search requests" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {["draft", "new", "triage", "waiting_for_client", "in_progress", "ready_for_offer", "offer_created", "closed", "cancelled", "archived"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.priority} onChange={(event) => setFilters({ ...filters, priority: event.target.value })}>
              <option value="">All priorities</option>
              {["low", "normal", "high", "urgent"].map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.source} onChange={(event) => setFilters({ ...filters, source: event.target.value })}>
              <option value="">All sources</option>
              {["staff_created", "website_form", "client_portal", "phone", "email", "whatsapp", "walk_in", "imported"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
          </section>
          {filtered.length ? (
            <div className="grid gap-4">
              {filtered.map((request) => (
                <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={`/agency/requests/${request.id}`} key={request.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{request.request_reference}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{request.title}</h3>
                      <p className="mt-1 text-sm text-slate-600">{request.client?.display_name || "Client"} · {request.route_summary || "Route not set"}</p>
                    </div>
                    <RequestStatusBadge status={request.status} />
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-4">
                    <span>Priority: {request.priority}</span>
                    <span>Source: {request.source.replaceAll("_", " ")}</span>
                    <span>Passengers: {request.passenger_count}</span>
                    <span>Services: {request.service_count}</span>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">{request.service_summary || "No service summary yet"}</p>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No requests found" body="Create a request from a client and link passengers, intended segments, services, messages, and tasks." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
