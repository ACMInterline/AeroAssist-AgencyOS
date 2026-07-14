import { useEffect, useState } from "react"
import Search from "lucide-react/dist/esm/icons/search.js"
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"
import { apiGet, apiPost } from "../../lib/api"

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  return <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{String(children || "unknown").replaceAll("_", " ")}</span>
}

export default function FareBrandLibraryPage() {
  const [state, setState] = useState(null)
  const [airline, setAirline] = useState("")
  const [comparison, setComparison] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const payload = await apiGet(`/api/agencies/${context.agency.id}/fare-brand-library`)
    setState({ ...context, ...payload })
  }

  async function compare(event) {
    event.preventDefault()
    setError("")
    try {
      const payload = await apiPost(`/api/agencies/${state.agency.id}/fare-brand-library/compare`, { airline_code: airline })
      setComparison(payload)
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header>
            <p className="text-sm font-semibold uppercase text-blue-700">Published commercial-product intelligence</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-950">Fare Brand Library</h1>
            <p className="mt-1 max-w-5xl text-sm text-slate-600">Compare governed fare-brand flexibility, included services, booking-class mappings, and baggage summaries for offer preparation.</p>
            <p className="mt-2 text-sm font-medium text-amber-800">Advisory and read-only. Confirm unknown, variable, and interline allowances against the ticketed fare; this page does not quote live prices or availability.</p>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Metric label="Airlines" value={state?.summary?.airline_count} /><Metric label="Fare families" value={state?.summary?.fare_family_count} /><Metric label="RBD mappings" value={state?.summary?.rbd_mapping_count} /><Metric label="Baggage rules" value={state?.summary?.baggage_rule_count} /><Metric label="Caveats" value={state?.operational_caveats?.length} /></section>

          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={compare}><input required maxLength="3" className="rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" placeholder="Airline code" value={airline} onChange={(event) => setAirline(event.target.value)} /><button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Compare published brands</button></form>

          {comparison ? <section><h2 className="font-semibold text-slate-950">Fare-brand comparison</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[1180px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Brand</th><th className="px-3 py-2">Cabin</th><th className="px-3 py-2">Baggage</th><th className="px-3 py-2">Changes</th><th className="px-3 py-2">Refunds</th><th className="px-3 py-2">Seats</th><th className="px-3 py-2">Meals</th><th className="px-3 py-2">Lounge</th><th className="px-3 py-2">Caveats</th></tr></thead><tbody>{comparison.rows?.map((item) => <tr className="border-t border-slate-200 align-top" key={item.fare_family_id}><td className="px-3 py-3"><p className="font-semibold">{item.label}</p><p className="text-xs text-slate-500">{item.airline_code} · {item.brand_code}</p></td><td className="px-3 py-3">{item.cabin || "Unknown"}</td><td className="px-3 py-3 text-slate-600">{item.baggage_summary}</td><td className="px-3 py-3"><Status>{item.attributes?.changeability?.status}</Status></td><td className="px-3 py-3"><Status>{item.attributes?.refundability?.status}</Status></td><td className="px-3 py-3"><Status>{item.attributes?.seat_selection?.status}</Status></td><td className="px-3 py-3"><Status>{item.attributes?.meals?.status}</Status></td><td className="px-3 py-3"><Status>{item.attributes?.lounge?.status}</Status></td><td className="px-3 py-3 text-slate-600">{[...(item.operational_caveats || []), ...(item.warnings || [])].join(" ") || "None recorded"}</td></tr>)}</tbody></table></div></section> : null}

          {!comparison ? <section><h2 className="font-semibold text-slate-950">Published fare families</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Brand</th><th className="px-3 py-2">Cabin</th><th className="px-3 py-2">Hierarchy</th><th className="px-3 py-2">Channels</th><th className="px-3 py-2">Freshness</th></tr></thead><tbody>{state?.fare_families?.map((item) => <tr className="border-t border-slate-200" key={item.id}><td className="px-3 py-3 font-semibold">{item.airline_code}</td><td className="px-3 py-3">{item.client_safe_label || item.commercial_name || item.family_name}</td><td className="px-3 py-3">{item.cabin || "Unknown"}</td><td className="px-3 py-3">Level {item.hierarchy_level || 0}</td><td className="px-3 py-3 text-slate-600">{item.distribution_channel_scope?.join(", ") || "All / unknown"}</td><td className="px-3 py-3"><Status>{item.freshness_status}</Status></td></tr>)}</tbody></table></div></section> : null}

          {state?.operational_caveats?.length ? <section><h2 className="font-semibold text-slate-950">Operational caveats</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state.operational_caveats.map((item, index) => <div className="flex gap-3 py-3 text-sm text-slate-600" key={`${item.record_id}-${index}`}><TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" /><p>{item.message}</p></div>)}</div></section> : null}

          <section><h2 className="font-semibold text-slate-950">Offer-builder integration</h2><p className="mt-3 border-y border-slate-200 py-4 text-sm text-slate-600">Published client-safe brand labels, commercial attributes, baggage summaries, and operational caveats are available to existing offer-intelligence packages. Internal evidence notes remain excluded, and the offer builder must not invent missing intelligence.</p></section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
