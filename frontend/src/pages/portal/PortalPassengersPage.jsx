import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalPassengersPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/passengers")]).then(([me, passengers]) => setState({ me, passengers: passengers.items })).catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <Header title="Passengers" subtitle={state?.me?.subject_type === "passenger" ? "The Passenger profile explicitly linked to this Portal identity." : "Passenger profiles visible through your relationship permissions."} portalLabel={state?.me?.subject_type === "passenger" ? "Passenger portal" : "Client portal"} />
          {!state?.passengers?.length ? <EmptyState title="No passengers visible" body="Your agency controls passenger visibility through relationship permissions." /> : (
            <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
              {state.passengers.map((passenger) => <a className="block p-4 text-sm hover:bg-slate-50" href={`/portal/passengers/${passenger.id}`} key={passenger.id}><span className="font-semibold text-slate-950">{passenger.display_name}</span><span className="ml-2 text-slate-600">{passenger.passenger_type} · {passenger.relationship || "relationship"}</span></a>)}
            </div>
          )}
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Header({ title, subtitle, portalLabel }) {
  return <div><p className="text-sm font-semibold uppercase tracking-wide text-blue-700">{portalLabel}</p><h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2><p className="mt-1 text-sm text-slate-600">{subtitle}</p></div>
}
