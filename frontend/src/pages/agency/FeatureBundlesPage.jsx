import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function FeatureBundlesPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const bundles = await apiGet(`/api/agencies/${context.agency.id}/feature-flag-bundles`)
      setState({
        ...context,
        bundles: bundles.items || [],
        summary: bundles,
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = [
    ["Bundles", state?.bundles?.length || 0],
    ["Contained flags", state?.bundles?.reduce((total, item) => total + (item.flag_count || 0), 0) || 0],
    ["Read-only", state?.summary?.read_only ? "Yes" : "No"],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Available Feature Bundles</h2>
              <p className="mt-1 text-sm text-slate-600">Feature bundles are informational only. They do not enable features or perform operational enforcement.</p>
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
              <h3 className="font-semibold text-slate-950">Bundle metadata</h3>
            </div>
            {state?.bundles?.length ? (
              <div className="divide-y divide-slate-100">
                {state.bundles.map((bundle) => <BundleCard bundle={bundle} key={bundle.bundle_id} />)}
              </div>
            ) : <EmptyState title="No available feature bundles" body="Platform owners have not exposed bundle metadata for this agency yet." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function BundleCard({ bundle }) {
  return (
    <div className="p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-950">{bundle.bundle_name}</p>
          <p className="mt-1 max-w-3xl text-sm text-slate-600">{bundle.description || "Reusable feature bundle metadata."}</p>
        </div>
        <StatusBadge label={bundle.readiness_status || "Metadata draft"} />
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-[2fr_1fr]">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Contained Flags</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {(bundle.members || []).map((member) => (
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200" key={`${bundle.bundle_id}-${member.feature_key}`}>
                {member.display_name}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Review Notes</p>
          <p className="mt-2 text-sm text-slate-600">{bundle.review_notes || "Platform review metadata only."}</p>
        </div>
      </div>
    </div>
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

function StatusBadge({ label }) {
  return <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">{label}</span>
}
