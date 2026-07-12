import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const entityTypes = ["request", "trip", "booking", "service", "offer", "ticket", "emd"]

const defaultFilters = {
  agency_id: "",
  entity_type: "",
  workflow_status: "",
  current_state: "",
}

export default function OperationalWorkflowsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/operational-workflows${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      definitions: response.definitions || [],
      instances: response.instances || [],
      guards: response.guards || [],
      summary: response.summary || {},
      maps: response.state_transition_maps || {},
      diagnostics: response.diagnostics || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.entity_type, filters.workflow_status, filters.current_state])

  const metrics = [
    ["Definitions", state?.summary?.definition_count || 0],
    ["Defaults", state?.summary?.default_definition_count || Object.keys(state?.maps || {}).length],
    ["Instances", state?.summary?.instance_count || 0],
    ["Transitions", state?.summary?.transition_count || 0],
    ["Active blockers", state?.summary?.active_blocker_count || 0],
  ]
  const agencyOptions = (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id])

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Operational Workflows</h2>
              <p className="mt-1 text-sm text-slate-600">Canonical workflow-state and guarded-transition metadata around existing request, trip, offer, booking, ticket, EMD, document, timeline, and passenger-service workflow foundations. It does not replace those workspaces, run automation, call providers, or overwrite entity statuses without explicit future adapters.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Guarded transitions</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No status overwrite</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Workflow filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Entity type" value={filters.entity_type} onChange={(value) => setFilters({ ...filters, entity_type: value })} options={entityTypes.map((item) => [item, formatType(item)])} placeholder="All entities" />
              <Field label="Workflow status" value={filters.workflow_status} onChange={(value) => setFilters({ ...filters, workflow_status: value })} />
              <Field label="Current state" value={filters.current_state} onChange={(value) => setFilters({ ...filters, current_state: value })} />
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Workflow Definitions" count={state?.definitions?.length || 0}>
              {(state?.definitions || []).length ? (
                <div className="space-y-3">
                  {state.definitions.slice(0, 8).map((definition) => (
                    <RecordCard key={definition.id} title={definition.name} value={{
                      code: definition.workflow_code,
                      entity_type: definition.entity_type,
                      version: definition.version,
                      status: definition.status,
                      initial_state: definition.initial_state,
                      terminal_states: definition.terminal_states,
                      state_count: definition.state_count,
                      transition_count: definition.transition_count,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No workflow definitions" body="Platform workflow definitions and safe defaults will appear here." />}
            </Panel>

            <Panel title="Guard Configuration Summary" count={state?.guards?.length || 0}>
              {(state?.guards || []).length ? (
                <div className="space-y-3">
                  {state.guards.slice(0, 8).map((guard) => (
                    <RecordCard key={guard.id} title={guard.guard_code} value={{
                      transition: guard.transition_code,
                      guard_type: guard.guard_type,
                      severity: guard.severity,
                      evaluation_mode: guard.evaluation_mode,
                      active: guard.is_active,
                      remediation: guard.remediation_guidance,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No guard definitions" body="Guard metadata appears after platform definitions add transition checks." />}
            </Panel>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Workflow Instances</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{state?.instances?.length || 0}</span>
            </div>
            {(state?.instances || []).length ? <InstanceTable instances={state.instances} /> : <EmptyState title="No workflow instances" body="Workflow orchestration instances will appear after an agency starts metadata orchestration around an entity." />}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <RecordCard title="State And Transition Maps" value={state?.maps || {}} />
            <RecordCard title="Diagnostics And Safety" value={{
              guard_results: state?.diagnostics?.guard_results,
              guard_types: state?.diagnostics?.guard_types,
              entity_status_sync_disabled_by_default: state?.diagnostics?.entity_status_sync_disabled_by_default,
              unrestricted_dynamic_mutation_disabled: state?.diagnostics?.unrestricted_dynamic_mutation_disabled,
              provider_integrations_disabled: state?.diagnostics?.provider_integrations_disabled,
              automation_disabled: state?.diagnostics?.automation_disabled,
            }} />
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function InstanceTable({ instances }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Entity</th>
            <th className="px-4 py-3">State</th>
            <th className="px-4 py-3">Definition</th>
            <th className="px-4 py-3">Blockers</th>
            <th className="px-4 py-3">Warnings</th>
            <th className="px-4 py-3">Adapter</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {instances.slice(0, 12).map((instance) => (
            <tr key={instance.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{formatType(instance.entity_type)}</p>
                <p className="mt-1 text-xs text-slate-500">{instance.entity_id}</p>
                <p className="mt-1 text-xs text-slate-500">{instance.agency_id}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Current: {formatType(instance.current_state)}</p>
                <p className="mt-1">Previous: {formatType(instance.previous_state)}</p>
                <p className="mt-1">Status: {formatType(instance.workflow_status)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{instance.definition?.name || instance.workflow_definition_id}</p>
                <p className="mt-1">{instance.definition?.workflow_code || "Definition metadata"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{(instance.active_blockers_json || []).length}</td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{(instance.active_warnings_json || []).length}</td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{instance.adapter?.collection || "No adapter"}</p>
                <p className="mt-1">Status sync: {instance.adapter?.status_sync_enabled ? "Enabled" : "Disabled"}</p>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function Panel({ title, count, children }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{count}</span>
      </div>
      {children}
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

function RecordCard({ title, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="font-semibold text-slate-950">{title}</p>
      <pre className="mt-3 max-h-72 overflow-auto rounded-md bg-slate-50 p-3 text-xs text-slate-700">{JSON.stringify(value, null, 2)}</pre>
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
