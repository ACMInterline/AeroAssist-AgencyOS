import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

const statusTone = {
  published: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  approved: "bg-blue-50 text-blue-800 ring-blue-200",
  needs_review: "bg-amber-50 text-amber-800 ring-amber-200",
  draft: "bg-slate-100 text-slate-700 ring-slate-200",
}

function Badge({ children, tone = "bg-slate-100 text-slate-700 ring-slate-200" }) {
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{children}</span>
}

function List({ label, values }) {
  return <div><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1 text-sm text-slate-800">{values?.length ? values.join(", ") : "Unknown"}</dd></div>
}

export default function AirlineMasterProfilesPage() {
  const [state, setState] = useState(null)
  const [selectedId, setSelectedId] = useState("")
  const [search, setSearch] = useState("")
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [form, setForm] = useState({ canonical_airline_id: "", commercial_name: "", accounting_prefix_code: "", airline_type: "unknown", review_status: "draft", evidence_status: "unknown", confidence: "low" })
  const [alias, setAlias] = useState({ alias: "", alias_type: "commercial_name", review_status: "approved", confidence: "medium" })

  async function load(query = search) {
    setError("")
    const suffix = query ? `?search=${encodeURIComponent(query)}` : ""
    const [summary, payload] = await Promise.all([apiGet("/api/platform/summary"), apiGet(`/api/platform/airline-master-profiles${suffix}`)])
    setState({ summary, ...payload })
    const first = payload.items?.[0]?.identity?.canonical_airline_id || ""
    setSelectedId((current) => current || first)
  }

  useEffect(() => { load("").catch((err) => setError(err.message)) }, [])

  const selected = useMemo(() => state?.items?.find((item) => item.identity.canonical_airline_id === selectedId), [state, selectedId])
  const unenriched = state?.items?.filter((item) => !item.profile) || []

  async function createProfile(event) {
    event.preventDefault()
    setError("")
    try {
      await apiPost("/api/platform/airline-master-profiles", form)
      setMessage("Governed enrichment profile created against the canonical airline identity.")
      await load("")
      setSelectedId(form.canonical_airline_id)
    } catch (err) { setError(err.message) }
  }

  async function createAlias(event) {
    event.preventDefault()
    setError("")
    try {
      await apiPost(`/api/platform/airline-master-profiles/${selectedId}/aliases`, alias)
      setAlias({ alias: "", alias_type: "commercial_name", review_status: "approved", confidence: "medium" })
      setMessage("Identity alias linked for governed resolution.")
      await load(search)
    } catch (err) { setError(err.message) }
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="flex flex-wrap items-end justify-between gap-4">
            <div><p className="text-sm font-semibold uppercase text-blue-700">Airline intelligence governance</p><h1 className="mt-1 text-2xl font-semibold text-slate-950">Airline Master Profiles</h1><p className="mt-1 max-w-3xl text-sm text-slate-600">Governed enrichment of the existing canonical airline directory. This layer does not create a second airline catalogue.</p></div>
            <form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); load(search).catch((err) => setError(err.message)) }}><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Code or airline" /><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Search</button></form>
          </header>

          {message ? <p className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">{message}</p> : null}

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {[
              ["Canonical airlines", state?.coverage?.canonical_airline_count], ["Enriched", state?.coverage?.enriched_profile_count], ["Approved / published", state?.coverage?.approved_or_published_count], ["Missing enrichment", state?.coverage?.missing_enriched_profile_count], ["Evidence conflicts", state?.coverage?.conflicting_evidence_count],
            ].map(([label, value]) => <div className="rounded-md border border-slate-200 bg-white p-4" key={label}><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value ?? 0}</p></div>)}
          </section>

          {unenriched.length ? <section className="border-y border-slate-200 py-5"><h2 className="font-semibold text-slate-950">Create governed enrichment</h2><form className="mt-3 grid gap-3 md:grid-cols-4" onSubmit={createProfile}><select required className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.canonical_airline_id} onChange={(event) => setForm({ ...form, canonical_airline_id: event.target.value })}><option value="">Canonical airline</option>{unenriched.map((item) => <option key={item.identity.canonical_airline_id} value={item.identity.canonical_airline_id}>{item.identity.iata_code} · {item.identity.commercial_name}</option>)}</select><input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Commercial name" value={form.commercial_name} onChange={(event) => setForm({ ...form, commercial_name: event.target.value })} /><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.airline_type} onChange={(event) => setForm({ ...form, airline_type: event.target.value })}>{["unknown", "full_service", "low_cost", "regional", "charter", "leisure", "hybrid", "cargo", "virtual"].map((value) => <option key={value}>{value}</option>)}</select><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Create profile</button></form></section> : null}

          <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
            <section className="min-w-0"><h2 className="text-sm font-semibold text-slate-950">Airline directory</h2><div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">{state?.items?.map((item) => <button type="button" className={`block w-full px-2 py-3 text-left hover:bg-slate-50 ${selectedId === item.identity.canonical_airline_id ? "bg-blue-50" : ""}`} key={item.identity.canonical_airline_id} onClick={() => setSelectedId(item.identity.canonical_airline_id)}><span className="block text-sm font-semibold text-slate-950">{item.identity.iata_code || "--"} · {item.identity.commercial_name}</span><span className="mt-1 flex items-center justify-between gap-2 text-xs text-slate-500"><span>{item.identity.country_of_registration || "Country unknown"}</span><span>{item.completeness.score}% complete</span></span></button>)}</div></section>

            {selected ? <section className="min-w-0 space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4"><div><h2 className="text-xl font-semibold text-slate-950">{selected.identity.commercial_name}</h2><p className="mt-1 text-sm text-slate-600">{selected.identity.iata_code || "IATA unknown"} · {selected.identity.icao_code || "ICAO unknown"} · {selected.identity.country_of_registration || "Country unknown"}</p></div><div className="flex gap-2"><Badge tone={statusTone[selected.profile?.review_status]}>{selected.profile?.review_status || "not enriched"}</Badge><Badge>{selected.confidence.level} confidence</Badge><Badge>{selected.completeness.score}% complete</Badge></div></div>
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><List label="Aliases" values={selected.aliases.map((item) => item.alias)} /><List label="Primary hubs" values={selected.operational_summary.primary_hubs} /><List label="Focus cities" values={selected.operational_summary.focus_cities} /><List label="Classifications" values={selected.operational_summary.classifications} /><List label="Route regions" values={selected.operational_summary.route_regions} /><List label="Service desks" values={selected.operational_summary.service_desks_known} /></dl>
              <div className="grid gap-4 md:grid-cols-2"><div><h3 className="text-sm font-semibold text-slate-950">Distribution and servicing</h3><p className="mt-2 text-sm text-slate-600">Distribution known: {selected.operational_summary.distribution_known ? "Yes" : "Unknown"}. Contacts: {selected.operational_summary.contact_count}. Capability records: {selected.operational_summary.capability_record_count}.</p></div><div><h3 className="text-sm font-semibold text-slate-950">Evidence and revisions</h3><p className="mt-2 text-sm text-slate-600">{selected.evidence.length} evidence links · {selected.confidence.conflicting_evidence_count} conflicts · {selected.revision_history.length} revisions.</p></div></div>
              <div><h3 className="text-sm font-semibold text-slate-950">Missing intelligence</h3><div className="mt-2 flex flex-wrap gap-2">{selected.unknown_fields.length ? selected.unknown_fields.map((field) => <Badge key={field}>{field.replaceAll("_", " ")}</Badge>) : <Badge tone="bg-emerald-50 text-emerald-800 ring-emerald-200">No tracked gaps</Badge>}</div></div>
              {selected.profile ? <form className="border-t border-slate-200 pt-4" onSubmit={createAlias}><h3 className="text-sm font-semibold text-slate-950">Add identity alias</h3><div className="mt-3 flex flex-wrap gap-2"><input required className="min-w-48 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Alias" value={alias.alias} onChange={(event) => setAlias({ ...alias, alias: event.target.value })} /><select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={alias.alias_type} onChange={(event) => setAlias({ ...alias, alias_type: event.target.value })}>{["commercial_name", "legal_name", "former_name", "iata_code", "icao_code", "accounting_prefix"].map((value) => <option key={value}>{value}</option>)}</select><button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white">Link alias</button></div></form> : null}
            </section> : null}
          </div>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
