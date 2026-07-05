import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function RolloutPlansPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const [plans, summary] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-plans`),
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-plans/summary`),
      ])
      setState({
        ...context,
        plans: plans.items || [],
        summary: summary.summary || plans.summary || {},
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const stageCounts = state?.summary?.by_rollout_stage || {}
  const metrics = [
    ["Plans", state?.plans?.length || 0],
    ["Readiness review", stageCounts.readiness_review || 0],
    ["Scheduled", stageCounts.scheduled || 0],
    ["Paused", stageCounts.paused || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rollout Plans</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only bundle rollout plan metadata. It does not activate, publish, send, bill, enforce access, or block features.</p>
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

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Bundle rollout plans</h3>
            </div>
            {state?.plans?.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Plan</th>
                      <th className="px-4 py-3">Bundle</th>
                      <th className="px-4 py-3">Stage</th>
                      <th className="px-4 py-3">Target</th>
                      <th className="px-4 py-3">Owner</th>
                      <th className="px-4 py-3">Checklist counts</th>
                      <th className="px-4 py-3">Warnings</th>
                      <th className="px-4 py-3">Blockers</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {state.plans.map((plan) => (
                      <tr key={plan.rollout_plan_id}>
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-950">{plan.plan_name}</p>
                          <p className="text-xs text-slate-500">{plan.rollout_plan_id}</p>
                        </td>
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-950">{plan.bundle_name || plan.bundle_id}</p>
                          <p className="text-xs text-slate-500">{plan.bundle_key || plan.bundle_id}</p>
                        </td>
                        <td className="px-4 py-3"><StatusBadge status={plan.rollout_stage} /></td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(plan.target_start_date)} - {formatDate(plan.target_end_date)}</td>
                        <td className="px-4 py-3 text-slate-600">{plan.rollout_owner || "Not assigned"}</td>
                        <td className="px-4 py-3 text-slate-600">{formatCounts(plan.checklist_summary?.counts)}</td>
                        <td className="px-4 py-3 text-slate-600">{plan.warnings || 0}</td>
                        <td className="px-4 py-3 text-slate-600">{plan.blockers || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState title="No rollout plans" body="Platform plan metadata will appear here when rollout planning begins." />}
          </section>
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

function StatusBadge({ status }) {
  const tones = {
    scheduled: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    readiness_review: "bg-blue-50 text-blue-700 ring-blue-200",
    paused: "bg-amber-50 text-amber-700 ring-amber-200",
    archived: "bg-slate-100 text-slate-600 ring-slate-200",
    draft: "bg-slate-100 text-slate-700 ring-slate-200",
  }
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tones[status] || tones.draft}`}>{titleize(status)}</span>
}

function formatCounts(counts = {}) {
  return `Passed ${counts.passed || 0} / Warn ${counts.warning || 0} / Block ${counts.blocked || 0}`
}

function titleize(value) {
  if (!value) return "Draft"
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatDate(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleDateString()
}
