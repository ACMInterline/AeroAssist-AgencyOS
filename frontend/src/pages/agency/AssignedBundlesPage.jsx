import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AssignedBundlesPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const [assignments, history] = await Promise.all([
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-assignments`),
        apiGet(`/api/agencies/${context.agency.id}/feature-bundle-assignment-history`),
      ])
      setState({
        ...context,
        assignments: assignments.items || [],
        history: history.items || [],
        summary: assignments,
      })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = [
    ["Assigned bundles", state?.assignments?.length || 0],
    ["History records", state?.history?.length || 0],
    ["Read-only", state?.summary?.read_only ? "Yes" : "No"],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Assigned Bundles</h2>
              <p className="mt-1 text-sm text-slate-600">Feature bundle assignments are metadata only. They do not activate features or change access.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No activation</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-3">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <h3 className="font-semibold text-slate-950">Assignment metadata</h3>
            </div>
            {state?.assignments?.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100 text-left text-sm">
                  <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Bundle</th>
                      <th className="px-4 py-3">Assignment date</th>
                      <th className="px-4 py-3">Review status</th>
                      <th className="px-4 py-3">Notes</th>
                      <th className="px-4 py-3">Effective</th>
                      <th className="px-4 py-3">Expiration</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {state.assignments.map((item) => (
                      <tr key={item.assignment_id}>
                        <td className="px-4 py-3 font-semibold text-slate-950">{item.bundle_name}</td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(item.assigned_at)}</td>
                        <td className="px-4 py-3"><StatusBadge label={titleize(item.review_status)} /></td>
                        <td className="max-w-sm px-4 py-3 text-slate-600">{item.notes || "Platform assignment metadata."}</td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(item.effective_date)}</td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(item.expiration_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState title="No assigned bundles" body="Platform owners have not recorded feature bundle assignments for this agency." />}
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

function StatusBadge({ label }) {
  return <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">{label}</span>
}

function titleize(value) {
  if (!value) return "Metadata"
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatDate(value) {
  if (!value) return "Not set"
  return new Date(value).toLocaleDateString()
}
