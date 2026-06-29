import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "ready_to_book", "booking_in_progress", "booked", "blocked", "cancelled"]
const providers = ["manual", "travelport", "amadeus", "ndc", "supplier", "other"]

export default function BookingWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ status: "", provider_target: "", search: "" })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const query = new URLSearchParams()
    if (filters.status) query.set("status", filters.status)
    if (filters.provider_target) query.set("provider_target", filters.provider_target)
    const suffix = query.toString() ? `?${query.toString()}` : ""
    const workspaces = await apiGet(`/api/agencies/${context.agency.id}/booking-workspaces${suffix}`)
    setState({ ...context, workspaces: workspaces.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [filters.status, filters.provider_target])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.workspaces || []).filter((workspace) => {
      const record = workspace.booking_record || {}
      const trip = workspace.trip_summary || {}
      return !search || [
        workspace.workspace_number,
        workspace.title,
        trip.trip_reference,
        trip.trip_title,
        record.pnr_locator,
        workspace.request_id,
      ].some((value) => String(value || "").toLowerCase().includes(search))
    })
  }, [filters.search, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="text-2xl font-semibold text-slate-950">Booking Workspaces</h2>
              <p className="mt-1 text-sm text-slate-600">Manual booking workspace and PNR mirror records created from booking readiness packages.</p>
            </div>
            <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/bookings">Legacy bookings</a>
          </div>

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-3">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search workspace, trip, PNR" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {statuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.provider_target} onChange={(event) => setFilters({ ...filters, provider_target: event.target.value })}>
              <option value="">All providers</option>
              {providers.map((value) => <option value={value} key={value}>{label(value)}</option>)}
            </select>
          </section>

          {filtered.length ? (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <div className="grid grid-cols-[1.2fr_1.3fr_0.9fr_0.9fr_0.8fr_0.8fr_0.8fr] gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>Workspace</span>
                <span>Trip / request</span>
                <span>Provider</span>
                <span>Status</span>
                <span>Booking</span>
                <span>Warnings</span>
                <span>Created</span>
              </div>
              <div className="divide-y divide-slate-100">
                {filtered.map((workspace) => (
                  <a className="grid grid-cols-[1.2fr_1.3fr_0.9fr_0.9fr_0.8fr_0.8fr_0.8fr] gap-3 px-4 py-4 text-sm text-slate-700 hover:bg-blue-50/60" href={`/agency/booking-workspaces/${workspace.id}`} key={workspace.id}>
                    <span>
                      <span className="block font-semibold text-slate-950">{workspace.workspace_number}</span>
                      <span className="block truncate text-xs text-slate-500">{workspace.title}</span>
                    </span>
                    <span>
                      <span className="block font-medium text-slate-900">{workspace.trip_summary?.trip_reference || workspace.trip_id}</span>
                      <span className="block truncate text-xs text-slate-500">{workspace.request_id || "No request link"}</span>
                    </span>
                    <span>{label(workspace.provider_target)}</span>
                    <span>{label(workspace.status)}</span>
                    <span>
                      <span className="block">{label(workspace.booking_record?.booking_status || "draft")}</span>
                      <span className="block text-xs text-slate-500">{workspace.booking_record?.pnr_locator || "PNR pending"}</span>
                    </span>
                    <span>{workspace.warning_count || 0}</span>
                    <span>{dateLabel(workspace.created_at)}</span>
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState title="No booking workspaces found" body="Create one from an accepted offer booking readiness package." />
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function label(value) {
  return String(value || "none").replaceAll("_", " ")
}

function dateLabel(value) {
  return value ? new Date(value).toLocaleDateString() : "Not set"
}
