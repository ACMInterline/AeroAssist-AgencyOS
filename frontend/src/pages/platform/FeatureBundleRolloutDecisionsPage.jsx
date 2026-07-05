import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const categoryOptions = ["readiness", "approval", "schedule", "dependency", "risk", "issue", "rollout_scope", "operational", "governance"]
const statusOptions = ["draft", "proposed", "accepted", "deferred", "rejected", "superseded", "archived"]

const defaultFilters = {
  rollout_plan_id: "",
  category: "",
  owner: "",
  status: "",
}

export default function PlatformFeatureBundleRolloutDecisionsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, plans, decisions] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/platform/feature-bundle-rollout-plans"),
      apiGet(`/api/platform/feature-bundle-rollout-decisions${query}`),
    ])
    setState({
      me,
      plans: plans.items || [],
      decisions: decisions.items || [],
      summary: decisions.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.rollout_plan_id, filters.category, filters.owner, filters.status])

  const planOptions = useMemo(() => {
    return (state?.plans || []).map((plan) => [plan.rollout_plan_id, `${plan.plan_name} · ${plan.agency_name || plan.agency_id}`])
  }, [state?.plans])

  const metrics = [
    ["Decisions", state?.decisions?.length || 0],
    ["Accepted", state?.summary?.by_status?.accepted || 0],
    ["Deferred", state?.summary?.by_status?.deferred || 0],
    ["Related issues", state?.summary?.related_issue_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Rollout Decisions</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only decision register. These records do not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, notify users, publish, or switch runtime behavior.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Read-only UI</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No activation</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Decision filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Rollout" value={filters.rollout_plan_id} onChange={(value) => setFilters({ ...filters, rollout_plan_id: value })} options={planOptions} placeholder="All rollouts" />
              <SelectField label="Category" value={filters.category} onChange={(value) => setFilters({ ...filters, category: value })} options={categoryOptions.map((item) => [item, formatType(item)])} placeholder="All categories" />
              <Field label="Owner" value={filters.owner} onChange={(value) => setFilters({ ...filters, owner: value })} />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
            </div>
          </section>

          {state?.decisions?.length ? <DecisionList decisions={state.decisions} /> : <EmptyState title="No rollout decisions" body="Feature bundle rollout decision metadata will appear here after platform records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function DecisionList({ decisions }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Decision</th>
            <th className="px-4 py-3">Rollout</th>
            <th className="px-4 py-3">Category</th>
            <th className="px-4 py-3">Owner</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Related metadata</th>
            <th className="px-4 py-3">Timeline references</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {decisions.map((decision) => (
            <tr key={decision.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{decision.decision_title}</p>
                <p className="mt-1 max-w-sm text-xs text-slate-500">{decision.decision_reason || decision.decision_summary || "No reason recorded"}</p>
              </td>
              <td className="px-4 py-3 align-top text-slate-700">
                <p>{decision.plan_name || decision.rollout_plan_id}</p>
                <p className="mt-1 text-xs text-slate-500">{decision.agency_name || "No agency"}</p>
              </td>
              <td className="px-4 py-3 align-top"><StatusBadge status={decision.decision_category} /></td>
              <td className="px-4 py-3 align-top text-slate-700">{decision.decision_owner || "Unassigned"}</td>
              <td className="px-4 py-3 align-top"><StatusBadge status={decision.decision_status} /></td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Bundles" items={decision.related_bundles?.map((item) => item.bundle_name || item.bundle_id)} />
                <ReferenceLine label="Risks" items={decision.related_risks?.map((item) => item.title || item.risk_id)} />
                <ReferenceLine label="Issues" items={decision.related_issues?.map((item) => item.title || item.issue_id)} />
                <ReferenceLine label="Dependencies" items={decision.related_dependencies?.map((item) => item.label || item.dependency_id)} />
              </td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">{formatList(decision.timeline_references?.map((item) => item.event_type || item.entry_id))}</td>
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
    accepted: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    rejected: "bg-red-50 text-red-700 ring-red-200",
    deferred: "bg-amber-50 text-amber-700 ring-amber-200",
    archived: "bg-slate-100 text-slate-600 ring-slate-200",
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

function formatList(items) {
  const values = (items || []).filter(Boolean)
  return values.length ? values.join(", ") : "None"
}

function formatType(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}
