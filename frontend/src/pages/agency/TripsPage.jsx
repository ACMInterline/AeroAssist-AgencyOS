import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statuses = ["draft", "planning", "quoted", "booked", "ticketed", "in_travel", "completed", "cancelled", "archived"]
const tripTypes = ["one_way", "round_trip", "multi_city", "open_jaw", "complex", "unknown"]

export default function TripsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ search: "", status: "", trip_type: "" })
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const trips = context.agency ? await apiGet(`/api/agencies/${context.agency.id}/trips`) : { items: [] }
      setState({ ...context, trips: trips.items })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    const search = filters.search.toLowerCase()
    return (state?.trips || []).filter((trip) => {
      const matchesSearch = !search || [trip.trip_reference, trip.trip_title, trip.route_summary, trip.client?.display_name].some((value) => String(value || "").toLowerCase().includes(search))
      return matchesSearch && (!filters.status || trip.trip_status === filters.status) && (!filters.trip_type || trip.trip_type === filters.trip_type)
    })
  }, [filters, state])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Trips</h2>
                <p className="mt-1 text-sm text-slate-600">Trip dossiers are operational shells. Requests remain independent records.</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{filtered.length} shown</span>
                <a className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold" href="/agency/trips/new">Create trip</a>
              </div>
            </div>
          </div>

          <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-3">
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search reference, client, route" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">All statuses</option>
              {statuses.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.trip_type} onChange={(event) => setFilters({ ...filters, trip_type: event.target.value })}>
              <option value="">All trip types</option>
              {tripTypes.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
          </section>

          {filtered.length ? (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <div className="grid grid-cols-[1.2fr_1fr_1fr_120px_120px] gap-3 border-b border-slate-100 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 max-lg:hidden">
                <span>Trip</span><span>Route</span><span>Dates</span><span>Counts</span><span>Updated</span>
              </div>
              <div className="divide-y divide-slate-100">
                {filtered.map((trip) => (
                  <a className="grid gap-3 px-4 py-4 hover:bg-slate-50 lg:grid-cols-[1.2fr_1fr_1fr_120px_120px]" href={`/agency/trips/${trip.id}`} key={trip.id}>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{trip.trip_reference}</p>
                      <h3 className="font-semibold text-slate-950">{trip.trip_title}</h3>
                      <p className="text-xs text-slate-500">{trip.trip_status.replaceAll("_", " ")} · {trip.trip_type.replaceAll("_", " ")} · {trip.linked_request_count || 0} request(s)</p>
                    </div>
                    <p className="text-sm text-slate-600">{trip.route_summary || "Route pending"}</p>
                    <p className="text-sm text-slate-600">{trip.date_summary || "Dates pending"}</p>
                    <p className="text-sm text-slate-600">{trip.passenger_count} pax · {trip.segment_count} seg · {trip.service_count} svc</p>
                    <p className="text-xs text-slate-500">{String(trip.updated_at || "").slice(0, 10)}</p>
                  </a>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8">
              <EmptyState title="No trip dossiers found" body="Create a manual trip dossier or convert an operational request when work becomes trip-shaped." />
            </div>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
