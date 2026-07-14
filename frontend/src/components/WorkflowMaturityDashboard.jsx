import { useState } from "react"
import EmptyState from "./EmptyState"

export default function WorkflowMaturityDashboard({ state, onRunTest }) {
  const [running, setRunning] = useState("")
  const [runResult, setRunResult] = useState(null)
  const [runError, setRunError] = useState("")
  const assessment = state?.assessment || {}
  const coverage = state?.operational_coverage || {}

  async function run(templateCode) {
    setRunning(templateCode)
    setRunError("")
    try {
      setRunResult(await onRunTest(templateCode))
    } catch (error) {
      setRunError(error.message)
    } finally {
      setRunning("")
    }
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-3 md:grid-cols-4">
        <Metric label="Maturity score" value={`${state?.maturity_score ?? 0}%`} />
        <Metric label="Status" value={formatType(state?.maturity_status)} />
        <Metric label="Critical blockers" value={assessment.critical_blocker_count || 0} />
        <Metric label="Operational stages" value={`${coverage.covered_stage_count || 0}/${coverage.total_stage_count || 0}`} />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-semibold text-slate-950">Maturity dimensions</h3>
            <p className="mt-1 text-sm text-slate-600">Deterministic scores across canonical Epic 54 contracts and linkage invariants.</p>
          </div>
          <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Deterministic assessment</span>
        </div>
        <Table
          rows={state?.module_scores || []}
          columns={[
            ["label", "Dimension"],
            ["score", "Score"],
            ["status", "Status"],
            ["observed_record_count", "Records"],
          ]}
        />
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="font-semibold text-slate-950">Canonical golden path</h3>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {(state?.golden_path_stages || []).map((stage, index) => (
            <div className="flex min-h-14 items-center gap-3 rounded-md border border-slate-200 px-3 py-2 text-sm" key={stage}>
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-700">{index + 1}</span>
              <span className="font-medium text-slate-800">{formatType(stage)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-semibold text-slate-950">Isolated golden-path diagnostics</h3>
            <p className="mt-1 text-sm text-slate-600">Runs are not persisted and never create production requests, trips, offers, bookings, tickets, EMDs, or after-sales cases.</p>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">Production records disabled</span>
        </div>
        {runError ? <p className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{runError}</p> : null}
        <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">
          {(state?.test_templates || []).map((template) => (
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3" key={template.template_code}>
              <div>
                <p className="text-sm font-semibold text-slate-950">{template.name}</p>
                <p className="mt-1 text-xs text-slate-500">{formatType(template.family)} · Expected {formatType(template.expected_status)}</p>
              </div>
              <button className="rounded-md border border-blue-600 px-3 py-2 text-sm font-semibold text-blue-700 disabled:opacity-50" disabled={Boolean(running)} onClick={() => run(template.template_code)} type="button">
                {running === template.template_code ? "Running..." : "Run diagnostic"}
              </button>
            </div>
          ))}
        </div>
      </section>

      {runResult?.test_run ? <TestRun result={runResult.test_run} /> : null}

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h3 className="font-semibold text-slate-950">Blocker register</h3>
          {!state?.blocker_register?.length ? <EmptyState title="No blockers" body="No maturity or operational blockers are visible for this scope." /> : (
            <div className="mt-4 divide-y divide-slate-100">
              {state.blocker_register.map((blocker) => (
                <a className="block py-3 text-sm" href={state.platform_governance ? blocker.platform_route : blocker.agency_route} key={blocker.blocker_code}>
                  <span className="font-semibold text-slate-950">{blocker.title}</span>
                  <span className="ml-2 text-xs font-semibold uppercase text-amber-700">{blocker.severity}</span>
                  <span className="mt-1 block text-slate-600">{formatValue(blocker.summary)}</span>
                </a>
              ))}
            </div>
          )}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h3 className="font-semibold text-slate-950">Recent workflow errors</h3>
          {!state?.recent_workflow_errors?.length ? <EmptyState title="No recent errors" body="Blocked or failed workflow diagnostics will appear here." /> : (
            <Table rows={state.recent_workflow_errors} columns={[["source", "Source"], ["status", "Status"], ["summary", "Summary"]]} />
          )}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="font-semibold text-slate-950">Operational coverage</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <Metric label="Workflow linkage" value={`${coverage.workflow_linkage_rate || 0}%`} />
          <Metric label="Work-item source linkage" value={`${coverage.work_item_source_linkage_rate || 0}%`} />
          <Metric label="Deadline queue/workflow linkage" value={`${coverage.deadline_workflow_or_queue_linkage_rate || 0}%`} />
        </div>
      </section>
    </div>
  )
}

function TestRun({ result }) {
  return (
    <section className="rounded-lg border border-blue-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-950">Diagnostic result</h3>
          <p className="mt-1 text-sm text-slate-600">{result.run_reference}</p>
        </div>
        <div className="flex gap-2">
          <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">{formatType(result.final_status)}</span>
          <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Not persisted</span>
        </div>
      </div>
      <Table rows={result.stage_results || []} columns={[["sequence", "#"], ["stage_label", "Stage"], ["status", "Status"], ["summary", "Result"]]} />
      <p className="mt-4 text-sm text-slate-600">Client and internal messages are stored as separate response fields. No source record was created.</p>
    </section>
  )
}

function Table({ rows, columns }) {
  if (!rows?.length) return <EmptyState title="No records" body="No metadata is available for this view." />
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead><tr className="border-b border-slate-100 text-xs uppercase text-slate-500">{columns.map(([, label]) => <th className="px-3 py-2" key={label}>{label}</th>)}</tr></thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row, index) => (
            <tr key={row.id || row.dimension || row.stage_code || `${row.source}-${index}`}>
              {columns.map(([key]) => <td className="max-w-xl px-3 py-2 text-slate-700" key={key}>{formatValue(row[key])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-slate-950">{value}</p></div>
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  if (Array.isArray(value)) return value.map(formatType).join(", ") || "None"
  if (typeof value === "object") return value.summary || JSON.stringify(value)
  return formatType(value)
}

function formatType(value) {
  if (value === null || value === undefined || value === "") return "Not set"
  return String(value).replaceAll("_", " ")
}
