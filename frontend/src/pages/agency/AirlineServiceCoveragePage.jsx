import { useEffect, useState } from "react"
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

export default function AirlineServiceCoveragePage() {
  const [state, setState] = useState(null)
  const [airline, setAirline] = useState("")
  const [family, setFamily] = useState("")
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const params = new URLSearchParams()
    if (airline) params.set("airline_code", airline)
    if (family) params.set("service_family", family)
    const query = params.toString() ? `?${params}` : ""
    const payload = await apiGet(`/api/agencies/${context.agency.id}/airline-service-coverage${query}`)
    setState({ ...context, ...payload })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Published airline intelligence</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Service Coverage</h1><p className="mt-1 max-w-4xl text-sm text-slate-600">Usable published service coverage, effective dates, confidence, and missing or unknown operational warnings.</p></header>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Metric label="Published coverage" value={state?.summary?.published_cell_count} /><Metric label="Operationally usable" value={state?.summary?.operationally_usable_cell_count} /><Metric label="Warnings" value={state?.summary?.missing_or_unknown_warning_count} /><Metric label="Airlines" value={state?.summary?.airline_count} /></section>
          <form className="flex flex-wrap gap-2 border-y border-slate-200 py-4" onSubmit={(event) => { event.preventDefault(); load().catch((err) => setError(err.message)) }}><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline code" value={airline} onChange={(event) => setAirline(event.target.value)} /><select className="min-w-56 rounded-md border border-slate-300 px-3 py-2 text-sm" value={family} onChange={(event) => setFamily(event.target.value)}><option value="">All service families</option>{state?.filters?.service_catalog?.map((item) => <option key={item.service_family} value={item.service_family}>{item.service_family.replaceAll("_", " ")}</option>)}</select><button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Filter</button></form>

          <section><h2 className="font-semibold text-slate-950">Usable published coverage</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[860px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Airline</th><th className="px-3 py-2">Service</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Confidence</th><th className="px-3 py-2">Freshness</th><th className="px-3 py-2">Effective</th><th className="px-3 py-2">Scope</th></tr></thead><tbody>{state?.usable_cells?.map((cell) => <tr className="border-t border-slate-200" key={cell.id}><td className="px-3 py-3 font-semibold">{cell.airline_code}</td><td className="px-3 py-3">{cell.service_family.replaceAll("_", " ")} {cell.service_code ? `· ${cell.service_code}` : ""}</td><td className="px-3 py-3"><Status>{cell.coverage_status}</Status></td><td className="px-3 py-3">{cell.confidence_score}</td><td className="px-3 py-3">{cell.evidence_freshness.replaceAll("_", " ")}</td><td className="px-3 py-3">{cell.effective_from ? new Date(cell.effective_from).toLocaleDateString() : "Not stated"}</td><td className="px-3 py-3">{cell.distribution_channel || "Published scope"}</td></tr>)}</tbody></table></div>{!state?.usable_cells?.length ? <p className="mt-4 text-sm text-slate-600">No operationally usable published coverage matches this view.</p> : null}</section>

          <div className="grid gap-6 lg:grid-cols-2">
            <section><h2 className="font-semibold text-slate-950">Missing or unknown</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.warnings?.map((warning, index) => <div className="py-3" key={`${warning.airline_code}-${warning.service_family}-${warning.service_code || index}`}><p className="text-sm font-semibold text-slate-950">{warning.airline_code} · {warning.service_family.replaceAll("_", " ")}</p><p className="mt-1 text-sm text-slate-600">{warning.message}</p></div>)}</div></section>
            <section><h2 className="font-semibold text-slate-950">Alternative airline hints</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.alternative_airline_hints?.map((hint) => <div className="py-3" key={hint.airline_code}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold text-slate-950">{hint.airline_code}</p><p className="mt-1 text-sm text-slate-600">{hint.message}</p></div><Status>{hint.recommendation_level || "coverage available"}</Status></div><p className="mt-2 text-xs text-slate-500">Usability {hint.operational_usability_score} · {hint.service_families.join(", ")}</p></div>)}</div></section>
          </div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
