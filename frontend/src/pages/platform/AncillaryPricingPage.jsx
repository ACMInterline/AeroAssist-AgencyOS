import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

const base = "/api/platform/ancillary-pricing"

const tabs = [
  ["pricing_rules", "Pricing rules", `${base}/pricing-rules`, "pricing_status"],
  ["price_components", "Components", `${base}/price-components`, "status"],
  ["applicability", "Applicability", `${base}/applicability`, "status"],
  ["pricing_matrices", "Matrices", `${base}/pricing-matrices`, "status"],
  ["pricing_matrix_rows", "Matrix rows", `${base}/pricing-matrix-rows`, "status"],
  ["exception_rules", "Exceptions", `${base}/exception-rules`, "status"],
  ["quote_scenarios", "Quote scenarios", `${base}/quote-scenarios`, null],
  ["quote_results", "Quote results", `${base}/quote-results`, null],
  ["candidate_pricing_links", "Candidate links", `${base}/candidate-pricing-links`, "review_status"],
]

const defaults = {
  pricing_rules: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    pricing_rule_name: "LH WCHR service pricing",
    pricing_status: "active",
    review_status: "suggested",
    mandatory_service: false,
    optional_service: true,
    fee_included_in_fare: false,
    separate_fee_required: true,
    emd_required: false,
    payment_rule_id: "",
    emd_issuance_rule_id: "",
    notes: "",
  },
  price_components: {
    pricing_rule_id: "",
    component_type: "service_fee",
    amount: "35",
    currency: "EUR",
    amount_type: "fixed",
    applies_per: "passenger",
    roundtrip_doubling_rule: false,
    sequence: "100",
    notes: "",
  },
  applicability: {
    pricing_rule_id: "",
    dimension_code: "direct_vs_connecting",
    operator: "any",
    value: "",
    value_json: "{}",
    applies_as: "condition",
  },
  pricing_matrices: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    matrix_name: "LH wheelchair pricing matrix",
    currency: "EUR",
    scope: "global",
  },
  pricing_matrix_rows: {
    matrix_id: "",
    pricing_rule_id: "",
    row_label: "Adult passenger direct route",
    direct_vs_connecting: "direct",
    passenger_type: "adult",
    cabin: "economy",
    amount: "35",
    currency: "EUR",
    applies_per: "passenger",
    emd_required: false,
    sort_order: "100",
    notes: "",
  },
  exception_rules: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    exception_name: "Manual confirmation for connecting itinerary",
    exception_type: "connection_restriction",
    severity: "warning",
    outcome: "manual_review",
    condition_json: "{\"direct_vs_connecting\":\"connecting\"}",
    explanation: "Connecting itineraries require manual review before quoting.",
    suggested_action: "Contact airline support desk before confirming the quote.",
    pricing_rule_id: "",
    mechanics_record_id: "",
  },
  quote_scenarios: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    scenario_name: "LH WCHR adult direct quote",
    passenger_age: "34",
    passenger_type: "adult",
    route_type: "international",
    direct_vs_connecting: "direct",
    origin_airport: "SOF",
    destination_airport: "FRA",
    origin_country: "BG",
    destination_country: "DE",
    cabin: "economy",
    segment_count: "1",
    direction_count: "1",
    currency: "EUR",
    context_json: "{}",
  },
  candidate_pricing_links: {
    candidate_type: "extracted_price",
    candidate_id: "",
    taxonomy_link_id: "",
    mechanics_link_id: "",
    pricing_record_type: "pricing_rule",
    pricing_record_id: "",
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    confidence_score: "0.7",
    evidence_text: "",
  },
}

const fieldSpecs = {
  pricing_rules: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["pricing_rule_name", "Rule name"],
    ["pricing_status", "Status", "select", ["draft", "active", "archived"]],
    ["review_status", "Review", "select", ["suggested", "confirmed", "corrected", "rejected", "needs_review"]],
    ["mandatory_service", "Mandatory", "checkbox"],
    ["optional_service", "Optional", "checkbox"],
    ["fee_included_in_fare", "Included in fare", "checkbox"],
    ["separate_fee_required", "Separate fee", "checkbox"],
    ["emd_required", "EMD referenced", "checkbox"],
    ["payment_rule_id", "Payment rule ID"],
    ["emd_issuance_rule_id", "EMD issuance rule ID"],
    ["notes", "Notes", "textarea"],
  ],
  price_components: [
    ["pricing_rule_id", "Pricing rule ID"],
    ["component_type", "Component", "select", ["base_fee", "service_fee", "direction_fee", "segment_fee", "connection_fee", "document_fee", "airport_fee", "child_fee", "adult_fee", "other"]],
    ["amount", "Amount", "number"],
    ["currency", "Currency"],
    ["amount_type", "Amount type", "select", ["fixed", "range", "percentage", "included", "unknown"]],
    ["applies_per", "Applies per", "select", ["passenger", "direction", "segment", "journey", "booking", "coupon", "emd", "other"]],
    ["roundtrip_doubling_rule", "Roundtrip doubling", "checkbox"],
    ["sequence", "Sequence", "number"],
    ["notes", "Notes", "textarea"],
  ],
  applicability: [
    ["pricing_rule_id", "Pricing rule ID"],
    ["dimension_code", "Dimension"],
    ["operator", "Operator", "select", ["equals", "not_equals", "in", "not_in", "min", "max", "between", "contains", "exists", "not_exists", "any"]],
    ["value", "Value"],
    ["value_json", "Value JSON", "textarea"],
    ["applies_as", "Applies as", "select", ["condition", "exclusion", "surcharge", "discount", "manual_review"]],
  ],
  pricing_matrices: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["matrix_name", "Matrix name"],
    ["currency", "Currency"],
    ["scope", "Scope", "select", ["global", "agency"]],
  ],
  pricing_matrix_rows: [
    ["matrix_id", "Matrix ID"],
    ["pricing_rule_id", "Pricing rule ID"],
    ["row_label", "Row label"],
    ["direct_vs_connecting", "Direct/connecting"],
    ["passenger_type", "Passenger type"],
    ["cabin", "Cabin"],
    ["amount", "Amount", "number"],
    ["currency", "Currency"],
    ["applies_per", "Applies per", "select", ["passenger", "direction", "segment", "journey", "booking", "coupon", "emd", "other"]],
    ["emd_required", "EMD referenced", "checkbox"],
    ["sort_order", "Sort order", "number"],
    ["notes", "Notes", "textarea"],
  ],
  exception_rules: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["exception_name", "Exception name"],
    ["exception_type", "Type", "select", ["service_not_permitted", "pricing_not_available", "route_restriction", "connection_restriction", "age_restriction", "country_restriction", "airport_restriction", "interline_restriction", "aircraft_restriction", "cabin_restriction", "deadline_restriction", "document_required", "manual_contact_required", "emd_required", "payment_restriction", "unknown"]],
    ["severity", "Severity", "select", ["info", "advisory", "warning", "blocker"]],
    ["outcome", "Outcome", "select", ["permitted", "not_permitted", "manual_review", "surcharge_required", "document_required", "airline_confirmation_required", "payment_required", "unknown"]],
    ["condition_json", "Condition JSON", "textarea"],
    ["explanation", "Explanation", "textarea"],
    ["suggested_action", "Suggested action"],
    ["pricing_rule_id", "Pricing rule ID"],
    ["mechanics_record_id", "Mechanics record ID"],
  ],
  quote_scenarios: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["scenario_name", "Scenario name"],
    ["passenger_age", "Passenger age", "number"],
    ["passenger_type", "Passenger type"],
    ["route_type", "Route type"],
    ["direct_vs_connecting", "Direct/connecting"],
    ["origin_airport", "Origin airport"],
    ["destination_airport", "Destination airport"],
    ["origin_country", "Origin country"],
    ["destination_country", "Destination country"],
    ["cabin", "Cabin"],
    ["segment_count", "Segments", "number"],
    ["direction_count", "Directions", "number"],
    ["currency", "Currency"],
    ["context_json", "Context JSON", "textarea"],
  ],
  candidate_pricing_links: [
    ["candidate_type", "Candidate type", "select", ["extracted_rule", "extracted_price", "extracted_communication", "extracted_emd_rule", "extracted_exception", "approved_knowledge"]],
    ["candidate_id", "Candidate ID"],
    ["taxonomy_link_id", "Taxonomy link ID"],
    ["mechanics_link_id", "Mechanics link ID"],
    ["pricing_record_type", "Pricing record", "select", ["pricing_rule", "price_component", "applicability", "pricing_matrix", "pricing_matrix_row", "exception_rule"]],
    ["pricing_record_id", "Pricing record ID"],
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["confidence_score", "Confidence", "number"],
    ["evidence_text", "Evidence", "textarea"],
  ],
}

const metricKeys = [
  ["Rules", "pricing_rule_count"],
  ["Components", "price_component_count"],
  ["Applicability", "pricing_applicability_count"],
  ["Matrices", "pricing_matrix_count"],
  ["Exceptions", "service_exception_rule_count"],
  ["Quotes", "quote_result_count"],
]

export default function AncillaryPricingPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("pricing_rules")
  const [forms, setForms] = useState(defaults)
  const [lookupForm, setLookupForm] = useState({ airline_code: "LH", domain_code: "mobility", family_code: "wheelchair", variant_code: "wchr" })
  const [lookupResult, setLookupResult] = useState(null)
  const [quoteResult, setQuoteResult] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const [summary, ...collections] = await Promise.all([
      apiGet(`${base}/summary`),
      ...tabs.map((item) => apiGet(item[2])),
    ])
    const collectionState = {}
    tabs.forEach((item, index) => {
      collectionState[item[0]] = collections[index].items || []
    })
    setState({ summary, ...collectionState })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const active = tabs.find((item) => item[0] === tab)
  const summaryCards = useMemo(() => metricKeys.map(([metricLabel, key]) => [metricLabel, state?.summary?.[key] ?? 0]), [state])

  function setFormValue(key, value) {
    setForms({ ...forms, [tab]: { ...forms[tab], [key]: value } })
  }

  async function createRecord(event) {
    event.preventDefault()
    if (!active || tab === "quote_results") return
    setWorking(`create-${tab}`)
    setError("")
    setMessage("")
    try {
      await apiPost(active[2], cleanPayload(forms[tab]))
      setMessage(`${active[1]} saved.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function archiveRecord(item) {
    if (!active?.[3]) return
    setWorking(item.id)
    setError("")
    try {
      const payload = active[3] === "review_status" ? { review_status: "rejected" } : { [active[3]]: "archived" }
      await apiPatch(`${active[2]}/${item.id}`, payload)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function runLookup(event) {
    event.preventDefault()
    setWorking("lookup")
    setError("")
    try {
      setLookupResult(await apiPost(`${base}/lookup`, cleanPayload(lookupForm)))
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function runQuote(event) {
    event.preventDefault()
    setWorking("quote")
    setError("")
    try {
      const result = await apiPost(`${base}/evaluate`, cleanPayload(forms.quote_scenarios))
      setQuoteResult(result)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  return (
    <PlatformLayout>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Ancillary Pricing</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Pricing Schema and Exceptions</h2>
              <p className="mt-1 text-sm text-slate-600">Pricing estimate != invoice, payment, accounting, settlement, or EMD issuance.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Provider execution disabled</span>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {summaryCards.map(([cardLabel, value]) => <Metric label={cardLabel} value={value} key={cardLabel} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createRecord}>
                <h3 className="font-semibold text-slate-950">{active?.[1]}</h3>
                {tab === "quote_results" ? (
                  <p className="text-sm text-slate-600">Quote results are stored by deterministic evaluation.</p>
                ) : (
                  <FormFields specs={fieldSpecs[tab] || []} values={forms[tab] || {}} onChange={setFormValue} />
                )}
                {tab !== "quote_results" ? (
                  <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === `create-${tab}`}>
                    {working === `create-${tab}` ? "Saving..." : "Save"}
                  </button>
                ) : null}
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runLookup}>
                <h3 className="font-semibold text-slate-950">Lookup</h3>
                <Field label="Airline code" value={lookupForm.airline_code} onChange={(value) => setLookupForm({ ...lookupForm, airline_code: value.toUpperCase() })} />
                <Field label="Domain code" value={lookupForm.domain_code} onChange={(value) => setLookupForm({ ...lookupForm, domain_code: value })} />
                <Field label="Family code" value={lookupForm.family_code} onChange={(value) => setLookupForm({ ...lookupForm, family_code: value })} />
                <Field label="Variant code" value={lookupForm.variant_code} onChange={(value) => setLookupForm({ ...lookupForm, variant_code: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "lookup"}>{working === "lookup" ? "Looking up..." : "Run lookup"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runQuote}>
                <h3 className="font-semibold text-slate-950">Quote evaluation</h3>
                <FormFields specs={fieldSpecs.quote_scenarios} values={forms.quote_scenarios} onChange={(key, value) => setForms({ ...forms, quote_scenarios: { ...forms.quote_scenarios, [key]: value } })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "quote"}>{working === "quote" ? "Evaluating..." : "Evaluate"}</button>
              </form>
            </div>

            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex flex-wrap gap-2">
                  {tabs.map(([key, tabLabel]) => (
                    <button className={`rounded-md px-3 py-2 text-sm font-semibold ${tab === key ? "bg-blue-600 text-white" : "border border-slate-300 text-slate-700"}`} type="button" key={key} onClick={() => setTab(key)}>
                      {tabLabel}
                    </button>
                  ))}
                </div>
              </div>

              <RecordList title={active?.[1] || "Records"} items={state?.[tab] || []} onArchive={archiveRecord} archiveField={active?.[3]} working={working} />

              {lookupResult ? <JsonPanel title="Lookup result" data={lookupResult} /> : null}
              {quoteResult ? <JsonPanel title="Quote result" data={quoteResult} /> : null}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function RecordList({ title, items, onArchive, archiveField, working }) {
  if (!items.length) {
    return <EmptyState title={`No ${title.toLowerCase()}`} body="No records found." />
  }
  return (
    <div className="divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      {items.map((item) => (
        <div className="grid gap-3 p-4 text-sm lg:grid-cols-[220px_minmax(0,1fr)_150px_110px]" key={item.id}>
          <div className="min-w-0">
            <p className="truncate font-semibold text-slate-950">{primaryLabel(item)}</p>
            <p className="truncate text-xs text-slate-500">{item.airline_code || item.pricing_record_type || "global"} / {label(item.pricing_status || item.status || item.review_status)}</p>
          </div>
          <div className="min-w-0 text-slate-600">
            <p className="truncate">{taxonomyPath(item)}</p>
            <p className="truncate text-xs">{item.id}</p>
          </div>
          <span className="text-slate-600">{item.amount ?? item.amount_type ?? item.outcome ?? item.evaluation_status ?? item.confidence_score ?? "metadata"}</span>
          {archiveField ? (
            <button className="rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold disabled:opacity-60" type="button" onClick={() => onArchive(item)} disabled={working === item.id}>
              {archiveField === "review_status" ? "Reject" : "Archive"}
            </button>
          ) : <span />}
        </div>
      ))}
    </div>
  )
}

function FormFields({ specs, values, onChange }) {
  return (
    <div className="grid gap-3">
      {specs.map(([name, fieldLabel, type, options]) => <DynamicField name={name} label={fieldLabel} type={type} options={options} value={values[name]} onChange={(value) => onChange(name, value)} key={name} />)}
    </div>
  )
}

function DynamicField({ label: fieldLabel, type, options, value, onChange }) {
  if (type === "checkbox") {
    return (
      <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
        {fieldLabel}
      </label>
    )
  }
  if (type === "select") return <Select label={fieldLabel} value={value ?? ""} options={options} onChange={onChange} />
  if (type === "textarea") return <TextArea label={fieldLabel} value={value ?? ""} onChange={onChange} />
  return <Field label={fieldLabel} value={value ?? ""} type={type === "number" ? "number" : "text"} onChange={onChange} />
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

function JsonPanel({ title, data }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <pre className="mt-3 max-h-[460px] overflow-auto rounded-md bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(data, null, 2)}</pre>
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

function cleanPayload(payload) {
  const clean = { ...payload }
  Object.keys(clean).forEach((key) => {
    if (clean[key] === "") clean[key] = null
    if (["amount", "min_amount", "max_amount", "confidence_score"].includes(key) && clean[key] !== null) clean[key] = Number(clean[key])
    if (["sequence", "sort_order", "passenger_age", "segment_count", "direction_count", "min_age", "max_age"].includes(key) && clean[key] !== null) clean[key] = Number(clean[key])
    if (["condition_json", "context_json", "value_json"].includes(key)) {
      try {
        clean[key] = clean[key] ? JSON.parse(clean[key]) : {}
      } catch {
        clean[key] = {}
      }
    }
  })
  return clean
}

function primaryLabel(item) {
  return item.pricing_rule_name || item.component_type || item.dimension_code || item.matrix_name || item.row_label || item.exception_name || item.scenario_name || item.pricing_record_id || item.id
}

function taxonomyPath(item) {
  return [item.domain_code, item.family_code, item.variant_code].filter(Boolean).join(" / ") || item.pricing_rule_id || item.matrix_id || item.scenario_id || "not mapped"
}

function label(value) {
  return String(value || "not set").replaceAll("_", " ")
}
