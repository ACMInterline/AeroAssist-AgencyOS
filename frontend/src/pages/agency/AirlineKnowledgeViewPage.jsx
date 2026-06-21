import { useEffect, useState } from "react"
import ConfidenceBadge from "../../components/ConfidenceBadge"
import KnowledgeCategoryBadge from "../../components/KnowledgeCategoryBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ReviewStatusBadge from "../../components/ReviewStatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function AirlineKnowledgeViewPage({ knowledgeId }) {
  const [state, setState] = useState(null)
  const [note, setNote] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const detail = await apiGet(`/api/agencies/${context.agency.id}/airline-knowledge/${knowledgeId}`)
    setState({ ...context, knowledge: detail.knowledge })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [knowledgeId])

  async function recordUsage(event) {
    event.preventDefault()
    await apiPost(`/api/agencies/${state.agency.id}/airline-knowledge/${knowledgeId}/usage`, { used_in_context_type: "manual_search", note })
    setNote("")
  }

  const item = state?.knowledge

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href={`/agency/airline-intelligence/${item.airline_id}`}>Back to airline</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{item.airline.airline_code} · {item.airline.airline_name}</p>
              <h2 className="text-2xl font-semibold text-slate-950">{item.title}</h2>
              <p className="mt-1 text-sm text-slate-600">{item.decision_support_notice}</p>
            </div>
            <div className="flex flex-wrap gap-2"><KnowledgeCategoryBadge category={item.category} /><ReviewStatusBadge status={item.review_status} /><ConfidenceBadge confidence={item.confidence} /></div>
          </div>
          <section className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
            <article className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Merged Agency View</h3>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{item.agency_override.merged_text}</p>
              {item.agency_override.annotations?.length ? (
                <div className="mt-5 rounded-md border border-amber-200 bg-amber-50 p-4">
                  <h4 className="text-sm font-semibold text-amber-950">Agency annotations</h4>
                  <div className="mt-2 space-y-2 text-sm text-amber-900">
                    {item.agency_override.annotations.map((override) => <p key={override.id}>{override.override_text}</p>)}
                  </div>
                </div>
              ) : null}
            </article>
            <aside className="space-y-4">
              <Info title="Applicability" rows={[["Service code", item.service_code || "Not set"], ["Passenger type", item.passenger_type || "Any"], ["Region", item.region_scope || "Any"], ["Cabin", item.cabin_scope || "Any"], ["Route", item.route_scope || "Any"]]} />
              <Info title="Review" rows={[["Confidence", item.confidence], ["Effective from", item.effective_from || "Not set"], ["Effective to", item.effective_to || "Not set"], ["Internal warning", item.internal_warning || item.agency_override.has_internal_warning ? "Yes" : "No"]]} />
            </aside>
          </section>
          <section className="grid gap-4 lg:grid-cols-2">
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Sources</h3>
              <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                {item.sources.length ? item.sources.map((source) => <div className="p-3 text-sm text-slate-700" key={source.id}>{source.title} · {source.source_type.replaceAll("_", " ")} · {source.reliability}</div>) : <div className="p-3 text-sm text-slate-500">No sources linked.</div>}
              </div>
            </section>
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-950">Usage Note</h3>
              <form className="mt-4 space-y-3" onSubmit={recordUsage}>
                <textarea className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Optional note about where this was used" value={note} onChange={(event) => setNote(event.target.value)} />
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Record manual use</button>
              </form>
            </section>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Info({ title, rows }) {
  return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value}</dd></div>)}</dl></section>
}
