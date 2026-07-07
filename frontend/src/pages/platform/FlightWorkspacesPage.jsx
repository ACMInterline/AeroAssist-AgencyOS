import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const statusOptions = ["draft", "active", "schedule_review", "ready", "flown", "archived"]

const defaultFilters = {
  agency_id: "",
  status: "",
  airline: "",
  departure_airport: "",
  arrival_airport: "",
  departure_date: "",
  cabin: "",
  booking_class: "",
}

export default function PlatformFlightWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, flights] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/flight-workspaces${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      flights: flights.items || [],
      summary: flights.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.status, filters.airline, filters.departure_airport, filters.arrival_airport, filters.departure_date, filters.cabin, filters.booking_class])

  const agencyOptions = useMemo(() => {
    return (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id])
  }, [state?.agencies])

  const metrics = [
    ["Flights", state?.flights?.length || 0],
    ["Active", state?.summary?.by_status?.active || 0],
    ["Ready", state?.summary?.by_status?.ready || 0],
    ["Passengers", state?.summary?.passenger_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Flight Workspaces</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only flight records. These records do not execute bookings, run live flight search, connect to GDS or NDC, call airline APIs, process payments, issue tickets, synchronize schedules, call external APIs, use AI, run background workers, automatically generate routes, validate flights, look up airlines, or update live schedules.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Read-only UI</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No live search</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Flight filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-8">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="From" value={filters.departure_airport} onChange={(value) => setFilters({ ...filters, departure_airport: value })} />
              <Field label="To" value={filters.arrival_airport} onChange={(value) => setFilters({ ...filters, arrival_airport: value })} />
              <Field label="Departure date" type="date" value={filters.departure_date} onChange={(value) => setFilters({ ...filters, departure_date: value })} />
              <Field label="Cabin" value={filters.cabin} onChange={(value) => setFilters({ ...filters, cabin: value })} />
              <Field label="Booking class" value={filters.booking_class} onChange={(value) => setFilters({ ...filters, booking_class: value })} />
            </div>
          </section>

          {state?.flights?.length ? <FlightList flights={state.flights} showAgency /> : <EmptyState title="No flight workspaces" body="Flight workspace metadata will appear here after platform records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function FlightList({ flights, showAgency = false }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Flight</th>
            {showAgency ? <th className="px-4 py-3">Agency</th> : null}
            <th className="px-4 py-3">Airline</th>
            <th className="px-4 py-3">Departure</th>
            <th className="px-4 py-3">Arrival</th>
            <th className="px-4 py-3">Cabin</th>
            <th className="px-4 py-3">Operations</th>
            <th className="px-4 py-3">Linked records</th>
            <th className="px-4 py-3">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {flights.map((flight) => (
            <tr key={flight.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{flight.flight_designator || flight.flight_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{flight.flight_reference}</p>
                <p className="mt-1"><StatusBadge status={flight.flight_status} /></p>
                <p className="mt-2 text-xs text-slate-500">{flight.operational_workspace?.workspace_title || flight.operational_workspace_id || "No assigned workspace"}</p>
              </td>
              {showAgency ? <td className="px-4 py-3 align-top text-slate-700">{flight.agency_name || flight.agency_id}</td> : null}
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{flight.airline_name || flight.airline_code || "Airline unset"}</p>
                <p className="mt-1">Marketing carrier: {flight.marketing_carrier || "Unset"}</p>
                <p className="mt-1">Operating carrier: {flight.operating_carrier || "Unset"}</p>
                <p className="mt-1">Flight: {flight.flight_number || "Unset"} / {flight.operating_flight_number || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{flight.departure_airport || "Origin unset"}</p>
                <p className="mt-1">Terminal {flight.departure_terminal || "Unset"}</p>
                <p className="mt-1">{formatDateTime(flight.departure_datetime)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{flight.arrival_airport || "Destination unset"}</p>
                <p className="mt-1">Terminal {flight.arrival_terminal || "Unset"}</p>
                <p className="mt-1">{formatDateTime(flight.arrival_datetime)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{flight.cabin_class || "Cabin unset"}</p>
                <p className="mt-1">Booking: {flight.booking_class || "Unset"}</p>
                <p className="mt-1">Fare: {flight.fare_family || "Unset"}</p>
                <p className="mt-1">Aircraft: {flight.aircraft_type || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{flight.flight_type || "Type unset"} / {flight.travel_direction || "Direction unset"}</p>
                <p className="mt-1">Baggage: {flight.baggage_summary || "Unset"}</p>
                <p className="mt-1">Connections: {flight.connection_summary || "Unset"}</p>
                <p className="mt-1">Stopovers: {flight.stopover_summary || "Unset"}</p>
                <p className="mt-1">Elapsed: {flight.elapsed_travel_time || "Unset"}</p>
                <ReferenceLine label="Operating days" items={flight.operating_days} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Passengers" items={flight.passengers?.map((item) => item.label || item.passenger_id)} />
                <ReferenceLine label="Requests" items={flight.linked_requests?.map((item) => item.label || item.request_id)} />
                <ReferenceLine label="Trips" items={flight.linked_trips?.map((item) => item.label || item.trip_id)} />
                <ReferenceLine label="Offers" items={flight.linked_offers?.map((item) => item.label || item.offer_id)} />
                <ReferenceLine label="Bookings" items={flight.linked_bookings?.map((item) => item.label || item.booking_id)} />
                <ReferenceLine label="Tickets" items={flight.linked_tickets?.map((item) => item.label || item.ticket_id)} />
                <ReferenceLine label="Documents" items={flight.linked_documents?.map((item) => item.label || item.document_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{flight.operational_notes || "No notes recorded"}</td>
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
    schedule_review: "bg-violet-50 text-violet-700 ring-violet-200",
    flown: "bg-slate-100 text-slate-700 ring-slate-200",
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

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : "Unset"
}
