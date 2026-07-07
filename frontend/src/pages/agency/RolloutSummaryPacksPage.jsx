import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const statusOptions = ["draft", "assembled", "reviewing", "ready", "archived"]
const audienceOptions = ["platform", "agency", "operations", "compliance", "executive"]

const defaultFilters = {
  rollout_plan_id: "",
  status: "",
  audience: "",
  bundle_id: "",
}

export default function RolloutSummaryPacksPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const context = await loadCurrentAgency()
    const query = queryString(nextFilters)
    const [packs, summary] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-summary-packs${query}`),
      apiGet(`/api/agencies/${context.agency.id}/feature-bundle-rollout-summary-packs/summary`),
    ])
    setState({
      ...context,
      packs: packs.items || [],
      summary: packs.summary || summary.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.rollout_plan_id, filters.status, filters.audience, filters.bundle_id])

  const metrics = [
    ["Summary packs", state?.packs?.length || 0],
    ["Ready", state?.summary?.by_status?.ready || 0],
    ["Agency audience", state?.summary?.by_audience?.agency || 0],
    ["Evidence refs", totalReferences(state?.summary)],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Settings</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Rollout Summary Packs</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only rollout summary evidence-pack metadata. These records do not execute rollouts, activate or deactivate features, enforce access, bill, call providers or external APIs, use AI, send notifications or email, publish, switch runtime behavior, generate PDFs, or export files.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No PDF or export</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Summary pack filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <Field label="Rollout" value={filters.rollout_plan_id} onChange={(value) => setFilters({ ...filters, rollout_plan_id: value })} />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Audience" value={filters.audience} onChange={(value) => setFilters({ ...filters, audience: value })} options={audienceOptions.map((item) => [item, formatType(item)])} placeholder="All audiences" />
              <Field label="Bundle" value={filters.bundle_id} onChange={(value) => setFilters({ ...filters, bundle_id: value })} />
            </div>
          </section>

          {state?.packs?.length ? <SummaryPackList packs={state.packs} /> : <EmptyState title="No rollout summary packs" body="Platform summary evidence-pack metadata will appear here after records are created for this agency." />}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function SummaryPackList({ packs }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Pack</th>
            <th className="px-4 py-3">Rollout</th>
            <th className="px-4 py-3">Audience</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Covered bundles</th>
            <th className="px-4 py-3">Evidence references</th>
            <th className="px-4 py-3">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {packs.map((pack) => (
            <tr key={pack.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{pack.pack_title}</p>
                <p className="mt-1 max-w-sm text-xs text-slate-500">{pack.pack_summary || "No summary recorded"}</p>
                <p className="mt-1 text-xs text-slate-500">Updated: {formatDate(pack.updated_at)}</p>
              </td>
              <td className="px-4 py-3 align-top text-slate-700">
                <p>{pack.plan_name || pack.rollout_plan_id}</p>
                <p className="mt-1 text-xs text-slate-500">{pack.agency_name || "This agency"}</p>
              </td>
              <td className="px-4 py-3 align-top"><StatusBadge status={pack.generated_for_audience} /></td>
              <td className="px-4 py-3 align-top"><StatusBadge status={pack.pack_status} /></td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                {formatList(pack.covered_bundles?.map((item) => item.bundle_name || item.bundle_id) || pack.covered_bundle_ids)}
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Readiness references" items={pack.readiness_references?.map((item) => item.status || item.readiness_id)} />
                <ReferenceLine label="Approval references" items={pack.approval_references?.map((item) => item.status || item.approval_id)} />
                <ReferenceLine label="Schedule references" items={pack.schedule_references?.map((item) => item.rollout_name || item.schedule_id)} />
                <ReferenceLine label="Timeline references" items={pack.timeline_references?.map((item) => item.event_label || item.timeline_entry_id)} />
                <ReferenceLine label="Dependencies" items={pack.dependency_references?.map((item) => item.label || item.dependency_id)} />
                <ReferenceLine label="Risks" items={pack.risk_references?.map((item) => item.title || item.risk_id)} />
                <ReferenceLine label="Issues" items={pack.issue_references?.map((item) => item.title || item.issue_id)} />
                <ReferenceLine label="Decisions" items={pack.decision_references?.map((item) => item.title || item.decision_id)} />
                <ReferenceLine label="Change requests" items={pack.change_request_references?.map((item) => item.title || item.change_request_id)} />
                <ReferenceLine label="Rollback plans" items={pack.rollback_plan_references?.map((item) => item.title || item.rollback_plan_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <p><span className="font-semibold text-slate-700">Evidence notes:</span> {pack.evidence_notes || "None"}</p>
                <p className="mt-2"><span className="font-semibold text-slate-700">Compliance notes:</span> {pack.compliance_notes || "None"}</p>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
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

function Field({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function SelectField({ label, value, onChange, options, placeholder }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <select className="rounded-md border border-slate-300 px-3 py-2" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map(([optionValue, labelText]) => <option value={optionValue} key={optionValue}>{labelText}</option>)}
      </select>
    </label>
  )
}

function ReferenceLine({ label, items }) {
  return <p><span className="font-semibold text-slate-700">{label}:</span> {formatList(items)}</p>
}

function StatusBadge({ status }) {
  const tones = {
    ready: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    assembled: "bg-sky-50 text-sky-700 ring-sky-200",
    reviewing: "bg-amber-50 text-amber-700 ring-amber-200",
    archived: "bg-slate-100 text-slate-600 ring-slate-200",
    compliance: "bg-violet-50 text-violet-700 ring-violet-200",
    executive: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[status] || "bg-blue-50 text-blue-700 ring-blue-200"}`}>{formatType(status)}</span>
}

function queryString(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const text = params.toString()
  return text ? `?${text}` : ""
}

function totalReferences(summary) {
  return [
    "readiness_reference_count",
    "approval_reference_count",
    "schedule_reference_count",
    "timeline_reference_count",
    "dependency_reference_count",
    "risk_reference_count",
    "issue_reference_count",
    "decision_reference_count",
    "change_request_reference_count",
    "rollback_plan_reference_count",
  ].reduce((total, key) => total + (summary?.[key] || 0), 0)
}

function formatList(items) {
  const values = (items || []).filter(Boolean)
  return values.length ? values.join(", ") : "None"
}

function formatType(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "Unknown"
}
