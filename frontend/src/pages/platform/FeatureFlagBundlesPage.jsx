import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const base = "/api/platform/feature-flag-bundles"

export default function PlatformFeatureFlagBundlesPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const [me, bundles, reviews] = await Promise.all([
        apiGet("/api/auth/me"),
        apiGet(base),
        apiGet(`${base}/reviews`),
      ])
      setState({
        me,
        bundles: bundles.items || [],
        reviews: reviews.items || [],
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = [
    ["Bundles", state?.bundles?.length || 0],
    ["Flags", state?.bundles?.reduce((total, item) => total + (item.flag_count || 0), 0) || 0],
    ["Reviews", state?.reviews?.length || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Flag Bundles</h2>
              <p className="mt-1 text-sm text-slate-600">Bundles are reusable metadata only and do not enable features, publish changes, or enforce access.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform review</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-3">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Bundle review</h3>
            </div>
            {state?.bundles?.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Bundle Name</th>
                      <th className="px-4 py-3">Description</th>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Number of Flags</th>
                      <th className="px-4 py-3">Review Status</th>
                      <th className="px-4 py-3">Readiness</th>
                      <th className="px-4 py-3">Last Updated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {state.bundles.map((bundle) => (
                      <tr key={bundle.bundle_id}>
                        <td className="px-4 py-3 font-semibold text-slate-950">{bundle.bundle_name}</td>
                        <td className="max-w-sm px-4 py-3 text-slate-600">{bundle.description || "Reusable feature bundle metadata."}</td>
                        <td className="px-4 py-3 text-slate-600">{titleize(bundle.category)}</td>
                        <td className="px-4 py-3 text-slate-600">{bundle.flag_count || 0}</td>
                        <td className="px-4 py-3"><StatusBadge label={titleize(bundle.review_status)} tone="blue" /></td>
                        <td className="px-4 py-3"><StatusBadge label={bundle.readiness_status || "Metadata draft"} /></td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(bundle.last_updated)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState title="No feature flag bundles" body="Reusable bundle metadata will appear here for platform review." />}
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

function StatusBadge({ label, tone = "slate" }) {
  const toneClass = tone === "blue" ? "bg-blue-50 text-blue-700 ring-blue-200" : "bg-slate-100 text-slate-700 ring-slate-200"
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${toneClass}`}>{label}</span>
}

function titleize(value) {
  if (!value) return "Metadata"
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatDate(value) {
  if (!value) return "Not stored"
  return new Date(value).toLocaleDateString()
}
