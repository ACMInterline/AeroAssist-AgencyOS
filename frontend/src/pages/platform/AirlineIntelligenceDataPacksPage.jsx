import { useEffect, useMemo, useState } from "react"
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js"
import FileCheck2 from "lucide-react/dist/esm/icons/file-check-2.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import RefreshCw from "lucide-react/dist/esm/icons/refresh-cw.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

const base = "/api/platform/airline-intelligence-data-packs"

const packTypes = ["starter_pack", "airline_profile_pack", "fleet_pack", "fare_pack", "special_services_pack", "cms_branding_pack", "mixed_pack"]
const sourceTypes = ["manual", "curated", "agency_supplied", "platform_supplied", "demo_sample", "imported_file"]
const domains = ["airline_profile", "fleet", "routes", "fare_families", "rbd_matrix", "fare_rules", "ancillaries", "special_services_rules", "cms_content", "client_portal_display_metadata"]
const noteTypes = ["source", "verification", "agency_display", "cms_display", "client_portal", "offer_builder", "review"]

const defaultPack = {
  name: "",
  description: "",
  pack_type: "starter_pack",
  airline_codes: "",
  source_type: "demo_sample",
  source_reference: "",
  version_label: "v1",
  is_demo_data: true,
  is_operationally_verified: false,
  safe_for_agency_internal_crm: false,
  safe_for_agency_display: false,
  safe_for_cms_display: false,
  safe_for_client_portal_later: false,
  safe_for_offer_builder: false,
  human_summary: "",
  operator_guidance: "",
}

const defaultItem = {
  airline_iata_code: "",
  target_domain: "airline_profile",
  display_name: "",
  plain_language_summary: "",
  source_reference: "",
  proposed_action: "review_only",
  payload_text: "{}",
  is_demo_data: true,
  is_operationally_verified: false,
}

export default function AirlineIntelligenceDataPacksPage() {
  const [state, setState] = useState(null)
  const [selectedPackId, setSelectedPackId] = useState("")
  const [packForm, setPackForm] = useState(defaultPack)
  const [itemForm, setItemForm] = useState(defaultItem)
  const [jsonText, setJsonText] = useState('[{"airline_iata_code":"ZZ","target_domain":"routes","display_name":"Sample routes","plain_language_summary":"Demo route coverage for review only","source_reference":"Demo sample","payload":{"routes":["ZZ100"]},"is_demo_data":true}]')
  const [csvText, setCsvText] = useState("airline_iata_code,target_domain,display_name,plain_language_summary,source_reference,is_demo_data,is_operationally_verified\nZZ,fare_families,Sample fare family,Demo fare family coverage,Demo sample,true,false")
  const [note, setNote] = useState({ note_type: "verification", note: "" })
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load(openPackId = selectedPackId) {
    const [me, summary, packs, snapshots] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/packs`),
      apiGet(`${base}/coverage-snapshots`),
    ])
    const packItems = packs.items || []
    const nextPackId = openPackId || packItems[0]?.id || ""
    const detail = nextPackId ? await apiGet(`${base}/packs/${nextPackId}`) : null
    setSelectedPackId(nextPackId)
    setState({
      me,
      summary,
      packs: packItems,
      snapshots: snapshots.items || [],
      detail,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const selectedPack = state?.detail?.pack
  const metrics = useMemo(() => [
    ["Total packs", state?.summary?.data_pack_count || 0],
    ["Need review", state?.summary?.packs_needing_review_count || 0],
    ["Approved", state?.summary?.approved_pack_count || 0],
    ["Demo/sample", state?.summary?.demo_pack_count || 0],
    ["Agency display", state?.summary?.agency_display_safe_pack_count || 0],
    ["CMS display", state?.summary?.cms_display_safe_pack_count || 0],
    ["Client portal later", state?.summary?.client_portal_safe_pack_count || 0],
    ["Offer builder", state?.summary?.offer_builder_safe_pack_count || 0],
  ], [state])

  async function runAction(name, action) {
    setWorking(name)
    setError("")
    setMessage("")
    try {
      await action()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  function createPack(event) {
    event.preventDefault()
    runAction("create-pack", async () => {
      const created = await apiPost(`${base}/packs`, {
        ...packForm,
        airline_codes: splitCodes(packForm.airline_codes),
        target_domains: [],
      })
      setMessage("Data pack created for review.")
      setPackForm(defaultPack)
      await load(created.pack.id)
    })
  }

  function updateSelectedPack(updates) {
    if (!selectedPackId) return
    runAction("update-pack", async () => {
      await apiPatch(`${base}/packs/${selectedPackId}`, updates)
      setMessage("Data pack review metadata updated.")
      await load(selectedPackId)
    })
  }

  function addItem(event) {
    event.preventDefault()
    if (!selectedPackId) return
    runAction("add-item", async () => {
      await apiPost(`${base}/packs/${selectedPackId}/items`, {
        ...itemForm,
        payload: parseJson(itemForm.payload_text),
        normalized_payload: {},
      })
      setMessage("Staged data item added.")
      setItemForm(defaultItem)
      await load(selectedPackId)
    })
  }

  function validatePack() {
    if (!selectedPackId) return
    runAction("validate", async () => {
      const result = await apiPost(`${base}/packs/${selectedPackId}/validate`, {})
      setMessage(result.plain_language_summary || "Validation complete.")
      await load(selectedPackId)
    })
  }

  function runJsonDryRun() {
    if (!selectedPackId) return
    runAction("json", async () => {
      const result = await apiPost(`${base}/packs/${selectedPackId}/dry-run-json`, { inline_json: jsonText })
      setMessage(result.plain_language_summary || "JSON dry run complete.")
      await load(selectedPackId)
    })
  }

  function runCsvDryRun() {
    if (!selectedPackId) return
    runAction("csv", async () => {
      const result = await apiPost(`${base}/packs/${selectedPackId}/dry-run-csv`, { inline_csv: csvText })
      setMessage(result.plain_language_summary || "CSV dry run complete.")
      await load(selectedPackId)
    })
  }

  function addNote(event) {
    event.preventDefault()
    if (!selectedPackId) return
    runAction("note", async () => {
      await apiPost(`${base}/packs/${selectedPackId}/review-notes`, note)
      setMessage("Review note added.")
      setNote({ note_type: "verification", note: "" })
      await load(selectedPackId)
    })
  }

  function createSnapshot() {
    runAction("snapshot", async () => {
      await apiPost(`${base}/coverage-snapshots`, { snapshot_label: "Platform airline data coverage" })
      setMessage("Coverage snapshot created.")
      await load(selectedPackId)
    })
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Intelligence</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Data Packs</h2>
              <p className="mt-1 text-sm text-slate-600">Guided staging, validation, and review for airline data before any future operational use.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={validatePack} disabled={!selectedPackId || working === "validate"}><CheckCircle2 className="h-4 w-4" />Validate</button>
              <button className="inline-flex items-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="button" onClick={createSnapshot} disabled={working === "snapshot"}><FileCheck2 className="h-4 w-4" />Snapshot</button>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createPack}>
                <h3 className="font-semibold text-slate-950">Create data pack</h3>
                <Field label="Pack name" value={packForm.name} onChange={(value) => setPackForm({ ...packForm, name: value })} required />
                <Select label="Pack type" value={packForm.pack_type} options={packTypes} onChange={(value) => setPackForm({ ...packForm, pack_type: value })} />
                <Field label="Airline codes" value={packForm.airline_codes} onChange={(value) => setPackForm({ ...packForm, airline_codes: value.toUpperCase() })} placeholder="LH, BA, AF" />
                <Select label="Source type" value={packForm.source_type} options={sourceTypes} onChange={(value) => setPackForm({ ...packForm, source_type: value })} />
                <Field label="Source reference" value={packForm.source_reference} onChange={(value) => setPackForm({ ...packForm, source_reference: value })} placeholder="Manual review note, supplier file, demo sample" />
                <TextArea label="Human summary" value={packForm.human_summary} onChange={(value) => setPackForm({ ...packForm, human_summary: value })} />
                <TextArea label="Operator guidance" value={packForm.operator_guidance} onChange={(value) => setPackForm({ ...packForm, operator_guidance: value })} />
                <FlagGrid form={packForm} setForm={setPackForm} />
                <button className="inline-flex items-center gap-2 aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "create-pack"}><Plus className="h-4 w-4" />Create pack</button>
              </form>

              <section className="rounded-lg border border-slate-200 bg-white">
                <div className="border-b border-slate-200 p-4">
                  <h3 className="font-semibold text-slate-950">Guided pack list</h3>
                </div>
                <div className="divide-y divide-slate-100">
                  {(state?.packs || []).map((pack) => (
                    <button className={`block w-full p-4 text-left hover:bg-slate-50 ${selectedPackId === pack.id ? "bg-blue-50" : ""}`} type="button" onClick={() => load(pack.id)} key={pack.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-slate-950">{pack.name}</p>
                          <p className="mt-1 text-sm text-slate-600">{label(pack.pack_type)} · {(pack.airline_codes || []).join(", ") || "No airline code yet"}</p>
                        </div>
                        <StatusBadge status={pack.verification_status} demo={pack.is_demo_data} verified={pack.is_operationally_verified} />
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                        <span>Confidence {Math.round((pack.confidence_score || 0) * 100)}%</span>
                        {pack.safe_for_offer_builder ? <span>Available for offer builder</span> : null}
                        {pack.safe_for_cms_display ? <span>Available for agency website</span> : null}
                      </div>
                    </button>
                  ))}
                </div>
              </section>
            </div>

            <div className="space-y-4">
              {!selectedPack ? <EmptyState title="No data pack selected" body="Create or select a data pack to review staged airline intelligence." /> : (
                <>
                  <section className="rounded-lg border border-slate-200 bg-white p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{selectedPack.name}</h3>
                        <p className="mt-1 text-sm text-slate-600">{selectedPack.human_summary || selectedPack.description || "No plain-language summary yet."}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => updateSelectedPack({ verification_status: "needs_review" })}>Needs verification</button>
                        <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => updateSelectedPack({ verification_status: "approved", is_operationally_verified: true })}>Approve metadata</button>
                      </div>
                    </div>
                    <div className="mt-4 grid gap-2 text-sm md:grid-cols-3">
                      {["safe_for_agency_internal_crm", "safe_for_offer_builder", "safe_for_cms_display", "safe_for_client_portal_later", "safe_for_agency_display", "is_demo_data"].map((flag) => (
                        <button className={`rounded-md border px-3 py-2 text-left ${selectedPack[flag] ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-slate-200 bg-slate-50 text-slate-600"}`} type="button" onClick={() => updateSelectedPack({ [flag]: !selectedPack[flag] })} key={flag}>
                          {flagLabel(flag)}
                        </button>
                      ))}
                    </div>
                  </section>

                  <section className="grid gap-4 xl:grid-cols-2">
                    <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={addItem}>
                      <h3 className="font-semibold text-slate-950">Add staged item</h3>
                      <Field label="Airline code" value={itemForm.airline_iata_code} onChange={(value) => setItemForm({ ...itemForm, airline_iata_code: value.toUpperCase() })} />
                      <Select label="Data area" value={itemForm.target_domain} options={domains} onChange={(value) => setItemForm({ ...itemForm, target_domain: value })} />
                      <Field label="Display name" value={itemForm.display_name} onChange={(value) => setItemForm({ ...itemForm, display_name: value })} required />
                      <TextArea label="Plain-language summary" value={itemForm.plain_language_summary} onChange={(value) => setItemForm({ ...itemForm, plain_language_summary: value })} />
                      <Field label="Source/reference" value={itemForm.source_reference} onChange={(value) => setItemForm({ ...itemForm, source_reference: value })} />
                      <TextArea label="Advanced staged payload JSON" value={itemForm.payload_text} onChange={(value) => setItemForm({ ...itemForm, payload_text: value })} />
                      <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="submit"><Plus className="h-4 w-4" />Add item</button>
                    </form>

                    <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
                      <h3 className="font-semibold text-slate-950">Dry run / validation</h3>
                      <TextArea label="Inline JSON" value={jsonText} onChange={setJsonText} />
                      <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={runJsonDryRun}><RefreshCw className="h-4 w-4" />Run JSON dry run</button>
                      <TextArea label="Inline CSV" value={csvText} onChange={setCsvText} />
                      <button className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={runCsvDryRun}><RefreshCw className="h-4 w-4" />Run CSV dry run</button>
                    </section>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Pack items</h3>
                    </div>
                    <div className="divide-y divide-slate-100">
                      {(state?.detail?.items || []).map((item) => <ItemRow item={item} key={item.id} />)}
                    </div>
                  </section>

                  <section className="grid gap-4 xl:grid-cols-2">
                    <section className="rounded-lg border border-slate-200 bg-white">
                      <div className="border-b border-slate-200 p-4">
                        <h3 className="font-semibold text-slate-950">Validation results</h3>
                      </div>
                      <div className="divide-y divide-slate-100">
                        {(state?.detail?.validation_issues || []).slice(0, 12).map((issue) => (
                          <div className="p-4 text-sm" key={issue.id}>
                            <p className="font-semibold text-slate-950">{issue.user_friendly_message}</p>
                            <p className="mt-1 text-slate-600">{issue.suggested_resolution}</p>
                          </div>
                        ))}
                      </div>
                    </section>

                    <section className="rounded-lg border border-slate-200 bg-white p-5">
                      <h3 className="font-semibold text-slate-950">Review notes</h3>
                      <form className="mt-3 space-y-3" onSubmit={addNote}>
                        <Select label="Note type" value={note.note_type} options={noteTypes} onChange={(value) => setNote({ ...note, note_type: value })} />
                        <TextArea label="Note" value={note.note} onChange={(value) => setNote({ ...note, note: value })} required />
                        <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold">Add note</button>
                      </form>
                      <div className="mt-4 space-y-2">
                        {(state?.detail?.review_notes || []).slice(0, 5).map((item) => (
                          <div className="rounded-md bg-slate-50 p-3 text-sm" key={item.id}>
                            <p className="font-medium text-slate-900">{label(item.note_type)}</p>
                            <p className="text-slate-600">{item.note}</p>
                          </div>
                        ))}
                      </div>
                    </section>
                  </section>

                  <section className="rounded-lg border border-slate-200 bg-white">
                    <div className="border-b border-slate-200 p-4">
                      <h3 className="font-semibold text-slate-950">Coverage snapshots</h3>
                    </div>
                    <div className="divide-y divide-slate-100">
                      {(state?.snapshots || []).slice(0, 5).map((snapshot) => (
                        <div className="grid gap-3 p-4 text-sm md:grid-cols-4" key={snapshot.id}>
                          <span className="font-semibold text-slate-950">{snapshot.snapshot_label}</span>
                          <span>Profiles {snapshot.airlines_with_profiles}</span>
                          <span>Offer ready {snapshot.airlines_safe_for_offer_builder}</span>
                          <span>Website ready {snapshot.airlines_safe_for_cms_display}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                </>
              )}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function ItemRow({ item }) {
  return (
    <div className="p-4 text-sm">
      <div className="grid gap-3 md:grid-cols-[100px_160px_1fr_130px]">
        <span className="font-semibold text-slate-900">{item.airline_iata_code || "Missing code"}</span>
        <span>{label(item.target_domain)}</span>
        <span>{item.display_name}</span>
        <StatusBadge status={item.validation_status} demo={item.is_demo_data} verified={item.is_operationally_verified} />
      </div>
      <p className="mt-2 text-slate-600">{item.plain_language_summary || "Needs a plain-language summary."}</p>
      <details className="mt-2">
        <summary className="cursor-pointer text-xs font-semibold text-slate-500">Advanced staged payload</summary>
        <pre className="mt-2 max-h-48 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(item.payload || {}, null, 2)}</pre>
      </details>
    </div>
  )
}

function FlagGrid({ form, setForm }) {
  const flags = ["safe_for_agency_internal_crm", "safe_for_offer_builder", "safe_for_agency_display", "safe_for_cms_display", "safe_for_client_portal_later", "is_operationally_verified", "is_demo_data"]
  return (
    <div className="grid gap-2 text-sm md:grid-cols-2 xl:grid-cols-1">
      {flags.map((flag) => (
        <label className="flex items-start gap-2 rounded-md border border-slate-200 bg-slate-50 p-3" key={flag}>
          <input type="checkbox" checked={form[flag]} onChange={(event) => setForm({ ...form, [flag]: event.target.checked })} />
          <span>
            <span className="block font-semibold text-slate-800">{flagLabel(flag)}</span>
            <span className="text-xs text-slate-500">{flagHelp(flag)}</span>
          </span>
        </label>
      ))}
    </div>
  )
}

function Field({ label, value, onChange, required = false, placeholder = "" }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} required={required} placeholder={placeholder} />
    </label>
  )
}

function TextArea({ label, value, onChange, required = false }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} required={required} />
    </label>
  )
}

function Select({ label, value, options, onChange }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{labelText(option)}</option>)}
      </select>
    </label>
  )
}

function StatusBadge({ status, demo, verified }) {
  const text = demo ? "Demo/sample data" : verified ? "Operationally verified" : labelText(status || "needs_review")
  const tone = verified && !demo ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-700 ring-amber-200"
  return <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ring-1 ${tone}`}>{text}</span>
}

function labelText(value) {
  return label(value)
}

function label(value) {
  return String(value || "").replaceAll("_", " ")
}

function flagLabel(flag) {
  const labels = {
    safe_for_agency_internal_crm: "Safe for agency internal CRM use",
    safe_for_agency_display: "Safe for agency display",
    safe_for_cms_display: "Available for agency website",
    safe_for_client_portal_later: "Available for client portal later",
    safe_for_offer_builder: "Available for offer builder",
    is_operationally_verified: "Operationally verified",
    is_demo_data: "Demo/sample data",
  }
  return labels[flag] || label(flag)
}

function flagHelp(flag) {
  const help = {
    safe_for_agency_internal_crm: "May support future internal client and account enrichment.",
    safe_for_agency_display: "May be shown inside agency workspaces.",
    safe_for_cms_display: "May support future agency website content.",
    safe_for_client_portal_later: "May support later client portal explanations.",
    safe_for_offer_builder: "May support future offer builder context.",
    is_operationally_verified: "Reviewed enough for operational interpretation.",
    is_demo_data: "Sample data only; not operationally verified.",
  }
  return help[flag] || ""
}

function splitCodes(value) {
  return String(value || "").split(/[, ]+/).map((item) => item.trim().toUpperCase()).filter(Boolean)
}

function parseJson(value) {
  try {
    return JSON.parse(value || "{}")
  } catch {
    return { raw_text: value }
  }
}
