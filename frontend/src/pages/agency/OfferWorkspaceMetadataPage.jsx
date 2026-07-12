import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statusOptions = ["draft", "preparing", "review", "ready", "shared", "accepted", "declined", "expired", "archived"]

const defaultFilters = {
  status: "",
  validity: "",
  client_id: "",
  destination: "",
  min_price: "",
  max_price: "",
  assigned_agent: "",
}

export default function OfferWorkspaceMetadataPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [offers, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces-v2${query}`),
      apiGet(`/api/agencies/${context.agency.id}/offer-workspaces-v2/summary`),
    ])
    setState({
      ...context,
      offers: offers.items || [],
      summary: offers.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.status, filters.validity, filters.client_id, filters.destination, filters.min_price, filters.max_price, filters.assigned_agent])

  const metrics = [
    ["Offers", state?.offers?.length || 0],
    ["Ready", state?.summary?.by_status?.ready || 0],
    ["Shared", state?.summary?.by_status?.shared || 0],
    ["Passengers", state?.summary?.passenger_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Daily Work</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Offers</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only offer workspace metadata. These records do not execute bookings, issue tickets, process payments, connect to GDS or NDC, call airline APIs, calculate fares, generate AI itineraries, integrate suppliers, call external APIs, automatically convert bookings, or run background workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No live pricing</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
            <p className="font-semibold text-slate-950">Operational workflow summary</p>
            <p className="mt-1">Offer lifecycle summaries and accepted-offer guard metadata are available in <a className="font-semibold text-blue-700" href="/agency/operational-workflows">Operational Workflows</a>. These summaries are metadata-only and do not convert or book offers.</p>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Offer filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-7">
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <Field label="Validity" type="date" value={filters.validity} onChange={(value) => setFilters({ ...filters, validity: value })} />
              <Field label="Client" value={filters.client_id} onChange={(value) => setFilters({ ...filters, client_id: value })} />
              <Field label="Destination" value={filters.destination} onChange={(value) => setFilters({ ...filters, destination: value })} />
              <Field label="Min price" type="number" value={filters.min_price} onChange={(value) => setFilters({ ...filters, min_price: value })} />
              <Field label="Max price" type="number" value={filters.max_price} onChange={(value) => setFilters({ ...filters, max_price: value })} />
              <Field label="Assigned agent" value={filters.assigned_agent} onChange={(value) => setFilters({ ...filters, assigned_agent: value })} />
            </div>
          </section>

          {state?.offers?.length ? <OfferList offers={state.offers} /> : <EmptyState title="No offer workspaces" body="Offer workspace metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function OfferList({ offers }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Offer reference</th>
            <th className="px-4 py-3">Trip summary</th>
            <th className="px-4 py-3">Passenger summary</th>
            <th className="px-4 py-3">Flight summary</th>
            <th className="px-4 py-3">Pricing summary</th>
            <th className="px-4 py-3">Services</th>
            <th className="px-4 py-3">Validity</th>
            <th className="px-4 py-3">Linked records</th>
            <th className="px-4 py-3">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {offers.map((offer) => (
            <tr key={offer.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{offer.offer_display_name || offer.offer_title}</p>
                <p className="mt-1 text-xs text-slate-500">{offer.offer_reference}</p>
                <p className="mt-1"><StatusBadge status={offer.offer_status} /></p>
                <p className="mt-2 text-xs text-slate-500">{offer.offer_type || "Offer type unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{offer.trip_workspace?.label || offer.trip_workspace_id || "No trip workspace"}</p>
                <p className="mt-2">Destination: {offer.destination_summary || "Unset"}</p>
                <p className="mt-1">Itinerary: {offer.itinerary_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Client: {offer.client?.label || offer.client_id || "Unset"}</p>
                <ReferenceLine label="Passengers" items={offer.passengers?.map((item) => item.label || item.passenger_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Flights" items={offer.flight_workspaces?.map((item) => item.label || item.flight_workspace_id)} />
                <p className="mt-2">Baggage: {offer.baggage_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatMoney(offer.total_price, offer.currency)}</p>
                <p className="mt-1">Pricing: {offer.pricing_summary || "Unset"}</p>
                <p className="mt-1">Taxes: {offer.taxes_summary || "Unset"}</p>
                <p className="mt-1">Fees: {offer.fees_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Ancillary: {offer.ancillary_summary || "Unset"}</p>
                <p className="mt-1">Seats: {offer.seat_summary || "Unset"}</p>
                <p className="mt-1">Meals: {offer.meal_summary || "Unset"}</p>
                <p className="mt-1">Hotels: {offer.hotel_summary || "Unset"}</p>
                <p className="mt-1">Transfers: {offer.transfer_summary || "Unset"}</p>
                <p className="mt-1">Insurance: {offer.insurance_summary || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatDate(offer.validity_date)}</p>
                <p className="mt-2">{offer.assigned_agent || "No assigned agent"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Bookings" items={offer.linked_bookings?.map((item) => item.label || item.booking_id)} />
                <ReferenceLine label="Tickets" items={offer.linked_tickets?.map((item) => item.label || item.ticket_id)} />
                <ReferenceLine label="Documents" items={offer.linked_documents?.map((item) => item.label || item.document_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Agent: {offer.agent_notes || "Unset"}</p>
                <p className="mt-1">Customer: {offer.customer_notes || "Unset"}</p>
                <p className="mt-1">Internal: {offer.internal_notes || "Unset"}</p>
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
    ready: "bg-sky-50 text-sky-700 ring-sky-200",
    shared: "bg-violet-50 text-violet-700 ring-violet-200",
    accepted: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    declined: "bg-red-50 text-red-700 ring-red-200",
    expired: "bg-amber-50 text-amber-700 ring-amber-200",
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

function formatMoney(value, currency) {
  if (value === null || value === undefined || value === "") return "Price unset"
  return `${currency || "CUR"} ${Number(value).toLocaleString()}`
}
