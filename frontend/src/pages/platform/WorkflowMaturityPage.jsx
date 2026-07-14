import { useEffect, useMemo, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowMaturityDashboard from "../../components/WorkflowMaturityDashboard"
import PlatformLayout from "../../layouts/PlatformLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function WorkflowMaturityPage() {
  const [state, setState] = useState(null)
  const [agencyId, setAgencyId] = useState("")
  const [error, setError] = useState("")

  async function load(nextAgencyId = agencyId) {
    const query = nextAgencyId ? `?agency_id=${encodeURIComponent(nextAgencyId)}` : ""
    const [me, agencies, response] = await Promise.all([
      apiGet("/api/auth/me"),
      apiGet("/api/agencies"),
      apiGet(`/api/platform/workflow-maturity${query}`),
    ])
    setState({ me, agencies: agencies.items || [], ...response })
  }

  useEffect(() => {
    load(agencyId).catch((err) => setError(err.message))
  }, [agencyId])

  const agencyOptions = useMemo(() => (state?.agencies || []).map((agency) => [agency.id, agency.name || agency.slug || agency.id]), [state?.agencies])

  async function runTest(templateCode) {
    const query = agencyId ? `?agency_id=${encodeURIComponent(agencyId)}` : ""
    return apiPost(`/api/platform/workflow-maturity/test-runs${query}`, { template_code: templateCode })
  }

  return (
    <PlatformLayout user={state?.me?.user}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase text-blue-700">Operations Governance</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Workflow Maturity</h2>
              <p className="mt-1 max-w-4xl text-sm text-slate-600">Epic 54 end-to-end maturity assessment across workflow, queue, SLA, task dependencies, conversion, booking handoff, servicing, command-center visibility, audit, agency isolation, and production safety.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">Consolidation only</span>
          </header>
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <label className="grid max-w-sm gap-1 text-sm font-medium text-slate-700">Agency scope
              <select className="rounded-md border border-slate-300 px-3 py-2 font-normal" value={agencyId} onChange={(event) => setAgencyId(event.target.value)}>
                <option value="">All agencies</option>
                {agencyOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
          </section>
          <WorkflowMaturityDashboard state={state} onRunTest={runTest} />
        </div>
      </ProtectedRoute>
    </PlatformLayout>
  )
}
