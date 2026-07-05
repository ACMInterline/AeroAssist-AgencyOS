import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const impactOptions = ["low", "medium", "high", "critical"]
const likelihoodOptions = ["rare", "unlikely", "possible", "likely", "almost_certain"]
const statusOptions = ["open", "reviewing", "mitigating", "mitigated", "accepted", "closed"]

const defaultFilters = {
  agency_id: "",
  bundle_id: "",
  rollout_plan_id: "",
  status: "",
  impact: "",
  likelihood: "",
}

export default function PlatformFeatureBundleRolloutRisksPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, plans, risks] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/platform/feature-bundle-rollout-plans"),
      apiGet(`/api/platform/feature-bundle-rollout-risks${query}`),
    ])
    setState({
      me,
      plans: plans.items || [],
      risks: risks.items || [],
      summary: risks.summary || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.bundle_id, filters.rollout_plan_id, filters.status, filters.impact, filters.likelihood])

  const options = useMemo(() => {
    const plans = state?.plans || []
    return {
      agencies: uniqueOptions(plans, "agency_id", "agency_name"),
      bundles: uniqueOptions(plans, "bundle_id", "bundle_name"),
      plans: plans.map((plan) => [plan.rollout_plan_id, `${plan.plan_name} · ${plan.agency_name || plan.agency_id}`]),
    }
  }, [state?.plans])

  const byImpact = state?.summary?.by_impact || {}
  const metrics = [
    ["Risks", state?.risks?.length || 0],
    ["High", byImpact.high || 0],
    ["Critical", byImpact.critical || 0],
    ["Plans", state?.summary?.plan_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Feature Flags</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Feature Bundle Rollout Risks</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only rollout risk register. These records do not execute rollouts, enforce risk decisions, block anything, send notifications, activate bundles, add automation, or call external providers.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No enforcement</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No blocking</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Risk filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-6">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={options.agencies} placeholder="All agencies" />
              <SelectField label="Bundle" value={filters.bundle_id} onChange={(value) => setFilters({ ...filters, bundle_id: value })} options={options.bundles} placeholder="All bundles" />
              <SelectField label="Plan" value={filters.rollout_plan_id} onChange={(value) => setFilters({ ...filters, rollout_plan_id: value })} options={options.plans} placeholder="All plans" />
              <SelectField label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} options={statusOptions.map((item) => [item, formatType(item)])} placeholder="All statuses" />
              <SelectField label="Impact" value={filters.impact} onChange={(value) => setFilters({ ...filters, impact: value })} options={impactOptions.map((item) => [item, formatType(item)])} placeholder="All impacts" />
              <SelectField label="Likelihood" value={filters.likelihood} onChange={(value) => setFilters({ ...filters, likelihood: value })} options={likelihoodOptions.map((item) => [item, formatType(item)])} placeholder="All likelihoods" />
            </div>
          </section>

          {state?.risks?.length ? <RiskTable risks={state.risks} /> : <EmptyState title="No rollout risks" body="Feature bundle rollout risk metadata will appear here after platform records are created." />}
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function RiskTable({ risks }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3">Risk</th>
            <th className="px-4 py-3">Bundle</th>
            <th className="px-4 py-3">Plan</th>
            <th className="px-4 py-3">Impact</th>
            <th className="px-4 py-3">Likelihood</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Mitigation</th>
            <th className="px-4 py-3">Owner</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {risks.map((risk) => (
            <tr key={risk.risk_id}>
              <td className="px-4 py-3">
                <p className="font-medium text-slate-950">{risk.title}</p>
                <p className="mt-1 max-w-xs text-xs text-slate-500">{risk.description || "No description"}</p>
              </td>
              <td className="px-4 py-3 text-slate-700">{risk.bundle_name || risk.bundle_id || "No bundle"}</td>
              <td className="px-4 py-3 text-slate-700">{risk.plan_name || risk.rollout_plan_id || "No plan"}</td>
              <td className="px-4 py-3"><StatusBadge status={risk.impact} toneType="impact" /></td>
              <td className="px-4 py-3 text-slate-700">{formatType(risk.likelihood)}</td>
              <td className="px-4 py-3"><StatusBadge status={risk.status} toneType="status" /></td>
              <td className="px-4 py-3 text-slate-600">{risk.mitigation_notes || "No mitigation notes"}</td>
              <td className="px-4 py-3 text-slate-700">{risk.owner || "Unassigned"}</td>
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

function StatusBadge({ status, toneType }) {
  const statusTones = {
    mitigated: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    accepted: "bg-sky-50 text-sky-700 ring-sky-200",
    closed: "bg-slate-100 text-slate-600 ring-slate-200",
    deleted: "bg-slate-100 text-slate-600 ring-slate-200",
  }
  const impactTones = {
    low: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    medium: "bg-blue-50 text-blue-700 ring-blue-200",
    high: "bg-amber-50 text-amber-700 ring-amber-200",
    critical: "bg-red-50 text-red-700 ring-red-200",
  }
  const tones = toneType === "impact" ? impactTones : statusTones
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

function uniqueOptions(items, idKey, labelKey) {
  const seen = new Map()
  items.forEach((item) => {
    if (item[idKey] && !seen.has(item[idKey])) seen.set(item[idKey], item[labelKey] || item[idKey])
  })
  return Array.from(seen.entries())
}

function formatType(value) {
  return String(value || "Unknown").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase())
}
