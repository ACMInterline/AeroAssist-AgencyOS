import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalActionsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/actions")])
      .then(([me, actions]) => setState({ me, actions: actions.items }))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Client portal</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Actions</h2>
          </div>
          {!state.actions.length ? <EmptyState title="No actions yet" body="Submitted requests, messages, decisions, and acknowledgements will appear here." /> : (
            <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
              {state.actions.map((item) => <div className="grid gap-2 p-4 text-sm md:grid-cols-[180px_1fr_160px]" key={item.id}><span className="font-semibold text-slate-950">{item.action_type.replaceAll("_", " ")}</span><span className="text-slate-700">{item.summary}</span><span className="text-slate-500">{item.status.replaceAll("_", " ")}</span></div>)}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
