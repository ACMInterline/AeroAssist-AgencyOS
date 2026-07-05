import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function PlatformFeatureBundleRolloutReadinessPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState(false)

  async function load() {
    const [me, readiness, summary] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/platform/feature-bundle-rollout-readiness"),
      apiGet("/api/platform/feature-bundle-rollout-readiness/summary"),
    ])
    setState({
      me,
      items: readiness.items || [],
      summary: summary.summary || readiness.summary || {},
      response: readiness,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function createDefaults() {
    setWorking(true)
    setError("")
    setMessage("")
    try {
      const result = await apiPost("/api/platform/feature-bundle-rollout-readiness/defaults", {})
      setMessage(`${result.created_count || 0} default readiness records created as metadata only.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking(false)
    }
  }

  const statusCounts = state?.summary?.by_readiness_status || {}
  const metrics = [
    ["Readiness views", state?.items?.length || 0],
    ["Ready", statusCounts.ready || 0],
    ["Reviewing", statusCounts.reviewing || 0],
    ["Blocked", statusCounts.blocked || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Rollout Readiness</h2>
              <p className="mt-1 text-sm text-slate-600">Readiness is metadata only. It does not activate, deactivate, allow, or block features.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform review</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No activation</span>
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createDefaults} disabled={working}>
                Create defaults
              </button>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Assigned bundle readiness</h3>
            </div>
            {state?.items?.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Agency</th>
                      <th className="px-4 py-3">Bundle</th>
                      <th className="px-4 py-3">Assignment</th>
                      <th className="px-4 py-3">Readiness</th>
                      <th className="px-4 py-3">Checklist</th>
                      <th className="px-4 py-3">Warnings</th>
                      <th className="px-4 py-3">Blockers</th>
                      <th className="px-4 py-3">Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {state.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-3 text-slate-600">{item.agency_name || item.agency_id}</td>
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-950">{item.bundle_name || item.bundle_id}</p>
                          <p className="text-xs text-slate-500">{item.bundle_key || item.bundle_id}</p>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{item.assignment_id}</td>
                        <td className="px-4 py-3"><StatusBadge status={item.readiness_status} /></td>
                        <td className="px-4 py-3 text-slate-600">{formatCounts(item.checklist_counts)}</td>
                        <td className="px-4 py-3 text-slate-600">{(item.warnings || []).length}</td>
                        <td className="px-4 py-3 text-slate-600">{(item.blockers || []).length}</td>
                        <td className="px-4 py-3 text-slate-600">{item.stored_record ? "Stored review" : "Default view"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState title="No rollout readiness metadata" body="Create or assign feature bundles to see readiness views here." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
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
    ready: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    reviewing: "bg-blue-50 text-blue-700 ring-blue-200",
    blocked: "bg-red-50 text-red-700 ring-red-200",
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
