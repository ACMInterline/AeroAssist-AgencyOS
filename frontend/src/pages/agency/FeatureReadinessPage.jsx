import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const checklist = [
  ["documentation_complete", "Documentation"],
  ["backend_complete", "Backend"],
  ["api_complete", "API"],
  ["ui_complete", "UI"],
  ["testing_complete", "Testing"],
  ["deployment_ready", "Deployment"],
  ["rollout_ready", "Rollout"],
]

export default function FeatureReadinessPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const readiness = await apiGet(`/api/agencies/${context.agency.id}/feature-readiness`)
      setState({
        ...context,
        readiness: readiness.items || [],
        summary: readiness,
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = [
    ["Features", state?.readiness?.length || 0],
    ["Deployment ready", state?.readiness?.filter((item) => item.deployment_ready).length || 0],
    ["Rollout ready", state?.readiness?.filter((item) => item.rollout_ready).length || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Readiness</h2>
              <p className="mt-1 text-sm text-slate-600">Feature readiness is informational only. Operational enforcement is not performed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No switches</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-3">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Readiness checklist</h3>
            </div>
            {state?.readiness?.length ? (
              <div className="divide-y divide-slate-100">
                {state.readiness.map((item) => <ReadinessCard item={item} key={item.id} />)}
              </div>
            ) : <EmptyState title="No feature readiness metadata" body="Platform owners have not reviewed readiness metadata for this agency yet." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function ReadinessCard({ item }) {
  return (
    <div className="p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-950">{item.feature_key}</p>
          <p className="mt-1 text-sm text-slate-600">Last reviewed: {formatDate(item.last_reviewed)} · {item.reviewed_by || "Platform review"}</p>
        </div>
        <StatusBadge label="Rollout" active={item.rollout_ready} />
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {checklist.map(([key, label]) => <ChecklistItem label={label} active={item[key]} key={key} />)}
      </div>
    </div>
  )
}

function ChecklistItem({ label, active }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{active ? "Complete" : "Review"}</span>
    </div>
  )
}

function Metric({ label: text, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{text}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function StatusBadge({ label, active }) {
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${active ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-slate-100 text-slate-600 ring-slate-200"}`}>{label}: {active ? "Ready" : "Review"}</span>
}

function formatDate(value) {
  if (!value) return "Not reviewed"
  return new Date(value).toLocaleDateString()
}
