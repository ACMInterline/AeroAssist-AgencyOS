import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost } from "../../lib/api"

export default function PortalActionsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  async function load() {
    const me = await apiGet("/api/auth/me")
    const agencies = await apiGet("/api/agencies")
    const agency = agencies.items[0]
    const actions = agency ? await apiGet(`/api/agencies/${agency.id}/portal-actions`) : { items: [] }
    setState({ me, agency, actions: actions.items })
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  async function markProcessed(actionId) {
    setError("")
    try {
      await apiPost(`/api/agencies/${state.agency.id}/portal-actions/${actionId}/process`, { status: "processed" })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error && !state ? error : ""}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agency Workspace</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Portal actions</h2>
          </div>
          {error ? <p className="rounded-md bg-rose-50 p-3 text-sm text-rose-800">{error}</p> : null}
          {!state.actions.length ? <EmptyState title="No portal actions" body="Client-originated actions will appear here for staff review." /> : (
            <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
              {state.actions.map(({ action, client }) => (
                <div className="grid gap-3 p-4 text-sm lg:grid-cols-[170px_1fr_160px_130px]" key={action.id}>
                  <div><p className="font-semibold text-slate-950">{action.action_type.replaceAll("_", " ")}</p><p className="text-slate-500">{client?.display_name || "Client"}</p></div>
                  <p className="text-slate-700">{action.summary}</p>
                  <p className="text-slate-500">{action.status.replaceAll("_", " ")}</p>
                  <button className="rounded-md border border-slate-200 px-3 py-2 text-slate-700 hover:bg-slate-50 disabled:opacity-50" disabled={action.status === "processed"} type="button" onClick={() => markProcessed(action.id)}>Mark processed</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}
