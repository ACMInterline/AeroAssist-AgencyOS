import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Metric, RecordCard, formatType } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function PilotReadinessPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [dashboard, checklist] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/pilot-readiness`),
      apiGet(`/api/agencies/${context.agency.id}/pilot-readiness/remediation-checklist`),
    ])
    setState({
      ...context,
      summary: dashboard.summary || {},
      moduleReadiness: dashboard.module_readiness || [],
      coverage: dashboard.airline_service_coverage || {},
      assessments: dashboard.assessments || [],
      runs: dashboard.golden_path_runs || [],
      issues: dashboard.issues || [],
      sampleCases: dashboard.sample_cases || [],
      remediationChecklist: checklist.remediation_checklist || [],
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  const summary = state?.summary || {}
  const metrics = [
    ["Latest Score", summary.latest_readiness_score ?? "No run"],
    ["Status", formatType(summary.latest_assessment_status || "No assessment")],
    ["Open Issues", summary.open_issue_count || 0],
    ["Critical Blockers", summary.critical_blocker_count || 0],
  ]

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Pilot Stabilization</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Pilot Readiness</h2>
              <p className="mt-1 text-sm text-slate-600">Read-only operational diagnostic metadata for pilot readiness. This page does not activate features, execute providers, run AI, seed production data, reset records, or change operational authority.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Read-only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Metadata only</span>
            </div>
          </div>

          {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

          <section className="grid gap-3 md:grid-cols-4">
            {metrics.map(([label, value]) => <Metric label={label} value={value} key={label} />)}
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
            <h3 className="text-lg font-semibold text-slate-950">Remediation Checklist</h3>
            {(state?.remediationChecklist || []).length ? (
              <div className="space-y-3">
                {state.remediationChecklist.map((item) => (
                  <div key={item.item_key} className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-950">{item.label}</p>
                        <p className="mt-1 text-xs text-slate-600">{item.agency_route || item.platform_route || "No route recorded"}</p>
                      </div>
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{formatType(item.severity)} / {formatType(item.status)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No remediation items" body="Open pilot-readiness blockers and warnings will appear here." />}
          </section>

          <section className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-950">Module Readiness</h3>
            <div className="grid gap-3 lg:grid-cols-2">
              {(state?.moduleReadiness || []).map((module) => (
                <div key={module.module_code} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{module.module_name}</p>
                      <p className="mt-1 text-xs text-slate-600">{module.agency_route}</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{formatType(module.status)}</span>
                  </div>
                  <p className="mt-3 text-xs text-slate-600">Metadata records: {module.metadata_record_count}</p>
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
                family: item.case_family,
                scenario_type: item.scenario_type,
                auto_seed_disabled: item.sample_template_auto_seed_disabled,
              }} />
            )} />
          </section>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Panel({ title, items, empty, renderer }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{items.length}</span>
      </div>
      {items.length ? <div className="space-y-3">{items.slice(0, 8).map((item) => <div key={item.id || item.case_reference}>{renderer(item)}</div>)}</div> : <EmptyState title={empty} body="Pilot readiness metadata for this agency will appear here." />}
    </section>
  )
}
