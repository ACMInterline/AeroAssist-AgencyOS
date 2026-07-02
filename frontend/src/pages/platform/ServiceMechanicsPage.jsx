import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

const tabs = [
  ["communication_rules", "Communication rules", "/api/platform/service-mechanics/communication-rules"],
  ["ssr_osi_templates", "SSR/OSI templates", "/api/platform/service-mechanics/ssr-osi-templates"],
  ["requirements", "Requirements", "/api/platform/service-mechanics/requirements"],
  ["status_recognition_rules", "Status recognition", "/api/platform/service-mechanics/status-recognition-rules"],
  ["rejection_patterns", "Rejection patterns", "/api/platform/service-mechanics/rejection-patterns"],
  ["payment_rules", "Payment rules", "/api/platform/service-mechanics/payment-rules"],
  ["emd_issuance_rules", "EMD issuance", "/api/platform/service-mechanics/emd-issuance-rules"],
  ["rfic_rfisc_mappings", "RFIC/RFISC", "/api/platform/service-mechanics/rfic-rfisc-mappings"],
  ["emd_interline_rules", "Interline", "/api/platform/service-mechanics/emd-interline-rules"],
  ["emd_lifecycle_rules", "Lifecycle", "/api/platform/service-mechanics/emd-lifecycle-rules"],
  ["candidate_mechanics_links", "Candidate links", "/api/platform/service-mechanics/candidate-mechanics-links"],
]

const defaults = {
  communication_rules: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    canonical_service_label: "Wheelchair assistance",
    communication_channel: "gds",
    gds_system: "amadeus",
    request_method: "ssr",
    ssr_code: "WCHR",
    osi_required: false,
    oths_required: false,
    passenger_association_required: true,
    segment_association_required: true,
    airline_confirmation_required: true,
    manual_contact_required: false,
    notes: "",
  },
  ssr_osi_templates: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    gds_system: "amadeus",
    template_type: "ssr",
    ssr_code: "WCHR",
    template_text: "SR WCHR {airline} HK1 {passenger_ref} {segment_ref}",
    example_text: "SR WCHR LH HK1 P1 S1",
    required_fields: "passenger_ref, segment_ref",
    max_length: "",
  },
  requirements: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    requirement_type: "passenger_data",
    requirement_code: "pax_assoc",
    requirement_label: "Passenger association",
    mandatory: true,
    applies_to_passenger: true,
    applies_to_segment: false,
    validation_hint: "",
  },
  status_recognition_rules: {
    airline_code: "LH",
    gds_system: "amadeus",
    ssr_code: "WCHR",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    match_type: "contains",
    match_value: "HK",
    recognized_status: "confirmed",
    confidence_score: "0.82",
    priority: "20",
  },
  rejection_patterns: {
    airline_code: "LH",
    gds_system: "amadeus",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    rejection_code: "UN",
    pattern_text: "UNABLE",
    reason_category: "unknown",
    severity: "warning",
    suggested_action: "Contact airline support for manual review.",
  },
  payment_rules: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    payment_required: false,
    fee_included_in_fare: true,
    separate_emd_required: false,
    payment_timing: "not_applicable",
    passenger_association_required: true,
    segment_association_required: true,
    notes: "",
  },
  emd_issuance_rules: {
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    emd_type: "not_required",
    rfic: "",
    rfisc: "",
    service_subcode: "",
    reason_for_issuance_description: "No EMD expected for basic wheelchair assistance.",
    gds_system: "amadeus",
  },
  rfic_rfisc_mappings: {
    airline_code: "LH",
    domain_code: "baggage_special_items",
    family_code: "sports_equipment",
    variant_code: "",
    rfic: "C",
    rfisc: "0DG",
    service_subcode: "0DG",
    commercial_name: "Sports equipment",
    reason_for_issuance_description: "Sports equipment service fee",
    emd_type: "emd_a",
  },
  emd_interline_rules: {
    airline_code: "LH",
    domain_code: "baggage_special_items",
    family_code: "sports_equipment",
    variant_code: "",
    interline_allowed: false,
    plating_carrier_required: "LH",
    validating_carrier_must_equal_operating: false,
    validating_carrier_must_equal_marketing: true,
    partner_airline_restrictions: "manual review required",
    restriction_text: "",
  },
  emd_lifecycle_rules: {
    airline_code: "LH",
    domain_code: "baggage_special_items",
    family_code: "sports_equipment",
    variant_code: "",
    refundable: false,
    exchangeable: false,
    voidable: true,
    reissuable: false,
    refund_conditions: "",
    exchange_conditions: "",
    void_conditions: "Manual mirror only; live void remains disabled.",
    no_show_policy: "",
    residual_value_policy: "",
  },
  candidate_mechanics_links: {
    candidate_type: "extracted_communication",
    candidate_id: "",
    taxonomy_link_id: "",
    mechanics_type: "communication_rule",
    mechanics_record_id: "",
    airline_code: "LH",
    domain_code: "mobility",
    family_code: "wheelchair",
    variant_code: "wchr",
    confidence_score: "0.76",
    evidence_text: "",
  },
}

const fieldSpecs = {
  communication_rules: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["canonical_service_label", "Service label"],
    ["communication_channel", "Channel", "select", ["gds", "ndc", "airline_portal", "email", "phone", "manual", "other"]],
    ["gds_system", "GDS system", "select", ["", "amadeus", "sabre", "travelport", "galileo", "worldspan", "other"]],
    ["request_method", "Request method", "select", ["ssr", "osi", "oths", "remark", "manual_contact", "ndc_service", "other"]],
    ["ssr_code", "SSR code"],
    ["osi_required", "OSI required", "checkbox"],
    ["oths_required", "OTHS required", "checkbox"],
    ["passenger_association_required", "Passenger association", "checkbox"],
    ["segment_association_required", "Segment association", "checkbox"],
    ["airline_confirmation_required", "Airline confirmation", "checkbox"],
    ["manual_contact_required", "Manual contact", "checkbox"],
    ["notes", "Notes", "textarea"],
  ],
  ssr_osi_templates: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["gds_system", "GDS system", "select", ["amadeus", "sabre", "travelport", "galileo", "worldspan", "other"]],
    ["template_type", "Template type", "select", ["ssr", "osi", "oths", "remark", "other"]],
    ["ssr_code", "SSR code"],
    ["template_text", "Template text", "textarea"],
    ["example_text", "Example text"],
    ["required_fields", "Required fields"],
    ["max_length", "Max length", "number"],
  ],
  requirements: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["requirement_type", "Requirement type", "select", ["passenger_data", "segment_data", "document", "medical_form", "age", "contact", "free_text", "approval", "deadline", "other"]],
    ["requirement_code", "Requirement code"],
    ["requirement_label", "Requirement label"],
    ["mandatory", "Mandatory", "checkbox"],
    ["applies_to_passenger", "Applies to passenger", "checkbox"],
    ["applies_to_segment", "Applies to segment", "checkbox"],
    ["validation_hint", "Validation hint", "textarea"],
  ],
  status_recognition_rules: [
    ["airline_code", "Airline code"],
    ["gds_system", "GDS system", "select", ["", "amadeus", "sabre", "travelport", "galileo", "worldspan", "other"]],
    ["ssr_code", "SSR code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["match_type", "Match type", "select", ["exact", "contains", "regex", "token"]],
    ["match_value", "Match value"],
    ["recognized_status", "Recognized status", "select", ["requested", "pending", "confirmed", "rejected", "cancelled", "waitlisted", "unable", "unknown"]],
    ["confidence_score", "Confidence", "number"],
    ["priority", "Priority", "number"],
  ],
  rejection_patterns: [
    ["airline_code", "Airline code"],
    ["gds_system", "GDS system", "select", ["", "amadeus", "sabre", "travelport", "galileo", "worldspan", "other"]],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["rejection_code", "Rejection code"],
    ["pattern_text", "Pattern text"],
    ["reason_category", "Reason", "select", ["age_restriction", "route_restriction", "connection_restriction", "equipment_restriction", "capacity", "documentation", "deadline", "interline", "channel_not_supported", "payment_required", "unknown"]],
    ["severity", "Severity", "select", ["info", "advisory", "warning", "blocker"]],
    ["suggested_action", "Suggested action", "textarea"],
  ],
  payment_rules: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["payment_required", "Payment required", "checkbox"],
    ["fee_included_in_fare", "Fee included in fare", "checkbox"],
    ["separate_emd_required", "Separate EMD required", "checkbox"],
    ["payment_timing", "Payment timing", "select", ["before_ticketing", "after_ticketing", "before_departure", "at_airport", "not_applicable", "unknown"]],
    ["passenger_association_required", "Passenger association", "checkbox"],
    ["segment_association_required", "Segment association", "checkbox"],
    ["notes", "Notes", "textarea"],
  ],
  emd_issuance_rules: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["emd_type", "EMD type", "select", ["emd_a", "emd_s", "unknown", "not_required"]],
    ["rfic", "RFIC"],
    ["rfisc", "RFISC"],
    ["service_subcode", "Service subcode"],
    ["reason_for_issuance_description", "Reason description", "textarea"],
    ["gds_system", "GDS system", "select", ["", "amadeus", "sabre", "travelport", "galileo", "worldspan", "other"]],
  ],
  rfic_rfisc_mappings: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["rfic", "RFIC"],
    ["rfisc", "RFISC"],
    ["service_subcode", "Service subcode"],
    ["commercial_name", "Commercial name"],
    ["reason_for_issuance_description", "Reason description", "textarea"],
    ["emd_type", "EMD type", "select", ["emd_a", "emd_s", "unknown", "not_required"]],
  ],
  emd_interline_rules: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["interline_allowed", "Interline allowed", "checkbox"],
    ["plating_carrier_required", "Plating carrier"],
    ["validating_carrier_must_equal_operating", "Validate equals operating", "checkbox"],
    ["validating_carrier_must_equal_marketing", "Validate equals marketing", "checkbox"],
    ["partner_airline_restrictions", "Partner restrictions"],
    ["restriction_text", "Restriction text", "textarea"],
  ],
  emd_lifecycle_rules: [
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["refundable", "Refundable", "checkbox"],
    ["exchangeable", "Exchangeable", "checkbox"],
    ["voidable", "Voidable", "checkbox"],
    ["reissuable", "Reissuable", "checkbox"],
    ["refund_conditions", "Refund conditions", "textarea"],
    ["exchange_conditions", "Exchange conditions", "textarea"],
    ["void_conditions", "Void conditions", "textarea"],
    ["no_show_policy", "No-show policy", "textarea"],
    ["residual_value_policy", "Residual value", "textarea"],
  ],
  candidate_mechanics_links: [
    ["candidate_type", "Candidate type", "select", ["extracted_rule", "extracted_price", "extracted_communication", "extracted_emd_rule", "extracted_exception", "approved_knowledge"]],
    ["candidate_id", "Candidate id"],
    ["taxonomy_link_id", "Taxonomy link id"],
    ["mechanics_type", "Mechanics type", "select", ["communication_rule", "ssr_osi_template", "requirement", "status_recognition", "rejection_pattern", "payment_rule", "emd_issuance_rule", "rfic_rfisc_mapping", "interline_rule", "lifecycle_rule"]],
    ["mechanics_record_id", "Mechanics record id"],
    ["airline_code", "Airline code"],
    ["domain_code", "Domain code"],
    ["family_code", "Family code"],
    ["variant_code", "Variant code"],
    ["confidence_score", "Confidence", "number"],
    ["evidence_text", "Evidence text", "textarea"],
  ],
}

const numericFields = new Set(["max_length", "confidence_score", "priority"])
const listFields = new Set(["required_fields", "partner_airline_restrictions"])

export default function ServiceMechanicsPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("communication_rules")
  const [forms, setForms] = useState(defaults)
  const [lookupForm, setLookupForm] = useState({ airline_code: "LH", domain_code: "mobility", family_code: "wheelchair", variant_code: "wchr" })
  const [lookupResult, setLookupResult] = useState(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const [platform, mechanicsSummary, taxonomySummary, ...collections] = await Promise.all([
      apiGet("/api/platform/summary"),
      apiGet("/api/platform/service-mechanics/summary"),
      apiGet("/api/platform/service-taxonomy/summary"),
      ...tabs.map((item) => apiGet(item[2])),
    ])
    const collectionState = {}
    tabs.forEach((item, index) => {
      collectionState[item[0]] = collections[index].items || []
    })
    setState({
      user: platform.current_user,
      summary: mechanicsSummary,
      taxonomySummary,
      ...collectionState,
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const active = tabs.find((item) => item[0] === tab) || tabs[0]
  const summaryCards = useMemo(() => [
    ["Communication", state?.summary?.communication_rule_count],
    ["Templates", state?.summary?.ssr_osi_template_count],
    ["Requirements", state?.summary?.ssr_osi_requirement_count],
    ["Payment", state?.summary?.payment_rule_count],
    ["RFIC/RFISC", state?.summary?.rfic_rfisc_mapping_count],
    ["Links", state?.summary?.candidate_mechanics_link_count],
  ], [state])

  async function createRecord(event) {
    event.preventDefault()
    setWorking(`create-${tab}`)
    setError("")
    setMessage("")
    try {
      await apiPost(active[2], cleanPayload(forms[tab]))
      setMessage(`${active[1]} record saved.`)
      setForms((current) => ({ ...current, [tab]: defaults[tab] }))
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function archiveRecord(item) {
    setWorking(item.id)
    setError("")
    try {
      await apiPatch(`${active[2]}/${item.id}`, { status: "archived" })
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
      setLookupResult(await apiPost("/api/platform/service-mechanics/lookup", cleanPayload(lookupForm)))
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  return (
    <PlatformLayout user={state?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Service Mechanics</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">SSR/OSI and EMD Mechanics Mapping</h2>
              <p className="mt-1 text-sm text-slate-600">Platform governs communication rules separately from payment and EMD mechanics.</p>
            </div>
            <span className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700">Provider execution disabled</span>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}
          {state?.taxonomySummary?.domain_count === 0 ? (
            <EmptyState title="No canonical taxonomy records found" body="Service mechanics can be created with explicit codes, but platform taxonomy seed or governance is needed before dropdown-backed selection can be reliable." />
          ) : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {summaryCards.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
            <div className="space-y-4">
              <LookupPanel form={lookupForm} setForm={setLookupForm} result={lookupResult} onSubmit={runLookup} working={working === "lookup"} />
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={createRecord}>
                <h3 className="font-semibold text-slate-950">Create {active[1].toLowerCase()}</h3>
                {(fieldSpecs[tab] || []).map((spec) => (
                  <DynamicField
                    key={spec[0]}
                    spec={spec}
                    value={forms[tab][spec[0]]}
                    onChange={(value) => setForms((current) => ({ ...current, [tab]: { ...current[tab], [spec[0]]: value } }))}
                  />
                ))}
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === `create-${tab}`}>
                  {working === `create-${tab}` ? "Saving..." : "Save record"}
                </button>
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
              <MechanicsTable items={state?.[tab] || []} tab={tab} onArchive={archiveRecord} working={working} />
            </section>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function LookupPanel({ form, setForm, result, onSubmit, working }) {
  return (
    <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={onSubmit}>
      <h3 className="font-semibold text-slate-950">Mechanics lookup</h3>
      <Field label="Airline code" value={form.airline_code} onChange={(value) => setForm({ ...form, airline_code: value.toUpperCase() })} />
      <Field label="Domain code" value={form.domain_code} onChange={(value) => setForm({ ...form, domain_code: value })} />
      <Field label="Family code" value={form.family_code} onChange={(value) => setForm({ ...form, family_code: value })} />
      <Field label="Variant code" value={form.variant_code} onChange={(value) => setForm({ ...form, variant_code: value })} />
      <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working}>{working ? "Looking up..." : "Run lookup"}</button>
      {result ? (
        <div className="space-y-3 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-950">
          <LookupSection title="Communication" groups={result.communication} />
          <LookupSection title="Payment and EMD" groups={result.payment} />
          {result.warnings?.length ? <p className="text-blue-800">{result.warnings.join(" ")}</p> : null}
        </div>
      ) : null}
    </form>
  )
}

function LookupSection({ title, groups }) {
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

function MechanicsTable({ items, tab, onArchive, working }) {
  if (!items.length) {
    return <EmptyState title={`No ${label(tab)}`} body="Create records or connect policy candidates to populate this section." />
  }

  return (
    <div className="divide-y divide-slate-100">
      {items.map((item) => (
        <div className="grid gap-3 p-4 text-sm lg:grid-cols-[220px_minmax(0,1fr)_150px_110px]" key={item.id}>
          <div>
            <p className="font-semibold text-slate-950">{primaryLabel(item)}</p>
            <p className="text-xs text-slate-500">{item.airline_code || item.mechanics_type || "global"} · {label(item.status || item.review_status)}</p>
          </div>
          <div className="min-w-0 text-slate-600">
            <p className="truncate">{taxonomyPath(item)}</p>
            <p className="truncate text-xs">{item.template_text || item.match_value || item.pattern_text || item.reason_for_issuance_description || item.evidence_text || item.notes || "No note"}</p>
          </div>
          <span className="text-slate-600">{item.request_method || item.template_type || item.emd_type || item.payment_timing || formatConfidence(item.confidence_score)}</span>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold disabled:opacity-60" type="button" onClick={() => onArchive(item)} disabled={working === item.id}>
            Archive
          </button>
        </div>
      ))}
    </div>
  )
}

function DynamicField({ spec, value, onChange }) {
  const [name, fieldLabel, type, options] = spec
  if (type === "checkbox") {
    return (
      <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(event.target.checked)} />
        {fieldLabel}
      </label>
    )
  }
  if (type === "select") {
    return <Select label={fieldLabel} value={value ?? ""} options={options} onChange={onChange} />
  }
  if (type === "textarea") {
    return <TextArea label={fieldLabel} value={value ?? ""} onChange={onChange} />
  }
  return <Field label={fieldLabel} value={value ?? ""} type={type === "number" ? "number" : "text"} onChange={name === "airline_code" || name === "ssr_code" || name === "rfic" || name === "rfisc" || name === "service_subcode" ? (next) => onChange(next.toUpperCase()) : onChange} />
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
        {options.map((option) => <option value={option} key={option}>{option ? label(option) : "not set"}</option>)}
      </select>
    </label>
  )
}

function cleanPayload(payload) {
  const clean = { ...payload }
  Object.keys(clean).forEach((key) => {
    if (clean[key] === "") {
      clean[key] = null
    } else if (numericFields.has(key)) {
      clean[key] = clean[key] === null ? null : Number(clean[key])
    } else if (listFields.has(key)) {
      clean[key] = String(clean[key] || "").split(",").map((item) => item.trim()).filter(Boolean)
    }
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
