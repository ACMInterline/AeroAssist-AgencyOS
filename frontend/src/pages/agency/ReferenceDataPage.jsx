import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"
import {
  activateReferenceRecord,
  approveReferenceSuggestion,
  archiveReferenceSuggestion,
  createReferenceImportBatch,
  createReferenceRecord,
  deactivateReferenceRecord,
  fetchReferenceDomain,
  fetchReferenceDomains,
  fetchReferenceImportBatches,
  fetchReferenceSuggestions,
  fetchServiceCatalogue,
  rejectReferenceSuggestion,
  requestReferenceSuggestionInfo,
  searchReferenceDomain,
  searchServiceCatalogue,
  submitReferenceSuggestion,
  updateReferenceRecord,
} from "../../lib/referenceData"

const defaultForm = { code: "", label: "", description: "", aliases: "", sort_order: 100 }
const defaultSuggestion = { suggested_code: "", suggested_label: "", suggested_description: "", suggested_aliases: "", suggestion_type: "new_record", evidence_note: "" }
const defaultImport = { filename: "reference-data.csv", csv_text: "domain,code,label,description,aliases,sort_order,is_active,metadata_json\n", dry_run: false }

export default function ReferenceDataPage() {
  const [state, setState] = useState(null)
  const [domains, setDomains] = useState([])
  const [selectedDomain, setSelectedDomain] = useState("countries")
  const [activeTab, setActiveTab] = useState("global")
  const [records, setRecords] = useState([])
  const [families, setFamilies] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [importBatches, setImportBatches] = useState([])
  const [query, setQuery] = useState("")
  const [includeInactive, setIncludeInactive] = useState(false)
  const [form, setForm] = useState(defaultForm)
  const [suggestionForm, setSuggestionForm] = useState(defaultSuggestion)
  const [importForm, setImportForm] = useState(defaultImport)
  const [editingId, setEditingId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  const isPlatformOwner = ["platform_owner", "platform_admin"].includes(state?.me?.user?.global_role)
  const selectedLabel = useMemo(() => domains.find((item) => item.domain === selectedDomain)?.label || selectedDomain.replaceAll("_", " "), [domains, selectedDomain])

  async function load(nextTab = activeTab, domain = selectedDomain, search = query) {
    const context = state || await loadCurrentAgency()
    const domainResult = await fetchReferenceDomains()
    setState(context)
    setDomains(domainResult.domains)
    if (nextTab === "catalogue") {
      const result = search ? await searchServiceCatalogue(search, includeInactive) : await fetchServiceCatalogue(includeInactive)
      setRecords(result.items || [])
      setFamilies(result.families || [])
      return
    }
    if (nextTab === "suggestions" || nextTab === "review") {
      const result = await fetchReferenceSuggestions(nextTab === "suggestions" && context.agency ? { agency_id: context.agency.id } : {})
      setSuggestions(result.items || [])
      return
    }
    if (nextTab === "import") {
      const result = await fetchReferenceImportBatches()
      setImportBatches(result.items || [])
      return
    }
    const result = search ? await searchReferenceDomain(domain, search, includeInactive) : await fetchReferenceDomain(domain, includeInactive)
    setRecords(result.items || [])
    setFamilies([])
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [includeInactive])

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
    setForm(defaultForm)
    setEditingId("")
    await load(activeTab, domain, "")
  }

  async function runSearch(event) {
    event.preventDefault()
    setError("")
    await load(activeTab, selectedDomain, query)
  }

  async function saveReferenceRecord(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    const payload = {
      code: form.code.trim(),
      key: form.code.trim(),
      label: form.label.trim(),
      description: form.description.trim() || null,
      aliases: form.aliases.split(",").map((item) => item.trim()).filter(Boolean),
      sort_order: Number(form.sort_order || 100),
      scope: "global",
      source_type: "platform",
    }
    try {
      if (editingId) {
        await updateReferenceRecord(selectedDomain, editingId, payload)
        setMessage("Global reference record updated.")
      } else {
        await createReferenceRecord(selectedDomain, payload)
        setMessage("Global reference record created.")
      }
      setForm(defaultForm)
      setEditingId("")
      await load("global", selectedDomain, query)
    } catch (err) {
      setError(err.message)
    }
  }

  async function sendSuggestion(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await submitReferenceSuggestion({
        submitting_agency_id: state.agency.id,
        submitting_workspace_id: state.agency.workspace_id,
        domain: selectedDomain,
        suggested_code: suggestionForm.suggested_code.trim() || null,
        suggested_label: suggestionForm.suggested_label.trim(),
        suggested_description: suggestionForm.suggested_description.trim() || null,
        suggested_aliases: suggestionForm.suggested_aliases.split(",").map((item) => item.trim()).filter(Boolean),
        suggestion_type: suggestionForm.suggestion_type,
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

  async function submitImport(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await createReferenceImportBatch({ ...importForm, domain: selectedDomain, scope: "global" })
      setMessage(importForm.dry_run ? "Import file validated." : "Import batch processed.")
      await load("import")
    } catch (err) {
      setError(err.message)
    }
  }

  async function reviewSuggestion(suggestion, action) {
    const note = window.prompt("Reviewer note") || ""
    try {
      if (action === "approve") await approveReferenceSuggestion(suggestion.id, { reviewer_note: note })
      if (action === "reject") await rejectReferenceSuggestion(suggestion.id, { reviewer_note: note })
      if (action === "info") await requestReferenceSuggestionInfo(suggestion.id, { reviewer_note: note })
      if (action === "archive") await archiveReferenceSuggestion(suggestion.id, { reviewer_note: note })
      setMessage(`Suggestion ${action} action completed.`)
      await load("review")
    } catch (err) {
      setError(err.message)
    }
  }

  async function toggleRecord(record) {
    setError("")
    setMessage("")
    try {
      if (record.is_active) {
        await deactivateReferenceRecord(selectedDomain, record.id)
        setMessage("Reference record deactivated.")
      } else {
        await activateReferenceRecord(selectedDomain, record.id)
        setMessage("Reference record activated.")
      }
      await load("global", selectedDomain, query)
    } catch (err) {
      setError(err.message)
    }
  }

  function editRecord(record) {
    setEditingId(record.id)
    setForm({
      code: record.code || record.key || "",
      label: record.label || "",
      description: record.description || "",
      aliases: (record.aliases || []).join(", "),
      sort_order: record.sort_order || 100,
    })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={!state ? error : ""}>
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Governed lookup foundation</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Reference data governance</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Global reference data is platform-owned. Agencies consume approved records and submit suggestions into a review queue instead of creating master data directly.</p>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>

          <div className="flex flex-wrap gap-2 rounded-lg border border-slate-200 bg-white p-3">
            <Tab active={activeTab === "global"} onClick={() => selectTab("global")}>Global Reference Data</Tab>
            <Tab active={activeTab === "catalogue"} onClick={() => selectTab("catalogue")}>Service Catalogue</Tab>
            <Tab active={activeTab === "suggestions"} onClick={() => selectTab("suggestions")}>Suggestions</Tab>
            {isPlatformOwner ? <Tab active={activeTab === "import"} onClick={() => selectTab("import")}>Import / Bulk Upload</Tab> : null}
            {isPlatformOwner ? <Tab active={activeTab === "review"} onClick={() => selectTab("review")}>Review Queue</Tab> : null}
          </div>

          <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
            <aside className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Domains</p>
              <div className="space-y-1">
                {domains.map((domain) => (
                  <button className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedDomain === domain.domain ? "bg-blue-50 font-semibold text-blue-800" : "text-slate-700 hover:bg-slate-50"}`} type="button" onClick={() => selectDomain(domain.domain)} key={domain.domain}>
                    <span className="block">{domain.label}</span>
                    <span className="text-xs text-slate-500">{domain.active_record_count} active · Global approved</span>
                  </button>
                ))}
              </div>
            </aside>

            <main className="space-y-4">
              {activeTab === "global" ? (
                <GlobalReferencePanel selectedLabel={selectedLabel} query={query} setQuery={setQuery} includeInactive={includeInactive} setIncludeInactive={setIncludeInactive} runSearch={runSearch} isPlatformOwner={isPlatformOwner} form={form} setForm={setForm} editingId={editingId} setEditingId={setEditingId} saveReferenceRecord={saveReferenceRecord} records={records} editRecord={editRecord} toggleRecord={toggleRecord} />
              ) : null}
              {activeTab === "catalogue" ? <ServiceCataloguePanel families={families} /> : null}
              {activeTab === "suggestions" ? <SuggestionsPanel selectedLabel={selectedLabel} form={suggestionForm} setForm={setSuggestionForm} sendSuggestion={sendSuggestion} suggestions={suggestions} /> : null}
              {activeTab === "import" && isPlatformOwner ? <ImportPanel selectedDomain={selectedDomain} form={importForm} setForm={setImportForm} submitImport={submitImport} batches={importBatches} /> : null}
              {activeTab === "review" && isPlatformOwner ? <ReviewPanel suggestions={suggestions} onReview={reviewSuggestion} /> : null}
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

function GlobalReferencePanel({ selectedLabel, query, setQuery, includeInactive, setIncludeInactive, runSearch, isPlatformOwner, form, setForm, editingId, setEditingId, saveReferenceRecord, records, editRecord, toggleRecord }) {
  return (
    <>
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div><h3 className="text-xl font-semibold text-slate-950">{selectedLabel}</h3><p className="text-sm text-slate-600">Approved global records used by builders, forms, documents, and future policy workflows.</p></div>
          <form className="flex flex-wrap items-center gap-2" onSubmit={runSearch}>
            <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search code, label, alias" value={query} onChange={(event) => setQuery(event.target.value)} />
            <label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={includeInactive} onChange={(event) => setIncludeInactive(event.target.checked)} /> Include inactive</label>
            <button className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white" type="submit">Search</button>
          </form>
        </div>
      </section>
      {isPlatformOwner ? (
        <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-5" onSubmit={saveReferenceRecord}>
          <Field label="Code" value={form.code} onChange={(value) => setForm({ ...form, code: value })} required />
          <Field label="Label" value={form.label} onChange={(value) => setForm({ ...form, label: value })} required />
          <Field label="Aliases" value={form.aliases} onChange={(value) => setForm({ ...form, aliases: value })} placeholder="Comma separated" />
          <Field label="Sort" value={form.sort_order} onChange={(value) => setForm({ ...form, sort_order: value })} type="number" />
          <Field label="Description" value={form.description} onChange={(value) => setForm({ ...form, description: value })} />
          <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white md:w-fit" type="submit">{editingId ? "Update global record" : "Create global record"}</button>
          {editingId ? <button className="text-sm font-semibold text-slate-600 md:w-fit" type="button" onClick={() => { setEditingId(""); setForm(defaultForm) }}>Cancel edit</button> : null}
        </form>
      ) : (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Agency users can read global approved data and submit suggestions, but cannot create or approve global records directly.</p>
      )}
      <ReferenceTable records={records} canManage={isPlatformOwner} editRecord={editRecord} toggleRecord={toggleRecord} />
    </>
  )
}

function ServiceCataloguePanel({ families }) {
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      {families.map((family) => (
        <article className="rounded-lg border border-slate-200 bg-white p-4" key={family.code}>
          <h4 className="font-semibold text-slate-950">{family.label}</h4>
          <div className="mt-3 divide-y divide-slate-100">
            {(family.items || []).map((record) => <ServiceRow record={record} key={record.id || record.service_code} />)}
            {!family.items?.length ? <p className="py-3 text-sm text-slate-500">No active services in this family.</p> : null}
          </div>
        </article>
      ))}
    </section>
  )
}

function SuggestionsPanel({ selectedLabel, form, setForm, sendSuggestion, suggestions }) {
  return (
    <>
      <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-2" onSubmit={sendSuggestion}>
        <div className="md:col-span-2"><h3 className="text-lg font-semibold text-slate-950">Suggest change for {selectedLabel}</h3><p className="text-sm text-slate-600">Suggestions stay pending until a platform owner approves, rejects, merges, or archives them.</p></div>
        <Field label="Suggested code" value={form.suggested_code} onChange={(value) => setForm({ ...form, suggested_code: value })} />
        <Field label="Suggested label" value={form.suggested_label} onChange={(value) => setForm({ ...form, suggested_label: value })} required />
        <Select label="Suggestion type" value={form.suggestion_type} onChange={(value) => setForm({ ...form, suggestion_type: value })} options={["new_record", "correction", "deactivation_request", "merge_request", "missing_domain_value"]} />
        <Field label="Aliases" value={form.suggested_aliases} onChange={(value) => setForm({ ...form, suggested_aliases: value })} placeholder="Comma separated" />
        <Textarea label="Description" value={form.suggested_description} onChange={(value) => setForm({ ...form, suggested_description: value })} />
        <Textarea label="Evidence note" value={form.evidence_note} onChange={(value) => setForm({ ...form, evidence_note: value })} />
        <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white md:w-fit" type="submit">Submit suggestion</button>
      </form>
      <SuggestionList title="Submitted suggestions" suggestions={suggestions} />
    </>
  )
}

function ImportPanel({ selectedDomain, form, setForm, submitImport, batches }) {
  return (
    <>
      <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={submitImport}>
        <h3 className="text-lg font-semibold text-slate-950">Import global records for {selectedDomain}</h3>
        <p className="text-sm text-slate-600">Manual CSV import only. Required columns: domain, code, label. Duplicate file rows are reported and no destructive deletes run.</p>
        <Field label="Filename" value={form.filename} onChange={(value) => setForm({ ...form, filename: value })} />
        <Textarea label="CSV text" value={form.csv_text} onChange={(value) => setForm({ ...form, csv_text: value })} rows={8} />
        <label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={form.dry_run} onChange={(event) => setForm({ ...form, dry_run: event.target.checked })} /> Dry run / validate only</label>
        <button className="rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white" type="submit">Upload import batch</button>
      </form>
      <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">Import batches</h3><BatchList batches={batches} /></section>
    </>
  )
}

function ReviewPanel({ suggestions, onReview }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="text-lg font-semibold text-slate-950">Platform review queue</h3>
      <p className="text-sm text-slate-600">Approval promotes accepted suggestions into global reference data. Rejections remain non-global.</p>
      <SuggestionList suggestions={suggestions} review onReview={onReview} />
    </section>
  )
}

function ReferenceTable({ records, canManage, editRecord, toggleRecord }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">Code</th><th className="px-4 py-3">Label</th><th className="px-4 py-3">Aliases</th><th className="px-4 py-3">Governance</th><th className="px-4 py-3">Actions</th></tr></thead>
        <tbody className="divide-y divide-slate-100">
          {records.map((record) => (
            <tr key={record.id}>
              <td className="px-4 py-3 font-mono text-xs text-slate-700">{record.code || record.key}</td>
              <td className="px-4 py-3"><p className="font-semibold text-slate-950">{record.label}</p><p className="text-xs text-slate-500">{record.description}</p></td>
              <td className="px-4 py-3 text-slate-600">{(record.aliases || []).join(", ") || "—"}</td>
              <td className="px-4 py-3"><Status value={record.is_active ? "Global approved" : "Inactive"} tone={record.is_active ? "green" : "slate"} /></td>
              <td className="px-4 py-3">{canManage ? <><button className="mr-3 font-semibold text-blue-700" type="button" onClick={() => editRecord(record)}>Edit</button><button className="font-semibold text-slate-700" type="button" onClick={() => toggleRecord(record)}>{record.is_active ? "Deactivate" : "Activate"}</button></> : <span className="text-xs text-slate-500">Read-only</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!records.length ? <div className="p-6"><EmptyState title="No reference records" body="Run the safe bootstrap or submit a suggestion for platform review." /></div> : null}
    </section>
  )
}

function SuggestionList({ title, suggestions, review = false, onReview }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      {title ? <h3 className="font-semibold text-slate-950">{title}</h3> : null}
      <div className="mt-3 divide-y divide-slate-100">
        {suggestions.map((item) => (
          <div className="py-3" key={item.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><p className="font-semibold text-slate-950">{item.suggested_label}</p><p className="text-xs text-slate-500">{item.domain} · {item.suggested_code || "No code"} · {item.suggestion_type}</p><p className="mt-1 text-sm text-slate-600">{item.evidence_note || item.suggested_description}</p></div>
              <Status value={item.status} tone={item.status === "approved" ? "green" : item.status === "rejected" ? "rose" : "amber"} />
            </div>
            {review && ["pending_review", "needs_more_information"].includes(item.status) ? <div className="mt-3 flex flex-wrap gap-2"><button className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white" type="button" onClick={() => onReview(item, "approve")}>Approve</button><button className="rounded-md bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white" type="button" onClick={() => onReview(item, "reject")}>Reject</button><button className="rounded-md bg-amber-100 px-3 py-1.5 text-xs font-semibold text-amber-800" type="button" onClick={() => onReview(item, "info")}>Needs info</button><button className="rounded-md bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700" type="button" onClick={() => onReview(item, "archive")}>Archive</button></div> : null}
          </div>
        ))}
        {!suggestions.length ? <EmptyState title="No suggestions" body="Agency suggestions and review decisions appear here." /> : null}
      </div>
    </section>
  )
}

function BatchList({ batches }) {
  return <div className="mt-3 divide-y divide-slate-100">{batches.map((batch) => <div className="py-3 text-sm" key={batch.id}><p className="font-semibold text-slate-950">{batch.filename}</p><p className="text-xs text-slate-500">{batch.domain} · {batch.status} · {batch.valid_rows}/{batch.total_rows} valid · inserted {batch.inserted_count} · updated {batch.updated_count} · skipped {batch.skipped_count}</p>{batch.error_report_json?.errors?.length ? <p className="mt-1 text-xs text-rose-700">{batch.error_report_json.errors.slice(0, 3).join(" ")}</p> : null}</div>)}{!batches.length ? <EmptyState title="No import batches" body="Validated CSV import batches appear here." /> : null}</div>
}

function ServiceRow({ record }) {
  return <div className="py-3"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-950">{record.service_label}</p><p className="text-xs text-slate-500">{record.service_code} · SSR {record.default_ssr_code || "manual"} · {record.beneficiary_type}</p></div><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{record.requires_policy_check ? "Policy check" : "Lookup"}</span></div><p className="mt-2 text-xs text-slate-500">{record.requires_document_check ? "Document check required. " : ""}{record.requires_manual_pricing ? "Manual pricing required. " : ""}{record.requires_segment_scoping ? "Segment scoped." : "Trip scoped."}</p></div>
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
