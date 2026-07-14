import { useEffect, useState } from "react"
import ProtectedRoute from "../../components/ProtectedRoute"
import WorkflowMaturityDashboard from "../../components/WorkflowMaturityDashboard"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function WorkflowMaturityPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const response = await apiGet(`/api/agencies/${context.agency.id}/workflow-maturity`)
    setState({ ...context, ...response })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [])

  async function runTest(templateCode) {
    return apiPost(`/api/agencies/${state.agency.id}/workflow-maturity/test-runs`, { template_code: templateCode })
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <header className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase text-blue-700">Operations</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Workflow Maturity</h2>
              <p className="mt-1 max-w-4xl text-sm text-slate-600">End-to-end operational coverage, blockers, remediation links, and isolated golden-path diagnostics. Test runs never create or change production operational records.</p>
            </div>
            <div className="flex gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">Agency isolated</span>
              <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">No production seeding</span>
            </div>
          </header>
          <WorkflowMaturityDashboard state={state} onRunTest={runTest} />
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
