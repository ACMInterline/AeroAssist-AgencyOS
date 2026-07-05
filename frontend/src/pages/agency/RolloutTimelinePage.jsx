import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const eventTypes = [
  "plan_created",
  "plan_edited",
  "approval_requested",
  "approval_granted",
  "approval_rejected",
  "schedule_created",
  "schedule_changed",
  "rollout_started",
  "rollout_completed",
  "rollback_planned",
  "note_added",
]

const defaultFilters = {
  rollout_plan_id: "",
  bundle_id: "",
  event_type: "",
  date_from: "",
  date_to: "",
}

export default function RolloutTimelinePage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [timeline, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-timeline${query}`),
      apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-timeline/summary`),
    ])
    setState({
      ...context,
      entries: timeline.items || [],
      summary: timeline.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.rollout_plan_id, filters.bundle_id, filters.event_type, filters.date_from, filters.date_to])

  const counts = state?.summary?.by_event_type || {}
  const metrics = [
    ["Timeline Entries", state?.entries?.length || 0],
    ["Plans", state?.summary?.plan_count || 0],
    ["Approval Events", (counts.approval_requested || 0) + (counts.approval_granted || 0) + (counts.approval_rejected || 0)],
    ["Schedule Events", (counts.schedule_created || 0) + (counts.schedule_changed || 0)],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rollout Timeline</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only rollout timeline metadata. It does not enable bundles, change permissions, execute rollout plans, schedule background jobs, publish, call providers, send emails or notifications, enforce rollout state, modify subscriptions, or introduce automation.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Newest first</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Timeline filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <Field label="Plan" value={filters.rollout_plan_id} onChange={(value) => setFilters({ ...filters, rollout_plan_id: value })} />
              <Field label="Bundle" value={filters.bundle_id} onChange={(value) => setFilters({ ...filters, bundle_id: value })} />
              <SelectField label="Event" value={filters.event_type} onChange={(value) => setFilters({ ...filters, event_type: value })} options={eventTypes.map((eventType) => [eventType, formatEvent(eventType)])} placeholder="All events" />
              <Field label="From" type="date" value={filters.date_from} onChange={(value) => setFilters({ ...filters, date_from: value })} />
              <Field label="To" type="date" value={filters.date_to} onChange={(value) => setFilters({ ...filters, date_to: value })} />
            </div>
          </section>

          {state?.entries?.length ? (
            <section className="grid gap-4">
              {state.entries.map((entry) => <TimelineCard entry={entry} key={entry.timeline_entry_id} />)}
            </section>
          ) : <EmptyState title="No rollout timeline entries" body="Platform rollout history metadata will appear here after timeline records are created." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function TimelineCard({ entry }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{entry.bundle_name || entry.bundle_id}</p>
          <h3 className="mt-1 font-semibold text-slate-950">{entry.event_label || formatEvent(entry.event_type)}</h3>
          <p className="text-sm text-slate-600">{entry.description || "No description"}</p>
        </div>
        <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 ring-1 ring-blue-200">{formatEvent(entry.event_type)}</span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm md:grid-cols-4">
        <Info label="Actor" value={entry.actor?.display_name || entry.actor?.email || "Platform metadata"} />
        <Info label="Timestamp" value={formatDateTime(entry.occurred_at)} />
        <Info label="Plan" value={entry.plan_name || entry.rollout_plan_id} />
        <Info label="Source" value={entry.source || "Platform metadata"} />
      </dl>
    </article>
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

function Field({ label, value, onChange, type = "text" }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" type={type} value={value} onChange={(event) => onChange(event.target.value)} />
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

function Info({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-slate-700">{value || "Not set"}</dd>
    </div>
  )
}

function queryString(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function formatEvent(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDateTime(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleString()
}
