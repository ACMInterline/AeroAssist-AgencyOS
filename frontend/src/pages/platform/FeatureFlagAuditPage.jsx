import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"
import { featureFlagClass, featureFlagLabel } from "../../lib/moduleCatalog"

const base = "/api/platform/feature-flags"

export default function PlatformFeatureFlagAuditPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const [me, audits, readiness, agencies] = await Promise.all([
        apiGet("/api/auth/me"),
        apiGet(`${base}/audits`),
        apiGet(`${base}/readiness`),
        apiGet("/api/agencies"),
      ])
      setState({
        me,
        audits: audits.items || [],
        readiness: readiness.items || [],
        agencies: agencies.items || [],
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = [
    ["Audits", state?.audits?.length || 0],
    ["Readiness", state?.readiness?.length || 0],
    ["Rollout ready", state?.readiness?.filter((item) => item.rollout_ready).length || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Audit History</h2>
              <p className="mt-1 text-sm text-slate-600">Feature flag audit and readiness metadata is read-only and does not perform enforcement.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Platform review</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Read-only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-3">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Audit history</h3>
            </div>
            {state?.audits?.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Feature</th>
                      <th className="px-4 py-3">Agency</th>
                      <th className="px-4 py-3">Previous</th>
                      <th className="px-4 py-3">Proposed</th>
                      <th className="px-4 py-3">Reviewer</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {state.audits.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-3 font-semibold text-slate-950">{item.feature_key}</td>
                        <td className="px-4 py-3 text-slate-600">{agencyName(state.agencies, item.agency_id)}</td>
                        <td className="px-4 py-3"><FlagBadge state={item.previous_state} /></td>
                        <td className="px-4 py-3"><FlagBadge state={item.proposed_state} /></td>
                        <td className="px-4 py-3 text-slate-600">{item.changed_by || "Platform review"}</td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(item.changed_at)}</td>
                        <td className="px-4 py-3 text-slate-600">{item.notes || item.reason || "Metadata record"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState title="No feature flag audit history" body="Audit metadata will appear after platform feature visibility changes." />}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Readiness review</h3>
            </div>
            {state?.readiness?.length ? (
              <div className="divide-y divide-slate-100">
                {state.readiness.slice(0, 12).map((item) => <ReadinessRow item={item} agencies={state.agencies} key={item.id} />)}
              </div>
            ) : <EmptyState title="No readiness metadata" body="Readiness checklist metadata will appear when feature visibility is reviewed." />}
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function ReadinessRow({ item, agencies }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-4">
      <div>
        <p className="font-semibold text-slate-950">{item.feature_key}</p>
        <p className="mt-1 text-sm text-slate-600">{agencyName(agencies, item.agency_id)}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <StatusBadge label="Deployment" active={item.deployment_ready} />
        <StatusBadge label="Rollout" active={item.rollout_ready} />
      </div>
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

function FlagBadge({ state }) {
  if (!state) return <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600 ring-1 ring-slate-200">None</span>
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${featureFlagClass(state)}`}>{featureFlagLabel(state)}</span>
}

function StatusBadge({ label, active }) {
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ring-1 ${active ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-slate-100 text-slate-600 ring-slate-200"}`}>{label}: {active ? "Ready" : "Review"}</span>
}

function agencyName(agencies, agencyId) {
  return agencies?.find((agency) => agency.id === agencyId)?.name || agencyId || "Agency"
}

function formatDate(value) {
  if (!value) return "Not reviewed"
  return new Date(value).toLocaleString()
}
