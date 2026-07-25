import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalRecordList, formatDate, formatMoney } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalTicketsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/tickets")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PortalPageHeader eyebrow="Travel documents" title={state?.me?.subject_type === "passenger" ? "My Tickets" : "Tickets"} description="Ticket status, flight coupons, baggage, and servicing history." actions={<a className="secondary-button" href="/portal/emds">View EMDs</a>} />
          <PortalRecordList items={state?.items} emptyTitle="No tickets visible" emptyBody="Issued ticket records linked to your trips will appear here." href={(item) => `/portal/tickets/${item.id}`}>
            {(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.6fr)_auto] sm:items-center"><div><p className="font-semibold text-slate-950">{item.ticket_number || "Ticket pending"}</p><p className="mt-1 text-sm text-slate-600">{item.passenger_name || "Passenger"} · {item.validating_carrier || "Carrier pending"}</p></div><p className="text-sm text-slate-600">{formatDate(item.issue_date)} · {formatMoney(item.total_amount, item.currency)}</p><PortalStatusBadge status={item.status} /></div>}
          </PortalRecordList>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
