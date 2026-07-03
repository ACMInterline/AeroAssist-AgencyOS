import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import StatusBadge from "../../components/StatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"
import { platformModuleGroups } from "../../lib/moduleCatalog"

export default function PlatformDashboardPage() {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    apiGet("/api/platform/summary").then(setSummary).catch((err) => setError(err.message))
  }, [])

  return (
    <PlatformLayout user={summary?.current_user}>
      <ProtectedRoute loading={!summary && !error} error={error}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Current layer</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-950">Platform Console</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                  System owners use this console to manage SaaS agencies, governed airline intelligence, website/CMS foundations,
                  client portal visibility, offer evidence, document review, and readiness metadata.
                </p>
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
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {platformModuleGroups.map((group) => (
              <a className="rounded-lg border border-slate-200 bg-white p-5 hover:border-blue-300" href={group.items[0]?.href || "/platform"} key={group.title}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold text-slate-950">{group.title}</h3>
                  <span className="rounded-full bg-blue-50 px-2 py-1 text-[11px] font-semibold text-blue-700">{group.audience}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">{group.description}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">{group.safety}</span>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">{group.items.length} modules</span>
                </div>
              </a>
            ))}
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-sm font-semibold text-slate-950">Production Onboarding</h3>
            <p className="mt-2 text-sm text-slate-600">Readiness and onboarding state stays informational for platform owners.</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {Object.entries(summary?.production_onboarding || {}).map(([label, value]) => (
                <div className="flex items-center justify-between gap-3 rounded-md bg-slate-50 p-3 text-sm" key={label}>
                  <span className="font-medium text-slate-700">{label.replaceAll("_", " ")}</span>
                  <StatusBadge status={typeof value === "boolean" ? (value ? "active" : "pending") : String(value)} />
                </div>
              ))}
            </div>
            <a className="mt-5 inline-flex rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" href="/platform/agencies">
              Manage agencies
            </a>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
