import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import { Field, Metric, RecordCard, formatType, queryString } from "../../components/ClientPassengerMasterRecordList"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

const steps = [
  "Review request",
  "Resolve client/passengers",
  "Review segments",
  "Review services/pets/items",
  "Review offers",
  "Preview generated trip",
  "Execute",
  "Show mapping/results",
]

export default function RequestTripConversionPage() {
  const initialRequestId = new URLSearchParams(window.location.search).get("request_id") || ""
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ request_id: initialRequestId, existing_trip_id: "", idempotency_key: "" })
  const [result, setResult] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/request-trip-conversion${queryString({ request_id: form.request_id })}`)
    setState({ ...context, ...response })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  function payload() {
    return {
      request_id: form.request_id,
      existing_trip_id: form.existing_trip_id || undefined,
      idempotency_key: form.idempotency_key || undefined,
      allow_warnings: true,
      start_workflow: true,
      generate_tasks_deadlines: true,
      metadata: { ui_route: "/agency/request-trip-conversion" },
    }
  }

  async function action(kind) {
    if (!form.request_id) {
      setError("Request id is required.")
      return
    }
    const response = await apiPost(`/api/agencies/${state.agency.id}/request-trip-conversion/${kind}`, payload())
    setResult(response)
    await load()
  }

  const summary = state?.summary || {}
  const validation = result?.validation || result?.preview?.validation || {}
  const mappings = result?.mappings || []
  const issues = result?.issues || [...(validation.critical_issues || []), ...(validation.warnings || [])]
  const runs = state?.recent_runs || []

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Request-to-Trip Conversion</h2>
              <p className="mt-1 text-sm text-slate-600">Production-safe conversion metadata. The request remains the intake/audit origin, the trip becomes the downstream operational shell, and no booking, ticketing, provider call, AI action, worker, or external execution runs here.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Metadata only</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Never request id as trip id</span>
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
            <h3 className="font-semibold text-slate-950">Conversion wizard</h3>
            <div className="mt-4 grid gap-2 md:grid-cols-4">
              {steps.map((step, index) => (
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs" key={step}>
                  <p className="font-semibold text-slate-500">Step {index + 1}</p>
                  <p className="mt-1 text-slate-900">{step}</p>
                </div>
              ))}
            </div>
            <div className="mt-5 grid gap-3 lg:grid-cols-3">
              <Field label="Request id" value={form.request_id} onChange={(value) => setForm({ ...form, request_id: value })} />
              <Field label="Existing trip id" value={form.existing_trip_id} onChange={(value) => setForm({ ...form, existing_trip_id: value })} />
              <Field label="Idempotency key" value={form.idempotency_key} onChange={(value) => setForm({ ...form, idempotency_key: value })} />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => action("preview")}>Preview</button>
              <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => action("validate")}>Validate</button>
              <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={() => action("execute")}>Execute metadata conversion</button>
            </div>
          </section>

          {result ? (
            <section className="grid gap-4 lg:grid-cols-2">
              <Panel title="Preview / Result">
                <RecordCard title="Conversion snapshot" value={{
                  conversion_mode: result.conversion_mode || result.run?.conversion_mode,
                  run_status: result.run?.run_status,
                  trip_id: result.trip?.id || result.run?.trip_id,
                  trip_reference: result.trip?.trip_reference,
                  idempotent_reused: result.idempotent_reused,
                  conversion_blocked: result.conversion_blocked,
                  integrations: result.integrations || result.run?.result_snapshot_json,
                }} />
              </Panel>
              <Panel title="Validation">
                <RecordCard title="Validation summary" value={validation.summary || validation} />
              </Panel>
            </section>
          ) : null}

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Issues" count={issues.length}>
              {issues.length ? <IssueList items={issues} /> : <EmptyState title="No conversion issues" body="Preview and validation warnings appear here." />}
            </Panel>
            <Panel title="Mappings" count={mappings.length || summary.mapping_count || 0}>
              {mappings.length ? <MappingList items={mappings} /> : <EmptyState title="No mappings yet" body="Entity mappings appear after metadata conversion executes." />}
            </Panel>
          </section>

          <Panel title="Recent Runs" count={runs.length}>
            {runs.length ? <RunList items={runs} /> : <EmptyState title="No conversion runs" body="Executed or blocked conversion runs appear here." />}
          </Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
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

function IssueList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm" key={item.id || item.issue_code || index}>
          <p className="font-semibold text-slate-950">{item.title || item.description}</p>
          <p className="mt-1 text-xs text-slate-600">{formatType(item.severity || item.issue_type)} · {formatType(item.issue_code)}</p>
          {item.remediation_guidance ? <p className="mt-2 text-xs text-slate-600">{item.remediation_guidance}</p> : null}
        </div>
      ))}
    </div>
  )
}

function MappingList({ items }) {
  return (
    <div className="space-y-3">
      {items.slice(0, 20).map((item) => (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs" key={item.id}>
          <p className="font-semibold text-slate-950">{formatType(item.mapping_type)}</p>
          <p className="mt-1 text-slate-600">{item.source_entity_type}:{item.source_entity_id} → {item.target_entity_type}:{item.target_entity_id}</p>
          <p className="mt-1 text-slate-500">{formatType(item.mapping_status)}</p>
        </div>
      ))}
    </div>
  )
}

function RunList({ items }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wide text-slate-500">
          <tr><th className="py-2 pr-4">Run</th><th className="py-2 pr-4">Request</th><th className="py-2 pr-4">Trip</th><th className="py-2 pr-4">Status</th><th className="py-2 pr-4">Mappings</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr className="border-t border-slate-100" key={item.id}>
              <td className="py-2 pr-4 font-medium text-slate-900">{item.run_reference}</td>
              <td className="py-2 pr-4 text-slate-600">{item.request_id}</td>
              <td className="py-2 pr-4 text-slate-600">{item.trip_id || "Pending"}</td>
              <td className="py-2 pr-4 text-slate-600">{formatType(item.run_status)}</td>
              <td className="py-2 pr-4 text-slate-600">{item.mapping_count || 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
