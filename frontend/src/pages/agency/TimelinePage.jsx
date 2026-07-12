import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const eventTypes = ["passenger_created", "passenger_updated", "travel_request_received", "offer_created", "offer_accepted", "booking_created", "ticket_linked", "emd_linked", "ssr_created", "ssr_confirmed", "osi_added", "medif_requested", "medif_received", "document_uploaded", "document_verified", "approval_requested", "approval_received", "approval_rejected", "airport_handling_confirmed", "customer_contacted", "airline_contacted", "internal_note", "task_completed", "reminder", "deadline_reached", "other"]
const communicationTypes = ["email", "phone", "chat", "letter", "meeting", "internal_note", "airline_message", "airport_message", "customer_message", "other"]

const defaultFilters = {
  passenger: "",
  booking: "",
  ticket: "",
  emd: "",
  ssr: "",
  airline: "",
  communication_type: "",
  event_type: "",
  priority: "",
  status: "",
  date: "",
}

export default function TimelinePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [timeline, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/operational-timelines${query}`),
      apiGet(`/api/agencies/${context.agency.id}/operational-timelines/summary`),
    ])
    setState({
      ...context,
      entries: timeline.items || [],
      summary: timeline.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.passenger, filters.booking, filters.ticket, filters.emd, filters.ssr, filters.airline, filters.communication_type, filters.event_type, filters.priority, filters.status, filters.date])

  const metrics = [
    ["Events", state?.entries?.length || 0],
    ["Attachments", state?.summary?.attachment_count || 0],
    ["Approvals", state?.summary?.approval_reference_count || 0],
    ["Reminders", state?.summary?.reminder_required_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Timeline</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only operational history metadata across passengers, requests, trips, bookings, tickets, EMDs, SSR / OSI records, and documents. It records communication summaries and approval history without sending messages, running AI summaries, starting workers, or calling providers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No messaging</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
            <p className="font-semibold text-slate-950">Operational workflow summary</p>
            <p className="mt-1">Workflow transition history and orchestration events are available in <a className="font-semibold text-blue-700" href="/agency/operational-workflows">Operational Workflows</a>. Timeline records stay historical metadata and no messaging or automation is triggered.</p>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Timeline filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Booking" value={filters.booking} onChange={(value) => setFilters({ ...filters, booking: value })} />
              <Field label="Ticket" value={filters.ticket} onChange={(value) => setFilters({ ...filters, ticket: value })} />
              <Field label="EMD" value={filters.emd} onChange={(value) => setFilters({ ...filters, emd: value })} />
              <Field label="SSR" value={filters.ssr} onChange={(value) => setFilters({ ...filters, ssr: value })} />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value })} />
              <SelectField label="Communication" value={filters.communication_type} onChange={(value) => setFilters({ ...filters, communication_type: value })} options={communicationTypes.map((item) => [item, formatType(item)])} placeholder="All communication" />
              <SelectField label="Event" value={filters.event_type} onChange={(value) => setFilters({ ...filters, event_type: value })} options={eventTypes.map((item) => [item, formatType(item)])} placeholder="All events" />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
              <Field label="Date" type="date" value={filters.date} onChange={(value) => setFilters({ ...filters, date: value })} />
            </div>
          </section>

          {state?.entries?.length ? <TimelineList entries={state.entries} /> : <EmptyState title="No timeline entries" body="Operational timeline metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function TimelineList({ entries }) {
  return (
    <section className="space-y-3">
      {entries.map((entry) => (
        <details key={entry.id} className="rounded-lg border border-slate-200 bg-white p-4" open>
          <summary className="cursor-pointer list-none">
            <div className="grid gap-3 md:grid-cols-[160px_1fr_180px]">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{formatDateTime(entry.created_at)}</div>
              <div>
                <p className="font-semibold text-slate-950">{entry.timeline_display_name || entry.timeline_reference}</p>
                <p className="mt-1 text-sm text-slate-600">{formatType(entry.event_type)} · {entry.event_status || "status unset"}</p>
              </div>
              <div className="text-xs text-slate-600">
                <p>Priority: {entry.event_priority || "Unset"}</p>
                <p className="mt-1">Communication: {entry.communication_type || "Unset"}</p>
              </div>
            </div>
          </summary>
          <div className="mt-4 grid gap-4 text-xs text-slate-600 lg:grid-cols-4">
            <DetailBlock title="Linked workspaces" lines={[
              `Passenger: ${entry.passenger_workspace_id || "Unset"}`,
              `Request: ${entry.travel_request_workspace_id || "Unset"}`,
              `Trip: ${entry.trip_workspace_id || "Unset"}`,
              `Booking: ${entry.booking_workspace_id || "Unset"}`,
              `Ticket: ${entry.ticket_workspace_id || "Unset"}`,
              `EMD: ${entry.emd_workspace_id || "Unset"}`,
              `SSR / OSI: ${entry.ssr_osi_workspace_id || "Unset"}`,
              `Document: ${entry.document_workspace_id || "Unset"}`,
            ]} />
            <DetailBlock title="Communication summary" lines={[
              `Direction: ${entry.communication_direction || "Unset"}`,
              `Channel: ${entry.communication_channel || "Unset"}`,
              `Sender: ${entry.sender || "Unset"}`,
              `Recipient: ${entry.recipient || "Unset"}`,
              `Subject: ${entry.subject || "Unset"}`,
              `Summary: ${entry.summary || "Unset"}`,
            ]} />
            <DetailBlock title="Approval history" lines={[
              `Reference: ${entry.approval_reference || "Unset"}`,
              `Status: ${entry.approval_status || "Unset"}`,
              `Due: ${formatDate(entry.due_date)}`,
              `Completed: ${formatDate(entry.completed_date)}`,
              `Reminder: ${entry.reminder_required ? "Required" : "No"}`,
            ]} />
            <DetailBlock title="Notes and attachments" lines={[
              `Airline: ${entry.related_airline || "Unset"}`,
              `Airport: ${entry.related_airport || "Unset"}`,
              `Attachments: ${formatList(entry.attachment_ids)}`,
              `Passenger visible: ${entry.passenger_visible ? "Yes" : "No"}`,
              `Airline visible: ${entry.airline_visible ? "Yes" : "No"}`,
              `Notes: ${entry.operational_notes || "Unset"}`,
            ]} />
          </div>
        </details>
      ))}
    </section>
  )
}

function DetailBlock({ title, lines }) {
  return (
    <div>
      <p className="font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-2 space-y-1">
        {lines.map((line) => <p key={line}>{line}</p>)}
      </div>
    </div>
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

function Field({ label, value, onChange, type = "text" }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input type={type} className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
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

function queryString(values) {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatType(value) {
  return String(value || "unset").replaceAll("_", " ")
}

function formatDate(value) {
  return value ? String(value).slice(0, 10) : "Unset"
}

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}

function formatList(items) {
  return (items || []).length ? items.join(", ") : "None"
}
