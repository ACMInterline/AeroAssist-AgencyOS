import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  trigger_event: "",
  status: "",
}

export default function TaskAutomationPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [runForm, setRunForm] = useState({ trigger_event: "request_created", source_entity_type: "request", source_entity_id: "", request_id: "", source_label: "" })
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const response = await apiGet(`/api/agencies/${context.agency.id}/task-automation${query}`)
    setState({
      ...context,
      templates: response.templates || [],
      rules: response.rules || [],
      runs: response.runs || [],
      dependencies: response.dependencies || [],
      readyTasks: response.ready_tasks || [],
      blockedTasks: response.blocked_tasks || [],
      summary: response.summary || {},
      safeTemplateCodes: response.safe_template_codes || [],
    })
  }

  async function runAutomation() {
    if (!runForm.source_entity_id) {
      setError("Source entity is required for safe metadata task automation.")
      return
    }
    await apiPost(`/api/agencies/${state.agency.id}/task-automation/runs`, {
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
    await apiPost(`/api/agencies/${state.agency.id}/task-automation/runs/${runId}/retry`, { reason: "Manual safe retry from agency workspace" })
    await load(filters)
  }

  async function updateDependency(dependencyId, action) {
    await apiPost(`/api/agencies/${state.agency.id}/task-automation/dependencies/${dependencyId}/${action}`, { reason: `Manual ${action} from agency task automation workspace` })
    await load(filters)
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.trigger_event, filters.status])

  const triggerOptions = useMemo(() => Array.from(new Set((state?.templates || []).map((template) => template.trigger_event).filter(Boolean))).map((value) => [value, formatType(value)]), [state?.templates])
  const metrics = [
    ["Runs", state?.summary?.run_count || 0],
    ["Ready tasks", state?.readyTasks?.length || 0],
    ["Blocked tasks", state?.blockedTasks?.length || 0],
    ["Created", state?.summary?.created_task_count || 0],
    ["Skipped", state?.summary?.skipped_task_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Task Automation</h2>
              <p className="mt-1 text-sm text-slate-600">Agency-scoped safe task automation metadata. Templates can create request tasks and dependencies, but no arbitrary code, provider calls, background workers, messaging, ticketing, or operational execution is performed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Human controlled</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              <SelectField label="Trigger event" value={filters.trigger_event} onChange={(value) => setFilters({ ...filters, trigger_event: value })} options={triggerOptions} placeholder="All triggers" />
              <Field label="Run status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Manual safe automation run</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <SelectField label="Trigger" value={runForm.trigger_event} onChange={(value) => setRunForm({ ...runForm, trigger_event: value })} options={triggerOptions} placeholder="Trigger" />
              <Field label="Source type" value={runForm.source_entity_type} onChange={(value) => setRunForm({ ...runForm, source_entity_type: value })} />
              <Field label="Source id" value={runForm.source_entity_id} onChange={(value) => setRunForm({ ...runForm, source_entity_id: value })} />
              <Field label="Request id" value={runForm.request_id} onChange={(value) => setRunForm({ ...runForm, request_id: value })} />
              <Field label="Label" value={runForm.source_label} onChange={(value) => setRunForm({ ...runForm, source_label: value })} />
            </div>
            <button className="mt-4 rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={runAutomation}>Create safe tasks</button>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Ready Tasks" count={state?.readyTasks?.length || 0}>
              {(state?.readyTasks || []).length ? (
                <div className="space-y-3">
                  {state.readyTasks.slice(0, 10).map((task) => <TaskCard task={task} key={task.id} />)}
                </div>
              ) : <EmptyState title="No ready tasks" body="Ready tasks appear when they are open and not blocked by predecessor dependencies." />}
            </Panel>
            <Panel title="Blocked By Dependencies" count={state?.blockedTasks?.length || 0}>
              {(state?.blockedTasks || []).length ? (
                <div className="space-y-3">
                  {state.blockedTasks.slice(0, 10).map((task) => <TaskCard task={task} key={task.id} />)}
                </div>
              ) : <EmptyState title="No blocked tasks" body="Blocked tasks appear when predecessor dependency metadata is pending." />}
            </Panel>
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
            <Panel title="Automation Runs" count={state?.runs?.length || 0}>
              {(state?.runs || []).length ? <RunTable runs={state.runs} onRetry={retryRun} /> : <EmptyState title="No automation runs" body="Safe metadata runs appear here after task creation is requested." />}
            </Panel>
            <Panel title="Dependency Graph" count={state?.dependencies?.length || 0}>
              {(state?.dependencies || []).length ? (
                <div className="space-y-3">
                  {state.dependencies.slice(0, 16).map((dependency) => <DependencyCard dependency={dependency} key={dependency.id} onAction={updateDependency} />)}
                </div>
              ) : <EmptyState title="No dependencies" body="Dependency relationships appear when generated templates include predecessor requirements." />}
            </Panel>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Task Templates" count={state?.templates?.length || 0}>
              {(state?.templates || []).length ? (
                <div className="space-y-3">
                  {state.templates.slice(0, 12).map((template) => (
                    <RecordCard key={template.id || template.template_code} title={template.title_pattern || template.template_code} value={{
                      template_code: template.template_code,
                      trigger_event: template.trigger_event,
                      priority: template.default_priority,
                      team: template.assigned_team_strategy || "unset",
                      dependencies: (template.dependency_template_codes || []).join(", ") || "none",
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No task templates" body="Default safe templates are available to this agency." />}
            </Panel>
            <Panel title="Automation Rules" count={state?.rules?.length || 0}>
              {(state?.rules || []).length ? (
                <div className="space-y-3">
                  {state.rules.slice(0, 12).map((rule) => (
                    <RecordCard key={rule.id || rule.rule_code} title={rule.name || rule.rule_code} value={{
                      rule_code: rule.rule_code,
                      trigger_event: rule.trigger_event,
                      generated_template_code: rule.generated_template_code,
                      enabled: rule.enabled ? "yes" : "no",
                      status: rule.status,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No automation rules" body="Default safe rules create existing request task metadata." />}
            </Panel>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
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

function TaskCard({ task }) {
  return (
    <div className="rounded-md border border-slate-200 p-3">
      <p className="font-medium text-slate-950">{task.title}</p>
      <p className="mt-1 text-xs text-slate-500">{task.description || "No description"}</p>
      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
        <p>Status: {formatType(task.status)}</p>
        <p>Priority: {formatType(task.priority)}</p>
        <p>Due: {formatDateTime(task.due_at)}</p>
      </div>
    </div>
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
            <th className="px-4 py-3">Retry</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {runs.slice(0, 16).map((run) => (
            <tr key={run.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{run.run_reference}</p>
                <p className="mt-1 text-xs text-slate-500">{formatType(run.status)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{formatType(run.trigger_event)}</td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Created: {(run.tasks_created || []).length}</p>
                <p className="mt-1">Skipped: {(run.tasks_skipped || []).length}</p>
              </td>
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

function DependencyCard({ dependency, onAction }) {
  return (
    <div className="rounded-md border border-slate-200 p-3 text-sm">
      <p className="font-medium text-slate-950">{dependency.predecessor_task?.title || dependency.predecessor_task_id}</p>
      <p className="mt-1 text-xs text-slate-500">blocks</p>
      <p className="mt-1 font-medium text-slate-950">{dependency.successor_task?.title || dependency.successor_task_id}</p>
      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
        <p>Status: {formatType(dependency.status)}</p>
        <p>Type: {formatType(dependency.dependency_type)}</p>
        <p>Predecessor: {dependency.predecessor_task?.status || "unknown"}</p>
        <p>Successor: {dependency.successor_task?.status || "unknown"}</p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" type="button" onClick={() => onAction(dependency.id, "satisfy")}>Satisfy</button>
        <button className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" type="button" onClick={() => onAction(dependency.id, "waive")}>Waive</button>
      </div>
    </div>
  )
}

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}
