import { useEffect, useMemo, useState } from "react"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const tabs = ["directory", "templates", "escalation paths", "verification & evidence", "stale contacts"]

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  const value = String(children || "unknown")
  const tone = ["active", "verified", "published", "current"].includes(value) ? "bg-emerald-50 text-emerald-800" : ["stale", "expired", "failed", "inactive"].includes(value) ? "bg-rose-50 text-rose-800" : "bg-amber-50 text-amber-800"
  return <span className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${tone}`}>{value.replaceAll("_", " ")}</span>
}

export default function AirlineContactIntelligencePage() {
  const [state, setState] = useState(null)
  const [activeTab, setActiveTab] = useState("directory")
  const [airline, setAirline] = useState("")
  const [desk, setDesk] = useState("")
  const [showEditor, setShowEditor] = useState(false)
  const [draft, setDraft] = useState({ airline_code: "", desk_type: "general_agency_support", contact_name: "" })
  const [error, setError] = useState("")

  async function load() {
    const params = new URLSearchParams()
    if (airline) params.set("airline_code", airline)
    if (desk) params.set("desk_type", desk)
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/airline-contact-intelligence${params.size ? `?${params}` : ""}`)])
    setState({ currentUser: summary.current_user, ...payload })
  }

  async function createContact(event) {
    event.preventDefault()
    setError("")
    try {
      await apiPost("/api/platform/airline-contact-intelligence/contacts", {
        ...draft,
        contact_status: "unverified",
        verification_status: "pending",
        freshness_status: "unknown",
        publication_status: "draft",
        agency_visibility_status: "platform_only",
      })
      setDraft({ airline_code: "", desk_type: "general_agency_support", contact_name: "" })
      setShowEditor(false)
      await load()
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  const verificationRows = useMemo(() => state?.verifications || [], [state])

  return (
    <PlatformLayout user={state?.currentUser}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header>
            <p className="text-sm font-semibold uppercase text-blue-700">Governed supplier communication intelligence</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Contact & Communication Intelligence</h1>
            <p className="mt-1 max-w-5xl text-sm text-slate-600">Govern airline desks, channels, operational scope, hours, escalation paths, communication requirements, templates, verification, and evidence.</p>
            <p className="mt-2 text-sm font-medium text-amber-800">Intelligence only. No credentials are stored and this workspace does not send messages, call providers, or trigger automatic escalation.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Metric label="Airlines" value={state?.summary?.airline_count} />
            <Metric label="Contacts" value={state?.summary?.contact_count} />
            <Metric label="Channels" value={state?.summary?.channel_count} />
            <Metric label="Templates" value={state?.summary?.template_count} />
            <Metric label="Verified" value={state?.summary?.verified_contact_count} />
            <Metric label="Stale / review" value={state?.summary?.stale_contact_count} />
          </section>

          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load().catch((err) => setError(err.message)) }}>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="Airline code" value={airline} onChange={(event) => setAirline(event.target.value)} />
            <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={desk} onChange={(event) => setDesk(event.target.value)}><option value="">All desks</option>{state?.filters?.desk_types?.map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}</select>
            <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Filter</button>
            <button type="button" title="Refresh contact intelligence" onClick={() => load().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 text-slate-700"><RefreshCw className="h-4 w-4" /></button>
            <button type="button" onClick={() => setShowEditor((value) => !value)} className="ml-auto inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700"><Plus className="h-4 w-4" />Contact</button>
          </form>

          {showEditor ? <form className="grid gap-3 border-b border-slate-200 pb-5 sm:grid-cols-2 lg:grid-cols-4" onSubmit={createContact}><label className="text-xs font-semibold uppercase text-slate-500">Airline code<input required maxLength="3" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={draft.airline_code} onChange={(event) => setDraft({ ...draft, airline_code: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Desk type<select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.desk_type} onChange={(event) => setDraft({ ...draft, desk_type: event.target.value })}>{state?.filters?.desk_types?.map((item) => <option value={item} key={item}>{item.replaceAll("_", " ")}</option>)}</select></label><label className="text-xs font-semibold uppercase text-slate-500">Contact name<input required className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.contact_name} onChange={(event) => setDraft({ ...draft, contact_name: event.target.value })} /></label><button className="mt-5 h-10 w-fit rounded-md bg-blue-600 px-3 text-sm font-semibold text-white">Create draft</button></form> : null}

          <div className="flex gap-1 overflow-x-auto border-b border-slate-200" role="tablist">{tabs.map((tab) => <button type="button" role="tab" aria-selected={activeTab === tab} key={tab} onClick={() => setActiveTab(tab)} className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-semibold ${activeTab === tab ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500"}`}>{tab}</button>)}</div>

          {activeTab === "directory" ? <section><h2 className="font-semibold text-slate-950">Governed directory</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[1100px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Desk</th><th className="px-3 py-2">Contact</th><th className="px-3 py-2">Market / airport</th><th className="px-3 py-2">Languages</th><th className="px-3 py-2">Response</th><th className="px-3 py-2">Verification</th><th className="px-3 py-2">Publication</th></tr></thead><tbody>{state?.contacts?.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3">{item.desk_type?.replaceAll("_", " ")}</td><td className="px-3 py-3">{item.contact_name}</td><td className="px-3 py-3 text-slate-600">{[...(item.market_scope || []), ...(item.airport_scope || [])].join(", ") || "General"}</td><td className="px-3 py-3">{item.language_codes?.join(", ") || "Unknown"}</td><td className="px-3 py-3">{item.expected_response_minutes ? `${item.expected_response_minutes} min` : "Unknown"}</td><td className="px-3 py-3"><Status>{item.verification_status}</Status></td><td className="px-3 py-3"><Status>{item.publication_status}</Status></td></tr>)}</tbody></table></div></section> : null}

          {activeTab === "templates" ? <section><h2 className="font-semibold text-slate-950">Separated communication templates</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.templates?.map((item) => <article className="grid gap-4 py-4 lg:grid-cols-4" key={item.id}><div><p className="font-semibold text-slate-950">{item.template_name}</p><p className="mt-1 text-xs text-slate-500">{item.airline_code || "Generic"} · {item.template_type?.replaceAll("_", " ")}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Internal instruction</p><p className="mt-1 text-sm text-slate-600">{item.internal_instructions || "None"}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Supplier message</p><p className="mt-1 text-sm text-slate-600">{item.supplier_message_template}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Client status</p><p className="mt-1 text-sm text-slate-600">{item.client_status_message_template || "None"}</p></div></article>)}</div></section> : null}

          {activeTab === "escalation paths" ? <section><h2 className="font-semibold text-slate-950">Manual escalation paths</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Desk</th><th className="px-3 py-2">Path</th><th className="px-3 py-2">Trigger</th><th className="px-3 py-2">Steps</th><th className="px-3 py-2">Status</th></tr></thead><tbody>{state?.escalation_paths?.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3">{item.desk_type?.replaceAll("_", " ")}</td><td className="px-3 py-3">{item.path_name}</td><td className="px-3 py-3">{item.trigger_after_minutes ? `${item.trigger_after_minutes} min` : "Manual"}</td><td className="px-3 py-3">{item.escalation_steps?.length || 0}</td><td className="px-3 py-3"><Status>{item.path_status}</Status></td></tr>)}</tbody></table></div><p className="mt-3 text-sm text-slate-600">Escalation paths are recommendations only and never run automatically.</p></section> : null}

          {activeTab === "verification & evidence" ? <section className="grid gap-6 lg:grid-cols-2"><div><h2 className="font-semibold text-slate-950">Verification history</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{verificationRows.map((item) => <div className="flex items-center justify-between gap-3 py-3 text-sm" key={item.id}><div><p className="font-semibold">{item.airline_code} · {item.target_type?.replaceAll("_", " ")}</p><p className="text-slate-500">{item.verification_method?.replaceAll("_", " ")} · {item.verified_at ? new Date(item.verified_at).toLocaleString() : "Pending"}</p></div><Status>{item.verification_status}</Status></div>)}</div></div><div><h2 className="font-semibold text-slate-950">Evidence governance</h2><dl className="mt-3 grid grid-cols-2 gap-3 border-y border-slate-200 py-4 text-sm"><dt className="text-slate-500">Evidence-linked contacts</dt><dd className="font-semibold">{state?.contacts?.filter((item) => item.evidence_link_ids?.length).length || 0}</dd><dt className="text-slate-500">Review due</dt><dd className="font-semibold">{state?.summary?.stale_contact_count || 0}</dd><dt className="text-slate-500">Restricted channels</dt><dd className="font-semibold">{state?.channels?.filter((item) => ["restricted_internal", "platform_only"].includes(item.access_classification)).length || 0}</dd></dl></div></section> : null}

          {activeTab === "stale contacts" ? <section><h2 className="font-semibold text-slate-950">Freshness review queue</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.stale_contacts?.map((item) => <div className="flex items-center justify-between gap-3 py-3 text-sm" key={item.id}><div><p className="font-semibold">{item.airline_code} · {item.contact_name}</p><p className="text-slate-500">{item.desk_type?.replaceAll("_", " ")} · next review {item.next_review_at ? new Date(item.next_review_at).toLocaleDateString() : "not set"}</p></div><Status>{item.freshness_status}</Status></div>)}</div></section> : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
