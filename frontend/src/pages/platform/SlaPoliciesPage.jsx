import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  status: "",
  deadline_type: "",
  priority: "",
  service_family: "",
}

export default function SlaPoliciesPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/sla-policies${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      deadlines: response.deadlines || [],
      policies: response.policies || [],
      calendars: response.business_calendars || [],
      summary: response.summary || {},
      deadlineTypes: response.deadline_types || [],
    })
  }

  async function monitorSelectedAgency() {
    const query = filters.agency_id ? `?agency_id=${encodeURIComponent(filters.agency_id)}` : ""
    await apiPost(`/api/platform/sla-policies/deadlines/monitor${query}`, {})
    await load(filters)
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.status, filters.deadline_type, filters.priority, filters.service_family])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const typeOptions = useMemo(() => (state?.deadlineTypes || []).map((type) => [type, formatType(type)]), [state?.deadlineTypes])
  const metrics = [
    ["Deadlines", state?.summary?.deadline_count || 0],
    ["Due soon", state?.summary?.due_soon_count || 0],
    ["Overdue", state?.summary?.overdue_count || 0],
    ["Paused", state?.summary?.paused_count || 0],
    ["Completed", state?.summary?.completed_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">SLA Policies</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only SLA policy and deadline governance. Calculations explain due dates and sync queue visibility, but they do not enforce routes, send messages, call providers, schedule workers, or execute operational actions.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white" type="button" onClick={monitorSelectedAgency}>Refresh deadline states</button>
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No automation</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Governance filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
              <SelectField label="Deadline type" value={filters.deadline_type} onChange={(value) => setFilters({ ...filters, deadline_type: value })} options={typeOptions} placeholder="All types" />
              <Field label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} />
              <Field label="Service family" value={filters.service_family} onChange={(value) => setFilters({ ...filters, service_family: value })} />
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="SLA Policies" count={state?.policies?.length || 0}>
              {(state?.policies || []).length ? (
                <div className="space-y-3">
                  {state.policies.slice(0, 12).map((policy) => (
                    <RecordCard key={policy.id || policy.policy_code} title={policy.name} value={{
                      policy_code: policy.policy_code,
                      agency_id: policy.agency_id || "platform default",
                      deadline_type: policy.deadline_type,
                      entity_type: policy.entity_type,
                      work_item_type: policy.work_item_type,
                      duration: `${policy.duration_value} ${policy.duration_unit}`,
                      business_hours_behavior: policy.business_hours_behavior,
                      status: policy.status,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No SLA policies" body="Default SLA policies are exposed by the deadline service." />}
            </Panel>
            <Panel title="Business Calendars" count={state?.calendars?.length || 0}>
              {(state?.calendars || []).length ? (
                <div className="space-y-3">
                  {state.calendars.slice(0, 12).map((calendar) => (
                    <RecordCard key={calendar.id || calendar.calendar_code} title={calendar.name} value={{
                      calendar_code: calendar.calendar_code,
                      agency_id: calendar.agency_id || "platform default",
                      timezone: calendar.timezone,
                      working_days: calendar.working_days,
                      working_hours: calendar.working_hours_json,
                      holidays: calendar.holidays,
                      status: calendar.status,
                    }} />
                  ))}
                </div>
              ) : <EmptyState title="No calendars" body="Default business calendar metadata is available." />}
            </Panel>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-950">Operational Deadlines</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{state?.deadlines?.length || 0}</span>
            </div>
            {(state?.deadlines || []).length ? <DeadlinesTable deadlines={state.deadlines} showAgency /> : <EmptyState title="No deadline metadata" body="Deadlines appear when agencies or platform governance create SLA deadline records." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function DeadlinesTable({ deadlines, showAgency = false }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Deadline</th>
            {showAgency ? <th className="px-4 py-3">Agency</th> : null}
            <th className="px-4 py-3">Due / status</th>
            <th className="px-4 py-3">Source</th>
            <th className="px-4 py-3">Policy explanation</th>
            <th className="px-4 py-3">Escalation</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {deadlines.slice(0, 24).map((deadline) => (
            <tr key={deadline.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{formatType(deadline.deadline_type)}</p>
                <p className="mt-1 text-xs text-slate-500">{deadline.deadline_reference}</p>
                <p className="mt-1 text-xs text-slate-500">Priority: {formatType(deadline.priority)}</p>
              </td>
              {showAgency ? <td className="px-4 py-3 align-top text-xs text-slate-600">{deadline.agency_id}</td> : null}
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>Due: {formatDateTime(deadline.due_at)}</p>
                <p className="mt-1">Status: {formatType(deadline.status)}</p>
                <p className="mt-1">Breach: {formatType(deadline.breach_state)}</p>
                <p className="mt-1">Paused: {deadline.paused_duration_minutes || 0}m</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p>{formatType(deadline.source_entity_type)}</p>
                <p className="mt-1">{deadline.source_entity_id}</p>
                <p className="mt-1">Work item: {deadline.work_item_id || "Generated/none"}</p>
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{deadline.explanation || "No explanation recorded"}</td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                {(deadline.escalation_suggestions || []).slice(0, 2).map((suggestion, index) => (
                  <p className="mb-1" key={`${deadline.id}-${index}`}>{suggestion.suggested_action || "Review manually"}</p>
                ))}
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
