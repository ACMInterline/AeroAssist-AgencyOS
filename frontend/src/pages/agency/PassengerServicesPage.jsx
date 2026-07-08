import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const needCategories = ["mobility", "medical", "visual_impairment", "hearing_impairment", "cognitive", "unaccompanied_minor", "infant", "pet", "assistance_animal", "sports_equipment", "musical_instrument", "oversized_baggage", "dangerous_goods", "religious", "dietary", "seating", "security", "immigration", "documentation", "vip", "disruption", "other"]
const approvalStatuses = ["not_required", "pending", "approved", "rejected", "expired"]
const readinessStatuses = ["ready", "pending", "awaiting_airline", "awaiting_documents", "awaiting_payment", "awaiting_emd", "awaiting_medif", "awaiting_customer", "blocked"]

const defaultFilters = {
  need_category: "",
  airline: "",
  approval_status: "",
  readiness_status: "",
  passenger: "",
  priority: "",
  rfic: "",
  rfisc: "",
}

export default function PassengerServicesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [workspaces, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/ssr-osi-workspaces${query}`),
      apiGet(`/api/agencies/${context.agency.id}/ssr-osi-workspaces/summary`),
    ])
    setState({
      ...context,
      workspaces: workspaces.items || [],
      summary: workspaces.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.need_category, filters.airline, filters.approval_status, filters.readiness_status, filters.passenger, filters.priority, filters.rfic, filters.rfisc])

  const metrics = [
    ["Services", state?.workspaces?.length || 0],
    ["Ready", state?.summary?.by_readiness_status?.ready || 0],
    ["Awaiting airline", state?.summary?.by_readiness_status?.awaiting_airline || 0],
    ["Blocked", state?.summary?.by_readiness_status?.blocked || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Daily Work</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Passenger Services</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only SSR / OSI operational workspace metadata. These records show passenger needs, service requirements, SSR/OSI handling, documents, EMD references, tasks, timeline references, communications, and AOIE readiness context without live transmission, provider calls, airline APIs, AI recommendation, automatic approval, EMD issuance, or workers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No SSR/OSI transmission</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Passenger service filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-8">
              <SelectField label="Need" value={filters.need_category} onChange={(value) => setFilters({ ...filters, need_category: value })} options={needCategories.map((item) => [item, formatType(item)])} placeholder="All needs" />
              <Field label="Airline" value={filters.airline} onChange={(value) => setFilters({ ...filters, airline: value.toUpperCase() })} />
              <SelectField label="Approval" value={filters.approval_status} onChange={(value) => setFilters({ ...filters, approval_status: value })} options={approvalStatuses.map((item) => [item, formatType(item)])} placeholder="All approvals" />
              <SelectField label="Readiness" value={filters.readiness_status} onChange={(value) => setFilters({ ...filters, readiness_status: value })} options={readinessStatuses.map((item) => [item, formatType(item)])} placeholder="All readiness" />
              <Field label="Passenger" value={filters.passenger} onChange={(value) => setFilters({ ...filters, passenger: value })} />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="RFIC" value={filters.rfic} onChange={(value) => setFilters({ ...filters, rfic: value.toUpperCase() })} />
              <Field label="RFISC" value={filters.rfisc} onChange={(value) => setFilters({ ...filters, rfisc: value.toUpperCase() })} />
            </div>
          </section>

          {state?.workspaces?.length ? <WorkspaceTable workspaces={state.workspaces} /> : <EmptyState title="No passenger services" body="SSR / OSI operational service metadata will appear here after platform records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function WorkspaceTable({ workspaces }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Service workspace</th>
            <th className="px-4 py-3">Passenger need</th>
            <th className="px-4 py-3">SSR / OSI</th>
            <th className="px-4 py-3">Approval</th>
            <th className="px-4 py-3">EMD</th>
            <th className="px-4 py-3">Documents</th>
            <th className="px-4 py-3">Fulfilment</th>
            <th className="px-4 py-3">Readiness</th>
            <th className="px-4 py-3">Operational notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {workspaces.map((workspace) => (
            <tr key={workspace.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{workspace.workspace_display_name || workspace.workspace_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{workspace.workspace_reference}</p>
                <p className="mt-2 text-xs text-slate-500">Priority: {workspace.operational_priority || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatType(workspace.need_category)}</p>
                <p className="mt-1">{workspace.need_description || "Need description unset"}</p>
                <p className="mt-1">Passenger statement: {workspace.passenger_statement || "Unset"}</p>
                <p className="mt-1">Passenger: {workspace.passenger_workspace_id || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>SSR: {workspace.ssr_code || "Unset"}</p>
                <p className="mt-1">{workspace.ssr_description || "SSR description unset"}</p>
                <p className="mt-1">Confirmation: {workspace.ssr_confirmation_status || "Unset"}</p>
                <p className="mt-1">OSI required: {workspace.osi_required ? "Yes" : "No"}</p>
                <p className="mt-1">OSI: {workspace.osi_text || "Unset"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Airline: {workspace.airline_code || "Unset"}</p>
                <p className="mt-1">Approval: {formatType(workspace.approval_status)}</p>
                <p className="mt-1">Reference: {workspace.approval_reference || "Unset"}</p>
                <p className="mt-1">Deadline: {formatDate(workspace.approval_deadline)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Required: {workspace.emd_required ? "Yes" : "No"}</p>
                <p className="mt-1">RFIC/RFISC: {workspace.rfic || "Unset"} / {workspace.rfisc || "Unset"}</p>
                <ReferenceLine label="EMDs" items={workspace.emd_workspace_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Requirements" items={workspace.document_requirements} />
                <p className="mt-1">MEDIF: {workspace.medif_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Medical cert: {workspace.medical_certificate_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Veterinary: {workspace.veterinary_documents_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Customs: {workspace.customs_documents_required ? "Required" : "Not required"}</p>
                <p className="mt-1">Visa: {workspace.visa_documents_required ? "Required" : "Not required"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Tasks" items={workspace.task_ids} />
                <ReferenceLine label="Timeline" items={workspace.timeline_ids} />
                <ReferenceLine label="Comms" items={workspace.communication_ids} />
                <ReferenceLine label="Flights" items={workspace.flight_workspace_ids} />
                <ReferenceLine label="Documents" items={workspace.linked_document_ids} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <StatusBadge status={workspace.readiness_status} />
                <ReferenceLine label="Missing" items={workspace.missing_requirements} />
                <ReferenceLine label="Unresolved" items={workspace.unresolved_items} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Agent: {workspace.agent_notes || "Unset"}</p>
                <p className="mt-1">Passenger: {workspace.passenger_notes || "Unset"}</p>
                <p className="mt-1">Airline: {workspace.airline_notes || "Unset"}</p>
                <p className="mt-1">Internal: {workspace.internal_notes || "Unset"}</p>
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

function Field({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
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
  return <span className="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{formatType(status || "pending")}</span>
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

function formatList(items) {
  return (items || []).length ? items.join(", ") : "None"
}
