import { useEffect, useState } from "react"
import EmptyState from "../../components/EmptyState"
import ProtectedRoute from "../../components/ProtectedRoute"
import AgencyLayout from "../../layouts/AgencyLayout"
import { apiGet, apiPost, apiPut } from "../../lib/api"
import { loadCurrentAgency } from "../../lib/agency"

export default function TripDetailPage({ tripId }) {
  const [state, setState] = useState(null)
  const [form, setForm] = useState({ trip_title: "", trip_status: "draft", trip_type: "unknown", operational_summary: "", internal_notes: "", client_visible_notes: "", link_request_id: "" })
  const [changeForm, setChangeForm] = useState({
    operation_type: "itinerary_change",
    reason: "",
    source_booking_workspace_id: "",
    source_booking_record_id: "",
    summary_text: "",
    proposed_change_notes: "",
    internal_notes: "",
    original_snapshot_json: "",
    proposed_snapshot_json: "",
    operation_id: "",
    original_ticket_record_id: "",
    original_emd_record_id: "",
  })
  const [error, setError] = useState("")

  async function load() {
    const context = await loadCurrentAgency()
    const [detail, requests, acceptedOffer, bookingReadiness, bookingWorkspaces, tickets, emds, changes] = await Promise.all([
      apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}`),
      apiGet(`/api/agencies/${context.agency.id}/requests`),
      apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}/accepted-offer`),
      apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}/booking-readiness`),
      apiGet(`/api/agencies/${context.agency.id}/booking-workspaces?trip_id=${encodeURIComponent(tripId)}`),
      apiGet(`/api/agencies/${context.agency.id}/tickets?trip_id=${encodeURIComponent(tripId)}`),
      apiGet(`/api/agencies/${context.agency.id}/emds?trip_id=${encodeURIComponent(tripId)}`),
      apiGet(`/api/agencies/${context.agency.id}/trips/${tripId}/change-operations`),
    ])
    const bookingRecordId = bookingWorkspaces.items?.[0]?.booking_record?.id
    const ticketEmdReadiness = bookingRecordId
      ? await apiGet(`/api/agencies/${context.agency.id}/booking-records/${bookingRecordId}/ticket-emd-readiness`)
      : null
    setState({ ...context, ...detail, requests: requests.items, acceptedOffer, bookingReadiness, bookingWorkspaces: bookingWorkspaces.items || [], tickets: tickets.items || [], emds: emds.items || [], changes, ticketEmdReadiness })
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

  async function startTripChange(event) {
    event.preventDefault()
    try {
      await apiPost(`/api/agencies/${state.agency.id}/trips/${tripId}/change-operations`, {
        operation_type: changeForm.operation_type,
        reason: changeForm.reason || null,
        source_booking_workspace_id: changeForm.source_booking_workspace_id || null,
        source_booking_record_id: changeForm.source_booking_record_id || null,
        change_summary_json: compactObject({
          summary_text: changeForm.summary_text,
          proposed_change_notes: changeForm.proposed_change_notes,
          internal_notes: changeForm.internal_notes,
        }),
        original_snapshot_json: parseOptionalJson(changeForm.original_snapshot_json, "Original snapshot"),
        proposed_snapshot_json: parseOptionalJson(changeForm.proposed_snapshot_json, "Proposed snapshot"),
      })
      setChangeForm((current) => ({
        ...current,
        reason: "",
        summary_text: "",
        proposed_change_notes: "",
        internal_notes: "",
        original_snapshot_json: "",
        proposed_snapshot_json: "",
      }))
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createChangeBooking() {
    const operationId = changeForm.operation_id || state?.changes?.items?.[0]?.id
    if (!operationId) {
      setError("Create a trip change operation first.")
      return
    }
    try {
      const created = await apiPost(`/api/agencies/${state.agency.id}/trip-change-operations/${operationId}/create-change-booking`, {
        source_context: "existing_trip_change",
        trip_id: tripId,
        title: `${state.trip.trip_reference} change booking`,
        provider_target: "manual",
        create_draft_record: true,
        original_booking_record_id: changeForm.source_booking_record_id || null,
        revision_reason: changeForm.summary_text || changeForm.reason || "Existing trip change mirror",
        internal_notes: changeForm.internal_notes || null,
      })
      window.location.href = `/agency/booking-workspaces/${created.booking_workspace.id}`
    } catch (err) {
      setError(err.message)
    }
  }

  async function startTicketExchange() {
    if (!changeForm.original_ticket_record_id) {
      setError("Original ticket record id is required.")
      return
    }
    try {
      await apiPost(`/api/agencies/${state.agency.id}/ticket-exchange-operations`, {
        original_ticket_record_id: changeForm.original_ticket_record_id,
        operation_type: "exchange",
        trip_id: tripId,
        reason: changeForm.reason || null,
      })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function startEmdExchange() {
    if (!changeForm.original_emd_record_id) {
      setError("Original EMD record id is required.")
      return
    }
    try {
      await apiPost(`/api/agencies/${state.agency.id}/emd-exchange-operations`, {
        original_emd_record_id: changeForm.original_emd_record_id,
        operation_type: "exchange",
        trip_id: tripId,
        reason: changeForm.reason || null,
      })
      await load()
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

          <TripDocumentsPanel state={state} tripId={tripId} />

          <ChangesExchangesPanel
            changeForm={changeForm}
            onChange={(updates) => setChangeForm((current) => ({ ...current, ...updates }))}
            onCreateChangeBooking={createChangeBooking}
            onStartEmdExchange={startEmdExchange}
            onStartTicketExchange={startTicketExchange}
            onStartTripChange={startTripChange}
            state={state}
          />

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {["Bookings", "Tickets / EMDs", "Invoices / Payments"].map((title) => <FuturePanel title={title} key={title} />)}
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
      {readiness ? (
        <div className="flex flex-wrap gap-2 rounded-md border border-dashed border-slate-300 p-4">
          <p className="text-sm text-slate-600">Use the booking handoff workspace to review blockers, mappings, documents, price/payment status, and instructions before creating or opening a booking mirror.</p>
          <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={`/agency/booking-handoffs?acceptance_id=${acceptance?.id || readiness.acceptance_id || ""}&booking_readiness_package_id=${readiness.id}&trip_id=${readiness.trip_id}`}>
            Open booking handoff
          </a>
        </div>
      ) : null}
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

function TripDocumentsPanel({ state, tripId }) {
  const trip = state?.trip
  const change = state?.changes?.items?.[0]
  const bookingWorkspace = state?.bookingWorkspaces?.[0]
  const ticket = state?.tickets?.[0]
  const emd = state?.emds?.[0]
  const sourceId = trip?.id || tripId
  return (
    <Panel title="Documents">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-dashed border-slate-300 p-4">
        <p className="text-sm text-slate-600">Generate internal document previews from this trip dossier and linked mirrors.</p>
        <div className="flex flex-wrap gap-2">
          <a className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" href={documentHref("trip_confirmation", "trip", sourceId)}>Trip confirmation</a>
          <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("internal_case_summary", "trip", sourceId)}>Internal case summary</a>
          {bookingWorkspace ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("booking_confirmation", "booking_workspace", bookingWorkspace.id)}>Booking document</a> : null}
          {ticket ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("ticket_receipt", "ticket_record", ticket.id)}>Ticket receipt</a> : null}
          {emd ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("emd_receipt", "emd_record", emd.id)}>EMD receipt</a> : null}
          {change ? <a className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" href={documentHref("trip_change_summary", "trip_change_operation", change.id)}>Change summary</a> : null}
        </div>
      </div>
    </Panel>
  )
}

function ChangesExchangesPanel({ changeForm, onChange, onCreateChangeBooking, onStartEmdExchange, onStartTicketExchange, onStartTripChange, state }) {
  const operations = state?.changes?.items || []
  const ticketExchanges = state?.changes?.ticket_exchange_operations || []
  const emdExchanges = state?.changes?.emd_exchange_operations || []
  return (
    <Panel title="Changes & Exchanges">
      <form className="space-y-4" onSubmit={onStartTripChange}>
        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-950">Start trip change</h4>
          <div className="grid gap-3 md:grid-cols-3">
            <Select label="Operation type" value={changeForm.operation_type} onChange={(value) => onChange({ operation_type: value })} options={["itinerary_change", "booking_change", "ticket_exchange", "ticket_reissue", "emd_exchange", "emd_reissue", "cancellation", "refund_quote", "service_change", "other"]} />
            <Field label="Source booking workspace id optional" value={changeForm.source_booking_workspace_id} onChange={(value) => onChange({ source_booking_workspace_id: value })} />
            <Field label="Source booking record id optional" value={changeForm.source_booking_record_id} onChange={(value) => onChange({ source_booking_record_id: value })} />
            <Field label="Reason" value={changeForm.reason} onChange={(value) => onChange({ reason: value })} />
            <Field label="Summary text" value={changeForm.summary_text} onChange={(value) => onChange({ summary_text: value })} />
            <Field label="Proposed change notes" value={changeForm.proposed_change_notes} onChange={(value) => onChange({ proposed_change_notes: value })} />
            <Textarea label="Internal notes" value={changeForm.internal_notes} onChange={(value) => onChange({ internal_notes: value })} />
          </div>
          <details className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <summary className="cursor-pointer text-sm font-semibold text-slate-950">Advanced change snapshots</summary>
            <p className="mt-2 text-sm text-slate-600">Advanced only. Structured fields above build the change summary unless snapshot JSON is provided.</p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <RawTextarea label="Original snapshot JSON" value={changeForm.original_snapshot_json} onChange={(value) => onChange({ original_snapshot_json: value })} />
              <RawTextarea label="Proposed snapshot JSON" value={changeForm.proposed_snapshot_json} onChange={(value) => onChange({ proposed_snapshot_json: value })} />
            </div>
          </details>
          <button className="aa-primary-action rounded-md px-3 py-2 text-sm font-semibold" type="submit">Start trip change</button>
        </section>
      </form>
      <section className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-950">Change booking mirror</h4>
        <div className="grid gap-3 md:grid-cols-4">
          <a className="rounded-md border border-slate-300 px-3 py-2 text-center text-sm font-semibold" href={`/agency/booking-imports?linked_trip_id=${state?.trip?.id || ""}`}>Attach imported GDS booking to this trip</a>
          <a className="rounded-md border border-slate-300 px-3 py-2 text-center text-sm font-semibold" href={`/agency/booking-workspaces?mode=manual_booking&trip_id=${state?.trip?.id || ""}`}>Open structured booking form</a>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onCreateChangeBooking}>Create change booking mirror</button>
          <Field label="Change operation id" value={changeForm.operation_id} onChange={(value) => onChange({ operation_id: value })} />
        </div>
      </section>
      <section className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-950">Ticket and EMD exchanges</h4>
        <div className="grid gap-3 md:grid-cols-4">
          <Field label="Original ticket record id" value={changeForm.original_ticket_record_id} onChange={(value) => onChange({ original_ticket_record_id: value })} />
          <Field label="Original EMD record id" value={changeForm.original_emd_record_id} onChange={(value) => onChange({ original_emd_record_id: value })} />
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onStartTicketExchange}>Start ticket exchange</button>
          <button className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold" type="button" onClick={onStartEmdExchange}>Start EMD exchange</button>
        </div>
      </section>
      <section className="grid gap-4 lg:grid-cols-3">
        <SnapshotList
          title="Trip Change Operations"
          items={operations}
          render={(item) => `${item.operation_type?.replaceAll("_", " ")} · ${item.status?.replaceAll("_", " ")} · ${item.new_booking_workspace_id || "no revised booking"}`}
        />
        <SnapshotList
          title="Ticket Exchange Operations"
          items={ticketExchanges}
          render={(item) => `${item.operation_type?.replaceAll("_", " ")} · ${item.status?.replaceAll("_", " ")} · ${item.original_ticket_record_id} → ${item.new_ticket_record_id || "pending"}`}
        />
        <SnapshotList
          title="EMD Exchange Operations"
          items={emdExchanges}
          render={(item) => `${item.operation_type?.replaceAll("_", " ")} · ${item.status?.replaceAll("_", " ")} · ${item.original_emd_record_id} → ${item.new_emd_record_id || "pending"}`}
        />
      </section>
      <p className="text-sm text-slate-600">Change, exchange, refund, and void actions are internal mirrors only. No provider execution is performed.</p>
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

function RawTextarea({ label, value, onChange }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<textarea className="min-h-24 rounded-md border border-slate-300 px-3 py-2 font-mono text-xs font-normal" value={value} onChange={(event) => onChange(event.target.value)} spellCheck={false} /></label>
}

function Select({ label, value, onChange, options }) {
  return <label className="grid gap-1 text-sm font-medium text-slate-700">{label}<select className="rounded-md border border-slate-300 px-3 py-2 text-sm font-normal" value={value} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option value={option} key={option}>{option.replaceAll("_", " ")}</option>)}</select></label>
}

function compactObject(item) {
  return Object.fromEntries(Object.entries(item).filter(([, value]) => value !== "" && value !== null && value !== undefined))
}

function parseOptionalJson(value, label) {
  const text = String(value || "").trim()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`${label} JSON must be valid.`)
  }
}

function documentHref(documentType, sourceContextType, sourceContextId) {
  const params = new URLSearchParams({
    document_type: documentType,
    source_context_type: sourceContextType,
    source_context_id: sourceContextId || "",
  })
  return `/agency/documents?${params.toString()}`
}
