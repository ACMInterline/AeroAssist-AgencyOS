import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const defaults = {
  airline_codes: "LH, AF",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
  snapshot_name: "Agency wheelchair policy comparison",
  route_context_json: "{\"direct_vs_connecting\":\"direct\",\"origin_airport\":\"SOF\",\"destination_airport\":\"FRA\"}",
  passenger_context_json: "{\"passenger_type\":\"adult\",\"passenger_age\":34}",
  service_context_json: "{}",
}

const viewDefaults = {
  view_name: "Agency service comparison view",
  airline_codes: "LH, AF",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
  visible_columns: "airline,ssr_osi,confirmation,emd_required,pricing,manual_contact,complexity",
}

export default function PolicyComparisonPage() {
  const [state, setState] = useState(null)
  const [form, setForm] = useState(defaults)
  const [viewForm, setViewForm] = useState(viewDefaults)
  const [comparison, setComparison] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const base = `/api/agencies/${context.agency.id}/policy-comparison`
    const [summary, profiles, snapshots, savedViews] = await Promise.all([
      apiGet(`${base}/summary`),
      apiGet(`${base}/profiles`),
      apiGet(`${base}/snapshots`),
      apiGet(`${base}/saved-views`),
    ])
    setState({ ...context, base, summary, profiles: profiles.items || [], snapshots: snapshots.items || [], savedViews: savedViews.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Profiles", state?.summary?.comparison_profile_count],
    ["Snapshots", state?.summary?.comparison_snapshot_count],
    ["Rows", state?.summary?.comparison_row_count],
    ["Saved views", state?.summary?.saved_view_count],
  ], [state])

  async function runCompare(event) {
    event.preventDefault()
    setWorking("compare")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${state.base}/compare`, comparisonPayload(form))
      setComparison(result)
      setMessage(`Comparison snapshot created with ${(result.rows || []).length} rows.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function saveView(event) {
    event.preventDefault()
    setWorking("view")
    setError("")
    setMessage("")
    try {
      await apiPost(`${state.base}/saved-views`, savedViewPayload(viewForm))
      setMessage("Agency-local saved view created.")
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
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Policy Comparison</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Policy Comparison</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only global profiles with agency-local comparisons and saved views.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Global mutation blocked</span>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runCompare}>
                <h3 className="font-semibold text-slate-950">Comparison builder</h3>
                <Field label="Airline codes" value={form.airline_codes} onChange={(value) => setForm({ ...form, airline_codes: value.toUpperCase() })} />
                <Field label="Domain code" value={form.domain_code} onChange={(value) => setForm({ ...form, domain_code: value })} />
                <Field label="Family code" value={form.family_code} onChange={(value) => setForm({ ...form, family_code: value })} />
                <Field label="Variant code" value={form.variant_code} onChange={(value) => setForm({ ...form, variant_code: value })} />
                <Field label="Snapshot name" value={form.snapshot_name} onChange={(value) => setForm({ ...form, snapshot_name: value })} />
                <TextArea label="Route context JSON" value={form.route_context_json} onChange={(value) => setForm({ ...form, route_context_json: value })} />
                <TextArea label="Passenger context JSON" value={form.passenger_context_json} onChange={(value) => setForm({ ...form, passenger_context_json: value })} />
                <TextArea label="Service context JSON" value={form.service_context_json} onChange={(value) => setForm({ ...form, service_context_json: value })} />
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "compare"}>{working === "compare" ? "Comparing..." : "Compare airlines"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveView}>
                <h3 className="font-semibold text-slate-950">Saved view</h3>
                <Field label="View name" value={viewForm.view_name} onChange={(value) => setViewForm({ ...viewForm, view_name: value })} />
                <Field label="Airline codes" value={viewForm.airline_codes} onChange={(value) => setViewForm({ ...viewForm, airline_codes: value.toUpperCase() })} />
                <Field label="Domain code" value={viewForm.domain_code} onChange={(value) => setViewForm({ ...viewForm, domain_code: value })} />
                <Field label="Family code" value={viewForm.family_code} onChange={(value) => setViewForm({ ...viewForm, family_code: value })} />
                <Field label="Variant code" value={viewForm.variant_code} onChange={(value) => setViewForm({ ...viewForm, variant_code: value })} />
                <TextArea label="Visible columns" value={viewForm.visible_columns} onChange={(value) => setViewForm({ ...viewForm, visible_columns: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "view"}>{working === "view" ? "Saving..." : "Save agency view"}</button>
              </form>
            </div>

            <div className="space-y-4">
              <ComparisonTable rows={comparison?.rows || []} />
              <SimpleList title="Profiles" items={state?.profiles || []} fields={["airline_code", "display_name", "review_status", "status"]} />
              <SimpleList title="Snapshots" items={state?.snapshots || []} fields={["snapshot_name", "airline_codes", "generated_from", "created_at"]} />
              <SimpleList title="Saved views" items={state?.savedViews || []} fields={["view_name", "airline_codes", "status", "created_at"]} />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function comparisonPayload(values) {
  return {
    snapshot_name: values.snapshot_name,
    airline_codes: splitCsv(values.airline_codes),
    domain_code: values.domain_code,
    family_code: values.family_code,
    variant_code: values.variant_code || null,
    route_context_json: parseJson(values.route_context_json),
    passenger_context_json: parseJson(values.passenger_context_json),
    service_context_json: parseJson(values.service_context_json),
    generated_from: "manual",
  }
}

function savedViewPayload(values) {
  return {
    view_name: values.view_name,
    airline_codes: splitCsv(values.airline_codes),
    domain_code: values.domain_code || null,
    family_code: values.family_code || null,
    variant_code: values.variant_code || null,
    visible_columns: splitCsv(values.visible_columns),
    filters_json: {},
    sort_json: {},
    is_global: false,
  }
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

function Field({ label, value, onChange }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={value || ""} onChange={(event) => onChange(event.target.value)} />
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

function ComparisonTable({ rows }) {
  if (!rows.length) return <EmptyState title="No comparison rows" body="Run a comparison to generate agency-local rows." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Comparison result</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[980px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Airline", "SSR/OSI", "Confirmation", "EMD", "Pricing", "Exceptions", "Manual contact", "Complexity"].map((header) => <th className="px-3 py-2" key={header}>{header}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => (
              <tr key={row.id}>
                <td className="px-3 py-3 font-semibold text-slate-950">{row.airline_code}</td>
                <td className="px-3 py-3">{row.ssr_osi_summary}</td>
                <td className="px-3 py-3">{row.confirmation_summary}</td>
                <td className="px-3 py-3">{row.emd_required ? "Required" : "Not indicated"}</td>
                <td className="px-3 py-3">{row.pricing_summary}</td>
                <td className="px-3 py-3">{row.warning_level}</td>
                <td className="px-3 py-3">{row.manual_contact_required ? "Yes" : "No"}</td>
                <td className="px-3 py-3">{row.operational_complexity_score ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
        {items.slice(0, 8).map((item) => (
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
