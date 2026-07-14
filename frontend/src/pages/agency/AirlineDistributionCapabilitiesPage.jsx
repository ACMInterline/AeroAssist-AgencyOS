import { useEffect, useState } from "react"
import AlertTriangle from "lucide-react/dist/esm/icons/triangle-alert.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  return <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{String(children || "unknown").replaceAll("_", " ")}</span>
}

export default function AirlineDistributionCapabilitiesPage() {
  const [state, setState] = useState(null)
  const [airline, setAirline] = useState("")
  const [channel, setChannel] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const params = new URLSearchParams()
    if (airline) params.set("airline_code", airline)
    if (channel) params.set("channel_code", channel)
    const query = params.toString() ? `?${params}` : ""
    const payload = await apiGet(`/api/agencies/${context.agency.id}/distribution-capabilities${query}`)
    setState({ ...context, ...payload })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Published distribution intelligence</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Distribution Capabilities</h1><p className="mt-1 max-w-5xl text-sm text-slate-600">Published channel availability, capability warnings, fallback methods, and booking-handoff planning context.</p><p className="mt-2 text-sm font-medium text-amber-800">Read-only planning guidance. A listed channel does not activate or confirm live provider connectivity.</p></header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Metric label="Available channels" value={state?.booking_handoff?.available_channel_count} /><Metric label="Published channels" value={state?.summary?.channel_count} /><Metric label="Capabilities" value={state?.summary?.capability_count} /><Metric label="Manual handling" value={state?.summary?.manual_handling_count} /><Metric label="Warnings" value={state?.warnings?.length} /></section>

          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load().catch((err) => setError(err.message)) }}><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline code" value={airline} onChange={(event) => setAirline(event.target.value)} /><select className="min-w-56 rounded-md border border-slate-300 px-3 py-2 text-sm" value={channel} onChange={(event) => setChannel(event.target.value)}><option value="">All channels</option>{state?.filters?.distribution_channels?.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select><button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Filter</button></form>

          <section><div className="flex items-end justify-between gap-3"><div><h2 className="font-semibold text-slate-950">Operationally available channels</h2><p className="mt-1 text-sm text-slate-500">Availability means suitable for human planning from published metadata.</p></div><Status>no live execution</Status></div><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[980px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Channel</th><th className="px-3 py-2">Capability</th><th className="px-3 py-2">Provider stage</th><th className="px-3 py-2">Planning availability</th><th className="px-3 py-2">Handling</th><th className="px-3 py-2">Fallback</th><th className="px-3 py-2">Freshness</th></tr></thead><tbody>{state?.operational_channels?.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3"><span className="block font-medium">{item.channel_name}</span><span className="text-xs text-slate-500">{item.provider_name || item.channel_code.replaceAll("_", " ")}</span></td><td className="px-3 py-3"><Status>{item.capability_status}</Status></td><td className="px-3 py-3"><Status>{item.provider_stage}</Status></td><td className="px-3 py-3">{item.planning_availability_status.replaceAll("_", " ")}</td><td className="px-3 py-3">{item.manual_handling_indicator ? "Manual" : "Human reviewed"}</td><td className="px-3 py-3 text-slate-600">{item.fallback_method || "No published fallback"}</td><td className="px-3 py-3">{String(item.freshness_status || "unknown").replaceAll("_", " ")}</td></tr>)}</tbody></table></div>{!state?.operational_channels?.length ? <p className="mt-4 text-sm text-slate-600">No published distribution capability records match this view.</p> : null}</section>

          <div className="grid gap-6 xl:grid-cols-2">
            <section><h2 className="font-semibold text-slate-950">Capability warnings</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.warnings?.map((warning, index) => <div className="flex gap-3 py-3" key={`${warning.airline_code}-${warning.channel_code}-${warning.warning_type}-${index}`}><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" /><div><p className="text-sm font-semibold text-slate-950">{warning.airline_code} · {String(warning.channel_code || "channel").replaceAll("_", " ")}</p><p className="mt-1 text-sm text-slate-600">{warning.message}</p></div></div>)}</div></section>
            <section><h2 className="font-semibold text-slate-950">Booking handoff context</h2><div className="mt-3 border-y border-slate-200 py-3"><dl className="grid grid-cols-2 gap-3 text-sm"><dt className="text-slate-500">Published channels</dt><dd className="font-semibold">{state?.booking_handoff?.channel_count || 0}</dd><dt className="text-slate-500">Available for planning</dt><dd className="font-semibold">{state?.booking_handoff?.available_channel_count || 0}</dd><dt className="text-slate-500">Manual review</dt><dd>{state?.booking_handoff?.manual_review_required ? "Required" : "No additional warning"}</dd><dt className="text-slate-500">Live connectivity</dt><dd>Not confirmed</dd></dl><div className="mt-4 space-y-2">{state?.fallback_methods?.map((item, index) => <p className="text-sm text-slate-600" key={`${item.airline_code}-${item.channel_code}-${index}`}><span className="font-semibold text-slate-900">{item.airline_code}:</span> {item.fallback_method}</p>)}</div></div></section>
          </div>

          <div className="grid gap-6 xl:grid-cols-3"><section><h2 className="font-semibold text-slate-950">PSS context</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.pss_profiles?.map((item) => <div className="py-3" key={item.id}><p className="font-semibold">{item.airline_code} · {item.known_pss || "Unknown PSS"}</p><p className="mt-1 text-sm text-slate-600">Reservation {item.reservation_host || "unknown"} · Ticketing {item.ticketing_host || "unknown"}</p></div>)}</div></section><section><h2 className="font-semibold text-slate-950">GDS coverage</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.gds_participations?.map((item) => <div className="py-3" key={item.id}><p className="font-semibold">{item.airline_code} · {item.gds_code}</p><p className="mt-1 text-sm text-slate-600">Booking {item.booking_status} · Ticketing {item.ticketing_status}</p></div>)}</div></section><section><h2 className="font-semibold text-slate-950">NDC coverage</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.ndc_capabilities?.map((item) => <div className="py-3" key={item.id}><p className="font-semibold">{item.airline_code} · {item.ndc_type.replaceAll("_", " ")}</p><p className="mt-1 text-sm text-slate-600">{item.provider_name || "Airline direct"} · {item.capability_status}</p></div>)}</div></section></div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
