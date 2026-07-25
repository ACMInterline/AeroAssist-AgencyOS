import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalRecordList, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalAssistancePage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/workspace/dashboard")])
      .then(([me, dashboard]) => setState({ me, items: dashboard.service_requests || [] }))
      .catch((err) => setError(err.message))
  }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><PortalPageHeader eyebrow="Passenger services" title={state?.me?.subject_type === "passenger" ? "My Assistance" : "Service Requests"} description="Assistance and special-service requirements linked to current trips." /><PortalRecordList items={state?.items} emptyTitle="No assistance requests visible" emptyBody="Passenger services will appear after they are linked to a trip.">{(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.5fr)_auto] sm:items-center"><div><p className="font-semibold text-slate-950">{item.service_label || item.service_code || "Passenger service"}</p><p className="mt-1 text-sm text-slate-600">{titleCase(item.service_family)}</p></div><a className="text-sm font-semibold text-blue-700" href={`/portal/trips/${item.trip_id}`}>Open trip</a><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></div></ProtectedRoute></ClientPortalLayout>
}
