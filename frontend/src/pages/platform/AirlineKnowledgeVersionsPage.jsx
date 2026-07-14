import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPut } from "../../lib/api"

function Count({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  return <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{String(children || "unknown").replaceAll("_", " ")}</span>
}

export default function AirlineKnowledgeVersionsPage() {
  const [state, setState] = useState(null)
  const [detail, setDetail] = useState(null)
  const [selectedId, setSelectedId] = useState("")
  const [category, setCategory] = useState("")
  const [error, setError] = useState("")

  async function load(filter = category) {
    const query = filter ? `?category=${encodeURIComponent(filter)}` : ""
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/knowledge-versions${query}`)])
    setState({ summary, ...payload })
    setSelectedId((current) => current || payload.change_sets?.[0]?.id || "")
  }

  async function loadDetail(changeSetId) {
    if (!changeSetId) { setDetail(null); return }
    setDetail(await apiGet(`/api/platform/knowledge-versions/change-sets/${changeSetId}`))
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  useEffect(() => { loadDetail(selectedId).catch((err) => setError(err.message)) }, [selectedId])
  const selected = useMemo(() => state?.change_sets?.find((item) => item.id === selectedId), [state, selectedId])

  async function review(reviewStatus) {
    try {
      await apiPut(`/api/platform/knowledge-versions/change-sets/${selectedId}/review`, { review_status: reviewStatus, review_decision: reviewStatus, review_notes: "Human-reviewed deterministic change set." })
      await load(category); await loadDetail(selectedId)
    } catch (err) { setError(err.message) }
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Airline knowledge governance</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Knowledge Versions</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Immutable snapshots, deterministic field-level changes, downstream impact review, and governed revalidation. Historical operational snapshots are never rewritten.</p></header>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Count label="Versions" value={state?.coverage?.version_count} /><Count label="Change sets" value={state?.coverage?.change_set_count} /><Count label="Field changes" value={state?.coverage?.field_change_count} /><Count label="Potential impacts" value={state?.coverage?.impact_assessment_count} /><Count label="Revalidation open" value={state?.coverage?.open_revalidation_count} /></section>

          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load(category).catch((err) => setError(err.message)) }}><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">All change categories</option>{state?.change_categories?.map((value) => <option key={value}>{value}</option>)}</select><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Filter</button></form>

          <section><h2 className="font-semibold text-slate-950">Version timeline</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Version</th><th className="px-3 py-2">Lifecycle</th><th className="px-3 py-2">Objects</th><th className="px-3 py-2">Airlines</th><th className="px-3 py-2">Effective</th></tr></thead><tbody>{state?.versions?.map((version) => <tr className="border-t border-slate-200" key={version.id}><td className="px-3 py-3 font-medium">{version.version_label || version.knowledge_version_reference}</td><td className="px-3 py-3"><Status>{version.lifecycle_status}</Status></td><td className="px-3 py-3">{version.version_item_count || 0}</td><td className="px-3 py-3">{version.affected_airline_codes?.join(", ") || "All scoped airlines"}</td><td className="px-3 py-3">{version.effective_from ? new Date(version.effective_from).toLocaleDateString() : "Not set"}</td></tr>)}</tbody></table></div></section>

          <div className="grid gap-5 lg:grid-cols-[360px_1fr]">
            <section><h2 className="font-semibold text-slate-950">Change sets</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.change_sets?.map((item) => <button type="button" className={`block w-full px-2 py-3 text-left hover:bg-slate-50 ${selectedId === item.id ? "bg-blue-50" : ""}`} key={item.id} onClick={() => setSelectedId(item.id)}><span className="block text-sm font-semibold text-slate-950">{item.change_set_reference}</span><span className="mt-1 block text-xs text-slate-500">{item.field_change_count} fields · {item.highest_severity} · {item.review_status}</span></button>)}</div></section>
            {selected && detail ? <section className="min-w-0 space-y-5"><div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4"><div><h2 className="text-xl font-semibold text-slate-950">{selected.change_set_reference}</h2><p className="mt-1 text-sm text-slate-600">{selected.change_summary}</p></div><div className="flex gap-2"><button type="button" className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" onClick={() => review("under_review")}>Start review</button><button type="button" className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" onClick={() => review("accepted")}>Accept</button></div></div>
              <div className="flex flex-wrap gap-2"><Status>{selected.highest_severity}</Status>{selected.change_categories?.map((value) => <Status key={value}>{value}</Status>)}{selected.re_qa_required ? <Status>re-QA required</Status> : null}{selected.republish_required ? <Status>republish required</Status> : null}</div>
              <div><h3 className="text-sm font-semibold text-slate-950">Structured diff</h3><div className="mt-2 overflow-x-auto border-y border-slate-200"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Field</th><th className="px-3 py-2">Change</th><th className="px-3 py-2">Severity</th><th className="px-3 py-2">Explanation</th></tr></thead><tbody>{detail.field_changes?.map((field) => <tr className="border-t border-slate-200" key={field.id}><td className="px-3 py-3 font-mono text-xs">{field.field_path}</td><td className="px-3 py-3">{field.change_category.replaceAll("_", " ")}</td><td className="px-3 py-3">{field.severity}</td><td className="px-3 py-3">{field.human_summary}</td></tr>)}</tbody></table></div></div>
              <div className="grid gap-5 md:grid-cols-2"><div><h3 className="text-sm font-semibold text-slate-950">Impact assessment</h3><div className="mt-2 space-y-2">{detail.impact_assessments?.map((impact) => <div className="rounded-md border border-slate-200 p-3" key={impact.id}><p className="text-sm font-semibold">{impact.impact_type.replaceAll("_", " ")}</p><p className="mt-1 text-sm text-slate-600">{impact.impact_summary}</p></div>)}</div></div><div><h3 className="text-sm font-semibold text-slate-950">Revalidation</h3><div className="mt-2 space-y-2">{detail.revalidation_requests?.map((item) => <div className="rounded-md border border-slate-200 p-3" key={item.id}><p className="text-sm font-semibold">{item.request_type.replaceAll("_", " ")}</p><p className="mt-1 text-sm text-slate-600">{item.reason}</p></div>)}</div><p className="mt-4 text-sm text-slate-600">Rollback reference: {selected.rollback_version_id || "None"}</p></div></div>
            </section> : null}
          </div>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
