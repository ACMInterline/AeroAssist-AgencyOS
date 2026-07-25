import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalRecordList, formatDate, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalTripsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/trips")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PortalPageHeader eyebrow="Journey records" title={state?.me?.subject_type === "passenger" ? "My Trips" : "Trips"} description="Current itineraries, passenger services, travel documents, and fulfilment status." />
          <PortalRecordList items={state?.items} emptyTitle="No trips visible" emptyBody="Trips will appear after your agency creates the operational journey record." href={(item) => `/portal/trips/${item.id}`}>
            {(item) => (
              <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.5fr)_auto] sm:items-center">
                <div><p className="font-semibold text-slate-950">{item.title || item.trip_reference || "Trip"}</p><p className="mt-1 text-sm text-slate-600">{item.route_summary || "Route pending"}</p></div>
                <p className="text-sm text-slate-600">{item.date_summary || formatDate(item.next_departure)}</p>
                <PortalStatusBadge status={item.status || titleCase(item.type)} />
              </div>
            )}
          </PortalRecordList>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
