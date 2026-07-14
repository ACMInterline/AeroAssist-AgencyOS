import { useEffect, useMemo, useState } from "react"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const tabs = ["overview", "shopping", "booking", "fulfillment", "servicing", "pss and hosts", "evidence"]

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children, tone = "slate" }) {
  const tones = { slate: "bg-slate-100 text-slate-700", blue: "bg-blue-100 text-blue-800", amber: "bg-amber-100 text-amber-800", green: "bg-emerald-100 text-emerald-800", red: "bg-rose-100 text-rose-800" }
  return <span className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${tones[tone] || tones.slate}`}>{String(children || "unknown").replaceAll("_", " ")}</span>
}

function statusTone(value) {
  if (["supported", "production_enabled_provider", "current"].includes(value)) return "green"
  if (["unsupported", "stale", "expired"].includes(value)) return "red"
  if (["conditional", "manual_only", "review_due", "configured_provider", "tested_sandbox"].includes(value)) return "amber"
  return "slate"
}

export default function AirlineDistributionCapabilitiesPage() {
  const [state, setState] = useState(null)
  const [airline, setAirline] = useState("")
  const [channel, setChannel] = useState("")
  const [activeTab, setActiveTab] = useState("overview")
  const [error, setError] = useState("")

  async function load() {
    const params = new URLSearchParams()
    if (airline) params.set("airline_code", airline)
    if (channel) params.set("channel_code", channel)
    const query = params.toString() ? `?${params}` : ""
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/airline-distribution-capabilities${query}`)])
    setState({ currentUser: summary.current_user, ...payload })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  const areaRecords = useMemo(() => {
    if (!["shopping", "booking", "fulfillment", "servicing"].includes(activeTab)) return []
    if (activeTab === "fulfillment") return state?.fulfillment_capabilities || []
    if (activeTab === "servicing") return state?.servicing_capabilities || []
    return (state?.capabilities || []).filter((item) => item.capability_area === activeTab)
  }, [activeTab, state])

  return (
    <PlatformLayout user={state?.currentUser}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header>
            <p className="text-sm font-semibold uppercase text-blue-700">Distribution intelligence</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Distribution Capabilities</h1>
            <p className="mt-1 max-w-5xl text-sm text-slate-600">Governed shopping, booking, fulfillment, and servicing capability metadata across direct, GDS, NDC, partner, and manual channels.</p>
            <p className="mt-2 text-sm font-medium text-amber-800">Planning intelligence only. Documented capability is separate from configured, sandbox-tested, and production-enabled provider status, and none confirms live connectivity.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Metric label="Airlines" value={state?.summary?.airline_count} />
            <Metric label="Channels" value={state?.summary?.channel_count} />
            <Metric label="Capabilities" value={state?.summary?.capability_count} />
            <Metric label="GDS participation" value={state?.summary?.gds_participation_count} />
            <Metric label="NDC records" value={state?.summary?.ndc_capability_count} />
            <Metric label="Restrictions" value={state?.summary?.restriction_count} />
          </section>

          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load().catch((err) => setError(err.message)) }}>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline code" value={airline} onChange={(event) => setAirline(event.target.value)} />
            <select className="min-w-56 rounded-md border border-slate-300 px-3 py-2 text-sm" value={channel} onChange={(event) => setChannel(event.target.value)}><option value="">All channels</option>{state?.filters?.distribution_channels?.map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}</select>
            <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Filter</button>
            <button type="button" title="Refresh capability intelligence" onClick={() => load().catch((err) => setError(err.message))} className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 text-slate-700"><RefreshCw className="h-4 w-4" /></button>
          </form>

          <div className="flex gap-1 overflow-x-auto border-b border-slate-200" role="tablist">{tabs.map((tab) => <button type="button" role="tab" aria-selected={activeTab === tab} key={tab} onClick={() => setActiveTab(tab)} className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-semibold ${activeTab === tab ? "border-blue-600 text-blue-700" : "border-transparent text-slate-500"}`}>{tab.replaceAll("_", " ")}</button>)}</div>

          {activeTab === "overview" ? <section>
            <div className="flex flex-wrap items-end justify-between gap-2"><div><h2 className="font-semibold text-slate-950">Airline × channel matrix</h2><p className="mt-1 text-sm text-slate-500">Capability state and provider readiness are intentionally separate.</p></div><Status tone="blue">live connectivity disabled</Status></div>
            <div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[1100px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Channel</th><th className="px-3 py-2">Capability</th><th className="px-3 py-2">Provider stage</th><th className="px-3 py-2">Shopping</th><th className="px-3 py-2">Booking</th><th className="px-3 py-2">Fulfillment</th><th className="px-3 py-2">Servicing</th><th className="px-3 py-2">Restrictions</th><th className="px-3 py-2">Handling</th></tr></thead><tbody>{state?.matrix?.map((item) => <tr className="border-t border-slate-200" key={item.channel_id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3"><span className="block font-medium">{item.channel_name}</span><span className="text-xs text-slate-500">{item.provider_name || item.channel_code.replaceAll("_", " ")}</span></td><td className="px-3 py-3"><Status tone={statusTone(item.capability_status)}>{item.capability_status}</Status></td><td className="px-3 py-3"><Status tone={statusTone(item.provider_stage)}>{item.provider_stage}</Status></td>{["shopping", "booking", "fulfillment", "servicing"].map((area) => <td className="px-3 py-3" key={area}><Status tone={statusTone(item.area_statuses?.[area])}>{item.area_statuses?.[area]}</Status></td>)}<td className="px-3 py-3">{item.restriction_count || 0}</td><td className="px-3 py-3">{item.manual_handling_required ? "Manual" : "Human reviewed"}</td></tr>)}</tbody></table></div>
            {!state?.matrix?.length ? <p className="mt-4 text-sm text-slate-600">No governed distribution channel records match this view.</p> : null}
          </section> : null}

          {["shopping", "booking", "fulfillment", "servicing"].includes(activeTab) ? <section><h2 className="font-semibold text-slate-950">{activeTab[0].toUpperCase() + activeTab.slice(1)} capability detail</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Channel</th><th className="px-3 py-2">Capability</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Provider stage</th><th className="px-3 py-2">Freshness</th><th className="px-3 py-2">Provider notes</th></tr></thead><tbody>{areaRecords.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3">{item.channel_code || "Any governed channel"}</td><td className="px-3 py-3">{String(item.capability_code || item.capability_name).replaceAll("_", " ")}</td><td className="px-3 py-3"><Status tone={statusTone(item.capability_status)}>{item.capability_status}</Status></td><td className="px-3 py-3"><Status tone={statusTone(item.provider_stage)}>{item.provider_stage}</Status></td><td className="px-3 py-3">{String(item.freshness_status || "unknown").replaceAll("_", " ")}</td><td className="px-3 py-3 text-slate-600">{item.provider_specific_notes || "No published provider-specific note"}</td></tr>)}</tbody></table></div></section> : null}

          {activeTab === "pss and hosts" ? <div className="grid gap-6 xl:grid-cols-3">
            <section><h2 className="font-semibold text-slate-950">PSS and host summary</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.pss_profiles?.map((item) => <div className="py-3" key={item.id}><div className="flex items-start justify-between gap-3"><p className="font-semibold">{item.airline_code}</p><Status tone={statusTone(item.freshness_status)}>{item.freshness_status}</Status></div><dl className="mt-2 grid grid-cols-2 gap-2 text-sm"><dt className="text-slate-500">Known PSS</dt><dd>{item.known_pss || "Unknown"}</dd><dt className="text-slate-500">Reservation host</dt><dd>{item.reservation_host || "Unknown"}</dd><dt className="text-slate-500">Ticketing host</dt><dd>{item.ticketing_host || "Unknown"}</dd><dt className="text-slate-500">EMD host</dt><dd>{item.emd_host || "Unknown"}</dd></dl></div>)}</div></section>
            <section><h2 className="font-semibold text-slate-950">GDS participation</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.gds_participations?.map((item) => <div className="py-3" key={item.id}><div className="flex justify-between gap-3"><p className="font-semibold">{item.airline_code} · {item.gds_code}</p><Status tone={statusTone(item.provider_stage)}>{item.provider_stage}</Status></div><p className="mt-2 text-sm text-slate-600">Shopping {item.shopping_status} · Booking {item.booking_status} · Ticketing {item.ticketing_status} · Servicing {item.servicing_status}</p></div>)}</div></section>
            <section><h2 className="font-semibold text-slate-950">NDC coverage</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.ndc_capabilities?.map((item) => <div className="py-3" key={item.id}><div className="flex justify-between gap-3"><p className="font-semibold">{item.airline_code} · {item.ndc_type.replaceAll("_", " ")}</p><Status tone={statusTone(item.capability_status)}>{item.capability_status}</Status></div><p className="mt-2 text-sm text-slate-600">{item.provider_name || "Airline direct"} · version {item.ndc_standard_version || "unknown"}</p></div>)}</div></section>
          </div> : null}

          {activeTab === "evidence" ? <div className="grid gap-6 xl:grid-cols-2"><section><h2 className="font-semibold text-slate-950">Restrictions</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.restrictions?.map((item) => <div className="py-3" key={item.id}><div className="flex justify-between gap-3"><p className="font-semibold">{item.airline_code} · {item.title}</p><Status>{item.restriction_status}</Status></div><p className="mt-1 text-sm text-slate-600">{item.description}</p><p className="mt-2 text-xs text-slate-500">Fallback: {item.fallback_method || "Human review required"}</p></div>)}</div></section><section><h2 className="font-semibold text-slate-950">Evidence and freshness</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.evidence_links?.map((item) => <div className="py-3" key={item.id}><div className="flex justify-between gap-3"><p className="font-semibold">{item.airline_code} · {item.target_type.replaceAll("_", " ")}</p><Status tone={statusTone(item.freshness_status)}>{item.freshness_status}</Status></div><p className="mt-1 text-sm text-slate-600">{item.authority_level} authority · {item.confidence} confidence · {item.evidence_status}</p></div>)}</div></section></div> : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
