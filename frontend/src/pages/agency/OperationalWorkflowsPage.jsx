import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const entityTypes = ["request", "trip", "booking", "service", "offer", "ticket", "emd"]

const defaultFilters = {
  entity_type: "",
  entity_id: "",
  workflow_status: "",
  current_state: "",
}

export default function OperationalWorkflowsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const dashboard = await apiGet(`/api/agencies/${context.agency.id}/operational-workflows${query}`)
    const instances = dashboard.instances || []
    const transitionPairs = await Promise.all(
      instances.slice(0, 8).map(async (instance) => {
        const response = await apiGet(`/api/agencies/${context.agency.id}/operational-workflows/instances/${instance.id}/available-transitions`)
        return [instance.id, response.available_transitions || []]
      })
    )
    setState({
      ...context,
      instances,
      summary: dashboard.summary || {},
      maps: dashboard.state_transition_maps || {},
      transitionsByInstance: Object.fromEntries(transitionPairs),
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.entity_type, filters.entity_id, filters.workflow_status, filters.current_state])

  const metrics = [
    ["Workflows", state?.summary?.instance_count || 0],
    ["Transitions", state?.summary?.transition_count || 0],
    ["Blockers", state?.summary?.active_blocker_count || 0],
    ["Warnings", state?.summary?.active_warning_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Workflows</h2>
              <p className="mt-1 text-sm text-slate-600">Shared metadata-only workflow-state and transition metadata around existing operational records. Transitions only update orchestration metadata and immutable history; they do not book, ticket, issue EMDs, message, call providers, run AI, automate work, or overwrite linked workspace statuses.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Guarded transitions</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Workflow filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Entity type" value={filters.entity_type} onChange={(value) => setFilters({ ...filters, entity_type: value })} options={entityTypes.map((item) => [item, formatType(item)])} placeholder="All entities" />
              <Field label="Entity id" value={filters.entity_id} onChange={(value) => setFilters({ ...filters, entity_id: value })} />
              <Field label="Workflow status" value={filters.workflow_status} onChange={(value) => setFilters({ ...filters, workflow_status: value })} />
              <Field label="Current state" value={filters.current_state} onChange={(value) => setFilters({ ...filters, current_state: value })} />
            </div>
          </section>

          {state?.instances?.length ? (
            <section className="space-y-3">
              {state.instances.map((instance) => (
                <WorkflowCard key={instance.id} instance={instance} transitions={state.transitionsByInstance?.[instance.id] || []} />
              ))}
            </section>
          ) : <EmptyState title="No operational workflows" body="Workflow orchestration metadata will appear here after instances are started for this agency." />}

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="font-semibold text-slate-950">State Maps</p>
            <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-50 p-3 text-xs text-slate-700">{JSON.stringify(state?.maps || {}, null, 2)}</pre>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function WorkflowCard({ instance, transitions }) {
  return (
    <details className="rounded-lg border border-slate-200 bg-white p-4" open>
      <summary className="cursor-pointer list-none">
        <div className="grid gap-3 md:grid-cols-[1fr_180px_180px]">
          <div>
            <p className="font-semibold text-slate-950">{formatType(instance.entity_type)} {instance.entity_id}</p>
            <p className="mt-1 text-sm text-slate-600">{formatType(instance.current_state)} · {formatType(instance.workflow_status)}</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>Previous: {formatType(instance.previous_state)}</p>
            <p className="mt-1">Definition: {instance.definition?.workflow_code || instance.workflow_definition_id}</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>Blockers: {(instance.active_blockers_json || []).length}</p>
            <p className="mt-1">Warnings: {(instance.active_warnings_json || []).length}</p>
          </div>
        </div>
      </summary>
      <div className="mt-4 grid gap-4 text-xs text-slate-600 lg:grid-cols-4">
        <DetailBlock title="Available next actions" lines={transitions.length ? transitions.map((transition) => `${formatType(transition.transition_code)}: ${formatType(transition.availability_status)}`) : ["No transitions available from the current state"]} />
        <DetailBlock title="Blockers" lines={(instance.active_blockers_json || []).length ? (instance.active_blockers_json || []).map((item) => `${item.guard_code || item.guard_type}: ${item.failure_message_internal || item.status}`) : ["No active blockers"]} />
        <DetailBlock title="Warnings" lines={(instance.active_warnings_json || []).length ? (instance.active_warnings_json || []).map((item) => `${item.guard_code || item.guard_type}: ${item.failure_message_internal || item.status}`) : ["No active warnings"]} />
        <DetailBlock title="Linked entity adapter" lines={[
          `Collection: ${instance.adapter?.collection || "No adapter"}`,
          `Status field: ${instance.adapter?.status_field || "Unset"}`,
          `Status sync: ${instance.adapter?.status_sync_enabled ? "Enabled" : "Disabled"}`,
          `Started: ${formatDateTime(instance.started_at)}`,
          `Completed: ${formatDateTime(instance.completed_at)}`,
        ]} />
      </div>
      <div className="mt-4 rounded-md bg-slate-50 p-3 text-xs text-slate-600">
        <p className="font-semibold text-slate-700">Transition history</p>
        <p className="mt-1">Immutable transition history is available from the orchestration API. This view does not trigger automation, provider calls, messaging, or linked status mutation.</p>
      </div>
    </details>
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

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}
