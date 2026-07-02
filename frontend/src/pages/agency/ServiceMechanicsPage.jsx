import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const tabs = [
  ["communication_rules", "Communication rules", "communication-rules"],
  ["ssr_osi_templates", "SSR/OSI templates", "ssr-osi-templates"],
  ["requirements", "Requirements", "requirements"],
  ["status_recognition_rules", "Status recognition", "status-recognition-rules"],
  ["rejection_patterns", "Rejection patterns", "rejection-patterns"],
  ["payment_rules", "Payment rules", "payment-rules"],
  ["emd_issuance_rules", "EMD issuance", "emd-issuance-rules"],
  ["rfic_rfisc_mappings", "RFIC/RFISC", "rfic-rfisc-mappings"],
  ["emd_interline_rules", "Interline", "emd-interline-rules"],
  ["emd_lifecycle_rules", "Lifecycle", "emd-lifecycle-rules"],
  ["candidate_mechanics_links", "Candidate links", "candidate-mechanics-links"],
]

export default function ServiceMechanicsPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("communication_rules")
  const [lookupForm, setLookupForm] = useState({ airline_code: "LH", domain_code: "mobility", family_code: "wheelchair", variant_code: "wchr" })
  const [linkForm, setLinkForm] = useState({
    candidate_type: "extracted_communication",
    candidate_id: "",
    taxonomy_link_id: "",
    mechanics_type: "communication_rule",
    mechanics_record_id: "",
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    confidence_score: "0.7",
    evidence_text: "",
  })
  const [lookupResult, setLookupResult] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/service-mechanics`
    const [summary, taxonomySummary, ...collections] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`/api/agencies/${context.agency.id}/service-taxonomy/summary`),
      ...tabs.map((item) => apiGet(`${base}/${item[2]}`)),
    ])
    const collectionState = {}
    tabs.forEach((item, index) => {
      collectionState[item[0]] = collections[index].items || []
    })
    setState({
      ...context,
      base,
      summary,
      taxonomySummary,
      ...collectionState,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const summaryCards = useMemo(() => [
    ["Communication", state?.summary?.communication_rule_count],
    ["Templates", state?.summary?.ssr_osi_template_count],
    ["Payment", state?.summary?.payment_rule_count],
    ["EMD rules", state?.summary?.emd_issuance_rule_count],
    ["RFIC/RFISC", state?.summary?.rfic_rfisc_mapping_count],
    ["Local links", state?.summary?.candidate_mechanics_link_count],
  ], [state])

  async function runLookup(event) {
    event.preventDefault()
    setWorking("lookup")
    setError("")
    try {
      setLookupResult(await apiPost(`${state.base}/lookup`, cleanPayload(lookupForm)))
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function createLink(event) {
    event.preventDefault()
    setWorking("link")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/candidate-mechanics-links`, cleanPayload(linkForm))
      setMessage(`Local mechanics link saved as ${label(result.link.review_status)}.`)
      setLinkForm({ ...linkForm, candidate_id: "", taxonomy_link_id: "", mechanics_record_id: "", evidence_text: "" })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Service Mechanics</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">SSR/OSI and EMD Mechanics Lookup</h2>
              <p className="mt-1 text-sm text-slate-600">Global mechanics are read-only. Local links stay scoped to this agency.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No global mutation controls</span>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}
          {state?.taxonomySummary?.domain_count === 0 ? (
            <EmptyState title="No canonical taxonomy records found" body="Lookup can still use manually entered codes, but platform taxonomy seed or governance is needed before canonical service selection is complete." />
          ) : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {summaryCards.map(([cardLabel, value]) => <Metric label={cardLabel} value={value ?? 0} key={cardLabel} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runLookup}>
                <h3 className="font-semibold text-slate-950">Lookup tester</h3>
                <Field label="Airline code" value={lookupForm.airline_code} onChange={(value) => setLookupForm({ ...lookupForm, airline_code: value.toUpperCase() })} />
                <Field label="Domain code" value={lookupForm.domain_code} onChange={(value) => setLookupForm({ ...lookupForm, domain_code: value })} />
                <Field label="Family code" value={lookupForm.family_code} onChange={(value) => setLookupForm({ ...lookupForm, family_code: value })} />
                <Field label="Variant code" value={lookupForm.variant_code} onChange={(value) => setLookupForm({ ...lookupForm, variant_code: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "lookup"}>
                  {working === "lookup" ? "Looking up..." : "Run lookup"}
                </button>
                {lookupResult ? <LookupResult result={lookupResult} /> : null}
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createLink}>
                <h3 className="font-semibold text-slate-950">Create local candidate link</h3>
                <Select label="Candidate type" value={linkForm.candidate_type} options={["extracted_rule", "extracted_price", "extracted_communication", "extracted_emd_rule", "extracted_exception", "approved_knowledge"]} onChange={(value) => setLinkForm({ ...linkForm, candidate_type: value })} />
                <Field label="Candidate id" value={linkForm.candidate_id} onChange={(value) => setLinkForm({ ...linkForm, candidate_id: value })} />
                <Field label="Taxonomy link id" value={linkForm.taxonomy_link_id} onChange={(value) => setLinkForm({ ...linkForm, taxonomy_link_id: value })} />
                <Select label="Mechanics type" value={linkForm.mechanics_type} options={["communication_rule", "ssr_osi_template", "requirement", "status_recognition", "rejection_pattern", "payment_rule", "emd_issuance_rule", "rfic_rfisc_mapping", "interline_rule", "lifecycle_rule"]} onChange={(value) => setLinkForm({ ...linkForm, mechanics_type: value })} />
                <Field label="Mechanics record id" value={linkForm.mechanics_record_id} onChange={(value) => setLinkForm({ ...linkForm, mechanics_record_id: value })} />
                <Field label="Airline code" value={linkForm.airline_code} onChange={(value) => setLinkForm({ ...linkForm, airline_code: value.toUpperCase() })} />
                <Field label="Domain code" value={linkForm.domain_code} onChange={(value) => setLinkForm({ ...linkForm, domain_code: value })} />
                <Field label="Family code" value={linkForm.family_code} onChange={(value) => setLinkForm({ ...linkForm, family_code: value })} />
                <Field label="Variant code" value={linkForm.variant_code} onChange={(value) => setLinkForm({ ...linkForm, variant_code: value })} />
                <Field label="Confidence" value={linkForm.confidence_score} type="number" onChange={(value) => setLinkForm({ ...linkForm, confidence_score: value })} />
                <TextArea label="Evidence text" value={linkForm.evidence_text} onChange={(value) => setLinkForm({ ...linkForm, evidence_text: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "link"}>{working === "link" ? "Saving..." : "Save local link"}</button>
              </form>
            </div>

            <section className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-5 py-4">
                <div className="flex flex-wrap gap-2">
                  {tabs.map(([key, title]) => (
                    <button className={`rounded-md px-3 py-2 text-sm font-semibold ${tab === key ? "bg-blue-600 text-white" : "border border-slate-300 text-slate-700"}`} type="button" key={key} onClick={() => setTab(key)}>
                      {title}
                    </button>
                  ))}
                </div>
              </div>
              <MechanicsTable items={state?.[tab] || []} tab={tab} />
            </section>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function LookupResult({ result }) {
  return (
    <div className="space-y-3 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-950">
      <LookupPanel title="Communication mechanics" groups={result.communication} />
      <LookupPanel title="Payment and EMD mechanics" groups={result.payment} />
      {result.warnings?.length ? <p className="text-blue-800">{result.warnings.join(" ")}</p> : null}
    </div>
  )
}

function LookupPanel({ title, groups }) {
  const count = Object.values(groups || {}).reduce((sum, items) => sum + (items?.length || 0), 0)
  return (
    <div>
      <p className="font-semibold">{title}: {count}</p>
      <div className="mt-1 grid gap-1 text-xs text-blue-800">
        {Object.entries(groups || {}).map(([key, items]) => <span key={key}>{label(key)}: {items.length}</span>)}
      </div>
    </div>
  )
}

function MechanicsTable({ items, tab }) {
  if (!items.length) {
    return <EmptyState title={`No ${label(tab)}`} body="Records will appear here when platform governance or agency-local links exist." />
  }

  return (
    <div className="divide-y divide-slate-100">
      {items.map((item) => (
        <div className="grid gap-3 p-4 text-sm lg:grid-cols-[220px_minmax(0,1fr)_150px]" key={item.id}>
          <div>
            <p className="font-semibold text-slate-950">{primaryLabel(item)}</p>
            <p className="text-xs text-slate-500">{item.airline_code || item.mechanics_type || "global"} · {label(item.status || item.review_status)}</p>
          </div>
          <div className="min-w-0 text-slate-600">
            <p className="truncate">{taxonomyPath(item)}</p>
            <p className="truncate text-xs">{item.template_text || item.match_value || item.pattern_text || item.reason_for_issuance_description || item.evidence_text || item.notes || "No note"}</p>
          </div>
          <span className="text-slate-600">{item.request_method || item.template_type || item.emd_type || item.payment_timing || formatConfidence(item.confidence_score)}</span>
        </div>
      ))}
    </div>
  )
}

function Metric({ label: metricLabel, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className="mt-2 text-xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Field({ label: fieldLabel, value, onChange, type = "text" }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function TextArea({ label: fieldLabel, value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label: fieldLabel, value, options, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{label(option)}</option>)}
      </select>
    </label>
  )
}

function cleanPayload(payload) {
  const clean = { ...payload }
  Object.keys(clean).forEach((key) => {
    if (clean[key] === "") clean[key] = null
    if (key === "confidence_score" && clean[key] !== null) clean[key] = Number(clean[key])
  })
  return clean
}

function primaryLabel(item) {
  return item.canonical_service_label || item.commercial_name || item.requirement_label || item.ssr_code || item.rejection_code || item.mechanics_record_id || item.id
}

function taxonomyPath(item) {
  return [item.domain_code, item.family_code, item.variant_code].filter(Boolean).join(" / ") || "not mapped"
}

function formatConfidence(value) {
  const number = Number(value)
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "not set"
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}
