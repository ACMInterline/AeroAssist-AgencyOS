import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RolloutSchedulePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const [schedules, summary] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-schedule`),
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-schedule/summary`),
      ])
      setState({
        ...context,
        schedules: schedules.items || [],
        summary: summary.summary || schedules.summary || {},
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const statusCounts = state?.summary?.by_schedule_status || {}
  const metrics = [
    ["Schedules", state?.schedules?.length || 0],
    ["Planned", statusCounts.Planned || 0],
    ["Approved", statusCounts.Approved || 0],
    ["Deferred", statusCounts.Deferred || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rollout Schedule</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only rollout schedule metadata. It does not execute rollouts, activate features, change entitlements, modify permissions, start timers, call external APIs, use AI, bill, or publish automatically.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          {state?.schedules?.length ? (
            <section className="grid gap-4 xl:grid-cols-2">
              {state.schedules.map((schedule) => (
                <article className="rounded-lg border border-slate-200 bg-white p-5" key={schedule.schedule_id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{schedule.bundle_name || schedule.bundle_id}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{schedule.rollout_name || schedule.plan_name}</h3>
                      <p className="text-sm text-slate-600">{schedule.schedule_id}</p>
                    </div>
                    <StatusBadge status={schedule.schedule_status} />
                  </div>

                  <dl className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                    <Info label="Planned start" value={formatDateTime(schedule.planned_start)} />
                    <Info label="Planned finish" value={formatDateTime(schedule.planned_finish)} />
                    <Info label="Maintenance window" value={schedule.maintenance_window || "Not set"} />
                    <Info label="Duration" value={schedule.estimated_duration || "Not estimated"} />
                    <Info label="Dependencies" value={summaryText(schedule.dependency_summary)} />
                    <Info label="Approval" value={formatStatus(schedule.approval_summary?.latest_status || "Not approved")} />
                    <Info label="Plan stage" value={formatStatus(schedule.rollout_stage)} />
                    <Info label="Owner" value={schedule.rollout_owner || "Platform metadata"} />
                    <Info label="Notes" value={schedule.scheduling_notes || "No schedule notes"} />
                  </dl>
                </article>
              ))}
            </section>
          ) : <EmptyState title="No rollout schedule" body="Platform rollout schedule metadata will appear here after intended timing is recorded." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
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

function Info({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-slate-700">{value || "Not set"}</dd>
    </div>
  )
}

function StatusBadge({ status }) {
  const tones = {
    Approved: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    Ready: "bg-blue-50 text-blue-700 ring-blue-200",
    AwaitingApproval: "bg-sky-50 text-sky-700 ring-sky-200",
    Deferred: "bg-amber-50 text-amber-700 ring-amber-200",
    Cancelled: "bg-red-50 text-red-700 ring-red-200",
    CompletedMetadata: "bg-slate-100 text-slate-600 ring-slate-200",
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[status] || "bg-indigo-50 text-indigo-700 ring-indigo-200"}`}>{formatStatus(status)}</span>
}

function formatStatus(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/([a-z])([A-Z])/g, "$1 $2")
}

function summaryText(value) {
  if (!value || !Object.keys(value).length) return "No dependencies"
  return value.notes || Object.entries(value).map(([key, item]) => `${key}: ${item}`).join(", ")
}

function formatDateTime(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleString()
}
