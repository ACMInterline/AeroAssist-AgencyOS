import { useEffect, useState } from "react"
import { CircleAlert, ShieldCheck } from "lucide-react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value ?? 0}</p></div>
}

function Status({ children }) {
  const value = String(children || "unknown")
  const color = value === "released" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${color}`}>{value.replaceAll("_", " ")}</span>
}

export default function AirlineIntelligenceReadinessPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    async function load() {
      const context = await loadCurrentAgency()
      const response = await apiGet(`/api/agencies/${context.agency.id}/airline-intelligence-readiness`)
      setState({ ...context, ...response })
    }
    load().catch((err) => setError(err.message))
  }, [])

  const summary = state?.summary || {}
  const coverage = state?.released_coverage || []

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header>
            <p className="text-sm font-semibold uppercase text-blue-700">Released Airline Intelligence</p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-950">Airline Intelligence Readiness</h1>
            <p className="mt-1 max-w-5xl text-sm text-slate-600">Read-only visibility into airline intelligence releases assigned to this agency. Draft governance, internal notes, and restricted evidence are hidden. This page does not publish knowledge, activate providers, or execute recommendations.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Released airlines" value={summary.released_airline_count} />
            <Metric label="Assigned releases" value={summary.released_candidate_count} />
            <Metric label="Usable modules" value={summary.usable_module_count} />
            <Metric label="Warnings" value={summary.conditional_or_stale_count} />
          </section>

          {(state?.warnings || []).length ? <section><h2 className="text-lg font-semibold text-slate-950">Operational warnings</h2><div className="mt-3 space-y-2">{state.warnings.map((item) => <div className="flex gap-3 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900" key={item.candidate_reference}><CircleAlert className="mt-0.5 h-4 w-4 shrink-0" /><div><p className="font-semibold">{item.airline_code} · {item.candidate_reference}</p><p className="mt-1">{item.warnings?.join(" ") || "This release contains stale or conditional knowledge; confirm before operational use."}</p></div></div>)}</div></section> : null}

          <section>
            <div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-blue-700" /><h2 className="text-lg font-semibold text-slate-950">Assigned released coverage</h2></div>
            {coverage.length ? <div className="mt-3 grid gap-4 lg:grid-cols-2">{coverage.map((item) => <article className="rounded-lg border border-slate-200 bg-white p-5" key={item.id}><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-semibold text-slate-950">{item.airline_code} · {item.candidate_name}</h3><p className="mt-1 text-xs text-slate-500">{item.candidate_reference}</p></div><Status>{item.candidate_status}</Status></div><dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm"><dt className="text-slate-500">Assigned release</dt><dd className="font-medium text-slate-900">{item.assigned_release_version || "Reference pending"}</dd><dt className="text-slate-500">Effective from</dt><dd className="font-medium text-slate-900">{item.effective_from || "Not supplied"}</dd><dt className="text-slate-500">Confidence</dt><dd className="font-medium text-slate-900">{item.confidence_score}/100</dd><dt className="text-slate-500">Freshness</dt><dd className="font-medium text-slate-900">{item.freshness_score}/100</dd></dl><div className="mt-4 border-t border-slate-200 pt-4"><p className="text-xs font-semibold uppercase text-slate-500">Usable modules</p><p className="mt-1 text-sm text-slate-700">{item.usable_modules?.join(", ") || "No modules assigned"}</p><p className="mt-3 text-sm text-slate-600">{item.client_facing_summary || "No agency-safe release summary supplied."}</p></div>{item.warnings?.length ? <div className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">{item.warnings.join(" ")}</div> : null}</article>)}</div> : <EmptyState title="No assigned releases" body="Platform-reviewed airline intelligence will appear after a controlled release is assigned to this agency." />}
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
