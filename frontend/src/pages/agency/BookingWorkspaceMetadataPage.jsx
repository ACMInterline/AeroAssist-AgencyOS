import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statusOptions = ["draft", "ready_to_book", "booking_in_progress", "booked", "blocked", "cancelled"]

const defaultFilters = {
  status: "",
  booking_owner: "",
  airline: "",
  supplier: "",
  booking_date: "",
}

export default function BookingWorkspaceMetadataPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [bookings, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/booking-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/booking-workspaces/summary`),
    ])
    setState({
      ...context,
      bookings: bookings.items || [],
      summary: bookings.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.status, filters.booking_owner, filters.airline, filters.supplier, filters.booking_date])

  const metrics = [
    ["Bookings", state?.bookings?.length || 0],
    ["Ready", state?.summary?.by_status?.ready_to_book || 0],
    ["Booked", state?.summary?.by_status?.booked || 0],
    ["Tickets", state?.summary?.ticket_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Daily Work</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Bookings</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only booking workspace metadata. These records do not create live bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, calculate fares, use AI, run background workers, automatically confirm bookings, automatically generate tickets, or integrate external providers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No ticket issuance</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Booking filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <Field label="Booking owner" value={filters.booking_owner} onChange={(value) => setFilters({ ...filters, booking_owner: value })} />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <Field label="Supplier" value={filters.supplier} onChange={(value) => setFilters({ ...filters, supplier: value })} />
              <Field label="Booking date" type="date" value={filters.booking_date} onChange={(value) => setFilters({ ...filters, booking_date: value })} />
            </div>
          </section>

          {state?.bookings?.length ? <BookingList bookings={state.bookings} /> : <EmptyState title="No booking workspaces" body="Booking workspace metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function BookingList({ bookings }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Booking reference</th>
            <th className="px-4 py-3">Booking status</th>
            <th className="px-4 py-3">Booking owner</th>
            <th className="px-4 py-3">Airline and supplier</th>
            <th className="px-4 py-3">Passenger summary</th>
            <th className="px-4 py-3">Flight summary</th>
            <th className="px-4 py-3">Trip and offer summary</th>
            <th className="px-4 py-3">Links</th>
            <th className="px-4 py-3">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {bookings.map((booking) => (
            <tr key={booking.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{booking.booking_display_name}</p>
                <p className="mt-1 text-xs text-slate-500">{booking.booking_reference}</p>
                <p className="mt-2 text-xs text-slate-500">{booking.booking_type || "Booking type unset"}</p>
              </td>
              <td className="px-4 py-3 align-top"><StatusBadge status={booking.booking_status} /></td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{booking.booking_owner || "No owner"}</p>
                <p className="mt-1">Source: {booking.booking_source || "Unset"}</p>
                <p className="mt-1">Created: {formatDate(booking.booking_created_date)}</p>
                <p className="mt-1">Deadline: {formatDate(booking.booking_deadline)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Airline PNR: {booking.airline_pnr || "Unset"}</p>
                <p className="mt-1">GDS locator: {booking.gds_record_locator || "Unset"}</p>
                <p className="mt-1">Supplier: {booking.supplier_reference || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Passengers" items={booking.passengers?.map((item) => item.label || item.passenger_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Flights" items={booking.flight_workspaces?.map((item) => item.label || item.flight_workspace_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Trip: {booking.trip_workspace?.label || booking.trip_workspace_id || "Unset"}</p>
                <p className="mt-1">Offer: {booking.offer_workspace?.label || booking.offer_workspace_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Tickets" items={booking.tickets?.map((item) => item.label || item.ticket_id)} />
                <ReferenceLine label="EMDs" items={booking.emds?.map((item) => item.label || item.emd_id)} />
                <ReferenceLine label="SSR" items={booking.ssrs?.map((item) => item.label || item.ssr_id)} />
                <ReferenceLine label="OSI" items={booking.osis?.map((item) => item.label || item.osi_id)} />
                <ReferenceLine label="Documents" items={booking.documents?.map((item) => item.label || item.document_id)} />
                <ReferenceLine label="Timeline" items={booking.timeline?.map((item) => item.label || item.timeline_id)} />
                <ReferenceLine label="Communications" items={booking.communications?.map((item) => item.label || item.communication_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Booking: {booking.booking_summary || "Unset"}</p>
                <p className="mt-1">Payment: {booking.payment_summary || "Unset"}</p>
                <p className="mt-1">Operational: {booking.operational_notes || booking.internal_notes || "Unset"}</p>
              </td>
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
    ready_to_book: "bg-sky-50 text-sky-700 ring-sky-200",
    booking_in_progress: "bg-blue-50 text-blue-700 ring-blue-200",
    booked: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    blocked: "bg-red-50 text-red-700 ring-red-200",
    cancelled: "bg-zinc-100 text-zinc-600 ring-zinc-200",
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[status] || "bg-slate-100 text-slate-700 ring-slate-200"}`}>{formatType(status)}</span>
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
