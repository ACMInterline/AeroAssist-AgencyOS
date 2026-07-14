import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AirlineEvidencePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  const [filters, setFilters] = useState({ source_type: "", freshness_status: "" })

  async function load(next = filters) {
    const context = await loadCurrentAgency()
    const query = new URLSearchParams(Object.entries(next).filter(([, value]) => value)).toString()
    const payload = await apiGet(`/api/agencies/${context.agency.id}/airline-evidence${query ? `?${query}` : ""}`)
    setState({ ...context, ...payload })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Airline intelligence evidence</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Evidence</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Approved evidence summaries for human-reviewed operational decisions. Restricted attachments, source locations, and internal review notes are not shown.</p></header>
          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load(filters).catch((err) => setError(err.message)) }}><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Source type" value={filters.source_type} onChange={(event) => setFilters({ ...filters, source_type: event.target.value })} /><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.freshness_status} onChange={(event) => setFilters({ ...filters, freshness_status: event.target.value })}><option value="">Any freshness</option>{["fresh", "review_due_soon", "review_overdue", "stale", "expired", "superseded", "unknown"].map((value) => <option key={value}>{value}</option>)}</select><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Filter</button></form>
          <section className="grid gap-3 sm:grid-cols-3"><div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">Visible sources</p><p className="mt-2 text-2xl font-semibold">{state?.visible_source_count || 0}</p></div><div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">Approved assertions</p><p className="mt-2 text-2xl font-semibold">{state?.visible_assertion_count || 0}</p></div><div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">Published links</p><p className="mt-2 text-2xl font-semibold">{state?.visible_link_count || 0}</p></div></section>
          <section><h2 className="font-semibold text-slate-950">Approved evidence summary</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.sources?.map((source) => <article className="grid gap-3 py-4 md:grid-cols-[1fr_180px_150px_150px]" key={source.id}><div><h3 className="font-semibold text-slate-950">{source.title}</h3><p className="mt-1 text-sm text-slate-600">{source.source_owner || "Source owner not published"}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Source type</p><p className="mt-1 text-sm">{source.source_type.replaceAll("_", " ")}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Confidence</p><p className="mt-1 text-sm">{source.authority_assessment.level}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Freshness</p><p className="mt-1 text-sm">{source.freshness?.freshness_status || "unknown"}</p></div></article>)}</div>{!state?.sources?.length ? <p className="mt-4 text-sm text-slate-600">No approved agency-visible evidence matches these filters.</p> : null}</section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
