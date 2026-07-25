import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalPageHeader, PortalRecordList, formatDateTime } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalBookingsPage() {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet("/api/portal/booking-records")])
      .then(([me, data]) => setState({ me, items: data.items || [] }))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <PortalPageHeader eyebrow="Travel fulfilment" title="Bookings" description="Airline record locators, fulfilment status, services, and travel warnings." />
          <PortalRecordList items={state?.items} emptyTitle="No bookings visible" emptyBody="Booking records will appear after an accepted offer is handed to agency operations." href={(item) => `/portal/bookings/${item.id}`}>
            {(item) => <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.5fr)_auto] sm:items-center"><div><p className="font-semibold text-slate-950">{item.record_locator || item.booking_reference || "Booking pending"}</p><p className="mt-1 text-sm text-slate-600">{item.airlines?.join(", ") || "Airline pending"}</p></div><p className="text-sm text-slate-600">{formatDateTime(item.confirmation_timestamp || item.updated_at)}</p><PortalStatusBadge status={item.status} /></div>}
          </PortalRecordList>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}
