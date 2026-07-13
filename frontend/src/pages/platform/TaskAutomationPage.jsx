import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  trigger_event: "",
  status: "",
}

export default function TaskAutomationPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [runForm, setRunForm] = useState({ agency_id: "", trigger_event: "request_created", source_entity_type: "request", source_entity_id: "", request_id: "", source_label: "" })
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/task-automation${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      templates: response.templates || [],
      rules: response.rules || [],
      runs: response.runs || [],
      dependencies: response.dependencies || [],
      summary: response.summary || {},
      safeTemplateCodes: response.safe_template_codes || [],
    })
  }

  async function runAutomation() {
    if (!runForm.agency_id || !runForm.source_entity_id) {
      setError("Agency and source entity are required for a safe metadata automation run.")
      return
    }
    await apiPost("/api/platform/task-automation/runs", {
      agency_id: runForm.agency_id,
      trigger_event: runForm.trigger_event,
      source_entity_type: runForm.source_entity_type,
      source_entity_id: runForm.source_entity_id,
      request_id: runForm.request_id || runForm.source_entity_id,
      event_snapshot_json: {
        source_label: runForm.source_label || runForm.source_entity_id,
        request_id: runForm.request_id || runForm.source_entity_id,
      },
    })
    await load(filters)
  }

  async function retryRun(runId) {
    await apiPost(`/api/platform/task-automation/runs/${runId}/retry`, { reason: "Manual safe retry from platform governance" })
    await load(filters)
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.trigger_event, filters.status])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const triggerOptions = useMemo(() => Array.from(new Set((state?.templates || []).map((template) => template.trigger_event).filter(Boolean))).map((value) => [value, formatType(value)]), [state?.templates])
  const metrics = [
    ["Runs", state?.summary?.run_count || 0],
    ["Created tasks", state?.summary?.created_task_count || 0],
    ["Skipped tasks", state?.summary?.skipped_task_count || 0],
    ["Dependencies", state?.summary?.dependency_count || 0],
    ["Blocked", state?.summary?.blocked_dependency_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Task Automation</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only task templates, dependencies, and safe task creation on top of existing request tasks. This does not execute providers, run arbitrary code, schedule workers, send messages, or replace human authority.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Existing tasks reused</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Governance filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-3">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Trigger event" value={filters.trigger_event} onChange={(value) => setFilters({ ...filters, trigger_event: value })} options={triggerOptions} placeholder="All triggers" />
              <Field label="Run status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Safe metadata run</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-6">
              <SelectField label="Agency" value={runForm.agency_id} onChange={(value) => setRunForm({ ...runForm, agency_id: value })} options={agencyOptions} placeholder="Choose agency" />
              <SelectField label="Trigger" value={runForm.trigger_event} onChange={(value) => setRunForm({ ...runForm, trigger_event: value })} options={triggerOptions} placeholder="Trigger" />
              <Field label="Source type" value={runForm.source_entity_type} onChange={(value) => setRunForm({ ...runForm, source_entity_type: value })} />
              <Field label="Source id" value={runForm.source_entity_id} onChange={(value) => setRunForm({ ...runForm, source_entity_id: value })} />
              <Field label="Request id" value={runForm.request_id} onChange={(value) => setRunForm({ ...runForm, request_id: value })} />
              <Field label="Label" value={runForm.source_label} onChange={(value) => setRunForm({ ...runForm, source_label: value })} />
            </div>
            <button className="mt-4 rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={runAutomation}>Create safe tasks</button>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Task Templates" count={state?.templates?.length || 0}>
              {(state?.templates || []).length ? (
                <div className="space-y-3">
                  {state.templates.slice(0, 14).map((template) => (
                    <RecordCard key={template.id || template.template_code} title={template.title_pattern || template.template_code} value={{
                      template_code: template.template_code,
                      trigger_event: template.trigger_event,
                      priority: template.default_priority,
                      assigned_team: template.assigned_team_strategy || "unset",
                      dependencies: (template.dependency_template_codes || []).join(", ") || "none",
                      status: template.status,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No task templates" body="Default safe task templates are exposed by the service." />}
            </Panel>
            <Panel title="Automation Rules" count={state?.rules?.length || 0}>
              {(state?.rules || []).length ? (
                <div className="space-y-3">
                  {state.rules.slice(0, 14).map((rule) => (
                    <RecordCard key={rule.id || rule.rule_code} title={rule.name || rule.rule_code} value={{
                      rule_code: rule.rule_code,
                      trigger_event: rule.trigger_event,
                      generated_template_code: rule.generated_template_code,
                      enabled: rule.enabled ? "yes" : "no",
                      status: rule.status,
                      deduplication: rule.deduplication_key_pattern,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No automation rules" body="Default rules create metadata-only request tasks." />}
            </Panel>
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
            <Panel title="Automation Runs" count={state?.runs?.length || 0}>
              {(state?.runs || []).length ? <RunTable runs={state.runs} onRetry={retryRun} /> : <EmptyState title="No automation runs" body="Safe metadata runs appear here after task creation is requested." />}
            </Panel>
            <Panel title="Task Dependencies" count={state?.dependencies?.length || 0}>
              {(state?.dependencies || []).length ? (
                <div className="space-y-3">
                  {state.dependencies.slice(0, 16).map((dependency) => <DependencyCard dependency={dependency} key={dependency.id} />)}
                </div>
              ) : <EmptyState title="No dependencies" body="Dependency records appear when generated task templates reference predecessor templates." />}
            </Panel>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Panel({ title, count, children }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{count}</span>
      </div>
      {children}
    </section>
  )
}

function RunTable({ runs, onRetry }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Run</th>
            <th className="px-4 py-3">Trigger</th>
            <th className="px-4 py-3">Tasks</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Retry</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {runs.slice(0, 20).map((run) => (
            <tr key={run.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{run.run_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{run.source_entity_type} {run.source_entity_id}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{formatType(run.trigger_event)}</td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Created: {(run.tasks_created || []).length}</p>
                <p className="mt-1">Skipped: {(run.tasks_skipped || []).length}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{formatType(run.status)}</td>
              <td className="px-4 py-3 align-top">
                <button className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" type="button" onClick={() => onRetry(run.id)}>Retry safely</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function DependencyCard({ dependency }) {
  return (
    <div className="rounded-md border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-950">{dependency.predecessor_task?.title || dependency.predecessor_task_id}</p>
      <p className="mt-1 text-xs text-slate-500">blocks</p>
      <p className="mt-1 font-medium text-slate-950">{dependency.successor_task?.title || dependency.successor_task_id}</p>
      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
        <p>Type: {formatType(dependency.dependency_type)}</p>
        <p>Status: {formatType(dependency.status)}</p>
        <p>Predecessor: {dependency.predecessor_task?.status || "unknown"}</p>
        <p>Successor: {dependency.successor_task?.status || "unknown"}</p>
      </div>
    </div>
  )
}
