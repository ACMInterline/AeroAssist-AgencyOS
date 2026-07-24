import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalFacts, PortalPageHeader, PortalRecordList, PortalSection, PortalTimeline, formatDateTime, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalBookingDetailPage({ bookingId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/booking-records/${bookingId}`)])
      .then(([me, detail]) => setState({ me, ...detail }))
      .catch((err) => setError(err.message))
  }, [bookingId])

  const booking = state?.booking || {}
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-8">
          <PortalPageHeader eyebrow="Booking record" title={booking.record_locator || booking.booking_reference || "Booking"} description={booking.airlines?.join(", ") || "Airline details pending"} status={booking.status} backHref="/portal/bookings" backLabel="Back to bookings" />
          <PortalSection title="Booking details">
            <PortalFacts columns={2} rows={[["Record locator", booking.record_locator], ["Airlines", booking.airlines], ["Confirmed", formatDateTime(booking.confirmation_timestamp)], ["Status", titleCase(booking.status)]]} />
          </PortalSection>
          <PortalSection title="Airline locators">
            <CompactRows items={booking.airline_locators} render={(item) => `${item.airline_code || item.carrier || "Airline"} · ${item.record_locator || item.locator || "Locator pending"}`} />
          </PortalSection>
          <div className="grid gap-8 lg:grid-cols-2">
            <PortalSection title="Passengers"><CompactRows items={booking.passengers} render={(item) => item.display_name || item.name || item.passenger_name || "Passenger"} /></PortalSection>
            <PortalSection title="Flight segments"><CompactRows items={booking.segments} render={(item) => `${item.origin_airport_code || item.origin || "TBC"} to ${item.destination_airport_code || item.destination || "TBC"} · ${item.marketing_carrier || item.airline_code || "Airline pending"} ${item.flight_number || ""}`} /></PortalSection>
          </div>
          <PortalSection title="Passenger services"><CompactRows items={asRows(booking.services)} render={(item) => `${item.service_label || item.service_name || item.code || "Service"} · ${titleCase(item.status)}`} /></PortalSection>
          {booking.warnings?.length ? <PortalSection title="Travel warnings"><CompactRows items={booking.warnings} render={(item) => item.summary || "Agency review required"} /></PortalSection> : null}
          <div className="grid gap-8 lg:grid-cols-2">
            <PortalSection title="Tickets">
              <PortalRecordList items={state?.tickets} emptyTitle="No tickets linked" emptyBody="Issued tickets will appear here." href={(item) => `/portal/tickets/${item.id}`}>
                {(item) => <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">{item.ticket_number || "Ticket pending"}</p><p className="text-sm text-slate-600">{item.passenger_name || "Passenger"}</p></div><PortalStatusBadge status={item.status} /></div>}
              </PortalRecordList>
            </PortalSection>
            <PortalSection title="Service documents">
              <PortalRecordList items={state?.emds} emptyTitle="No EMDs linked" emptyBody="Issued service documents will appear here." href={(item) => `/portal/emds/${item.id}`}>
                {(item) => <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">{item.emd_number || "EMD pending"}</p><p className="text-sm text-slate-600">{item.service_name || item.service_code || "Ancillary service"}</p></div><PortalStatusBadge status={item.status} /></div>}
              </PortalRecordList>
            </PortalSection>
          </div>
          <PortalSection title="Documents">
            <PortalRecordList items={state?.documents} emptyTitle="No booking documents" emptyBody="Visible booking documents will appear here." href={(item) => `/portal/documents/${item.id}`}>
              {(item) => <div className="flex flex-wrap items-center justify-between gap-3"><p className="font-semibold text-slate-950">{item.title}</p><PortalStatusBadge status={item.status} /></div>}
            </PortalRecordList>
          </PortalSection>
          <div className="grid gap-8 lg:grid-cols-2">
            <PortalSection title="Booking timeline"><PortalTimeline items={state?.timeline} /></PortalSection>
            <PortalSection title="Messages"><PortalRecordList items={state?.communications} emptyTitle="No booking conversations" emptyBody="Shared booking conversations will appear here." href={(item) => `/portal/communications/${item.id}`}>{(item) => <p className="font-medium text-slate-950">{item.subject || item.title || "Conversation"}</p>}</PortalRecordList></PortalSection>
          </div>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function CompactRows({ items, render }) {
  const rows = asRows(items)
  return rows.length ? <div className="divide-y divide-slate-200 border-y border-slate-200">{rows.map((item, index) => <p className="py-3 text-sm text-slate-700" key={item.id || index}>{render(item)}</p>)}</div> : <p className="text-sm text-slate-500">None visible.</p>
}

function asRows(value) {
  if (Array.isArray(value)) return value
  if (value && typeof value === "object") return Object.entries(value).map(([key, item]) => typeof item === "object" ? { id: key, ...item } : { id: key, code: key, status: item })
  return []
}
