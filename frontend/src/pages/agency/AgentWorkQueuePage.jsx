import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const queueTabs = [
  ["unassigned", "Unassigned"],
  ["my_work", "My Work"],
  ["team_queue", "Team"],
  ["urgent_critical", "Urgent"],
  ["due_soon", "Due Soon"],
  ["overdue", "Overdue"],
  ["blocked", "Blocked"],
  ["waiting_client", "Waiting Client"],
  ["waiting_documents", "Documents"],
  ["knowledge_gap_queue", "Knowledge"],
  ["workflow_blocker_queue", "Workflow Blockers"],
]

const defaultFilters = {
  queue_code: "unassigned",
  status: "",
  priority: "",
  severity: "",
  work_item_type: "",
  assigned_team_code: "",
}

export default function AgentWorkQueuePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [selectedIds, setSelectedIds] = useState([])
  const [reason, setReason] = useState("Queue review")
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const dashboard = await apiGet(`/api/agencies/${context.agency.id}/work-queue${query}`)
    setState({
      ...context,
      items: dashboard.items || [],
      summary: dashboard.summary || {},
      queues: dashboard.queue_summary || [],
      definitions: dashboard.queue_definitions || [],
      views: dashboard.queue_views || [],
      ordering: dashboard.ordering || {},
    })
  }

  async function reloadAfter(action) {
    await action()
    await load(filters)
  }

  async function syncQueue() {
    await reloadAfter(() => apiPost(`/api/agencies/${state.agency.id}/work-queue/work-items/sync`, {}))
  }

  async function action(workItemId, name, body = {}) {
    await reloadAfter(() => apiPost(`/api/agencies/${state.agency.id}/work-queue/work-items/${workItemId}/${name}`, { reason, ...body }))
  }

  async function bulkAssignSelf() {
    await reloadAfter(() => apiPost(`/api/agencies/${state.agency.id}/work-queue/work-items/bulk-assign`, {
      work_item_ids: selectedIds,
      to_user_id: state.me.user.id,
      reason,
      only_unassigned: true,
    }))
    setSelectedIds([])
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.queue_code, filters.status, filters.priority, filters.severity, filters.work_item_type, filters.assigned_team_code])

  const metrics = [
    ["Open", state?.summary?.work_item_count || 0],
    ["Unassigned", state?.summary?.unassigned_count || 0],
    ["Blocked", state?.summary?.blocked_count || 0],
    ["Due soon", state?.summary?.due_soon_count || 0],
    ["Overdue", state?.summary?.overdue_count || 0],
  ]
  const queueOptions = useMemo(() => (state?.queues || []).map((queue) => [queue.queue_code, queue.label]), [state?.queues])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Agent Work Queue</h2>
              <p className="mt-1 text-sm text-slate-600">Canonical agency queue for actionable operational work. It links to existing requests, workflows, tasks, timelines, documents, bookings, and readiness issues without creating bookings, sending messages, calling providers, or replacing human authority.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={syncQueue}>Sync work</button>
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Agency scoped</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap gap-2">
              {queueTabs.map(([code, label]) => (
                <button key={code} type="button" onClick={() => setFilters({ ...filters, queue_code: code })} className={`rounded-md px-3 py-2 text-sm font-semibold ${filters.queue_code === code ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}>
                  {label}
                </button>
              ))}
            </div>
            <div className="mt-4 grid gap-3 lg:grid-cols-6">
              <SelectField label="Queue" value={filters.queue_code} onChange={(value) => setFilters({ ...filters, queue_code: value })} options={queueOptions} placeholder="All queues" />
              <Field label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="Severity" value={filters.severity} onChange={(value) => setFilters({ ...filters, severity: value })} />
              <Field label="Type" value={filters.work_item_type} onChange={(value) => setFilters({ ...filters, work_item_type: value })} />
              <Field label="Team" value={filters.assigned_team_code} onChange={(value) => setFilters({ ...filters, assigned_team_code: value })} />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
              <Field label="Action reason" value={reason} onChange={setReason} />
              <button className="self-end rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300" type="button" disabled={!selectedIds.length} onClick={bulkAssignSelf}>Bulk assign to me</button>
            </div>
          </section>

          {(state?.items || []).length ? (
            <section className="space-y-3">
              {state.items.map((item) => (
                <WorkItemCard
                  key={item.id}
                  item={item}
                  selected={selectedIds.includes(item.id)}
                  onSelect={(checked) => setSelectedIds((ids) => checked ? [...new Set([...ids, item.id])] : ids.filter((id) => id !== item.id))}
                  onAction={action}
                />
              ))}
            </section>
          ) : <EmptyState title="No work items" body="Use Sync work to create idempotent queue metadata from existing operational records." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function WorkItemCard({ item, selected, onSelect, onAction }) {
  return (
    <details className="rounded-lg border border-slate-200 bg-white p-4" open>
      <summary className="cursor-pointer list-none">
        <div className="grid gap-3 lg:grid-cols-[24px_1fr_180px_180px_200px]">
          <input className="mt-1" type="checkbox" checked={selected} onChange={(event) => onSelect(event.target.checked)} />
          <div>
            <p className="font-semibold text-slate-950">{item.title}</p>
            <p className="mt-1 text-sm text-slate-600">{item.summary || item.work_item_code}</p>
            <p className="mt-2 text-xs text-slate-500">{formatType(item.work_item_type)} · {formatType(item.source_entity_type)} {item.source_entity_id}</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>Status: {formatType(item.status)}</p>
            <p className="mt-1">Priority: {formatType(item.priority)}</p>
            <p className="mt-1">Severity: {formatType(item.severity)}</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>Assigned: {item.assigned_user_id || "Unassigned"}</p>
            <p className="mt-1">Team: {item.assigned_team_code || "No team"}</p>
            <p className="mt-1">Due: {formatDateTime(item.due_at)}</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>SLA: {formatType(item.sla_status)}</p>
            <p className="mt-1">Blocker: {formatType(item.blocker_status)}</p>
            <p className="mt-1">{item.source_route || "No route link"}</p>
          </div>
        </div>
      </summary>
      <div className="mt-4 grid gap-4 text-xs text-slate-600 lg:grid-cols-3">
        <DetailBlock title="Source linkage" lines={[
          `Workflow: ${item.workflow_instance_id || "None"}`,
          `Workflow event: ${item.workflow_event_id || "None"}`,
          `Request task: ${item.request_task_id || "None"}`,
          `Timeline: ${item.timeline_entry_id || "None"}`,
        ]} />
        <DetailBlock title="Compact history" lines={(item.assignment_events || []).length ? item.assignment_events.map((event) => `${formatType(event.event_type)} by ${event.actor_user_id || "unknown"}: ${event.reason || "No reason"}`) : ["No assignment history yet"]} />
        <div>
          <p className="font-semibold uppercase tracking-wide text-slate-500">Assignment actions</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <ActionButton label="Assign to me" onClick={() => onAction(item.id, "assign-self")} />
            <ActionButton label="Accept" onClick={() => onAction(item.id, "accept")} />
            <ActionButton label="In progress" onClick={() => onAction(item.id, "in-progress")} />
            <ActionButton label="Block" onClick={() => onAction(item.id, "block", { blocker_status: "blocked" })} />
            <ActionButton label="Complete" onClick={() => onAction(item.id, "complete")} />
            <ActionButton label="Reopen" onClick={() => onAction(item.id, "reopen")} />
            <ActionButton label="Release" onClick={() => onAction(item.id, "release")} />
          </div>
        </div>
      </div>
    </details>
  )
}

function ActionButton({ label, onClick }) {
  return <button className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50" type="button" onClick={onClick}>{label}</button>
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

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}
