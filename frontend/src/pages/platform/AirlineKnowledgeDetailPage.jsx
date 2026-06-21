import { useEffect, useState } from "react"
import ConfidenceBadge from "../../components/ConfidenceBadge"
import KnowledgeCategoryBadge from "../../components/KnowledgeCategoryBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ReviewStatusBadge from "../../components/ReviewStatusBadge"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"

export default function AirlineKnowledgeDetailPage({ knowledgeId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ title: "", summary: "", detailed_text: "" })
  const [error, setError] = useState("")

  async function load() {
    const [summary, detail] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/airline-knowledge/${knowledgeId}`)])
    setState({ summary, ...detail })
    setForm({ title: detail.knowledge.title, summary: detail.knowledge.summary, detailed_text: detail.knowledge.detailed_text })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [knowledgeId])

  async function save(event) {
    event.preventDefault()
    await apiPut(`/api/platform/airline-knowledge/${knowledgeId}`, form)
    await load()
  }

  async function publish() {
    await apiPost(`/api/platform/airline-knowledge/${knowledgeId}/publish`)
    await load()
  }

  async function archive() {
    await apiPost(`/api/platform/airline-knowledge/${knowledgeId}/archive`)
    await load()
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <a className="text-sm font-medium text-blue-700" href={`/platform/airlines/${state.knowledge.airline_id}`}>Back to airline</a>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.airline.airline_code} · platform knowledge</p>
              <h2 className="text-2xl font-semibold text-slate-950">{state.knowledge.title}</h2>
            </div>
            <div className="flex flex-wrap gap-2"><KnowledgeCategoryBadge category={state.knowledge.category} /><ReviewStatusBadge status={state.knowledge.review_status} /><ConfidenceBadge confidence={state.knowledge.confidence} /></div>
          </div>
          <form className="space-y-4 rounded-lg border border-slate-200 bg-white p-5" onSubmit={save}>
            <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} />
            <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.summary} onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))} />
            <textarea className="min-h-56 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.detailed_text} onChange={(event) => setForm((current) => ({ ...current, detailed_text: event.target.value }))} />
            <div className="flex flex-wrap gap-2">
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Save</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={publish}>Publish</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={archive}>Archive</button>
            </div>
          </form>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Sources</h3>
            <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
              {state.sources.length ? state.sources.map((source) => <div className="p-3 text-sm text-slate-700" key={source.id}>{source.title} · {source.reliability}</div>) : <div className="p-3 text-sm text-slate-500">No sources linked.</div>}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
