import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

export default function PlatformDashboardPage() {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    apiGet("/api/platform/summary").then(setSummary).catch((err) => setError(err.message))
  }, [])

  return (
    <PlatformLayout user={summary?.current_user}>
      <ProtectedRoute loading={!summary && !error} error={error}>
        <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Current layer</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">Platform Owner Foundation</h2>
              </div>
              <StatusBadge status={summary?.current_user?.global_role} />
            </div>
            <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(summary?.counts || {}).map(([label, value]) => (
                <div className="rounded-md bg-slate-50 p-4" key={label}>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label.replaceAll("_", " ")}</dt>
                  <dd className="mt-2 text-2xl font-semibold text-slate-950">{value}</dd>
                </div>
              ))}
            </dl>
          </section>
          <EmptyState
            title="Next platform modules"
            body="Airline intelligence editing, full template libraries, subscription tooling, and support workflows are intentionally not implemented in Phase 1."
          />
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
