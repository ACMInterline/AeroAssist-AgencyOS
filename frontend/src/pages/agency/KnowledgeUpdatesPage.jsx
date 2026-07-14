import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

function Status({ children }) {
  return <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{String(children || "unknown").replaceAll("_", " ")}</span>
}

export default function KnowledgeUpdatesPage() {
  const [state, setState] = useState(null)
  const [category, setCategory] = useState("")
  const [error, setError] = useState("")

  async function load(filter = category) {
    const context = await loadCurrentAgency()
    const query = filter ? `?category=${encodeURIComponent(filter)}` : ""
    const payload = await apiGet(`/api/agencies/${context.agency.id}/knowledge-updates${query}`)
    setState({ ...context, ...payload })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Published airline intelligence</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Knowledge Updates</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Published and effective airline knowledge changes, affected services, and operational review warnings. Draft changes and restricted source details are not visible.</p></header>
          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load(category).catch((err) => setError(err.message)) }}><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Change category" value={category} onChange={(event) => setCategory(event.target.value)} /><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Filter</button></form>
          <section className="grid gap-3 sm:grid-cols-3"><div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">Published updates</p><p className="mt-2 text-2xl font-semibold">{state?.published_update_count || 0}</p></div><div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">Operational warnings</p><p className="mt-2 text-2xl font-semibold">{state?.updates?.reduce((sum, item) => sum + item.operational_warnings.length, 0) || 0}</p></div><div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">Affected services</p><p className="mt-2 text-2xl font-semibold">{new Set(state?.updates?.flatMap((item) => item.affected_service_families) || []).size}</p></div></section>
          <section><h2 className="font-semibold text-slate-950">Effective-date notices</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.updates?.map((update) => <article className="py-5" key={update.id}><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-semibold text-slate-950">{update.version_label || update.change_set_reference}</h3><p className="mt-1 max-w-3xl text-sm text-slate-600">{update.change_summary}</p></div><div className="flex flex-wrap gap-2"><Status>{update.highest_severity}</Status>{update.re_qa_required ? <Status>re-QA</Status> : null}{update.republish_required ? <Status>republish review</Status> : null}</div></div><dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3"><div><dt className="font-semibold text-slate-500">Airlines</dt><dd className="mt-1">{update.affected_airline_codes.join(", ") || "Scoped publication"}</dd></div><div><dt className="font-semibold text-slate-500">Services</dt><dd className="mt-1">{update.affected_service_families.join(", ") || "General"}</dd></div><div><dt className="font-semibold text-slate-500">Effective</dt><dd className="mt-1">{update.effective_from ? new Date(update.effective_from).toLocaleDateString() : "Published release date"}</dd></div></dl><div className="mt-4 grid gap-5 md:grid-cols-2"><div><h4 className="text-sm font-semibold">Changes</h4><ul className="mt-2 space-y-1 text-sm text-slate-600">{update.field_changes.map((field, index) => <li key={`${field.field_path}-${index}`}>{field.human_summary}</li>)}</ul></div><div><h4 className="text-sm font-semibold">Operational warnings</h4><ul className="mt-2 space-y-1 text-sm text-slate-600">{update.operational_warnings.map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}</ul></div></div></article>)}</div>{!state?.updates?.length ? <p className="mt-4 text-sm text-slate-600">No published knowledge updates match this view.</p> : null}</section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
