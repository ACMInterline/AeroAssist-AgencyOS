import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

function Values({ label, values }) {
  return <div><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1 text-sm text-slate-800">{values?.length ? values.join(", ") : "Unknown"}</dd></div>
}

export default function AirlineProfilesPage() {
  const [state, setState] = useState(null)
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState("")
  const [error, setError] = useState("")

  async function load(query = "") {
    const context = await loadCurrentAgency()
    const suffix = query ? `?search=${encodeURIComponent(query)}` : ""
    const payload = await apiGet(`/api/agencies/${context.agency.id}/airline-master-profiles${suffix}`)
    setState({ ...context, ...payload })
    setSelected(payload.items?.[0] || null)
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-semibold uppercase text-blue-700">Airline intelligence</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Profiles</h1><p className="mt-1 max-w-3xl text-sm text-slate-600">Approved and published operational profile metadata. Evidence freshness supports human review and is not operational truth by itself.</p></div><form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); load(search).catch((err) => setError(err.message)) }}><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Airline or code" /><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Search</button></form></header>
          <div className="grid gap-5 lg:grid-cols-[300px_1fr]">
            <section><p className="text-sm font-semibold text-slate-950">Published directory</p><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.items?.map((item) => <button type="button" className={`w-full px-2 py-3 text-left hover:bg-slate-50 ${selected?.identity?.canonical_airline_id === item.identity.canonical_airline_id ? "bg-blue-50" : ""}`} key={item.identity.canonical_airline_id} onClick={() => setSelected(item)}><span className="block text-sm font-semibold text-slate-950">{item.identity.iata_code} · {item.identity.commercial_name}</span><span className="mt-1 block text-xs text-slate-500">{item.confidence.level} evidence freshness · {item.completeness.score}% coverage</span></button>)}</div>{!state?.items?.length ? <p className="mt-4 text-sm text-slate-600">No approved or published airline profiles match this view.</p> : null}</section>
            {selected ? <section className="space-y-5"><div className="border-b border-slate-200 pb-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-semibold text-slate-950">{selected.identity.commercial_name}</h2><p className="mt-1 text-sm text-slate-600">{selected.identity.iata_code} · {selected.identity.icao_code || "ICAO unknown"} · {selected.identity.country_of_registration}</p></div><span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-800 ring-1 ring-blue-200">{selected.profile.review_status}</span></div></div>
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><Values label="Aliases" values={selected.aliases.map((item) => item.alias)} /><Values label="Primary hubs" values={selected.operational_summary.primary_hubs} /><Values label="Airline groups and relationships" values={selected.relationships.map((item) => item.related_airline_name || item.relationship_type)} /><Values label="Operational classification" values={selected.operational_summary.classifications} /><Values label="Route regions" values={selected.operational_summary.route_regions} /><Values label="Known service desks" values={selected.operational_summary.service_desks_known} /></dl>
              <div className="grid gap-4 border-y border-slate-200 py-4 sm:grid-cols-3"><div><p className="text-xs font-semibold uppercase text-slate-500">Evidence freshness</p><p className="mt-1 text-lg font-semibold text-slate-950">{selected.confidence.level}</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Profile coverage</p><p className="mt-1 text-lg font-semibold text-slate-950">{selected.completeness.score}%</p></div><div><p className="text-xs font-semibold uppercase text-slate-500">Capabilities</p><p className="mt-1 text-lg font-semibold text-slate-950">{selected.operational_summary.capability_record_count}</p></div></div>
              <div><h3 className="text-sm font-semibold text-slate-950">Distribution and servicing</h3>{selected.distribution_summaries.length ? selected.distribution_summaries.map((item) => <p className="mt-2 text-sm text-slate-600" key={item.id}>GDS: {item.gds_participation?.join(", ") || "Unknown"} · NDC: {item.ndc_available == null ? "Unknown" : item.ndc_available ? "Available" : "Not recorded as available"} · EMD: {item.emd_support_summary || "Unknown"}</p>) : <p className="mt-2 text-sm text-slate-600">Distribution details are currently unknown.</p>}</div>
              <div className="flex flex-wrap gap-2"><a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-800" href={selected.operational_summary.policy_link}>Policy context</a><a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-800" href={selected.operational_summary.capability_link}>Capability context</a></div>
            </section> : null}
          </div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
