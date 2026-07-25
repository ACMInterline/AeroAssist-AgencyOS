import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalRecordList, formatDate, formatMoney } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalEmdsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/emds")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])
  return <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}><ProtectedRoute loading={!state && !error} error={error}><div className="space-y-6"><PortalPageHeader eyebrow="Ancillary services" title="EMDs" description="Issued service documents and their fulfilment status." backHref="/portal/tickets" backLabel="Back to tickets" /><PortalRecordList items={state?.items} emptyTitle="No EMDs visible" emptyBody="Issued service documents will appear here." href={(item) => `/portal/emds/${item.id}`}>{(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.6fr)_auto] sm:items-center"><div><p className="font-semibold text-slate-950">{item.emd_number || "EMD pending"}</p><p className="mt-1 text-sm text-slate-600">{item.service_name || item.service_code || "Ancillary service"} · {item.passenger_name || "Passenger"}</p></div><p className="text-sm text-slate-600">{formatDate(item.issue_date)} · {formatMoney(item.total_amount, item.currency)}</p><PortalStatusBadge status={item.status} /></div>}</PortalRecordList></div></ProtectedRoute></ClientPortalLayout>
}
