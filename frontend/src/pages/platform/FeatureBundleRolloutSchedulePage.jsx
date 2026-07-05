import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"

const scheduleStatuses = ["Planned", "Ready", "AwaitingApproval", "Approved", "Deferred", "Cancelled", "CompletedMetadata"]

const defaultForm = {
  rollout_plan_id: "",
  rollout_name: "",
  schedule_status: "Planned",
  planned_start: "",
  planned_finish: "",
  maintenance_window: "",
  estimated_duration: "",
  dependency_notes: "",
  scheduling_notes: "",
}

export default function PlatformFeatureBundleRolloutSchedulePage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaultForm)
  const [working, setWorking] = useState("")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function load(nextForm = form) {
    const [me, plans, schedules] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/platform/feature-bundle-rollout-plans"),
      apiGet("/api/platform/feature-bundle-rollout-schedule"),
    ])
    const planItems = plans.items || []
    setState({
      me,
      plans: planItems,
      schedules: schedules.items || [],
      summary: schedules.summary || {},
    })
    setForm((current) => ({
      ...current,
      ...nextForm,
      rollout_plan_id: nextForm.rollout_plan_id || current.rollout_plan_id || planItems[0]?.rollout_plan_id || "",
    }))
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function runAction(name, action) {
    setWorking(name)
    setError("")
    setMessage("")
    try {
      await action()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function createSchedule(event) {
    event.preventDefault()
    runAction("create", async () => {
      await apiPost("/api/platform/feature-bundle-rollout-schedule", schedulePayload(form))
      setMessage("Rollout schedule metadata saved. No timer, scheduler, worker, feature activation, entitlement change, permission change, billing, publishing, API call, AI action, or rollout execution occurred.")
      await load({ ...defaultForm, rollout_plan_id: form.rollout_plan_id })
    })
  }

  function updateStatus(schedule, status) {
    runAction(`${schedule.schedule_id}-${status}`, async () => {
      await apiPut(`/api/platform/feature-bundle-rollout-schedule/${schedule.schedule_id}`, {
        schedule_status: status,
        scheduling_notes: schedule.scheduling_notes || `Schedule status recorded as ${formatStatus(status)} metadata only.`,
      })
      setMessage(`Schedule status recorded as ${formatStatus(status)} metadata.`)
      await load()
    })
  }

  const statusCounts = state?.summary?.by_schedule_status || {}
  const metrics = [
    ["Schedules", state?.schedules?.length || 0],
    ["Planned", statusCounts.Planned || 0],
    ["Approved", statusCounts.Approved || 0],
    ["Deferred", statusCounts.Deferred || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Rollout Schedule</h2>
              <p className="mt-1 text-sm text-slate-600">Schedule records are metadata only. They do not execute rollouts, activate features, change entitlements, modify permissions, start cron jobs, schedulers, workers, queues, timers, call external APIs, use AI, bill, or publish automatically.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform metadata</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No timers</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No execution</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Schedule metadata</h3>
            <form className="mt-4 grid gap-3 lg:grid-cols-4" onSubmit={createSchedule}>
              <SelectField label="Rollout plan" value={form.rollout_plan_id} onChange={(value) => setForm({ ...form, rollout_plan_id: value })} options={(state?.plans || []).map((plan) => [plan.rollout_plan_id, `${plan.plan_name} · ${plan.agency_name || plan.agency_id}`])} />
              <Field label="Rollout name" value={form.rollout_name} onChange={(value) => setForm({ ...form, rollout_name: value })} />
              <SelectField label="Status" value={form.schedule_status} onChange={(value) => setForm({ ...form, schedule_status: value })} options={scheduleStatuses.map((status) => [status, formatStatus(status)])} />
              <Field label="Duration" value={form.estimated_duration} onChange={(value) => setForm({ ...form, estimated_duration: value })} placeholder="2 hours" />
              <Field label="Planned start" type="datetime-local" value={form.planned_start} onChange={(value) => setForm({ ...form, planned_start: value })} />
              <Field label="Planned finish" type="datetime-local" value={form.planned_finish} onChange={(value) => setForm({ ...form, planned_finish: value })} />
              <Field label="Maintenance window" value={form.maintenance_window} onChange={(value) => setForm({ ...form, maintenance_window: value })} />
              <Field label="Dependencies" value={form.dependency_notes} onChange={(value) => setForm({ ...form, dependency_notes: value })} />
              <label className="grid gap-1 text-sm lg:col-span-3">
                <span className="font-medium text-slate-700">Scheduling notes</span>
                <input className="rounded-md border border-slate-300 px-3 py-2" value={form.scheduling_notes} onChange={(event) => setForm({ ...form, scheduling_notes: event.target.value })} />
              </label>
              <div className="flex items-end">
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={!form.rollout_plan_id || working === "create"}>Save schedule</button>
              </div>
            </form>
          </section>

          {state?.schedules?.length ? (
            <section className="grid gap-4 xl:grid-cols-2">
              {state.schedules.map((schedule) => (
                <article className="rounded-lg border border-slate-200 bg-white p-5" key={schedule.schedule_id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{schedule.agency_name || schedule.agency_id}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{schedule.rollout_name || schedule.plan_name}</h3>
                      <p className="text-sm text-slate-600">{schedule.bundle_name || schedule.bundle_id}</p>
                    </div>
                    <StatusBadge status={schedule.schedule_status} />
                  </div>

                  <dl className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                    <Info label="Planned start" value={formatDateTime(schedule.planned_start)} />
                    <Info label="Planned finish" value={formatDateTime(schedule.planned_finish)} />
                    <Info label="Maintenance window" value={schedule.maintenance_window || "Not set"} />
                    <Info label="Duration" value={schedule.estimated_duration || "Not estimated"} />
                    <Info label="Dependencies" value={summaryText(schedule.dependency_summary)} />
                    <Info label="Notes" value={schedule.scheduling_notes || "No notes"} />
                  </dl>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {scheduleStatuses.map((status) => (
                      <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => updateStatus(schedule, status)} disabled={working === `${schedule.schedule_id}-${status}` || schedule.schedule_status === status} key={status}>{formatStatus(status)}</button>
                    ))}
                  </div>
                </article>
              ))}
            </section>
          ) : <EmptyState title="No rollout schedules" body="Create schedule metadata after rollout plans and approvals are reviewed." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function schedulePayload(form) {
  const payload = Object.fromEntries(Object.entries(form).filter(([key, value]) => value !== "" && key !== "dependency_notes"))
  if (form.dependency_notes) payload.dependency_summary = { notes: form.dependency_notes }
  return payload
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Field({ label, value, onChange, type = "text", placeholder = "" }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
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
  return String(value || "Unknown").replace(/([a-z])([A-Z])/g, "$1 $2")
}

function summaryText(value) {
  if (!value || !Object.keys(value).length) return "No dependencies"
  return value.notes || Object.entries(value).map(([key, item]) => `${key}: ${item}`).join(", ")
}

function formatDateTime(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleString()
}
