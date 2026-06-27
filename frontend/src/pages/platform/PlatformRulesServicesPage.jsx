import { cloneElement, useEffect, useMemo, useState } from "react"
import ClipboardCheck from "lucide-react/dist/esm/icons/clipboard-check.js"
import Plus from "lucide-react/dist/esm/icons/plus.js"
import Save from "lucide-react/dist/esm/icons/save.js"
import Wand2 from "lucide-react/dist/esm/icons/wand-2.js"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"

const tabs = [
  ["rules", "Airline Rules"],
  ["exceptions", "Exception Rules"],
  ["simulator", "Simulator"],
]

const jsonFields = [
  ["umnr_rules_json", "UMNR"],
  ["prm_rules_json", "PRM"],
  ["medical_rules_json", "Medical"],
  ["pets_service_animals_rules_json", "Pets & Service Animals"],
  ["cargo_oversized_rules_json", "Cargo & Restricted Items"],
  ["vip_protocol_rules_json", "VIP & Corporate"],
]

const emptyRulesForm = {
  airline_id: "",
  iata_code: "",
  general_notes: "",
  governance_status: "draft",
  umnr_rules_json: "{}",
  prm_rules_json: "{}",
  medical_rules_json: "{}",
  pets_service_animals_rules_json: "{}",
  cargo_oversized_rules_json: "{}",
  vip_protocol_rules_json: "{}",
}

const emptyExceptionForm = {
  id: "",
  category: "PRM",
  airline_id: "",
  iata_code: "",
  route_origin: "",
  route_destination: "",
  aircraft_type: "",
  condition_expression: "{}",
  action: "WARN",
  required_documents_json: "[]",
  notes: "",
  priority: 100,
  active: true,
}

const emptySimulationForm = {
  airline_id: "",
  iata_code: "",
  route_origin: "",
  route_destination: "",
  aircraft_type: "",
  service_category: "PRM",
  service_type: "WCHR",
  service_payload_json: "{}",
}

export default function PlatformRulesServicesPage() {
  const [state, setState] = useState(null)
  const [tab, setTab] = useState("rules")
  const [selectedAirlineId, setSelectedAirlineId] = useState("")
  const [rulesForm, setRulesForm] = useState(emptyRulesForm)
  const [exceptionForm, setExceptionForm] = useState(emptyExceptionForm)
  const [simulationForm, setSimulationForm] = useState(emptySimulationForm)
  const [simulation, setSimulation] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  const airlines = state?.airlines || []
  const selectedAirline = useMemo(() => airlines.find((item) => item.airline_id === selectedAirlineId || item.id === selectedAirlineId), [airlines, selectedAirlineId])

  async function load() {
    setError("")
    const [summaryResult, airlinesResult, exceptionResult] = await Promise.allSettled([
      apiGet("/api/platform/summary"),
      apiGet("/api/platform/airline-intelligence/airlines"),
      apiGet("/api/platform/rules-services/exception-rules"),
    ])
    const summary = summaryResult.status === "fulfilled" ? summaryResult.value : {}
    const airlineItems = airlinesResult.status === "fulfilled" ? airlinesResult.value.items || [] : []
    const exceptionItems = exceptionResult.status === "fulfilled" ? exceptionResult.value.items || [] : []
    setState({ summary, airlines: airlineItems, exceptions: exceptionItems })
    const firstAirlineId = selectedAirlineId || airlineItems[0]?.airline_id || airlineItems[0]?.id || ""
    if (firstAirlineId) {
      setSelectedAirlineId(firstAirlineId)
      await loadRules(firstAirlineId)
    }
    const errors = [summaryResult, airlinesResult, exceptionResult].filter((item) => item.status === "rejected").map((item) => item.reason?.message)
    if (errors.length) setError(errors.join(" "))
  }

  async function loadRules(airlineId) {
    if (!airlineId) return
    const result = await apiGet(`/api/platform/rules-services/airlines/${airlineId}/rules`)
    const rules = result.rules || {}
    setRulesForm({
      ...emptyRulesForm,
      airline_id: rules.airline_id || airlineId,
      iata_code: rules.iata_code || result.airline?.iata_code || "",
      general_notes: rules.general_notes || "",
      governance_status: rules.governance_status || "draft",
      ...Object.fromEntries(jsonFields.map(([field]) => [field, JSON.stringify(rules[field] || {}, null, 2)])),
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function parseJson(value, fallback) {
    const trimmed = String(value || "").trim()
    if (!trimmed) return fallback
    return JSON.parse(trimmed)
  }

  function setRulesField(name, value) {
    setRulesForm((current) => ({ ...current, [name]: value }))
  }

  function setExceptionField(name, value) {
    setExceptionForm((current) => ({ ...current, [name]: value }))
  }

  function setSimulationField(name, value) {
    setSimulationForm((current) => ({ ...current, [name]: value }))
  }

  async function chooseAirline(event) {
    const airlineId = event.target.value
    setSelectedAirlineId(airlineId)
    await loadRules(airlineId)
  }

  async function saveRules(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const payload = {
        airline_id: selectedAirlineId,
        iata_code: rulesForm.iata_code,
        general_notes: rulesForm.general_notes,
        governance_status: rulesForm.governance_status,
      }
      jsonFields.forEach(([field]) => {
        payload[field] = parseJson(rulesForm[field], {})
      })
      const result = await apiPut(`/api/platform/rules-services/airlines/${selectedAirlineId}/rules`, payload)
      setMessage(`Saved rules for ${result.rules.iata_code || selectedAirline?.iata_code || selectedAirlineId}.`)
      await loadRules(selectedAirlineId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveException(event) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      const payload = {
        category: exceptionForm.category,
        airline_id: exceptionForm.airline_id || null,
        iata_code: exceptionForm.iata_code || null,
        route_origin: exceptionForm.route_origin || null,
        route_destination: exceptionForm.route_destination || null,
        aircraft_type: exceptionForm.aircraft_type || null,
        condition_expression: parseJson(exceptionForm.condition_expression, {}),
        action: exceptionForm.action,
        required_documents_json: parseJson(exceptionForm.required_documents_json, []),
        notes: exceptionForm.notes || null,
        priority: Number(exceptionForm.priority || 100),
        active: Boolean(exceptionForm.active),
      }
      if (exceptionForm.id) {
        await apiPut(`/api/platform/rules-services/exception-rules/${exceptionForm.id}`, payload)
        setMessage("Exception rule updated.")
      } else {
        await apiPost("/api/platform/rules-services/exception-rules", payload)
        setMessage("Exception rule created.")
      }
      setExceptionForm(emptyExceptionForm)
      const exceptions = await apiGet("/api/platform/rules-services/exception-rules")
      setState((current) => ({ ...current, exceptions: exceptions.items || [] }))
    } catch (err) {
      setError(err.message)
    }
  }

  function editException(rule) {
    setExceptionForm({
      ...emptyExceptionForm,
      ...rule,
      condition_expression: JSON.stringify(rule.condition_expression || {}, null, 2),
      required_documents_json: JSON.stringify(rule.required_documents_json || [], null, 2),
    })
  }

  async function runSimulation(event) {
    event.preventDefault()
    setError("")
    try {
      const result = await apiPost("/api/platform/rules-services/simulate", {
        ...simulationForm,
        service_payload_json: parseJson(simulationForm.service_payload_json, {}),
      })
      setSimulation(result)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <PlatformLayout user={state?.summary?.current_user}>
      <ProtectedRoute loading={!state && !error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Rules & Services</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Rules Foundation</h2>
              <p className="mt-1 text-sm text-slate-600">Platform-owned rules, exceptions, and deterministic service previews.</p>
            </div>
            <div className="inline-flex rounded-md border border-slate-200 bg-white p-1">
              {tabs.map(([value, label]) => (
                <button className={`rounded px-3 py-2 text-sm font-semibold ${tab === value ? "bg-blue-600 text-white" : "text-slate-700"}`} type="button" onClick={() => setTab(value)} key={value}>{label}</button>
              ))}
            </div>
          </div>

          {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div> : null}
          {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{message}</div> : null}

          {tab === "rules" ? (
            <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex flex-wrap items-end gap-3">
                <label className="grid min-w-[260px] flex-1 gap-1 text-sm font-medium text-slate-700">Airline
                  <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={selectedAirlineId} onChange={chooseAirline}>
                    {airlines.map((airline) => <option value={airline.airline_id || airline.id} key={airline.id}>{airline.iata_code || "--"} · {airline.legal_name || airline.airline_profile?.airline_name}</option>)}
                  </select>
                </label>
                <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="button" onClick={saveRules}>
                  <Save className="h-4 w-4" />
                  Save
                </button>
              </div>
              <form className="grid gap-4 lg:grid-cols-2" onSubmit={saveRules}>
                {jsonFields.map(([field, label]) => <JsonArea label={label} value={rulesForm[field]} onChange={(value) => setRulesField(field, value)} key={field} />)}
                <label className="grid gap-1 text-sm font-medium text-slate-700 lg:col-span-2">General Notes
                  <textarea className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={rulesForm.general_notes} onChange={(event) => setRulesField("general_notes", event.target.value)} />
                </label>
                <div className="flex flex-wrap items-center gap-3 lg:col-span-2">
                  <select className="rounded-md border border-slate-300 px-3 py-2 text-sm" value={rulesForm.governance_status} onChange={(event) => setRulesField("governance_status", event.target.value)}>
                    {["draft", "needs_review", "approved", "published", "deprecated", "archived"].map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}
                  </select>
                  <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white" type="submit"><Save className="h-4 w-4" />Save Airline Rules</button>
                </div>
              </form>
            </section>
          ) : null}

          {tab === "exceptions" ? (
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
              <div className="rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-950">Exception Rules</h3>
                {state?.exceptions?.length ? (
                  <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
                    {state.exceptions.map((rule) => (
                      <button className="grid w-full gap-2 p-3 text-left text-sm hover:bg-slate-50 md:grid-cols-[100px_90px_1fr_80px]" type="button" onClick={() => editException(rule)} key={rule.id}>
                        <span className="font-semibold text-slate-950">{rule.category}</span>
                        <span className={rule.action === "BLOCK" ? "font-semibold text-rose-700" : "text-slate-700"}>{rule.action}</span>
                        <span className="text-slate-600">{rule.notes || "No notes"}</span>
                        <span className="text-slate-500">P{rule.priority}</span>
                      </button>
                    ))}
                  </div>
                ) : <EmptyState title="No exception rules" body="Create targeted rules for warnings, documents, blocks, and overrides." />}
              </div>
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveException}>
                <h3 className="font-semibold text-slate-950">{exceptionForm.id ? "Edit Rule" : "Create Rule"}</h3>
                <Field label="Category"><select value={exceptionForm.category} onChange={(event) => setExceptionField("category", event.target.value)}>{["PETS", "SERVICE_ANIMAL", "UMNR", "PRM", "MEDICAL", "CARGO", "VIP", "SEATING", "MEAL", "REFUND", "REBOOK", "GENERAL"].map((value) => <option value={value} key={value}>{value}</option>)}</select></Field>
                <Field label="Action"><select value={exceptionForm.action} onChange={(event) => setExceptionField("action", event.target.value)}>{["ALLOW", "BLOCK", "WARN", "REQUIRE_DOC", "OVERRIDE"].map((value) => <option value={value} key={value}>{value}</option>)}</select></Field>
                <Field label="Airline ID"><input value={exceptionForm.airline_id || ""} onChange={(event) => setExceptionField("airline_id", event.target.value)} /></Field>
                <Field label="IATA"><input value={exceptionForm.iata_code || ""} onChange={(event) => setExceptionField("iata_code", event.target.value.toUpperCase())} /></Field>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Origin"><input value={exceptionForm.route_origin || ""} onChange={(event) => setExceptionField("route_origin", event.target.value.toUpperCase())} /></Field>
                  <Field label="Destination"><input value={exceptionForm.route_destination || ""} onChange={(event) => setExceptionField("route_destination", event.target.value.toUpperCase())} /></Field>
                </div>
                <Field label="Aircraft"><input value={exceptionForm.aircraft_type || ""} onChange={(event) => setExceptionField("aircraft_type", event.target.value.toUpperCase())} /></Field>
                <JsonArea label="Condition Expression" value={exceptionForm.condition_expression} onChange={(value) => setExceptionField("condition_expression", value)} compact />
                <JsonArea label="Required Docs" value={exceptionForm.required_documents_json} onChange={(value) => setExceptionField("required_documents_json", value)} compact />
                <Field label="Notes"><textarea value={exceptionForm.notes || ""} onChange={(event) => setExceptionField("notes", event.target.value)} /></Field>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Priority"><input type="number" value={exceptionForm.priority} onChange={(event) => setExceptionField("priority", event.target.value)} /></Field>
                  <label className="flex items-center gap-2 pt-6 text-sm font-medium text-slate-700"><input type="checkbox" checked={exceptionForm.active !== false} onChange={(event) => setExceptionField("active", event.target.checked)} />Active</label>
                </div>
                <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit"><Plus className="h-4 w-4" />{exceptionForm.id ? "Update Rule" : "Create Rule"}</button>
              </form>
            </section>
          ) : null}

          {tab === "simulator" ? (
            <section className="grid gap-4 lg:grid-cols-[420px_minmax(0,1fr)]">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runSimulation}>
                <h3 className="font-semibold text-slate-950">Simulator</h3>
                <Field label="Airline"><select value={simulationForm.airline_id} onChange={(event) => setSimulationField("airline_id", event.target.value)}><option value="">Manual code</option>{airlines.map((airline) => <option value={airline.airline_id || airline.id} key={airline.id}>{airline.iata_code || "--"} · {airline.legal_name}</option>)}</select></Field>
                <Field label="IATA"><input value={simulationForm.iata_code} onChange={(event) => setSimulationField("iata_code", event.target.value.toUpperCase())} /></Field>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Origin"><input value={simulationForm.route_origin} onChange={(event) => setSimulationField("route_origin", event.target.value.toUpperCase())} /></Field>
                  <Field label="Destination"><input value={simulationForm.route_destination} onChange={(event) => setSimulationField("route_destination", event.target.value.toUpperCase())} /></Field>
                </div>
                <Field label="Aircraft"><input value={simulationForm.aircraft_type} onChange={(event) => setSimulationField("aircraft_type", event.target.value.toUpperCase())} /></Field>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Category"><select value={simulationForm.service_category} onChange={(event) => setSimulationField("service_category", event.target.value)}>{["UMNR", "PRM", "MEDICAL", "PETS", "SERVICE_ANIMAL", "CARGO", "VIP", "SEATING", "MEAL", "GENERAL"].map((value) => <option value={value} key={value}>{value}</option>)}</select></Field>
                  <Field label="Service Type"><input value={simulationForm.service_type} onChange={(event) => setSimulationField("service_type", event.target.value.toUpperCase())} /></Field>
                </div>
                <JsonArea label="Service Payload" value={simulationForm.service_payload_json} onChange={(value) => setSimulationField("service_payload_json", value)} compact />
                <button className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit"><Wand2 className="h-4 w-4" />Run Simulation</button>
              </form>
              <div className="rounded-lg border border-slate-200 bg-white p-5">
                <h3 className="flex items-center gap-2 font-semibold text-slate-950"><ClipboardCheck className="h-4 w-4" />Result</h3>
                {simulation ? <SimulationResult result={simulation} /> : <EmptyState title="No simulation yet" body="Run a service check to preview rules, documents, and SSR/OSI text." />}
              </div>
            </section>
          ) : null}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Field({ label, children }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}{enhanceControl(children)}</label>
}

function enhanceControl(child) {
  return cloneElement(child, { className: `${child.props.className || ""} rounded-md border border-slate-300 px-3 py-2 text-sm font-normal` })
}

function JsonArea({ label, value, onChange, compact = false }) {
  return (
    <label className="grid gap-1 text-sm font-medium text-slate-700">{label}
      <textarea className={`${compact ? "min-h-24" : "min-h-36"} rounded-md border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-xs font-normal text-slate-800`} value={value} onChange={(event) => onChange(event.target.value)} spellCheck="false" />
    </label>
  )
}

function SimulationResult({ result }) {
  return (
    <div className="mt-4 space-y-4 text-sm">
      <div className={`rounded-md border p-3 ${result.blocked ? "border-rose-200 bg-rose-50 text-rose-900" : "border-emerald-200 bg-emerald-50 text-emerald-900"}`}>
        <p className="font-semibold">{result.blocked ? "Blocked" : result.allowed ? "Allowed" : "Manual Review"}</p>
        <p className="mt-1">Confidence {Math.round((result.confidence || 0) * 100)}%</p>
      </div>
      <ResultList title="Warnings" items={result.warnings} />
      <ResultList title="Required Documents" items={(result.required_documents || []).map((item) => item.label || item.code || JSON.stringify(item))} />
      <ResultList title="Rules Fired" items={(result.rules_fired || []).map((item) => `${item.action} · ${item.notes || item.id}`)} />
      <Preview title="SSR Preview" value={result.ssr_preview} />
      <Preview title="OSI Preview" value={result.osi_preview} />
    </div>
  )
}

function ResultList({ title, items }) {
  return <div><h4 className="font-semibold text-slate-950">{title}</h4>{items?.length ? <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700">{items.map((item, index) => <li key={`${title}-${index}`}>{item}</li>)}</ul> : <p className="mt-2 text-slate-500">None</p>}</div>
}

function Preview({ title, value }) {
  return <div><h4 className="font-semibold text-slate-950">{title}</h4><pre className="mt-2 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(value || [], null, 2)}</pre></div>
}
