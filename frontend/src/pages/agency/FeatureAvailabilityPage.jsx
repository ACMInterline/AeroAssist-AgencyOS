import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"
import { featureFlagClass, featureFlagLabel } from "../../lib/moduleCatalog"

export default function FeatureAvailabilityPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const base = `/api/agencies/${context.agency.id}/feature-flags`
      const [summary, flags, reviews] = await Promise.all([
        apiGet(`${base}/summary`),
        apiGet(`${base}/flags`),
        apiGet(`${base}/reviews`),
      ])
      setState({
        ...context,
        summary,
        flags: flags.items || [],
        reviews: reviews.items || [],
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = [
    ["Flags", state?.summary?.flag_count || 0],
    ["Reviews", state?.summary?.review_count || 0],
    ["Enabled", state?.summary?.state_counts?.enabled || 0],
    ["Beta", state?.summary?.state_counts?.beta || 0],
    ["Pilot", state?.summary?.state_counts?.pilot || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Availability</h2>
              <p className="mt-1 text-sm text-slate-600">Feature visibility is informational only. Operational enforcement is not performed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No enforcement</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Availability metadata</h3>
            </div>
            {state?.flags?.length ? (
              <div className="divide-y divide-slate-100">
                {state.flags.map((item) => (
                  <div className="flex flex-wrap items-start justify-between gap-3 p-4" key={item.id}>
                    <div>
                      <p className="font-semibold text-slate-950">{item.display_name}</p>
                      <p className="mt-1 text-sm text-slate-600">{item.module_key} · {item.feature_key}</p>
                      {item.visibility_note ? <p className="mt-1 text-sm text-slate-500">{item.visibility_note}</p> : null}
                    </div>
                    <FlagBadge state={item.state} />
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No feature availability metadata" body="Platform owners have not defined feature visibility metadata for this agency yet." />}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Review notes</h3>
            </div>
            {state?.reviews?.length ? (
              <div className="divide-y divide-slate-100">
                {state.reviews.slice(0, 8).map((item) => (
                  <div className="p-4 text-sm" key={item.id}>
                    <p className="text-slate-700">{item.notes}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.created_at}</p>
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No feature review notes" body="Review notes will appear here when available." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
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

function FlagBadge({ state }) {
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${featureFlagClass(state)}`}>{featureFlagLabel(state)}</span>
}
