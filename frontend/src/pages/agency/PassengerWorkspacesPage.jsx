import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statusOptions = ["draft", "active", "incomplete", "review", "ready", "archived"]

const defaultFilters = {
  status: "",
  nationality: "",
  citizenship: "",
  assistance_profile: "",
  travel_date: "",
  operational_workspace_id: "",
}

export default function PassengerWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [passengers, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/passenger-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/passenger-workspaces/summary`),
    ])
    setState({
      ...context,
      passengers: passengers.items || [],
      summary: passengers.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.status, filters.nationality, filters.citizenship, filters.assistance_profile, filters.travel_date, filters.operational_workspace_id])

  const metrics = [
    ["Passengers", state?.passengers?.length || 0],
    ["Active", state?.summary?.by_status?.active || 0],
    ["Ready", state?.summary?.by_status?.ready || 0],
    ["Linked records", totalLinkedRecords(state?.summary)],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Daily Work</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Passengers</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only passenger workspace metadata. These records do not execute bookings, issue tickets, connect to GDS or NDC, process payments, integrate suppliers, use AI, send email or SMS, run background workers, call external APIs, automatically match profiles, automatically validate documents, or communicate with airlines.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No document validation</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Passenger filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-6">
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <Field label="Nationality" value={filters.nationality} onChange={(value) => setFilters({ ...filters, nationality: value })} />
              <Field label="Citizenship" value={filters.citizenship} onChange={(value) => setFilters({ ...filters, citizenship: value })} />
              <Field label="Assistance" value={filters.assistance_profile} onChange={(value) => setFilters({ ...filters, assistance_profile: value })} />
              <Field label="Travel date" type="date" value={filters.travel_date} onChange={(value) => setFilters({ ...filters, travel_date: value })} />
              <Field label="Workspace" value={filters.operational_workspace_id} onChange={(value) => setFilters({ ...filters, operational_workspace_id: value })} />
            </div>
          </section>

          {state?.passengers?.length ? <PassengerList passengers={state.passengers} /> : <EmptyState title="No passenger workspaces" body="Passenger workspace metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function PassengerList({ passengers }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Passenger</th>
            <th className="px-4 py-3">Personal information</th>
            <th className="px-4 py-3">Travel documents</th>
            <th className="px-4 py-3">Loyalty</th>
            <th className="px-4 py-3">Profiles</th>
            <th className="px-4 py-3">Preferences</th>
            <th className="px-4 py-3">Linked records</th>
            <th className="px-4 py-3">Internal notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {passengers.map((passenger) => (
            <tr key={passenger.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{passenger.display_name || passenger.passenger_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{passenger.passenger_reference}</p>
                <p className="mt-1"><StatusBadge status={passenger.passenger_status} /></p>
                <p className="mt-2 text-xs text-slate-500">{passenger.operational_workspace?.workspace_title || passenger.operational_workspace_id || "No assigned workspace"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatName(passenger)}</p>
                <p className="mt-1">DOB: {formatDate(passenger.date_of_birth)}</p>
                <p className="mt-1">Gender: {passenger.gender || "Unset"}</p>
                <p className="mt-1">{passenger.nationality || "Nationality unset"} / {passenger.citizenship || "Citizenship unset"}</p>
                <p className="mt-1">{passenger.contact_email || "No email"} / {passenger.contact_phone || "No phone"}</p>
                <ProfileLine label="Emergency" value={passenger.emergency_contact} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{passenger.identity_document_type || "Document type unset"}</p>
                <p className="mt-1">{passenger.passport_number || "Passport unset"}</p>
                <p className="mt-1">{passenger.passport_country || "Country unset"} exp {formatDate(passenger.passport_expiry)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Programs" items={passenger.loyalty_programs?.map(formatRecord)} />
                <ReferenceLine label="FF numbers" items={passenger.frequent_flyer_numbers?.map(formatRecord)} />
                <ReferenceLine label="Known traveler" items={passenger.known_traveler_numbers} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ProfileLine label="Medical" value={passenger.medical_profile} />
                <ProfileLine label="Mobility" value={passenger.mobility_profile} />
                <ProfileLine label="Assistance" value={passenger.assistance_profile} />
                <ProfileLine label="Dietary" value={passenger.dietary_profile} />
                <ProfileLine label="Baggage" value={passenger.baggage_profile} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ProfileLine label="Seating" value={passenger.seating_preferences} />
                <ReferenceLine label="Languages" items={passenger.language_preferences} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Requests" items={passenger.linked_requests?.map((item) => item.label || item.request_id)} />
                <ReferenceLine label="Trips" items={passenger.linked_trips?.map((item) => item.label || item.trip_id)} />
                <ReferenceLine label="Offers" items={passenger.linked_offers?.map((item) => item.label || item.offer_id)} />
                <ReferenceLine label="Bookings" items={passenger.linked_bookings?.map((item) => item.label || item.booking_id)} />
                <ReferenceLine label="Tickets" items={passenger.linked_tickets?.map((item) => item.label || item.ticket_id)} />
                <ReferenceLine label="Documents" items={passenger.linked_documents?.map((item) => item.label || item.document_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{passenger.internal_notes || "No notes recorded"}</td>
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
  return <p><span className="font-semibold text-slate-700">{label}:</span> {formatList(items)}</p>
}

function ProfileLine({ label, value }) {
  return <p className="mt-1"><span className="font-semibold text-slate-700">{label}:</span> {formatRecord(value)}</p>
}

function StatusBadge({ status }) {
  const tones = {
    active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    ready: "bg-sky-50 text-sky-700 ring-sky-200",
    review: "bg-violet-50 text-violet-700 ring-violet-200",
    incomplete: "bg-amber-50 text-amber-700 ring-amber-200",
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

function totalLinkedRecords(summary) {
  return [
    "linked_request_count",
    "linked_trip_count",
    "linked_offer_count",
    "linked_booking_count",
    "linked_ticket_count",
    "linked_document_count",
  ].reduce((total, key) => total + (summary?.[key] || 0), 0)
}

function formatName(passenger) {
  return [passenger.title, passenger.first_name, passenger.middle_name, passenger.last_name].filter(Boolean).join(" ") || passenger.preferred_name || "Name not set"
}

function formatRecord(value) {
  if (!value) return "None"
  if (Array.isArray(value)) return formatList(value.map(formatRecord))
  if (typeof value === "object") {
    const entries = Object.entries(value).filter(([, entryValue]) => entryValue !== null && entryValue !== undefined && entryValue !== "")
    return entries.length ? entries.map(([key, entryValue]) => `${formatType(key)}: ${entryValue}`).join(", ") : "None"
  }
  return String(value)
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
