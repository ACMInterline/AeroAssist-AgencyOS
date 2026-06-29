import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"
import {
  fetchReferenceDomain,
  fetchReferenceDomains,
  fetchReferenceSuggestions,
  fetchServiceCatalogue,
  searchReferenceDomain,
  searchServiceCatalogue,
  submitReferenceSuggestion,
} from "../../lib/referenceData"

const defaultSuggestion = {
  suggested_code: "",
  suggested_label: "",
  suggested_description: "",
  suggested_aliases: "",
  suggested_metadata_json: "",
  suggestion_type: "new_record",
  evidence_note: "",
  target_reference_record_id: "",
}

export default function ReferenceDataPage() {
  const [state, setState] = useState(null)
  const [domains, setDomains] = useState([])
  const [selectedDomain, setSelectedDomain] = useState("countries")
  const [activeTab, setActiveTab] = useState("global")
  const [records, setRecords] = useState([])
  const [families, setFamilies] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [query, setQuery] = useState("")
  const [suggestionForm, setSuggestionForm] = useState(defaultSuggestion)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  const selectedLabel = useMemo(() => domains.find((item) => item.domain === selectedDomain)?.label || selectedDomain.replaceAll("_", " "), [domains, selectedDomain])

  async function load(nextTab = activeTab, domain = selectedDomain, search = query) {
    const context = state || await loadCurrentAgency()
    const domainResult = await fetchReferenceDomains()
    setState(context)
    setDomains(domainResult.domains || [])
    if (nextTab === "catalogue") {
      const result = search ? await searchServiceCatalogue(search, false) : await fetchServiceCatalogue(false)
      setRecords(result.items || [])
      setFamilies(result.families || [])
      return
    }
    if (nextTab === "suggestions") {
      const result = await fetchReferenceSuggestions(context.agency ? { agency_id: context.agency.id } : {})
      setSuggestions(result.items || [])
      return
    }
    const result = search ? await searchReferenceDomain(domain, search, false) : await fetchReferenceDomain(domain, false)
    setRecords(result.items || [])
    setFamilies([])
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function selectTab(tab) {
    setActiveTab(tab)
    setError("")
    setMessage("")
    setQuery("")
    await load(tab, selectedDomain, "")
  }

  async function selectDomain(domain) {
    setSelectedDomain(domain)
    setError("")
    setMessage("")
    setQuery("")
    await load(activeTab, domain, "")
  }

  async function runSearch(event) {
    event.preventDefault()
    setError("")
    await load(activeTab, selectedDomain, query)
  }

  function startSuggestion(type, record = null) {
    setActiveTab("suggestions")
    setMessage("")
    setError("")
    setSuggestionForm({
      ...defaultSuggestion,
      suggestion_type: type,
      suggested_code: record?.code || record?.key || "",
      suggested_label: record?.label || "",
      suggested_description: record?.description || "",
      suggested_aliases: (record?.aliases || []).join(", "),
      target_reference_record_id: record?.id || "",
    })
    load("suggestions", selectedDomain, "").catch((err) => setError(err.message))
  }

  async function sendSuggestion(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      let metadata = {}
      if (suggestionForm.suggested_metadata_json.trim()) {
        metadata = JSON.parse(suggestionForm.suggested_metadata_json)
      }
      await submitReferenceSuggestion({
        submitting_agency_id: state.agency.id,
        submitting_workspace_id: state.agency.workspace_id,
        domain: selectedDomain,
        suggested_code: suggestionForm.suggested_code.trim() || null,
        suggested_label: suggestionForm.suggested_label.trim(),
        suggested_description: suggestionForm.suggested_description.trim() || null,
        suggested_aliases: suggestionForm.suggested_aliases.split(",").map((item) => item.trim()).filter(Boolean),
        suggested_metadata_json: metadata,
        suggestion_type: suggestionForm.suggestion_type,
        target_reference_record_id: suggestionForm.target_reference_record_id || null,
        source_context: "manual_reference_page",
        evidence_note: suggestionForm.evidence_note.trim() || null,
      })
      setSuggestionForm(defaultSuggestion)
      setMessage("Suggestion submitted for platform review.")
      await load("suggestions")
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Governed lookup foundation</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Reference Data</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Global reference data is managed by AeroAssist. Your agency can consume approved records and submit suggestions for corrections or additions; foundation records and service catalogue entries cannot be edited from agency workspaces.</p>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>

          <div className="flex flex-wrap gap-2 rounded-lg border border-slate-200 bg-white p-3">
            <Tab active={activeTab === "global"} onClick={() => selectTab("global")}>Global Reference Data</Tab>
            <Tab active={activeTab === "catalogue"} onClick={() => selectTab("catalogue")}>Service Catalogue</Tab>
            <Tab active={activeTab === "suggestions"} onClick={() => selectTab("suggestions")}>Suggestions</Tab>
          </div>

          <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
            <aside className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Domains</p>
              <div className="space-y-1">
                {domains.map((domain) => (
                  <button className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedDomain === domain.domain ? "bg-blue-50 font-semibold text-blue-800" : "text-slate-700 hover:bg-slate-50"}`} type="button" onClick={() => selectDomain(domain.domain)} key={domain.domain}>
                    <span className="block">{domain.label}</span>
                    <span className="text-xs text-slate-500">{domain.active_record_count} approved</span>
                  </button>
                ))}
              </div>
            </aside>

            <main className="space-y-4">
              {activeTab === "global" ? <GlobalReferencePanel selectedLabel={selectedLabel} query={query} setQuery={setQuery} runSearch={runSearch} records={records} startSuggestion={startSuggestion} /> : null}
              {activeTab === "catalogue" ? <ServiceCataloguePanel query={query} setQuery={setQuery} runSearch={runSearch} families={families} records={records} /> : null}
              {activeTab === "suggestions" ? <SuggestionsPanel selectedLabel={selectedLabel} form={suggestionForm} setForm={setSuggestionForm} sendSuggestion={sendSuggestion} suggestions={suggestions} startSuggestion={startSuggestion} /> : null}
            </main>
          </div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Tab({ active, onClick, children }) {
  return <button className={`rounded-md px-3 py-2 text-sm font-semibold ${active ? "bg-slate-950 text-white" : "text-slate-700 hover:bg-slate-100"}`} type="button" onClick={onClick}>{children}</button>
}

function GlobalReferencePanel({ selectedLabel, query, setQuery, runSearch, records, startSuggestion }) {
  return (
    <>
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div><h3 className="text-xl font-semibold text-slate-950">{selectedLabel}</h3><p className="text-sm text-slate-600">Approved global records used by builders, forms, documents, and policy workflows.</p></div>
          <form className="flex flex-wrap items-center gap-2" onSubmit={runSearch}>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search code, label, alias" value={query} onChange={(event) => setQuery(event.target.value)} />
            <button className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white" type="submit">Search</button>
          </form>
        </div>
      </section>
      <div className="flex flex-wrap gap-2">
        <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="button" onClick={() => startSuggestion("new_record")}>Suggest new record</button>
      </div>
      <ReferenceTable records={records} startSuggestion={startSuggestion} />
    </>
  )
}

function ServiceCataloguePanel({ query, setQuery, runSearch, families, records }) {
  return (
    <>
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div><h3 className="text-xl font-semibold text-slate-950">Service Catalogue</h3><p className="text-sm text-slate-600">Active platform-managed services available to request, rules, offer, acceptance, booking readiness, and document workflows.</p></div>
          <form className="flex flex-wrap items-center gap-2" onSubmit={runSearch}>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search service or SSR" value={query} onChange={(event) => setQuery(event.target.value)} />
            <button className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white" type="submit">Search</button>
          </form>
        </div>
      </section>
      {families.length ? (
        <section className="grid gap-4 xl:grid-cols-2">
          {families.map((family) => (
            <article className="rounded-lg border border-slate-200 bg-white p-4" key={family.code}>
              <h4 className="font-semibold text-slate-950">{family.label}</h4>
              <div className="mt-3 divide-y divide-slate-100">
                {(family.items || []).map((record) => <ServiceRow record={record} key={record.id || record.service_code} />)}
                {!family.items?.length ? <p className="py-3 text-sm text-slate-500">No approved services in this family.</p> : null}
              </div>
            </article>
          ))}
        </section>
      ) : (
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <div className="divide-y divide-slate-100">
            {records.map((record) => <ServiceRow record={record} key={record.id || record.service_code} />)}
            {!records.length ? <EmptyState title="No service entries" body="No approved service catalogue entries matched the current search." /> : null}
          </div>
        </section>
      )}
    </>
  )
}

function SuggestionsPanel({ selectedLabel, form, setForm, sendSuggestion, suggestions, startSuggestion }) {
  return (
    <>
      <div className="flex flex-wrap gap-2">
        <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="button" onClick={() => startSuggestion("new_record")}>Suggest new record</button>
      </div>
      <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-2" onSubmit={sendSuggestion}>
        <div className="md:col-span-2"><h3 className="text-lg font-semibold text-slate-950">Submit suggestion for {selectedLabel}</h3><p className="text-sm text-slate-600">Suggestions stay pending until a platform owner reviews them.</p></div>
        <Select label="Suggestion type" value={form.suggestion_type} onChange={(value) => setForm({ ...form, suggestion_type: value })} options={["new_record", "correction", "deactivation_request"]} />
        <Field label="Suggested code" value={form.suggested_code} onChange={(value) => setForm({ ...form, suggested_code: value })} />
        <Field label="Suggested label" value={form.suggested_label} onChange={(value) => setForm({ ...form, suggested_label: value })} required />
        <Field label="Aliases" value={form.suggested_aliases} onChange={(value) => setForm({ ...form, suggested_aliases: value })} placeholder="Comma separated" />
        <Textarea label="Description or notes" value={form.suggested_description} onChange={(value) => setForm({ ...form, suggested_description: value })} />
        <Textarea label="Evidence/source note" value={form.evidence_note} onChange={(value) => setForm({ ...form, evidence_note: value })} />
        <Textarea label="Optional metadata JSON" value={form.suggested_metadata_json} onChange={(value) => setForm({ ...form, suggested_metadata_json: value })} />
        <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white md:w-fit" type="submit">Submit suggestion</button>
      </form>
      <SuggestionList title="Submitted suggestions" suggestions={suggestions} />
    </>
  )
}

function ReferenceTable({ records, startSuggestion }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">Code</th><th className="px-4 py-3">Label</th><th className="px-4 py-3">Aliases</th><th className="px-4 py-3">Description</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Actions</th></tr></thead>
        <tbody className="divide-y divide-slate-100">
          {records.map((record) => (
            <tr key={record.id}>
              <td className="px-4 py-3 font-mono text-xs text-slate-700">{record.code || record.key}</td>
              <td className="px-4 py-3 font-semibold text-slate-950">{record.label}</td>
              <td className="px-4 py-3 text-slate-600">{(record.aliases || []).join(", ") || "-"}</td>
              <td className="px-4 py-3 text-slate-600">{record.description || "-"}</td>
              <td className="px-4 py-3"><Status value="Global approved" tone="green" /></td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-2">
                  <button className="font-semibold text-blue-700" type="button" onClick={() => startSuggestion("correction", record)}>Suggest correction</button>
                  <button className="font-semibold text-slate-700" type="button" onClick={() => startSuggestion("deactivation_request", record)}>Request removal</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!records.length ? <div className="p-6"><EmptyState title="No reference records" body="No approved records matched the current filters." /></div> : null}
    </section>
  )
}

function SuggestionList({ title, suggestions }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      {title ? <h3 className="font-semibold text-slate-950">{title}</h3> : null}
      <div className="mt-3 divide-y divide-slate-100">
        {suggestions.map((item) => (
          <div className="py-3" key={item.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><p className="font-semibold text-slate-950">{item.suggested_label}</p><p className="text-xs text-slate-500">{item.domain} · {item.suggested_code || "No code"} · {item.suggestion_type}</p><p className="mt-1 text-sm text-slate-600">{item.evidence_note || item.suggested_description || "No note provided."}</p></div>
              <Status value={item.status} tone={item.status === "approved" ? "green" : item.status === "rejected" ? "rose" : "amber"} />
            </div>
          </div>
        ))}
        {!suggestions.length ? <EmptyState title="No suggestions" body="Your agency reference suggestions and review statuses appear here." /> : null}
      </div>
    </section>
  )
}

function ServiceRow({ record }) {
  const mappings = record.operational_mappings || {}
  const documents = mappings.documents?.required_documents_json || record.required_documents_json || []
  return (
    <div className="py-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-950">{record.label || record.service_label}</p>
          <p className="text-xs text-slate-500">{record.service_key || record.service_code} · SSR {record.ssr_code || record.default_ssr_code || "manual"} · {record.category || record.service_family_code}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{record.requires_policy_check ? "Policy check" : "Lookup"}</span>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        {(documents || []).length ? `Documents: ${documents.map((item) => item.label || item.code).join(", ")}. ` : ""}
        {record.requires_manual_pricing || mappings.acceptance_booking_readiness?.fee_expected ? "Pricing or EMD review may apply. " : ""}
        {record.requires_segment_scope || record.requires_segment_scoping ? "Segment scoped. " : "Trip scoped. "}
        {mappings.acceptance_booking_readiness?.booking_readiness_enabled === false ? "Excluded from booking readiness." : "Included in booking readiness checks."}
      </p>
    </div>
  )
}

function Status({ value, tone = "slate" }) {
  const tones = { green: "bg-emerald-50 text-emerald-700", rose: "bg-rose-50 text-rose-700", amber: "bg-amber-50 text-amber-800", slate: "bg-slate-100 text-slate-600" }
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${tones[tone] || tones.slate}`}>{String(value || "").replaceAll("_", " ")}</span>
}

function Field({ label, value, onChange, required = false, placeholder = "", type = "text" }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value || ""} required={required} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} /></label>
}

function Textarea({ label, value, onChange, rows = 3 }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<textarea className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" rows={rows} value={value || ""} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<select className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{option.replaceAll("_", " ")}</option>)}</select></label>
}
