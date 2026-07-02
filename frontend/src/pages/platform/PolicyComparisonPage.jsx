import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPatch, apiPost } from "../../lib/api"

const base = "/api/platform/policy-comparison"

const compareDefaults = {
  airline_codes: "LH, AF",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
  snapshot_name: "Wheelchair policy comparison",
  route_context_json: "{\"direct_vs_connecting\":\"direct\",\"origin_airport\":\"SOF\",\"destination_airport\":\"FRA\"}",
  passenger_context_json: "{\"passenger_type\":\"adult\",\"passenger_age\":34}",
  service_context_json: "{}",
}

const profileDefaults = {
  airline_code: "LH",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
  display_name: "LH mobility wheelchair WCHR",
  notes: "",
}

const viewDefaults = {
  view_name: "Wheelchair operations view",
  airline_codes: "LH, AF",
  domain_code: "mobility",
  family_code: "wheelchair",
  variant_code: "wchr",
  visible_columns: "airline,commercial_name,ssr_osi,confirmation,emd_required,pricing,exceptions,manual_contact,complexity",
}

export default function PolicyComparisonPage() {
  const [state, setState] = useState(null)
  const [compareForm, setCompareForm] = useState(compareDefaults)
  const [profileForm, setProfileForm] = useState(profileDefaults)
  const [viewForm, setViewForm] = useState(viewDefaults)
  const [comparison, setComparison] = useState(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [working, setWorking] = useState("")

  async function load() {
    const [me, summary, profiles, snapshots, savedViews] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet(`${base}/summary`),
      apiGet(`${base}/profiles`),
      apiGet(`${base}/snapshots`),
      apiGet(`${base}/saved-views`),
    ])
    setState({ me, summary, profiles: profiles.items || [], snapshots: snapshots.items || [], savedViews: savedViews.items || [] })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const metrics = useMemo(() => [
    ["Profiles", state?.summary?.comparison_profile_count],
    ["Snapshots", state?.summary?.comparison_snapshot_count],
    ["Rows", state?.summary?.comparison_row_count],
    ["Advisor scenarios", state?.summary?.advisor_scenario_count],
    ["Advisor results", state?.summary?.advisor_result_count],
    ["Saved views", state?.summary?.saved_view_count],
  ], [state])

  async function buildProfile(event) {
    event.preventDefault()
    setWorking("profile")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${base}/build-profile`, cleanPayload(profileForm))
      setMessage(`Profile built for ${result.comparison_profile.airline_code}.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function confirmFirstProfile() {
    const profile = state?.profiles?.[0]
    if (!profile) return
    setWorking("confirm")
    setError("")
    try {
      await apiPatch(`${base}/profiles/${profile.id}`, { review_status: "confirmed" })
      setMessage(`Profile confirmed for ${profile.airline_code}.`)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  async function runCompare(event) {
    event.preventDefault()
    setWorking("compare")
    setError("")
    setMessage("")
    try {
      const result = await apiPost(`${base}/compare`, comparisonPayload(compareForm))
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
      await apiPost(`${base}/saved-views`, savedViewPayload(viewForm))
      setMessage("Saved comparison view created.")
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking("")
    }
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Policy Comparison</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Airline Policy Comparison and Advisor Governance</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only comparison profiles, snapshots, advisor scenarios, and saved views.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700">Recommendations disabled</span>
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{message}</div> : null}

          <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {metrics.map(([label, value]) => <Metric label={label} value={value ?? 0} key={label} />)}
          </section>

          <section className="grid gap-4 xl:grid-cols-[410px_minmax(0,1fr)]">
            <div className="space-y-4">
              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={buildProfile}>
                <h3 className="font-semibold text-slate-950">Profile builder</h3>
                <Field label="Airline code" value={profileForm.airline_code} onChange={(value) => setProfileForm({ ...profileForm, airline_code: value.toUpperCase() })} />
                <Field label="Domain code" value={profileForm.domain_code} onChange={(value) => setProfileForm({ ...profileForm, domain_code: value })} />
                <Field label="Family code" value={profileForm.family_code} onChange={(value) => setProfileForm({ ...profileForm, family_code: value })} />
                <Field label="Variant code" value={profileForm.variant_code} onChange={(value) => setProfileForm({ ...profileForm, variant_code: value })} />
                <Field label="Display name" value={profileForm.display_name} onChange={(value) => setProfileForm({ ...profileForm, display_name: value })} />
                <TextArea label="Notes" value={profileForm.notes} onChange={(value) => setProfileForm({ ...profileForm, notes: value })} />
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60" type="submit" disabled={working === "profile"}>{working === "profile" ? "Building..." : "Build profile"}</button>
                  <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={confirmFirstProfile} disabled={working === "confirm" || !state?.profiles?.length}>Confirm first profile</button>
                </div>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={runCompare}>
                <h3 className="font-semibold text-slate-950">Comparison builder</h3>
                <Field label="Airline codes" value={compareForm.airline_codes} onChange={(value) => setCompareForm({ ...compareForm, airline_codes: value.toUpperCase() })} />
                <Field label="Domain code" value={compareForm.domain_code} onChange={(value) => setCompareForm({ ...compareForm, domain_code: value })} />
                <Field label="Family code" value={compareForm.family_code} onChange={(value) => setCompareForm({ ...compareForm, family_code: value })} />
                <Field label="Variant code" value={compareForm.variant_code} onChange={(value) => setCompareForm({ ...compareForm, variant_code: value })} />
                <Field label="Snapshot name" value={compareForm.snapshot_name} onChange={(value) => setCompareForm({ ...compareForm, snapshot_name: value })} />
                <TextArea label="Route context JSON" value={compareForm.route_context_json} onChange={(value) => setCompareForm({ ...compareForm, route_context_json: value })} />
                <TextArea label="Passenger context JSON" value={compareForm.passenger_context_json} onChange={(value) => setCompareForm({ ...compareForm, passenger_context_json: value })} />
                <TextArea label="Service context JSON" value={compareForm.service_context_json} onChange={(value) => setCompareForm({ ...compareForm, service_context_json: value })} />
                <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60" type="submit" disabled={working === "compare"}>{working === "compare" ? "Comparing..." : "Compare airlines"}</button>
              </form>

              <form className="space-y-3 rounded-lg border border-slate-200 bg-white p-5" onSubmit={saveView}>
                <h3 className="font-semibold text-slate-950">Saved view</h3>
                <Field label="View name" value={viewForm.view_name} onChange={(value) => setViewForm({ ...viewForm, view_name: value })} />
                <Field label="Airline codes" value={viewForm.airline_codes} onChange={(value) => setViewForm({ ...viewForm, airline_codes: value.toUpperCase() })} />
                <Field label="Domain code" value={viewForm.domain_code} onChange={(value) => setViewForm({ ...viewForm, domain_code: value })} />
                <Field label="Family code" value={viewForm.family_code} onChange={(value) => setViewForm({ ...viewForm, family_code: value })} />
                <Field label="Variant code" value={viewForm.variant_code} onChange={(value) => setViewForm({ ...viewForm, variant_code: value })} />
                <TextArea label="Visible columns" value={viewForm.visible_columns} onChange={(value) => setViewForm({ ...viewForm, visible_columns: value })} />
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-60" type="submit" disabled={working === "view"}>{working === "view" ? "Saving..." : "Save view"}</button>
              </form>
            </div>

            <div className="space-y-4">
              <ComparisonTable rows={comparison?.rows || []} />
              <ProfileList items={state?.profiles || []} />
              <SnapshotList items={state?.snapshots || []} />
              <SavedViewList items={state?.savedViews || []} />
            </div>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
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
    is_global: true,
  }
}

function cleanPayload(values) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ""))
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
  if (!rows.length) return <EmptyState title="No comparison rows" body="Run a comparison to generate normalized rows." />
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h3 className="font-semibold text-slate-950">Comparison result</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-[1100px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {["Airline", "Commercial", "Mandatory/Optional", "SSR/OSI", "Confirmation", "EMD", "RFIC/RFISC", "Pricing", "Exceptions", "Manual contact", "Complexity", "Confidence"].map((header) => <th className="px-3 py-2" key={header}>{header}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => (
              <tr key={row.id}>
                <td className="px-3 py-3 font-semibold text-slate-950">{row.airline_code}</td>
                <td className="px-3 py-3">{row.commercial_name || "-"}</td>
                <td className="px-3 py-3">{row.mandatory_optional_summary}</td>
                <td className="px-3 py-3">{row.ssr_osi_summary}</td>
                <td className="px-3 py-3">{row.confirmation_summary}</td>
                <td className="px-3 py-3">{row.emd_required ? "Required" : "Not indicated"} {row.emd_type || ""}</td>
                <td className="px-3 py-3">{[row.rfic, row.rfisc].filter(Boolean).join(" / ") || "-"}</td>
                <td className="px-3 py-3">{row.pricing_summary}</td>
                <td className="px-3 py-3">{row.warning_level}</td>
                <td className="px-3 py-3">{row.manual_contact_required ? "Yes" : "No"}</td>
                <td className="px-3 py-3">{row.operational_complexity_score ?? 0}</td>
                <td className="px-3 py-3">{row.confidence_score ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ProfileList({ items }) {
  return <SimpleList title="Profiles" items={items} fields={["airline_code", "display_name", "review_status", "status"]} />
}

function SnapshotList({ items }) {
  return <SimpleList title="Snapshots" items={items} fields={["snapshot_name", "airline_codes", "generated_from", "created_at"]} />
}

function SavedViewList({ items }) {
  return <SimpleList title="Saved views" items={items} fields={["view_name", "airline_codes", "status", "created_at"]} />
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
