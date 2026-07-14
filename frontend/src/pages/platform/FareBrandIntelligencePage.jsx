import { useEffect, useMemo, useState } from "react"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const tabs = ["fare families", "RBD mappings", "baggage rules", "attributes", "exceptions", "evidence & versioning"]

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  const value = String(children || "unknown")
  const tone = ["published", "known", "current", "included", "supported"].includes(value) ? "bg-emerald-50 text-emerald-800" : ["stale", "expired", "unsupported"].includes(value) ? "bg-rose-50 text-rose-800" : "bg-amber-50 text-amber-800"
  return <span className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${tone}`}>{value.replaceAll("_", " ")}</span>
}

export default function FareBrandIntelligencePage() {
  const [state, setState] = useState(null)
  const [airline, setAirline] = useState("")
  const [activeTab, setActiveTab] = useState("fare families")
  const [showEditor, setShowEditor] = useState(false)
  const [draft, setDraft] = useState({ airline_id: "", airline_code: "", family_code: "", family_name: "", cabin: "economy" })
  const [error, setError] = useState("")

  async function load() {
    const query = airline ? `?airline_code=${encodeURIComponent(airline)}` : ""
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/fare-brand-intelligence${query}`)])
    setState({ currentUser: summary.current_user, ...payload })
  }

  async function createFamily(event) {
    event.preventDefault()
    setError("")
    try {
      await apiPost("/api/platform/fare-brand-intelligence/fare-families", {
        ...draft,
        brand_code: draft.family_code,
        commercial_name: draft.family_name,
        publication_status: "draft",
        freshness_status: "unknown",
        agency_visibility_status: "platform_only",
      })
      setDraft({ airline_id: "", airline_code: "", family_code: "", family_name: "", cabin: "economy" })
      setShowEditor(false)
      await load()
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  const rows = useMemo(() => {
    if (activeTab === "RBD mappings") return state?.rbd_mappings || []
    if (activeTab === "baggage rules") return state?.baggage_rules || []
    if (activeTab === "attributes") return state?.attributes || []
    if (activeTab === "exceptions") return state?.baggage_exceptions || []
    return []
  }, [activeTab, state])

  return (
    <PlatformLayout user={state?.currentUser}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header>
            <p className="text-sm font-semibold uppercase text-blue-700">Commercial-product knowledge governance</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-950">Fare Family, RBD, Baggage & Brand Intelligence</h1>
            <p className="mt-1 max-w-5xl text-sm text-slate-600">Maintain evidence-linked fare-family hierarchy, booking-class mappings, commercial attributes, and contextual baggage rules.</p>
            <p className="mt-2 text-sm font-medium text-amber-800">Intelligence only. This workspace does not calculate fares, invent availability, connect to providers, book, or ticket.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Metric label="Airlines" value={state?.summary?.airline_count} />
            <Metric label="Fare families" value={state?.summary?.fare_family_count} />
            <Metric label="RBD mappings" value={state?.summary?.rbd_mapping_count} />
            <Metric label="Baggage rules" value={state?.summary?.baggage_rule_count} />
            <Metric label="Attributes" value={state?.summary?.attribute_count} />
            <Metric label="Needs review" value={state?.summary?.stale_or_incomplete_count} />
          </section>

          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load().catch((err) => setError(err.message)) }}>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="Airline code" value={airline} onChange={(event) => setAirline(event.target.value)} />
            <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Filter</button>
            <button type="button" title="Refresh intelligence" onClick={() => load().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 text-slate-700"><RefreshCw className="h-4 w-4" /></button>
            <button type="button" onClick={() => setShowEditor((value) => !value)} className="ml-auto inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700"><Plus className="h-4 w-4" />Fare family</button>
          </form>

          {showEditor ? <form className="grid gap-3 border-b border-slate-200 pb-5 sm:grid-cols-2 lg:grid-cols-5" onSubmit={createFamily}><label className="text-xs font-semibold uppercase text-slate-500">Canonical airline ID<input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.airline_id} onChange={(event) => setDraft({ ...draft, airline_id: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Airline code<input required maxLength="3" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={draft.airline_code} onChange={(event) => setDraft({ ...draft, airline_code: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Brand code<input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={draft.family_code} onChange={(event) => setDraft({ ...draft, family_code: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Commercial name<input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.family_name} onChange={(event) => setDraft({ ...draft, family_name: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Cabin<select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.cabin} onChange={(event) => setDraft({ ...draft, cabin: event.target.value })}><option value="economy">Economy</option><option value="premium_economy">Premium economy</option><option value="business">Business</option><option value="first">First</option></select></label><button className="w-fit rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create draft</button></form> : null}

          <div className="flex gap-1 overflow-x-auto border-b border-slate-200" role="tablist">{tabs.map((tab) => <button type="button" role="tab" aria-selected={activeTab === tab} key={tab} onClick={() => setActiveTab(tab)} className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-semibold ${activeTab === tab ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500"}`}>{tab}</button>)}</div>

          {activeTab === "fare families" ? <section><h2 className="font-semibold text-slate-950">Fare-family hierarchy editor</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[980px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Brand</th><th className="px-3 py-2">Commercial name</th><th className="px-3 py-2">Cabin</th><th className="px-3 py-2">Parent</th><th className="px-3 py-2">Channels</th><th className="px-3 py-2">Publication</th><th className="px-3 py-2">Freshness</th></tr></thead><tbody>{state?.fare_families?.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.airline_code || item.airline_id}</td><td className="px-3 py-3">{item.brand_code || item.family_code}</td><td className="px-3 py-3">{item.commercial_name || item.family_name}</td><td className="px-3 py-3">{item.cabin || "Unknown"}</td><td className="px-3 py-3">{item.parent_family_code || "Root"}</td><td className="px-3 py-3 text-slate-600">{item.distribution_channel_scope?.join(", ") || "All / unknown"}</td><td className="px-3 py-3"><Status>{item.publication_status}</Status></td><td className="px-3 py-3"><Status>{item.freshness_status}</Status></td></tr>)}</tbody></table></div></section> : null}

          {["RBD mappings", "baggage rules", "attributes", "exceptions"].includes(activeTab) ? <section><h2 className="font-semibold text-slate-950">{activeTab}</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[960px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Reference</th><th className="px-3 py-2">Brand / family</th><th className="px-3 py-2">Definition</th><th className="px-3 py-2">Scope</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Evidence</th></tr></thead><tbody>{rows.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3">{item.rbd_code || item.baggage_rule_reference || item.attribute_reference || item.baggage_exception_reference}</td><td className="px-3 py-3">{item.brand_code || item.fare_family_id || "Any"}</td><td className="px-3 py-3 text-slate-600">{item.attribute_label || item.baggage_concept || item.exception_type || `${item.cabin || "Unknown"} cabin`}</td><td className="px-3 py-3 text-slate-600">{[...(item.route_scope || []), ...(item.market_scope || [])].join(", ") || "General"}</td><td className="px-3 py-3"><Status>{item.mapping_status || item.allowance_status || item.attribute_status || item.exception_status}</Status></td><td className="px-3 py-3">{item.evidence_link_ids?.length || 0}</td></tr>)}</tbody></table></div></section> : null}

          {activeTab === "evidence & versioning" ? <section className="grid gap-6 lg:grid-cols-2"><div><h2 className="font-semibold text-slate-950">Evidence-linked product intelligence</h2><dl className="mt-3 grid grid-cols-2 gap-3 border-y border-slate-200 py-4 text-sm"><dt className="text-slate-500">Evidence links</dt><dd className="font-semibold">{state?.summary?.evidence_link_count || 0}</dd><dt className="text-slate-500">Stale or incomplete</dt><dd className="font-semibold">{state?.stale_or_incomplete?.length || 0}</dd><dt className="text-slate-500">Unknown RBD mappings</dt><dd className="font-semibold">{state?.summary?.unknown_mapping_count || 0}</dd></dl></div><div><h2 className="font-semibold text-slate-950">Versioning boundary</h2><p className="mt-3 border-y border-slate-200 py-4 text-sm text-slate-600">Fare families, RBD mappings, baggage rules, exceptions, commercial bundles, and comparison profiles are registered with the governed evidence and structured knowledge-version services. Existing fare-family and RBD source records remain preserved.</p></div></section> : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
