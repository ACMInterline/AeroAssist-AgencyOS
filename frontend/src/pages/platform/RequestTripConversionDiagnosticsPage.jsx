import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
  request_id: "",
  trip_id: "",
  status: "",
}

export default function RequestTripConversionDiagnosticsPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/request-trip-conversion${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      summary: response.summary || {},
      runs: response.recent_runs || [],
      plans: response.recent_plans || [],
      issues: response.recent_issues || [],
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id, filters.request_id, filters.trip_id, filters.status])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])
  const summary = state?.summary || {}

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Request-to-Trip Conversion Diagnostics</h2>
              <p className="mt-1 text-sm text-slate-600">Platform diagnostics for request conversion metadata. This page is read-only and does not convert requests, book trips, issue tickets, call providers, run workers, or override agency staff.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Agency isolated</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            <Metric label="Plans" value={summary.plan_count || 0} />
            <Metric label="Runs" value={summary.run_count || 0} />
            <Metric label="Mappings" value={summary.mapping_count || 0} />
            <Metric label="Warnings" value={summary.warning_count || 0} />
            <Metric label="Critical" value={summary.critical_issue_count || 0} />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Diagnostics filters</h3>
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Request id" value={filters.request_id} onChange={(value) => setFilters({ ...filters, request_id: value })} />
              <Field label="Trip id" value={filters.trip_id} onChange={(value) => setFilters({ ...filters, trip_id: value })} />
              <Field label="Run status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value })} />
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Recent Runs" count={state?.runs?.length || 0}>
              {(state?.runs || []).length ? <RunTable items={state.runs} /> : <EmptyState title="No conversion runs" body="Conversion runs appear after agencies execute or validate conversion metadata." />}
            </Panel>
            <Panel title="Recent Issues" count={state?.issues?.length || 0}>
              {(state?.issues || []).length ? <IssueList items={state.issues} /> : <EmptyState title="No conversion issues" body="Critical validation and warning metadata appears here." />}
            </Panel>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Run Status Counts">
              <Counts value={summary.run_status_counts || {}} />
            </Panel>
            <Panel title="Mapping Type Counts">
              <Counts value={summary.mapping_type_counts || {}} />
            </Panel>
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Panel({ title, count, children }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold text-slate-950">{title}</h3>
        {count !== undefined ? <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{count}</span> : null}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  )
}

function RunTable({ items }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wide text-slate-500">
          <tr><th className="py-2 pr-4">Run</th><th className="py-2 pr-4">Agency</th><th className="py-2 pr-4">Request</th><th className="py-2 pr-4">Trip</th><th className="py-2 pr-4">Status</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr className="border-t border-slate-100" key={item.id}>
              <td className="py-2 pr-4 font-medium text-slate-900">{item.run_reference}</td>
              <td className="py-2 pr-4 text-slate-600">{item.agency_id}</td>
              <td className="py-2 pr-4 text-slate-600">{item.request_id}</td>
              <td className="py-2 pr-4 text-slate-600">{item.trip_id || "Pending"}</td>
              <td className="py-2 pr-4 text-slate-600">{formatType(item.run_status)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function IssueList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm" key={item.id}>
          <p className="font-semibold text-slate-950">{item.title}</p>
          <p className="mt-1 text-xs text-slate-600">{formatType(item.severity)} · {formatType(item.issue_code)}</p>
          <p className="mt-1 text-xs text-slate-500">{item.request_id}</p>
        </div>
      ))}
    </div>
  )
}

function Counts({ value }) {
  const entries = Object.entries(value)
  if (!entries.length) return <EmptyState title="No counts" body="Counts appear after metadata records exist." />
  return (
    <div className="grid gap-2 md:grid-cols-2">
      {entries.map(([key, count]) => (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3" key={key}>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{formatType(key)}</p>
          <p className="mt-1 text-lg font-semibold text-slate-950">{count}</p>
        </div>
      ))}
    </div>
  )
}
