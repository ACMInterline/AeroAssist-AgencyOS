import { useEffect, useState } from "react"
import BookingStatusBadge from "../../components/BookingStatusBadge"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalBookingDetailPage({ bookingId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")
  useEffect(() => { Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/bookings/${bookingId}`)]).then(([me, detail]) => setState({ me, ...detail })).catch((err) => setError(err.message)) }, [bookingId])
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><a className="text-sm font-medium text-blue-700" href="/portal/bookings">Back to bookings</a><p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state.booking.booking_reference}</p><h2 className="text-2xl font-semibold text-slate-950">PNR {state.booking.pnr || "not set"}</h2></div><BookingStatusBadge status={state.booking.status} /></div>
          <section className="grid gap-4 md:grid-cols-3"><Info title="Overview" rows={[["Channel", state.booking.booking_channel], ["Carrier", state.booking.validating_airline_code], ["Total", `${state.booking.total_amount} ${state.booking.currency}`], ["Due", `${state.booking.amount_due} ${state.booking.currency}`]]} /><Info title="Notes" rows={[["Client-visible notes", state.booking.client_visible_notes]]} /><Info title="Counts" rows={[["Passengers", state.passengers.length], ["Segments", state.segments.length], ["Tickets", state.tickets.length], ["EMDs", state.emds.length]]} /></section>
          <Panel title="Passengers"><Rows items={state.passengers} render={(item) => `${item.snapshot_display_name} · ${item.snapshot_passenger_type} · ${item.ticket_status}`} /></Panel>
          <Panel title="Segments"><Rows items={state.segments} render={(item) => `${item.marketing_airline_code}${item.flight_number || ""} ${item.origin_airport_code}-${item.destination_airport_code} · ${item.segment_status}`} /></Panel>
          <Panel title="Tickets"><Rows items={state.tickets} render={(item) => `${item.ticket_number} · ${item.validating_airline_code} · ${item.status} · ${item.total_amount} ${item.currency}`} /></Panel>
          <Panel title="EMDs"><Rows items={state.emds} render={(item) => `${item.emd_number} · ${item.service_code} ${item.service_name} · ${item.status}`} /></Panel>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function Panel({ title, children }) { return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section> }
function Rows({ items, render }) { return <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200">{items.length ? items.map((item) => <div className="p-3 text-sm text-slate-700" key={item.id}>{render(item)}</div>) : <div className="p-3 text-sm text-slate-500">No visible records.</div>}</div> }
function Info({ title, rows }) { return <section className="rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3><dl className="mt-4 space-y-3 text-sm">{rows.map(([label, value]) => <div key={label}><dt className="font-medium text-slate-700">{label}</dt><dd className="mt-1 text-slate-600">{value || "Not set"}</dd></div>)}</dl></section> }
