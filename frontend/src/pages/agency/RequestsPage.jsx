import { useEffect, useMemo, useState } from "react"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import EmptyState from "../../components/EmptyState"
import FilterBar from "../../components/FilterBar"
import PageHeader from "../../components/PageHeader"
import PrimaryButton from "../../components/PrimaryButton"
import PriorityBadge from "../../components/PriorityBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import RequestStatusBadge from "../../components/RequestStatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"
import { productLabel } from "../../lib/productLanguage"

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
          <PageHeader
            eyebrow="Client requests"
            title="Requests"
            description="Capture what the client needs, who is travelling, and the services required before preparing a trip or offer."
            actions={<PrimaryButton href="/agency/requests/new" icon={Plus}>Create request</PrimaryButton>}
          />
          <FilterBar
            onClear={() => setFilters({ search: "", status: "", priority: "", source: "" })}
            resultCount={filtered.length}
            title="Filter requests"
          >
            <div className="grid gap-3 md:grid-cols-4">
              <label className="grid gap-1 text-sm font-medium text-slate-700">
                Search
                <input className="field" placeholder="Client, route, or request reference" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
              </label>
              <label className="grid gap-1 text-sm font-medium text-slate-700">
                Current status
                <select className="field" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
                  <option value="">All statuses</option>
                  {["draft", "new", "triage", "waiting_for_client", "in_progress", "ready_for_offer", "offer_created", "closed", "cancelled", "archived"].map((value) => <option key={value} value={value}>{productLabel(value)}</option>)}
                </select>
              </label>
              <label className="grid gap-1 text-sm font-medium text-slate-700">
                Priority
                <select className="field" value={filters.priority} onChange={(event) => setFilters({ ...filters, priority: event.target.value })}>
                  <option value="">All priorities</option>
                  {["low", "normal", "high", "urgent"].map((value) => <option key={value} value={value}>{productLabel(value)}</option>)}
                </select>
              </label>
              <label className="grid gap-1 text-sm font-medium text-slate-700">
                Received through
                <select className="field" value={filters.source} onChange={(event) => setFilters({ ...filters, source: event.target.value })}>
                  <option value="">All sources</option>
                  {["staff_created", "website_form", "public_website", "client_portal", "phone", "email", "whatsapp", "walk_in", "imported", "internal"].map((value) => <option key={value} value={value}>{productLabel(value)}</option>)}
                </select>
              </label>
            </div>
          </FilterBar>
          {filtered.length ? (
            <div className="grid gap-4">
              {filtered.map((request) => (
                <a className="group rounded-lg border border-slate-200 bg-white p-5 hover:-translate-y-0.5 hover:border-blue-300" href={`/agency/requests/${request.id}`} key={request.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{request.request_reference}</p>
                      <h3 className="mt-1 font-semibold text-slate-950 group-hover:text-blue-700">{request.title}</h3>
                      <p className="mt-1 text-sm text-slate-600">{request.client?.display_name || "Client"} · {request.route_summary || "Route not set"}</p>
                      {request.linked_trip ? <span className="mt-2 inline-flex rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">{request.linked_trip.trip_reference}</span> : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <PriorityBadge priority={request.priority} />
                      <RequestStatusBadge status={request.status} />
                    </div>
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-slate-600 md:grid-cols-4">
                    <span>Assigned priority: {productLabel(request.priority)}</span>
                    <span>Received through: {productLabel(request.source)}</span>
                    <span>Passengers: {request.passenger_count}</span>
                    <span>Services: {request.service_count}</span>
                  </div>
                  <p className="mt-3 text-sm text-slate-600">{request.service_summary || "No service summary yet"}</p>
                </a>
              ))}
            </div>
          ) : (
            <EmptyState title="No requests match these filters" body="Clear the filters or create a request when a client needs travel support.">
              <PrimaryButton href="/agency/requests/new" icon={Plus}>Create request</PrimaryButton>
            </EmptyState>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
