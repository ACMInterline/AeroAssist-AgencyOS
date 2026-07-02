import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const tabs = [
  ["pricing_rules", "Pricing rules", "pricing-rules"],
  ["price_components", "Components", "price-components"],
  ["applicability", "Applicability", "applicability"],
  ["pricing_matrices", "Matrices", "pricing-matrices"],
  ["pricing_matrix_rows", "Matrix rows", "pricing-matrix-rows"],
  ["exception_rules", "Exceptions", "exception-rules"],
  ["quote_scenarios", "Quote scenarios", "quote-scenarios"],
  ["quote_results", "Quote results", "quote-results"],
  ["candidate_pricing_links", "Candidate links", "candidate-pricing-links"],
]

const quoteDefaults = {
  airline_code: "LH",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
  scenario_name: "Agency WCHR quote scenario",
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
}

const linkDefaults = {
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
}

export default function AncillaryPricingPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("pricing_rules")
  const [lookupForm, setLookupForm] = useState({ airline_code: "LH", domain_code: "mobility", family_code: "wheelchair", variant_code: "wchr" })
  const [quoteForm, setQuoteForm] = useState(quoteDefaults)
  const [linkForm, setLinkForm] = useState(linkDefaults)
  const [lookupResult, setLookupResult] = useState(null)
  const [quoteResult, setQuoteResult] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/ancillary-pricing`
    const [summary, ...collections] = await Promise.all([
      apiGet(`${base}/summary`),
      ...tabs.map((item) => apiGet(`${base}/${item[2]}`)),
    ])
    const collectionState = {}
    tabs.forEach((item, index) => {
      collectionState[item[0]] = collections[index].items || []
    })
    setState({ ...context, base, summary, ...collectionState })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const summaryCards = useMemo(() => [
    ["Rules", state?.summary?.pricing_rule_count],
    ["Components", state?.summary?.price_component_count],
    ["Exceptions", state?.summary?.service_exception_rule_count],
    ["Scenarios", state?.summary?.quote_scenario_count],
    ["Results", state?.summary?.quote_result_count],
    ["Local links", state?.summary?.candidate_pricing_link_count],
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

  async function runQuote(event) {
    event.preventDefault()
    setWorking("quote")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/evaluate`, cleanPayload(quoteForm))
      setQuoteResult(result)
      setMessage(`Quote evaluated as ${label(result.result.evaluation_status)}.`)
      await load()
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
      const result = await apiPost(`${state.base}/candidate-pricing-links`, cleanPayload(linkForm))
      setMessage(`Local pricing link saved as ${label(result.link.review_status)}.`)
      setLinkForm({ ...linkDefaults, airline_code: linkForm.airline_code, domain_code: linkForm.domain_code, family_code: linkForm.family_code, variant_code: linkForm.variant_code })
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
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Ancillary Pricing</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Pricing Lookup and Exceptions</h2>
              <p className="mt-1 text-sm text-slate-600">Estimates are non-binding and separate from invoices, payments, settlement, provider execution, and EMD issuance.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Read-only global pricing</span>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {summaryCards.map(([cardLabel, value]) => <Metric label={cardLabel} value={value ?? 0} key={cardLabel} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runLookup}>
                <h3 className="font-semibold text-slate-950">Lookup</h3>
                <Field label="Airline code" value={lookupForm.airline_code} onChange={(value) => setLookupForm({ ...lookupForm, airline_code: value.toUpperCase() })} />
                <Field label="Domain code" value={lookupForm.domain_code} onChange={(value) => setLookupForm({ ...lookupForm, domain_code: value })} />
                <Field label="Family code" value={lookupForm.family_code} onChange={(value) => setLookupForm({ ...lookupForm, family_code: value })} />
                <Field label="Variant code" value={lookupForm.variant_code} onChange={(value) => setLookupForm({ ...lookupForm, variant_code: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "lookup"}>{working === "lookup" ? "Looking up..." : "Run lookup"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runQuote}>
                <h3 className="font-semibold text-slate-950">Quote evaluation</h3>
                <QuoteFields values={quoteForm} onChange={(key, value) => setQuoteForm({ ...quoteForm, [key]: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "quote"}>{working === "quote" ? "Evaluating..." : "Evaluate"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createLink}>
                <h3 className="font-semibold text-slate-950">Local candidate link</h3>
                <Select label="Candidate type" value={linkForm.candidate_type} options={["extracted_rule", "extracted_price", "extracted_communication", "extracted_emd_rule", "extracted_exception", "approved_knowledge"]} onChange={(value) => setLinkForm({ ...linkForm, candidate_type: value })} />
                <Field label="Candidate ID" value={linkForm.candidate_id} onChange={(value) => setLinkForm({ ...linkForm, candidate_id: value })} />
                <Field label="Taxonomy link ID" value={linkForm.taxonomy_link_id} onChange={(value) => setLinkForm({ ...linkForm, taxonomy_link_id: value })} />
                <Field label="Mechanics link ID" value={linkForm.mechanics_link_id} onChange={(value) => setLinkForm({ ...linkForm, mechanics_link_id: value })} />
                <Select label="Pricing record" value={linkForm.pricing_record_type} options={["pricing_rule", "price_component", "applicability", "pricing_matrix", "pricing_matrix_row", "exception_rule"]} onChange={(value) => setLinkForm({ ...linkForm, pricing_record_type: value })} />
                <Field label="Pricing record ID" value={linkForm.pricing_record_id} onChange={(value) => setLinkForm({ ...linkForm, pricing_record_id: value })} />
                <Field label="Airline code" value={linkForm.airline_code} onChange={(value) => setLinkForm({ ...linkForm, airline_code: value.toUpperCase() })} />
                <Field label="Domain code" value={linkForm.domain_code} onChange={(value) => setLinkForm({ ...linkForm, domain_code: value })} />
                <Field label="Family code" value={linkForm.family_code} onChange={(value) => setLinkForm({ ...linkForm, family_code: value })} />
                <Field label="Variant code" value={linkForm.variant_code} onChange={(value) => setLinkForm({ ...linkForm, variant_code: value })} />
                <Field label="Confidence" type="number" value={linkForm.confidence_score} onChange={(value) => setLinkForm({ ...linkForm, confidence_score: value })} />
                <TextArea label="Evidence" value={linkForm.evidence_text} onChange={(value) => setLinkForm({ ...linkForm, evidence_text: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "link"}>{working === "link" ? "Saving..." : "Save local link"}</button>
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

              <RecordList title={label(tab)} items={state?.[tab] || []} />
              {lookupResult ? <JsonPanel title="Lookup result" data={lookupResult} /> : null}
              {quoteResult ? <JsonPanel title="Quote result" data={quoteResult} /> : null}
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function QuoteFields({ values, onChange }) {
  const fields = [
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
  ]
  return (
    <div className="grid gap-3">
      {fields.map(([key, fieldLabel, type]) => {
        if (type === "textarea") return <TextArea label={fieldLabel} value={values[key]} onChange={(value) => onChange(key, value)} key={key} />
        return <Field label={fieldLabel} value={values[key]} type={type === "number" ? "number" : "text"} onChange={(value) => onChange(key, key.includes("airport") || key.includes("country") || key === "airline_code" || key === "currency" ? value.toUpperCase() : value)} key={key} />
      })}
    </div>
  )
}

function RecordList({ title, items }) {
  if (!items.length) {
    return <EmptyState title={`No ${title}`} body="No records found." />
  }
  return (
    <div className="divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      {items.map((item) => (
        <div className="grid gap-3 p-4 text-sm lg:grid-cols-[220px_minmax(0,1fr)_150px]" key={item.id}>
          <div className="min-w-0">
            <p className="truncate font-semibold text-slate-950">{primaryLabel(item)}</p>
            <p className="truncate text-xs text-slate-500">{item.airline_code || item.pricing_record_type || "global"} / {label(item.pricing_status || item.status || item.review_status || item.evaluation_status)}</p>
          </div>
          <div className="min-w-0 text-slate-600">
            <p className="truncate">{taxonomyPath(item)}</p>
            <p className="truncate text-xs">{item.id}</p>
          </div>
          <span className="text-slate-600">{item.amount ?? item.amount_type ?? item.outcome ?? item.estimated_amount ?? item.confidence_score ?? "metadata"}</span>
        </div>
      ))}
    </div>
  )
}

function Field({ label: fieldLabel, value, onChange, type = "text" }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value || ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function TextArea({ label: fieldLabel, value, onChange }) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {fieldLabel}
      <textarea className="mt-1 min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} onChange={(event) => onChange(event.target.value)} />
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
    if (["confidence_score"].includes(key) && clean[key] !== null) clean[key] = Number(clean[key])
    if (["passenger_age", "segment_count", "direction_count"].includes(key) && clean[key] !== null) clean[key] = Number(clean[key])
    if (["context_json"].includes(key)) {
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
