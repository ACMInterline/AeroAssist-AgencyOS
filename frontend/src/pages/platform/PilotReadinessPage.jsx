import { useEffect, useMemo, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, SelectField, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet } from "../../lib/api"

const defaultFilters = {
  agency_id: "",
}

export default function PilotReadinessPage() {
  const [state, setState] = useState(null)
  const [filters, setFilters] = useState(defaultFilters)
  const [error, setError] = useState("")

  async function load(nextFilters = filters) {
    const query = queryString(nextFilters)
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/pilot-readiness${query}`),
    ])
    setState({
      me,
      agencies: agencies.items || [],
      summary: response.summary || {},
      moduleReadiness: response.module_readiness || [],
      coverage: response.airline_service_coverage || {},
      profiles: response.profiles || [],
      assessments: response.assessments || [],
      sampleCases: response.sample_cases || [],
      cases: response.golden_path_cases || [],
      runs: response.golden_path_runs || [],
      issues: response.issues || [],
      remediationLinks: response.remediation_links || {},
    })
  }

  useEffect(() => {
    load(filters).catch((err) => setError(err.message))
  }, [filters.agency_id])

  const agencies = state?.agencies || []
  const agencyOptions = useMemo(() => agencies.map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [agencies])
  const summary = state?.summary || {}
  const metrics = [
    ["Latest Score", summary.latest_readiness_score ?? "No run"],
    ["Assessments", summary.assessment_count || 0],
    ["Critical Blockers", summary.critical_blocker_count || 0],
    ["Open Issues", summary.open_issue_count || 0],
    ["Golden Runs", summary.golden_path_run_count || 0],
  ]

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Pilot Stabilization</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Pilot Readiness</h2>
              <p className="mt-1 text-sm text-slate-600">Metadata-only end-to-end readiness diagnostics across knowledge production, passenger service precision, feasibility, recommendations, intelligent offers, and operational follow-up. No production seeding, resets, provider calls, AI, or operational execution.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Deterministic scoring</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-5">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-950">Pilot Scope</h3>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <SelectField label="Agency" value={filters.agency_id} onChange={(value) => setFilters({ ...filters, agency_id: value })} options={agencyOptions} placeholder="All agencies" />
              <Field label="Readiness Status" value={formatType(summary.latest_assessment_status || "No assessment")} onChange={() => {}} disabled />
              <Field label="Golden Templates" value={String(state?.sampleCases?.length || 0)} onChange={() => {}} disabled />
            </div>
          </section>

          <section className="grid gap-3 lg:grid-cols-2">
            <RecordCard title="Airline Service Coverage" value={state?.coverage || {}} />
            <RecordCard title="Status Counts" value={{
              assessments: summary.assessment_status_counts || {},
              checks: summary.check_status_counts || {},
              runs: summary.run_status_counts || {},
              issues: summary.issue_status_counts || {},
            }} />
          </section>

          <section className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-950">Module Readiness</h3>
            <div className="grid gap-3 lg:grid-cols-2">
              {(state?.moduleReadiness || []).map((module) => (
                <div key={module.module_code} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{module.module_name}</p>
                      <p className="mt-1 text-xs text-slate-600">{module.collection}</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{formatType(module.status)}</span>
                  </div>
                  <div className="mt-3 grid gap-2 text-xs text-slate-600 md:grid-cols-3">
                    <p>Records: {module.metadata_record_count}</p>
                    <p>Platform: {module.platform_route}</p>
                    <p>Agency: {module.agency_route}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Latest Assessments" items={state?.assessments || []} empty="No pilot assessments" renderer={(item) => (
              <RecordCard title={item.assessment_reference} value={item.score_section || item} />
            )} />
            <Panel title="Open Issues" items={state?.issues || []} empty="No pilot readiness issues" renderer={(item) => (
              <RecordCard title={item.title || item.issue_reference} value={{
                severity: item.severity,
                status: item.issue_status,
                related_module: item.related_module,
                platform_route: item.remediation_route,
                agency_route: item.agency_remediation_route,
              }} />
            )} />
            <Panel title="Golden-Path Runs" items={state?.runs || []} empty="No golden-path runs" renderer={(item) => (
              <RecordCard title={item.run_reference} value={{
                status: item.run_status,
                readiness_score: item.readiness_score,
                blocking_stage: item.blocking_stage,
                stage_count: item.stage_count,
              }} />
            )} />
            <Panel title="Golden-Path Templates" items={state?.sampleCases || []} empty="No sample templates" renderer={(item) => (
              <RecordCard title={item.case_name} value={{
                case_reference: item.case_reference,
                family: item.case_family,
                scenario_type: item.scenario_type,
                auto_seed_disabled: item.sample_template_auto_seed_disabled,
              }} />
            )} />
          </section>
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}

function Panel({ title, items, empty, renderer }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
      </div>
      {items.length ? <div className="space-y-3">{items.slice(0, 8).map((item) => <div key={item.id || item.case_reference}>{renderer(item)}</div>)}</div> : <EmptyState title={empty} body="Pilot readiness metadata will appear here after diagnostic records are created." />}
    </section>
  )
}
