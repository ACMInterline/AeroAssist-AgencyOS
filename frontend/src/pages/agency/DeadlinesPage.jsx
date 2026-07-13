import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaultFilters = {
  status: "",
  deadline_type: "",
  priority: "",
  service_family: "",
}

const statusTabs = [
  ["", "All"],
  ["due_soon", "Due Soon"],
  ["overdue", "Overdue"],
  ["paused", "Paused"],
  ["completed", "Completed"],
]

export default function DeadlinesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [reason, setReason] = useState("Deadline review")
  const [extensionDueAt, setExtensionDueAt] = useState("")
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const dashboard = await apiGet(`/api/agencies/${context.agency.id}/deadlines${query}`)
    setState({
      ...context,
      deadlines: dashboard.deadlines || [],
      summary: dashboard.summary || {},
      policies: dashboard.policies || [],
      calendars: dashboard.business_calendars || [],
      deadlineTypes: dashboard.deadline_types || [],
    })
  }

  async function reloadAfter(action) {
    await action()
    await load(filters)
  }

  async function monitorDeadlines() {
    await reloadAfter(() => apiPost(`/api/agencies/${state.agency.id}/deadlines/monitor`, {}))
  }

  async function action(deadlineId, name, body = {}) {
    await reloadAfter(() => apiPost(`/api/agencies/${state.agency.id}/deadlines/${deadlineId}/${name}`, { reason, ...body }))
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.status, filters.deadline_type, filters.priority, filters.service_family])

  const metrics = [
    ["Deadlines", state?.summary?.deadline_count || 0],
    ["Due soon", state?.summary?.due_soon_count || 0],
    ["Overdue", state?.summary?.overdue_count || 0],
    ["Paused", state?.summary?.paused_count || 0],
    ["Completed", state?.summary?.completed_count || 0],
  ]
  const typeOptions = useMemo(() => (state?.deadlineTypes || []).map((type) => [type, formatType(type)]), [state?.deadlineTypes])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Deadlines</h2>
              <p className="mt-1 text-sm text-slate-600">Agency-scoped SLA and operational deadline metadata. Deadlines explain timing, queue impact, and escalation suggestions without executing workflows, sending messages, calling providers, enforcing access, or replacing human review.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={monitorDeadlines}>Refresh states</button>
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
              {statusTabs.map(([status, label]) => (
                <button key={label} type="button" onClick={() => setFilters({ ...filters, status })} className={`rounded-md px-3 py-2 text-sm font-semibold ${filters.status === status ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}>
                  {label}
                </button>
              ))}
            </div>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Deadline type" value={filters.deadline_type} onChange={(value) => setFilters({ ...filters, deadline_type: value })} options={typeOptions} placeholder="All types" />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="Service family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
              <Field label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="grid gap-3 lg:grid-cols-[1fr_240px]">
              <Field label="Action reason" value={reason} onChange={setReason} />
              <Field label="Extension due date/time" value={extensionDueAt} onChange={setExtensionDueAt} />
            </div>
          </section>

          {(state?.deadlines || []).length ? (
            <section className="space-y-3">
              {state.deadlines.map((deadline) => (
                <DeadlineCard key={deadline.id} deadline={deadline} extensionDueAt={extensionDueAt} onAction={action} />
              ))}
            </section>
          ) : <EmptyState title="No deadline metadata" body="SLA deadlines appear after operational records or manual deadline metadata are added." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function DeadlineCard({ deadline, extensionDueAt, onAction }) {
  return (
    <details className="rounded-lg border border-slate-200 bg-white p-4" open>
      <summary className="cursor-pointer list-none">
        <div className="grid gap-3 lg:grid-cols-[1fr_190px_190px_220px]">
          <div>
            <p className="font-semibold text-slate-950">{formatType(deadline.deadline_type)}</p>
            <p className="mt-1 text-sm text-slate-600">{deadline.explanation || deadline.deadline_reference}</p>
            <p className="mt-2 text-xs text-slate-500">{deadline.deadline_reference} · {formatType(deadline.source_entity_type)} {deadline.source_entity_id}</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>Status: {formatType(deadline.status)}</p>
            <p className="mt-1">Breach: {formatType(deadline.breach_state)}</p>
            <p className="mt-1">Priority: {formatType(deadline.priority)}</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>Due: {formatDateTime(deadline.due_at)}</p>
            <p className="mt-1">Original: {formatDateTime(deadline.original_due_at)}</p>
            <p className="mt-1">Paused: {deadline.paused_duration_minutes || 0}m</p>
          </div>
          <div className="text-xs text-slate-600">
            <p>Queue SLA: {formatType(deadline.sla_status)}</p>
            <p className="mt-1">Work item: {deadline.work_item_id || "Generated/none"}</p>
            <p className="mt-1">Manual extension: {deadline.manual_extension_approved ? "Yes" : "No"}</p>
          </div>
        </div>
      </summary>
      <div className="mt-4 grid gap-4 text-xs text-slate-600 lg:grid-cols-3">
        <DetailBlock title="Escalation indicators" lines={(deadline.escalation_suggestions || []).length ? deadline.escalation_suggestions.slice(0, 4).map((suggestion) => suggestion.suggested_action || "Review manually") : ["No escalation suggestion recorded"]} />
        <DetailBlock title="SLA audit history" lines={(deadline.events || []).length ? deadline.events.map((event) => `${formatType(event.event_type)} by ${event.actor_user_id || "unknown"}: ${event.reason || "No reason"}`) : ["No SLA events yet"]} />
        <div>
          <p className="font-semibold uppercase tracking-wide text-slate-500">Manual actions</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <ActionButton label="Pause" onClick={() => onAction(deadline.id, "pause")} />
            <ActionButton label="Resume" onClick={() => onAction(deadline.id, "resume")} />
            <ActionButton label="Extend" onClick={() => onAction(deadline.id, "extend", { due_at: extensionDueAt || deadline.due_at })} />
            <ActionButton label="Recalculate" onClick={() => onAction(deadline.id, "recalculate")} />
            <ActionButton label="Complete" onClick={() => onAction(deadline.id, "complete")} />
            <ActionButton label="Waive" onClick={() => onAction(deadline.id, "waive")} />
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
        {lines.map((line, index) => <p key={`${title}-${index}`}>{line}</p>)}
      </div>
    </div>
  )
}

function formatDateTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 16) : "Unset"
}
