import { useEffect, useMemo, useState } from "react"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  const value = String(children || "unknown")
  const tone = value === "supported" || value === "current" ? "bg-emerald-50 text-emerald-800" : value === "unsupported" || value === "expired" ? "bg-rose-50 text-rose-800" : "bg-amber-50 text-amber-800"
  return <span className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${tone}`}>{value.replaceAll("_", " ")}</span>
}

const tabs = ["relationships", "responsibility matrix", "through check", "baggage", "EMD", "evidence"]

export default function InterlineCodeshareIntelligencePage() {
  const [state, setState] = useState(null)
  const [airline, setAirline] = useState("")
  const [activeTab, setActiveTab] = useState("relationships")
  const [error, setError] = useState("")

  async function load() {
    const params = new URLSearchParams()
    if (airline) params.set("airline_code", airline)
    const query = params.toString() ? `?${params}` : ""
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/interline-codeshare-intelligence${query}`)])
    setState({ currentUser: summary.current_user, ...payload })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  const currentRows = useMemo(() => {
    if (activeTab === "through check") return state?.through_check_rules || []
    if (activeTab === "baggage") return state?.baggage_rules || []
    if (activeTab === "EMD") return state?.interline_emd_rules || []
    return []
  }, [activeTab, state])

  return (
    <PlatformLayout user={state?.currentUser}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header>
            <p className="text-sm font-semibold uppercase text-blue-700">Carrier responsibility governance</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-950">Interline, Codeshare & Operating Carrier Intelligence</h1>
            <p className="mt-1 max-w-5xl text-sm text-slate-600">Governed relationships and responsibility rules for marketed, operating, validating, ticketing, plating, and handling carriers.</p>
            <p className="mt-2 text-sm font-medium text-amber-800">Advisory metadata only. Unknown ownership remains unknown until evidence-backed human review resolves it.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Metric label="Airlines" value={state?.summary?.airline_count} />
            <Metric label="Relationships" value={state?.summary?.relationship_count} />
            <Metric label="Interline profiles" value={state?.summary?.interline_agreement_count} />
            <Metric label="Codeshare rules" value={state?.summary?.codeshare_rule_count} />
            <Metric label="Responsibility rules" value={state?.summary?.responsibility_rule_count} />
            <Metric label="Manual review" value={state?.summary?.manual_review_count} />
          </section>

          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load().catch((err) => setError(err.message)) }}>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline code" value={airline} onChange={(event) => setAirline(event.target.value)} />
            <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Filter</button>
            <button type="button" title="Refresh intelligence" onClick={() => load().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 text-slate-700"><RefreshCw className="h-4 w-4" /></button>
          </form>

          <div className="flex gap-1 overflow-x-auto border-b border-slate-200" role="tablist">{tabs.map((tab) => <button type="button" role="tab" aria-selected={activeTab === tab} key={tab} onClick={() => setActiveTab(tab)} className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-semibold ${activeTab === tab ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500"}`}>{tab}</button>)}</div>

          {activeTab === "relationships" ? <section><h2 className="font-semibold text-slate-950">Commercial relationships</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[980px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Carriers</th><th className="px-3 py-2">Relationship</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Marketing</th><th className="px-3 py-2">Operating</th><th className="px-3 py-2">Validating</th><th className="px-3 py-2">Scope</th><th className="px-3 py-2">Freshness</th></tr></thead><tbody>{state?.relationships?.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.carrier_a_code} · {item.carrier_b_code}</td><td className="px-3 py-3">{item.relationship_type.replaceAll("_", " ")}</td><td className="px-3 py-3"><Status>{item.relationship_status}</Status></td><td className="px-3 py-3">{item.marketing_carrier_code || "Unknown"}</td><td className="px-3 py-3">{item.operating_carrier_code || "Unknown"}</td><td className="px-3 py-3">{item.validating_carrier_code || "Unknown"}</td><td className="px-3 py-3 text-slate-600">{[...(item.route_scope || []), ...(item.market_scope || [])].join(", ") || "General"}</td><td className="px-3 py-3"><Status>{item.freshness_status}</Status></td></tr>)}</tbody></table></div></section> : null}

          {activeTab === "responsibility matrix" ? <section><h2 className="font-semibold text-slate-950">Special-service responsibility matrix</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[1150px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Carriers</th><th className="px-3 py-2">Service</th><th className="px-3 py-2">Policy</th><th className="px-3 py-2">SSR</th><th className="px-3 py-2">Confirmation</th><th className="px-3 py-2">Pricing</th><th className="px-3 py-2">EMD</th><th className="px-3 py-2">Airport</th><th className="px-3 py-2">Status</th></tr></thead><tbody>{state?.responsibility_matrix?.map((item) => <tr className="border-t border-slate-200" key={item.record_id}><td className="px-3 py-3 font-semibold">{item.marketing_carrier || "Any"} / {item.operating_carrier}</td><td className="px-3 py-3">{String(item.service || "General").replaceAll("_", " ")}</td><td className="px-3 py-3">{item.policy_owner || "Unknown"}</td><td className="px-3 py-3">{item.ssr_owner || "Unknown"}</td><td className="px-3 py-3">{item.confirmation_owner || "Unknown"}</td><td className="px-3 py-3">{item.pricing_owner || "Unknown"}</td><td className="px-3 py-3">{item.emd_owner || "Unknown"}</td><td className="px-3 py-3">{item.airport_owner || "Unknown"}</td><td className="px-3 py-3"><Status>{item.status}</Status></td></tr>)}</tbody></table></div></section> : null}

          {["through check", "baggage", "EMD"].includes(activeTab) ? <section><h2 className="font-semibold text-slate-950">{activeTab} rules and exceptions</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{currentRows.map((item) => <div className="grid gap-2 py-3 md:grid-cols-[1fr_1fr_1fr_2fr]" key={item.id}><p className="font-semibold">{item.airline_code || item.marketing_carrier_code || item.operating_carrier_code} · {item.partner_airline_code || item.operating_carrier_code || item.validating_carrier_code}</p><Status>{item.rule_status || item.interline_emd_status || item.through_check_in_status}</Status><p className="text-sm text-slate-600">Confidence {item.confidence}</p><p className="text-sm text-slate-600">{item.recommended_action || item.minimum_connection_notes || item.most_significant_carrier_context || "Review evidence and scoped exceptions."}</p></div>)}</div></section> : null}

          {activeTab === "evidence" ? <section className="grid gap-6 lg:grid-cols-2"><div><h2 className="font-semibold text-slate-950">Evidence coverage</h2><dl className="mt-3 grid grid-cols-2 gap-3 border-y border-slate-200 py-4 text-sm"><dt className="text-slate-500">Evidence links</dt><dd className="font-semibold">{state?.summary?.evidence_link_count || 0}</dd><dt className="text-slate-500">Unknown rules</dt><dd className="font-semibold">{state?.summary?.unknown_count || 0}</dd><dt className="text-slate-500">Unsupported combinations</dt><dd className="font-semibold">{state?.summary?.unsupported_count || 0}</dd></dl></div><div><h2 className="font-semibold text-slate-950">Legacy source preservation</h2><p className="mt-3 border-y border-slate-200 py-4 text-sm text-slate-600">Existing airline interline agreements and EMD interline rules remain retained as source context. Phase 55.6 adds normalized, evidence-linked responsibility records without rewriting those sources.</p></div></section> : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
