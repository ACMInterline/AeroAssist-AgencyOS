import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statusOptions = ["draft", "planning", "active", "ready", "traveling", "completed", "archived"]

const defaultFilters = {
  status: "",
  departure_country: "",
  destination_country: "",
  departure_date: "",
  assigned_agent: "",
  priority: "",
}

export default function TripWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [trips, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/trip-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/trip-workspaces/summary`),
    ])
    setState({
      ...context,
      trips: trips.items || [],
      summary: trips.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.status, filters.departure_country, filters.destination_country, filters.departure_date, filters.assigned_agent, filters.priority])

  const metrics = [
    ["Trips", state?.trips?.length || 0],
    ["Active", state?.summary?.by_status?.active || 0],
    ["Ready", state?.summary?.by_status?.ready || 0],
    ["Passengers", state?.summary?.passenger_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Daily Work</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Trips</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only trip workspace metadata. These records do not execute bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, create invoices, use AI, run background workers, automatically generate trips, automatically generate itineraries, call external integrations, or automate journeys.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No itinerary generation</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Trip filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-6">
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <Field label="Departure country" value={filters.departure_country} onChange={(value) => setFilters({ ...filters, departure_country: value })} />
              <Field label="Destination country" value={filters.destination_country} onChange={(value) => setFilters({ ...filters, destination_country: value })} />
              <Field label="Departure date" type="date" value={filters.departure_date} onChange={(value) => setFilters({ ...filters, departure_date: value })} />
              <Field label="Assigned agent" value={filters.assigned_agent} onChange={(value) => setFilters({ ...filters, assigned_agent: value })} />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
            </div>
          </section>

          {state?.trips?.length ? <TripList trips={state.trips} /> : <EmptyState title="No trip workspaces" body="Trip workspace metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function TripList({ trips }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Trip</th>
            <th className="px-4 py-3">Journey</th>
            <th className="px-4 py-3">Travel dates</th>
            <th className="px-4 py-3">Origin / Destination</th>
            <th className="px-4 py-3">Passenger summary</th>
            <th className="px-4 py-3">Flight summary</th>
            <th className="px-4 py-3">Linked records</th>
            <th className="px-4 py-3">Assigned team</th>
            <th className="px-4 py-3">Operational notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {trips.map((trip) => (
            <tr key={trip.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{trip.trip_display_name || trip.trip_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{trip.trip_reference}</p>
                <p className="mt-1"><StatusBadge status={trip.trip_status} /></p>
                <p className="mt-2 text-xs text-slate-500">{trip.operational_workspace?.workspace_title || trip.operational_workspace_id || "No assigned workspace"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Journey type: {trip.journey_type || "Unset"}</p>
                <p className="mt-1">Service type: {trip.service_type || "Unset"}</p>
                <p className="mt-1">Priority: {trip.operational_priority || "Unset"}</p>
                <p className="mt-1">Client: {trip.client?.label || trip.client_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Depart: {formatDate(trip.departure_date)}</p>
                <p className="mt-1">Return: {formatDate(trip.return_date)}</p>
                <p className="mt-1">Duration: {trip.travel_duration || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{trip.departure_city || "Origin city unset"}, {trip.departure_country || "Country unset"}</p>
                <p className="mt-1">{trip.origin_airport || "Origin airport unset"}</p>
                <p className="mt-2">{trip.destination_city || "Destination city unset"}, {trip.destination_country || "Country unset"}</p>
                <p className="mt-1">{trip.destination_airport || "Destination airport unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Count: {trip.passenger_count || trip.passenger_ids?.length || 0}</p>
                <ReferenceLine label="Passengers" items={trip.passengers?.map((item) => item.label || item.passenger_id)} />
                <p className="mt-2">Baggage: {trip.baggage_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Flights" items={trip.flight_workspaces?.map((item) => item.label || item.flight_workspace_id)} />
                <p className="mt-2">Itinerary: {trip.itinerary_summary || "Unset"}</p>
                <p className="mt-1">Services: {trip.service_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Requests" items={trip.travel_requests?.map((item) => item.label || item.request_id)} />
                <ReferenceLine label="Offers" items={trip.offers?.map((item) => item.label || item.offer_id)} />
                <ReferenceLine label="Bookings" items={trip.bookings?.map((item) => item.label || item.booking_id)} />
                <ReferenceLine label="Tickets" items={trip.tickets?.map((item) => item.label || item.ticket_id)} />
                <ReferenceLine label="EMDs" items={trip.emds?.map((item) => item.label || item.emd_id)} />
                <ReferenceLine label="Documents" items={trip.documents?.map((item) => item.label || item.document_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{trip.assigned_agent || "No assigned agent"}</p>
                <ReferenceLine label="Team" items={trip.assigned_team} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{trip.operational_notes || "No notes recorded"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Field({ label, type = "text", value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function SelectField({ label, value, onChange, options, placeholder }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
  )
}

function ReferenceLine({ label, items }) {
  return <p className="mt-1"><span className="font-semibold text-slate-700">{label}:</span> {formatList(items)}</p>
}

function StatusBadge({ status }) {
  const tones = {
    active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    ready: "bg-sky-50 text-sky-700 ring-sky-200",
    planning: "bg-violet-50 text-violet-700 ring-violet-200",
    traveling: "bg-amber-50 text-amber-700 ring-amber-200",
    completed: "bg-slate-100 text-slate-700 ring-slate-200",
    archived: "bg-zinc-100 text-zinc-600 ring-zinc-200",
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[status] || "bg-blue-50 text-blue-700 ring-blue-200"}`}>{formatType(status)}</span>
}

function queryString(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatList(items) {
  const values = (items || []).filter(Boolean)
  return values.length ? values.join(", ") : "None"
}

function formatType(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString() : "Unset"
}
