import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const changeTypeOptions = ["scope", "schedule", "readiness", "approval", "dependency", "risk", "issue", "decision", "documentation", "operational"]
const priorityOptions = ["low", "medium", "high", "urgent"]
const impactOptions = ["low", "medium", "high", "critical"]
const statusOptions = ["draft", "requested", "under_review", "approved", "rejected", "deferred", "superseded", "archived"]

const defaultFilters = {
  rollout_plan_id: "",
  status: "",
  priority: "",
  impact_level: "",
  change_type: "",
}

export default function PlatformFeatureBundleRolloutChangeRequestsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, plans, changeRequests] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/platform/feature-bundle-rollout-plans"),
      apiGet(`/api/platform/feature-bundle-rollout-change-requests${query}`),
    ])
    setState({
      me,
      plans: plans.items || [],
      changeRequests: changeRequests.items || [],
      summary: changeRequests.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.rollout_plan_id, filters.status, filters.priority, filters.impact_level, filters.change_type])

  const planOptions = useMemo(() => {
    return (state?.plans || []).map((plan) => [plan.rollout_plan_id, `${plan.plan_name} · ${plan.agency_name || plan.agency_id}`])
  }, [state?.plans])

  const metrics = [
    ["Change requests", state?.changeRequests?.length || 0],
    ["Urgent", state?.summary?.by_priority?.urgent || 0],
    ["Critical impact", state?.summary?.by_impact_level?.critical || 0],
    ["Related decisions", state?.summary?.related_decision_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Rollout Change Requests</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only rollout change requests. These records do not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, notify users, publish, or switch runtime behavior.</p>
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
            <h3 className="font-semibold text-slate-950">Change request filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <SelectField label="Rollout" value={filters.rollout_plan_id} onChange={(value) => setFilters({ ...filters, rollout_plan_id: value })} options={planOptions} placeholder="All rollouts" />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Priority" value={filters.priority} onChange={(value) => setFilters({ ...filters, priority: value })} options={priorityOptions.map((item) => [item, formatType(item)])} placeholder="All priorities" />
              <SelectField label="Impact level" value={filters.impact_level} onChange={(value) => setFilters({ ...filters, impact_level: value })} options={impactOptions.map((item) => [item, formatType(item)])} placeholder="All impacts" />
              <SelectField label="Change type" value={filters.change_type} onChange={(value) => setFilters({ ...filters, change_type: value })} options={changeTypeOptions.map((item) => [item, formatType(item)])} placeholder="All types" />
            </div>
          </section>

          {state?.changeRequests?.length ? <ChangeRequestList changeRequests={state.changeRequests} /> : <EmptyState title="No rollout change requests" body="Feature bundle rollout change request metadata will appear here after platform records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function ChangeRequestList({ changeRequests }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Change request</th>
            <th className="px-4 py-3">Rollout</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Impact</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Related metadata</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {changeRequests.map((changeRequest) => (
            <tr key={changeRequest.id}>
              <td className="px-4 py-3 align-top">
                <p className="font-medium text-slate-950">{changeRequest.change_title}</p>
                <p className="mt-1 max-w-sm text-xs text-slate-500">{changeRequest.change_reason || changeRequest.change_summary || "No reason recorded"}</p>
              </td>
              <td className="px-4 py-3 align-top text-slate-700">
                <p>{changeRequest.plan_name || changeRequest.rollout_plan_id}</p>
                <p className="mt-1 text-xs text-slate-500">{changeRequest.agency_name || "No agency"}</p>
              </td>
              <td className="px-4 py-3 align-top"><StatusBadge status={changeRequest.change_type} /></td>
              <td className="px-4 py-3 align-top"><StatusBadge status={changeRequest.priority} /></td>
              <td className="px-4 py-3 align-top"><StatusBadge status={changeRequest.impact_level} /></td>
              <td className="px-4 py-3 align-top"><StatusBadge status={changeRequest.change_status} /></td>
              <td className="px-4 py-3 align-top text-xs text-slate-600">
                <ReferenceLine label="Affected bundles" items={changeRequest.affected_bundles?.map((item) => item.bundle_name || item.bundle_id)} />
                <ReferenceLine label="Feature flags" items={changeRequest.affected_feature_flags?.map((item) => item.feature_key || item.feature_flag_id)} />
                <ReferenceLine label="Decisions" items={changeRequest.related_decisions?.map((item) => item.title || item.decision_id)} />
                <ReferenceLine label="Risks" items={changeRequest.related_risks?.map((item) => item.title || item.risk_id)} />
                <ReferenceLine label="Issues" items={changeRequest.related_issues?.map((item) => item.title || item.issue_id)} />
                <ReferenceLine label="Dependencies" items={changeRequest.related_dependencies?.map((item) => item.label || item.dependency_id)} />
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
    approved: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    rejected: "bg-red-50 text-red-700 ring-red-200",
    urgent: "bg-red-50 text-red-700 ring-red-200",
    critical: "bg-red-50 text-red-700 ring-red-200",
    high: "bg-amber-50 text-amber-700 ring-amber-200",
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
