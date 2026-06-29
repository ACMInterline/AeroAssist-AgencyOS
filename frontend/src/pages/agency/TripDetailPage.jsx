import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function TripDetailPage({ tripId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ trip_title: "", trip_status: "draft", trip_type: "unknown", operational_summary: "", internal_notes: "", client_visible_notes: "", link_request_id: "" })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [detail, requests, acceptedOffer, bookingReadiness, bookingWorkspaces, tickets, emds] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}`),
      apiGet(`/api/agencies/${context.agency.id}/requests`),
      apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}/accepted-offer`),
      apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}/booking-readiness`),
      apiGet(`/api/agencies/${context.agency.id}/booking-workspaces?trip_id=${encodeURIComponent(tripId)}`),
      apiGet(`/api/agencies/${context.agency.id}/tickets?trip_id=${encodeURIComponent(tripId)}`),
      apiGet(`/api/agencies/${context.agency.id}/emds?trip_id=${encodeURIComponent(tripId)}`),
    ])
    const bookingRecordId = bookingWorkspaces.items?.[0]?.booking_record?.id
    const ticketEmdReadiness = bookingRecordId
      ? await apiGet(`/api/agencies/${context.agency.id}/booking-records/${bookingRecordId}/ticket-emd-readiness`)
      : null
    setState({ ...context, ...detail, requests: requests.items, acceptedOffer, bookingReadiness, bookingWorkspaces: bookingWorkspaces.items || [], tickets: tickets.items || [], emds: emds.items || [], ticketEmdReadiness })
    setForm({
      trip_title: detail.trip.trip_title || "",
      trip_status: detail.trip.trip_status || "draft",
      trip_type: detail.trip.trip_type || "unknown",
      operational_summary: detail.trip.operational_summary || "",
      internal_notes: detail.trip.internal_notes || "",
      client_visible_notes: detail.trip.client_visible_notes || "",
      link_request_id: "",
    })
  }

  useEffect(() => {
    load().catch((err) => setError(err.message))
  }, [tripId])

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function save(event) {
    event.preventDefault()
    await apiPut(`/api/agencies/${state.agency.id}/trips/${tripId}`, {
      trip_title: form.trip_title,
      trip_status: form.trip_status,
      trip_type: form.trip_type,
      operational_summary: form.operational_summary,
      internal_notes: form.internal_notes,
      client_visible_notes: form.client_visible_notes,
    })
    await load()
  }

  async function linkRequest(event) {
    event.preventDefault()
    if (!form.link_request_id) return
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/link-request/${form.link_request_id}`)
    await load()
  }

  async function unlinkRequest(requestId) {
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/unlink-request/${requestId}`)
    await load()
  }

  async function rebuild() {
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/rebuild-summary`)
    await load()
  }

  async function archive() {
    await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/archive`)
    await load()
  }

  async function createOrOpenOfferWorkspace() {
    try {
      const existing = await apiGet(`/api/agencies/${state.agency.id}/offer-workspaces?trip_id=${encodeURIComponent(tripId)}`)
      const workspace = existing.items?.[0] || (await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/offer-workspace`)).workspace
      window.location.href = `/agency/offers/${workspace.id}/builder`
    } catch (err) {
      setError(err.message)
    }
  }

  async function createOrOpenBookingWorkspace() {
    try {
      const existing = state?.bookingWorkspaces?.[0]
      if (existing) {
        window.location.href = `/agency/booking-workspaces/${existing.id}`
        return
      }
      const readinessId = state?.bookingReadiness?.booking_readiness?.id
      if (!readinessId) {
        setError("Booking readiness package is required before creating a booking workspace.")
        return
      }
      const created = await apiPost(`/api/agencies/${state.agency.id}/booking-workspaces/from-readiness`, {
        booking_readiness_package_id: readinessId,
        create_draft_record: true,
      })
      window.location.href = `/agency/booking-workspaces/${created.booking_workspace.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  const unlinkedRequests = (state?.requests || []).filter((request) => !request.trip_id || request.trip_id === tripId)

  return (
    <AgencyLayout user={state?.me?.user} agency={state?.agency}>
      <ProtectedRoute loading={!state && !error} error={error}>
        <div className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <a className="text-sm font-medium text-blue-700" href="/agency/trips">Back to trips</a>
                <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{state?.trip?.trip_reference}</p>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{state?.trip?.trip_title}</h2>
                <p className="mt-1 text-sm text-slate-600">{state?.trip?.route_summary || "Route pending"} · {state?.trip?.date_summary || "Dates pending"}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={createOrOpenOfferWorkspace}>Create / open offer workspace</button>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={rebuild}>Rebuild summary</button>
                <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={archive}>Archive</button>
              </div>
            </div>
          </div>

          <section className="grid gap-4 lg:grid-cols-4">
            <Metric label="Status" value={state?.trip?.trip_status?.replaceAll("_", " ")} />
            <Metric label="Passengers" value={state?.trip?.passenger_count ?? 0} />
            <Metric label="Segments" value={state?.trip?.segment_count ?? 0} />
            <Metric label="Services" value={state?.trip?.service_count ?? 0} />
          </section>

          <form className="grid gap-4 rounded-lg border border-slate-200 bg-white p-5 md:grid-cols-3" onSubmit={save}>
            <Field label="Trip title" value={form.trip_title} onChange={(value) => setField("trip_title", value)} />
            <Select label="Status" value={form.trip_status} onChange={(value) => setField("trip_status", value)} options={["draft", "planning", "quoted", "booked", "ticketed", "in_travel", "completed", "cancelled", "archived"]} />
            <Select label="Trip type" value={form.trip_type} onChange={(value) => setField("trip_type", value)} options={["one_way", "round_trip", "multi_city", "open_jaw", "complex", "unknown"]} />
            <Textarea label="Operational summary" value={form.operational_summary} onChange={(value) => setField("operational_summary", value)} />
            <Textarea label="Internal notes" value={form.internal_notes} onChange={(value) => setField("internal_notes", value)} />
            <Textarea label="Client-visible notes" value={form.client_visible_notes} onChange={(value) => setField("client_visible_notes", value)} />
            <div className="md:col-span-3">
              <button className="aa-primary-action rounded-md px-4 py-2 text-sm font-semibold" type="submit">Save trip</button>
            </div>
          </form>

          <Panel title="Linked requests">
            <form className="flex flex-wrap gap-2" onSubmit={linkRequest}>
              <select className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" value={form.link_request_id} onChange={(event) => setField("link_request_id", event.target.value)}>
                <option value="">Select request</option>
                {unlinkedRequests.map((request) => <option key={request.id} value={request.id}>{request.request_reference} · {request.title}</option>)}
              </select>
              <button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white" type="submit">Link request</button>
            </form>
            <List items={state?.linked_requests} empty="No linked requests" render={(request) => (
              <div className="flex flex-wrap items-center justify-between gap-2">
                <a className="font-medium text-blue-700" href={`/agency/requests/${request.id}`}>{request.request_reference} · {request.title}</a>
                <button className="rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold" type="button" onClick={() => unlinkRequest(request.id)}>Unlink</button>
              </div>
            )} />
          </Panel>

          <section className="grid gap-4 lg:grid-cols-2">
            <Panel title="Passengers"><List items={state?.passengers} empty="No trip passengers copied yet" render={(item) => `${item.display_name} · ${item.passenger_type.replaceAll("_", " ")}${item.assistance_summary ? ` · ${item.assistance_summary}` : ""}`} /></Panel>
            <Panel title="Segments"><List items={state?.segments} empty="No trip segments copied yet" render={(item) => `${item.segment_order}. ${item.origin_airport_code} to ${item.destination_airport_code}${item.departure_date ? ` · ${item.departure_date}` : ""}${item.flight_number ? ` · ${item.flight_number}` : ""}`} /></Panel>
          </section>
          <Panel title="Services"><List items={state?.services} empty="No trip services copied yet" render={(item) => `${item.service_code} · ${item.service_label} · ${item.status.replaceAll("_", " ")} · ${item.passenger_ids.length} pax / ${item.segment_ids.length} seg`} /></Panel>
          <Panel title="Special Services">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-950">Passenger service checks</p>
                <p className="mt-1 text-sm text-slate-600">Rules evaluation and SSR/OSI previews for this trip.</p>
              </div>
              <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/trips/${tripId}/special-services`}>Open Special Services</a>
            </div>
          </Panel>

          <AcceptedOfferPanel state={state} onCreateOrOpenBookingWorkspace={createOrOpenBookingWorkspace} />

          <TicketsEmdsTripPanel state={state} />

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {["Bookings", "Tickets / EMDs", "Documents", "Invoices / Payments"].map((title) => <FuturePanel title={title} key={title} />)}
          </section>

          <Panel title="Timeline"><List items={state?.timeline} empty="No trip timeline events yet" render={(item) => `${item.title}${item.summary ? ` · ${item.summary}` : ""}`} /></Panel>
        </div>
      </ProtectedRoute>
    </AgencyLayout>
  )
}

function Metric({ label, value }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p></div>
}

function Panel({ title, children }) {
  return <section className="space-y-4 rounded-lg border border-slate-200 bg-white p-5"><h3 className="font-semibold text-slate-950">{title}</h3>{children}</section>
}

function FuturePanel({ title }) {
  return <section className="rounded-lg border border-dashed border-slate-300 bg-white p-4"><h3 className="text-sm font-semibold text-slate-950">{title}</h3><p className="mt-2 text-xs text-slate-500">Future phase. This dossier can anchor the workflow later, but no functionality is active here yet.</p></section>
}

function AcceptedOfferPanel({ state, onCreateOrOpenBookingWorkspace }) {
  const snapshot = state?.acceptedOffer?.accepted_offer
  const acceptance = state?.acceptedOffer?.acceptance
  const readiness = state?.bookingReadiness?.booking_readiness
  const bookingWorkspace = state?.bookingWorkspaces?.[0]
  if (!snapshot && !readiness) {
    return (
      <Panel title="Accepted Offer + Booking Readiness">
        <EmptyState title="No accepted offer" body="Accepted offer snapshots appear here after an offer option is accepted." />
      </Panel>
    )
  }
  const pricing = snapshot?.confirmed_pricing_json?.summary || readiness?.pricing_snapshot_json?.summary || {}
  const services = snapshot?.confirmed_services_json || readiness?.services_snapshot_json || {}
  const pets = snapshot?.confirmed_pets_json || readiness?.pets_snapshot_json || {}
  const items = snapshot?.confirmed_special_items_json || readiness?.special_items_snapshot_json || {}
  const ssr = readiness?.ssr_json || snapshot?.ssr_osi_preview_json?.ssr || []
  const osi = readiness?.osi_json || snapshot?.ssr_osi_preview_json?.osi || []
  return (
    <Panel title="Accepted Offer + Booking Readiness">
      <div className="grid gap-4 lg:grid-cols-5">
        <Metric label="Acceptance" value={acceptance?.status || "snapshot"} />
        <Metric label="Readiness" value={readiness?.status || "pending"} />
        <Metric label="Pricing" value={money(pricing.total_amount, pricing.currency)} />
        <Metric label="Provider" value={readiness?.provider_target || "manual"} />
        <Metric label="Booking Workspace" value={bookingWorkspace?.workspace_number || "not created"} />
      </div>
      <section className="grid gap-4 lg:grid-cols-2">
        <SnapshotList
          title="Confirmed Segments"
          items={snapshot?.confirmed_segments_json || readiness?.segments_snapshot_json}
          render={(item) => `${item.sequence || item.segment_order}. ${item.origin_airport || item.origin_airport_code} to ${item.destination_airport || item.destination_airport_code}${item.flight_number ? ` · ${item.flight_number}` : ""}`}
        />
        <SnapshotList
          title="Confirmed Fare"
          items={snapshot?.confirmed_fare_bundle_json?.items}
          render={(item) => `${item.fare_family_name} · ${item.cabin_class}${item.booking_class ? ` · ${item.booking_class}` : ""}`}
        />
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <SnapshotList
          title="Services"
          items={[
            ...(services.trip_service_items || []),
            ...(services.passenger_service_requests || []),
            ...(services.requested_services || []),
          ]}
          render={(item) => item.service_label || item.service_name || item.service_code || item.category || "Service"}
        />
        <SnapshotList
          title="Pets + Special Items"
          items={[...(pets.items || []), ...(items.items || [])]}
          render={(item) => item.pet_name || item.item_label || item.item_type || item.service_code || "Item"}
        />
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <SnapshotList
          title="SSR Preview"
          items={ssr}
          render={(item) => item.ssr_code || item.code || JSON.stringify(item)}
        />
        <SnapshotList
          title="OSI Preview"
          items={osi}
          render={(item) => item.osi_text || item.text || JSON.stringify(item)}
        />
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <SnapshotList
          title="Warnings"
          items={readiness?.warnings_json}
          render={(item) => item.message || JSON.stringify(item)}
        />
        <SnapshotList
          title="Required Documents"
          items={readiness?.required_documents_json}
          render={(item) => item.label || item.document_type || JSON.stringify(item)}
        />
      </section>
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-dashed border-slate-300 p-4">
        <p className="text-sm text-slate-600">Create or open the manual booking workspace and PNR mirror. Live provider booking remains disabled.</p>
        <div className="flex flex-wrap gap-2">
          {bookingWorkspace ? (
            <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/booking-workspaces/${bookingWorkspace.id}`}>
              Open Booking Workspace
            </a>
          ) : (
            <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="button" onClick={onCreateOrOpenBookingWorkspace} disabled={!readiness}>
              Create Booking Workspace
            </button>
          )}
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-400" type="button" disabled>
            Create Live Booking
          </button>
        </div>
      </div>
    </Panel>
  )
}

function TicketsEmdsTripPanel({ state }) {
  const bookingWorkspace = state?.bookingWorkspaces?.[0]
  const readiness = state?.ticketEmdReadiness
  return (
    <Panel title="Tickets & EMDs">
      <div className="grid gap-4 lg:grid-cols-4">
        <Metric label="Tickets" value={state?.tickets?.length || 0} />
        <Metric label="EMDs" value={state?.emds?.length || 0} />
        <Metric label="Missing ticket #" value={readiness?.missing_ticket_numbers ?? 0} />
        <Metric label="Services without EMD" value={readiness?.services_without_emd?.length ?? 0} />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-dashed border-slate-300 p-4">
        <p className="text-sm text-slate-600">Ticket and EMD records are internal mirrors only. Live issuance is disabled.</p>
        <div className="flex flex-wrap gap-2">
          <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href="/agency/tickets-emds">Open Tickets & EMDs</a>
          {bookingWorkspace ? <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/booking-workspaces/${bookingWorkspace.id}`}>Open booking workspace</a> : null}
        </div>
      </div>
      <SnapshotList
        title="EMD Readiness Warnings"
        items={readiness?.warnings}
        render={(item) => item.message || JSON.stringify(item)}
      />
    </Panel>
  )
}

function SnapshotList({ title, items, render }) {
  const list = items || []
  return (
    <section>
      <h4 className="text-sm font-semibold text-slate-950">{title}</h4>
      {list.length ? (
        <div className="mt-2 divide-y divide-slate-100 rounded-md border border-slate-200">
          {list.map((item, index) => (
            <div className="p-3 text-sm text-slate-700" key={item.id || index}>
              {render(item)}
            </div>
          ))}
        </div>
      ) : <p className="mt-2 text-sm text-slate-500">None recorded.</p>}
    </section>
  )
}

function money(amount, currency) {
  if (amount === null || amount === undefined || amount === "") return "Not priced"
  return `${Number(amount).toFixed(2)} ${currency || "EUR"}`
}

function List({ items, empty, render }) {
  if (!items?.length) return <EmptyState title={empty} body="Trip dossier records appear here after requests are linked or conversion runs." />
  return <div className="divide-y divide-slate-100 rounded-md border border-slate-200 bg-white">{items.map((item) => <div className="p-3 text-sm leading-6 text-slate-700" key={item.id}>{render(item)}</div>)}</div>
}

function Field({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<input className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Textarea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700 md:col-span-3">{label}<textarea className="min-h-20 rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)} /></label>
}

function Select({ label, value, onChange, options }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{option.replaceAll("_", " ")}</option>)}</select></label>
}
