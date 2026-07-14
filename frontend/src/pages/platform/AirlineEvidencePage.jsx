import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"

const sourceTypes = ["airline_public_website", "airline_conditions_of_carriage", "airline_tariff", "airline_agent_manual", "gds_help_page", "gds_cryptic_response", "airline_operational_bulletin", "airline_trade_communication", "airline_email_confirmation", "airline_support_desk_response", "airport_handling_response", "internal_operational_observation", "historical_case_evidence", "regulator_government_source", "iata_industry_publication", "supplier_consolidator_instruction", "screenshot", "pdf_manual", "structured_import", "api_response"]

function Badge({ children, tone = "bg-slate-100 text-slate-700 ring-slate-200" }) {
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{children}</span>
}

function Count({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value ?? 0}</p></div>
}

export default function AirlineEvidencePage() {
  const [state, setState] = useState(null)
  const [selectedId, setSelectedId] = useState("")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [sourceForm, setSourceForm] = useState({ source_type: "airline_public_website", title: "", source_url: "", source_owner: "", evidence_status: "draft", accessibility: "internal_restricted", confidence: "unknown", effective_from: "", review_due_date: "" })
  const [assertionForm, setAssertionForm] = useState({ assertion_type: "policy", assertion_key: "", assertion_title: "", excerpt: "", structured_value: "", evidence_status: "draft", accessibility: "internal_restricted", effective_from: "" })
  const [artifactForm, setArtifactForm] = useState({ artifact_type: "pdf_manual", title: "", file_name: "", checksum: "", accessibility: "internal_restricted" })

  async function load() {
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet("/api/platform/airline-evidence")])
    setState({ summary, ...payload })
    setSelectedId((current) => current || payload.sources?.[0]?.id || "")
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  const selected = useMemo(() => state?.sources?.find((item) => item.id === selectedId), [state, selectedId])
  const sourceAssertions = state?.assertions?.filter((item) => item.source_id === selectedId) || []
  const sourceArtifacts = state?.artifacts?.filter((item) => item.source_id === selectedId) || []

  async function createSource(event) {
    event.preventDefault(); setError(""); setMessage("")
    try {
      const body = Object.fromEntries(Object.entries(sourceForm).filter(([, value]) => value !== ""))
      const result = await apiPost("/api/platform/airline-evidence/sources", body)
      setMessage("Evidence source registered. Raw intake records remain separate and unchanged.")
      setSourceForm({ ...sourceForm, title: "", source_url: "", source_owner: "" })
      await load(); setSelectedId(result.source.id)
    } catch (err) { setError(err.message) }
  }

  async function createAssertion(event) {
    event.preventDefault(); setError("")
    try {
      const body = Object.fromEntries(Object.entries({ ...assertionForm, source_id: selectedId }).filter(([, value]) => value !== ""))
      try { body.structured_value = JSON.parse(body.structured_value) } catch { body.structured_value = assertionForm.structured_value }
      await apiPost("/api/platform/airline-evidence/assertions", body)
      setAssertionForm({ ...assertionForm, assertion_key: "", assertion_title: "", excerpt: "", structured_value: "" })
      setMessage("Assertion registered and checked for conflicts."); await load()
    } catch (err) { setError(err.message) }
  }

  async function createArtifact(event) {
    event.preventDefault(); setError("")
    try {
      await apiPost("/api/platform/airline-evidence/artifacts", { ...artifactForm, source_id: selectedId })
      setArtifactForm({ ...artifactForm, title: "", file_name: "", checksum: "" })
      setMessage("Artifact metadata registered. No file transfer was performed."); await load()
    } catch (err) { setError(err.message) }
  }

  async function resolveConflict(conflict) {
    setError("")
    try {
      await apiPut(`/api/platform/airline-evidence/conflicts/${conflict.id}`, { status: "resolved", accepted_assertion_ids: conflict.assertion_ids, resolution_summary: "Human review accepted the documented source variants." })
      setMessage("Conflict reviewed without deleting either source assertion."); await load()
    } catch (err) { setError(err.message) }
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Airline knowledge governance</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Policy Evidence</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Canonical provenance for airline policy, pricing, rules, capability, servicing, contacts, and publications. Conflicts are retained for human review.</p></header>
          {message ? <p className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">{message}</p> : null}
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6"><Count label="Sources" value={state?.coverage?.source_count} /><Count label="Artifacts" value={state?.coverage?.artifact_count} /><Count label="Assertions" value={state?.coverage?.assertion_count} /><Count label="Links" value={state?.coverage?.evidence_link_count} /><Count label="Open conflicts" value={state?.coverage?.unresolved_conflict_count} /><Count label="Unsupported" value={state?.coverage?.unsupported_knowledge_count} /></section>

          <section className="border-y border-slate-200 py-5"><h2 className="font-semibold text-slate-950">Register source governance metadata</h2><form className="mt-3 grid gap-3 md:grid-cols-3" onSubmit={createSource}><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={sourceForm.source_type} onChange={(event) => setSourceForm({ ...sourceForm, source_type: event.target.value })}>{sourceTypes.map((value) => <option key={value}>{value}</option>)}</select><input required className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Source title" value={sourceForm.title} onChange={(event) => setSourceForm({ ...sourceForm, title: event.target.value })} /><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="URL or reference" value={sourceForm.source_url} onChange={(event) => setSourceForm({ ...sourceForm, source_url: event.target.value })} /><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Source owner" value={sourceForm.source_owner} onChange={(event) => setSourceForm({ ...sourceForm, source_owner: event.target.value })} /><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={sourceForm.evidence_status} onChange={(event) => setSourceForm({ ...sourceForm, evidence_status: event.target.value })}>{["draft", "under_review", "verified", "approved", "published"].map((value) => <option key={value}>{value}</option>)}</select><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Register source</button></form></section>

          <div className="grid gap-5 lg:grid-cols-[330px_1fr]">
            <section><h2 className="text-sm font-semibold text-slate-950">Source registry</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.sources?.map((source) => <button type="button" className={`block w-full px-2 py-3 text-left hover:bg-slate-50 ${selectedId === source.id ? "bg-blue-50" : ""}`} key={source.id} onClick={() => setSelectedId(source.id)}><span className="block text-sm font-semibold text-slate-950">{source.title}</span><span className="mt-1 block text-xs text-slate-500">{source.source_type.replaceAll("_", " ")} · {source.evidence_status}</span></button>)}</div></section>
            {selected ? <section className="min-w-0 space-y-5"><div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4"><div><h2 className="text-xl font-semibold text-slate-950">{selected.title}</h2><p className="mt-1 text-sm text-slate-600">{selected.source_reference} · {selected.source_owner || "Owner unknown"}</p></div><div className="flex gap-2"><Badge>{selected.authority_assessment.level} confidence</Badge><Badge>{selected.freshness?.freshness_status || "freshness unknown"}</Badge></div></div>
              <div className="grid gap-5 md:grid-cols-2"><form onSubmit={createArtifact}><h3 className="text-sm font-semibold text-slate-950">Register artifact metadata</h3><div className="mt-3 space-y-2"><input required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Artifact title" value={artifactForm.title} onChange={(event) => setArtifactForm({ ...artifactForm, title: event.target.value })} /><input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="File name or document reference" value={artifactForm.file_name} onChange={(event) => setArtifactForm({ ...artifactForm, file_name: event.target.value })} /><button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold">Register artifact</button></div></form><form onSubmit={createAssertion}><h3 className="text-sm font-semibold text-slate-950">Register structured assertion</h3><div className="mt-3 space-y-2"><input required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Assertion key, e.g. petc.weight_limit" value={assertionForm.assertion_key} onChange={(event) => setAssertionForm({ ...assertionForm, assertion_key: event.target.value })} /><input required className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Value or JSON" value={assertionForm.structured_value} onChange={(event) => setAssertionForm({ ...assertionForm, structured_value: event.target.value })} /><button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold">Register assertion</button></div></form></div>
              <div className="grid gap-4 sm:grid-cols-2"><div><h3 className="text-sm font-semibold text-slate-950">Artifacts</h3><p className="mt-2 text-sm text-slate-600">{sourceArtifacts.length} registered metadata records. No upload or provider action occurs here.</p></div><div><h3 className="text-sm font-semibold text-slate-950">Assertions</h3><p className="mt-2 text-sm text-slate-600">{sourceAssertions.length} structured assertions linked to this source.</p></div></div>
            </section> : null}
          </div>

          <section><h2 className="font-semibold text-slate-950">Conflict queue</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Assertion</th><th className="px-3 py-2">Type</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Sources retained</th><th className="px-3 py-2">Review</th></tr></thead><tbody>{state?.conflicts?.map((conflict) => <tr className="border-t border-slate-200" key={conflict.id}><td className="px-3 py-3 font-medium">{conflict.assertion_key}</td><td className="px-3 py-3">{conflict.conflict_type}</td><td className="px-3 py-3">{conflict.status}</td><td className="px-3 py-3">{conflict.source_ids.length}</td><td className="px-3 py-3">{["resolved", "archived"].includes(conflict.status) ? "Reviewed" : <button className="text-sm font-semibold text-blue-700" type="button" onClick={() => resolveConflict(conflict)}>Resolve metadata</button>}</td></tr>)}</tbody></table></div></section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
