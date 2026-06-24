import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { loadCurrentAgency } from "../../lib/agency"
import {
  activateReferenceRecord,
  createReferenceRecord,
  deactivateReferenceRecord,
  fetchReferenceDomain,
  fetchReferenceDomains,
  fetchServiceCatalogue,
  searchReferenceDomain,
  searchServiceCatalogue,
  updateReferenceRecord,
} from "../../lib/referenceData"

const defaultForm = { code: "", label: "", description: "", aliases: "", sort_order: 100 }

export default function ReferenceDataPage() {
  const [state, setState] = useState(null)
  const [domains, setDomains] = useState([])
  const [selectedDomain, setSelectedDomain] = useState("service_catalogue")
  const [records, setRecords] = useState([])
  const [families, setFamilies] = useState([])
  const [query, setQuery] = useState("")
  const [includeInactive, setIncludeInactive] = useState(false)
  const [form, setForm] = useState(defaultForm)
  const [editingId, setEditingId] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  const selectedLabel = useMemo(() => {
    if (selectedDomain === "service_catalogue") return "Service catalogue"
    return domains.find((item) => item.domain === selectedDomain)?.label || selectedDomain.replaceAll("_", " ")
  }, [domains, selectedDomain])

  async function load(domain = selectedDomain, search = query) {
    const context = state || await loadCurrentAgency()
    const domainResult = await fetchReferenceDomains()
    setState(context)
    setDomains(domainResult.domains)
    if (domain === "service_catalogue") {
      const result = search ? await searchServiceCatalogue(search, includeInactive) : await fetchServiceCatalogue(includeInactive)
      setRecords(result.items || [])
      setFamilies(result.families || [])
    } else {
      const result = search ? await searchReferenceDomain(domain, search, includeInactive) : await fetchReferenceDomain(domain, includeInactive)
      setRecords(result.items || [])
      setFamilies([])
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [includeInactive])

  async function selectDomain(domain) {
    setError("")
    setMessage("")
    setSelectedDomain(domain)
    setQuery("")
    setForm(defaultForm)
    setEditingId("")
    await load(domain, "")
  }

  async function runSearch(event) {
    event.preventDefault()
    setError("")
    await load(selectedDomain, query)
  }

  async function saveReferenceRecord(event) {
    event.preventDefault()
    if (selectedDomain === "service_catalogue") return
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
        setMessage("Reference record updated.")
      } else {
        await createReferenceRecord(selectedDomain, payload)
        setMessage("Reference record created.")
      }
      setForm(defaultForm)
      setEditingId("")
      await load(selectedDomain, query)
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
      await load(selectedDomain, query)
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
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations foundation</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Reference data and service catalogue</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Manage stable lookup lists used by request intake, builders, documents, and policy checks. Airline-specific rules remain in Airline Intelligence and are not duplicated here.</p>
            {message ? <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p> : null}
            {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          </section>

          <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
            <aside className="rounded-lg border border-slate-200 bg-white p-4">
              <button className={`mb-2 w-full rounded-md px-3 py-2 text-left text-sm font-semibold ${selectedDomain === "service_catalogue" ? "bg-blue-50 text-blue-800" : "text-slate-700 hover:bg-slate-50"}`} type="button" onClick={() => selectDomain("service_catalogue")}>
                Service catalogue
              </button>
              <div className="mt-4 space-y-1">
                {domains.map((domain) => (
                  <button className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedDomain === domain.domain ? "bg-blue-50 font-semibold text-blue-800" : "text-slate-700 hover:bg-slate-50"}`} type="button" onClick={() => selectDomain(domain.domain)} key={domain.domain}>
                    <span className="block">{domain.label}</span>
                    <span className="text-xs text-slate-500">{domain.active_record_count} active</span>
                  </button>
                ))}
              </div>
            </aside>

            <main className="space-y-4">
              <section className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div>
                    <h3 className="text-xl font-semibold text-slate-950">{selectedLabel}</h3>
                    <p className="text-sm text-slate-600">{selectedDomain === "service_catalogue" ? "Default operational services grouped by assistance family." : "Master lookup records. Platform owners can add, edit, activate, or deactivate global values."}</p>
                  </div>
                  <form className="flex flex-wrap items-center gap-2" onSubmit={runSearch}>
                    <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search code, label, alias" value={query} onChange={(event) => setQuery(event.target.value)} />
                    <label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={includeInactive} onChange={(event) => setIncludeInactive(event.target.checked)} /> Include inactive</label>
                    <button className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white" type="submit">Search</button>
                  </form>
                </div>
              </section>

              {selectedDomain !== "service_catalogue" ? (
                <form className="grid gap-3 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-5" onSubmit={saveReferenceRecord}>
                  <Field label="Code" value={form.code} onChange={(value) => setForm({ ...form, code: value })} required />
                  <Field label="Label" value={form.label} onChange={(value) => setForm({ ...form, label: value })} required />
                  <Field label="Aliases" value={form.aliases} onChange={(value) => setForm({ ...form, aliases: value })} placeholder="Comma separated" />
                  <Field label="Sort" value={form.sort_order} onChange={(value) => setForm({ ...form, sort_order: value })} type="number" />
                  <Field label="Description" value={form.description} onChange={(value) => setForm({ ...form, description: value })} />
                  <button className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white md:w-fit" type="submit">{editingId ? "Update record" : "Create record"}</button>
                  {editingId ? <button className="text-sm font-semibold text-slate-600 md:w-fit" type="button" onClick={() => { setEditingId(""); setForm(defaultForm) }}>Cancel edit</button> : null}
                </form>
              ) : null}

              {selectedDomain === "service_catalogue" && families.length ? (
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
              ) : (
                <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <tr><th className="px-4 py-3">Code</th><th className="px-4 py-3">Label</th><th className="px-4 py-3">Aliases</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Actions</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {records.map((record) => (
                        <tr key={record.id}>
                          <td className="px-4 py-3 font-mono text-xs text-slate-700">{record.code || record.key}</td>
                          <td className="px-4 py-3"><p className="font-semibold text-slate-950">{record.label}</p><p className="text-xs text-slate-500">{record.description}</p></td>
                          <td className="px-4 py-3 text-slate-600">{(record.aliases || []).join(", ") || "—"}</td>
                          <td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${record.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{record.is_active ? "Active" : "Inactive"}</span></td>
                          <td className="px-4 py-3"><button className="mr-3 font-semibold text-blue-700" type="button" onClick={() => editRecord(record)}>Edit</button><button className="font-semibold text-slate-700" type="button" onClick={() => toggleRecord(record)}>{record.is_active ? "Deactivate" : "Activate"}</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!records.length ? <div className="p-6"><EmptyState title="No reference records" body="Run the Phase 33 bootstrap script or create a platform-managed reference record." /></div> : null}
                </section>
              )}
            </main>
          </div>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function ServiceRow({ record }) {
  return (
    <div className="py-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-950">{record.service_label}</p>
          <p className="text-xs text-slate-500">{record.service_code} · SSR {record.default_ssr_code || "manual"} · {record.beneficiary_type}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{record.requires_policy_check ? "Policy check" : "Lookup"}</span>
      </div>
      <p className="mt-2 text-xs text-slate-500">{record.requires_document_check ? "Document check required. " : ""}{record.requires_manual_pricing ? "Manual pricing required. " : ""}{record.requires_segment_scoping ? "Segment scoped." : "Trip scoped."}</p>
    </div>
  )
}

function Field({ label, value, onChange, required = false, placeholder = "", type = "text" }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value || ""} required={required} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} /></label>
}
