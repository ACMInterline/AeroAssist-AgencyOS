import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  queue_code: "",
  status: "",
  priority: "",
  severity: "",
  work_item_type: "",
}

export default function WorkQueueGovernancePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/work-queues${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      items: response.items || [],
      definitions: response.queue_definitions || [],
      views: response.queue_views || [],
      summary: response.summary || {},
      queues: response.queue_summary || [],
      ordering: response.ordering || {},
      generationRules: response.generation_rules || [],
    })
  }

  async function syncSelectedAgency() {
    if (!filters.agency_id) {
      setError("Select an agency before synchronizing queue metadata.")
      return
    }
    await apiPost(`/api/platform/work-queues/work-items/sync?agency_id=${filters.agency_id}`, {})
    await load(filters)
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.queue_code, filters.status, filters.priority, filters.severity, filters.work_item_type])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const metrics = [
    ["Work items", state?.summary?.work_item_count || 0],
    ["Unassigned", state?.summary?.unassigned_count || 0],
    ["Blocked", state?.summary?.blocked_count || 0],
    ["Due soon", state?.summary?.due_soon_count || 0],
    ["Overdue", state?.summary?.overdue_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Work Queue Governance</h2>
              <p className="mt-1 text-sm text-slate-600">Platform governance only. Canonical operational queue metadata for agency work. Platform can inspect queue definitions and synchronization health; assignment actions remain agency-scoped and preserve actor history.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No provider execution</span>
              <button className="rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={syncSelectedAgency}>Sync selected agency</button>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Governance filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-6">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <SelectField label="Queue" value={filters.queue_code} onChange={(value) => setFilters({ ...filters, queue_code: value })} options={(state?.queues || []).map((queue) => [queue.queue_code, queue.label])} placeholder="All queues" />
              <Field label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="Severity" value={filters.severity} onChange={(value) => setFilters({ ...filters, severity: value })} />
              <Field label="Type" value={filters.work_item_type} onChange={(value) => setFilters({ ...filters, work_item_type: value })} />
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Queue Definitions" count={state?.definitions?.length || 0}>
              {(state?.definitions || []).length ? (
                <div className="space-y-3">
                  {state.definitions.slice(0, 10).map((definition) => (
                    <RecordCard key={definition.id} title={definition.name} value={{
                      queue_code: definition.queue_code,
                      agency_id: definition.agency_id || "platform default",
                      assignment_strategy: definition.assignment_strategy,
                      is_active: definition.is_active,
                      filter_json: definition.filter_json,
                      sort_json: definition.sort_json,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No queue definitions" body="Default queue definitions are exposed by the work queue service." />}
            </Panel>
            <Panel title="Queue Rules" count={state?.generationRules?.length || 0}>
              <RecordCard title="Generation and ordering" value={{ generation_rules: state?.generationRules || [], ordering: state?.ordering || {} }} />
            </Panel>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Operational Work Items</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{state?.items?.length || 0}</span>
            </div>
            {(state?.items || []).length ? <WorkItemsTable items={state.items} showAgency /> : <EmptyState title="No queue metadata" body="Work items appear after agency work is created or synchronized." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function WorkItemsTable({ items, showAgency = false }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Work item</th>
            {showAgency ? <th className="px-4 py-3">Agency</th> : null}
            <th className="px-4 py-3">Queue</th>
            <th className="px-4 py-3">Assignment</th>
            <th className="px-4 py-3">SLA / blocker</th>
            <th className="px-4 py-3">Source</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.slice(0, 20).map((item) => (
            <tr key={item.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{item.title}</p>
                <p className="mt-1 text-xs text-slate-500">{item.work_item_code}</p>
                <p className="mt-1 text-xs text-slate-500">{formatType(item.work_item_type)} · {formatType(item.status)}</p>
              </td>
              {showAgency ? <td className="px-4 py-3 align-top text-xs text-slate-600">{item.agency_id}</td> : null}
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatType(item.queue_code)}</p>
                <p className="mt-1">Priority: {formatType(item.priority)}</p>
                <p className="mt-1">Severity: {formatType(item.severity)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>User: {item.assigned_user_id || "Unassigned"}</p>
                <p className="mt-1">Team: {item.assigned_team_code || "No team"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>SLA: {formatType(item.sla_status)}</p>
                <p className="mt-1">Blocker: {formatType(item.blocker_status)}</p>
                <p className="mt-1">Due: {formatDateTime(item.due_at)}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatType(item.source_entity_type)}</p>
                <p className="mt-1">{item.source_entity_id}</p>
                {item.source_route ? <p className="mt-1">{item.source_route}</p> : null}
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

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}
