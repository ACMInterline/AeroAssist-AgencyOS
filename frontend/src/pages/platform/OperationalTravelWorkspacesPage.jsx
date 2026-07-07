import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const typeOptions = ["general", "request", "trip", "offer", "booking", "ticketing", "documents", "disruption", "service_case"]
const statusOptions = ["draft", "open", "active", "waiting", "review", "completed", "archived"]
const priorityOptions = ["low", "medium", "high", "urgent"]

const defaultFilters = {
  agency_id: "",
  status: "",
  workspace_type: "",
  priority: "",
  assigned_agent: "",
  travel_date: "",
}

export default function PlatformOperationalTravelWorkspacesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, workspaces] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/operational-travel-workspaces${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      workspaces: workspaces.items || [],
      summary: workspaces.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.status, filters.workspace_type, filters.priority, filters.assigned_agent, filters.travel_date])

  const agencyOptions = useMemo(() => {
    return (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id])
  }, [state?.agencies])

  const metrics = [
    ["Workspaces", state?.workspaces?.length || 0],
    ["Active", state?.summary?.by_status?.active || 0],
    ["Urgent", state?.summary?.urgent_count || 0],
    ["Linked records", totalLinkedRecords(state?.summary)],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Travel Workspaces</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only operational travel workspace records. These records do not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, or automate travel operations.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Read-only UI</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No provider actions</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Workspace filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-6">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Type" value={filters.workspace_type} onChange={(value) => setFilters({ ...filters, workspace_type: value })} options={typeOptions.map((item) => [item, formatType(item)])} placeholder="All types" />
              <SelectField label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} options={priorityOptions.map((item) => [item, formatType(item)])} placeholder="All priorities" />
              <Field label="Assigned agent" value={filters.assigned_agent} onChange={(value) => setFilters({ ...filters, assigned_agent: value })} />
              <Field label="Travel date" type="date" value={filters.travel_date} onChange={(value) => setFilters({ ...filters, travel_date: value })} />
            </div>
          </section>

          {state?.workspaces?.length ? <WorkspaceList workspaces={state.workspaces} /> : <EmptyState title="No operational travel workspaces" body="Operational travel workspace metadata will appear here after platform records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function WorkspaceList({ workspaces }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Workspace</th>
            <th className="px-4 py-3">Agency</th>
            <th className="px-4 py-3">Client / passenger</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Travel</th>
            <th className="px-4 py-3">Linked records</th>
            <th className="px-4 py-3">Operational notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {workspaces.map((workspace) => (
            <tr key={workspace.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{workspace.workspace_title}</p>
                <p className="mt-1 text-xs text-slate-500">{workspace.workspace_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{formatType(workspace.workspace_type)}</p>
              </td>
              <td className="px-4 py-3 align-top text-slate-700">{workspace.agency_name || workspace.agency_id}</td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p><span className="font-semibold text-slate-700">Client:</span> {workspace.primary_client?.display_name || workspace.primary_client_id || "None"}</p>
                <p className="mt-1"><span className="font-semibold text-slate-700">Passenger:</span> {workspace.primary_passenger?.display_name || workspace.primary_passenger_id || "None"}</p>
              </td>
              <td className="px-4 py-3 align-top"><StatusBadge status={workspace.workspace_status} /></td>
              <td className="px-4 py-3 align-top"><StatusBadge status={workspace.priority} /></td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatDate(workspace.travel_start_date)} to {formatDate(workspace.travel_end_date)}</p>
                <p className="mt-1">{workspace.origin_summary || "Origin not set"} to {workspace.destination_summary || "Destination not set"}</p>
                <p className="mt-1">{workspace.service_summary || "No service summary"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Requests" items={workspace.linked_requests?.map((item) => item.label || item.request_id)} />
                <ReferenceLine label="Trips" items={workspace.linked_trips?.map((item) => item.label || item.trip_id)} />
                <ReferenceLine label="Offers" items={workspace.linked_offers?.map((item) => item.label || item.offer_id)} />
                <ReferenceLine label="Bookings" items={workspace.linked_bookings?.map((item) => item.label || item.booking_id)} />
                <ReferenceLine label="Tickets" items={workspace.linked_tickets?.map((item) => item.label || item.ticket_id)} />
                <ReferenceLine label="Documents" items={workspace.linked_documents?.map((item) => item.label || item.document_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{workspace.operational_notes || "No notes recorded"}</p>
                <p className="mt-2"><span className="font-semibold text-slate-700">Team:</span> {formatList(workspace.assigned_team)}</p>
                <p className="mt-1"><span className="font-semibold text-slate-700">Agent:</span> {workspace.assigned_agent || "Unassigned"}</p>
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
  return <p><span className="font-semibold text-slate-700">{label}:</span> {formatList(items)}</p>
}

function StatusBadge({ status }) {
  const tones = {
    active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    open: "bg-sky-50 text-sky-700 ring-sky-200",
    urgent: "bg-red-50 text-red-700 ring-red-200",
    high: "bg-amber-50 text-amber-700 ring-amber-200",
    review: "bg-violet-50 text-violet-700 ring-violet-200",
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
