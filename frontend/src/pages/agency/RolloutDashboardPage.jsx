import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AgencyRolloutDashboardPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const dashboard = await apiGet(`/api/agencies/${context.agency.id}/rollout-dashboard`)
      setState({
        ...context,
        sections: dashboard.sections || [],
        counts: dashboard.counts || {},
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rollout Dashboard</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only rollout metadata for this agency. It does not activate features, enforce access, bill, publish, send, schedule, execute providers, use AI, or block routes.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No automation</span>
            </div>
          </div>

          <section className="grid gap-3 md:grid-cols-3">
            <Metric label="Dashboard cards" value={state?.sections?.length || 0} />
            <Metric label="Agency metadata records" value={state?.counts?.total_count || 0} />
            <Metric label="Warnings / Blockers" value={`${state?.counts?.warning_count || 0} / ${state?.counts?.blocker_count || 0}`} />
          </section>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {(state?.sections || []).map((section) => <DashboardCard section={section} key={section.section_key} />)}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function DashboardCard({ section }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-950">{section.title}</h3>
          <p className="mt-1 text-sm text-slate-600">{section.description}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{section.count || 0}</span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Counts</dt>
          <dd className="mt-1 text-slate-700">Total {section.counts?.total_count || section.count || 0}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Statuses</dt>
          <dd className="mt-2 flex flex-wrap gap-2">{statusChips(section.statuses)}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Last Updated</dt>
          <dd className="mt-1 text-slate-700">{formatDateTime(section.last_updated)}</dd>
        </div>
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

function statusChips(statuses = {}) {
  const entries = Object.entries(statuses)
  if (!entries.length) return <span className="text-slate-500">No status metadata</span>
  return entries.map(([label, value]) => (
    <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 ring-1 ring-blue-200" key={label}>
      {titleize(label)} {value}
    </span>
  ))
}

function titleize(value) {
  if (!value) return "Unknown"
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatDateTime(value) {
  if (!value) return "No timestamp"
  return new Date(value).toLocaleString()
}
