import { useEffect, useMemo, useState } from "react"
import ConfidenceBadge from "../../components/ConfidenceBadge"
import EmptyState from "../../components/EmptyState"
import KnowledgeCategoryBadge from "../../components/KnowledgeCategoryBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ReviewStatusBadge from "../../components/ReviewStatusBadge"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const categories = ["", "booking_policy", "servicing_policy", "special_service", "baggage", "pet_travel", "accessibility", "unaccompanied_minor", "medical_travel", "documents", "contact", "payment", "refund_exchange", "schedule_change", "disruption", "emd", "fare_family", "operational_note", "other"]

export default function AirlineIntelligencePage() {
  const params = useMemo(() => new URLSearchParams(window.location.search), [])
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState({ q: params.get("q") || params.get("service_code") || "", airline: params.get("airline") || "", category: "", service_code: params.get("service_code") || "", confidence: "", tag: "" })
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = new URLSearchParams()
    Object.entries(nextFilters).forEach(([key, value]) => {
      if (value) query.set(key, value)
    })
    const results = await apiGet(`/api/agencies/${context.agency.id}/airline-intelligence/search?${query.toString()}`)
    setState({ ...context, results })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [])

  function setField(name, value) {
    setFilters((current) => ({ ...current, [name]: value }))
  }

  async function runSearch(event) {
    event.preventDefault()
    await load(filters)
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Search Airline Knowledge</h2>
            <p className="mt-1 text-sm text-slate-600">Decision support, verify before action.</p>
          </div>
          <form className="rounded-lg border border-slate-200 bg-white p-5" onSubmit={runSearch}>
            <div className="grid gap-3 md:grid-cols-[1fr_150px_180px_140px_140px_auto]">
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Keyword, code, service, tag" value={filters.q} onChange={(event) => setField("q", event.target.value)} />
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Airline" value={filters.airline} onChange={(event) => setField("airline", event.target.value.toUpperCase())} />
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.category} onChange={(event) => setField("category", event.target.value)}>{categories.map((item) => <option value={item} key={item}>{item ? item.replaceAll("_", " ") : "Any category"}</option>)}</select>
              <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Service" value={filters.service_code} onChange={(event) => setField("service_code", event.target.value.toUpperCase())} />
              <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={filters.confidence} onChange={(event) => setField("confidence", event.target.value)}>
                <option value="">Any confidence</option>
                {["low", "medium", "high", "official_source"].map((item) => <option key={item}>{item}</option>)}
              </select>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Search</button>
            </div>
          </form>
          {!state.results.items.length ? <EmptyState title="No matching airline knowledge" body="Try a service code like PETC, WCHR, WCHS, WCHC, UMNR, or BAG." /> : (
            <div className="grid gap-4">
              {state.results.items.map((item) => (
                <article className="rounded-lg border border-slate-200 bg-white p-5" key={item.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.airline.airline_code} · {item.airline.airline_name}</p>
                      <a className="mt-1 block text-lg font-semibold text-blue-700" href={`/agency/airline-knowledge/${item.id}`}>{item.title}</a>
                      <p className="mt-2 text-sm text-slate-600">{item.summary}</p>
                    </div>
                    {item.has_agency_override ? <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 ring-1 ring-amber-200">agency override</span> : null}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2"><KnowledgeCategoryBadge category={item.category} /><ReviewStatusBadge status={item.review_status} /><ConfidenceBadge confidence={item.confidence} />{item.service_code ? <span className="rounded-full bg-slate-50 px-2 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200">{item.service_code}</span> : null}</div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/airline-intelligence/${item.airline_id}`}>Airline detail</a>
                    <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={`/agency/airline-knowledge/${item.id}`}>Open knowledge</a>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
