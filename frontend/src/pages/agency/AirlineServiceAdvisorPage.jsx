import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  scenario_name: "Wheelchair direct route advisory",
  airline_codes: "LH, AF",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
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
  requested_service_context_json: "{}",
}

export default function AirlineServiceAdvisorPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [result, setResult] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState(false)

  async function load() {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/policy-comparison`
    const [summary, scenarios, results] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/advisor-scenarios`),
      apiGet(`${base}/advisor-results`),
    ])
    setState({ ...context, base, summary, scenarios: scenarios.items || [], results: results.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Scenarios", state?.summary?.advisor_scenario_count],
    ["Results", state?.summary?.advisor_result_count],
    ["Rows", state?.summary?.comparison_row_count],
    ["Saved views", state?.summary?.saved_view_count],
  ], [state])

  async function evaluate(event) {
    event.preventDefault()
    setWorking(true)
    setError("")
    setMessage("")
    try {
      const response = await apiPost(`${state.base}/advisor-evaluate`, advisorPayload(form))
      setResult(response)
      setMessage(`Advisor evaluated as ${response.result.result_status}.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking(false)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Airline Service Advisor</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Service Advisory Metadata</h2>
              <p className="mt-1 text-sm text-slate-600">This is operational guidance metadata only. It does not book, issue, charge, or contact providers.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">No provider execution</span>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={evaluate}>
              <h3 className="font-semibold text-slate-950">Scenario</h3>
              <Field label="Scenario name" value={form.scenario_name} onChange={(value) => setForm({ ...form, scenario_name: value })} />
              <Field label="Airline codes" value={form.airline_codes} onChange={(value) => setForm({ ...form, airline_codes: value.toUpperCase() })} />
              <Field label="Domain code" value={form.domain_code} onChange={(value) => setForm({ ...form, domain_code: value })} />
              <Field label="Family code" value={form.family_code} onChange={(value) => setForm({ ...form, family_code: value })} />
              <Field label="Variant code" value={form.variant_code} onChange={(value) => setForm({ ...form, variant_code: value })} />
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Passenger age" type="number" value={form.passenger_age} onChange={(value) => setForm({ ...form, passenger_age: value })} />
                <Field label="Passenger type" value={form.passenger_type} onChange={(value) => setForm({ ...form, passenger_type: value })} />
                <Field label="Route type" value={form.route_type} onChange={(value) => setForm({ ...form, route_type: value })} />
                <Field label="Direct/connecting" value={form.direct_vs_connecting} onChange={(value) => setForm({ ...form, direct_vs_connecting: value })} />
                <Field label="Origin airport" value={form.origin_airport} onChange={(value) => setForm({ ...form, origin_airport: value.toUpperCase() })} />
                <Field label="Destination airport" value={form.destination_airport} onChange={(value) => setForm({ ...form, destination_airport: value.toUpperCase() })} />
                <Field label="Origin country" value={form.origin_country} onChange={(value) => setForm({ ...form, origin_country: value.toUpperCase() })} />
                <Field label="Destination country" value={form.destination_country} onChange={(value) => setForm({ ...form, destination_country: value.toUpperCase() })} />
                <Field label="Cabin" value={form.cabin} onChange={(value) => setForm({ ...form, cabin: value })} />
                <Field label="Segments" type="number" value={form.segment_count} onChange={(value) => setForm({ ...form, segment_count: value })} />
                <Field label="Directions" type="number" value={form.direction_count} onChange={(value) => setForm({ ...form, direction_count: value })} />
              </div>
              <TextArea label="Requested service context JSON" value={form.requested_service_context_json} onChange={(value) => setForm({ ...form, requested_service_context_json: value })} />
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working}>{working ? "Evaluating..." : "Evaluate advisor"}</button>
            </form>

            <div className="space-y-4">
              <ResultSummary result={result?.result} />
              <AdvisoryRows rows={result?.advisory_rows || []} />
              <SimpleList title="Recent scenarios" items={state?.scenarios || []} fields={["scenario_name", "airline_codes", "domain_code", "created_at"]} />
              <SimpleList title="Recent results" items={state?.results || []} fields={["result_status", "blocker_count", "warning_count", "created_at"]} />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function advisorPayload(values) {
  return {
    scenario_name: values.scenario_name,
    airline_codes: splitCsv(values.airline_codes),
    domain_code: values.domain_code,
    family_code: values.family_code,
    variant_code: values.variant_code || null,
    passenger_age: optionalNumber(values.passenger_age),
    passenger_type: values.passenger_type || null,
    route_type: values.route_type || null,
    direct_vs_connecting: values.direct_vs_connecting || null,
    origin_airport: values.origin_airport || null,
    destination_airport: values.destination_airport || null,
    origin_country: values.origin_country || null,
    destination_country: values.destination_country || null,
    cabin: values.cabin || null,
    segment_count: optionalNumber(values.segment_count),
    direction_count: optionalNumber(values.direction_count),
    requested_service_context_json: parseJson(values.requested_service_context_json),
  }
}

function optionalNumber(value) {
  if (value === "" || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function splitCsv(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean)
}

function parseJson(value) {
  try {
    return JSON.parse(value || "{}")
  } catch {
    return {}
  }
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function Field({ label, type = "text", value, onChange }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type={type} value={value || ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function TextArea({ label, value, onChange }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <textarea className="mt-1 min-h-20 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function ResultSummary({ result }) {
  if (!result) return <EmptyState title="No advisor result" body="Evaluate a scenario to see operational guidance cards." />
  const cards = [
    ["Status", result.result_status],
    ["Blockers", result.blocker_count],
    ["Warnings", result.warning_count],
    ["Manual contact", result.manual_contact_required_count],
    ["EMD metadata", result.emd_required_count],
    ["Pricing available", result.estimated_price_available_count],
  ]
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="font-semibold text-slate-950">Advisory result</h3>
      <p className="mt-1 text-sm text-slate-600">{result.explanation}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {cards.map(([label, value]) => (
          <div className="rounded-md bg-slate-50 p-3" key={label}>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
            <p className="mt-1 text-lg font-semibold text-slate-950">{value ?? 0}</p>
          </div>
        ))}
      </div>
      {result.operational_warnings?.length ? (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          {result.operational_warnings.join(" ")}
        </div>
      ) : null}
    </div>
  )
}

function AdvisoryRows({ rows }) {
  if (!rows.length) return null
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {rows.map((row) => (
        <div className="rounded-lg border border-slate-200 bg-white p-4" key={row.id}>
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-semibold text-slate-950">{row.airline_code}</h3>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{row.warning_level}</span>
          </div>
          <p className="mt-3 text-sm text-slate-600">{row.ssr_osi_summary}</p>
          <p className="mt-2 text-sm text-slate-600">{row.pricing_summary}</p>
          <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
            <MiniStat label="Complexity" value={row.operational_complexity_score ?? 0} />
            <MiniStat label="EMD" value={row.emd_required ? "Yes" : "No"} />
            <MiniStat label="Contact" value={row.manual_contact_required ? "Yes" : "No"} />
          </div>
        </div>
      ))}
    </div>
  )
}

function MiniStat({ label, value }) {
  return (
    <div className="rounded-md bg-slate-50 p-2">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 font-semibold text-slate-950">{value}</p>
    </div>
  )
}

function SimpleList({ title, items, fields }) {
  if (!items.length) return <EmptyState title={`No ${title.toLowerCase()}`} body="No records found." />
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">{title}</h3>
        <span className="text-sm text-slate-500">{items.length}</span>
      </div>
      <div className="divide-y divide-slate-100">
        {items.slice(0, 6).map((item) => (
          <div className="grid gap-2 p-4 text-sm md:grid-cols-4" key={item.id}>
            {fields.map((field) => <span className="truncate text-slate-700" key={field}>{formatValue(item[field])}</span>)}
          </div>
        ))}
      </div>
    </div>
  )
}

function formatValue(value) {
  if (Array.isArray(value)) return value.join(", ")
  if (typeof value === "string" && value.includes("T")) return new Date(value).toLocaleString()
  return value || "-"
}
