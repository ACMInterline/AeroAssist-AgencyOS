import { useEffect, useState } from "react"
import AlertTriangle from "lucide-react/dist/esm/icons/triangle-alert.js"
import Search from "lucide-react/dist/esm/icons/search.js"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

function Metric({ label, value }) {
  return <div className="rounded-md border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value || 0}</p></div>
}

function Status({ children }) {
  return <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{String(children || "unknown").replaceAll("_", " ")}</span>
}

export default function InterlineCodeshareAdvisorPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ marketing_carrier: "", operating_carrier: "", validating_carrier: "", origin: "", destination: "", service_code: "" })
  const [evaluation, setEvaluation] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const payload = await apiGet(`/api/agencies/${context.agency.id}/interline-codeshare-advisor`)
    setState({ ...context, ...payload })
  }

  async function evaluate(event) {
    event.preventDefault()
    setError("")
    try {
      const segment = { segment_reference: "SEG-1", marketing_carrier: form.marketing_carrier, operating_carrier: form.operating_carrier, origin: form.origin, destination: form.destination }
      if (form.validating_carrier) segment.validating_carrier = form.validating_carrier
      if (form.service_code) segment.service_requirements = [form.service_code]
      const payload = await apiPost(`/api/agencies/${state.agency.id}/interline-codeshare-advisor/evaluate`, { segments: [segment] })
      setEvaluation(payload)
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header><p className="text-sm font-semibold uppercase text-blue-700">Published carrier responsibility intelligence</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Interline & Codeshare Advisor</h1><p className="mt-1 max-w-5xl text-sm text-slate-600">Review marketed, operating, validating, ticketing, EMD, baggage, and special-service responsibility for an itinerary.</p><p className="mt-2 text-sm font-medium text-amber-800">Advisory only. Unknown or conditional results require carrier confirmation; this page does not book, ticket, issue an EMD, or contact a provider.</p></header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Metric label="Relationships" value={state?.summary?.relationship_count} /><Metric label="Interline profiles" value={state?.summary?.interline_agreement_count} /><Metric label="Responsibility rules" value={state?.summary?.responsibility_rule_count} /><Metric label="Unknown" value={state?.summary?.unknown_count} /><Metric label="Warnings" value={state?.warnings?.length} /></section>

          <form className="border-y border-slate-200 py-4" onSubmit={evaluate}><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6"><label className="text-xs font-semibold uppercase text-slate-500">Marketing carrier<input required maxLength="3" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={form.marketing_carrier} onChange={(event) => setForm({ ...form, marketing_carrier: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Operating carrier<input required maxLength="3" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={form.operating_carrier} onChange={(event) => setForm({ ...form, operating_carrier: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Validating carrier<input maxLength="3" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={form.validating_carrier} onChange={(event) => setForm({ ...form, validating_carrier: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Origin<input maxLength="3" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={form.origin} onChange={(event) => setForm({ ...form, origin: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Destination<input maxLength="3" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={form.destination} onChange={(event) => setForm({ ...form, destination: event.target.value })} /></label><label className="text-xs font-semibold uppercase text-slate-500">Service code<input placeholder="PETC" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase" value={form.service_code} onChange={(event) => setForm({ ...form, service_code: event.target.value })} /></label></div><button className="mt-3 inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"><Search className="h-4 w-4" />Evaluate responsibility</button></form>

          {evaluation ? <section><div className="flex flex-wrap items-end justify-between gap-2"><div><h2 className="font-semibold text-slate-950">Responsibility explanation</h2><p className="mt-1 text-sm text-slate-600">{evaluation.recommended_action}</p></div><Status>{evaluation.evaluation_status}</Status></div><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[1100px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Carrier map</th><th className="px-3 py-2">Policy</th><th className="px-3 py-2">SSR</th><th className="px-3 py-2">Confirmation</th><th className="px-3 py-2">Pricing</th><th className="px-3 py-2">Ticket</th><th className="px-3 py-2">EMD</th><th className="px-3 py-2">Baggage</th><th className="px-3 py-2">Airport</th></tr></thead><tbody>{evaluation.segments?.map((item) => <tr className="border-t border-slate-200" key={item.segment_reference}><td className="px-3 py-3 font-semibold">{item.carrier_roles.marketing_carrier} / {item.carrier_roles.operating_carrier}</td><td className="px-3 py-3">{item.responsibilities.policy_owner || "Unknown"}</td><td className="px-3 py-3">{item.responsibilities.ssr_request_owner || "Unknown"}</td><td className="px-3 py-3">{item.responsibilities.service_confirmation_owner || "Unknown"}</td><td className="px-3 py-3">{item.responsibilities.ancillary_pricing_owner || "Unknown"}</td><td className="px-3 py-3">{item.responsibilities.ticket_issue_owner || "Unknown"}</td><td className="px-3 py-3">{item.responsibilities.emd_issuer || "Unknown"}</td><td className="px-3 py-3">{item.responsibilities.baggage_rule_owner || "Unknown"}</td><td className="px-3 py-3">{item.responsibilities.airport_fulfillment_owner || "Unknown"}</td></tr>)}</tbody></table></div><div className="mt-4 grid gap-4 lg:grid-cols-2"><div><h3 className="text-sm font-semibold text-slate-950">Blockers and warnings</h3>{[...(evaluation.unsupported_combinations || []), ...(evaluation.warnings || [])].map((item, index) => <div className="mt-2 flex gap-2 text-sm text-slate-600" key={`${item.code || item.rule_family}-${index}`}><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" /><span>{item.reason || item.message}</span></div>)}</div><div><h3 className="text-sm font-semibold text-slate-950">Manual review requirements</h3>{evaluation.manual_review_requirements?.slice(0, 12).map((item, index) => <p className="mt-2 text-sm text-slate-600" key={`${item.segment_reference}-${item.area}-${index}`}><span className="font-semibold text-slate-900">{String(item.area).replaceAll("_", " ")}:</span> {item.reason}</p>)}</div></div></section> : null}

          {!evaluation ? <section><h2 className="font-semibold text-slate-950">Published responsibility matrix</h2><div className="mt-3 overflow-x-auto border-y border-slate-200"><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-3 py-2">Carriers</th><th className="px-3 py-2">Service</th><th className="px-3 py-2">Policy</th><th className="px-3 py-2">Confirmation</th><th className="px-3 py-2">EMD</th><th className="px-3 py-2">Status</th></tr></thead><tbody>{state?.responsibility_matrix?.map((item) => <tr className="border-t border-slate-200" key={item.record_id}><td className="px-3 py-3 font-semibold">{item.marketing_carrier || "Any"} / {item.operating_carrier}</td><td className="px-3 py-3">{String(item.service).replaceAll("_", " ")}</td><td className="px-3 py-3">{item.policy_owner || "Unknown"}</td><td className="px-3 py-3">{item.confirmation_owner || "Unknown"}</td><td className="px-3 py-3">{item.emd_owner || "Unknown"}</td><td className="px-3 py-3"><Status>{item.status}</Status></td></tr>)}</tbody></table></div></section> : null}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
