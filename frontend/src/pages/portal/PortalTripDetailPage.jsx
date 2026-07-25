import { useEffect, useState } from "react"
import PortalStatusBadge from "../../components/PortalStatusBadge"
import { PortalFacts, PortalPageHeader, PortalRecordList, PortalSection, PortalTimeline, formatDate, titleCase } from "../../components/portal/PortalWorkspace"
import ProtectedRoute from "../../components/ProtectedRoute"
import ClientPortalLayout from "../../layouts/ClientPortalLayout"
import { apiGet } from "../../lib/api"

export default function PortalTripDetailPage({ tripId }) {
  const [state, setState] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([apiGet("/api/portal/me"), apiGet(`/api/portal/trips/${tripId}`)])
      .then(([me, detail]) => setState({ me, ...detail }))
      .catch((err) => setError(err.message))
  }, [tripId])

  const trip = state?.trip || {}
  return (
    <ClientPortalLayout user={{ full_name: state?.me?.portal_account?.display_name }} brand={state?.me?.brand}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-8">
          <PortalPageHeader eyebrow={trip.trip_reference} title={trip.title || "Trip"} description={trip.route_summary || trip.date_summary} status={trip.status} backHref="/portal/trips" backLabel="Back to trips" />

          <PortalSection title="Journey">
            <PortalFacts columns={3} rows={[["Travel dates", trip.date_summary], ["Passengers", trip.passenger_count], ["Segments", trip.segment_count], ["Services", trip.service_count], ["Journey type", titleCase(trip.type)], ["Status", titleCase(trip.status)]]} />
          </PortalSection>

          <PortalSection title="Itinerary">
            <PortalRecordList items={state?.segments} emptyTitle="No itinerary segments" emptyBody="Flight details will appear after the itinerary is confirmed.">
              {(item) => <div className="grid gap-2 sm:grid-cols-[90px_minmax(0,1fr)_minmax(180px,0.7fr)_auto] sm:items-center"><p className="font-semibold text-blue-800">Segment {item.order || ""}</p><div><p className="font-semibold text-slate-950">{item.origin || "TBC"} to {item.destination || "TBC"}</p><p className="text-sm text-slate-600">{item.marketing_airline || item.operating_airline || "Airline pending"} {item.flight_number || ""}</p></div><p className="text-sm text-slate-600">{formatDate(item.departure_date)} {item.departure_time || ""}</p><PortalStatusBadge status={item.status} /></div>}
            </PortalRecordList>
          </PortalSection>

          <PortalSection title="Passengers">
            <PortalRecordList items={state?.passengers} emptyTitle="No passengers visible" emptyBody="Only passengers within your portal access are shown.">
              {(item) => <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">{item.display_name || "Passenger"}</p><p className="mt-1 text-sm text-slate-600">{titleCase(item.passenger_type)} · {item.assistance_summary || "No assistance summary"}</p></div></div>}
            </PortalRecordList>
          </PortalSection>

          <PortalSection title="Passenger services, pets, and special items">
            <div className="grid gap-6 lg:grid-cols-3">
              <SimpleRecords title="Services" items={asRows(state?.services)} label={(item) => item.service_label || item.service_code} detail={(item) => titleCase(item.status)} />
              <SimpleRecords title="Pets" items={asRows(state?.pets)} label={(item) => item.name || item.service_code || "Pet service"} detail={(item) => item.summary || item.status} />
              <SimpleRecords title="Special items" items={asRows(state?.special_items)} label={(item) => item.name || item.item_type || "Special item"} detail={(item) => item.summary || item.status} />
            </div>
          </PortalSection>

          <PortalSection title="Booking and fulfilment">
            <div className="grid gap-6 lg:grid-cols-3">
              <LinkedRecords title="Bookings" items={state?.bookings} href={(item) => `/portal/bookings/${item.id}`} label={(item) => item.record_locator || item.booking_reference || "Booking"} />
              <LinkedRecords title="Tickets" items={state?.tickets} href={(item) => `/portal/tickets/${item.id}`} label={(item) => item.ticket_number || "Ticket"} />
              <LinkedRecords title="EMDs" items={state?.emds} href={(item) => `/portal/emds/${item.id}`} label={(item) => item.emd_number || item.service_name || "Service document"} />
            </div>
          </PortalSection>

          <PortalSection title="Documents">
            <PortalRecordList items={state?.documents} emptyTitle="No trip documents" emptyBody="Visible travel documents will appear here." href={(item) => `/portal/documents/${item.id}`}>
              {(item) => <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-semibold text-slate-950">{item.title}</p><p className="mt-1 text-sm text-slate-600">{titleCase(item.type)}</p></div><PortalStatusBadge status={item.status} /></div>}
            </PortalRecordList>
          </PortalSection>

          <div className="grid gap-8 lg:grid-cols-2">
            <PortalSection title="Journey timeline"><PortalTimeline items={state?.timeline} /></PortalSection>
            <PortalSection title="Messages"><LinkedRecords title="" items={state?.communications} href={(item) => `/portal/communications/${item.id}`} label={(item) => item.subject || item.title || "Conversation"} /></PortalSection>
          </div>
        </div>
      </ProtectedRoute>
    </ClientPortalLayout>
  )
}

function SimpleRecords({ title, items, label, detail }) {
  return <div><h4 className="text-sm font-semibold text-slate-700">{title}</h4><div className="mt-2 space-y-2">{items?.length ? items.map((item, index) => <div className="border-l-2 border-slate-200 pl-3 text-sm" key={item.id || index}><p className="font-medium text-slate-950">{label(item)}</p><p className="text-slate-600">{detail(item) || "Details pending"}</p></div>) : <p className="text-sm text-slate-500">None visible.</p>}</div></div>
}

function LinkedRecords({ title, items, href, label }) {
  return <div>{title ? <h4 className="text-sm font-semibold text-slate-700">{title}</h4> : null}<div className={`${title ? "mt-2" : ""} space-y-2`}>{items?.length ? items.map((item) => <a className="block border-l-2 border-blue-200 pl-3 text-sm font-medium text-blue-700 hover:text-blue-900" href={href(item)} key={item.id}>{label(item)}<span className="block font-normal text-slate-500">{titleCase(item.status)}</span></a>) : <p className="text-sm text-slate-500">None visible.</p>}</div></div>
}

function asRows(value) {
  if (Array.isArray(value)) return value
  return value && typeof value === "object" ? [value] : []
}
